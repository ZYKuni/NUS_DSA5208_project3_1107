#!/bin/bash
# Source this on a Vanda COMPUTE node (login nodes are VMs; compile inside `qsub -I`).
#   qsub -I -l select=1:ncpus=4 -l walltime=00:20:00
#   source scripts/vanda/env.sh
# Owner: C. Confirm with `module avail`.
module purge
module load nvhpc-hpcx-cuda12/26.1   # recommended in Lecture 12 (CUDA-aware MPI)
# Alternative: module load OpenMPI/4.1.4-NVHPC-22.7-CUDA-11.7.0
# TODO(C): add CMake module if `cmake --version` < 3.18
export OMP_PROC_BIND=close
export OMP_PLACES=cores
