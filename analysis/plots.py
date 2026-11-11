"""Report figures from verified results/all.csv; PDFs, PNGs and a figure book.

Usage: python3 analysis/plots.py [results_dir]
Time, unknown-count and core/thread-count axes are logarithmic.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"pcg-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
import numpy as np
import pandas as pd

from collect import ROOT, one, require, sha256, write_json

COLORS = ["#176B91", "#D06A30", "#32876C", "#8758A6"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.titlesize": 11, "axes.labelsize": 10,
                     "legend.fontsize": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42,
                     "savefig.facecolor": "white", "figure.facecolor": "white"})
RUNTIME_NOTE = "Line/filled marker: minimum; hollow diamond: median; shading: observed min-max (3 runs, not a CI)."


def core_axis(ax, ticks=(1, 4, 16, 64, 288), label="Physical CPU cores"):
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel(label)
    ax.grid(True, which="major", alpha=.16)


def band(ax, g, x, label, color, metric="seconds", center=None, scale=1):
    g = g.sort_values(x)
    require(not g[x].duplicated().any(), f"multiple configurations at the same {x}: {label}")
    if metric in ["speedup", "efficiency", "weak_solve_ratio", "weak_iteration_ratio", "matched_mpi_ratio",
                  "gpu_speedup", "gpu_efficiency", "staged_over_transport"]:
        lo, med, hi = metric+"_low", metric+"_median", metric+"_high"
        center = center or metric
    else:
        lo, med, hi = [metric+"_"+s for s in ["min", "median", "max"]]
        center = center or lo
    ax.fill_between(g[x], g[lo]*scale, g[hi]*scale, color=color, alpha=.13, linewidth=0)
    ax.plot(g[x], g[center]*scale, "o-", color=color, label=label, markersize=4, linewidth=1.4)
    ax.plot(g[x], g[med]*scale, "D", color=color, markerfacecolor="white", markersize=3.5, linestyle="none")


class Figures:
    def __init__(self, results, record, data):
        self.results, self.record, self.data = results, record, data
        self.out = results/"figures"
        self.out.mkdir(parents=True, exist_ok=True)
        self.book = PdfPages(self.out/"scaling_figures.pdf", metadata={"Title": "Vanda parallel scaling - audited measurements",
                              "Author": "DSA5208 project team", "CreationDate": None, "ModDate": None})
        self.index = []

    def save(self, fig, name, title, caption, groups, platform_label="CPU"):
        fig.suptitle(title, x=.07, ha="left", y=.97, fontsize=15, fontweight="bold", color="#19384A")
        fig.text(.07, .91, f"Vanda | audited {platform_label} measurements | 3 independent runs per configuration", fontsize=9, color="#526673")
        fig.text(.07, .035, caption, fontsize=8, color="#465B68", va="bottom")
        fig.subplots_adjust(left=.08, right=.98, top=.80, bottom=.22, wspace=.32, hspace=.45)
        if len(fig.axes) == 4:
            fig.subplots_adjust(top=.83, bottom=.17, hspace=.46)
        fig.savefig(self.out/(name+".pdf"), metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(self.out/(name+".png"), dpi=170)
        self.book.savefig(fig)
        group_ids = sorted(set(groups))
        jobs = sorted(self.data.loc[self.data["group"].isin(group_ids), "job_id"].unique())
        self.index.append(dict(name=name, title=title, caption=caption, groups=group_ids, jobs=jobs,
                               pdf_sha256=sha256(self.out/(name+".pdf")),
                               png_sha256=sha256(self.out/(name+".png"))))
        plt.close(fig)

    def finish(self):
        self.book.close()
        write_json(self.out/"manifest.json", dict(figures=self.index, count=len(self.index),
                   book_sha256=sha256(self.out/"scaling_figures.pdf"),
                   all_csv_sha256=sha256(self.results/"all.csv"),
                   analysis_manifest_sha256=sha256(self.results/"analysis_manifest.json"),
                   plotter_sha256=sha256(__file__), coverage=self.record["coverage"],
                   versions=dict(python=platform.python_version(), matplotlib=matplotlib.__version__,
                                 pandas=pd.__version__, numpy=np.__version__),
                   skipped=([dict(figure="gpu_scaling", reason="No accepted GPU measurements")]
                            if self.record["coverage"]["accepted_gpu_groups"] == 0 else [])))


def serial_figures(df, output):
    s = df[df["experiment"] == "serial"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for color, (dim, g) in zip(COLORS, s.groupby("dim")):
        g = g.sort_values("unknowns")
        band(axes[0], g, "unknowns", f"{dim}D", color)
        axes[1].plot(g["unknowns"], g["iters"], "o-", color=color, label=f"{dim}D")
    for ax in axes:
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Interior unknowns N = n^d")
        ax.grid(True, which="major", alpha=.16); ax.legend()
    axes[0].set_ylabel("CG solve time (s)"); axes[1].set_ylabel("CG iterations")
    axes[0].set_title("Runtime vs problem size"); axes[1].set_title("Iteration growth is included in runtime")
    source_note = ("All serial sweep meshes retained, including the unused n=202 reference."
                   if 202 in s["n"].values else
                   "The n=203 serial reference is from the weak-scaling supplement; source allocations are retained in the tables.")
    output.save(fig, "serial_scaling", "Serial scaling: runtime and iteration count",
                RUNTIME_NOTE+"\n"+source_note, s["group"])

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for color, (dim, g) in zip(COLORS, s.groupby("dim")):
        h = 1/(g["n"]+1)
        ax.loglog(h, g["err_l2"], "o-", label=f"{dim}D measured", color=color)
        anchor = g.loc[g["n"].idxmin()]
        ax.loglog(h, anchor.err_l2*(h*(anchor.n+1))**2, "--", color=color, alpha=.65,
                  label=f"{dim}D h^2 reference")
    ax.set_xlabel("Grid spacing h = 1 / (n + 1)"); ax.set_ylabel("Discrete L2 error")
    ax.grid(True, which="major", alpha=.16); ax.legend(loc="upper left")
    output.save(fig, "serial_error", "Validation: serial discretization error",
                "Dashed lines show h^2 trends anchored at each dimension's coarsest mesh; they are not fitted models.\n"
                "Every retained parallel sample also passes the same-mesh serial iteration/error check and true residual < 1e-8.", s["group"])


def strong_figures(df, output):
    s = df[(df["experiment"] == "strong") & (df["impl"] == "mpi")]
    for (dim, n), g in s.groupby(["dim", "n"]):
        require(g["job_id"].nunique() == 1, "select one allocation per strong curve")
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.8))
        for color, (dec, v) in zip(COLORS, g.groupby("decomp")):
            for ax, metric in zip(axes, ["seconds", "speedup", "efficiency"]):
                band(ax, v, "cores", dec, color, metric, scale=100 if metric == "efficiency" else 1)
        for ax in axes:
            core_axis(ax); ax.legend()
        axes[0].set_yscale("log"); axes[0].set_ylabel("CG solve time (s)")
        axes[1].set_yscale("log"); axes[1].plot([1,288], [1,288], "--", color="#7A858B", lw=1, label="Ideal")
        axes[1].set_ylabel("Speedup T_MPI(1) / T_MPI(P)"); axes[1].legend()
        axes[2].axhline(100, color="#7A858B", linestyle="--", lw=1)
        axes[2].set_ylabel("Parallel efficiency (%)"); axes[2].set_ylim(bottom=0)
        for ax, title in zip(axes, ["Solve time", "Speedup", "Efficiency (not clipped at 100%)"]): ax.set_title(title)
        output.save(fig, f"strong_{dim}d_n{n}", f"{dim}D strong scaling | n={n} | through 288 physical cores",
                    RUNTIME_NOTE+"\nEach decomposition uses its own one-rank MPI baseline; ratio shading is an all-pairs range envelope.", g["group"])

        fig, axes = plt.subplots(1, 3, figsize=(12, 4.8))
        for color, (dec, v) in zip(COLORS, g.groupby("decomp")):
            for ax, metric in zip(axes, ["t_stencil", "t_halo", "t_reduce"]):
                band(ax, v, "cores", dec, color, metric, center=metric)
        for ax, title in zip(axes, ["Stencil + vector updates", "Halo exchange", "Dot products + reductions"]):
            core_axis(ax); ax.set_yscale("log"); ax.set_ylabel("Independent phase maximum (s)")
            ax.set_title(title); ax.legend()
        output.save(fig, f"phases_{dim}d_n{n}", f"{dim}D phase timing | n={n} | independent rank maxima",
                    "Line: phase from the fastest whole solve; hollow: phase median; shading: observed phase range.\n"
                    "Phase maxima may occur on different ranks and intervals may overlap. Do not stack or interpret their sum as total.", g["group"])


def weak_figures(df, output):
    s = df[df["experiment"] == "weak"]
    for dim, g in s.groupby("dim"):
        require(g["job_id"].nunique() == 1, "select one allocation per weak curve")
        g = g.sort_values("cores")
        fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))
        a, b, c, d = axes.flat
        band(a, g, "cores", "Whole solve", COLORS[0]); a.set_ylabel("CG solve time (s)"); a.set_yscale("log")
        band(b, g, "cores", "Per iteration", COLORS[1], "iteration_seconds")
        b.set_ylabel("Seconds / CG iteration"); b.set_yscale("log")
        c.plot(g["cores"], g["iters"], "o-", color=COLORS[2]); c.set_ylabel("CG iterations"); c.set_yscale("log")
        for metric, label, color in [("weak_solve_ratio", "Whole-solve T(1)/T(P)", COLORS[0]),
                                     ("weak_iteration_ratio", "Per-iteration cost(1)/cost(P)", COLORS[1])]:
            band(d, g, "cores", label, color, metric, scale=100)
        d.set_ylabel("Weak time ratio (%)"); d.set_ylim(bottom=0); d.legend()
        d.axhline(100, color="#7A858B", linestyle="--", lw=1)
        for ax, title in zip(axes.flat, ["Whole-solve runtime", "Iteration-normalised runtime", "Convergence cost", "Two views of weak scaling"]):
            core_axis(ax, ticks=[1,4,16,64,256] if dim == 2 else [1,8,64,256])
            ax.set_title(title)
            ax.set_xlim(.8, 350)
        missing = 256 not in g["cores"].values
        if missing:
            a.axvline(256, color="#9B6861", linestyle=":", lw=1)
            a.text(.03, .95, "P=256: missing", transform=a.transAxes, ha="left", va="top", color="#9B4032", fontsize=9)
        if missing:
            note = "3D curve ends at 216 cores; the planned 256-core point is absent and is not interpolated."
        elif dim == 2:
            note = "2D owned points/core are exactly constant at 16384 through 256 cores."
        else:
            endpoint = g[g["cores"] == 256].iloc[0]
            note = f"3D n={int(endpoint.n)} at 256 cores gives {endpoint.points_per_core:.3f} points/core (-0.276% vs the base)."
        output.save(fig, f"weak_{dim}d", f"{dim}D weak scaling" + (" | incomplete endpoint" if missing else " | through 256 physical cores"),
                    RUNTIME_NOTE+"\n"+note+"\nWhole-solve time includes iteration growth; per-iteration ratios isolate average iteration cost.", g["group"])


def variant_figures(df, output):
    s = df[(df["experiment"] == "variants") | ((df["experiment"] == "strong")
           & (df["decomp"] == "cart") & df["ranks"].isin([64,256]))]
    names = {("block","std"): "Blocking / standard", ("overlap","std"): "Overlap / standard",
             ("block","pipe"): "Blocking / single-reduction", ("overlap","pipe"): "Overlap / single-reduction"}
    for (dim, n), g in s.groupby(["dim", "n"]):
        require(g["job_id"].nunique() == 1, "select one allocation per variant comparison")
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
        for color, ((halo, cg), v) in zip(COLORS, g.groupby(["halo", "cg"], sort=False)):
            band(axes[0], v, "cores", names[halo,cg], color)
            band(axes[1], v, "cores", names[halo,cg], color, "t_reduce", center="t_reduce")
        for ax, title in zip(axes, ["Whole CG solve", "Independent reduction phase maximum"]):
            core_axis(ax, ticks=[64,256]); ax.set_xlim(50,330); ax.set_yscale("log"); ax.set_ylabel("Time (s)")
            ax.set_title(title); ax.legend()
        output.save(fig, f"variants_{dim}d_n{n}", f"{dim}D parallelization choices | n={n} | Cartesian decomposition",
                    "Whole solve: minimum/median/range of 3 runs. Phase line: same row as minimum solve; hollow: phase median.\n"
                    "'pipe' is single-reduction CG (Chronopoulos-Gear); it is not a claim of asynchronous pipelined CG.", g["group"])


def hybrid_figures(df, output):
    for (dim, n), g in df[df["experiment"] == "hybrid"].groupby(["dim", "n"]):
        require(g["job_id"].nunique() == 1, "select one allocation per hybrid comparison")
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
        band(axes[0], g, "threads", "MPI + OpenMP", COLORS[0])
        require(g["matched_mpi_ratio_baseline_group"].nunique() == 1, "mixed hybrid baselines")
        baseline = one(df, job_id=g["job_id"].iloc[0], group=g["matched_mpi_ratio_baseline_group"].iloc[0])
        axes[0].axhline(baseline.t_total, color=COLORS[1], linestyle="--", label="Pure MPI, 288 ranks (min)")
        axes[0].set_ylabel("CG solve time (s)"); axes[0].set_yscale("log"); axes[0].legend()
        band(axes[1], g, "threads", "Relative to pure MPI, 288 ranks", COLORS[0], "matched_mpi_ratio")
        axes[1].axhline(1, color=COLORS[1], linestyle="--"); axes[1].set_ylabel("T_MPI(288) / T_hybrid")
        axes[1].set_ylim(bottom=0)
        for ax, title in zip(axes, ["Fixed-resource runtime", "Same-resource runtime ratio"]):
            core_axis(ax, ticks=[1,2,4,9,18,72], label="OpenMP threads per MPI rank"); ax.set_title(title)
        output.save(fig, f"hybrid_{dim}d_n{n}", f"{dim}D MPI + OpenMP | n={n} | fixed 288 physical cores",
                    RUNTIME_NOTE+"\nMPI ranks x threads: 288x1, 144x2, 72x4, 32x9, 16x18, 4x72. Ratio is not a strong-scaling efficiency.", g["group"])


def gpu_figures(df, output):
    gpu = df[(df["impl"] == "cuda") & (df["experiment"] == "strong")]
    for (dim, n), g in gpu.groupby(["dim", "n"]):
        require(g["job_id"].nunique() == 1, "select one allocation per GPU comparison")
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.8))
        for color, (mode, v) in zip(COLORS, g.groupby("transport")):
            for ax, metric in zip(axes, ["seconds", "gpu_speedup", "gpu_efficiency"]):
                band(ax, v, "gpus", mode, color, metric, scale=100 if metric == "gpu_efficiency" else 1)
        for ax in axes:
            core_axis(ax, ticks=[1, 2], label="GPUs used (one per host)")
            ax.set_xlim(.9, 2.2); ax.legend()
        axes[0].set_yscale("log"); axes[0].set_ylabel("CG solve time (s)"); axes[0].set_title("Whole-solve runtime")
        axes[1].plot([1, 2], [1, 2], "--", color="#7A858B", label="Ideal")
        axes[1].set_ylabel("Speedup T_GPU(1) / T_GPU(G)"); axes[1].set_title("Same-transport baseline")
        axes[1].legend()
        axes[2].axhline(100, linestyle="--", color="#7A858B")
        axes[2].set_ylabel("GPU parallel efficiency (%)"); axes[2].set_ylim(bottom=0)
        axes[2].set_title("Efficiency (not clipped at 100%)")
        output.save(fig, f"gpu_{dim}d_n{n}", f"{dim}D MPI + CUDA | n={n} | one versus two GPUs",
                    RUNTIME_NOTE+"\nEach transport uses its own one-GPU baseline in the same allocation. Device-pointer MPI over TCP may internally stage.",
                    g["group"], platform_label="GPU")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("results_dir", nargs="?", type=Path, default=ROOT/"results")
    a = p.parse_args()
    record = json.loads((a.results_dir/"analysis_manifest.json").read_text())
    for name, checksum in record["output_sha256"].items():
        require(sha256(a.results_dir/name) == checksum, f"unverified analysis input: {name}")
    df = pd.read_csv(a.results_dir/"all.csv", keep_default_na=False, na_values=[""])
    require(not df["experiment"].isin(["preflight", "pilot"]).any(), "preflight in performance plots")
    output = Figures(a.results_dir, record, df)
    for make in [serial_figures, strong_figures, weak_figures, variant_figures, hybrid_figures, gpu_figures]:
        make(df, output)
    output.finish()
    print(f"Generated {len(output.index)} figures and scaling_figures.pdf in {output.out}")


if __name__ == "__main__":
    main()
