#!/usr/bin/env python3
"""Generate the LaTeX tables of the report from the committed result CSVs.

Run from the repository root:  python3 report/make_tables.py
Writes report/generated/*.tex. Every number in the report tables comes from
results/*.csv (minimum of three independent runs, see Section 5 of the report).
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
OUT = ROOT / "report" / "generated"


def rows(name):
    with open(RES / name) as f:
        return list(csv.DictReader(f))


def f(x, d=3):
    return f"{float(x):.{d}f}"


def sci(x, d=2):
    m, e = f"{float(x):.{d}e}".split("e")
    return f"${m}\\times10^{{{int(e)}}}$"


def write(name, text):
    (OUT / name).write_text(text)


def nnz(d, n):
    # rows * (2d+1) minus the stencil entries that fall on the Dirichlet boundary
    return (2 * d + 1) * n**d - 2 * d * n ** (d - 1)


def dims_create(p, nd):
    """MPI_Dims_create: balanced factorisation, non-increasing order."""
    dims = [1] * nd
    rest = p
    primes = []
    q = 2
    while rest > 1:
        while rest % q == 0:
            primes.append(q)
            rest //= q
        q += 1
    for pr in sorted(primes, reverse=True):
        i = dims.index(min(dims))
        dims[i] *= pr
    return sorted(dims, reverse=True)


def serial_table():
    lines = []
    prev = {}
    for r in rows("tables/serial_scaling.csv"):
        d, n, it = int(r["dim"]), int(r["n"]), int(r["iters"])
        N, Z = n**d, nnz(d, n)
        t = float(r["t_total"])
        per_nnz = t / it / Z * 1e9
        err = float(r["err_l2"])
        order = ""
        if d in prev:
            pn, perr = prev[d]
            order = f(math.log(perr / err) / math.log((n + 1) / (pn + 1)), 2)
        prev[d] = (n, err)
        lines.append(f"{d}D & {n} & {N:,} & {Z:,} & {it} & {f(t, 3) if t < 100 else f(t, 1)} & "
                     f"{f(t / it * 1e3, 3)} & {f(per_nnz, 2)} & {sci(err)} & {order} \\\\")
    write("serial.tex", "\n".join(lines) + "\n")


def strong_table(dim):
    data = {}
    for r in rows(f"strong_mpi_{dim}d.csv"):
        data[(r["decomp"], int(r["ranks"]))] = r
    ps = sorted({p for _, p in data})
    out = []
    for p in ps:
        cells = [str(p)]
        for dec in ("cart", "slab"):
            r = data[(dec, p)]
            t1 = float(data[(dec, 1)]["t_total"])
            t = float(r["t_total"])
            s = t1 / t
            cells += [f(t, 3), f(s, 1), f(100 * s / p, 1)]
        r = data[("cart", p)]
        cells += [f(r["t_stencil"], 3), f(r["t_halo"], 3), f(r["t_reduce"], 3)]
        nodes = r.get("nodes", "")
        cells.insert(1, nodes)
        out.append(" & ".join(cells) + " \\\\")
    write(f"strong_{dim}d.tex", "\n".join(out) + "\n")


def weak_table():
    out = []
    base = {}
    for r in rows("tables/weak_scaling.csv"):
        d, p, n, it = int(r["dim"]), int(r["ranks"]), int(r["n"]), int(r["iters"])
        t = float(r["t_total"])
        tpi = t / it
        if p == 1:
            base[d] = (t, tpi)
        t1, tpi1 = base[d]
        out.append(f"{d}D & {p} & {n} & {n**d / p:,.0f} & {it} & {f(t, 4)} & {f(r['seconds_median'], 4)} & "
                   f"{f(tpi * 1e6, 1)} & {f(100 * t1 / t, 1)} & {f(100 * tpi1 / tpi, 1)} \\\\")
    write("weak.tex", "\n".join(out) + "\n")


def variants_table():
    v = {}
    for r in rows("tables/variant_comparison.csv"):
        v[(int(r["dim"]), int(r["ranks"]), r["halo"], r["cg"])] = r
    out = []
    for d in (2, 3):
        for p in (64, 256):
            cells = [f"{d}D", str(p)]
            ts = {k: float(v[(d, p) + k]["t_total"]) for k in
                  [("block", "std"), ("overlap", "std"), ("block", "pipe"), ("overlap", "pipe")]}
            best = min(ts.values())
            for k, t in ts.items():
                s = f(t, 3)
                cells.append(f"\\textbf{{{s}}}" if t == best else s)
            rb, rp = v[(d, p, "block", "std")], v[(d, p, "block", "pipe")]
            cells += [f(rb["t_reduce"], 3), f(rp["t_reduce"], 3)]
            out.append(" & ".join(cells) + " \\\\")
    write("variants.tex", "\n".join(out) + "\n")


def hybrid_table():
    h = {}
    for r in rows("tables/hybrid_comparison.csv"):
        h[(int(r["dim"]), int(r["ranks"]), int(r["threads"]))] = r
    mpi = {d: {int(r["ranks"]): r for r in rows(f"strong_mpi_{d}d.csv") if r["decomp"] == "cart"}
           for d in (2, 3)}
    out = []
    splits = [(288, 1), (144, 2), (72, 4), (32, 9), (16, 18), (4, 72)]
    out.append("pure MPI & 288 & 1 & " + " & ".join(
        f"{f(mpi[d][288]['t_total'], 3)} & 1.00" for d in (2, 3)) + " \\\\ \\midrule")
    for p, t in splits:
        cells = ["MPI+OpenMP", str(p), str(t)]
        for d in (2, 3):
            r = h[(d, p, t)]
            cells += [f(r["t_total"], 3), f(float(r["t_total"]) / float(mpi[d][288]["t_total"]), 2)]
        out.append(" & ".join(cells) + " \\\\")
    write("hybrid.tex", "\n".join(out) + "\n")
    # phase detail
    out = []
    for d in (2, 3):
        for p, t in splits:
            r = h[(d, p, t)]
            out.append(f"{d}D & {p}$\\times${t} & {f(r['t_stencil'], 3)} & {f(r['t_halo'], 3)} & "
                       f"{f(r['t_reduce'], 3)} \\\\")
        if d == 2:
            out[-1] += " \\midrule"
    write("hybrid_phases.tex", "\n".join(out) + "\n")


def gpu_table():
    g = rows("tables/gpu_scaling.csv")
    ref = {2: rows("reference_serial_2d.csv")[0], 3: rows("reference_serial_3d.csv")[0]}
    base = {}
    out = []
    for r in g:
        d, gp = int(r["dim"]), int(r["gpus"])
        tr = r["group"].rsplit("-", 1)[1]
        t = float(r["t_total"])
        if gp == 1:
            base[(d, tr)] = t
        s = base[(d, tr)] / t
        out.append(f"{d}D, $n={r['n']}$ & {tr} & {gp} & {f(t, 3)} & {f(s, 2)} & {f(100 * s / gp, 1)} & "
                   f"{f(r['t_stencil'], 3)} & {f(r['t_halo'], 3)} & {f(r['t_reduce'], 3)} & "
                   f"{f(float(ref[d]['t_total']) / t, 1)} \\\\")
    write("gpu.tex", "\n".join(out) + "\n")


def comm_table():
    """Halo words sent per rank per CG iteration (one apply) for the largest block."""
    out = []
    for d, n in ((2, 2048), (3, 288)):
        for p in (64, 256, 288):
            cells = [f"{d}D, $n={n}$", str(p)]
            for kind in ("slab", "cart"):
                dims = [p] + [1] * (d - 1) if kind == "slab" else dims_create(p, d)
                L = [math.ceil(n / q) for q in dims]
                words = 0
                nb = 0
                for a in range(d):
                    if dims[a] == 1:
                        continue
                    face = math.prod(L[b] for b in range(d) if b != a)
                    words += 2 * face
                    nb += 2
                vol = math.prod(L)
                cells += ["$" + "\\times".join(map(str, dims)) + "$", str(nb),
                          f"{words * 8 / 1024:.1f}", f"{words / vol:.3f}"]
            out.append(" & ".join(cells) + " \\\\")
    write("comm.tex", "\n".join(out) + "\n")


def reduce_latency():
    out = []
    for d in (2, 3):
        rs = {int(r["ranks"]): r for r in rows(f"strong_mpi_{d}d.csv") if r["decomp"] == "cart"}
        for p in (1, 16, 64, 128, 256, 288):
            r = rs[p]
            per = float(r["t_reduce"]) / (2 * int(r["iters"])) * 1e6
            out.append(f"{d}D & {p} & {r['nodes']} & {f(per, 1)} \\\\")
        if d == 2:
            out[-1] += " \\midrule"
    write("reduce.tex", "\n".join(out) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    serial_table()
    strong_table(2)
    strong_table(3)
    weak_table()
    variants_table()
    hybrid_table()
    gpu_table()
    comm_table()
    reduce_latency()
    print("wrote", sorted(p.name for p in OUT.glob("*.tex")))


if __name__ == "__main__":
    main()
