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
