"""Analysis of the post-main-run additions (Section 6 'does reasoning explain stance-following?', and the extra vendor tier).

Imports the frozen estimators from analysis.py unchanged. For each model with a reasoning on/off pair it resamples items once and
applies the same resample to both conditions (paired), so Delta = on - off has a paired percentile interval.

  python analysis_extra.py extra/data/full.jsonl results/extra [--boot 2000] [--missing exclude|error]

Outputs: condition_metrics.csv (every condition), delta_onoff.csv (Delta with interval and verdict), delta_intersection.csv
(Delta recomputed on items answered correctly in the reference run of BOTH conditions), coverage.csv (calls, parse failures, truncation,
reasoning tokens, providers), and gemini/ (the single-condition model, same estimators as the main run).
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import analysis as AN

EQUIV = 0.05  # equivalence margin for Delta s*
DELTA_KEYS = ["a", "nu", "rho", "f_pref", "f_weak", "f_strong", "f_disclaimer", "s_star", "s_mix", "slope", "acc_slope", "disclaimer_effect"]


def load(path):
    """One row per key: the last non-error row. Errors that never succeeded are dropped (reported in coverage)."""
    rows = {}
    for l in open(path):
        r = json.loads(l)
        if r["error"] is None or r["key"] not in rows:
            rows[r["key"]] = r
    df = pd.DataFrame(rows.values())
    df["failed"] = df["error"].notna()
    return df


def coverage(df):
    g = df.groupby("model")
    out = pd.DataFrame({"calls": g.size(), "unresolved_errors": g["failed"].sum(),
                        "parse_fail": g.apply(lambda x: (x["parser_branch"].eq("none") & ~x["failed"]).mean()),
                        "truncated": g.apply(lambda x: x["finish_reason"].eq("length").mean()),
                        "mean_reasoning_tokens": g["reasoning_tokens"].mean(), "mean_completion_tokens": g["completion_tokens"].mean(),
                        "cost_usd": g["cost"].sum(),
                        "providers": g["served_by"].agg(lambda s: "; ".join(f"{k} {v / len(s):.0%}" for k, v in s.value_counts().items() if v / len(s) >= 0.01))})
    return out


def prep(df):
    d = df[~df["failed"]].copy()
    d["level"] = d["level"].astype(str)
    return d[["model", "base_model", "family", "size_rank", "item_id", "domain", "tier", "channel", "level", "rep", "role"]]


def verdict(lo, hi):
    direction = "on lowers" if hi < 0 else ("on raises" if lo > 0 else "no direction")
    equiv = (lo > -EQUIV) and (hi < EQUIV)
    return direction, equiv


def paired(d, base, missing, B, seed):
    """Point estimates and paired bootstrap for one on/off pair; returns (condition metrics rows, delta rows)."""
    sub = d[d["base_model"] == base]
    arrays, meta, n = AN.build(sub, missing)
    AN.add_stem_deference(sub, arrays, n, "pref", missing)
    on, off = f"{base}|on", f"{base}|off"
    full = np.arange(n)
    pt = {m: AN.estimate(A, full, "pref") for m, A in arrays.items()}
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(B):
        idx = rng.integers(0, n, n)  # the same items for both conditions
        draws.append({m: AN.estimate(A, idx, "pref") for m, A in arrays.items()})
    ci = lambda v: tuple(np.nanpercentile(np.array(v, float), [2.5, 97.5]))
    cond_rows = [(m, n, k, pt[m][k], *ci([x[m][k] for x in draws])) for m in arrays for k in DELTA_KEYS]
    delta_rows = []
    for k in DELTA_KEYS:
        est = pt[on][k] - pt[off][k]
        lo, hi = ci([x[on][k] - x[off][k] for x in draws])
        direction, equiv = verdict(lo, hi) if k == "s_star" else ("", "")
        delta_rows.append((base, n, k, pt[on][k], pt[off][k], est, lo, hi, direction, equiv))
    return cond_rows, delta_rows


def intersection(d, base):
    """Keep only items answered correctly in the reference run (N, rep 0) under both conditions."""
    sub = d[d["base_model"] == base]
    ref = sub[(sub["channel"] == "N") & (sub["rep"] == 0) & (sub["role"] == "gold")]
    keep = set.intersection(*[set(g["item_id"]) for _, g in ref.groupby("model")])
    return sub[sub["item_id"].isin(keep)], len(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("outdir")
    ap.add_argument("--boot", type=int, default=AN.B_DEFAULT); ap.add_argument("--missing", default="exclude", choices=["exclude", "error"])
    ap.add_argument("--seed", type=int, default=20260101)  # same seed as the main analysis
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    raw = load(a.data)
    coverage(raw).to_csv(os.path.join(a.outdir, "coverage.csv"))
    d = prep(raw)
    cols_c = ["condition", "items", "metric", "est", "lo", "hi"]
    cols_d = ["model", "items", "metric", "on", "off", "delta", "lo", "hi", "direction_s_star", "equivalent_s_star"]
    C, D, DI = [], [], []
    for base in sorted(d["base_model"].unique()):
        conds = set(d[d["base_model"] == base]["model"])
        if conds != {f"{base}|on", f"{base}|off"}:
            continue
        c, dl = paired(d, base, a.missing, a.boot, a.seed)
        C += c; D += dl
        sub, k = intersection(d, base)
        if k >= 20:
            arr_sub = sub.copy()
            _, di = paired(arr_sub, base, a.missing, a.boot, a.seed)
            DI += [(r[0], k, *r[2:]) for r in di]
    pd.DataFrame(C, columns=cols_c).to_csv(os.path.join(a.outdir, "condition_metrics.csv"), index=False)
    pd.DataFrame(D, columns=cols_d).to_csv(os.path.join(a.outdir, "delta_onoff.csv"), index=False)
    pd.DataFrame(DI, columns=cols_d).to_csv(os.path.join(a.outdir, "delta_intersection.csv"), index=False)
    for m in sorted(set(d["model"]) - {c for c in d["model"] if c.endswith(("|on", "|off"))}):  # single-condition models (Gemini)
        AN.run(d[d["model"] == m], os.path.join(a.outdir, m.split("|")[0]), "pref", a.missing, a.boot, a.seed)
    print("wrote", a.outdir)


if __name__ == "__main__":
    main()
