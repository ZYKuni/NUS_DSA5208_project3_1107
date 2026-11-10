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

### GPU correctness and outstanding scaling measurements

On Vanda, single-GPU job 1532562 passed the independent stencil and dot checks.
All six mesh sizes agreed with the serial reference in iteration count and
reported discrete L2 error across three launches each. At 511², CUDA needed
1,557 iterations and its maximum recomputed relative residual was 9.693 × 10⁻⁹;
at 95³ the corresponding values were 350 and 9.797 × 10⁻⁹. A single rank has no
neighbour to exchange with. Its short pilot times are used for workload sizing.
[CUDA and serial pilot summaries](../results/validation/step2/vanda_cuda_summary.csv)

The two-host GPU attempt (job 1533509) stopped at the device-pointer MPI
preflight. The remote rank was missing an environment flag. C's updated launcher
exports that flag and the halo transport choice explicitly. The queue permits
two GPUs per job. The remaining experiment compares one versus two GPUs at
2048² and 256³ with each transport, then compares device-pointer MPI against
host staging at the same two-GPU placement. Each configuration needs a passing
small-mesh comparison and three measured solves after warmup. GPU scaling and
the benefit of direct exchange remain open until those samples pass audit.
[GPU run and audit procedure](../scripts/vanda/STEP3.md#current-dataset-and-recovery)
