#include "local.hpp"

namespace pcg {
void omp_stencil(Tile t, int dim, double inv_h2, const double* direction, double* applied) {
    const std::size_t sy = t.nx + 2, sz = sy * (t.ny + 2);
#pragma omp for schedule(static)
    for (std::size_t i = 0; i < t.size(); ++i) {
        const auto j = t.ghost(i);
        double v = 2 * dim * direction[j] - direction[j - 1] - direction[j + 1] -
                   direction[j - sy] - direction[j + sy];
        if (dim == 3)
            v -= direction[j - sz] + direction[j + sz];
        applied[i] = inv_h2 * v;
    }
}

double omp_dot_partial(std::size_t n, const double* a, const double* b) {
    double part = 0;
#pragma omp for schedule(static) nowait
    for (std::size_t i = 0; i < n; ++i)
        part += a[i] * b[i];
    return part;
}

void omp_update(std::size_t n, double alpha, const double* direction, const double* applied,
                double* solution, double* residual, Tile t) {
#pragma omp for schedule(static)
    for (std::size_t i = 0; i < n; ++i) {
        solution[i] += alpha * direction[t.ghost(i)];
        residual[i] -= alpha * applied[i];
    }
}

void omp_direction(Tile t, double beta, const double* residual, double* direction) {
#pragma omp for schedule(static)
    for (std::size_t i = 0; i < t.size(); ++i) {
        auto j = t.ghost(i);
        direction[j] = residual[i] + beta * direction[j];
    }
}
} // namespace pcg
