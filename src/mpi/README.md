# src/mpi/ (owner: A)

Pure MPI CG. Built as the library `pcg_mpi`, which the hybrid versions also link.

| File | Content |
| --- | --- |
| `decomp.hpp/.cpp` | `make_decomp`: `MPI_Cart_create` communicator, neighbours, local `Block` |
| `halo.hpp/.cpp` | `Halo`: face exchange with `MPI_Type_create_subarray` datatypes |
| `mpi_backend.hpp/.cpp` | `MpiBackend`: the `pcg::Backend` used by `poisson_mpi` |

Variants selected at run time:

- `--decomp slab|cart`: 1D slabs along the slowest axis vs `MPI_Dims_create` 2D/3D blocks
- `--halo block|overlap`: `MPI_Sendrecv` before the stencil vs `MPI_Isend/Irecv`, stencil on the
  interior while messages are in flight, `MPI_Waitall`, then the boundary shell
- `--cg std|pipe`: two `MPI_Allreduce` per iteration vs one (Chronopoulos-Gear)

Hybrid backends derive from `MpiBackend` and override the virtual compute kernels
(`stencil`, `local_dot_hook`, `local_dot2_hook`, `axpy`, `xpay`, `copy`, `zero`).
