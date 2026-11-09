"""Regress the missing serial reference at the rounded 256-rank weak mesh."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('cpu_plan',Path(__file__).resolve().parents[1]/'run_cpu_scaling.py')
plan=importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class PlanTest(unittest.TestCase):
    def test_rounded_3d_mesh_and_reference_coverage(self):
        cases=plan.weak_cases(3,32,[1,8,64,216,256])
        self.assertEqual(cases[-1],(256,203))
        self.assertTrue({n for p,n in cases}.issubset(plan.serial_sizes(3)))

    def test_exact_2d_weak_volume(self):
        for p,n in plan.weak_cases(2,128,[1,4,16,64,256]):
            self.assertEqual(n*n//p,128*128)


if __name__=='__main__':unittest.main()
