# Task 3: scaling measurements and completion status

**Status, 9 November 2026:** the requested CPU extension is measured through
256 and 288 physical cores. Task 3 as a whole remains incomplete: the 3D weak
curve needs its 256-rank point and the GPU suite has no accepted measurements.
On November 9 at 13:48 Singapore, Vanda's login node was accessible, but both
`qstat -Bf stdct-mgmt-02` and direct `qsub` returned connection refused
(`errno=15010`). The prepared repair submission did not receive a job ID.

## Accepted CPU evidence

PBS job `1533443.stdct-mgmt-02` ran on November 8, 20:28–23:11 Singapore
(recorded walltime 02:43:15), with four exclusive 72-core hosts:
CN-013, CN-083, CN-132 and CN-138. The root host reports Intel Xeon Platinum
8452Y, two sockets, 36 cores/socket and one hardware thread/core. Rank placement
records independently establish disjoint physical cores for every retained
sample, including the 256/288-rank and MPI×OpenMP configurations.

The build used Release C++17, NVIDIA HPC SDK 26.1 `nvc++` through `mpicxx`,
HPC-X 2.25.1 and Open MPI 4.1.9a1. CPU communication explicitly selected
`ob1` / `self,vader,tcp`; HCOLL and UCC were disabled after initialization
failures. These measurements describe the TCP/shared-memory configuration.
They do not establish InfiniBand performance.

| Completed experiment | Groups | Accepted samples |
| --- | ---: | ---: |
| Small-mesh serial/MPI/OpenMP preflight | 8 | 24 |
| Serial size sweep | 11 | 33 |
| Strong scaling, 2D/3D, slab/cart, 1–288 ranks | 40 | 120 |
| Halo/CG choices at 64 and 256 ranks | 12 | 36 |
| Six MPI×OpenMP splits of 288 cores, both dimensions | 12 | 36 |
| Weak scaling: all five 2D points; first four 3D points | 9 | 27 |
| Total | 92 | 276 |

Each group has one excluded warmup and three independent processes with
`--repeat 1`. The summary selects a complete minimum-time row and retains
all samples, median, range and coefficient of variation (CV). It does not
combine independently selected phase times across repetitions. Timings cover
the CG iteration loop, including its end barrier, and exclude allocation,
initialization, error validation and output.

All seven CTest groups passed on the allocation. Every retained sample has
more than one CG iteration, a finite positive solve time, and a recomputed
relative residual below 1e-8 (maximum **5.597143e-9**). Parallel iteration counts
agree with a same-mesh serial reference within one; discrete L2 error agrees
within relative tolerance 1e-6. Source hashes match the frozen run snapshot.

## Selected strong-scaling measurements

These figures use Cartesian decomposition, blocking halos and standard CG.
`S(P)=T_MPI(1)/T_MPI(P)` and `E(P)=S(P)/P`; the reference is the same MPI
implementation on one physical core. Minima are across three samples.

| Dimension / mesh | MPI cores | Solve (s) | Speedup | Efficiency |
| --- | ---: | ---: | ---: | ---: |
| 2D n=2048 | 1 | 117.1827 | 1.00 | 100% |
| 2D n=2048 | 256 | 2.193631 | 53.42 | 20.87% |
| 2D n=2048 | 288 | 2.235047 | 52.43 | 18.20% |
| 3D n=288 | 1 | 146.6325 | 1.00 | 100% |
| 3D n=288 | 256 | 1.064990 | 137.68 | 53.78% |
| 3D n=288 | 288 | 1.060742 | 138.24 | 48.00% |

The 256-core Cartesian groups have appreciable variability: CV is 26.25% in
2D and 10.55% in 3D. Use their retained medians/ranges when interpreting small
differences. The 288-core 3D minimum is only about 0.4% below the 256-core
minimum, so this run does not demonstrate a robust improvement from that
increase. Two-dimensional scaling is non-monotonic; for example, 64-core
Cartesian time is 1.266300 s. Its superlinear speedup alone does not establish
a cause such as cache effects; this needs further analysis in task 4.

## Documented failure and pending supplement

The CPU job's **actual PBS exit status is 1**. After completing the 92 groups,
the driver reached 3D weak scaling at 256 ranks and raised `KeyError: (3, 203)`:
the formula `round(32*cbrt(256))` gives 203, while the original serial reference
list incorrectly contained 202. No 256-rank 3D weak sample was accepted.
The failure occurred in reference lookup, after the earlier groups had been
written and validated. An explicit partial-audit mode preserves those groups
without declaring the whole job successful.

The corrected driver derives serial sizes from the weak-scaling formula.
Its `weak3d` suite runs serial references and all five 3D weak points in one
new allocation. At 256 ranks, n=203 gives 32677.449 points/core, 0.276% below
the nominal 32768; report this rounding. Whole-solve weak-scaling time also
includes increasing CG iteration counts, so retain seconds/iteration too.

The latest GPU attempt, `1533509.stdct-mgmt-02`, exited 1 at the mandatory
two-rank device-pointer smoke test. Its records showed the remote rank lacked
`PCG_SMOKE_DEVICE_MPI` and followed a different collective path. Explicit
`mpiexec -x` exports for that flag, visible-GPU checks, and halo transport are
now added, but await execution. Earlier link/remote-launch/UCX failures and
cancelled attempts remain raw evidence; none count as runtime results.
The GPU plan is 1/2 GPUs on different hosts, staged/device-pointer modes,
with preflight serial comparisons before timings. The inspected queue allowed
at most two GPUs per job. Device-pointer MPI on the selected UCX TCP path
does not imply GPUDirect RDMA.

## Artifacts and next action

The accepted CSVs, original manifest, audit and archive hashes are in
[`results/benchmarks/step3`](../results/benchmarks/step3/README.md).
The original archive and frozen source/logs are preserved locally and on
Vanda, outside Git. Reproduction and the exact supplement commands are in
[`scripts/vanda/STEP3.md`](../scripts/vanda/STEP3.md#current-dataset-and-recovery).
After PBS recovers, submit the CPU supplement and GPU suite, archive their
final scheduler records, and audit both before claiming task 3 complete.
Task 4's collector and CPU figures are now available in
[`analysis_step4.md`](analysis_step4.md), with these measurement gaps retained.
