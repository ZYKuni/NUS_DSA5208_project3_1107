# results/

Audited experiment exports are in [`benchmarks/step3`](benchmarks/step3/README.md).
Raw PBS logs are not committed.

Task 4 produces `all.csv` (84 performance groups), `analysis_samples.csv`
(252 independent samples), split experiment CSVs, [`tables/`](tables/README.md)
and [`figures/`](figures/README.md). `analysis_manifest.json` records exact
inputs, exclusions, checksums, versions and missing coverage. It excludes eight
preflight groups and does not treat the original CPU job's nonzero exit as a
successful full suite. See [`analysis/README.md`](../analysis/README.md) to
reproduce the analysis and [`report/analysis_step4.md`](../report/analysis_step4.md)
for interpretation. GPU data and the 3D weak 256-core point are still absent.
