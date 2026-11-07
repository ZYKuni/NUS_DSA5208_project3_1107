"""Figures for the report from results/all.csv. Log axes for time, size and cores
(course requirement). Output: results/figures/*.pdf

Usage: python3 analysis/plots.py [results_dir]
Owner: C.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def savefig(fig, outdir: Path, name: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(outdir / f"{name}.pdf")
    plt.close(fig)


def serial_scaling(df, outdir):
    s = df[df["impl"] == "serial"]
    if s.empty:
        return
    fig, ax = plt.subplots()
    for dim, g in s.groupby("dim"):
        unknowns = g["n"] ** dim
        ax.loglog(unknowns, g["t_total"], "o-", label=f"{dim}D")
    ax.set_xlabel("unknowns N")
    ax.set_ylabel("time (s)")
    ax.legend()
    savefig(fig, outdir, "serial_scaling")


def strong_scaling(df, outdir):
    m = df[df["source"].str.startswith("strong")]
    for (dim, n), g in m.groupby(["dim", "n"]):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.5))
        for dec, gg in g.groupby("decomp"):
            a1.loglog(gg["cores"], gg["speedup"], "o-", label=dec)
            a2.semilogx(gg["cores"], gg["efficiency"], "o-", label=dec)
        cores = sorted(g["cores"].unique())
        a1.loglog(cores, cores, "k--", lw=0.8, label="ideal")
        a1.set_xlabel("cores"); a1.set_ylabel("speedup"); a1.legend()
        a2.set_xlabel("cores"); a2.set_ylabel("efficiency"); a2.set_ylim(0, 1.1)
        savefig(fig, outdir, f"strong_{dim}d_n{n}")


def time_breakdown(df, outdir):
    m = df[df["source"].str.startswith("strong")]
    for (dim, n, dec), g in m.groupby(["dim", "n", "decomp"]):
        g = g.sort_values("cores")
        fig, ax = plt.subplots()
        x = range(len(g))
        ax.bar(x, g["t_stencil"], label="stencil")
        ax.bar(x, g["t_halo"], bottom=g["t_stencil"], label="halo")
        ax.bar(x, g["t_reduce"], bottom=g["t_stencil"] + g["t_halo"], label="allreduce")
        ax.set_xticks(list(x), g["cores"].astype(str))
        ax.set_yscale("log")
        ax.set_xlabel("cores"); ax.set_ylabel("time (s)"); ax.legend()
        savefig(fig, outdir, f"breakdown_{dim}d_n{n}_{dec}")


def main(results_dir: str = "results") -> None:
    path = Path(results_dir) / "all.csv"
    if not path.exists():
        print(f"{path} not found; run analysis/collect.py first")
        return
    df = pd.read_csv(path)
    outdir = Path(results_dir) / "figures"
    serial_scaling(df, outdir)
    strong_scaling(df, outdir)
    time_breakdown(df, outdir)
    # TODO(C): weak scaling, hybrid rank x thread, GPU figures
    print(f"figures in {outdir}/")


if __name__ == "__main__":
    main(*sys.argv[1:])
