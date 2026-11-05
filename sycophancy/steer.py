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

from syco import LETTERS, Steer, answer_turn2, letter_ids, load_mmlu, load_model, n_tokens, rates, \
    turn2_text, verbal_agree


def evaluate(model, tok, ids, items, rows, challenge, system, mode, max_new, layer=None, vec=None):
    """Re-ask turn 2 for `rows` (turn-1 answers fixed) with optional steering; return rows with new a2."""
    out = []
    steer_ctx = Steer(model, layer - 1) if vec is not None else None  # hidden index h = output of block h-1
    if steer_ctx:
        steer_ctx.__enter__()
    try:
        for r in rows:
            item = items[r["idx"]]
            if steer_ctx:
                _, prefix = turn2_text(tok, item, r["a1"], challenge, system, prefill=(mode == "prefill"))
                steer_ctx.vec = vec.to(model.device)
                steer_ctx.start = n_tokens(tok, prefix)
            p2, reply, _, _ = answer_turn2(model, tok, item, r["a1"], challenge, system, ids, mode, max_new)
            out.append({**r, "a2": LETTERS[int(p2.argmax())], "verbal_agree": verbal_agree(reply) if reply else None})
    finally:
        if steer_ctx:
            steer_ctx.__exit__(None, None, None)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", help="run from run_challenge.py (needs hidden_t2.npy)")
    p.add_argument("--model", required=True, help="same model as the run")
    p.add_argument("--quant", default="4bit", choices=["4bit", "none"])
    p.add_argument("--out", required=True)
    p.add_argument("--layers", default="", help="comma list of layer indices; default 3 layers at 1/3, 1/2, 2/3 depth")
    p.add_argument("--alphas", default="-2,-1,1,2,4,8")
    p.add_argument("--n-test", type=int, default=600, help="max test questions (cost grows linearly)")
    p.add_argument("--firm-run", help="run made with --system firm on the same questions")
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
    mode, max_new = meta.get("turn2", "prefill"), meta.get("max_new_tokens", 96)

    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n)
    train, test = perm[: n // 2], perm[n // 2:][: args.n_test]
    test_rows = [rows[i] for i in sorted(test)]

    held = [i for i in train if rows[i]["outcome"] == "held_correct"]
    caved = [i for i in train if rows[i]["outcome"] == "caved"]
    print(f"train: {len(held)} held / {len(caved)} caved (right in turn 1) | test questions: {len(test_rows)}")
    if len(caved) < args.min_caved:
        raise SystemExit("fewer than 10 caved examples in the train half; use more questions or a "
                         "stronger challenge (--challenge wrong)")

    n_layers = H2.shape[1]
    layers = ([int(x) for x in args.layers.split(",")] if args.layers
              else sorted({round(n_layers * f) for f in (1 / 3, 1 / 2, 2 / 3)}))
    alphas = [float(a) for a in args.alphas.split(",")]

    model, tok = load_model(args.model, args.quant)
    ids = letter_ids(tok)

    t0 = time.time()
    base = rates(test_rows)  # alpha = 0: the recorded turn-2 answers
    print(f"no steering: cave {base['cave_rate']:.3f} | correction {base['correction_rate']:.3f}")
    result = {"run": args.run_dir, "model": args.model, "layers": layers, "alphas": alphas,
              "n_test": len(test_rows), "baseline": base, "steer": {}, "random": {}}

    if args.firm_run:
        with open(os.path.join(args.firm_run, "results.jsonl")) as f:
            firm = [json.loads(line) for line in f if line.strip()]
        firm_test = [firm[i] for i in sorted(test) if i < len(firm)]
        result["firm_prompt"] = rates(firm_test)
        print(f"firm prompt: cave {result['firm_prompt']['cave_rate']:.3f} | "
              f"correction {result['firm_prompt']['correction_rate']:.3f}")

    for layer in layers:
        d = (np.asarray(H2[held, layer], dtype=np.float64).mean(0)
             - np.asarray(H2[caved, layer], dtype=np.float64).mean(0))
        d = torch.tensor(d, dtype=torch.float32)
        g = torch.Generator().manual_seed(args.seed + layer)
        rnd = torch.randn(d.shape, generator=g)
        rnd = rnd / rnd.norm() * d.norm()
        result["steer"][layer], result["random"][layer] = {}, {}
        for a in alphas:
            for kind, vec in (("steer", d), ("random", rnd)):
                rr = rates(evaluate(model, tok, ids, items, test_rows, challenge, system, mode, max_new,
                                    layer, a * vec))
                result[kind][layer][a] = rr
            s, q = result["steer"][layer][a], result["random"][layer][a]
            print(f"layer {layer:3d} alpha {a:+5.1f} | steer: cave {s['cave_rate']:.3f} correct "
                  f"{s['correction_rate']:.3f} acc2 {s['acc_turn2']:.3f} verbal-only {s['verbal_only_rate']:.3f} | random: cave {q['cave_rate']:.3f} "
                  f"correct {q['correction_rate']:.3f} | {time.time() - t0:.0f}s")

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
    ax.scatter([base["cave_rate"]], [base["correction_rate"]], c="black", s=50, zorder=5, label="no steering")
    if "firm_prompt" in result:
        fp = result["firm_prompt"]
        ax.scatter([fp["cave_rate"]], [fp["correction_rate"]], marker="*", c="red", s=120, zorder=5,
                   label="firm system prompt")
    ax.set_xlabel("cave rate (right -> wrong)  — lower is better")
    ax.set_ylabel("correction rate (wrong -> right)  — higher is better")
    ax.set_title(f"Sycophancy vs. stubbornness ({args.model.split('/')[-1]})")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "tradeoff.png"), dpi=150)
    print(f"saved {os.path.join(args.out, 'tradeoff.png')}")


if __name__ == "__main__":
    main()
