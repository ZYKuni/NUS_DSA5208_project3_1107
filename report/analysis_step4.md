# Task 4: CPU result analysis and report figures

Task 4 is updated for the completed CPU matrix: reproducible collection,
derived metrics and report tables. The full 3D weak curve now reaches 256
cores. GPU measurements are pending the complete audit of retry `1540912`.

## Dataset and measurement conventions

The sources are the independently audited completed portion of Vanda job
`1533443.stdct-mgmt-02` (actual exit status 1, missing-reference failure),
and successful CPU repair `1540132.stdct-mgmt-02` (exit zero). The assembly
replaces the entire original 3D weak curve and unused n=202 reference, and
retains duplicate repair references in the original export only. Of the
assembled 93 CPU groups / 279 samples, eight preflight groups / 24 samples
are excluded from performance analysis. The remaining **85 groups / 255 samples** comprise
11 serial, 40 strong, ten weak, 12 MPI-choice and 12 hybrid configurations.
There is one excluded warmup and three separate measured processes per group.
All 255 retained CPU samples pass true residual <1e-8 and the same-mesh serial
iteration/error checks. Failed/cancelled jobs and raw logs are not inputs.

Timings cover the CG loop, including the end barrier, excluding setup,
allocation, validation and process launch. The primary statistic is the minimum
complete sample; medians, observed ranges and population CV remain visible.
There are only three repeats, so the ranges are descriptive, not confidence
intervals or significance tests. Subsecond configurations remain in the dataset
with a duration flag; their short timings limit precision.

The environment is four exclusive 72-core Vanda CPU hosts, NVIDIA HPC SDK
26.1, HPC-X/Open MPI, and explicit TCP/shared-memory point-to-point transports.
Full environment, placement, validation and archive provenance are in
[`scaling_step3.md`](scaling_step3.md). These results do not measure RDMA.

## Serial scaling and numerical validation

[Figures 1 and 2](../results/figures/README.md) show runtime, iteration growth
and discretization error. In 2D, n=128 to 2048 increases unknowns from 16384 to
4194304 and iterations from 392 to 6512; minimum runtime grows from 0.01471 s
to 117.2551 s. In 3D, n=32 to 288 increases unknowns from 32768 to 23887872,
iterations from 119 to 1109, and minimum runtime from 0.01134 s to 144.6353 s.
Whole-solve runtime includes this convergence growth; it is not simply the
cost of one stencil pass.

Adjacent-mesh discrete L2 error orders are approximately 2.00 in both
dimensions, consistent with second-order spatial accuracy. The h-squared
reference lines are anchored at the coarsest mesh rather than fitted to the
measurements. This discretization check complements the independent true
residual and serial/parallel agreement checks. The serial n=203 reference is
from the repair allocation; other serial curve points come from the original
allocation. Both use identical numerical source and CPU binary hashes. The
unused n=202 reference remains in the original export, outside this assembly.

## Strong scaling and decomposition

Figures 3 and 5 compare slab and Cartesian decomposition. Each curve uses its
**own one-rank MPI baseline**: `S(P)=T_MPI(1)/T_MPI(P)` and `E(P)=S(P)/P`.
This avoids mixing serial, preflight or weak-scaling baselines.

| Mesh / decomposition | Cores | Min (s) | Median (s) | Min-based speedup | Efficiency |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2D n=2048 / cart | 64 | 1.266300 | 1.294931 | 92.54 | 144.59% |
| 2D n=2048 / cart | 256 | 2.193631 | 2.234183 | 53.42 | 20.87% |
| 2D n=2048 / cart | 288 | 2.235047 | 2.241714 | 52.43 | 18.20% |
| 3D n=288 / cart | 256 | 1.064990 | 1.311154 | 137.68 | 53.78% |
| 3D n=288 / cart | 288 | 1.060742 | 1.066999 | 138.24 | 48.00% |
| 3D n=288 / slab | 256 | 5.464851 | 5.479364 | 26.82 | 10.48% |
| 3D n=288 / slab | 288 | 4.731633 | 4.803164 | 30.97 | 10.75% |

For the standard/blocking Cartesian 2D configuration, 64 cores is the fastest
tested count. Scaling is non-monotonic: 128 cores takes 2.814492 s, and the
256/288-core results remain slower than 64 cores. The observed superlinear
speedup at 64 cores is retained rather than clipped. Cache capacity, memory
bandwidth, placement and communication can affect scaling, but these timings
alone do not isolate the cause. The allocation uses one host through 64 ranks,
two at 128, and four at 256/288, which is relevant to the communication change.

Cartesian decomposition is substantially faster than slab for the large 3D
cases: at 256 cores its minimum is about 5.13 times faster. Figures 4 and 6
show lower Cartesian phase maxima in these cases, supporting a decomposition
effect without assigning a precise additive communication fraction.

The 3D Cartesian 288-core minimum improves over 256 cores by only 0.4%,
while its median is about 18.6% lower. The 256-core Cartesian groups have CV
26.25% (2D) and 10.55% (3D), and the 3D observed ranges overlap. Thus the
minimum alone understates variability, and three ordered repetitions do not
establish a statistically reliable 256-to-288-core improvement.

## Weak scaling and convergence growth

Figures 7 and 8 show two different quantities: whole-solve time and average
time per CG iteration. The measured meshes keep owned unknowns/core exactly
constant at 16384 in 2D. In 3D the base is 32768, with the rounded n=203
endpoint giving 32677.449 (-0.276%). Increasing n nevertheless increases
the number of unpreconditioned CG iterations.

| Dimension | Endpoint | Iterations at 1 / endpoint cores | Min endpoint (s) | Whole-solve T(1)/T(P) | Per-iteration cost ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2D | 256 cores | 392 / 6512 | 2.126299 | 0.435% | 7.22% |
| 3D | 256 cores | 119 / 775 | 0.464551 | 1.561% | 10.17% |

Even after normalising by iterations, the average iteration cost grows
substantially. Thus convergence growth alone does not explain the loss of
whole-solve weak scaling. The phase data show substantial reduction costs at
the larger configurations, but they cannot isolate network latency from all
other effects. In 2D at 256 cores, median runtime is 4.090440 s and CV is
27.30%, so the minimum-time ratio is an optimistic observed statistic.

The complete 3D curve uses only the repair allocation, including its one-core
MPI baseline. At 256 cores, median runtime is 0.530816 s and CV is 12.60%.
Its minimum is lower than the 216-core minimum (0.491579 s), but the median
ordering is reversed (216-core median 0.512261 s). This is not evidence of a
robust endpoint improvement. The slight points/core rounding is retained in
the tables rather than treating the 3D curve as exact constant work per core.

## Halo and CG choices

Figures 9 and 10 compare four choices at the same mesh and rank count.
The baseline is blocking halos with standard CG; `pipe` is single-reduction
Chronopoulos-Gear CG. It must not be described as an asynchronous pipelined
implementation.

| Mesh / ranks | Best tested choice by minimum | Min (s) | Matched baseline / choice |
| --- | --- | ---: | ---: |
| 2D n=2048 / 64 | Blocking / standard | 1.266300 | 1.00 |
| 2D n=2048 / 256 | Blocking / single-reduction | 1.424894 | 1.54 |
| 3D n=288 / 64 | Blocking / standard | 8.020275 | 1.00 |
| 3D n=288 / 256 | Overlap / standard | 0.854900 | 1.25 |

There is no universally fastest choice. At 64 ranks the additional vector
work in single-reduction CG does not pay off in the measured total times;
at 256 ranks it helps the 2D case. In the 3D 256-rank case overlap with
standard CG gives the lowest time, whereas single-reduction choices are
slower than standard/blocking. Lower reduction-phase maxima alone therefore
do not guarantee a faster solve. The timing observations are consistent with
these tradeoffs, but they do not independently measure each overhead's cause.

## MPI + OpenMP at fixed resources

Figures 11 and 12 compare 288x1, 144x2, 72x4, 32x9, 16x18 and 4x72
MPI ranks x OpenMP threads, always on 288 physical cores across four hosts.
The one-thread OpenMP backend gives the lowest minimum among the six hybrid
splits in both dimensions: 2.290007 s in 2D and 1.077616 s in 3D. Pure MPI
at 288 ranks is slightly faster at 2.235047 s and 1.060742 s respectively.

Every tested multi-thread split is slower than the pure-MPI baseline for
these meshes. For example, 4x72 takes 2.677803 s in 2D and 2.652749 s in 3D.
The data demonstrate that fewer MPI ranks plus more threads is not
automatically beneficial at fixed core count. Threading, NUMA and memory
effects are possible contributors, but assigning causality would require
additional profiling. The comparison is a same-resource runtime ratio, not
an OpenMP speedup curve or a claim that all OpenMP workloads scale poorly.

## Reproduction and limits

[`analysis/README.md`](../analysis/README.md) gives the complete commands,
input-selection rules and metric definitions. Machine-readable report tables
are under [`results/tables`](../results/tables/README.md). All figures are in
the [figure index and book](../results/figures/README.md). Sixteen regression
tests check baseline isolation, matching minima, missing repeats, altered
exports, convergence rejection, fixed-core arithmetic, GPU transport baselines
and the assembled CPU selection.

Phase maxima may occur on different ranks; their intervals can overlap. Their
sum/total diagnostic ranges up to about 1.59 in this dataset. Stacking those
values or labelling their sum a communication fraction would be misleading.
No failed GPU attempt is a runtime result, and no CPU/GPU speedup is claimed.
The GPU retry still needs a successful full audit before those results can
be incorporated.
