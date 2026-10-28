"""Paired analysis of the counterfactual prefix experiment (counterfactual.py).

Per entity and arm: share of continuation sentences (those after the prefix, with at least one claim) that contain a
contradicted claim. Effect = corrupt - clean, paired by entity; bootstrap CI over entities and Wilcoxon signed-rank.
Exclusions (main): pairs where the rewritten sentence still has a contradicted claim (clean arm not clean) or where the
original error sentence is no longer judged contradicted (corrupt arm not corrupt). Sensitivity: no exclusions.
Also: effect on the first K continuation sentences vs later, excluding 'dependent' errors (restating the prefix error),
and by whether the first error was the lead sentence.
"""
import argparse
import os

import numpy as np
from scipy.stats import wilcoxon

from common import DATA, read_jsonl


def arm_rate(arm, lo=0, hi=10 ** 9, drop=()):
    """Event rate over continuation sentences number lo+1..hi (counted after the prefix)."""
    npre = arm["n_prefix"]
    by = {}
    for c in arm["claims"]:
        k = c["sent"] - npre
        if k >= 1:
            by.setdefault(k, []).append(c["label"] if c["claim"] not in drop else "S")
    ks = [k for k in sorted(by) if lo < k <= hi]
    if not ks:
        return np.nan
    return float(np.mean(["C" in by[k] for k in ks]))


def paired(rows, drop_dep=False, **kw):
    a, b = [], []
    for r in rows:
        dep = set(r["dependent_claims"]) if drop_dep else ()
        a.append(arm_rate(r["arms"]["corrupt"], drop=dep, **kw))
        b.append(arm_rate(r["arms"]["clean"], **kw))
    a, b = np.array(a), np.array(b)
    ok = ~np.isnan(a) & ~np.isnan(b)
    return a[ok], b[ok]


def report(name, a, b, B=5000, seed=0):
    d = a - b
    rng = np.random.default_rng(seed)
    boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    try:
        p = wilcoxon(a, b).pvalue
    except ValueError:
        p = float("nan")
    print(f"{name:<44} n={len(d):<4} corrupt={a.mean():.3f} clean={b.mean():.3f} diff={d.mean():+.3f} [{lo:+.3f},{hi:+.3f}] p={p:.3g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cf", default=os.path.join(DATA, "cf_gemma-3-27b-it.jsonl"))
    a = ap.parse_args()
    allr = read_jsonl(a.cf)

    def pre_ok(r):
        np_ = r["arms"]["clean"]["n_prefix"]
        clean_bad = any(c["label"] == "C" for c in r["arms"]["clean"]["claims"] if c["sent"] == np_)
        corr_bad = any(c["label"] == "C" for c in r["arms"]["corrupt"]["claims"] if c["sent"] == r["arms"]["corrupt"]["n_prefix"])
        return (not clean_bad) and corr_bad

    rows = [r for r in allr if pre_ok(r)]
    print(f"{len(allr)} entities run; {len(rows)} kept (clean prefix really clean and corrupt prefix really wrong); "
          f"{len(allr) - len(rows)} excluded")
    print("\n-- main (kept pairs) --")
    report("all continuation sentences", *paired(rows))
    report("first 5 continuation sentences", *paired(rows, hi=5))
    report("sentences 6-10", *paired(rows, lo=5, hi=10))
    report("sentences 11+", *paired(rows, lo=10))
    print("\n-- repetition vs new errors --")
    n_dep = sum(len(r["dependent_claims"]) for r in rows)
    print(f"dependent errors flagged (corrupt arm): {n_dep} claims in {sum(1 for r in rows if r['dependent_claims'])} entities")
    report("all, dependent errors removed", *paired(rows, drop_dep=True))
    print("\n-- by where the first error was --")
    lead = [r for r in rows if r["s_star"] == 1]
    later = [r for r in rows if r["s_star"] > 1]
    report("lead sentence was wrong", *paired(lead))
    report("a later sentence (2-8) was wrong", *paired(later))
    print("\n-- sensitivity: no exclusions --")
    report("all continuation sentences", *paired(allr))


if __name__ == "__main__":
    main()
