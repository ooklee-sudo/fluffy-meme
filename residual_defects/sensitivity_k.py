"""Sensitivity of the detection-curve tail index k to (1) the defect definition and (2) the test order.

Defect definition variants (random test order unless stated):
  base      distinct failure signature per sample (as in analyze_samples.py)
  sample    all failing tests of a sample form ONE defect
  subtle    base, dropping catastrophic defects (fail >= 50% of tests) and load errors
  no_to     base, dropping samples with timeouts / load errors
Order variants (base defects): canonical (dataset order), short-first (shortest input repr first), long-first.
For a deterministic order a defect is found at the first failing test in that order.
Task-level bootstrap gives 95% intervals. eps = 1/(1+k) is the implied offsetting elasticity (linear cost).
"""
import json
import pathlib

import numpy as np
import pandas as pd

from analyze_samples import fit_tail, load, log_comb

HERE = pathlib.Path(__file__).parent
FR = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0])
B = 300
rng = np.random.default_rng(0)


def records(df):
    """One record per (sample, signature): task, M, failing indices, signature."""
    out = []
    for r in df.itertuples():
        for sig, ix in r.fails.items():
            out.append((r.task_id, r.n, np.asarray(ix), sig, r.has_timeout or r.load_err))
    return out


def und_random(M, f):
    """P(undetected after e = round(u M) tests) for random order."""
    e = np.maximum(1, np.round(FR * M))
    ok = (M - f) >= e
    lp = np.where(ok, log_comb(M - f, np.minimum(e, M - f)) - log_comb(M, e), -np.inf)
    return np.exp(lp)


def und_order(M, idx, rank):
    pos = rank[idx].min() + 1
    e = np.maximum(1, np.round(FR * M))
    return (pos > e).astype(float)


def build(recs, mode, ranks=None):
    """Per-task sums of the undetected indicator at each u, and defect counts."""
    sums, cnt = {}, {}
    for task, M, idx, sig, bad in recs:
        v = und_random(M, len(idx)) if mode == "random" else und_order(M, idx, ranks[mode][task])
        sums.setdefault(task, np.zeros(len(FR)))
        sums[task] += v
        cnt[task] = cnt.get(task, 0) + 1
    return sums, cnt


def pooled(sums, cnt, tasks):
    n = sum(cnt.get(t, 0) for t in tasks)
    if n < 30:
        return None, n
    return sum(sums[t] for t in tasks if t in sums) / n, n


def estimate(sums, cnt, tasks_all):
    S, n = pooled(sums, cnt, tasks_all)
    if S is None:
        return None
    ft = fit_tail(FR, S)
    kb = []
    for _ in range(B):
        ts = rng.choice(tasks_all, len(tasks_all))
        sb, nb = pooled(sums, cnt, ts)
        if sb is not None:
            kb.append(fit_tail(FR, sb)["heavy_k"])
    lo, hi = np.percentile(kb, [2.5, 97.5])
    return {"defects": n, "k": ft["heavy_k"], "k_lo": lo, "k_hi": hi, "eps": 1 / (1 + ft["heavy_k"]),
            "eps_lo": 1 / (1 + hi), "eps_hi": 1 / (1 + lo), "sse_exp": ft["exp_sse"], "sse_heavy": ft["heavy_sse"],
            "S(0.01)": S[3], "S(0.1)": S[6]}


def main():
    df = load()
    tasks_json = {t["task_id"]: t for t in json.loads((HERE / "data" / "tasks.json").read_text())}
    tasks_all = np.array(sorted(df.task_id.unique()))
    ranks = {"canonical": {}, "short_first": {}, "long_first": {}}
    for tid in tasks_all:
        inputs = tasks_json[tid]["inputs"]
        n = len(inputs)
        length = np.array([len(repr(x)) for x in inputs])
        for name, order in (("canonical", np.arange(n)), ("short_first", np.argsort(length, kind="stable")),
                            ("long_first", np.argsort(-length, kind="stable"))):
            rk = np.empty(n, int)
            rk[order] = np.arange(n)
            ranks[name][tid] = rk

    base = records(df)
    sample_def = []
    for r in df.itertuples():
        if r.fails:
            sample_def.append((r.task_id, r.n, np.unique(np.concatenate([np.asarray(v) for v in r.fails.values()])),
                               "ALL", r.has_timeout or r.load_err))
    variants = {
        "base (random order, signatures)": (base, "random"),
        "sample = one defect": (sample_def, "random"),
        "subtle only (f/M<0.5, no load err)": ([x for x in base if len(x[2]) / x[1] < 0.5 and not x[3].startswith("LOAD")], "random"),
        "drop timeout/load-error samples": ([x for x in base if not x[4]], "random"),
        "canonical order": (base, "canonical"),
        "short-input-first order": (base, "short_first"),
        "long-input-first order": (base, "long_first"),
    }
    rows = []
    for name, (recs, mode) in variants.items():
        sums, cnt = build(recs, mode, ranks)
        est = estimate(sums, cnt, tasks_all)
        rows.append({"variant": name, **est})
        print(f"{name:38s} defects={est['defects']:6,}  k={est['k']:.3f} [{est['k_lo']:.3f}, {est['k_hi']:.3f}]  "
              f"eps={est['eps']:.3f} [{est['eps_lo']:.3f}, {est['eps_hi']:.3f}]  SSE exp/heavy={est['sse_exp']:.2f}/{est['sse_heavy']:.2f}  "
              f"S(.01)={est['S(0.01)']:.3f}", flush=True)
    pd.DataFrame(rows).round(4).to_csv(HERE / "results_sensitivity_k.csv", index=False)


if __name__ == "__main__":
    main()
