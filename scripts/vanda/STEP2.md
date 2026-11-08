# Validate the shared CG workload before benchmarking

Use the already integrated manufactured problem from A, not the old sine mode.
Build the CPU versions and run a small check locally:

```bash
scripts/build.sh cpu build-check
python3 scripts/check_workload.py --bin-dir build-check/bin \
  --output results/raw/workload-local --launcher "mpiexec --bind-to none"
```

The output directory must be new, to prevent mixing old and new runs. The default
checks two mesh sizes in each dimension, three independent processes per
configuration, serial plus two-rank MPI and two-rank/two-thread OpenMP.
Every process uses `--repeat 1`; all raw rows and commands are retained.

On Vanda, submit from the repository root using your project:

```bash
qsub -P YOUR_PROJECT scripts/vanda/workload_cpu.pbs
qsub -P YOUR_PROJECT scripts/vanda/workload_gpu.pbs
```

These single-node jobs use the validated HPC-X toolchain and local process
launch. The CPU job requests 8 CPUs and tests two ranks; the GPU job requests one
A40-capable GPU allocation and tests one CUDA rank against a serial reference.
Neither launcher is a template for a multi-node run. The GPU job discovers the
actual CUDA architecture and runs the standalone stencil/dot check too.

Each job runs the seven existing CTest groups, then checks 2D n=15,31,511 and
3D n=15,31,95. This intentionally includes small correctness cases and larger
duration pilots. A successful check requires multiple CG iterations, finite
positive timing/error, true residual below 1e-8, matching implementation/resource
labels, iteration agreement with serial within one, and relative error agreement
within 1e-6.

Inspect `results/raw/step2-*/exit_code.txt`, `job.log` and
`workload/summary.csv`. Completion requires exit zero plus both
`WORKLOAD_VALIDATION=PASS` and `WORKLOAD_STEP2_COMPLETE`. The checker reports
whether the shortest of three samples reaches one second; this pilot heuristic
does not convert its numbers into a formal scaling dataset.

Timing boundaries and affinity must be resolved for formal experiments. In
particular, current CPU and CUDA setup work lies on different sides of their
timers. See `report/workload_step2.md` before deriving cross-backend speedups.
