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
coarse-to-fine error ratio was 3.999. The CUDA checks use the same script on a
GPU node.

Cluster results await C's measurements. For the fixed-core experiment compare
the fastest of three repeats per rank/thread split at the same global size.
Report total time and maximum-rank stencil, halo and reduction times. These maxima
can occur on different ranks. For each GPU transport, compare 1, 2 and 4 GPUs at
fixed size and report speedup relative to its one-GPU time. Compare transport
times at equal GPU counts of at least two. Record placement, hardware, compiler,
MPI build and CUDA version with C's CSVs before attributing a timing difference
to communication.
