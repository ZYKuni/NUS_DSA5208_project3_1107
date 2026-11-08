# C task 2: shared CG workload review

Date: 2026-11-08 (Asia/Singapore). This step reviews and validates the workload;
it does not perform the formal scaling experiments.

## Branches inspected

| Remote branch at inspection | Revision | Relevant change |
| --- | --- | --- |
| main | dee4c79 | PRs 1 and 2 merged: A's serial/MPI solvers and shared Backend, non-eigenmode problem, rebuilt OpenMP and tests |
| claude/project-thread-hs9gsj | 287b7f4 | Includes b/hybrid and rebuilds OpenMP on A's MPI backend; updates the hybrid validation script |
| b/hybrid | 908168b | Original hybrid CPU/GPU implementations; no later commit on this branch at inspection |
| c/bench | 02771e5 | Previously completed cluster access and minimum jobs |

`c/bench` now integrates main and the updated hybrid branch without changing the
other branches or merging anything into main.
The final refresh found main had advanced from d5e1467 to dee4c79 by merging
287b7f4. Its source tree is identical to the already validated upstream hybrid
revision; that merge was also integrated into c/bench.

## Accepted mathematical problem

Use A's existing problem definition for every executable:

```text
g(t) = t(1-t)exp(t)
u(x_1,...,x_d) = product g(x_k), d = 2 or 3
-g''(t) = t(t+3)exp(t)
f = sum_k [-g''(x_k) product_{j != k} g(x_j)]
```

This satisfies zero Dirichlet boundaries and produces a known smooth continuous
solution. The five-/seven-point discretisation has a measurable second-order
error. The previous product of sines was a single discrete eigenvector, allowing
standard CG with zero initial guess to finish in one iteration. A had already
fixed that issue; no second competing workload was introduced.

The serial, MPI, OpenMP and CUDA sources all use `include/problem.hpp`. The CPU
versions additionally share the CG driver. CUDA still has its separate standard
CG implementation and only supports `--cg std --halo block`.

## Checks and changes

- Resolved the CMake integration conflict while retaining the cluster probes,
  explicit GPU architecture selection and A's shared backend libraries.
- Added `scripts/check_workload.py`: independent `--repeat 1` processes, three
  retained samples per configuration, serial reference comparison, actual
  iteration count, true residual, error, run duration and variability checks.
- The checker rejects one-iteration, unconverged, non-finite and mislabelled
  results. It records binary and problem-header hashes, launcher commands and
  relevant environment settings.
- CUDA previously reported the recursive residual. Its final validation now
  exchanges the final solution's halo, applies the discrete operator, and
  computes the true residual outside the timed loop, matching the CPU meaning
  of `rel_res`.
- The local Linux Release build passed all seven existing CTest groups.
  Eighteen local workload groups (54 independent processes) passed; local timings
  are only development evidence.
- Vanda GPU job 1532562 passed all seven CTest groups, the independent 2D/3D GPU
  stencil/dot checks and all six serial/CUDA workload pairs with three repeats.
  Its PBS exit status was zero.
  This one-rank CUDA pilot checks the workload and kernels; it does not validate
  communication between GPUs. Multi-GPU correctness remains a prerequisite for
  the corresponding scaling experiments.
- Vanda CPU job 1532579 passed all seven CTest groups and all six
  serial/MPI/OpenMP workload triples with three repeats. Its PBS exit status was
  zero. This gives 54 CPU-pilot solves and 36 GPU-pilot solves, all retained.
- Initial CPU pilot 1532561 used PBS/TM for a single-node job; its MPI test
  startup was slow and it was cancelled. The accepted replacement uses local
  HPC-X launch within the one-node allocation. The original log is retained and
  its partial samples are not part of the accepted dataset.

Every accepted implementation/repetition returned the same iteration count at
each tested mesh:

| Dimension | n | CG iterations |
| --- | --- | --- |
| 2D | 15 | 45 |
| 2D | 31 | 92 |
| 2D | 511 | 1557 |
| 3D | 15 | 55 |
| 3D | 31 | 113 |
| 3D | 95 | 350 |

For duration calibration only, the CPU pilot's serial medians were 1.64513 s
(2D n=511) and 1.55332 s (3D n=95). On the GPU pilot, CUDA medians were
0.179232 s and 0.0875132 s respectively. These are different allocations with
different timing setup boundaries, not a CPU/GPU speedup comparison. Most small
and GPU cases are still below the one-second pilot threshold. One small OpenMP
group had CV about 0.81; no repetition was removed to hide the variability.

## Interpretation and handoff to task 3

Keep all per-repetition data. The checker reports min/median/max and coefficient
of variation (standard deviation divided by mean). A one-second minimum duration
is a pilot heuristic, not a course rule; short successful validation cases remain
labelled as too short for performance work.

These pilots do not establish speedup or efficiency. Affinity is not tuned, the
CPU and GPU pilots can use different CPU hardware/toolchains, and there is a
timing-contract difference to resolve before formal comparisons: the shared CPU
driver times work-vector allocation/initialisation inside `cg_solve`, whereas
the CUDA timer starts after its setup. Large-scale runs should use a clearly
documented common timing boundary.

For weak scaling, keep track of both iteration count and seconds per iteration:
this non-eigenmode CG problem needs more iterations as the mesh is refined.
Whole-solve weak scaling and per-iteration weak scaling answer different questions.
The current serial/MPI/OpenMP command-line programs can return exit zero even if
CG hits `maxit`; the checker therefore validates the CSV's true residual too.
Do not assume the default `maxit=10000` is sufficient for the large meshes in
the old batch templates: the measured 2D n=511 case already takes 1557 iterations.

The raw source archive, commands, CSV samples and job logs stay under ignored
`results/raw/`. Curated validation summaries are separate from formal benchmark
data and must not be silently ingested as scaling samples.
See [curated evidence](../results/validation/step2/README.md) for the accepted job
allocations, summaries, hashes and archive verification. Both accepted jobs'
exit codes, completion markers and all 90 samples were rechecked after download.
