# src/hybrid_omp/ (owner: B)

MPI + OpenMP. One parallel region per CG iteration, `MPI_THREAD_FUNNELED`, communication by the master thread.

The baseline implements standard CG and blocking exchange for slab and Cartesian partitions.
The shared hybrid domain is provisional until A publishes the MPI solver interface.
Run the small-grid correctness sweep from the repository root:

```sh
python3 src/hybrid_omp/checks/validate.py build/bin/poisson_omp
```

It covers 2D/3D, n=15/31, one rank and four ranks, and checks the analytical discrete error.
