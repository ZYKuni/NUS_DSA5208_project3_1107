# report/

| File | Content |
| --- | --- |
| `report.pdf` | **Final submitted report** (names and student IDs on the first page) |
| `report.tex` | LaTeX source of the report |
| `make_tables.py` | Generates every table in `generated/` from the committed CSV files in `results/` |
| `generated/*.tex` | Table bodies produced by `make_tables.py` (do not edit by hand) |
| `analysis_step4.md`, `scaling_step3.md`, `hybrid.md`, `cluster_step1.md`, `workload_step2.md` | Working notes behind the report (cluster setup, run audits, analysis) |

Rebuild the PDF from the repository root (needs a TeX Live installation with `latexmk`):

```bash
python3 report/make_tables.py
cd report && latexmk -pdf report.tex
```

Figures are read directly from `results/figures/*.pdf`.
