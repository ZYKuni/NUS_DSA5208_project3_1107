# Workload validation evidence (not scaling data)

Accepted Vanda jobs on 2026-11-08:

| Job | Host | Independent solves | Implementations |
| --- | --- | --- | --- |
| 1532579.stdct-mgmt-02 | CN-149 | 54 | serial, MPI (2 ranks), OpenMP (2 ranks × 2 threads) |
| 1532562.stdct-mgmt-02 | GN-A40-047 | 36 | serial, CUDA (1 rank, 1 A40 GPU), staged transport |

Both jobs exited zero. Each passed seven CTest groups; the GPU job also passed
the independent 2D/3D stencil and reduction check. All workload samples had true
relative residual below 1e-8 and matched their serial reference. The one-GPU
pilot does not validate inter-GPU halo communication or multi-GPU scaling.

The summary CSVs keep min/median/max, population coefficient of variation and
iteration ranges from all three independent samples. Only CSV line endings were
normalised to LF for version control. The manifests record binary/problem hashes
and environment; `vanda_audit.json` records verified job
completion, and `vanda_final-source-hashes.json` ties the numerical sources and
checker to the tested files. The local CPU files are development evidence only.

Full commands, samples, build logs, source archive and the cancelled first CPU
attempt are retained locally in ignored `results/raw/step2-vanda/`. The downloaded
`step2-evidence-20261108.tar` was verified against SHA-256:

```text
9b75b387a075024c4735fc907b749041f6c0460dad3d1b1c0d0adc658256fa95
```

Do not feed these summaries to the formal scaling collector. Timing boundaries,
placement and sufficiently long cases must be addressed first; see
[the task 2 report](../../../report/workload_step2.md).
