"""Step 3: does activation steering reduce caving without making the model stubborn?

Direction (per layer, from a TRAIN half of the questions answered correctly in turn 1):
    d = mean(hidden_t2 | held the right answer) - mean(hidden_t2 | caved)
Steering adds alpha * d to that layer's output at every token from the challenge onward.
alpha > 0 pushes toward "hold", alpha < 0 toward "cave" (a sanity check that the direction
means something).

Evaluated on the held-out TEST half, two numbers per setting:
    cave rate        right in turn 1 -> wrong in turn 2   (lower is better)
    correction rate  wrong in turn 1 -> right in turn 2   (higher is better; a fix that only
                                                           makes the model stubborn drives
                                                           this down too)
Controls:
    random   a random direction with the same norm as d (same alphas)
    firm     a system prompt telling the model not to cave without a reason
             (pass a run made with run_challenge.py --system firm via --firm-run)

Example:
  python steer.py runs/qwen3-4b_doubt --model Qwen/Qwen3-4B --out results/steer_qwen3-4b \
      --firm-run runs/qwen3-4b_doubt_firm
"""

import argparse
import json
import os
import time

import numpy as np
import torch

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from syco import LETTERS, Steer, answer_turn2, letter_ids, load_mmlu, load_model, rates, verbal_agree


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_gates(H1, rows, train, test_idx, layer):
    """Estimate P(turn-1 answer is right) for each test question, from information available
    before the challenge. Two gates: turn-1 confidence alone, and confidence + a hidden-state
    probe (stacked on out-of-fold probe predictions). Trained on the train half only."""
    conf = np.array([r["p1"][LETTERS.index(r["a1"])] for r in rows])
    y = np.array([int(r["a1"] == r["gold"]) for r in rows])
    gates = {"confidence": conf[test_idx]}
    probe = make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000))
    Xtr = np.asarray(H1[train, layer], dtype=np.float32)
    oof = cross_val_predict(probe, Xtr, y[train], cv=5, method="predict_proba")[:, 1]
    stack = LogisticRegression(max_iter=1000).fit(np.c_[_logit(oof), _logit(conf[train])], y[train])
    probe.fit(Xtr, y[train])
    p_te = probe.predict_proba(np.asarray(H1[test_idx, layer], dtype=np.float32))[:, 1]
    gates["probe+confidence"] = stack.predict_proba(np.c_[_logit(p_te), _logit(conf[test_idx])])[:, 1]
    aucs = {k: float(roc_auc_score(y[test_idx], g)) for k, g in gates.items()}
    # Upper bound: a gate that knows whether the turn-1 answer is right.
    gates["oracle"] = y[test_idx].astype(float)
    return gates, aucs


def evaluate(model, tok, ids, items, rows, challenge, system, mode, max_new, bs, layer=None, vec=None):
    """Re-ask turn 2 for `rows` (turn-1 answers fixed) with optional steering; return rows with new a2.
    `layer` is a hidden-state index h, i.e. the output of decoder block h - 1."""
    out = []
    steer = Steer(model, layer - 1, vec) if vec is not None else None
    if steer:
        steer.__enter__()
    try:
        for b0 in range(0, len(rows), bs):
            batch = rows[b0:b0 + bs]
            p2, replies, _, _ = answer_turn2(model, tok, [items[r["idx"]] for r in batch], [r["a1"] for r in batch],
                                          challenge, system, ids, mode, max_new, steer=steer)
            for r, pr, rep in zip(batch, p2, replies):
                out.append({**r, "a2": LETTERS[int(pr.argmax())],
                            "verbal_agree": verbal_agree(rep) if rep else None})
    finally:
        if steer:
            steer.__exit__(None, None, None)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", help="run from run_challenge.py (needs hidden_t2.npy)")
    p.add_argument("--model", required=True, help="same model as the run")
    p.add_argument("--quant", default="4bit", choices=["4bit", "none"])
    p.add_argument("--out", required=True)
    p.add_argument("--layers", default="", help="comma list of layer indices; default 3 layers at 1/3, 1/2, 2/3 depth")
    p.add_argument("--alphas", default="-4,2,4,8")
    p.add_argument("--n-test", type=int, default=300, help="max test questions (cost grows linearly)")
    p.add_argument("--turn2", choices=["free", "prefill"],
                   help="override the run's turn-2 mode; prefill is ~10x faster, handy to screen layers/alphas")
    p.add_argument("--bs", type=int, default=16)
    p.add_argument("--firm-run", help="run made with --system firm on the same questions")
    p.add_argument("--direction", default="cave", choices=["cave", "targeted", "combined"],
                   help="cave: mean(held|right) - mean(caved|right). "
                        "targeted: cave direction minus its projection on the 'keep when wrong' direction "
                        "mean(held|wrong) - mean(corrected|wrong), i.e. the shared 'keep my answer' part removed. "
                        "combined: unit(cave) - unit(keep-when-wrong): hold when right, change when wrong. "
                        "targeted/combined are rescaled to the norm of the cave direction so alphas compare.")
    p.add_argument("--gate", action="store_true",
                   help="also evaluate gated steering: steer with alpha>0 ('keep') only where the model is "
                        "probably right in turn 1, and with alpha<=0 (or not at all) elsewhere. Every test "
                        "question is run once per alpha, so all thresholds are scored without extra runs.")
    p.add_argument("--gate-layer", type=int, default=-1, help="hidden_t1 layer for the gate probe (default: last)")
    p.add_argument("--gate-taus", default="0.5,0.6,0.7,0.8,0.9,0.95",
                   help="thresholds on P(right): steer 'keep' when P(right) >= tau")
    p.add_argument("--min-caved", type=int, default=10, help="minimum caved examples needed in the train half")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    with open(os.path.join(args.run_dir, "meta.json")) as f:
        meta = json.load(f)
    if meta["model"] != args.model:
        print(f"[warn] run was made with {meta['model']}, steering {args.model}")
    with open(os.path.join(args.run_dir, "results.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    n = len(rows)
    H2 = np.load(os.path.join(args.run_dir, "hidden_t2.npy"), mmap_mode="r")
    items = load_mmlu(meta["n"], meta["seed"])
    challenge, system = meta["challenge_text"], meta["system_text"]
    run_mode, max_new = meta.get("turn2", "prefill"), meta.get("max_new_tokens", 96)
    mode = args.turn2 or run_mode

    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n)
    train, test = perm[: n // 2], perm[n // 2:][: args.n_test]
    test_rows = [rows[i] for i in sorted(test)]

    held = [i for i in train if rows[i]["outcome"] == "held_correct"]
    caved = [i for i in train if rows[i]["outcome"] == "caved"]
    held_w = [i for i in train if rows[i]["outcome"] == "held_wrong"]
    fixed = [i for i in train if rows[i]["outcome"] == "corrected"]
    print(f"train: {len(held)} held / {len(caved)} caved (right in turn 1), "
          f"{len(held_w)} held / {len(fixed)} corrected (wrong in turn 1) | test questions: {len(test_rows)}")
    if args.direction != "cave" and len(fixed) < args.min_caved:
        raise SystemExit(f"fewer than {args.min_caved} corrected examples in the train half for --direction {args.direction}")
    if len(caved) < args.min_caved:
        raise SystemExit(f"fewer than {args.min_caved} caved examples in the train half; use more questions or a "
                         "stronger challenge (--challenge wrong)")

    n_layers = H2.shape[1]
    layers = ([int(x) for x in args.layers.split(",")] if args.layers
              else sorted({round(n_layers * f) for f in (1 / 3, 1 / 2, 2 / 3)}))
    alphas = [float(a) for a in args.alphas.split(",")]

    model, tok = load_model(args.model, args.quant)
    ids = letter_ids(tok)

    t0 = time.time()
    if mode == run_mode:
        base_rows = test_rows  # alpha = 0: the recorded turn-2 answers
    else:  # different turn-2 mode: measure the unsteered baseline again
        base_rows = evaluate(model, tok, ids, items, test_rows, challenge, system, mode, max_new, args.bs)
    base = rates(base_rows)
    print(f"no steering: cave {base['cave_rate']:.3f} | correction {base['correction_rate']:.3f}")
    result = {"run": args.run_dir, "model": args.model, "turn2": mode, "layers": layers, "alphas": alphas,
              "n_test": len(test_rows), "baseline": base, "steer": {}, "random": {}}

    if args.firm_run:
        with open(os.path.join(args.firm_run, "results.jsonl")) as f:
            firm = [json.loads(line) for line in f if line.strip()]
        firm_test = [firm[i] for i in sorted(test) if i < len(firm)]
        result["firm_prompt"] = rates(firm_test)
        if mode != run_mode:
            print("[warn] the firm-prompt run used a different turn-2 mode than this evaluation")
        print(f"firm prompt: cave {result['firm_prompt']['cave_rate']:.3f} | "
              f"correction {result['firm_prompt']['correction_rate']:.3f}")

    steer_rows = {}
    result["direction"] = args.direction
    result["geometry"] = {}
    mean = lambda ix, l: np.asarray(H2[ix, l], dtype=np.float64).mean(0)
    for layer in layers:
        d_cave = mean(held, layer) - mean(caved, layer)
        geo = {"cave_norm_over_hidden_norm": float(np.linalg.norm(d_cave) / np.linalg.norm(
            np.asarray(H2[train, layer], dtype=np.float64), axis=1).mean())}
        d = d_cave
        if len(fixed) >= 2:
            d_wrong = mean(held_w, layer) - mean(fixed, layer)  # "keep my answer" when wrong
            u = d_wrong / np.linalg.norm(d_wrong)
            geo["cos(cave, keep_when_wrong)"] = float(d_cave @ u / np.linalg.norm(d_cave))
            if args.direction == "targeted":
                d = d_cave - (d_cave @ u) * u
            elif args.direction == "combined":
                d = d_cave / np.linalg.norm(d_cave) - u
            d = d / np.linalg.norm(d) * np.linalg.norm(d_cave)
        result["geometry"][layer] = geo
        print(f"layer {layer}: " + " | ".join(f"{k} {v:.3f}" for k, v in geo.items()), flush=True)
        d = torch.tensor(d, dtype=torch.float32)
        g = torch.Generator().manual_seed(args.seed + layer)
        rnd = torch.randn(d.shape, generator=g)
        rnd = rnd / rnd.norm() * d.norm()
        result["steer"][layer], result["random"][layer] = {}, {}
        for a in alphas:
            for kind, vec in (("steer", d), ("random", rnd)):
                out_rows = evaluate(model, tok, ids, items, test_rows, challenge, system, mode, max_new,
                                    args.bs, layer, a * vec)
                if kind == "steer":
                    steer_rows.setdefault(layer, {})[a] = out_rows
                rr = rates(out_rows)
                result[kind][layer][a] = rr
            s, q = result["steer"][layer][a], result["random"][layer][a]
            print(f"layer {layer:3d} alpha {a:+5.1f} | steer: cave {s['cave_rate']:.3f} correct "
                  f"{s['correction_rate']:.3f} acc2 {s['acc_turn2']:.3f} verbal-only {s['verbal_only_rate']:.3f} | random: cave {q['cave_rate']:.3f} "
                  f"correct {q['correction_rate']:.3f} | {time.time() - t0:.0f}s", flush=True)

    gated_pts = []
    if args.gate:
        H1 = np.load(os.path.join(args.run_dir, "hidden_t1.npy"), mmap_mode="r")
        test_idx = np.array(sorted(test))
        gl = args.gate_layer if args.gate_layer >= 0 else H1.shape[1] - 1
        gates, gate_auc = fit_gates(H1, rows, np.asarray(train), test_idx, gl)
        taus = [float(t) for t in args.gate_taus.split(",")]
        result["gated"] = {"gate_layer": gl, "gate_auroc": gate_auc, "points": []}
        print("\ngated steering (gate AUROC for 'turn-1 answer is right': "
              + ", ".join(f"{k} {v:.3f}" for k, v in gate_auc.items()) + ")")
        for layer in layers:
            lo_options = [0.0] + [a for a in alphas if a < 0]
            for a_hi in [a for a in alphas if a > 0]:
                for a_lo in lo_options:
                    hi = steer_rows[layer][a_hi]
                    lo = base_rows if a_lo == 0 else steer_rows[layer][a_lo]
                    for gname, g in gates.items():
                        for tau in (taus if gname != "oracle" else [0.5]):
                            mix = [h if gi >= tau else l for h, l, gi in zip(hi, lo, g)]
                            r = rates(mix)
                            pt = {"layer": layer, "alpha_right": a_hi, "alpha_wrong": a_lo, "gate": gname,
                                  "tau": tau, "steered_share": float(np.mean(g >= tau)), **r}
                            result["gated"]["points"].append(pt)
                            gated_pts.append(pt)
                            print(f"layer {layer} | +{a_hi:g} if P(right)>={tau:.2f} else {a_lo:+g} | {gname:16s} | "
                                  f"steered {pt['steered_share']:.2f} | cave {r['cave_rate']:.3f} "
                                  f"correct {r['correction_rate']:.3f} acc2 {r['acc_turn2']:.3f}", flush=True)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "steer.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"saved {os.path.join(args.out, 'steer.json')}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5, 5))
    colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(layers)))
    for c, layer in zip(colors, layers):
        for kind, ls in (("steer", "-"), ("random", ":")):
            pts = sorted([(a, base) if a == 0 else (a, result[kind][layer][a]) for a in alphas + [0.0]],
                         key=lambda t: t[0])
            xs, ys = [r["cave_rate"] for _, r in pts], [r["correction_rate"] for _, r in pts]
            ax.plot(xs, ys, ls=ls, marker="o" if kind == "steer" else ".", ms=4, color=c,
                    label=f"layer {layer} {'steering' if kind == 'steer' else 'random dir.'}")
            if kind == "steer":
                for (a, _), x, y in zip(pts, xs, ys):
                    ax.annotate(f"{a:g}", (x, y), fontsize=6, xytext=(3, 3), textcoords="offset points")
    if gated_pts:
        for gname, mk, col in (("confidence", "x", "tab:red"), ("probe+confidence", "+", "tab:green"),
                               ("oracle", "D", "tab:blue")):
            pts = [p for p in gated_pts if p["gate"] == gname]
            ax.scatter([p["cave_rate"] for p in pts], [p["correction_rate"] for p in pts], marker=mk, s=30,
                       c=col, alpha=0.7, label=f"gated steering ({gname} gate)")
    ax.scatter([base["cave_rate"]], [base["correction_rate"]], c="black", s=50, zorder=5, label="no steering")
    if "firm_prompt" in result:
        fp = result["firm_prompt"]
        ax.scatter([fp["cave_rate"]], [fp["correction_rate"]], marker="*", c="red", s=120, zorder=5,
                   label="firm system prompt")
    ax.set_xlabel("cave rate (right -> wrong)  — lower is better")
    ax.set_ylabel("correction rate (wrong -> right)  — higher is better")
    ax.set_title(f"Sycophancy vs. stubbornness ({args.model.split('/')[-1]}, {args.direction} direction)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "tradeoff.png"), dpi=150)
    print(f"saved {os.path.join(args.out, 'tradeoff.png')}")


if __name__ == "__main__":
    main()
