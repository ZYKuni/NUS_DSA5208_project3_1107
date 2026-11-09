# Task 3 accepted measurements — partial suite

Status as of **2026-11-09 13:48 Singapore**: CPU strong scaling through **288
physical cores** is measured and validated. The complete task is pending one
3D weak-scaling supplement and the GPU measurements. No supplement job was
accepted on November 9 because PBS refused both query and submission connections.

| File | Meaning |
| --- | --- |
| `cpu_main_samples.csv` | All 276 accepted independent samples, including labelled preflight/reference groups |
| `cpu_main_summary.csv` | 92 groups; the minimum-time complete row plus median, range and CV |
| `cpu_main_manifest.json` | Original run manifest, source/binary hashes and host list |
| `cpu_main_audit.json` | Independent audit scope, actual PBS exit status 1 and validation results |
| `provenance.json` | Archive checksums and pending-work status |

Do not count `preflight` groups as performance evidence. The serial 3D n=202
group is valid but unused; it is retained to preserve the original dataset.
The 3D weak curve currently ends at 216 ranks. Do not interpolate a 256-rank
measurement or label that curve complete. There are no accepted GPU data here.

Reproduce the partial audit from the preserved, ignored evidence directory:

```bash
python3 scripts/audit_scaling.py cpu \
  results/raw/step3-vanda-initial/source/results/raw/step3-cpu-1533443.stdct-mgmt-02 \
  --jobs-json results/raw/step3-vanda-initial/jobs-final.json \
  --source-root results/raw/step3-vanda-initial/source \
  --allow-missing-weak3d-reference --prefix cpu_main \
  --output results/benchmarks/step3
```

The explicit exception accepts only the documented missing-reference failure
and requires all 92 completed groups to pass their checks. Default auditing
requires exit zero and both completion markers. Raw logs, failed attempts and
the frozen source snapshot remain outside Git, under `results/raw/`, in line
with the repository's submission rules.

See [results and limitations](../../../report/scaling_step3.md) and
[recovery commands](../../../scripts/vanda/STEP3.md#current-dataset-and-recovery).
