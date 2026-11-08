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
- 2026-11-08, Claude: reviewed branch b/hybrid, rewrote the MPI+OpenMP solver as `OmpBackend`
  on top of the MPI backend (`src/hybrid_omp/omp_backend.*`, `apps/poisson_omp.cpp`), added
  `test_omp`, and updated `src/hybrid_omp/checks/validate.py` and report/hybrid.md for the new
  manufactured solution. Checked with ctest and by timing against the pure MPI solver.

## Jiahao Zhou

- 2026-11-07, OpenAI Codex: generated the hybrid CPU/GPU solvers, validation drivers,
  and draft sections 4 and 8. The OpenMP results were checked against the discrete
  sine-mode solution. CUDA sources were compiled with NVIDIA nvcc; GPU execution
  and team review are pending.

## Zheke Chen

- 2026-11-08, OpenAI Codex: inspected current branches and prepared standalone
  MPI/OpenMP and CUDA cluster probes, CMake/build integration, PBS scripts and
  environment documentation. Local Linux CPU build, common CTest and a two-rank
  CPU probe passed. Vanda CPU job 1532513 and GPU job 1532497 then completed with
  exit status zero and the expected arithmetic checks. Earlier failed/cancelled
  attempts were retained. These probes do not validate the Poisson solvers or
  establish scaling performance. Human review remains required.
