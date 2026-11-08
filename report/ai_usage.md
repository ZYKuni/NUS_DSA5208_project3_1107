# AI usage log

Each member records their own AI use here. The final report's AI section is compiled from this file.
For each entry: date, tool, what it was used for, which files or text came from it, how it was checked.

## Yikun Zhao

- 2026-11-07, Claude: read lecture slides and proposed the project plan, division of work and
  repository skeleton (README, CMakeLists.txt, shared headers, job and plotting scripts).
  Reviewed and adapted by the team.
- 2026-11-08, Claude: drafted the serial and MPI CG code (`include/grid.hpp`, `include/cg.hpp`,
  `src/common/grid.cpp`, `src/common/cg.cpp`, `src/serial/`, `src/mpi/`, `apps/poisson_serial.cpp`,
  `apps/poisson_mpi.cpp`) and the validation tests (`tests/test_serial.cpp`, `tests/test_mpi.cpp`).
  It also flagged that the original manufactured solution Π sin(π x_k) is a discrete eigenvector
  (CG converged in one iteration) and replaced it. Checked by running the tests on 1, 3, 4, 6 and
  8 MPI ranks and by reviewing the code.

## Jiahao Zhou

## Zheke Chen
