# apps/

One `main()` per executable. CMake builds a target only once its file exists.

| File | Target | Owner |
| --- | --- | --- |
| `poisson_serial.cpp` | `poisson_serial` | A |
| `poisson_mpi.cpp` | `poisson_mpi` | A |
| `poisson_omp.cpp` | `poisson_omp` | B |
| `poisson_cuda.cpp` | `poisson_cuda` | B |

Every main must: call `pcg::parse_args`, run the solve `--repeat` times keeping the fastest,
fill a `pcg::Result`, print it, and call `pcg::csv_append` on rank 0 when `--csv` is given.
