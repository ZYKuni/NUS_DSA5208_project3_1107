# AI usage log

Each member records their own AI use here. The final report's AI section is compiled from this file.
For each entry: date, tool, what it was used for, which files or text came from it, how it was checked.

## Yikun Zhao

- 2026-11-07, Claude: read lecture slides and proposed the project plan, division of work and
  repository skeleton (README, CMakeLists.txt, shared headers, job and plotting scripts).
  Reviewed and adapted by the team.

## Jiahao Zhou

## Zheke Chen

- 2026-11-08, OpenAI Codex: inspected current branches and prepared standalone
  MPI/OpenMP and CUDA cluster probes, CMake/build integration, PBS scripts and
  environment documentation. Local Linux CPU build, common CTest and a two-rank
  CPU probe passed. Vanda CPU job 1532513 and GPU job 1532497 then completed with
  exit status zero and the expected arithmetic checks. Earlier failed/cancelled
  attempts were retained. These probes do not validate the Poisson solvers or
  establish scaling performance. Human review remains required.
