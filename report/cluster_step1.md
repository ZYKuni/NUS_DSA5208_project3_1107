# C task 1: cluster access and minimum jobs

Date: 2026-11-08, Asia/Singapore. Base repository revision: f101953.
Working branch: c/bench. The source was exported with a per-file SHA256 manifest;
it was not a clean remote Git checkout. Subsequent PBS-script corrections are
preserved separately in the internal evidence.

## Accepted results

| Item | Evidence |
| --- | --- |
| Routing queue | `auto`, routing to `batch_cpu` and `batch_gpu` |
| CPU allocation | Job 1532513.stdct-mgmt-02: CN-148, CN-149, CN-151, CN-152; 2 CPUs per host, 4 MPI ranks, 2 OpenMP threads per rank |
| CPU outcome | PBS exit 0; `CPU_SMOKE=PASS`; global sum 200040000; `STEP1_CPU_COMPLETE` |
| GPU allocation | Job 1532497.stdct-mgmt-02: GN-A40-057; 36 CPUs, 1 NVIDIA A40, compute capability 8.6, reported memory 46068 MiB |
| GPU outcome | PBS exit 0; `GPU_SMOKE=PASS`; `STEP1_GPU_COMPLETE` |
| Build location | Both probes were compiled on allocated compute nodes |

## Toolchains and deployment findings

- Both jobs used CMake/3.26.3-GCCcore-12.3.0.
- The successful CPU job used `openmpi/gcc/64/4.1.8`, `ucx/1.10.1`, and
  `/opt/pbs/lib` on `LD_LIBRARY_PATH`. Explicit MPI `ras=tm` and `plm=tm` enable
  PBS-native task launch. OpenMP used two threads, `OMP_DYNAMIC=FALSE`,
  `OMP_PLACES=cores`, and `OMP_PROC_BIND=close`.
- The GPU job used `nvhpc-hpcx-cuda12/26.1`; its log reports NVHPC 26.1,
  Open MPI 4.1.9a1 and CUDA compiler 12.9.86. The CUDA architecture was detected
  from the allocated A40 and passed as 86, rather than assuming an A100.
- `select=4` alone means four resource chunks. `place=scatter` was necessary to
  obtain four physical hosts.
- The HPC-X build lacked PBS/TM. A hostfile made it discover four hosts, but
  explicit global-core binding failed in the fractional allocation. The CPU
  probe therefore uses the PBS-capable MPI build and avoids an additional MPI
  global-core binding; the runtime arithmetic and thread checks passed.
- The dedicated GPU pool was busy/offline at inspection. PBS also advertised
  A40 GPUs in `cpu_node`. A normal `auto` request with
  `ngpus=1:node_pool=cpu_node` was accepted into `batch_gpu`; this is the tested
  request in the delivered GPU probe. Job submission used the user's own project.

## Retained attempts

| Job | Outcome |
| --- | --- |
| 1532486 | Exit 1; chunks placed on one host, launcher rejected four ranks with one rank per node |
| 1532487 | Queued GPU request without explicit pool; cancelled |
| 1532491 | Exit 1; four hosts allocated, HPC-X did not discover them automatically |
| 1532492 | GPU pool busy/offline; cancelled |
| 1532496 | Exit 131; hostfile reached four hosts but MPI global-core binding failed |

The successful CPU test checks four distinct hostnames, the requested thread
count, distinct sampled Linux CPU IDs within each rank, and an MPI global sum.
This is not an exhaustive physical-affinity study. The successful GPU test checks
a CUDA kernel and device-to-host results in one MPI rank; it does not validate
multi-GPU transport or CUDA-aware MPI.

No Poisson benchmark, serial/MPI correctness comparison, scaling experiment,
or task 2 work has been performed in this step. The main branch's missing solver
applications remain a separate dependency.

Usage and reusable scripts: `scripts/vanda/STEP1.md`. Internal raw evidence is
kept under ignored `results/raw/` and must not enter the final submission archive.
