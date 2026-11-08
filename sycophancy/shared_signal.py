"""Shared-signal test (paper Section 7): do caving and self-correction share an internal signal?

A probe is trained ONLY on questions answered wrongly in turn 1 (held_wrong = 0 vs corrected = 1),
on the hidden state after the challenge (t2), and scored on questions answered correctly in turn 1
(held_correct = 0 vs caved = 1). Chance is 0.5.

Per layer it reports
  transfer AUROC   how well the self-correction probe ranks caving among right answers
  gain             AUROC of [turn-1 confidence + probe score] (cross-validated stacking within the
                   right-answer group) minus AUROC of confidence alone, with a 95% paired bootstrap interval
and counts the layers whose interval lies above / below zero.

Example:
  python shared_signal.py runs/code_q4b_96 runs/code_q4b_1024
"""

import argparse
import json
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from syco import LETTERS


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def analyze(run_dir, layer_step, n_boot, min_class, seed=0):
    with open(os.path.join(run_dir, "results.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    H = np.load(os.path.join(run_dir, "hidden_t2.npy"), mmap_mode="r")
    out = np.array([r["outcome"] for r in rows])
    conf = np.array([r["p1"][LETTERS.index(r["a1"])] for r in rows])
    w_idx = np.where(np.isin(out, ["held_wrong", "corrected"]))[0]
    r_idx = np.where(np.isin(out, ["held_correct", "caved"]))[0]
    yw = (out[w_idx] == "corrected").astype(int)
    yr = (out[r_idx] == "caved").astype(int)
    counts = {"wrong_held": int((yw == 0).sum()), "corrected": int(yw.sum()),
              "right_held": int((yr == 0).sum()), "caved": int(yr.sum())}
    print(f"\n== {run_dir}\n  {counts}")
    if min(counts.values()) < min_class:
        print(f"  fewer than {min_class} cases in a group: skipped")
        return {"run": run_dir, "counts": counts, "skipped": True}

    rng = np.random.default_rng(seed)
    boot = [rng.integers(0, len(yr), len(yr)) for _ in range(n_boot)]
    base_score = -conf[r_idx]
    base_auc = roc_auc_score(yr, base_score)
    cf = _logit(conf[r_idx])[:, None]
    folds = StratifiedKFold(5, shuffle=True, random_state=seed)
    layers = list(range(layer_step, H.shape[1], layer_step))
    res = []
    for l in layers:
        probe = make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000))
        probe.fit(np.asarray(H[w_idx, l], dtype=np.float32), yw)
        s = probe.decision_function(np.asarray(H[r_idx, l], dtype=np.float32))
        t_auc = roc_auc_score(yr, s)
        stack = cross_val_predict(LogisticRegression(max_iter=1000), np.column_stack([cf, s]), yr,
                                  cv=folds, method="predict_proba")[:, 1]
        gain = roc_auc_score(yr, stack) - base_auc
        diffs = []
        for i in boot:
            if 0 < yr[i].sum() < len(i):
                diffs.append(roc_auc_score(yr[i], stack[i]) - roc_auc_score(yr[i], base_score[i]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        res.append({"layer": l, "transfer_auroc": float(t_auc), "gain": float(gain),
                    "gain_ci": [float(lo), float(hi)]})
        print(f"  L{l:2d} transfer AUROC {t_auc:.3f} | gain over confidence {gain:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    above = sum(r["gain_ci"][0] > 0 for r in res)
    below = sum(r["gain_ci"][1] < 0 for r in res)
    ta = [r["transfer_auroc"] for r in res]
    g = [r["gain"] for r in res]
    print(f"  confidence AUROC {base_auc:.3f} | transfer {min(ta):.2f}-{max(ta):.2f} | "
          f"gain {min(g):+.3f} to {max(g):+.3f} | layers > 0 / < 0: {above} / {below} of {len(res)}")
    return {"run": run_dir, "counts": counts, "confidence_auroc": float(base_auc), "layers": res,
            "layers_above": above, "layers_below": below}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+")
    p.add_argument("--layer-step", type=int, default=4)
    p.add_argument("--n-boot", type=int, default=1000)
    p.add_argument("--min-class", type=int, default=10)
    p.add_argument("--out", default=None, help="JSON file for all results (default: shared_signal.json in each run)")
    p.add_argument("--plot", default=None, help="PNG with the gain by layer for all runs")
    args = p.parse_args()
    allres = []
    for d in args.runs:
        r = analyze(d, args.layer_step, args.n_boot, args.min_class)
        allres.append(r)
        if not args.out:
            with open(os.path.join(d, "shared_signal.json"), "w") as f:
                json.dump(r, f, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(allres, f, indent=2)
    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 3.5))
        for r in allres:
            if r.get("skipped"):
                continue
            L = [x["layer"] for x in r["layers"]]
            ax.plot(L, [x["gain"] for x in r["layers"]], marker="o", ms=3, label=os.path.basename(r["run"]))
            ax.fill_between(L, [x["gain_ci"][0] for x in r["layers"]], [x["gain_ci"][1] for x in r["layers"]],
                            alpha=0.15)
        ax.axhline(0, c="black", lw=0.8)
        ax.set_xlabel("layer")
        ax.set_ylabel("AUROC gain over confidence")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=150)
        print(f"plot saved: {args.plot}")


if __name__ == "__main__":
    main()
