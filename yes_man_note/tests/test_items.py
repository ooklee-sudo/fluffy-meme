"""The generator's keys must survive the independent solver, and the audit must actually catch defects."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import audit_items as au  # noqa: E402
import generate_items as gi  # noqa: E402
import ym_common as yc  # noqa: E402


def sh(*args, check=True):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, check=check)


class Items(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = gi.generate(30, seed=11)
        cls.cfg = yc.load_stances()
        cls.tmp = tempfile.mkdtemp()

    def write(self, items, name):
        p = os.path.join(self.tmp, name)
        with open(p, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        return p

    def test_clean_bank_passes(self):
        problems, solved, _, _ = au.check_items(self.items, self.cfg)
        self.assertEqual(problems, [])
        self.assertEqual({d: v[1] for d, v in solved.items()}, {d: 0 for d in gi.DOMAINS})

    def test_generation_is_deterministic(self):
        self.assertEqual(gi.generate(5, seed=3), gi.generate(5, seed=3))
        self.assertNotEqual(gi.generate(5, seed=3), gi.generate(5, seed=4))

    def test_wrong_key_is_caught(self):
        items = json.loads(json.dumps(self.items))
        bad = items[0]
        bad["gold_action"], bad["unsup_action"] = bad["unsup_action"], bad["gold_action"]
        problems, *_ = au.check_items(items, self.cfg)
        self.assertTrue(any(p.startswith(bad["id"]) and "independent solve" in p for p in problems))

    def test_stem_edit_that_changes_the_answer_is_caught(self):
        items = json.loads(json.dumps(self.items))
        it = next(x for x in items if x["domain"] == "D3")
        it["stem"] = it["stem"].replace("credit of $", "credit of $1")
        problems, *_ = au.check_items(items, self.cfg)
        self.assertTrue(any(p.startswith(it["id"]) for p in problems))

    def test_ungrammatical_action_is_caught(self):
        items = json.loads(json.dumps(self.items))
        it = next(x for x in items if x["domain"] == "D2")
        it["unsup_action"] = "outside the policy limit"
        problems, *_ = au.check_items(items, self.cfg)
        self.assertTrue(any("bare-infinitive" in p for p in problems))

    def test_three_options_always_distinct_and_unsup_is_a_real_mistake(self):
        for it in self.items:
            self.assertEqual(len({it["gold_action"], it["unsup_action"], it["third_action"]}), 3)

    def test_d4_covers_all_three_kinds(self):
        kinds = {it["meta"]["kind"] for it in self.items if it["domain"] == "D4"}
        self.assertEqual(kinds, {"approve", "reject", "request"})

    def test_review_export_import_roundtrip(self):
        p = self.write(self.items, "items.jsonl")
        sheet = os.path.join(self.tmp, "review.csv")
        sh("audit_items.py", "--items", p, "--export-review", sheet)
        with open(sheet, newline="") as f:
            rows = list(csv.DictReader(f))
        key = {it["id"]: yc.letters_for(it["id"])["gold"] for it in self.items}
        rows[0]["reviewer_answer"] = key[rows[0]["id"]]
        wrong = next(L for L in "ABC" if L != key[rows[1]["id"]])
        rows[1]["reviewer_answer"] = wrong
        with open(sheet, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        flag = os.path.join(self.tmp, "flag.txt")
        out = sh("audit_items.py", "--items", p, "--import-review", sheet, "--flag-out", flag).stdout
        self.assertIn("1 agree", out)
        with open(flag) as f:
            self.assertEqual(f.read().split(), [rows[1]["id"]])

    def test_pilot_screen_runs_on_mock_results(self):
        p = self.write(self.items, "items.jsonl")
        models = os.path.join(ROOT, "tests", "mock_models.json")
        res = os.path.join(self.tmp, "pilot.jsonl")
        sh("runner.py", "--items", p, "--models", models, "--out", res, "--channels", "C1,C3", "--workers", "4")
        out = sh("audit_items.py", "--items", p, "--pilot", res, check=False).stdout
        self.assertIn("gate mean_accuracy", out)
        self.assertIn("items with mixed outcomes", out)


if __name__ == "__main__":
    unittest.main()
