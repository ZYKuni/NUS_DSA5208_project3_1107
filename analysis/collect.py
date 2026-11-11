"""Collect explicitly selected, audited experiment exports; never scan raw logs.

Usage: python3 analysis/collect.py [results_dir] [--config analysis/datasets.json]
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LABELS = ["impl", "dim", "n", "ranks", "threads", "gpus", "decomp", "halo", "cg",
          "experiment", "job_id", "group", "nodes"]
VALUES = ["t_total", "t_stencil", "t_halo", "t_reduce", "rel_res", "err_l2"]
INTEGERS = ["dim", "n", "ranks", "threads", "gpus", "iters", "repeat", "nodes"]
EXPERIMENTS = {"serial", "strong", "weak", "variants", "hybrid", "reference"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_input(results, spec):
    """Check the immutable export, including its complete-row minimum selection."""
    paths = {kind: results / (spec["prefix"] + "_" + kind)
             for kind in ["samples.csv", "summary.csv", "manifest.json", "audit.json"]}
    for kind, path in paths.items():
        require(sha256(path) == spec["sha256"][kind], f"checksum mismatch: {path}")
    audit = json.loads(paths["audit.json"].read_text())
    manifest = json.loads(paths["manifest.json"].read_text())
    require(audit["sample_sha256"] == sha256(paths["samples.csv"]), "audit/sample mismatch")
    require(audit["job_id"] == manifest["job_id"], "audit/manifest job mismatch")
    require(all(audit[k] is True for k in ["source_hashes_match", "placement_verified",
                                          "serial_comparisons_pass"]), "audit did not pass")
    if audit["exit_status"] != 0:
        require(spec.get("allow_documented_partial", False)
                and audit["documented_missing_reference_failure"] is True
                and audit["scope"] == "completed groups only", "unapproved partial suite")
    samples = pd.read_csv(paths["samples.csv"], keep_default_na=False)
    exported = pd.read_csv(paths["summary.csv"], keep_default_na=False)
    labels = LABELS + (["transport"] if "transport" in samples.columns else [])
    require(set(LABELS + VALUES + INTEGERS).issubset(samples.columns), "missing sample fields")
    for k in INTEGERS:
        samples[k] = pd.to_numeric(samples[k], errors="raise")
        require(np.isfinite(samples[k]).all() and (samples[k] % 1 == 0).all(), f"non-integer {k}")
        samples[k] = samples[k].astype(int)
    for k in VALUES:
        samples[k] = pd.to_numeric(samples[k], errors="raise")
        require(np.isfinite(samples[k]).all() and (samples[k] >= 0).all(), f"invalid {k}")
    require((samples["t_total"] > 0).all() and (samples["rel_res"] < 1e-8).all()
            and samples["iters"].between(2, 19999).all(), "invalid convergence/timing")
    require(samples["dim"].isin([2, 3]).all() and (samples[["n", "ranks", "threads", "nodes"]] > 0).all().all()
            and (samples["gpus"] >= 0).all(), "invalid resource/mesh labels")
    require(samples["job_id"].eq(manifest["job_id"]).all(), "mixed job IDs in export")
    require(len(samples) == audit["samples"] and len(exported) == audit["groups"], "audit count mismatch")
    require(not exported["group"].duplicated().any(), "duplicate exported group")
    summaries = []
    for group, g in samples.groupby("group", sort=True):
        require(sorted(g["repeat"].tolist()) == [0, 1, 2], f"missing/duplicate repeat: {group}")
        require(all(g[k].nunique() == 1 for k in labels), f"mixed configuration: {group}")
        best = g.loc[g["t_total"].idxmin()]
        old = exported[exported["group"] == group]
        require(len(old) == 1, f"missing summary: {group}")
        old = old.iloc[0]
        for k in labels + ["repeat", "iters"]:
            require(old[k] == best[k], f"summary label/minimum mismatch: {group}/{k}")
        for k in VALUES:
            require(math.isclose(float(old[k]), float(best[k]), rel_tol=1e-12, abs_tol=1e-15),
                    f"summary row mismatch: {group}/{k}")
        times = g["t_total"]
        for k, value in [("seconds_min", times.min()), ("seconds_median", times.median()),
                         ("seconds_max", times.max()), ("cv", times.std(ddof=0)/times.mean())]:
            require(math.isclose(float(old[k]), float(value), rel_tol=1e-10, abs_tol=1e-14),
                    f"summary statistic mismatch: {group}/{k}")
        row = best.to_dict()
        row.update(seconds_min=times.min(), seconds_median=times.median(), seconds_max=times.max(),
                   cv=times.std(ddof=0)/times.mean(), repeats=3, iters_min=g["iters"].min(),
                   iters_max=g["iters"].max(), max_true_rel_res=g["rel_res"].max(),
                   shortest_at_least_one_second=bool(times.min() >= 1))
        per_iter = g["t_total"] / g["iters"]
        for name, values in [("iteration_seconds", per_iter)] + [(k, g[k]) for k in VALUES[1:4]]:
            for stat in ["min", "median", "max"]:
                row[name + "_" + stat] = getattr(values, stat)()
        row["source"] = spec["prefix"]
        summaries.append(row)
    require(len(summaries) == audit["groups"], "group count mismatch")
    # Retest comparisons using all references before any analysis exclusions.
    refs = samples[samples["impl"] == "serial"].groupby(["dim", "n"])
    for row in samples.itertuples():
        ref = refs.get_group((row.dim, row.n)).iloc[0]
        require(abs(row.iters-ref.iters) <= 1
                and math.isclose(row.err_l2, ref.err_l2, rel_tol=1e-6), "serial comparison failed")
    cpu = samples["gpus"] == 0
    require("physical_cores" in samples.columns or not samples["impl"].isin(["mpi", "omp"]).any(),
            "missing CPU placement count")
    if "physical_cores" in samples.columns:
        require((samples.loc[cpu, "physical_cores"] ==
                 samples.loc[cpu, "ranks"] * samples.loc[cpu, "threads"]).all(), "CPU count mismatch")
    gpu = samples["impl"] == "cuda"
    if gpu.any():
        require("transport" in samples.columns and samples.loc[gpu, "transport"].isin(["staged", "device"]).all(),
                "missing/invalid GPU transport")
        require((samples.loc[gpu, "ranks"] == samples.loc[gpu, "gpus"]).all(), "GPU/rank mismatch")
    samples["source"] = spec["prefix"]
    return pd.DataFrame(summaries), samples, audit


def one(frame, **labels):
    rows = frame
    for k, v in labels.items():
        rows = rows[rows[k] == v]
    require(len(rows) == 1, f"baseline must be unique ({len(rows)}): {labels}")
    return rows.iloc[0]


def ratio(row, baseline, prefix, metric="seconds"):
    """Min/min and median/median; range is an envelope, never a confidence interval."""
    fields = (["seconds_min", "seconds_median", "seconds_max"] if metric == "seconds"
              else [metric + "_" + s for s in ["min", "median", "max"]])
    lo, med, hi = fields
    same = row["group"] == baseline["group"] and row["job_id"] == baseline["job_id"]
    row[prefix] = 1.0 if same else baseline[lo] / row[lo]
    row[prefix + "_median"] = 1.0 if same else baseline[med] / row[med]
    row[prefix + "_low"] = 1.0 if same else baseline[lo] / row[hi]
    row[prefix + "_high"] = 1.0 if same else baseline[hi] / row[lo]
    row[prefix + "_baseline_group"] = baseline["group"]


def derive(frame):
    result = []
    for _, original in frame.iterrows():
        row = original.to_dict()
        row.update(cores=int(row["ranks"]*row["threads"]), unknowns=int(row["n"]**row["dim"]),
                   seconds_per_iteration=row["t_total"]/row["iters"])
        row["points_per_core"] = row["unknowns"]/row["cores"]
        # These independent maxima can overlap and can sum to more than total.
        row["phase_sum_over_total"] = sum(row[k] for k in VALUES[1:4])/row["t_total"]
        common = dict(job_id=row["job_id"], dim=row["dim"], impl=row["impl"],
                      decomp=row["decomp"], halo=row["halo"], cg=row["cg"], threads=row["threads"])
        if row["experiment"] == "strong" and row["impl"] == "mpi":
            base = one(frame, **common, experiment="strong", n=row["n"], ranks=1)
            ratio(row, base, "speedup")
            for suffix in ["", "_median", "_low", "_high"]:
                row["efficiency" + suffix] = row["speedup" + suffix]/row["cores"]
        elif row["experiment"] == "strong" and row["impl"] == "cuda":
            base = one(frame, **common, experiment="strong", n=row["n"], gpus=1,
                       transport=row["transport"])
            ratio(row, base, "gpu_speedup")
            for suffix in ["", "_median", "_low", "_high"]:
                row["gpu_efficiency" + suffix] = row["gpu_speedup" + suffix]/row["gpus"]
            staged = one(frame, **common, experiment="strong", n=row["n"], gpus=row["gpus"],
                         transport="staged")
            ratio(row, staged, "staged_over_transport")
        elif row["experiment"] == "weak":
            base = one(frame, **common, experiment="weak", ranks=1)
            ratio(row, base, "weak_solve_ratio")
            ratio(row, base, "weak_iteration_ratio", "iteration_seconds")
            row["weak_points_relative_to_base"] = row["points_per_core"]/(base["n"]**base["dim"])
        elif row["experiment"] in ["variants", "hybrid"]:
            base = one(frame, experiment="strong", job_id=row["job_id"], dim=row["dim"],
                       n=row["n"], ranks=row["ranks"] if row["experiment"] == "variants" else row["cores"],
                       threads=1, impl="mpi", decomp="cart", halo="block", cg="std")
            ratio(row, base, "matched_mpi_ratio")
        result.append(row)
    return pd.DataFrame(result).sort_values(
        ["experiment", "dim", "n", "impl", "decomp", "halo", "cg", "cores", "threads", "job_id"]
    ).reset_index(drop=True)


def coverage(df):
    strong_ranks = [1, 2, 4, 8, 16, 32, 64, 128, 256, 288]
    rows = []
    for dim, weak_ranks in [(2, [1, 4, 16, 64, 256]), (3, [1, 8, 64, 216, 256])]:
        for experiment, dec, planned in [("strong", "cart", strong_ranks),
                                          ("strong", "slab", strong_ranks),
                                          ("weak", "cart", weak_ranks)]:
            observed = sorted(df.loc[(df["experiment"] == experiment) & (df["dim"] == dim)
                                     & (df["decomp"] == dec) & (df["impl"] == "mpi"), "ranks"].unique())
            missing = sorted(set(planned)-set(observed))
            rows.append(dict(experiment=experiment, dim=dim, decomp=dec,
                             observed_ranks=[int(x) for x in observed], missing_ranks=missing,
                             complete=not missing))
    gpu = df[(df["impl"] == "cuda") & (df["experiment"] == "strong")]
    expected = {(d, n, t, g) for d,n in [(2,2048),(3,256)]
                for t in ["staged", "device"] for g in [1, 2]}
    observed = set(zip(gpu["dim"], gpu["n"], gpu.get("transport", []), gpu["gpus"]))
    missing_gpu = sorted(expected-observed)
    return dict(cpu_series=rows, accepted_gpu_groups=len(gpu),
                missing_gpu_configurations=[dict(dim=d, n=n, transport=t, gpus=g) for d,n,t,g in missing_gpu],
                gpu_status="unavailable" if gpu.empty else "partial" if missing_gpu else "complete",
                task3_complete=all(r["complete"] for r in rows) and not missing_gpu)


def collect(results, config_path):
    config = json.loads(config_path.read_text())
    groups, samples, input_records, exclusions = [], [], [], []
    for spec in config["inputs"]:
        summary, repetitions, audit = read_input(results, spec)
        explicit = set(spec.get("exclude_groups", []))
        require(explicit.issubset(set(summary["group"])), "unknown group in exclusion list")
        excluded = summary["experiment"].isin(config["exclude_experiments"]) | summary["group"].isin(explicit)
        for row in summary[excluded].itertuples():
            exclusions.append(dict(job_id=row.job_id, group=row.group,
                                   reason="explicit group exclusion" if row.group in explicit else row.experiment))
        keep = summary[~excluded]
        require(set(keep["experiment"]).issubset(EXPERIMENTS), "unrecognised experiment")
        groups.append(keep)
        samples.append(repetitions[repetitions["group"].isin(keep["group"])])
        input_records.append(dict(prefix=spec["prefix"], sha256=spec["sha256"], audit=audit))
    raw_groups = pd.concat(groups, ignore_index=True)
    require(not raw_groups.duplicated(["job_id", "group"]).any(), "duplicate source group")
    df = derive(raw_groups)
    repetitions = pd.concat(samples, ignore_index=True).sort_values(["job_id", "group", "repeat"])
    out = results / "all.csv"
    df.to_csv(out, index=False, lineterminator="\n", float_format="%.12g")
    repetitions.to_csv(results / "analysis_samples.csv", index=False, lineterminator="\n", float_format="%.12g")
    outputs = [out, results/"analysis_samples.csv"]
    tables = results / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    for (experiment, impl, dim), g in df.groupby(["experiment", "impl", "dim"]):
        path = results/f"{experiment}_{impl}_{dim}d.csv"
        g.to_csv(path, index=False, float_format="%.12g")
        outputs.append(path)
    exports = {
        "strong_endpoints": df[(df["experiment"] == "strong") & (df["impl"] == "mpi")
                               & df["ranks"].isin([1, 64, 256, 288])],
        "weak_scaling": df[df["experiment"] == "weak"],
        "hybrid_comparison": df[df["experiment"] == "hybrid"],
        "variant_comparison": df[(df["experiment"] == "variants") |
                                 ((df["experiment"] == "strong") & (df["decomp"] == "cart")
                                  & df["ranks"].isin([64, 256]))],
        "serial_scaling": df[df["experiment"] == "serial"],
    }
    gpu = df[(df["experiment"] == "strong") & (df["impl"] == "cuda")]
    if not gpu.empty:
        exports["gpu_scaling"] = gpu
    for name, g in exports.items():
        path = tables/(name+".csv")
        g.to_csv(path, index=False, float_format="%.12g")
        outputs.append(path)
    record = dict(dataset=config["dataset"], config_sha256=sha256(config_path),
                  collector_sha256=sha256(__file__), inputs=input_records,
                  groups=len(df), samples=len(repetitions), excluded_groups=exclusions,
                  counts={str(k):int(v) for k, v in df["experiment"].value_counts().items()},
                  coverage=coverage(df), output_sha256={str(p.relative_to(results)):sha256(p)
                                                       for p in outputs},
                  versions=dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__),
                  selection="minimum complete row of three repeats; median and range retained",
                  ratio_range="all-pairs envelope of observed sample ranges; not a confidence interval",
                  phases="independently maximised rank times; not additive or a communication fraction")
    write_json(results/"analysis_manifest.json", record)
    print(f"Collected {len(df)} groups / {len(repetitions)} samples; excluded {len(exclusions)} groups")
    print("Missing:", [(r["dim"], r["experiment"], r["missing_ranks"])
                       for r in record["coverage"]["cpu_series"] if r["missing_ranks"]],
          "; GPU:", record["coverage"]["gpu_status"])
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", nargs="?", type=Path, default=ROOT/"results")
    parser.add_argument("--config", type=Path, default=ROOT/"analysis/datasets.json")
    args = parser.parse_args()
    collect(args.results_dir.resolve(), args.config.resolve())


if __name__ == "__main__":
    main()
