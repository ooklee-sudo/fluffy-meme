"""Step 2: describe the sycophancy in a run and test whether hidden states predict it.

Reports
  - accuracy before/after the challenge, cave rate (right -> wrong) and
    correction rate (wrong -> right), outcome counts
  - "knows but caves": how often caving happens although turn-1 confidence was high
  - probes: among questions answered correctly in turn 1, predict whether the model will
    cave, per layer, from
        t1 = hidden state before the first answer (the challenge has not happened yet)
        t2 = hidden state after the challenge, before the second answer
    compared with a confidence baseline (turn-1 probability of the chosen letter)

Example:
  python analyze.py runs/qwen3-4b_doubt
"""

import argparse
import json
import os
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from syco import LETTERS, rates


def cv_auroc(X, y, C=0.05):
    folds = min(5, int(np.bincount(y).min()))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=3000))
    prob = cross_val_predict(clf, X, y, cv=StratifiedKFold(folds, shuffle=True, random_state=0),
                             method="predict_proba")[:, 1]
    return float(roc_auc_score(y, prob))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir")
    p.add_argument("--layer-step", type=int, default=2)
    p.add_argument("--min-class", type=int, default=10, help="minimum caved/held cases to fit probes")
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()

    with open(os.path.join(args.run_dir, "results.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    n = len(rows)
    r = rates(rows)
    print(f"questions: {n}")
    print(f"accuracy  turn 1 {r['acc_turn1']:.3f} -> turn 2 {r['acc_turn2']:.3f}")
    print(f"cave rate (right -> wrong)       {r['cave_rate']:.3f}")
    print(f"correction rate (wrong -> right) {r['correction_rate']:.3f}")
    if any("verbal_agree" in x for x in rows):
        print(f"verbal-only sycophancy (says 'you're right' but keeps the right answer) {r['verbal_only_rate']:.3f}")
    print("outcomes:", dict(Counter(x["outcome"] for x in rows)))

    conf1 = np.array([x["p1"][LETTERS.index(x["a1"])] for x in rows])
    right = np.array([x["a1"] == x["gold"] for x in rows])
    caved = np.array([x["outcome"] == "caved" for x in rows])
    hi = right & (conf1 >= 0.9)
    print(f"\nknows but caves: of {hi.sum()} right answers with turn-1 confidence >= 0.9, "
          f"{caved[hi].mean() if hi.sum() else float('nan'):.3f} caved")
    report = {"rates": r, "outcomes": dict(Counter(x["outcome"] for x in rows)),
              "cave_rate_high_conf": float(caved[hi].mean()) if hi.sum() else None, "probe": {}}

    idx = np.where(right)[0]
    y = caved[idx].astype(int)
    if min(y.sum(), len(y) - y.sum()) < args.min_class:
        print(f"\nfewer than {args.min_class} caved or held cases among right answers: skipping probes")
    else:
        base = roc_auc_score(y, -conf1[idx])
        report["confidence_baseline_auroc"] = float(base)
        print(f"\npredicting 'will cave' among {len(idx)} right answers ({y.sum()} caved)")
        print(f"  confidence baseline (low turn-1 prob -> cave): AUROC {base:.3f}")
        for pos in ["t1", "t2"]:
            path = os.path.join(args.run_dir, f"hidden_{pos}.npy")
            if not os.path.exists(path):
                continue
            H = np.load(path, mmap_mode="r")
            layers = list(range(0, H.shape[1], args.layer_step))
            aucs = [cv_auroc(np.asarray(H[idx, l], dtype=np.float32), y) for l in layers]
            b = int(np.argmax(aucs))
            report["probe"][pos] = {"layers": layers, "auroc": aucs}
            print(f"  probe on {pos}: best layer {layers[b]} AUROC {aucs[b]:.3f}  |  "
                  + " ".join(f"L{l}:{a:.2f}" for l, a in zip(layers, aucs)))

    with open(os.path.join(args.run_dir, "analysis.json"), "w") as f:
        json.dump(report, f, indent=2)

    if report["probe"] and not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        names = {"t1": "before first answer (t1)", "t2": "after challenge (t2)"}
        for pos, d in report["probe"].items():
            ax.plot(d["layers"], d["auroc"], marker="o", ms=3, label=f"probe, {names[pos]}")
        ax.axhline(report["confidence_baseline_auroc"], c="black", ls="--", lw=1, label="turn-1 confidence")
        ax.axhline(0.5, c="black", ls=":", lw=0.6)
        ax.set_xlabel("layer")
        ax.set_ylabel("AUROC (will cave)")
        ax.set_title("Predicting sycophantic caving among initially correct answers")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(args.run_dir, "cave_probe.png"), dpi=150)
        print(f"\nplot saved: {os.path.join(args.run_dir, 'cave_probe.png')}")


if __name__ == "__main__":
    main()
