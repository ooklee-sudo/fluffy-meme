"""Week 1 sanity check (and a preview of week 3).

Reads a run made by generate.py and reports
  - accuracy (how often the model is right / hallucinates),
  - AUROC of simple confidence baselines (log-prob, entropy) for spotting wrong answers,
  - AUROC of a logistic-regression probe trained on each layer's hidden state
    (5-fold cross-validation), at the "prompt" and "answer" positions.

AUROC 0.5 = no better than chance, 1.0 = separates correct and wrong answers perfectly.

Example:
  python quick_check.py runs/qwen3-8b_triviaqa
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


def probe_auroc(X, y, C, seed=0):
    folds = min(5, int(np.bincount(y).min()))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000))
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    prob = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]
    return roc_auc_score(y, prob)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir")
    p.add_argument("--C", type=float, default=0.05, help="inverse L2 strength of the probe")
    p.add_argument("--layer-step", type=int, default=1, help="probe every k-th layer (faster)")
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()

    with open(os.path.join(args.run_dir, "generations.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    n = len(rows)
    y = np.array([int(r["correct"]) for r in rows])
    print(f"questions: {n} | accuracy: {y.mean():.3f} | wrong (hallucination candidates): {n - y.sum()}")
    if min(y.sum(), n - y.sum()) < 5:
        raise SystemExit("need at least 5 correct and 5 wrong answers to compute AUROC; run more questions")

    report = {"n": n, "accuracy": float(y.mean()), "baselines": {}, "probe": {}}

    print("\nBaselines (AUROC for 'answer is correct'):")
    for key, sign in [("mean_logprob", 1), ("min_logprob", 1), ("first_logprob", 1), ("mean_entropy", -1)]:
        s = np.array([r[key] for r in rows], dtype=float) * sign
        s = np.nan_to_num(s, nan=np.nanmin(s) - 1)  # empty answers count as least confident
        auc = roc_auc_score(y, s)
        report["baselines"][key] = auc
        print(f"  {key:15s} {auc:.3f}")

    for pos in ["prompt", "answer"]:
        H = np.load(os.path.join(args.run_dir, f"hidden_{pos}.npy"), mmap_mode="r")[:n]
        layers = list(range(0, H.shape[1], args.layer_step))
        aucs = []
        for layer in layers:
            aucs.append(probe_auroc(np.asarray(H[:, layer], dtype=np.float32), y, args.C))
        best = int(np.argmax(aucs))
        report["probe"][pos] = {"layers": layers, "auroc": aucs}
        print(f"\nProbe at '{pos}' position: best layer {layers[best]} -> AUROC {aucs[best]:.3f}")
        print("  " + " ".join(f"L{l}:{a:.2f}" for l, a in zip(layers, aucs)))

    with open(os.path.join(args.run_dir, "quick_check.json"), "w") as f:
        json.dump(report, f, indent=2)

    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        for pos in ["prompt", "answer"]:
            ax.plot(report["probe"][pos]["layers"], report["probe"][pos]["auroc"], marker="o", ms=3,
                    label=f"probe ({pos} token)")
        ax.axhline(report["baselines"]["mean_logprob"], ls="--", c="gray", label="mean log-prob baseline")
        ax.axhline(0.5, ls=":", c="black", lw=0.8)
        ax.set_xlabel("layer")
        ax.set_ylabel("AUROC (correct vs. wrong)")
        ax.set_title(os.path.basename(os.path.normpath(args.run_dir)))
        ax.legend()
        fig.tight_layout()
        out = os.path.join(args.run_dir, "probe_auroc.png")
        fig.savefig(out, dpi=150)
        print(f"\nplot saved: {out}")


if __name__ == "__main__":
    main()
