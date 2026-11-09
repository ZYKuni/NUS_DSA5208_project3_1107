# Formal scaling runs

Submit from the repository root (all builds run on compute nodes):

```bash
qsub -P YOUR_PROJECT scripts/vanda/scaling_cpu.pbs
qsub -P YOUR_PROJECT scripts/vanda/scaling_gpu.pbs
```

The CPU job requests four exclusive, scattered 72-core hosts for three hours. The
GPU job requests one GPU on each of two shared hosts for one hour. Vanda's hook
normalises each one-GPU request to 36 CPUs and 240 GB, even when fewer are
requested. Record possible shared-host contention when interpreting its measurements. The Vanda
`batch_gpu` queue advertised a **total** limit of two GPUs per job at inspection;
the previous four-GPU request was rejected, so the GPU suite uses 1 and 2 GPUs.
Do not submit the old uncalibrated strong/weak/hybrid/GPU template scripts to
reproduce this dataset.

## Timing and validation

`CGStats::solve_seconds` measures the iteration loop after work-vector allocation,
zeroing/copying, and the initial norm/reduction. Phase timers reset at the same
point. A barrier precedes the start and ends the loop; the maximum elapsed time
over ranks is reported. Vector destruction, true residual and error checks are
outside this interval. CUDA already uses this setup/loop/validation separation.
The single-reduction method's initial operator application is setup too.

Each configuration has one excluded warmup and three **separate processes** with
`--repeat 1`. The checker retains every measured row and selects the entire
fastest row, including its matching iteration count and phase times. It also
reports median, min/max and population CV. A short case is flagged, not discarded.

The stopping tolerance is 5e-9, leaving a margin for accepting the recomputed
true residual below 1e-8. The maximum is 20000 iterations. Every parallel sample
must match a same-mesh serial reference in iteration count (within one) and
discrete L2 error (relative tolerance 1e-6). A process exit code alone is
insufficient. Warmups also undergo these checks.

## CPU matrix

| Experiment | Settings |
| --- | --- |
| Serial size sweep | 2D n=128,256,512,1024,2048; 3D n=32,64,128,192,203,288 |
| Strong scaling | 2D n=2048; 3D n=288; 1,2,4,8,16,32,64,128,256,288 MPI ranks; slab and cart; blocking standard CG |
| MPI choices | Both strong meshes at 64 and 256 ranks; cart; overlap/std, block/single-reduction, overlap/single-reduction, compared with the strong baseline |
| Fixed 288 cores | Both strong meshes; MPI ranks × OpenMP threads = 288×1,144×2,72×4,32×9,16×18,4×72 |
| 2D weak scaling | n=128 sqrt(P), P=1,4,16,64,256; exactly constant owned points/core |
| 3D weak scaling | n=round(32 cbrt(P)), P=1,8,64,216,256; actual points/core retained (rounding at 256) |

Before the full matrix, arithmetic/thread probes verify 256×1,288×1 and 4×72
on four hosts; small 2D/3D serial comparisons then check 256/288 MPI ranks and
32×9 OpenMP. Preflight samples remain labelled and must be excluded from scaling.

The launcher takes its host list only from `PBS_NODEFILE`, uses a balanced
`ppr` map across the required host subset, and disables MPI's inherited socket
binding. `pin_rank.py` selects disjoint physical cores from each process's allowed
CPU set (never both SMT siblings), applies `sched_setaffinity`, and supplies exact
OpenMP places. Every rank records its host, local rank, logical IDs and physical
package/core IDs. The checker rejects missing records and overlapping cores.
The smoke probe also checks actual OpenMP thread counts and distinct sampled CPUs.

CPU launches explicitly use Open MPI `ob1` with `self,vader,tcp`, matching the
site's point-to-point defaults. HCOLL and UCC are disabled after both failed in
multi-node initialisation. These results therefore describe this TCP/shared-memory
configuration, not an InfiniBand/RDMA benchmark.

## GPU matrix

Preflight compares 2D n=31 and 3D n=15 against serial on 1/2 GPUs, for both staged
and device-pointer transports. Only after all preflight cases pass does the job
measure 2D n=2048 and 3D n=256 on 1/2 GPUs with the same two transports. Two GPUs
are on different physical hosts, so this checks actual inter-node halos.

The GPU launcher uses UCX PML with TCP, shared-memory and CUDA transports, sets
`UCX_NET_DEVICES=all` instead of inheriting the site's empty setting, explicitly
exports the UCX settings to ranks, and disables HCOLL/UCC. Passing device
pointers to CUDA-aware MPI does not imply GPUDirect RDMA; the selected TCP path
can stage internally. Record this distinction when interpreting transport times.
Remote MPI daemons are started through `pbs_rsh.py` and PBS/TM so that GPU device
limits follow the allocation on each shared host. A two-rank probe requires one
visible GPU per rank and checks an actual device-pointer MPI transfer before
workload measurements.

`PCG_EXPECT_GPU_COUNT`, `PCG_SMOKE_DEVICE_MPI`, and `PCG_CUDA_HALO` are also
explicitly exported with `mpiexec -x`. Setting them only in the launcher's
environment did not propagate them through the PBS remote-daemon path.

## Evidence

Each job writes `results/raw/step3-{cpu,gpu}-JOBID/`. Completion requires PBS exit
zero, `exit_code.txt` equal to zero, and both the corresponding
`*_SCALING_VALIDATION=PASS` and `STEP3_*_COMPLETE` markers. Build commands, all
warmups/samples, placement records, source/binary hashes and failed attempts remain
in ignored raw evidence. Accepted CSVs and manifests are exported separately after
an independent audit; plotting and collector changes are task 4.

Weak-scaling solve time includes increasing CG iteration counts as the mesh grows.
Retain both whole-solve time and seconds/iteration. In 3D the rounded 256-rank
mesh has a slightly different points/core count; do not label it exact weak scaling.
The independently maximised phase times may come from different ranks and their
sum need not equal total time.

## Current dataset and recovery

See [the task 3 status and results](../../report/scaling_step3.md). The first
CPU job completed 92 groups before failing at the final 3D weak point: the old
serial reference list contained n=202, while the weak-mesh formula produces
n=203. The driver now derives the reference sizes from that same formula.
The 276 completed samples were audited individually; this is explicitly a
partial-suite export, not a successful-job declaration.

After PBS accepts submissions again, run from the tested source root:

```bash
qsub -P YOUR_PROJECT -l walltime=00:30:00 -v SUITE=weak3d scripts/vanda/scaling_cpu.pbs
qsub -P YOUR_PROJECT scripts/vanda/scaling_gpu.pbs
```

The `weak3d` suite reruns **all five** 3D weak points and their serial references
in one allocation (10 groups, 30 samples). Retain its complete export separately.
For a combined CPU matrix, replace the first job's four completed 3D weak groups
and unused serial n=202 group with the new five weak groups and serial n=203
group. Keep the other four new serial groups as supporting validation evidence.
This yields 93 groups / 279 samples without mixing allocations within a weak
curve or duplicating reference groups.

Audit each successful supplement against its own archived source snapshot:

```bash
python3 scripts/audit_scaling.py cpu RAW_CPU_JOB --jobs-json FINAL_JOBS.json \
  --source-root ARCHIVED_SOURCE --prefix cpu_weak3d --output results/benchmarks/step3
python3 scripts/audit_scaling.py gpu RAW_GPU_JOB --jobs-json FINAL_JOBS.json \
  --source-root ARCHIVED_SOURCE --prefix gpu --output results/benchmarks/step3
```

Archive scheduler JSON with `qstat -xf -F json JOBID` while job history is still
available. Check mathematical source and binary hashes against the first run
before combining CPU exports; preserve any differences in the provenance.
