"""Screening table for the small-model replication (SMALL_MODELS_PLAN.md): pooled skip rate at 3 turns left, by frame, parse failures, refusals, pass/fail at 5%.
usage: python screen_report.py results\\w16_gpt5nano.jsonl results\\w16_gem25fl.jsonl ...
"""
import json, sys
from env import SKIPS

def main(paths):
    print(f"{'file':34} {'n':>6} {'skip%':>7} {'loss%':>7} {'gain%':>7} {'neutr%':>7} {'parse_fail':>10} {'refusal':>8}  screen (>=5%)")
    for p in paths:
        rows = []
        for line in open(p):
            try: r = json.loads(line)
            except json.JSONDecodeError: continue
            if r.get("turn") == 0 and r.get("n_fails") == 0 and int(r["t"]) == 9: rows.append(r)
        if not rows: print(f"{p:34} no 3-turn first choices"); continue
        sk = lambda g: 100 * sum(r["action"] in SKIPS for r in g) / len(g) if g else float("nan")
        by = lambda f: [r for r in rows if r["frame"] == f]
        pf = sum(bool(r["parse_fail"]) for r in rows); rf = sum(r.get("reason") == "REFUSAL" for r in rows)
        s = sk(rows); invalid = pf / len(rows) > 0.05
        print(f"{p[-34:]:34} {len(rows):>6} {s:>7.1f} {sk(by('loss')):>7.1f} {sk(by('gain')):>7.1f} {sk(by('neutral')):>7.1f} {pf:>10} {rf:>8}  {'INVALID (parse failures > 5%: rerun or exclude)' if invalid else ('PASS' if s >= 5 else 'floor')}")

if __name__ == "__main__":
    main(sys.argv[1:] or sys.exit(__doc__))
