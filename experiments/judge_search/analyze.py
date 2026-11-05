"""Exact statistics for the GSM8K judge-search experiments (Tables 4 and 5).

Reads results/bon_raw.jsonl and results/rewrite_raw.jsonl written by run_gsm8k.py and
writes results/summary.json. Intervals are percentile bootstraps over questions
(10,000 resamples); tests are paired t-tests (df = n - 1) and exact McNemar tests.
"""
import json
import os
from collections import defaultdict
from math import comb

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
RNG = np.random.default_rng(20261105)
B = 10_000
NS = [1, 2, 4, 8, 16, 32]


def boot_ci(x):
    x = np.asarray(x, float)
    idx = RNG.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def paired_t(d):
    d = np.asarray(d, float)
    t, p = stats.ttest_1samp(d, 0.0)
    return {"t": float(t), "df": int(len(d) - 1), "p": float(p)}


def mcnemar(a, b):
    """Exact McNemar test for paired binary outcomes a (treatment) and b (control)."""
    a, b = np.asarray(a, int), np.asarray(b, int)
    n10 = int(((a == 1) & (b == 0)).sum())
    n01 = int(((a == 0) & (b == 1)).sum())
    p = stats.binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return {"b": n10, "c": n01, "p": float(p)}


def within_corr(groups):
    xs, ys = [], []
    for x, y in groups:
        x, y = np.asarray(x, float), np.asarray(y, float)
        xs.append(x - x.mean())
        ys.append(y - y.mean())
    x, y = np.concatenate(xs), np.concatenate(ys)
    return float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y)))


# ---------------------------------------------------------------- best-of-N
def analyze_bon():
    by_q = defaultdict(list)
    for l in open(os.path.join(OUT, "bon_raw.jsonl")):
        r = json.loads(l)
        if r["J"] is not None:
            by_q[r["qid"]].append(r)
    qids = sorted(by_q)
    draws = 2000
    per_n = {}
    for n in NS:
        acc, jj, ln, orc = [], [], [], []
        for q in qids:
            s = by_q[q]
            k = len(s)
            J = np.array([r["J"] for r in s], float)
            C = np.array([r["correct"] for r in s], float)
            L = np.array([r["length"] for r in s], float)
            m = min(n, k)
            # random subset of size m, highest J selected, ties broken at random
            sub = np.argsort(RNG.random((draws, k)), axis=1)[:, :m]
            noise = RNG.random((draws, m)) * 1e-3
            pick = sub[np.arange(draws), np.argmax(J[sub] + noise, axis=1)]
            acc.append(C[pick].mean())
            jj.append(J[pick].mean())
            ln.append(L[pick].mean())
            wrong = int(k - C.sum())
            orc.append(1 - comb(wrong, m) / comb(k, m))
        per_n[n] = {"acc": acc, "J": jj, "len": ln, "oracle": orc}
    table = []
    for n in NS:
        d = per_n[n]
        table.append({"N": n, "acc": float(np.mean(d["acc"])), "acc_ci": boot_ci(d["acc"]),
                      "mean_J": float(np.mean(d["J"])), "length": float(np.mean(d["len"])),
                      "oracle": float(np.mean(d["oracle"]))})
    a1 = np.array(per_n[1]["acc"])
    a32 = np.array(per_n[32]["acc"])
    test = paired_t(a32 - a1)
    captured = [(t["acc"] - table[0]["acc"]) / (t["oracle"] - table[0]["acc"])
                for t in table[1:] if t["oracle"] > table[0]["acc"]]
    corr_c = within_corr([([r["J"] for r in by_q[q]], [r["correct"] for r in by_q[q]]) for q in qids])
    corr_l = within_corr([([r["J"] for r in by_q[q]], [r["length"] for r in by_q[q]]) for q in qids])
    return {"n_questions": len(qids), "table": table, "test_32_vs_1": test,
            "captured_share": [float(min(captured)), float(max(captured))],
            "within_corr_J_correct": corr_c, "within_corr_J_length": corr_l}


# ---------------------------------------------------------------- rewriting
def analyze_rewrite():
    chains = defaultdict(dict)
    for l in open(os.path.join(OUT, "rewrite_raw.jsonl")):
        r = json.loads(l)
        chains[r["judge"]].setdefault(r["qid"], {})[r["arm"]] = r["history"]
    out = {}
    for judge, qd in chains.items():
        qids = sorted(q for q, v in qd.items() if "optimize" in v and "control" in v)
        rows = defaultdict(list)
        for q in qids:
            for arm in ("optimize", "control"):
                h = qd[q][arm]
                h0, h6 = h[0], h[-1]
                j0 = h0["J"] if h0["J"] is not None else np.nan
                j6 = h6["J"] if h6["J"] is not None else np.nan
                rows[f"{arm}_c0"].append(h0["correct"])
                rows[f"{arm}_c6"].append(h6["correct"])
                rows[f"{arm}_j6"].append(j6)
                rows[f"{arm}_l0"].append(h0["length"])
                rows[f"{arm}_l6"].append(h6["length"])
                rows[f"{arm}_div"].append(int(j6 > j0 and h6["correct"] < h0["correct"]))
        R = {k: np.array(v, float) for k, v in rows.items()}
        res = {"n_questions": len(qids)}
        for arm in ("optimize", "control"):
            res[arm] = {"acc0": float(R[f"{arm}_c0"].mean()), "acc6": float(R[f"{arm}_c6"].mean()),
                        "len0": float(R[f"{arm}_l0"].mean()), "len6": float(R[f"{arm}_l6"].mean()),
                        "J6": float(np.nanmean(R[f"{arm}_j6"]))}
        meas = {}
        d = R["optimize_c6"] - R["control_c6"]
        meas["gold"] = {"diff": float(d.mean()), "ci": boot_ci(d), "t": paired_t(d),
                        "mcnemar": mcnemar(R["optimize_c6"], R["control_c6"])}
        d = R["optimize_j6"] - R["control_j6"]
        d = d[~np.isnan(d)]
        meas["J"] = {"diff": float(d.mean()), "ci": boot_ci(d), "t": paired_t(d)}
        d = R["optimize_l6"] - R["control_l6"]
        meas["length"] = {"diff": float(d.mean()), "ci": boot_ci(d), "t": paired_t(d)}
        d = R["optimize_div"] - R["control_div"]
        meas["div"] = {"diff": float(d.mean()), "ci": boot_ci(d), "t": paired_t(d),
                       "mcnemar": mcnemar(R["optimize_div"], R["control_div"])}
        res["measures"] = meas
        out[judge] = res
    return out


if __name__ == "__main__":
    summary = {}
    if os.path.exists(os.path.join(OUT, "bon_raw.jsonl")):
        summary["bon"] = analyze_bon()
    if os.path.exists(os.path.join(OUT, "rewrite_raw.jsonl")):
        summary["rewrite"] = analyze_rewrite()
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
