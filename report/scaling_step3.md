# Task 3: scaling measurements and completion status

**Status, 11 November 2026:** the CPU matrix is complete, with strong scaling
through 288 cores and weak scaling through 256 cores in both dimensions.
GPU job `1540912.stdct-mgmt-02` also passed the complete independent audit,
covering both planned meshes and transports on one and two GPUs. Earlier submission
attempts were refused on November 9; an explicit urgent-maintenance notice
appeared on November 10. Login and PBS scheduling recovered on November 11.

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

## Completed 3D weak-scaling repair

Job `1540132.stdct-mgmt-02` ran on November 11, 14:13–14:22 Singapore,
on CN-133, CN-136, CN-137 and CN-139 (four exclusive 72-core Xeon Platinum
8452Y hosts). PBS exit status is **0** and all ten groups / 30 samples passed
the independent audit. Maximum true relative residual is 4.976624e-9; rank
placement and serial comparisons passed. Numerical source and serial/MPI/OpenMP
binary hashes are identical to the first CPU run.

The entire 3D weak curve comes from this single replacement allocation:

| MPI cores | n | CG iterations | Minimum (s) | Median (s) |
| --- | ---: | ---: | ---: | ---: |
| 1 | 32 | 119 | 0.007251792 | 0.007360886 |
| 8 | 64 | 241 | 0.03774247 | 0.03791845 |
| 64 | 128 | 485 | 0.09329851 | 0.09382242 |
| 216 | 192 | 734 | 0.4915792 | 0.5122607 |
| 256 | 203 | 775 | 0.4645508 | 0.5308163 |

The 256-core point uses 32677.449 unknowns/core, 0.276% below the base load
because of integer mesh rounding. Its CV is 12.60%; the lower minimum at
256 than at 216 cores does not establish a robust improvement, since the
median ordering is reversed.

`cpu_combined_*` assembles **93 CPU groups / 279 samples**, retaining eight
preflight groups as validation evidence. It replaces the original four 3D
weak groups and unused serial n=202 group, and keeps the new n=203 reference.
The repair's other four serial references remain in its original export.
The assembly manifest preserves the first job's actual exit status 1 and
does not invent a successful single PBS run.

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

## Completed GPU measurements

Job `1540912.stdct-mgmt-02` used one A40 GPU on each of GN-A40-028 and
GN-A40-006, with one rank per host. It ran on November 11, 16:27-16:47 Singapore
(recorded walltime 00:20:04), with 16 GB host memory per host. PBS exited zero. The independent audit
accepted all **20 groups / 60 samples**: ten small-mesh preflight groups,
two serial-reference groups and eight formal CUDA configurations. The build
passed all seven CTest groups; B's expanded stencil/dot/halo-face checks and
the two-host device-pointer MPI probe passed before workload measurements.
Every sample passed true residual <1e-8 and same-mesh serial iteration/error
agreement. The source hashes match the frozen successful-run snapshot.

| Mesh | Transport | GPUs | Min (s) | Median (s) | CV | Speedup | GPU efficiency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2D n=2048 | device | 1 | 6.215259 | 6.218436 | 0.05% | 1.000 | 100.00% |
| 2D n=2048 | device | 2 | 5.069166 | 5.226168 | 2.08% | 1.226 | 61.30% |
| 2D n=2048 | staged | 1 | 6.213837 | 6.217811 | 0.06% | 1.000 | 100.00% |
| 2D n=2048 | staged | 2 | 4.358878 | 4.369072 | 11.89% | 1.426 | 71.28% |
| 3D n=256 | device | 1 | 4.238899 | 4.239031 | 0.02% | 1.000 | 100.00% |
| 3D n=256 | device | 2 | 2.983993 | 2.987092 | 0.29% | 1.421 | 71.03% |
| 3D n=256 | staged | 1 | 4.238452 | 4.239921 | 0.02% | 1.000 | 100.00% |
| 3D n=256 | staged | 2 | 2.860062 | 2.867455 | 1.77% | 1.482 | 74.10% |

Each transport uses its own one-GPU baseline within this allocation. Hosts
are shared, and three repeats provide descriptive ranges rather than confidence
intervals. Device-pointer MPI on UCX's selected TCP path may stage internally;
these results do not establish GPUDirect RDMA. No scaling beyond two GPUs or
CPU-core/GPU efficiency conversion is claimed. The traceable GPU table retains
all medians, ranges, CV, phase values and group IDs.

## Documented failed attempts

The CPU job's **actual PBS exit status is 1**. After completing the 92 groups,
the driver reached 3D weak scaling at 256 ranks and raised `KeyError: (3, 203)`:
the formula `round(32*cbrt(256))` gives 203, while the original serial reference
list incorrectly contained 202. No 256-rank 3D weak sample was accepted.
The failure occurred in reference lookup, after the earlier groups had been
written and validated. An explicit partial-audit mode preserves those groups
without declaring the whole job successful.

The corrected driver derives serial sizes from the weak-scaling formula.
The successful `weak3d` repair above supplies all five points and their serial
references. Whole-solve weak-scaling time includes increasing CG iteration
counts, so the analysis retains seconds/iteration too.

An earlier GPU attempt, `1533509.stdct-mgmt-02`, exited 1 at the mandatory
two-rank device-pointer smoke test. Its records showed the remote rank lacked
`PCG_SMOKE_DEVICE_MPI` and followed a different collective path. Explicit
`mpiexec -x` exports for that flag, visible-GPU checks, and halo transport are
now added and passed execution in job `1540133.stdct-mgmt-02`. Earlier link/remote-launch/UCX failures and
cancelled attempts remain raw evidence; none count as runtime results.
That job also passed B's expanded GPU stencil, dot and halo-face checks and
all ten small-mesh preflight groups. It then exited at the 2D n=2048 warmup:
the recomputed true residual was 5.582144e-9, below the experiment's 1e-8
accuracy threshold but above the executable's then-configured 5e-9 threshold.
The fix preserves strict true-residual exit validation with `--tol 1e-8` and
sets the recursive target separately with `PCG_CUDA_STOP_TOL=5e-9` on every
rank. Serial references still stop at 5e-9. The failed warmup remains excluded
from performance data. The next attempt, `1540688.stdct-mgmt-02`, passed all four large 2D GPU
configurations and their serial reference, then exited 1 when its 3D n=256
serial-reference warmup received SIGKILL. No host memory had been explicitly
requested in that allocation. The kill is consistent with a memory limit;
no numerical-check failure was reported. Retry `1540912.stdct-mgmt-02`
requests 16 GB host memory per GPU host, with the same numerical binaries,
recursive target and accuracy checks. The full rerun passed; the
previous attempt remains excluded raw evidence.

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
The CPU supplement and GPU retry archives, final scheduler records and
successful audits are preserved. The planned task 3 matrix is complete.
Task 4 now incorporates **95 selected groups / 285 samples** in 14 figures
and the discussion in [`analysis_step4.md`](analysis_step4.md). Task 5 has
not been started.
