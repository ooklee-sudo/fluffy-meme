"""Summarize the Phase 3 pilot (exploratory): does capacity demand rise with task size, and how does the
TT-vs-LoRA gap move with it?

Capacity demand of a task instance = LoRA r=16 minus LoRA r=1 (relative gain, and accuracy for facts).
Gaps at matched budgets: TT r=7 - LoRA r=1 (~0.7M params) and TT r=31 - LoRA r=16 (~11.5M params).

Usage: python analyze_pilot.py [results/phase3_pilot]
"""
import glob
import json
import os
import sys


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/phase3_pilot"
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    rows.sort(key=lambda r: (r["task"], r["n_facts"] or 0))
    if not rows:
        raise SystemExit(f"no results in {d}")
    print(f"{'instance':<22}{'steps':>6}  {'config':<9}{'params':>12}{'rel gain':>10}{'acc':>8}{'best step':>11}")
    for r in rows:
        acc0 = "" if r["acc_none"] is None else f"{r['acc_none']:.3f}"
        print(f"{r['name']:<22}{r['steps']:>6}  {'none':<9}{0:>12,}{0:>10.4f}{acc0:>8}")
        for x in r["runs"]:
            acc = "" if x["acc"] is None else f"{x['acc']:.3f}"
            print(f"{'':<28}{x['config']:<9}{x['params']:>12,}{x['rel_gain']:>10.4f}{acc:>8}{x['best_step']:>11}")
    print(f"\n{'instance':<22}{'demand (gain)':>14}{'demand (acc)':>13}{'TT7-L1 gain':>13}{'TT31-L16 gain':>15}"
          f"{'TT7-L1 acc':>12}{'TT31-L16 acc':>14}")
    for r in rows:
        g = {x["config"]: x for x in r["runs"]}
        if not all(c in g for c in ("lora:1", "lora:16", "tt:7", "tt:31")):
            continue
        dg = g["lora:16"]["rel_gain"] - g["lora:1"]["rel_gain"]
        a = lambda c: g[c]["acc"] if g[c]["acc"] is not None else float("nan")
        print(f"{r['name']:<22}{dg:>+14.4f}{a('lora:16') - a('lora:1'):>+13.3f}"
              f"{g['tt:7']['rel_gain'] - g['lora:1']['rel_gain']:>+13.4f}{g['tt:31']['rel_gain'] - g['lora:16']['rel_gain']:>+15.4f}"
              f"{a('tt:7') - a('lora:1'):>+12.3f}{a('tt:31') - a('lora:16'):>+14.3f}")
    print("\nThe pilot works if capacity demand rises with N (and is clearly positive for the largest N or math);"
          "\nthat is what the preregistered H3 test needs. Learning rates are still Phase 2's, so gaps are provisional.")


if __name__ == "__main__":
    main()
