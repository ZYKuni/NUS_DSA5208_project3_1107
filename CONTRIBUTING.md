# 小组统一规范

所有人写代码、跑实验、写报告前先读这一页。改动这里的约定要在群里说一声。

## 分工

| 成员 | 负责目录 | 报告章节 |
| --- | --- | --- |
| A Yikun Zhao | `src/common` `src/serial` `src/mpi` `apps/poisson_serial.cpp` `apps/poisson_mpi.cpp` `tests/` `README.md` | 1 引言、3 MPI 设计、5 验证、9 结论，统稿 |
| B Jiahao Zhou | `src/hybrid_omp` `src/hybrid_cuda` `apps/poisson_omp.cpp` `apps/poisson_cuda.cpp` | 4 MPI+X 设计、8 MPI+X 与 GPU 结果 |
| C Zheke Chen | `scripts/` `analysis/` `CMakeLists.txt` `results/` | 2 串行数据、6 实验环境、7 MPI 扩展性结果，全部图 |

## Git 流程

- `main` 只通过 PR 合入，至少另一人看过再合。
- 分支名：`a/<主题>`、`b/<主题>`、`c/<主题>`，例如 `a/mpi-cart`。
- 提交信息用英文祈使句，例如 `Add overlapped halo exchange`。
- 不提交 `build/`、PBS 输出（`*.o12345`）、原始 log。老师明确要求不要提交 log。

## 代码约定

- C++17，命名空间 `pcg`，4 空格缩进，提交前跑 `clang-format -i`（配置见 `.clang-format`）。
- 禁止使用 BLAS / LAPACK / cuBLAS / PETSc 等线性代数库（课程规定）。
- 所有可执行文件必须用 `include/params.hpp` 的 `parse_args`，命令行参数完全一致。
- 所有可执行文件必须通过 `include/csv.hpp` 的 `csv_append` 输出结果，只在 rank 0 写。
- 模型问题统一用 `include/problem.hpp`：n 为每边内部点数，h = 1/(n+1)，制造解为 sin 乘积。
- 网格存储按行主序，最后一维变化最快；局部数组含一层 ghost（halo）。

## 计时约定

- `t_total` 只计 CG 求解循环，不含初始化、分配和输出；计时前后各 `MPI_Barrier` 一次。
- 用 `PhaseTimer` 把时间分到三段：`Stencil`（矩阵向量乘与向量更新）、`Halo`（邻居通信）、`Reduce`（点积与 Allreduce）。
- 各段报告所有 rank 的最大值（`MPI_Reduce` with `MPI_MAX`）。
- GPU 版本计时前后要 `cudaDeviceSynchronize()`。
- 每个配置 `--repeat 3`，取最快一次。

## 收敛与正确性

- 停止条件：‖r‖₂ / ‖b‖₂ < `tol`（默认 1e-8），初值 u = 0。
- 每个实现都要报告 `rel_res` 和 `err_l2`（离散 L2 误差，乘以 h^(d/2)）。
- 并行版本与串行版在同一 n 下的迭代次数应一致（允许 ±1），`err_l2` 相对差 < 1e-6。

## 实验约定

- 坐标轴：时间、问题规模、核数一律对数坐标（课程要求）。
- MPI 必须测到 ≥ 256 核：Vanda 4 节点 × 72 核 = 288 核。strong 和 weak 都要做。
- 结果 CSV 放 `results/`，文件名 `<实验>_<impl>_<dim>d.csv`，由 `analysis/collect.py` 合并。

## AI 使用记录

每人在 `report/ai_usage.md` 自己那一节记录：用了什么工具、做了什么、哪些代码或文字来自 AI、自己如何检查。报告最后一节由此汇总。
