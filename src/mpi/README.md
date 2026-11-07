# src/mpi/ (owner: A)

Pure MPI CG. Variants selected at run time:

- `--decomp slab|cart`: 1D slabs vs `MPI_Cart_create` 2D/3D blocks
- `--halo block|overlap`: `MPI_Sendrecv` vs `MPI_Isend/Irecv` overlapped with interior points
- `--cg std|pipe`: two `MPI_Allreduce` per iteration vs one (Chronopoulos-Gear)
