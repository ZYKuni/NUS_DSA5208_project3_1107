# src/hybrid_omp/ (owner: B)

MPI + OpenMP. `OmpBackend` derives from `MpiBackend` (src/mpi) and overrides only the compute
kernels (stencil, local dot products, vector updates) with `#pragma omp parallel for` loops.
Decomposition, halo exchange, reductions and both CG variants are inherited, so `poisson_omp`
accepts every option of `poisson_mpi` (`--decomp`, `--halo`, `--cg`).

- `MPI_THREAD_FUNNELED`: all MPI calls happen on the master thread, outside parallel regions.
- The stencil distributes (z, y) rows over threads with `collapse(2)`; the contiguous x loop
  stays inside one thread so it vectorises.
- Pin threads: Open MPI binds each rank to ONE core by default when np <= 2, which puts all
  threads of a rank on that core. Use `--map-by ppr:R:node:PE=T --bind-to core` (as in
  `scripts/vanda/hybrid_omp.pbs`) or `--bind-to none` for quick local runs.

`domain.hpp` and `local.hpp` hold the tile layout used by the MPI+CUDA solver (src/hybrid_cuda).

Validation: `ctest` runs `test_omp` (the MPI test against the serial solver, 2 threads per
rank). The end-to-end script compares the binary with `poisson_serial`:

```sh
python3 src/hybrid_omp/checks/validate.py build/bin/poisson_omp
```
