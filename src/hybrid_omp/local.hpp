// Collective operations: every thread in the existing OpenMP team calls these.
#pragma once
#include <cstddef>

namespace pcg {
struct Tile {
    int nx, ny, nz; // 2D: nz = 1. Fastest index is x.
    std::size_t size() const {
        return std::size_t(nx) * ny * nz;
    }
    std::size_t ghost(std::size_t i) const {
        return ((i / nx / ny + 1) * (ny + 2) + i / nx % ny + 1) * (nx + 2) + i % nx + 1;
    }
};

// Direction has a one-cell ghost layer. Other vectors contain interiors only.
void omp_stencil(Tile t, int dim, double inv_h2, const double* direction, double* applied);
// Each thread returns its own partial sum; combine before the MPI reduction.
double omp_dot_partial(std::size_t n, const double* a, const double* b);
void omp_update(std::size_t n, double alpha, const double* direction, const double* applied,
                double* solution, double* residual, Tile t);
void omp_direction(Tile t, double beta, const double* residual, double* direction);
} // namespace pcg
