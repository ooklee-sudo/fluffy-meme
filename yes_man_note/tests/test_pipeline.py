"""End-to-end check with the mock backend: the analysis should recover the parameters the mock was built with
(noise-only model -> s* near 0; deferential model -> flat gradient; updater -> positive slope)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import ym_common as yc  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=True, capture_output=True, text=True)


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.items = os.path.join(cls.tmp, "items.jsonl")
        cls.models = os.path.join(ROOT, "tests", "mock_models.json")
        cls.res = os.path.join(cls.tmp, "res.jsonl")
        cls.out = os.path.join(cls.tmp, "out")
        run("make_mock_items.py", "--n", "600", "--out", cls.items)
        run("runner.py", "--items", cls.items, "--models", cls.models, "--out", cls.res, "--workers", "4")
        run("analyze.py", "--results", cls.res, "--models", cls.models, "--outdir", cls.out, "--boot", "300")
        with open(os.path.join(cls.out, "model_stats.json")) as f:
            cls.r = json.load(f)

    def stat(self, m, k):
        return self.r["models"][m]["stats"][k]

    def test_letters_identical_across_channels_and_balanced(self):
        its = yc.load_items(self.items)
        cfg = yc.load_stances()
        m = yc.load_models(self.models)[0]
        reqs = yc.enumerate_requests(m, its[:30], cfg)
        by_item = {}
        for q in reqs:
            if q.rot == 0:
                by_item.setdefault(q.item["id"], set()).add(tuple(sorted(q.letters.items())))
        self.assertTrue(all(len(v) == 1 for v in by_item.values()))
        gold = [yc.letters_for(i["id"])["gold"] for i in its]
        for L in "ABC":
            self.assertGreater(gold.count(L) / len(gold), 0.25)

    def test_neutral_matched_in_length(self):
        its = yc.load_items(self.items)
        cfg = yc.load_stances()
        gaps = [abs(len(yc.neutral_sentence(i, cfg).split()) -
                    len(yc.stance_sentence(i, "weak", "against", cfg).split())) for i in its]
        self.assertLessEqual(sum(gaps) / len(gaps), 3.0)

    def test_noise_only_model_has_raw_flip_but_no_corrected_effect(self):
        m = "mock-noisy-S"
        self.assertGreater(self.stat(m, "raw_s"), 0.12)          # large raw "deference" from instability
        self.assertAlmostEqual(self.stat(m, "s_star"), 0.0, delta=0.06)
        self.assertAlmostEqual(self.stat(m, "nu_U"), self.stat(m, "rho_U"), delta=0.09)

    def test_deferential_model_flat_gradient_and_corrected_effect_kept(self):
        m = "mock-deferential-L"
        self.assertAlmostEqual(self.stat(m, "s_star"), 0.28, delta=0.07)
        self.assertAlmostEqual(self.stat(m, "slope"), 0.0, delta=0.06)

    def test_updater_has_positive_slope_and_disclaimer_drop(self):
        m = "mock-updater-L"
        self.assertAlmostEqual(self.stat(m, "slope"), 0.15, delta=0.06)
        self.assertLess(self.stat(m, "disclaimer"), -0.02)

    def test_disclosed_accuracy_gradient_recovered(self):
        # acc_slope 0.30 per 30 points = 0.10 per +10 points (acc_s0 .35 keeps all levels inside [0, 1]); deferential mock is flat
        self.assertAlmostEqual(self.stat("mock-updater-L", "acc_slope"), 0.10, delta=0.04)
        self.assertAlmostEqual(self.stat("mock-deferential-L", "acc_slope"), 0.0, delta=0.03)
        self.assertAlmostEqual(self.stat("mock-updater-L", "acc_high_low"), 0.60, delta=0.10)   # 0.65 - 0.05, no clipping

    def test_parse_failures_reported(self):
        q = self.r["models"]["mock-updater-S"]["qc"]
        self.assertGreater(q["parse_failed"], 0)
        self.assertEqual(self.r["models"]["mock-noisy-S"]["qc"]["parse_failed"], 0)

    def test_resume_skips_finished_calls(self):
        def n_lines():
            with open(self.res) as f:
                return sum(1 for _ in f)
        before = n_lines()
        run("runner.py", "--items", self.items, "--models", self.models, "--out", self.res)
        self.assertEqual(before, n_lines())

    def test_outputs_written(self):
        for f in ("model_stats.json", "model_stats.csv", "summary.md"):
            self.assertTrue(os.path.exists(os.path.join(self.out, f)))


if __name__ == "__main__":
    unittest.main()
