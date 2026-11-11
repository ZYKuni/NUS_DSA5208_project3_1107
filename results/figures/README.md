# CPU scaling figure index

The [12-page figure book](scaling_figures.pdf) contains all figures below in
page order. Individual PDFs are vector graphics; matching `.png` files are
provided for preview. `manifest.json` records checksums, source group IDs,
analysis input hashes and plotting-library versions.

| Page | Figure | Content |
| --- | --- | --- |
| 1 | [Serial scaling](serial_scaling.pdf) | Runtime and CG iteration count vs interior unknowns |
| 2 | [Serial error](serial_error.pdf) | Discrete L2 error vs h; h-squared reference trends |
| 3 | [2D strong scaling](strong_2d_n2048.pdf) | n=2048; time, speedup and efficiency through 288 cores |
| 4 | [2D phases](phases_2d_n2048.pdf) | Separate stencil, halo and reduction maxima |
| 5 | [3D strong scaling](strong_3d_n288.pdf) | n=288; time, speedup and efficiency through 288 cores |
| 6 | [3D phases](phases_3d_n288.pdf) | Separate stencil, halo and reduction maxima |
| 7 | [2D weak scaling](weak_2d.pdf) | Whole-solve and per-iteration time; ratios; iterations |
| 8 | [3D weak scaling](weak_3d.pdf) | Full replacement curve through 256 physical cores |
| 9 | [2D MPI choices](variants_2d_n2048.pdf) | Blocking/overlap and standard/single-reduction CG |
| 10 | [3D MPI choices](variants_3d_n288.pdf) | Same four choices at 64 and 256 cores |
| 11 | [2D hybrid](hybrid_2d_n2048.pdf) | Six MPI/OpenMP splits of fixed 288 physical cores |
| 12 | [3D hybrid](hybrid_3d_n288.pdf) | Same fixed-resource comparison |

Filled points/lines use minimum whole-solve time; hollow diamonds use medians;
shading retains observed ranges from three independent processes. Phase lines
retain the phases from the fastest whole-solve row. Ratios use the matched
baselines described in [the analysis guide](../../analysis/README.md).
Ranges are not confidence intervals. Time, size and CPU count axes are
logarithmic; ratio y axes are linear and superlinear values are not clipped.

These figures use 85 groups / 255 samples after excluding eight preflight
groups. **No GPU performance figure is available.** No absent measurement is
interpolated. See [the discussion](../../report/analysis_step4.md) for limits,
the meaning of weak-scaling ratios and the GPU retry status.
