# Cluster access and toolchain probes

These jobs validate the cluster toolchain independently of the Poisson solvers.
They do not produce algorithm runtime or scaling results.

Use `place=scatter` for the four-node CPU probe: four PBS chunks with the default
`place=free` can land on a single physical host. Select a resource pool explicitly.
On 2026-11-08, the GPU-bearing `gpu_node` pool was fully busy or offline. The
`cpu_node` pool also advertised A40 GPUs, and a normal `auto` submission with
`ngpus=1:node_pool=cpu_node` was accepted into `batch_gpu` and allocated an A40.
The probe uses this verified resource request; it still reserves a GPU and charges
the project normally. Recheck availability before later runs.

The HPC-X build has no PBS/TM component: it initially saw only the launch host.
Passing a hostfile reached the remote hosts but then failed CPU binding in the
partial-core allocation. The successful CPU probe instead uses
`openmpi/gcc/64/4.1.8`, `ucx/1.10.1`, and `/opt/pbs/lib` in `LD_LIBRARY_PATH`,
with explicit `--mca ras tm --mca plm tm`. PBS/TM launches tasks inside the
allocation. `--bind-to none` avoids rebinding the rank to global core numbers;
OpenMP uses `OMP_PLACES=cores`, `OMP_PROC_BIND=close`, and two threads.
Do not interpret this small probe as a full performance-affinity study.

From the repository root on Vanda, submit with your own project:

```bash
qsub -P YOUR_PROJECT scripts/vanda/smoke_cpu.pbs
qsub -P YOUR_PROJECT scripts/vanda/smoke_gpu.pbs
```

The CPU job builds on a compute node, runs the common tests, then starts one MPI
rank on each of four nodes, with two OpenMP threads per rank. It checks the thread
count, distinct sampled Linux CPU IDs per rank, global reduction, and four distinct
hostnames. Launcher binding output and `lscpu` are retained for inspection; the
sampled CPU IDs alone are not a proof of complete physical-core affinity.

The GPU job requests the 36 CPU / 1 GPU ratio shown by `hpc gpu`, detects the
allocated GPU's compute capability, compiles a CUDA kernel, and checks every
returned value. One-rank success does not establish CUDA-aware inter-rank MPI.
The GPU probe offers an explicit two-rank device-buffer check through
`PCG_SMOKE_DEVICE_MPI=1`; it is not enabled in the one-GPU job.

Success requires job exit status zero **and** `CPU_SMOKE=PASS` /
`GPU_SMOKE=PASS` plus the matching `STEP1_*_COMPLETE` marker. Inspect PBS records
for the actual allocation. Evidence stays in ignored `results/raw/step1-*` and
must be excluded from the final submission archive.

The shared environment defaults to CMake/3.26.3-GCCcore-12.3.0 and
nvhpc-hpcx-cuda12/26.1; the latter was validated for the single-GPU job.
The CPU script overrides `PCG_MPI_MODULE` as described above. Do not reuse the
HPC-X default for fractional multi-node CPU allocations without resolving PBS
launch and affinity. A listed module alone does not establish runtime success.

Completed on 2026-11-08 (Singapore time):

| Probe | PBS job | Result |
| --- | --- | --- |
| Four-node MPI/OpenMP | 1532513.stdct-mgmt-02 | Exit 0; four ranks, four hosts, two threads per rank; sum 200040000 |
| One-GPU MPI/CUDA | 1532497.stdct-mgmt-02 | Exit 0; NVIDIA A40, compute capability 8.6; kernel values verified |

Earlier failed/cancelled attempts are retained in internal evidence. No Poisson
solver benchmark, GPU transport comparison, or scaling study is included here.
