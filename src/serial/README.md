# src/serial/ (owner: A)

Serial matrix-free CG for 2D and 3D. Reference for all validation.

`SerialBackend` implements `pcg::Backend` (`include/cg.hpp`) on one `pcg::Block` covering the
whole grid. Boundary ghosts stay 0 (Dirichlet), so `apply()` is a single stencil sweep.
Both CG variants (`--cg std|pipe`) run serially as well, which is how the single-reduction
variant is validated without MPI.
