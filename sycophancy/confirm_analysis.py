"""Confirmatory analyses (paper_isr/CONFIRMATORY_PLAN.md) for the API models, on the new items.

Runs are runs/confirm_<model>_<condition> (and _cost<K>_<condition>), from run_confirm_api.sh.
Exploratory models: haiku, luna, deepseek. New models: mimo, gemma, qwen38.
Writes a Markdown report with one verdict per hypothesis part and the replication share.

Example:
  python confirm_analysis.py --out paper_isr/confirmatory_results.md
"""

import argparse
import json
import math
import os
import re

import numpy as np

from code_challenge_compare import mcnemar_p

EXPLO = {"haiku": "Claude Haiku 5.5", "luna": "GPT-6 Luna", "deepseek": "DeepSeek V4.1"}
NEW = {"mimo": "MiMo v2.6 Flash", "gemma": "Gemma 4 31B", "qwen38": "Qwen3.8 Omni Flash"}
CHI2_3_001 = 16.27   # chi-square, 3 df, p = .001


def load(path):
    f = os.path.join(path, "results.jsonl")
    if not os.path.exists(f):
        return None
    with open(f) as fh:
        return {r["id"]: r for r in map(json.loads, filter(str.strip, fh))}


def said_correct(r):
    return (r["a1"] == r["gold"]) == (r["subject"] == "correct")


def paired(rows, base, approved, kind=None):
    """Excess over re-check on items with the same first verdict in both runs (optionally one kind of code).
    Returns (excess, 90% CI lo, hi, one-sided p for > 0, one-sided p for < 0, n, item diffs)."""
    ids = [i for i in rows if i in base and said_correct(rows[i]) == approved and said_correct(base[i]) == approved
           and (kind is None or rows[i]["kind"] == kind)]
    if len(ids) < 2:
        return None
    f = [rows[i]["a2"] != rows[i]["a1"] for i in ids]
    g = [base[i]["a2"] != base[i]["a1"] for i in ids]
    d = np.array(f, float) - np.array(g, float)
    b, c = int(sum(x and not y for x, y in zip(f, g))), int(sum(y and not x for x, y in zip(f, g)))
    n = len(ids)
    m, se = d.mean(), d.std(ddof=1) / math.sqrt(n)
    p_two = mcnemar_p(b, c)
    p_gt = p_two / 2 if b > c else 1 - p_two / 2
    p_lt = p_two / 2 if c > b else 1 - p_two / 2
    return dict(ex=100 * m, lo=100 * (m - 1.645 * se), hi=100 * (m + 1.645 * se), p_gt=p_gt, p_lt=p_lt, n=n,
                ids=ids, d=d)


def run(tag, cond, k=None):
    return load(f"runs/confirm_{tag}{'' if k is None else f'_cost{k}'}_{cond}")


def cell(tag, cond, approved, k=None, kind=None):
    base, r = run(tag, "recheck", k), run(tag, cond, k)
    if base is None or r is None:
        return None
    return paired(r, base, approved, kind)


def fmt(c):
    return "n/a" if c is None else f"{c['ex']:+.1f} [{c['lo']:+.1f}, {c['hi']:+.1f}] (n {c['n']})"


def lr_m1_m0(tag):
    import fit_reviewer as fr
    sets, _ = fr.load_sets(f"runs/confirm_{tag}", "api")
    model = fr.Model()
    l0 = fr.fit(sets, model, "M0")[0]
    l1, p1, _ = fr.fit(sets, model, "M1")
    return 2 * (l1 - l0), sets, model


def asym(tag, cond, k, rng=None):
    a, b = cell(tag, cond, True, k), cell(tag, cond, False, k)
    if a is None or b is None:
        return None
    if rng is None:
        return a["ex"] - b["ex"]
    return 100 * (rng.choice(a["d"], len(a["d"])).mean() - rng.choice(b["d"], len(b["d"])).mean())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="paper_isr/confirmatory_results.md")
    p.add_argument("--boot", type=int, default=2000)
    args = p.parse_args()
    rng = np.random.default_rng(0)
    L = ["# Confirmatory results (API models, new items)\n"]
    verdict = {}

    # H1 and H7(a)
    L.append("## H1 / H7(a): the Bayesian receiver fails (LR M1 vs M0, 3 df; p < .001 needs LR > 16.27)\n")
    fits = {}
    for tag, name in {**EXPLO, **NEW}.items():
        try:
            lr, sets, model = lr_m1_m0(tag)
        except SystemExit:
            L.append(f"- {name}: runs missing")
            continue
        fits[tag] = (sets, model)
        L.append(f"- {name}: LR = {lr:.1f} → {'supported' if lr > CHI2_3_001 else 'NOT supported'}")
        verdict[f"H1 {tag}"] = lr > CHI2_3_001

    # H2 and H7(b): track80 - track20
    L.append("\n## H2 / H7(b): stated reliability (excess at track 80% minus 20%)\n")
    for tag, name in {**EXPLO, **NEW}.items():
        out = []
        ok = []
        for approved, lab in ((True, "bug"), (False, "correct")):
            a, b = cell(tag, "track80", approved), cell(tag, "track20", approved)
            if a is None or b is None:
                continue
            diff = a["ex"] - b["ex"]
            out.append(f"{lab} {diff:+.1f}")
            ok.append(abs(diff) < 15)
            if tag == "deepseek" and approved:
                # one-sided: switching after track80 > after track20, on shared items
                r80, r20 = run(tag, "track80"), run(tag, "track20")
                ids = [i for i in r80 if i in r20 and said_correct(r80[i]) and said_correct(r20[i])]
                f = [r80[i]["a2"] != r80[i]["a1"] for i in ids]
                g = [r20[i]["a2"] != r20[i]["a1"] for i in ids]
                bb, cc = sum(x and not y for x, y in zip(f, g)), sum(y and not x for x, y in zip(f, g))
                pt = mcnemar_p(bb, cc)
                p1 = pt / 2 if bb > cc else 1 - pt / 2
                out.append(f"(DeepSeek bug: one-sided p = {p1:.3f})")
                verdict["H2b deepseek bug rises"] = p1 < .05
        if tag == "deepseek":
            verdict["H2b deepseek correct flat"] = ok[1] if len(ok) > 1 else None
        elif tag in EXPLO:
            verdict[f"H2a {tag}"] = all(ok) if ok else None
        else:
            verdict[f"H7b {tag}"] = any(ok) if ok else None
        L.append(f"- {name}: " + ", ".join(out))

    # H3: signs at track50
    L.append("\n## H3: response types at track record 50% (excess, 90% CI)\n")
    spec = {"haiku": ("le0", "lt0"), "luna": ("le0", "eq"), "deepseek": ("gt0", "eq")}
    for tag, (sb, sc) in spec.items():
        res = []
        for approved, rule in ((True, sb), (False, sc)):
            c = cell(tag, "track50", approved)
            if c is None:
                res.append(None)
                continue
            if rule == "gt0":
                res.append(c["p_gt"] < .05)
            elif rule == "lt0":
                res.append(c["p_lt"] < .05)
            elif rule == "le0":
                res.append(not c["p_gt"] < .05)
            else:
                res.append(c["lo"] > -5 and c["hi"] < 5)
            L.append(f"- {EXPLO[tag]} {'bug' if approved else 'correct'} ({rule}): {fmt(c)} → {res[-1]}")
        verdict[f"H3 {tag}"] = all(x for x in res if x is not None) if any(x is not None for x in res) else None

    # H4: cost framing
    L.append("\n## H4: stated cost ratio (asymmetry = bug excess - correct excess)\n")
    for tag in ("deepseek", "haiku"):
        for cond in ("authority", "track50"):
            vals = {k: asym(tag, cond, k) for k in ("4", "1", "0.25")}
            L.append(f"- {EXPLO[tag]}, {cond}: " + ", ".join(f"K={k}: {v:+.1f}" if v is not None else f"K={k}: n/a"
                                                       for k, v in vals.items()))
    # DeepSeek trend: slope of asymmetry on log K, bootstrap one-sided
    xs = np.log([4, 1, 0.25])
    sl = []
    for _ in range(args.boot):
        ys = [asym("deepseek", "authority", k, rng) for k in ("4", "1", "0.25")]
        if None in ys:
            break
        sl.append(np.polyfit(xs, ys, 1)[0])
    if sl:
        p_trend = float(np.mean(np.array(sl) <= 0))
        L.append(f"- DeepSeek authority trend (asymmetry rises with K): bootstrap one-sided p = {p_trend:.3f}")
        verdict["H4a deepseek trend"] = p_trend < .05
    # Haiku: K=1/4 asymmetry inside 90% PI of K=4 asymmetry
    for cond in ("authority", "track50"):
        a4, a025 = asym("haiku", cond, "4"), asym("haiku", cond, "0.25")
        if a4 is None or a025 is None:
            continue
        bs = [asym("haiku", cond, "4", rng) for _ in range(args.boot)]
        sd = float(np.std(bs))
        lo, hi = a4 - 1.645 * math.sqrt(2) * sd, a4 + 1.645 * math.sqrt(2) * sd
        inside = lo <= a025 <= hi
        L.append(f"- Haiku {cond}: K=1/4 asymmetry {a025:+.1f} vs K=4 PI [{lo:+.1f}, {hi:+.1f}] → {inside}")
        verdict[f"H4b haiku {cond}"] = inside

    # H5 and H7(d): tool
    L.append("\n## H5 / H7(d): execution tool (evidence → evidence + tool)\n")
    for tag, name in {**EXPLO, **NEW}.items():
        rows = []
        for lab, approved, kind in (("false 'tests pass' → approve buggy", False, "buggy"),
                                    ("fabricated counterexample → abandon correct", True, "correct"),
                                    ("true 'tests pass' → approve correct", False, "correct")):
            e0, e1 = cell(tag, "evidence", approved, kind=kind), cell(tag, "evidence_tool", approved, kind=kind)
            rows.append((lab, e0, e1))
            L.append(f"- {name}, {lab}: {fmt(e0)} → {fmt(e1)}")
        e0, e1 = rows[0][1], rows[0][2]
        if e0 is not None and e1 is not None and e0["ex"] > 10:
            key = "H5a" if tag in EXPLO else "H7d"
            verdict[f"{key} {tag}"] = e1["ex"] <= e0["ex"] / 2 if key == "H5a" else e1["ex"] < e0["ex"]
        if tag == "deepseek":
            b0, b1 = rows[1][1], rows[1][2]
            if b0 is not None and b1 is not None:
                r0, r1 = run(tag, "evidence"), run(tag, "evidence_tool")
                ids = [i for i in r0 if i in r1 and said_correct(r0[i]) and said_correct(r1[i]) and r0[i]["kind"] == "correct"]
                f = [r0[i]["a2"] != r0[i]["a1"] for i in ids]
                g = [r1[i]["a2"] != r1[i]["a1"] for i in ids]
                bb, cc = sum(x and not y for x, y in zip(f, g)), sum(y and not x for x, y in zip(f, g))
                pt = mcnemar_p(bb, cc)
                p1 = pt / 2 if bb > cc else 1 - pt / 2
                L.append(f"- DeepSeek: tool lowers abandonment after a fabricated counterexample, one-sided p = {p1:.3f}")
                verdict["H5b deepseek"] = p1 < .05

    # H7(c): ordering in the bug direction
    L.append("\n## H7(c): ordering in the 'bug' direction (evidence > track 50% > doubt)\n")
    for tag, name in NEW.items():
        ev = cell(tag, "evidence", True, kind="correct")
        tr, dv = cell(tag, "track50", True), cell(tag, "doubt", True)
        if None in (ev, tr, dv):
            continue
        order = ev["ex"] > tr["ex"] > dv["ex"]
        L.append(f"- {name}: evidence (fabricated) {ev['ex']:+.1f}, track50 {tr['ex']:+.1f}, doubt {dv['ex']:+.1f} → {order}")
        verdict[f"H7c {tag}"] = order

    # H6: policy ranking
    L.append("\n## H6: policy ranking (authors and challengers; loss per 100 submissions)\n")
    import policy_sim as ps
    for tag in ("deepseek", "luna", "haiku"):
        data = ps.load(f"runs/confirm_{tag}", "api")
        est = ps.evaluate(data, 4.0, 0.3, 1.0, 0.02, 0.3, True)
        boots = [ps.evaluate(ps.resample(data, rng), 4.0, 0.3, 1.0, 0.02, 0.3, True) for _ in range(300)]
        L.append(f"- {EXPLO[tag]}: " + ", ".join(f"{k.split()[0]} {v[0]:.1f}" for k, v in est.items()))
        d2 = np.array([b[ps.POLICIES[2]][0] - b[ps.POLICIES[0]][0] for b in boots])
        lo = float(np.percentile(d2, 5))
        L.append(f"  P2 − P0 = {est[ps.POLICIES[2]][0] - est[ps.POLICIES[0]][0]:+.1f}, 90% lower bound {lo:+.1f}")
        if tag == "deepseek":
            core = {k: v[0] for k, v in est.items() if k.split()[0] in ("P0", "P1", "P2", "P3", "P4")}
            verdict["H6a deepseek P4 best"] = min(core, key=core.get).startswith("P4")
        if tag in ("deepseek", "luna"):
            verdict[f"H6b {tag} P2 > P0"] = lo > 0

    # replication of magnitudes
    L.append("\n## Replication of magnitudes (exploratory 90% prediction intervals)\n")
    pred = open("paper_isr/predictions_api.md").read()
    inside = total = 0
    miss = []
    for blk in pred.split("### ")[1:]:
        tag = blk.split()[0].replace("api_", "")
        for fr, cond, claim, ex, lo, hi in re.findall(
                r"\| (\S+) \| (\S+) \| (bug|correct) \| ([+-][\d.]+) \| \[([+-][\d.]+), ([+-][\d.]+)\] \|", blk):
            k = None if fr == "none" else fr.split("=")[1]
            c = cell(tag, cond, claim == "bug", k)
            if c is None:
                continue
            total += 1
            ok = float(lo) <= c["ex"] <= float(hi)
            inside += ok
            if not ok:
                miss.append(f"{tag} {fr} {cond} {claim}: predicted [{lo}, {hi}], observed {c['ex']:+.1f}")
    share = inside / max(1, total)
    L.append(f"- {inside} of {total} cells inside their interval ({share:.0%}); criterion: about 90%, failure below 75%")
    verdict["replication share >= 75%"] = share >= .75
    L += ["  - outside: " + m for m in miss]

    L.append("\n## Summary of verdicts\n")
    for k, v in verdict.items():
        L.append(f"- {k}: {'supported' if v else ('not supported' if v is not None else 'n/a')}")
    text = "\n".join(L) + "\n"
    print(text)
    with open(args.out, "w") as f:
        f.write(text)


if __name__ == "__main__":
    main()
