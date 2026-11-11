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

The CPU inputs are the **documented partial** main suite from job
`1533443.stdct-mgmt-02` (92 groups, 276 samples, actual exit status 1) and the
successful full 3D weak repair `1540132.stdct-mgmt-02` (10 groups, 30 samples).
Only the documented original failure has an explicit `allow_documented_partial`
opt-in. The repair requires exit zero and both completion markers. Numerical
source and CPU binary hashes match across these two allocations.

The selected matrix replaces the entire original 3D weak curve and the unused
serial n=202 reference. Four duplicate serial references remain in the repair
export, outside the selected matrix. The assembly retains 93 CPU groups / 279
samples, including validation preflight; `cpu_combined_manifest.json` preserves
both original job exit statuses and the exact selection.

The collector checks file checksums, audit status and counts, resource labels,
finite values, convergence, three distinct repeats, same-mesh serial comparisons,
and the exact correspondence between the fastest sample and its exported
iteration/phase values. It recomputes summary statistics from samples.
The eight CPU `preflight` groups are excluded from performance analysis; no
measured outlier is removed. The current result is **85 groups / 255 independent
samples**. The serial n=203 reference was measured in the repair allocation;
its allocation difference is recorded in the serial figures.

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
- GPU speedup uses the same job, mesh and **same transport** at one GPU:
  `S(G)=T_GPU(1)/T_GPU(G)` and `E(G)=S(G)/G`. `staged_over_transport` compares
  the staged and selected transport at the same GPU count. GPU counts are
  not CPU core counts. Serial references stop recursively at 5e-9; CUDA uses
  `PCG_CUDA_STOP_TOL=5e-9` with `--tol 1e-8`, retaining strict true-residual
  acceptance in both the executable and the audit.
- Phase times are independently maximised over ranks and may overlap. They
  are plotted separately. `phase_sum_over_total` is only a diagnostic; no
  additive stacked chart or `comm_frac` is produced.
- Time, mesh/unknown-count and core/thread-count axes are logarithmic. Ratios
  use linear y axes. Subsecond groups remain present and carry the
  `shortest_at_least_one_second` flag; short durations limit interpretation.

## Outputs

- `results/all.csv`: the 85 selected configurations, statistics and applicable
  derived metrics. Blank metrics mean not applicable, not zero.
- `results/analysis_samples.csv`: all 255 selected repetitions.
- `results/<experiment>_<impl>_<dim>d.csv`: split views of the same groups.
- `results/tables/*.csv`: traceable report tables, with group and job IDs.
- `results/analysis_manifest.json`: input/code/output hashes, exact exclusions,
  software versions, counts and missing endpoints.
- `results/figures/`: 12 vector PDFs and matching PNGs, a 12-page figure book,
  and an index with file hashes and exact contributing group IDs.

The plotter checks the collector's output hashes before reading the data and
rejects mixed-allocation strong/weak/variant/hybrid series. The figure manifest
is authoritative for the current generated figure set.

## Coverage and later GPU export

Both CPU weak curves now reach **256 physical cores**; CPU strong scaling
reaches 288. All five 3D weak points use the same repair allocation. Integer
rounding gives 32677.449 unknowns/core at n=203 and 256 ranks, 0.276% below
the base load. No absent endpoint is interpolated.

GPU retry `1540688.stdct-mgmt-02` is pending a successful complete audit. Until
its four accepted export files and checksums are added to `datasets.json`,
there are no GPU inputs or performance figures. The collector already checks
GPU-count/transport baseline isolation and records exact missing GPU meshes.
After adding an accepted export, rerun collection, tests and plots, review
coverage, and render the new PDF pages for inspection. Never reuse CPU core
efficiency as GPU efficiency.

See [the results discussion](../report/analysis_step4.md) and
[the figure index](../results/figures/README.md).
