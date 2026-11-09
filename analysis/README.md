# Reproducing the task 4 analysis

Run from the repository root with Python 3.12 and the analysis dependencies:

```bash
python3 -m pip install -r analysis/requirements-reproduce.txt
python3 analysis/collect.py
python3 analysis/plots.py
python3 -m unittest discover -s analysis/tests -v
```

The general supported dependencies remain in `requirements.txt`; the versioned
file records the exact NumPy, pandas and Matplotlib releases used for these
artifacts. Neither command needs cluster access, compilation or raw logs.
An optional positional argument selects a different results directory.

## Inputs and acceptance

`datasets.json` explicitly lists the four immutable input files for each
audited export (samples, summary, run manifest, audit), with SHA-256 checksums.
There is no recursive CSV scan: raw attempts, earlier validation jobs,
preflight rows and previous generated outputs cannot silently enter a curve.

The current input is the **documented partial** CPU suite from job
`1533443.stdct-mgmt-02`: 92 completed groups, 276 samples, actual exit status 1.
It requires an explicit `allow_documented_partial` opt-in and the matching
independent audit. An ordinary failed job is rejected. This does not declare
task 3 complete.

The collector checks file checksums, audit status and counts, resource labels,
finite values, convergence, three distinct repeats, same-mesh serial comparisons,
and the exact correspondence between the fastest sample and its exported
iteration/phase values. It recomputes summary statistics from samples.
The eight `preflight` groups are excluded from performance analysis; no measured
outlier is removed. The result is **84 groups / 252 independent samples**.
The valid serial n=202 sweep point is retained and identified as an unused
reference; no n=203 measurement is manufactured.

## Metrics and plots

- The primary time is the minimum of three separate processes. Median, maximum,
  population CV and per-iteration statistics are retained. Figure diamonds show
  medians; shaded time ranges show observed min-max, not confidence intervals.
- Strong scaling uses the **same job, mesh, implementation, decomposition,
  halo, CG variant and thread count** at one MPI rank. `S(P)=T_MPI(1)/T_MPI(P)`;
  `E(P)=S(P)/P`. The baseline is not the serial executable or a weak/preflight
  row. Missing or ambiguous baselines are errors. Efficiency is not clipped
  at 100%, so superlinear observations remain visible.
- Ratio medians use median/median. Ratio range envelopes use minimum-baseline /
  maximum-target and maximum-baseline / minimum-target. The baseline compared
  with itself is identically one. These ranges are descriptive, not inferential.
- Weak scaling reports both `T(1)/T(P)` for the **whole solve** and the ratio
  of average seconds/iteration. The mesh and CG iteration count change with P;
  whole-solve ratios must not be interpreted as pure communication efficiency.
- Variant comparisons use the standard/blocking Cartesian MPI configuration
  at the same mesh and rank count. `pipe` means single-reduction
  Chronopoulos-Gear CG, not an asynchronous pipeline.
- Hybrid comparisons keep **288 physical cores** and four hosts fixed. Threads
  are not extra cores: ranks x threads is always 288. Runtime ratios use the
  288-rank pure-MPI baseline; they are not strong-scaling efficiency.
- Phase times are independently maximised over ranks and may overlap. They
  are plotted separately. `phase_sum_over_total` is only a diagnostic; no
  additive stacked chart or `comm_frac` is produced.
- Time, mesh/unknown-count and core/thread-count axes are logarithmic. Ratios
  use linear y axes. Subsecond groups remain present and carry the
  `shortest_at_least_one_second` flag; short durations limit interpretation.

## Outputs

- `results/all.csv`: the 84 selected configurations, statistics and applicable
  derived metrics. Blank metrics mean not applicable, not zero.
- `results/analysis_samples.csv`: all 252 selected repetitions.
- `results/<experiment>_<impl>_<dim>d.csv`: split views of the same groups.
- `results/tables/*.csv`: traceable report tables, with group and job IDs.
- `results/analysis_manifest.json`: input/code/output hashes, exact exclusions,
  software versions, counts and missing endpoints.
- `results/figures/`: 12 vector PDFs and matching PNGs, a 12-page figure book,
  and an index with file hashes and exact contributing group IDs.

The plotter checks the collector's output hashes before reading the data and
rejects mixed-allocation strong/weak/variant/hybrid series. The figure manifest
is authoritative for the current generated figure set.

## Missing data and later supplements

3D weak scaling stops at **216 cores**; the 256-core point is marked missing,
with no extrapolation or connecting line to a fabricated endpoint. There are
no accepted GPU measurements, so the manifest records that GPU figures were
skipped. The published figure set is CPU only. Task 4 is complete for this
accepted dataset while task 3 remains partial.

After an independently audited CPU supplement is available, add its four
files and verified checksums to `datasets.json`. Use explicit `exclude_groups`
to replace the **entire** old 3D weak curve as described in
[`STEP3.md`](../scripts/vanda/STEP3.md#current-dataset-and-recovery), retaining
the supplement's serial references in its original export. Run the tests and
both commands again, review coverage, and inspect the new figures. Preserve
allocation differences in the serial-reference provenance. GPU comparisons
require their own accepted export and GPU-count/transport analysis; never
reuse CPU core efficiency as GPU efficiency.

See [the results discussion](../report/analysis_step4.md) and
[the figure index](../results/figures/README.md).
