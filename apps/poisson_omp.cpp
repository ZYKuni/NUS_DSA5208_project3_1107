#include "../src/hybrid_omp/domain.hpp"
#include "csv.hpp"
#include "params.hpp"
#include "problem.hpp"
#include "timer.hpp"
#include <cmath>
#include <iostream>
#include <omp.h>
#include <vector>

namespace pcg {
Result solve(const Params& p, const Domain& dom) {
    const Tile t = dom.tile;
    const auto n = t.size();
    const double h = grid_h(p.n);
    std::vector<double> exact(n), u(n), r(n), ap(n);
    std::vector<double> dir(std::size_t(t.nz + 2) * (t.ny + 2) * (t.nx + 2));
    double local = 0, initial = 0;
    for (std::size_t i = 0; i < n; ++i) {
        double x = (dom.origin[2] + i % t.nx + 1) * h,
               y = (dom.origin[1] + i / t.nx % t.ny + 1) * h;
        double z = (dom.origin[0] + i / t.nx / t.ny + 1) * h;
        exact[i] = exact_u(p.dim, x, y, z);
        r[i] = rhs_f(p.dim, x, y, z);
        dir[t.ghost(i)] = r[i];
        local += r[i] * r[i];
    }
    MPI_Allreduce(&local, &initial, 1, MPI_DOUBLE, MPI_SUM, dom.comm);
    Result out;
    MPI_Comm_size(dom.comm, &out.ranks);
    int rank;
    MPI_Comm_rank(dom.comm, &rank);
    double rho = initial, alpha = 0, beta = 0;
    PhaseTimer timer;
    MPI_Barrier(dom.comm);
    double start = MPI_Wtime();
    for (; out.iters < p.maxit && std::sqrt(rho / initial) >= p.tol; ++out.iters) {
        local = 0;
#pragma omp parallel
        {
#pragma omp master
            {
                out.threads = omp_get_num_threads();
                timer.start(Phase::Halo);
                dom.exchange(dir.data());
                timer.stop(Phase::Halo);
                timer.start(Phase::Stencil);
            }
#pragma omp barrier
            omp_stencil(t, p.dim, 1 / (h * h), dir.data(), ap.data());
#pragma omp master
            {
                timer.stop(Phase::Stencil);
                timer.start(Phase::Reduce);
            }
#pragma omp barrier
            double part = 0;
#pragma omp for nowait
            for (std::size_t i = 0; i < n; ++i)
                part += dir[t.ghost(i)] * ap[i];
#pragma omp atomic update
            local += part;
#pragma omp barrier
#pragma omp master
            {
                double denom;
                MPI_Allreduce(&local, &denom, 1, MPI_DOUBLE, MPI_SUM, dom.comm);
                alpha = rho / denom;
                local = 0;
                timer.stop(Phase::Reduce);
                timer.start(Phase::Stencil);
            }
#pragma omp barrier
            omp_update(n, alpha, dir.data(), ap.data(), u.data(), r.data(), t);
#pragma omp master
            {
                timer.stop(Phase::Stencil);
                timer.start(Phase::Reduce);
            }
#pragma omp barrier
            part = omp_dot_partial(n, r.data(), r.data());
#pragma omp atomic update
            local += part;
#pragma omp barrier
#pragma omp master
            {
                double next;
                MPI_Allreduce(&local, &next, 1, MPI_DOUBLE, MPI_SUM, dom.comm);
                beta = next / rho;
                rho = next;
                timer.stop(Phase::Reduce);
                timer.start(Phase::Stencil);
                if (p.verbose && rank == 0)
                    std::cerr << out.iters + 1 << " " << std::sqrt(rho / initial) << "\n";
            }
#pragma omp barrier
            omp_direction(t, beta, r.data(), dir.data());
        }
        timer.stop(Phase::Stencil);
    }
    MPI_Barrier(dom.comm);
    double times[]{MPI_Wtime() - start, timer.get(Phase::Stencil), timer.get(Phase::Halo),
                   timer.get(Phase::Reduce)};
    double maxima[4]{};
    MPI_Allreduce(times, maxima, 4, MPI_DOUBLE, MPI_MAX, dom.comm);
    local = 0;
    for (std::size_t i = 0; i < n; ++i)
        local += (u[i] - exact[i]) * (u[i] - exact[i]);
    double err;
    MPI_Allreduce(&local, &err, 1, MPI_DOUBLE, MPI_SUM, dom.comm);
    out.impl = "omp";
    out.dim = p.dim;
    out.n = p.n;
    out.decomp = p.decomp;
    out.halo = p.halo;
    out.cg = p.cg;
    out.t_total = maxima[0];
    out.t_stencil = maxima[1];
    out.t_halo = maxima[2];
    out.t_reduce = maxima[3];
    out.err_l2 = std::sqrt(err * std::pow(h, p.dim));
    out.rel_res = std::sqrt(rho / initial);
    return out;
}
} // namespace pcg

int main(int argc, char** argv) {
    const auto p = pcg::parse_args(argc, argv);
    int provided, rank;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    int status = 0;
    try {
        if (provided < MPI_THREAD_FUNNELED || p.cg != "std" || p.halo != "block")
            throw std::runtime_error(
                "OpenMP baseline requires FUNNELED, --cg std and --halo block");
        pcg::Domain dom(p.n, p.dim, p.decomp == "slab");
        pcg::Result best;
        for (int rep = 0; rep < p.repeat; ++rep) {
            auto row = pcg::solve(p, dom);
            if (rep == 0 || row.t_total < best.t_total)
                best = row;
        }
        if (rank == 0) {
            std::cout << pcg::csv_header() << "\n" << pcg::csv_row(best) << "\n";
            if (!p.csv.empty())
                pcg::csv_append(p.csv, best);
        }
        status = !(best.rel_res < p.tol);
    } catch (const std::exception& e) {
        if (rank == 0)
            std::cerr << e.what() << "\n";
        status = 1;
    }
    MPI_Finalize();
    return status;
}
