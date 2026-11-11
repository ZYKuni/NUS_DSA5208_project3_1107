# MPI + CUDA

Build the repository with ENABLE_CUDA=ON and a CUDA architecture matching the allocated GPU.
Use one rank per GPU. The solver selects the node-local rank's device, or device zero when the scheduler exposes only one GPU per process. Duplicate device assignments on a node are rejected.

On a GPU compute node, run the standalone stencil and reduction check first:

```sh
nvcc -std=c++17 src/hybrid_cuda/checks/kernel_check.cu -o build/kernel_check
build/kernel_check
PCG_CUDA_HALO=staged python3 src/hybrid_omp/checks/validate.py build/bin/poisson_cuda --ranks 2
# Run the next command with a confirmed CUDA-aware MPI installation.
PCG_CUDA_HALO=device python3 src/hybrid_omp/checks/validate.py build/bin/poisson_cuda --ranks 2
```

The default staged path copies packed faces through host buffers. The device path passes contiguous GPU buffers to MPI_Sendrecv. Both use standard CG and blocking halo exchange, with slab or Cartesian partitions. Set the same transport on every rank. Keep staged and device results in separate CSV files so C's collector can distinguish the source. For example, on a two-GPU allocation:

```sh
for mode in staged device; do
  PCG_CUDA_HALO=$mode mpirun -np 2 build/bin/poisson_cuda --dim 3 --n 127 --repeat 3 --csv results/gpu_${mode}_cuda_3d.csv
done
```

Use at least two ranks to exercise a real halo transfer. With one GPU the run checks the local solver and does not measure inter-GPU transport.

The final `rel_res` is recomputed as the true residual `||b-Ax||/||b||`, outside
the timed solve, rather than reporting only the recursive CG residual. The
shared manufactured problem and serial comparison are checked by
`scripts/check_workload.py`; see `scripts/vanda/STEP2.md` for the cluster pilot.

`--tol` is also the true-residual threshold used for the CUDA executable's
exit status. For a tighter recursive CG stopping target, set
`PCG_CUDA_STOP_TOL` on **every rank**. It must be finite, positive and no larger
than `--tol`; without it, the stopping target remains `--tol`. Formal runs use
`--tol 1e-8` with `PCG_CUDA_STOP_TOL=5e-9`, while serial references stop at
5e-9. This retains the same iteration target while leaving a margin for
roundoff in the recomputed true residual. The launcher explicitly exports
the variable with `mpiexec -x PCG_CUDA_STOP_TOL`. Every accepted sample must
still have true residual below 1e-8 and agree with its serial reference.

The standalone check also packs each of the four 2D and six 3D faces of a
non-square tile, compares the contiguous buffer to a CPU coordinate traversal,
then checks the full padded field after unpacking. This isolates face-index
errors before starting the two-host MPI preflight. For formal runs use
[C's Vanda driver](../../scripts/vanda/STEP3.md#current-dataset-and-recovery),
which exports the transport to every rank and preserves all three samples.
