"""H5 and H10 analysis (PREREGISTRATION_H5_H7.md).

H5 primary: for each brand, the primary judge's win rate of LoRA r=1 over RAG-8 on "overall" (ties count
one half); Wilcoxon signed-rank test of (win rate - 0.5) across brands, two-sided, alpha 0.05.
H10 primary: rank brands by response type-token ratio, lowest first; personalize the top third; share of the
total LoRA r=1 relative gain (NLL) captured, against all random choices of the same size (permutation test,
two-sided, 20,000 draws).

Usage: python analyze_h5.py results/h5_gen results/h5_judge.jsonl
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import wilcoxon

PRIMARY_JUDGE = "anthropic/claude-haiku-5.5"
CRITERIA = ["overall", "voice", "helpfulness"]


def oriented(r):
    """The verdict with A/B mapped back to the method names, plus per-method flags."""
    a, b = (r["second"], r["first"]) if r["flip"] else (r["first"], r["second"])
    v = r["verdict"]
    win = {}
    for c in CRITERIA:
        x = str(v.get(c, "tie")).strip().upper()
        win[c] = a if x == "A" else b if x == "B" else "tie"
    flags = {a: dict(unsupported=bool(v.get("unsupported_A")), send=bool(v.get("send_as_is_A"))),
             b: dict(unsupported=bool(v.get("unsupported_B")), send=bool(v.get("send_as_is_B")))}
    return win, flags


def kappa(x, y):
    cats = sorted(set(x) | set(y))
    n = len(x)
    po = sum(i == j for i, j in zip(x, y)) / n
    pe = sum((x.count(c) / n) * (y.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    gen_dir = sys.argv[1] if len(sys.argv) > 1 else "results/h5_gen"
    jpath = sys.argv[2] if len(sys.argv) > 2 else "results/h5_judge.jsonl"
    gens = {json.load(open(p))["brand"]: json.load(open(p)) for p in glob.glob(os.path.join(gen_dir, "*.json"))}
    recs = [json.loads(l) for l in open(jpath)]
    print(f"{len(gens)} brands generated; {len(recs)} judgments "
          f"(${sum(r.get('cost', 0) for r in recs):.2f})\n")

    by = defaultdict(lambda: defaultdict(list))  # (first, second) -> brand -> list of (win dict, flags)
    for r in recs:
        if r["judge"] == PRIMARY_JUDGE:
            by[(r["first"], r["second"])][r["brand"]].append(oriented(r))

    def winrate(items, m, c):
        return np.mean([1.0 if w[c] == m else 0.5 if w[c] == "tie" else 0.0 for w, _ in items])

    for (a, b), brands in by.items():
        names = sorted(brands)
        print(f"=== {a} vs {b} ({len(names)} brands, {sum(len(v) for v in brands.values())} comparisons) ===")
        for c in CRITERIA:
            wr = np.array([winrate(brands[n], a, c) for n in names])
            d = wr - 0.5
            p = wilcoxon(d).pvalue if not np.allclose(d, 0) else float("nan")
            tag = "  <- PRIMARY H5" if (a, b) == ("lora:1", "rag-8") and c == "overall" else ""
            print(f"  {c:<12} mean win rate of {a}: {wr.mean():.3f}  (brands above 0.5: {(d > 0).sum()}/{len(d)}, "
                  f"below: {(d < 0).sum()})  Wilcoxon p = {p:.4f}{tag}")
        for m in (a, b):
            fl = [f[m] for v in brands.values() for _, f in v]
            print(f"  {m:<10} send as is {np.mean([x['send'] for x in fl]):.3f}   "
                  f"unsupported claims {np.mean([x['unsupported'] for x in fl]):.3f}")
        print()

    # second judge agreement on the primary pair
    pj = {r["key"]: oriented(r)[0]["overall"] for r in recs if r["judge"] == PRIMARY_JUDGE}
    sj = {r["key"]: oriented(r)[0]["overall"] for r in recs if r["judge"] != PRIMARY_JUDGE}
    common = sorted(set(pj) & set(sj))
    if common:
        x, y = [pj[k] for k in common], [sj[k] for k in common]
        print(f"second judge on {len(common)} primary comparisons: agreement {np.mean([i == j for i, j in zip(x, y)]):.3f}, "
              f"Cohen's kappa {kappa(x, y):.3f}; second judge's LoRA win rate "
              f"{np.mean([1 if j == 'lora:1' else 0.5 if j == 'tie' else 0 for j in y]):.3f}\n")

    # H10: decision rule on NLL relative gain
    names = sorted(gens)
    gain = np.array([gens[n]["rel_gain"]["lora:1"] for n in names])
    ttr = np.array([gens[n]["features"]["response_type_token_ratio"] for n in names])
    k = round(len(names) / 3)
    pick = np.argsort(ttr, kind="stable")[:k]
    share = gain[pick].sum() / gain.sum()
    oracle = np.sort(gain)[::-1][:k].sum() / gain.sum()
    rng = np.random.default_rng(0)
    draws = np.array([gain[rng.choice(len(gain), k, replace=False)].sum() / gain.sum() for _ in range(20000)])
    p = 2 * min((draws >= share).mean(), (draws <= share).mean())
    print(f"H10 (n = {len(names)}, top {k}): type-token-ratio rule captures {share:.1%} of total LoRA gain; "
          f"random {draws.mean():.1%}; oracle {oracle:.1%}; permutation p = {min(p, 1):.4f} (two-sided)")


if __name__ == "__main__":
    main()
