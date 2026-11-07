// Model problem shared by all implementations (owner: A).
//   -Laplace(u) = f  on (0,1)^d,  u = 0 on the boundary, d = 2 or 3.
// Manufactured solution: u(x) = prod_k sin(pi x_k), so f = d * pi^2 * u.
// Grid: n interior points per side, h = 1/(n+1), x_i = (i+1) h for i = 0..n-1.
// Discrete operator: standard 5-point (2D) / 7-point (3D) stencil scaled by 1/h^2.
#pragma once

#include <cmath>

namespace pcg {

inline double grid_h(long n) { return 1.0 / static_cast<double>(n + 1); }

inline double exact_u(int dim, double x, double y, double z) {
    const double pi = 3.14159265358979323846;
    double u = std::sin(pi * x) * std::sin(pi * y);
    return dim == 3 ? u * std::sin(pi * z) : u;
}

inline double rhs_f(int dim, double x, double y, double z) {
    const double pi = 3.14159265358979323846;
    return dim * pi * pi * exact_u(dim, x, y, z);
}

} // namespace pcg
