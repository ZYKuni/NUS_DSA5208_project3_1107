# Parallel Conjugate Gradient for the 2D/3D Poisson Equation (MPI + X)

DSA5208 Project 3, AY2026/27 Semester 1, National University of Singapore.

| Name | Student ID | Main responsibility |
| --- | --- | --- |
| Yikun Zhao | A0353894M | Serial and MPI solvers, validation, report editing |
| Jiahao Zhou | A0354090J | MPI + OpenMP and MPI + CUDA solvers |
| Zheke Chen | A0356140M | Cluster builds, benchmarks on Vanda/Atlas, figures |

## Problem

We solve -Δu = f on the unit square (2D) and unit cube (3D) with u = 0 on the boundary.
A 5-point (2D) or 7-point (3D) finite-difference stencil gives a sparse symmetric
positive-definite system Au = b, solved with the conjugate gradient (CG) method.
A is never stored: each matrix-vector product is a stencil sweep (matrix-free).
The right-hand side comes from the manufactured solution u(x) = Π x_k (1 − x_k) e^{x_k}, so the
discretisation error can be measured exactly. (We deliberately avoid u = Π sin(π x_k): it is an
exact eigenvector of the discrete Laplacian, so CG would converge in a single iteration.)
No BLAS or LAPACK is used.

## Repository layout

```
include/          shared headers: CLI parameters, timers, CSV format, model problem,
                  grid block + stencil kernels (grid.hpp), CG driver + Backend interface (cg.hpp)
src/common/       shared implementation (CLI parser, CSV writer, kernels, CG driver)
src/serial/       serial CG                          (owner: Yikun)
src/mpi/          pure MPI CG                        (owner: Yikun)
src/hybrid_omp/   MPI + OpenMP CG                    (owner: Jiahao)
src/hybrid_cuda/  MPI + CUDA CG                      (owner: Jiahao)
apps/             one main() per executable
tests/            validation tests
scripts/          build script, PBS job scripts for Vanda and Atlas (owner: Zheke)
analysis/         result collection and plotting     (owner: Zheke)
results/          merged CSV files and figures (raw logs are not committed)
report/           report sources and AI-usage log
```

## Requirements

- C++17 compiler, CMake >= 3.18
- An MPI implementation (Open MPI, MPICH or NVIDIA HPC-X) providing `mpicxx`
- OpenMP support in the compiler (for `poisson_omp`)
- CUDA toolkit and an NVIDIA GPU (only for `poisson_cuda`)
- Python 3.9+ for the analysis scripts: `python3 -m pip install -r requirements.txt`

## Build

```bash
scripts/build.sh            # serial + MPI + MPI/OpenMP, runs tests
scripts/build.sh cuda       # also MPI/CUDA
```

or manually:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=mpicxx [-DENABLE_CUDA=ON]
cmake --build build -j
ctest --test-dir build --output-on-failure
```

Executables are written to `build/bin/`.

### On Vanda

Login nodes are virtual machines, so compile on a compute node:

```bash
qsub -I -l select=1:ncpus=4 -l walltime=00:20:00
cd $PBS_O_WORKDIR
source scripts/vanda/env.sh
scripts/build.sh cuda
```

### On Atlas

```bash
source scripts/atlas/env.sh
scripts/build.sh
```

## Run

All executables accept the same options:

```
--dim 2|3               problem dimension (default 2)
--n N                   interior grid points per side (default 256)
--tol T                 relative residual tolerance (default 1e-8)
--maxit M               maximum CG iterations (default 10000)
--decomp slab|cart      MPI decomposition (default cart)
--halo block|overlap    halo exchange strategy (default block)
--cg std|pipe           standard CG or single-reduction CG (default std)
--repeat R              repeat solve R times, report fastest (default 1)
--csv FILE              append one result row to FILE
--verbose               print residual history
```

Examples:

```bash
build/bin/poisson_serial --dim 2 --n 512
mpirun -np 16 build/bin/poisson_mpi --dim 3 --n 256 --decomp cart --halo overlap
OMP_NUM_THREADS=18 mpirun -np 4 build/bin/poisson_omp --dim 3 --n 256
mpirun -np 2 build/bin/poisson_cuda --dim 3 --n 512
```

## Output format

Each run appends one CSV row with these columns:

```
impl,dim,n,ranks,threads,gpus,decomp,halo,cg,iters,t_total,t_stencil,t_halo,t_reduce,rel_res,err_l2
```

Times are in seconds, cover the solve only (not setup or I/O), and are the maximum over ranks.
`t_stencil`, `t_halo` and `t_reduce` split each run into computation, neighbour communication
and global reductions.

## Reproducing the experiments

```bash
qsub -P YOUR_PROJECT scripts/vanda/scaling_cpu.pbs # serial, strong/weak, MPI choices, hybrid; up to 288 cores
qsub -P YOUR_PROJECT scripts/vanda/scaling_gpu.pbs # serial checks, 1/2 GPUs, staged/device transport
```

See [the task 3 run guide](scripts/vanda/STEP3.md) for exact meshes, timing,
placement, queue limits and evidence requirements. The original individual PBS
files are uncalibrated templates.
The [task 3 status](report/scaling_step3.md) records the validated 288-core CPU
results and the outstanding 3D weak/GPU runs; the suite is not yet complete.

Reproduce the task 4 analysis from the committed audited CPU exports:

```bash
python3 -m pip install -r analysis/requirements-reproduce.txt
python3 analysis/collect.py
python3 analysis/plots.py
```

The [analysis guide](analysis/README.md) defines the baselines and explicit
data selection. Outputs include 84 performance groups / 252 samples,
[report tables](results/tables/README.md), [12 figures and a PDF book](results/figures/README.md),
and [the results discussion](report/analysis_step4.md). The missing 3D weak
endpoint and unavailable GPU measurements remain marked; no raw log is needed
to reproduce these CPU artifacts.

## Validation

`ctest --test-dir build --output-on-failure` runs:

| Test | What it checks |
| --- | --- |
| `common` | CLI parser, CSV format, manufactured solution |
| `serial` | A is symmetric positive definite; err_l2 falls as O(h²) (observed order 2.00 in 2D and 3D); standard and single-reduction CG give the same iterations and error |
| `mpi_np1`, `mpi_np3`, `mpi_np4` | every `--decomp` × `--halo` × `--cg` combination, 2D and 3D, uneven splits and one-point-thick blocks: same iteration count as serial (±1), same err_l2 (1e-6 relative), and every grid point equal to the serial solution (max-norm, 1e-8 relative) |

The MPI test can be run on any number of ranks: `mpirun -np 8 build/bin/test_mpi`.
With Open MPI on a machine with fewer cores than ranks, configure with
`-DPCG_MPIEXEC_EXTRA="--oversubscribe"`.

Every run also reports `rel_res`, the true residual ‖b − A x‖/‖b‖ recomputed after the solve,
and `err_l2`, the discrete L2 error √(h^d Σ (x − u)²) against the manufactured solution.

## AI usage

See `report/ai_usage.md`.
