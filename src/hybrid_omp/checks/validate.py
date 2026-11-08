"""Check a hybrid binary against the exact discrete sine eigenmode on small grids."""
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
with tempfile.TemporaryDirectory() as temp:
    for dim in (2, 3):
        errors = []
        for n in (15, 31):
            for ranks, decomp in ((1, "slab"), (args.ranks, "cart"), (args.ranks, "slab")):
                path = Path(temp) / "row.csv"
                threads = 2 if impl == "omp" and ranks > 1 else 1
                subprocess.run([args.launcher, "-n", str(ranks), str(args.binary.resolve()),
                                "--dim", str(dim), "--n", str(n), "--decomp", decomp,
                                "--repeat", "2", "--csv", str(path)], check=True,
                               env=dict(os.environ, OMP_NUM_THREADS=str(threads)), stdout=subprocess.DEVNULL)
                with path.open() as stream:
                    row, = csv.DictReader(stream)
                path.unlink()
                h = 1 / (n + 1)
                factor = (math.pi*h / (2*math.sin(math.pi*h/2)))**2
                expected = (factor-1)*2**(-dim/2)
                assert int(row["iters"]) == 1 and float(row["rel_res"]) < 1e-8, row
                assert row["impl"] == impl and int(row["ranks"]) == ranks, row
                assert int(row["threads"]) == threads, row
                assert int(row["gpus"]) == (ranks if impl == "cuda" else 0), row
                assert math.isclose(float(row["err_l2"]), expected, rel_tol=1e-6), row
            errors.append(float(row["err_l2"]))
        ratio = errors[0] / errors[1]
        assert 3.9 < ratio < 4.1, ratio
        print(f"{dim}D: six configurations passed; error ratio {ratio:.5f}")
