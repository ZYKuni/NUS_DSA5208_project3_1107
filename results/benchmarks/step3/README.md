# Task 3 accepted measurements

The CPU matrix is complete: strong scaling reaches **288 physical cores** and
both weak curves reach **256**. GPU retry `1540688.stdct-mgmt-02` is pending a
successful complete audit. Failed attempts are retained only as raw evidence.

| Prefix | Scope | Groups / samples | PBS status |
| --- | --- | ---: | --- |
| `cpu_main` | Original completed groups, including preflight | 92 / 276 | Actual exit 1; documented missing n=203 reference |
| `cpu_weak3d` | Full replacement 3D weak curve and five serial references | 10 / 30 | Exit 0; both completion markers |
| `cpu_combined` | Selected complete CPU matrix, including eight preflight groups | 93 / 279 | Assembly of audited sources, not a single PBS job |

Each original prefix has `samples.csv`, `summary.csv`, `manifest.json` and
`audit.json`. The combined prefix has samples, summary and an assembly manifest.
It replaces all four old 3D weak points and the unused serial n=202 reference;
four duplicate repair serial references remain in the repair export only.
Numerical source and CPU binary hashes match across the two CPU allocations.
The assembly preserves the original job's actual exit status.

Performance analysis excludes eight preflight groups, leaving **85 CPU groups /
255 samples**. No measured outlier is removed. All five 3D weak points and their
one-rank baseline come from the repair allocation. The new n=203 serial point
is labelled with that allocation; the other serial sweep points remain from
the main allocation. Archive and export hashes are in `provenance.json`.

Reproduce the original partial audit:

```bash
python3 scripts/audit_scaling.py cpu \
  results/raw/step3-vanda-initial/source/results/raw/step3-cpu-1533443.stdct-mgmt-02 \
  --jobs-json results/raw/step3-vanda-initial/jobs-final.json \
  --source-root results/raw/step3-vanda-initial/source \
  --allow-missing-weak3d-reference --prefix cpu_main \
  --output results/benchmarks/step3
```

The explicit exception accepts only the documented missing-reference failure
and requires all 92 completed groups to pass their checks. Reproduce the
successful repair and CPU assembly:

```bash
python3 scripts/audit_scaling.py cpu \
  results/raw/step3-vanda-repair-20261111/source/results/raw/step3-cpu-1540132.stdct-mgmt-02 \
  --jobs-json results/raw/step3-vanda-repair-20261111/repair-jobs-final.json \
  --source-root results/raw/step3-vanda-repair-20261111/source \
  --prefix cpu_weak3d --output results/benchmarks/step3
python3 scripts/combine_cpu_scaling.py \
  --main results/benchmarks/step3/cpu_main \
  --repair results/benchmarks/step3/cpu_weak3d \
  --output results/benchmarks/step3/cpu_combined
```

Raw logs, failed attempts and frozen source snapshots remain outside Git under
`results/raw/`. Reproduction of the figures needs only the committed exports.
See [results and limitations](../../../report/scaling_step3.md) and
[run commands](../../../scripts/vanda/STEP3.md#current-dataset-and-recovery).
