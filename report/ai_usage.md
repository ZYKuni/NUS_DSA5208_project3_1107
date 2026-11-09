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

- 2026-11-08, OpenAI Codex: reviewed every remote branch, integrated A's latest
  serial/MPI/OpenMP work into c/bench, added the workload checker and PBS pilots,
  and added CUDA true-residual validation. The non-eigenmode manufactured problem
  was supplied by A's upstream change. Checks include the existing seven CTest
  groups, independent repeated serial/parallel comparisons, and Vanda jobs; exact
  accepted results and limitations are recorded in report/workload_step2.md.

- 2026-11-08, OpenAI Codex: prepared task 3's CPU/GPU experiment drivers,
  physical-core pinning and evidence audit; moved the shared CPU timer inside
  CG to exclude setup; corrected the CUDA-only probe's MPI wrapper link; and
  added a regression check for the PBS remote-launch command protocol. The local
  seven-group CTest run and launcher regression passed. Cluster completion and
  accepted measurement counts must be taken from the audited task 3 evidence;
  submitted, failed and cancelled attempts are not accepted results.

- 2026-11-09, OpenAI Codex: audited the 92 completed CPU groups (276 samples),
  documented the actual nonzero job exit, corrected the missing n=203 serial
  reference, prepared a complete 3D weak-curve supplement, and added explicit
  GPU environment exports after inspecting the failed smoke test. Added two
  weak-mesh regression tests; all three script tests passed. Drafted
  `report/scaling_step3.md` and the accepted-data provenance. PBS refused
  submissions on this date; neither the supplement nor the GPU fix has been
  validated on the cluster, and task 3 remains incomplete.

- 2026-11-09, OpenAI Codex: completed task 4's CPU collector and plotting
  scripts, explicit audited-input selection, matched strong/weak/variant/hybrid
  baselines, repeat statistics, checksum manifests, report tables, 12 figures
  and the CPU results discussion. Excluded eight preflight groups without
  removing measured outliers; retained 84 groups / 252 samples and the missing
  3D weak/GPU status. Added 12 regression tests covering incorrect baselines,
  altered exports, missing repeats and failed convergence; all passed.
  Independently checked output metrics against the accepted CSVs and rendered
  every page of the exported PDF book for visual inspection. The text and
  figures describe observations and limitations; they do not invent missing
  GPU results or claim unmeasured causes of performance changes.
