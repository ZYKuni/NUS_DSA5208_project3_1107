#!/bin/bash
# Usage: scripts/build.sh [cpu|cuda] [build_dir]
#   cpu  (default): serial + MPI + MPI/OpenMP
#   cuda          : additionally MPI/CUDA
set -euo pipefail
MODE=${1:-cpu}
BUILD=${2:-build}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXTRA=()
if [ "$MODE" = "cuda" ]; then EXTRA+=(-DENABLE_CUDA=ON); fi
cmake -S "$ROOT" -B "$ROOT/$BUILD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=mpicxx "${EXTRA[@]}"
cmake --build "$ROOT/$BUILD" -j
ctest --test-dir "$ROOT/$BUILD" --output-on-failure
