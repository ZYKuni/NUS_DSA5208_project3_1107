## 4. MPI + X design

Both hybrid solvers distribute the interior grid over a nonperiodic MPI Cartesian
communicator. Slab mode splits the slowest axis. Cartesian mode uses MPI_Dims_create.
Each axis distributes remainder points to its lowest coordinates. A one-cell ghost
layer stores neighbouring values of the CG search direction. Physical boundary
ghosts remain zero. The baseline uses standard CG with blocking exchange and two
global scalar sums per iteration.

The CPU version reuses the pure MPI backend and replaces only its compute kernels.
Decomposition, halo exchange (blocking or overlapped), reductions and both CG
variants are therefore identical to the MPI solver. Each kernel is an OpenMP
parallel loop: the stencil distributes grid rows over threads and keeps the
contiguous x loop inside a thread for vectorisation, and the dot products use an
OpenMP reduction before the MPI sum. The primary thread alone issues MPI calls,
outside parallel regions, under MPI_THREAD_FUNNELED. At fixed core count,
increasing threads per rank changes both the number of MPI participants and the
surface area of each partition.

The GPU version assigns one device to each rank. The solution, residual, operator
output and ghosted search direction remain on the device throughout the solve.
A grid-stride kernel applies the five- or seven-point stencil. A shared-memory tree
reduces each thread block's dot product and a second kernel sums the partials.
One scalar passes to host memory for each global sum. A separate kernel packs
strided faces into contiguous device buffers. CUDA-aware MPI accepts those device
pointers directly. The staged path copies outgoing faces to host memory and
received faces back to the device. Both paths unpack the received face into
ghost cells. Timers synchronize device work before closing each phase.

## 8. Hybrid and GPU results

Local correctness checks used n=15 and n=31, halving the spacing on refinement,
with the manufactured solution of Section 1. The OpenMP solver matched the serial
solver's iteration count and discrete L2 error (relative tolerance 1e-6) for one
and several ranks, slab and Cartesian partitions, in both dimensions, and every
grid point matched the serial solution to rounding error (test_omp). The
coarse-to-fine error ratio was 3.999. The independent Vanda CUDA pilot is described below.


### Fixed-core OpenMP experiment

Vanda job 1533443 used four 72-core hosts, Cartesian partitions, blocking halo
exchange and standard CG. Each entry is the shortest complete solve of three
independent launches following one warmup. The meshes required 6,512 iterations
in 2D and 1,109 in 3D for every split. The run used shared memory and TCP for MPI.
The 36 hybrid samples passed the per-group audit before the job later stopped
in a separate weak-scaling experiment.

| MPI ranks × threads per rank | 2D, 2048² (s) | 3D, 288³ (s) |
| --- | ---: | ---: |
| Pure MPI, 288 ranks | 2.235 | 1.061 |
| 288 × 1 | 2.290 | 1.078 |
| 144 × 2 | 3.527 | 1.304 |
| 72 × 4 | 3.516 | 1.379 |
| 32 × 9 | 2.635 | 1.764 |
| 16 × 18 | 2.504 | 2.153 |
| 4 × 72 | 2.678 | 2.653 |

Among the six hybrid splits, 288 × 1 gave the lowest minimum and median in both
dimensions. Pure MPI's minimum was slightly lower in each case. The difference
between pure MPI and the one-thread OpenMP build is small relative to the
observed repeat ranges, especially in 2D (288 × 1 ranged from 2.290 to 3.128 s).

The best multi-threaded split depended on dimension. In 2D, 16 × 18 took
2.504 s; in 3D, 144 × 2 took 1.304 s. The 3D phase measurements help explain
why further reducing the rank count did not improve elapsed time. Between
288 × 1 and 4 × 72, the reduction-phase maximum fell from 0.704 to 0.533 s,
while the halo-phase maximum rose from 0.431 to 1.667 s and the stencil/vector
maximum from 0.337 to 0.729 s. The larger halo time includes waiting for
neighbours. These maxima can come from different ranks and cannot be added
to reconstruct wall time. [Matched results and repeat ranges](../results/tables/hybrid_comparison.csv) · [Allocation and audit](scaling_step3.md)

### GPU correctness and formal scaling measurements

On Vanda, single-GPU job 1532562 passed the independent stencil and dot checks.
All six mesh sizes agreed with the serial reference in iteration count and
reported discrete L2 error across three launches each. At 511², CUDA needed
1,557 iterations and its maximum recomputed relative residual was 9.693 × 10⁻⁹;
at 95³ the corresponding values were 350 and 9.797 × 10⁻⁹. A single rank has no
neighbour to exchange with. Its short pilot times are used for workload sizing.
[CUDA and serial pilot summaries](../results/validation/step2/vanda_cuda_summary.csv)

The initial two-host attempt 1533509 stopped because a device-test flag did
not reach the remote rank. Explicit MPI environment exports fixed that probe.
Attempt 1540133 then passed the probe and expanded GPU face checks but stopped
at an excluded warmup because the recursive stopping target and true-residual
exit threshold had both been set to 5e-9. The accepted experiment requires true
residual <1e-8. The successful retry uses a 5e-9 recursive target separately
from the executable's strict 1e-8 true-residual acceptance.

Attempt 1540688 later completed the large 2D cases but its 3D serial
reference received SIGKILL without an explicit host-memory reservation.
The final retry requested 16 GB host memory per host.

Formal job 1540912 passed the complete audit on GN-A40-028 and GN-A40-006,
using one NVIDIA A40 per rank and host. All ten preflight groups passed before
large-mesh timing. Each formal configuration has one excluded warmup and three
independent measured launches, checked against the same-mesh serial reference.

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

Speedup and GPU efficiency use the same job, mesh and transport at one GPU.
The device-pointer path uses CUDA-aware MPI over the selected UCX TCP path,
which may stage internally; no GPUDirect RDMA claim follows from passing a
device pointer. The shared hosts, observed repeat ranges and only two GPU
counts limit inference. See the [traceable GPU table](../results/tables/gpu_scaling.csv),
[full allocation and audit](scaling_step3.md), and [GPU figures](../results/figures/README.md).
