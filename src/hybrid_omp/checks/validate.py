"""Check a hybrid binary (poisson_omp or poisson_cuda) against poisson_serial on small grids.

For 2D/3D, n = 15 and 31, one rank and --ranks ranks with slab and cart partitions:
  - same iteration count as the serial solver (+-1),
  - same err_l2 as the serial solver (1e-6 relative),
  - err_l2 falls by ~4x when h halves (second-order discretisation).
poisson_serial is expected next to the binary (build/bin/).
"""
import argparse
import csv
import math
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("binary", type=Path)
parser.add_argument("--launcher", default="mpiexec")
parser.add_argument("--ranks", type=int, default=4)
args = parser.parse_args()
impl = args.binary.name.split("_")[-1]
serial = args.binary.resolve().parent / "poisson_serial"


def run(cmd, path, env=None):
    subprocess.run(cmd + ["--csv", str(path)], check=True, env=env, stdout=subprocess.DEVNULL)
    with path.open() as stream:
        (row,) = csv.DictReader(stream)
    path.unlink()
    return row


with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / "row.csv"
    for dim in (2, 3):
        errors = []
        for n in (15, 31):
            ref = run([str(serial), "--dim", str(dim), "--n", str(n)], path)
            for ranks, decomp in ((1, "slab"), (args.ranks, "cart"), (args.ranks, "slab")):
                threads = 2 if impl == "omp" and ranks > 1 else 1
                row = run([args.launcher, "-n", str(ranks), str(args.binary.resolve()),
                           "--dim", str(dim), "--n", str(n), "--decomp", decomp, "--repeat", "2"],
                          path, env=dict(os.environ, OMP_NUM_THREADS=str(threads)))
                assert abs(int(row["iters"]) - int(ref["iters"])) <= 1, (row, ref)
                assert float(row["rel_res"]) < 1e-8, row
                assert row["impl"] == impl and int(row["ranks"]) == ranks, row
                assert int(row["threads"]) == threads, row
                assert int(row["gpus"]) == (ranks if impl == "cuda" else 0), row
                assert math.isclose(float(row["err_l2"]), float(ref["err_l2"]), rel_tol=1e-6), (row, ref)
            errors.append(float(row["err_l2"]))
        ratio = errors[0] / errors[1]
        assert 3.9 < ratio < 4.1, ratio
        print(f"{dim}D: six configurations match poisson_serial; error ratio {ratio:.5f}")
