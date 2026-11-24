"""Compare two pipeline runs on the same units (e.g. a local 7B model vs a larger model).

Reports, per run, the tier and status distributions; cross-tabulations of status and tier; agreement on
whether a unit holds a claim (A1) and on whether it pushes away from care (H > 0); the rank correlation
of H; and the units where the runs disagree most, so they can be read side by side.

Status per unit is the most severe claim label: refuted > unsupported > contested > supported,
or no-claim / screened-out / ERROR when there are no claims.

    python compare_runs.py runs/pilot_v2/results.jsonl data/runs/pilot_qwen36plus/results.jsonl --names 7b large
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

import numpy as np
from scipy import stats

from reliability import kripp_alpha

SEVERITY = ["refuted", "unsupported", "contested", "supported"]
TIERS = {1: "Urgent", 2: "Review", 3: "Monitor"}


def load(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {r["unit_id"]: r for r in (json.loads(l) for l in f if l.strip())}


def status(r: dict) -> str:
    labels = [c["veracity"]["label"] for c in r["coded"]["claims"]]
    if labels:
        return min(labels, key=lambda l: SEVERITY.index(l) if l in SEVERITY else len(SEVERITY))
    if str(r.get("stage", "")).startswith("error"):
        return "ERROR"
    return "screened-out" if r.get("stage") == "screened_out" else "no-claim"


def crosstab(a: list, b: list, order: list, names) -> str:
    corner = f"{names[0]} / {names[1]}"
    rows = [f"{corner:<16}" + "".join(f"{o:>13}" for o in order)]
    for x in order:
        rows.append(f"{x:<16}" + "".join(f"{sum(1 for p, q in zip(a, b) if p == x and q == y):>13}" for y in order))
    return "\n".join(rows)


def main():
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--names", nargs=2, default=["A", "B"])
    ap.add_argument("--show", type=int, default=15, help="disagreements to list")
    a = ap.parse_args()
    A, B = load(a.run_a), load(a.run_b)
    ids = sorted(set(A) & set(B))
    if not ids:
        sys.exit("no common unit ids")
    na, nb = a.names
    print(f"{len(ids)} common units ({len(A)} in {na}, {len(B)} in {nb})\n")

    sa, sb = [status(A[i]) for i in ids], [status(B[i]) for i in ids]
    ta, tb = [TIERS[A[i]["tier"]] for i in ids], [TIERS[B[i]["tier"]] for i in ids]
    ha, hb = np.array([A[i]["H"] for i in ids]), np.array([B[i]["H"] for i in ids])
    for name, s, t, h in ((na, sa, ta, ha), (nb, sb, tb, hb)):
        print(f"{name:>6}: tiers {dict(Counter(t))}  status {dict(Counter(s))}  units with H>0: {int((h > 0).sum())}")

    st_order = [x for x in SEVERITY + ["no-claim", "screened-out", "ERROR"] if x in sa or x in sb]
    print("\nStatus (rows " + na + ", columns " + nb + ")\n" + crosstab(sa, sb, st_order, a.names))
    print("\nTier\n" + crosstab(ta, tb, ["Urgent", "Review", "Monitor"], a.names))

    claim_a = [int(s not in ("no-claim", "screened-out", "ERROR")) for s in sa]
    claim_b = [int(s not in ("no-claim", "screened-out", "ERROR")) for s in sb]
    push_a, push_b = (ha > 0).astype(int), (hb > 0).astype(int)
    rho = stats.spearmanr(ha, hb).statistic if ha.std() and hb.std() else float("nan")
    print(f"\nAgreement   has claim: {np.mean(np.array(claim_a) == np.array(claim_b)):.0%} "
          f"(alpha {kripp_alpha(claim_a, claim_b):.2f})   H>0: {np.mean(push_a == push_b):.0%} "
          f"(alpha {kripp_alpha(push_a.tolist(), push_b.tolist()):.2f})   "
          f"tier: {np.mean(np.array(ta) == np.array(tb)):.0%}   Spearman H: {rho:.2f}")

    order = sorted(range(len(ids)), key=lambda k: (-(ta[k] != tb[k]) * (abs(A[ids[k]]["tier"] - B[ids[k]]["tier"])),
                                                     -abs(ha[k] - hb[k])))
    print(f"\nLargest disagreements (tier first, then H):")
    for k in order[:a.show]:
        if ta[k] == tb[k] and abs(ha[k] - hb[k]) < 1e-9:
            break
        i = ids[k]
        print(f"- {i}  {na}: {ta[k]} H={ha[k]:.2f} {sa[k]}  |  {nb}: {tb[k]} H={hb[k]:.2f} {sb[k]}")
        print(f"    {' '.join(A[i]['text'].split())[:150]}")
        for name, R in ((na, A), (nb, B)):
            for c in R[i]["coded"]["claims"][:1]:
                print(f"    {name} claim: {c['claim_text'][:110]} | A4: {c['A4_recommended_care'][:40]}")


if __name__ == "__main__":
    main()
