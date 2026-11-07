## 4. MPI + X design

Both hybrid solvers distribute the interior grid over a nonperiodic MPI Cartesian
communicator. Slab mode splits the slowest axis. Cartesian mode uses MPI_Dims_create.
Each axis distributes remainder points to its lowest coordinates. A one-cell ghost
layer stores neighbouring values of the CG search direction. Physical boundary
ghosts remain zero. The baseline uses standard CG with blocking exchange and two
global scalar sums per iteration.

The CPU version enters one OpenMP parallel region per iteration. The primary
thread alone issues MPI calls under MPI_THREAD_FUNNELED. Threads share the
stencil and vector updates by static work sharing and compute thread-local
dot products before the MPI sum. Rank boundaries exchange strided faces using MPI
subarray datatypes. At fixed core count, increasing threads per rank changes
both the number of MPI participants and the surface area of each partition.

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

Local correctness checks used n=15 and n=31, halving the spacing on refinement.
The discrete sine mode has eigenvalue 4d sin²(πh/2)/h². Its sampled solution is
therefore scaled by (πh/(2 sin(πh/2)))². The measured OpenMP error agreed with
the resulting discrete L2 error within relative tolerance 1e−6 in both dimensions.
The coarse-to-fine error ratio was 4.00579. This right-hand side is a single
eigenmode, so a small-grid solve commonly takes one iteration. Report the actual
iteration count beside each timing, especially when interpreting short runs.

Cluster results await C's measurements. For the fixed-core experiment compare
the fastest of three repeats per rank/thread split at the same global size.
Report total time and maximum-rank stencil, halo and reduction times. These maxima
can occur on different ranks. For each GPU transport, compare 1, 2 and 4 GPUs at
fixed size and report speedup relative to its one-GPU time. Compare transport
times at equal GPU counts of at least two. Record placement, hardware, compiler,
MPI build and CUDA version with C's CSVs before attributing a timing difference
to communication.
