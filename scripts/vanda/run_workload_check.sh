#!/bin/bash
# Small correctness and workload-duration pilot, not a scaling experiment.
set -euo pipefail
mode=${1:?cpu or cuda}
[[ "$mode" = cpu || "$mode" = cuda ]]
evidence="$PWD/results/raw/step2-${mode}-${PBS_JOBID:?}"
mkdir -p "$evidence"
trap 'rc=$?; printf "%s\n" "$rc" > "$evidence/exit_code.txt"' EXIT
exec > >(tee "$evidence/job.log") 2>&1
qstat -f "$PBS_JOBID" > "$evidence/scheduler.txt"
date -u +%Y-%m-%dT%H:%M:%SZ
hostname
lscpu
export PCG_MPI_MODULE=nvhpc-hpcx-cuda12/26.1
source scripts/vanda/env.sh
# Both pilots use one PBS host, so the local launcher inherits its CPU cgroup.
# Do not reuse this launcher for a multi-node job: use PBS/TM as in step 1.
launcher="mpiexec --bind-to none"
if [[ "$mode" = cpu ]]; then
    enable_cuda=OFF
    extra=()
else
    nvidia-smi
    nvcc --version
    arch=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -n 1 | tr -d '. ')
    [[ "$arch" =~ ^[0-9]+$ ]]
    enable_cuda=ON
    extra=("-DCMAKE_CUDA_ARCHITECTURES=$arch" -DCMAKE_CUDA_STANDARD=17)
fi
# This pilot validates numerical work and reports variability. Affinity tuning
# and performance-ready problem sizes are separate tasks; avoid overlapping
# OpenMP core binding between the small shared-node MPI ranks here.
export OMP_PROC_BIND=FALSE OMP_DYNAMIC=FALSE OMP_WAIT_POLICY=PASSIVE
module list
mpicxx --showme
mpiexec --version
cmake --version
python3 --version
build="build-step2-$mode"
if [[ "$mode" = cpu ]]; then build=build-step2-cpu-hpcx; fi
cmake -S . -B "$build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=mpicxx \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DENABLE_CUDA="$enable_cuda" \
    "-DPCG_MPIEXEC_EXTRA=${launcher#mpiexec }" "${extra[@]}"
cmake --build "$build" --parallel 4
ctest --test-dir "$build" --output-on-failure
cp "$build/compile_commands.json" "$evidence/compile_commands.json"
sha256sum "$build"/bin/poisson_* > "$evidence/binaries.sha256"
if [[ "$mode" = cuda ]]; then
    nvcc -std=c++17 -arch="sm_$arch" src/hybrid_cuda/checks/kernel_check.cu -o "$build/kernel_check"
    "$build/kernel_check"
    export PCG_CUDA_HALO=staged
    impls=(cuda)
    ranks=1
    threads=1
else
    impls=(mpi omp)
    ranks=2
    threads=2
fi
python3 scripts/check_workload.py --bin-dir "$build/bin" --output "$evidence/workload" \
    --platform vanda --impls "${impls[@]}" --ranks "$ranks" --threads "$threads" \
    --launcher "$launcher" --sizes-2d 15 31 511 --sizes-3d 15 31 95 --repeats 3
printf 'WORKLOAD_STEP2_COMPLETE\n'
