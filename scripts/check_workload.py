#!/usr/bin/env python3
"""Validate the shared multi-iteration workload; report timing, not scaling claims.

Each repetition is a separate --repeat 1 process. Raw samples are retained instead
of pairing a fastest time with the last repetition's convergence statistics.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import statistics
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--impls", nargs="+", choices=("mpi", "omp", "cuda"), default=["mpi", "omp"])
    parser.add_argument("--sizes-2d", type=int, nargs="+", default=[15, 31])
    parser.add_argument("--sizes-3d", type=int, nargs="+", default=[15, 31])
    parser.add_argument("--ranks", type=int, default=2)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--launcher", default="mpiexec")
    parser.add_argument("--platform", choices=("local", "vanda", "atlas"), default="local")
    parser.add_argument("--min-solve-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if min(args.ranks, args.threads, args.repeats, *args.sizes_2d, *args.sizes_3d) < 1:
        parser.error("counts and problem sizes must be positive")
    if args.platform != "local" and not os.environ.get("PBS_JOBID"):
        parser.error("cluster validation must run inside a PBS allocation")
    args.bin_dir = args.bin_dir.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent.parent
    binaries = {impl: args.bin_dir / ("poisson_" + impl) for impl in ["serial"] + args.impls}
    manifest = {
        "platform": args.platform, "job_id": os.environ.get("PBS_JOBID"),
        "problem": "product x(1-x)exp(x); continuous manufactured RHS; zero initial guess",
        "problem_header_sha256": hashlib.sha256((root / "include/problem.hpp").read_bytes()).hexdigest(),
        "binary_sha256": {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in binaries.items()},
        "environment": {k: os.environ.get(k) for k in
                        ("OMP_PLACES", "OMP_PROC_BIND", "OMP_WAIT_POLICY", "PCG_CUDA_HALO")},
        "repetition_policy": "independent processes, --repeat 1; keep all samples",
        "min_solve_seconds": args.min_solve_seconds,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    samples, summary = [], []
    for dim, sizes in [(2, args.sizes_2d), (3, args.sizes_3d)]:
        for n in sizes:
            references = []
            for impl, binary in binaries.items():
                rows = []
                for repeat in range(args.repeats):
                    run_id = f"{impl}-{dim}d-n{n}-r{repeat}"
                    path = args.output / (run_id + ".csv")
                    command = [] if impl == "serial" else shlex.split(args.launcher) + ["-n", str(args.ranks)]
                    command += [str(binary), "--dim", str(dim), "--n", str(n), "--tol", "1e-8",
                                "--maxit", "10000", "--decomp", "cart", "--halo", "block",
                                "--cg", "std", "--repeat", "1", "--csv", str(path.resolve())]
                    env = dict(os.environ, OMP_NUM_THREADS=str(args.threads if impl == "omp" else 1),
                               OMP_DYNAMIC="FALSE")
                    (args.output / (run_id + ".command.json")).write_text(json.dumps(command) + "\n")
                    with (args.output / (run_id + ".stdout.log")).open("w") as out, \
                            (args.output / (run_id + ".stderr.log")).open("w") as err:
                        subprocess.run(command, env=env, stdout=out, stderr=err,
                                       check=True, timeout=args.timeout)
                    with path.open() as stream:
                        row, = csv.DictReader(stream)
                    expected = {"impl": impl, "dim": dim, "n": n,
                                "ranks": 1 if impl == "serial" else args.ranks,
                                "threads": args.threads if impl == "omp" else 1,
                                "gpus": args.ranks if impl == "cuda" else 0}
                    for key, value in expected.items():
                        actual = row[key] if key == "impl" else int(row[key])
                        if actual != value:
                            raise ValueError(f"{run_id}: {key}={actual}, expected {value}")
                    iters, residual = int(row["iters"]), float(row["rel_res"])
                    error, duration = float(row["err_l2"]), float(row["t_total"])
                    if not (1 < iters < 10000 and 0 <= residual < 1e-8 and error > 0
                            and duration > 0 and all(map(math.isfinite, [residual, error, duration]))):
                        raise ValueError(f"{run_id}: degenerate, unconverged or non-finite result: {row}")
                    if impl != "serial":
                        ref_iters = statistics.median(int(r["iters"]) for r in references)
                        ref_error = statistics.median(float(r["err_l2"]) for r in references)
                        if abs(iters - ref_iters) > 1 or not math.isclose(error, ref_error, rel_tol=1e-6):
                            raise ValueError(f"{run_id}: does not match serial reference")
                    rows.append(row)
                    samples.append(dict(row, repeat=repeat, platform=args.platform,
                                        job_id=os.environ.get("PBS_JOBID", "")))
                if impl == "serial":
                    references = rows
                times = [float(r["t_total"]) for r in rows]
                item = dict(impl=impl, dim=dim, n=n, repeats=len(rows),
                            iters_min=min(int(r["iters"]) for r in rows),
                            iters_max=max(int(r["iters"]) for r in rows),
                            seconds_min=min(times), seconds_median=statistics.median(times),
                            seconds_max=max(times), cv=statistics.pstdev(times)/statistics.mean(times),
                            max_true_rel_res=max(float(r["rel_res"]) for r in rows),
                            err_l2_median=statistics.median(float(r["err_l2"]) for r in rows),
                            long_enough_for_performance=min(times) >= args.min_solve_seconds)
                summary.append(item)
                print(f"PASS {impl} {dim}D n={n}: iters={item['iters_min']}..{item['iters_max']}, "
                      f"median={item['seconds_median']:.6g}s, CV={item['cv']:.3g}", flush=True)
    for name, rows in [("samples.csv", samples), ("summary.csv", summary)]:
        with (args.output / name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("WORKLOAD_VALIDATION=PASS", flush=True)


if __name__ == "__main__":
    main()
