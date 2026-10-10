"""Does ACT's toy advantage depend on the upgrade being a basis rotation?

act_toy.py builds the upgraded model by rotating the hidden basis (W_t = Q_{l+1}(W_s + noise)Q_l^T).  ACT undoes
exactly that kind of change.  Real Base -> Instruct upgrades look different: the basis is shared and the weights
move (a fine-tuning delta).  This script re-runs the toy with three upgrade types and compares recovery of copy
and ACT at matched drift levels.

  rotation : original toy
  perturb  : W_t = W_s + dense random perturbation, same basis
  lowrank  : W_t = W_s + rank-8 update (fine-tuning-like), same basis

Task shift (--tau): in act_toy the target-model task is, by construction, the *same change* the source adapter
made, so ACT's objective (preserve the source adapter's effect) is exactly the right one.  With tau > 0 the
target task is dW_t = sqrt(1-tau^2) dW* + tau dW_new (a fresh rank-4 change), i.e. retraining on the target learns
something the source adapter never encoded, as when an instruction-tuned model needs a different answer style.

Also reports the mean activation drift of the layers ACT corrects, to compare with the real models
(SmolLM2: median 0.27, range 0.03-0.55).

Usage:  python act_toy_variants.py [--seeds 3] [--steps 1500]
"""
import argparse
import json
import os
import time

import numpy as np

import act_toy as T

ORIG_MAKE_WORLD = T.make_world


class DW(list):
    """dW* list carrying the target-task change as attribute .t."""


TAU = 0.0


def targets_shifted(Ws, Wt, dW_star, x):
    zero = [np.zeros((T.D, T.D))] * T.L
    ys = T.forward(Ws, dW_star, x)
    dWt = getattr(dW_star, "t", dW_star)
    yt = T.forward(Wt, zero, x) + T.forward(Ws, dWt, x) - T.forward(Ws, zero, x)
    return ys, yt


def with_task_shift(mk):
    def wrapped(rng, s):
        Ws, Wt, dW_star = mk(rng, s)
        new = [rng.standard_normal((T.D, T.RANK)) @ rng.standard_normal((T.RANK, T.D)) * (0.6 / T.D)
               for _ in range(T.L)]
        out = DW(dW_star)
        out.t = [np.sqrt(1 - TAU ** 2) * a + TAU * b for a, b in zip(dW_star, new)]
        return Ws, Wt, out
    return wrapped


def make_world_variant(kind):
    if kind == "rotation":
        return ORIG_MAKE_WORLD

    def mk(rng, s):
        Ws = [rng.standard_normal((T.D, T.D)) * (1.5 / np.sqrt(T.D)) for _ in range(T.L)]
        Wt = []
        for W in Ws:
            if kind == "perturb":
                E = rng.standard_normal((T.D, T.D))
            else:  # lowrank
                E = rng.standard_normal((T.D, 8)) @ rng.standard_normal((8, T.D))
            E *= 0.5 * s * np.linalg.norm(W) / np.linalg.norm(E)
            Wt.append(W + E)
        dW_star = [rng.standard_normal((T.D, T.RANK)) @ rng.standard_normal((T.RANK, T.D)) * (0.6 / T.D)
                   for _ in range(T.L)]
        return Ws, Wt, dW_star
    return mk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", nargs="+", default=["rotation", "perturb", "lowrank"])
    ap.add_argument("--drifts", type=float, nargs="+", default=[0.1, 0.3, 0.5, 0.8])
    ap.add_argument("--taus", type=float, nargs="+", default=[0.0])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--out", default="results/act_toy_variants.json")
    a = ap.parse_args()

    global TAU
    T.targets = targets_shifted
    results = {}
    print(f"{'upgrade':>9} {'tau':>4} {'s':>4} {'act drift':>9} {'R_copy':>8} {'R_ACT':>8} {'ACT-copy':>9} {'wins':>5}")
    for kind in a.kinds:
        for tau in a.taus:
            TAU = tau
            T.make_world = with_task_shift(make_world_variant(kind))
            key = f"{kind}|tau={tau}"
            results[key] = []
            for s in a.drifts:
                t0 = time.time()
                rows = [T.run_one(s, seed, a.steps, extra=False)[0] for seed in range(a.seeds)]
                copy = np.array([r["copy"] for r in rows])
                act = np.array([r["act"] for r in rows])
                drift = float(np.mean([np.mean(r["drift"][1:]) for r in rows]))
                e = dict(drift_param=s, tau=tau, act_drift=drift, R_copy=float(copy.mean()),
                         R_act=float(act.mean()), gain=float((act - copy).mean()),
                         gain_sd=float((act - copy).std()), wins=int((act > copy).sum()),
                         n=a.seeds, seconds=time.time() - t0)
                results[key].append(e)
                print(f"{kind:>9} {tau:4.1f} {s:4.1f} {drift:9.3f} {e['R_copy']:8.3f} {e['R_act']:8.3f} "
                      f"{e['gain']:+9.3f} {e['wins']:>3}/{a.seeds}", flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(results, open(a.out, "w"), indent=2)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
