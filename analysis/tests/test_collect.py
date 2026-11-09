"""Regress scientific data-selection and baseline failures using audited samples."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("collect", ROOT/"analysis/collect.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CollectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT/"analysis/datasets.json").read_text())
        cls.spec = cls.config["inputs"][0]
        cls.summary, cls.samples, cls.audit = c.read_input(ROOT/"results", cls.spec)
        cls.performance = cls.summary[~cls.summary.experiment.isin(cls.config["exclude_experiments"])]
        cls.derived = c.derive(cls.performance)

    def fixture(self, folder):
        result = Path(folder)
        spec = copy.deepcopy(self.spec)
        for suffix in spec["sha256"]:
            p = result/(spec["prefix"]+"_"+suffix)
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/"results"/(spec["prefix"]+"_"+suffix), p)
        return result, spec

    def replace_samples(self, result, spec, samples):
        p = result/(spec["prefix"]+"_samples.csv")
        samples.to_csv(p, index=False)
        audit_path = result/(spec["prefix"]+"_audit.json")
        audit = json.loads(audit_path.read_text())
        audit.update(sample_sha256=c.sha256(p), samples=len(samples))
        c.write_json(audit_path, audit)
        spec["sha256"]["samples.csv"] = c.sha256(p)
        spec["sha256"]["audit.json"] = c.sha256(audit_path)

    def test_only_performance_groups_are_selected(self):
        self.assertEqual(len(self.summary), 92)
        self.assertEqual(len(self.performance), 84)
        self.assertEqual(len(self.samples[self.samples.group.isin(self.performance.group)]), 252)
        self.assertFalse(self.derived.experiment.isin(["preflight", "pilot"]).any())

    def test_minimum_retains_matching_iteration_and_phase_row(self):
        row = c.one(self.summary, experiment="weak", dim=2, ranks=256)
        sample = c.one(self.samples, group=row.group, repeat=row["repeat"])
        for k in c.VALUES+["iters"]:
            self.assertEqual(row[k], sample[k])
        self.assertGreater(row.seconds_max, row.seconds_min*1.5)
        self.assertGreater(row.seconds_median, row.seconds_min)

    def test_strong_baseline_ignores_other_experiments_and_jobs(self):
        extra = self.performance[(self.performance.experiment == "strong") & (self.performance.ranks == 1)].copy()
        extra["job_id"] = "other-job"
        for k in ["seconds_min", "seconds_median", "seconds_max"]:
            extra[k] *= 1000
        df = c.derive(pd.concat([self.performance, extra], ignore_index=True))
        row = c.one(df, experiment="strong", job_id=self.audit["job_id"], dim=3, ranks=256, decomp="cart")
        self.assertAlmostEqual(row.speedup, 146.6325/1.064990)
        slab = c.one(df, experiment="strong", job_id=self.audit["job_id"], dim=3, ranks=256, decomp="slab")
        own_base = c.one(self.performance, experiment="strong", dim=3, ranks=1, decomp="slab")
        self.assertAlmostEqual(slab.speedup, own_base.seconds_min/slab.seconds_min)

    def test_one_core_ratio_is_exactly_one(self):
        for experiment, prefix in [("strong", "speedup"), ("weak", "weak_solve_ratio")]:
            rows = self.derived[(self.derived.experiment == experiment) & (self.derived.ranks == 1)]
            for suffix in ["", "_median", "_low", "_high"]:
                self.assertTrue((rows[prefix+suffix] == 1).all())

    def test_missing_or_ambiguous_baseline_is_an_error(self):
        base = self.performance[(self.performance.experiment == "strong") &
                                (self.performance.dim == 3) & (self.performance.ranks == 1) &
                                (self.performance.decomp == "cart")]
        with self.assertRaisesRegex(ValueError, "baseline must be unique"):
            c.derive(self.performance.drop(base.index))
        with self.assertRaisesRegex(ValueError, "baseline must be unique"):
            c.derive(pd.concat([self.performance, base], ignore_index=True))

    def test_weak_ratio_uses_changing_mesh_iteration_cost(self):
        row = c.one(self.derived, experiment="weak", dim=2, ranks=256)
        self.assertAlmostEqual(row.weak_solve_ratio, .009239568/2.126299)
        self.assertAlmostEqual(row.weak_iteration_ratio, (.009239568/392)/(2.126299/6512))
        self.assertEqual(row.weak_points_relative_to_base, 1)
        self.assertTrue(pd.isna(row.speedup))
        missing = [v for v in c.coverage(self.derived)["cpu_series"] if v["missing_ranks"]]
        self.assertEqual([(v["dim"], v["experiment"], v["missing_ranks"]) for v in missing], [(3,"weak",[256])])
        self.assertFalse(c.coverage(self.derived)["task3_complete"])

    def test_hybrid_uses_fixed_total_cores(self):
        rows = self.derived[self.derived.experiment == "hybrid"]
        self.assertTrue((rows.cores == 288).all())
        row = c.one(rows, dim=3, threads=72)
        self.assertAlmostEqual(row.matched_mpi_ratio, 1.060742/2.652749)
        self.assertTrue(pd.isna(row.efficiency))

    def test_phase_maxima_are_not_a_communication_fraction(self):
        self.assertNotIn("comm_frac", self.derived.columns)
        self.assertGreater(self.derived.phase_sum_over_total.max(), 1)

    def test_changed_export_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            result, spec = self.fixture(folder)
            p = result/(spec["prefix"]+"_samples.csv")
            with p.open("a") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                c.read_input(result, spec)

    def test_missing_repeat_is_rejected_even_with_updated_checksums(self):
        with tempfile.TemporaryDirectory() as folder:
            result, spec = self.fixture(folder)
            self.replace_samples(result, spec, self.samples.drop(index=self.samples.index[0]))
            with self.assertRaisesRegex(ValueError, "missing/duplicate repeat"):
                c.read_input(result, spec)

    def test_unconverged_sample_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            result, spec = self.fixture(folder)
            samples = self.samples.copy()
            samples.loc[samples.index[0], "rel_res"] = 1e-5
            self.replace_samples(result, spec, samples)
            with self.assertRaisesRegex(ValueError, "invalid convergence"):
                c.read_input(result, spec)

    def test_partial_suite_requires_explicit_opt_in(self):
        spec = copy.deepcopy(self.spec)
        spec["allow_documented_partial"] = False
        with self.assertRaisesRegex(ValueError, "unapproved partial suite"):
            c.read_input(ROOT/"results", spec)


if __name__ == "__main__":
    unittest.main()
