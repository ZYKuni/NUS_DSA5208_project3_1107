"""Merge all results/*.csv into results/all.csv and add speedup / efficiency.

Usage: python3 analysis/collect.py [results_dir]
Owner: C.
"""
import sys
from pathlib import Path

import pandas as pd

KEYS = ["impl", "dim", "n", "decomp", "halo", "cg"]


def main(results_dir: str = "results") -> None:
    files = [f for f in Path(results_dir).glob("*.csv") if f.name != "all.csv"]
    if not files:
        print(f"no CSV files in {results_dir}/")
        return
    df = pd.concat([pd.read_csv(f).assign(source=f.stem) for f in files], ignore_index=True)
    df["cores"] = df["ranks"] * df["threads"]
    # --repeat already keeps the fastest run; if a config was run twice, keep the fastest too
    df = df.sort_values("t_total").drop_duplicates(
        KEYS + ["ranks", "threads", "gpus", "source"]).sort_values(KEYS + ["cores"])
    df["comm_frac"] = (df["t_halo"] + df["t_reduce"]) / df["t_total"]

    # Strong-scaling speedup relative to the 1-core run of the same configuration.
    base = df[df["cores"] == 1].set_index(KEYS + ["source"])["t_total"]
    idx = df.set_index(KEYS + ["source"]).index
    df["t_1core"] = base.reindex(idx).to_numpy()
    df["speedup"] = df["t_1core"] / df["t_total"]
    df["efficiency"] = df["speedup"] / df["cores"]

    out = Path(results_dir) / "all.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    main(*sys.argv[1:])
