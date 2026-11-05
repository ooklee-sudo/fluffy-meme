"""Week 2: does a hallucination probe survive a model update?

Setting: a probe was trained on the hidden states of a SOURCE model (e.g. Qwen3-4B-Base)
with correctness labels. The model is then replaced by a TARGET model (e.g. the Instruct
version, or the same model after LoRA fine-tuning). Relabeling answers for the target is
costly, so we ask how well the old probe still works and whether it can be repaired from
unlabeled questions only.

Both runs must come from generate.py on the same questions (same --dataset, --n, --seed);
use --prompt fewshot so both models see identical input text.

Questions are split into three disjoint parts:
  calib  questions whose hidden states we may read from both models, but with NO labels
  train  labeled questions (source labels for the source probe, target labels for oracles)
  test   evaluation; AUROC of predicting whether the TARGET model's answer is correct

Methods (per layer and token position):
  source (in-domain)  source probe on source test states, source labels   [reference]
  naive               source probe applied unchanged to target states
  restandardize       source probe, but features standardized with target calib statistics
  linear map          ridge map target -> source states fit on calib (label-free), then the
                      source probe; ridge strength picked on an 80/20 split of calib
  target k labels     new probe trained on k labeled target questions (labeling-cost curve)
  target oracle       new probe trained on all target train labels               [upper bound]
  logprob             target mean token log-prob (label-free, no probe)

Recovery R = (AUROC_method - AUROC_naive) / (AUROC_oracle - AUROC_naive): share of the
gap closed without target labels (same definition as the adapter experiments in ../).

Example:
  python transfer.py runs/qwen3-4b-base_fs runs/qwen3-4b_fs --out results/base_to_instruct
"""

import argparse
import json
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

ALPHAS = [10.0 ** e for e in range(-2, 6)]


def load_run(run_dir):
    with open(os.path.join(run_dir, "meta.json")) as f:
        meta = json.load(f)
    with open(os.path.join(run_dir, "generations.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    hidden = {pos: np.load(os.path.join(run_dir, f"hidden_{pos}.npy"), mmap_mode="r")
              for pos in ["prompt", "answer"]}
    return meta, rows, hidden


def auroc(y, s):
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


class Probe:
    """Standardize + L2 logistic regression. Scaling is kept separate from the classifier
    so it can be swapped for target statistics (restandardize)."""

    def __init__(self, C):
        self.C = C

    def fit(self, X, y):
        self.scaler = StandardScaler().fit(X)
        self.clf = LogisticRegression(C=self.C, max_iter=3000).fit(self.scaler.transform(X), y)
        return self

    def score(self, X, scaler=None):
        return self.clf.decision_function((scaler or self.scaler).transform(X))


def fit_ridge_map(X, Y, seed):
    """Ridge regression Y ~ X (both centered on calib means), alpha picked on an 80/20 split.
    Solved through the SVD of X, which is cheap when n_calib < hidden size."""
    mx, my = X.mean(0), Y.mean(0)
    Xc, Yc = X - mx, Y - my

    def solve(Xa, Ya, alpha_list):
        U, s, Vt = np.linalg.svd(Xa, full_matrices=False)
        UtY = U.T @ Ya
        return {a: Vt.T @ ((s / (s ** 2 + a))[:, None] * UtY) for a in alpha_list}

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(X))
    cut = int(0.8 * len(X))
    fit_i, val_i = perm[:cut], perm[cut:]
    Ws = solve(Xc[fit_i], Yc[fit_i], ALPHAS)
    err = {a: float(((Xc[val_i] @ W - Yc[val_i]) ** 2).mean()) for a, W in Ws.items()}
    best = min(err, key=err.get)
    W = solve(Xc, Yc, [best])[best]
    return (lambda Z: (Z - mx) @ W + my), best


def run_layer(Hs, Ht, ys, yt, split, ks, C, seed):
    cal, tr, te = split
    Xs_tr, Xs_te = Hs[tr], Hs[te]
    Xt_cal, Xt_tr, Xt_te = Ht[cal], Ht[tr], Ht[te]
    out = {}

    src = Probe(C).fit(Xs_tr, ys[tr])
    out["source (in-domain)"] = auroc(ys[te], src.score(Xs_te))

    same_dim = Hs.shape[1] == Ht.shape[1]
    if same_dim:
        out["naive"] = auroc(yt[te], src.score(Xt_te))
        out["restandardize"] = auroc(yt[te], src.score(Xt_te, scaler=StandardScaler().fit(Xt_cal)))
        # Does the source probe mostly track question difficulty shared by both models?
        out["naive vs source labels"] = auroc(ys[te], src.score(Xt_te))

    to_src, alpha = fit_ridge_map(Xt_cal, Hs[cal], seed)
    out["linear map"] = auroc(yt[te], src.score(to_src(Xt_te)))
    out["_ridge_alpha"] = alpha

    rng = np.random.default_rng(seed)
    for k in ks:
        if k >= len(tr):
            continue
        scores = []
        for r in range(3):
            pick = rng.choice(tr, size=k, replace=False)
            if 0 < yt[pick].sum() < k:
                scores.append(auroc(yt[te], Probe(C).fit(Ht[pick], yt[pick]).score(Xt_te)))
        out[f"target {k} labels"] = float(np.mean(scores)) if scores else float("nan")
    out["target oracle"] = auroc(yt[te], Probe(C).fit(Xt_tr, yt[tr]).score(Xt_te))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source_run")
    p.add_argument("target_run")
    p.add_argument("--out", required=True, help="output directory for transfer.json and the plot")
    p.add_argument("--calib-frac", type=float, default=0.25)
    p.add_argument("--test-frac", type=float, default=0.25)
    p.add_argument("--k", default="32,64,128", help="label budgets for the target-k-labels curve")
    p.add_argument("--layer-step", type=int, default=2)
    p.add_argument("--repeats", type=int, default=3, help="random splits to average over")
    p.add_argument("--C", type=float, default=0.05)
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()
    ks = [int(k) for k in args.k.split(",") if k]

    meta_s, rows_s, H_s = load_run(args.source_run)
    meta_t, rows_t, H_t = load_run(args.target_run)
    n = min(len(rows_s), len(rows_t))
    if [r["id"] for r in rows_s[:n]] != [r["id"] for r in rows_t[:n]]:
        raise SystemExit("the two runs used different questions; rerun with the same --dataset/--n/--seed")
    if meta_s.get("prompt") != meta_t.get("prompt"):
        print("[warn] the two runs used different prompt styles; prefer --prompt fewshot for both")

    ys = np.array([int(r["correct"]) for r in rows_s[:n]])
    yt = np.array([int(r["correct"]) for r in rows_t[:n]])
    lp = np.nan_to_num(np.array([r["mean_logprob"] for r in rows_t[:n]], dtype=float), nan=-1e9)
    print(f"source: {meta_s['model']}{' + ' + meta_s['adapter'] if meta_s.get('adapter') else ''}"
          f" | accuracy {ys.mean():.3f}")
    print(f"target: {meta_t['model']}{' + ' + meta_t['adapter'] if meta_t.get('adapter') else ''}"
          f" | accuracy {yt.mean():.3f}")
    print(f"questions: {n} | both correct {np.mean(ys & yt):.3f} | label agreement {np.mean(ys == yt):.3f}")

    n_layers = min(H_s["prompt"].shape[1], H_t["prompt"].shape[1])
    if H_s["prompt"].shape[1] != H_t["prompt"].shape[1]:
        print("[warn] different layer counts; layers are paired by index")
    layers = list(range(0, n_layers, args.layer_step))
    if layers[-1] != n_layers - 1:
        layers.append(n_layers - 1)

    splits = []
    for r in range(args.repeats):
        perm = np.random.default_rng(1000 + r).permutation(n)
        n_cal, n_te = int(args.calib_frac * n), int(args.test_frac * n)
        splits.append((perm[:n_cal], perm[n_cal + n_te:], perm[n_cal:n_cal + n_te]))

    result = {"source": meta_s, "target": meta_t, "n": n, "layers": layers,
              "source_accuracy": float(ys.mean()), "target_accuracy": float(yt.mean()),
              "label_agreement": float(np.mean(ys == yt)), "positions": {}}

    for pos in ["prompt", "answer"]:
        per_layer = []
        for layer in layers:
            Hs = np.asarray(H_s[pos][:n, layer], dtype=np.float32)
            Ht = np.asarray(H_t[pos][:n, layer], dtype=np.float32)
            runs = [run_layer(Hs, Ht, ys, yt, sp, ks, args.C, seed=r) for r, sp in enumerate(splits)]
            avg = {k: float(np.nanmean([d[k] for d in runs])) for k in runs[0]}
            avg["logprob"] = float(np.mean([auroc(yt[sp[2]], lp[sp[2]]) for sp in splits]))
            per_layer.append(avg)
            print(f"  [{pos}] layer {layer:3d}: " + " | ".join(
                f"{k} {v:.3f}" for k, v in avg.items() if k in ("naive", "linear map", "target oracle")))

        # Pick the layer with only source information (best in-domain source AUROC).
        best = int(np.nanargmax([d["source (in-domain)"] for d in per_layer]))
        sel = per_layer[best]
        gap = sel["target oracle"] - sel.get("naive", np.nan)
        recov = {m: (sel[m] - sel["naive"]) / gap
                 for m in ("restandardize", "linear map") if m in sel and gap > 0.01}
        result["positions"][pos] = {"per_layer": per_layer, "selected_layer": layers[best],
                                    "selected": sel, "recovery": recov}

        print(f"\n=== {pos} token, layer {layers[best]} (chosen by source in-domain AUROC) ===")
        for k, v in sel.items():
            if not k.startswith("_"):
                print(f"  {k:24s} {v:.3f}")
        for m, r in recov.items():
            print(f"  recovery R ({m}) = {r:.2f}")
        if not recov:
            print("  (oracle is not above naive by > 0.01 AUROC, so recovery is not meaningful here)")
        print()

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "transfer.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"saved {os.path.join(args.out, 'transfer.json')}")

    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
        methods = ["source (in-domain)", "naive", "restandardize", "linear map",
                   f"target {ks[0]} labels" if ks else None, "target oracle", "logprob"]
        styles = {"source (in-domain)": dict(c="gray", ls=":"), "naive": dict(c="tab:blue"),
                  "restandardize": dict(c="tab:orange"), "linear map": dict(c="tab:purple", lw=2),
                  methods[4]: dict(c="tab:red", ls="-."), "target oracle": dict(c="tab:green", lw=2),
                  "logprob": dict(c="black", ls="--", lw=1)}
        for ax, pos in zip(axes, ["prompt", "answer"]):
            per_layer = result["positions"][pos]["per_layer"]
            for m in methods:
                if m and m in per_layer[0]:
                    ax.plot(layers, [d[m] for d in per_layer], marker="o", ms=3, label=m, **styles.get(m, {}))
            ax.axhline(0.5, c="black", lw=0.5, ls=":")
            ax.set_title(f"{pos} token")
            ax.set_xlabel("layer")
        axes[0].set_ylabel("AUROC on target (correct vs. wrong)")
        axes[1].legend(fontsize=8)
        name = lambda m: m["model"].split("/")[-1] + (" + LoRA" if m.get("adapter") else "")
        fig.suptitle(f"probe transfer: {name(meta_s)} -> {name(meta_t)}")
        fig.tight_layout()
        path = os.path.join(args.out, "transfer.png")
        fig.savefig(path, dpi=150)
        print(f"saved {path}")


if __name__ == "__main__":
    main()
