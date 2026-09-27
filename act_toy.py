"""Toy simulation of Anchored Calibration Transfer (Appendix B). numpy only, single CPU.

Setup (B.1):
  - 4-layer MLP, width 32, tanh, rank-4 LoRA on every layer.
  - Upgrade: W_t = Q_{l+1} (W_s + noise) Q_l^T, Q = partial rotation of the hidden basis
    (angle = drift s), noise sd = 0.3 s / sqrt(d). Input/output bases fixed (shared tokenizer).
  - Task: hidden rank-4 modification dW* on the source. Target ground truth
    g_t(x) = f_t(x) + [f_{s+dW*}(x) - f_s(x)].
  - Adam, 2000 training examples, full batch, 1500 steps. Retraining upper bound = same on target.
  - Recovery R = (MSE_none - MSE_method) / (MSE_none - MSE_retrain), test set of 2000.
  - ACT: 256 unlabeled task inputs, 13 alphas in [1e-3, 1e3], per-layer choice with 80/20 split.

Usage:
  python act_toy.py                 # main table: drifts x seeds, copy / ACT / ACT-indep / ACT-full
  python act_toy.py --quick         # fewer seeds and steps
"""
import argparse
import json
import os
import time

import numpy as np
from scipy.linalg import expm
from scipy.stats import spearmanr

D, L, RANK = 32, 4, 4
ALPHAS = np.logspace(-3, 3, 13)


# ---------------------------------------------------------------- model
def forward(Ws, dWs, x, keep=False):
    """x: (d, n). Layers 0..L-2 use tanh; last layer is linear. Returns output (and layer inputs)."""
    h, inputs = x, []
    for l, (W, dW) in enumerate(zip(Ws, dWs)):
        inputs.append(h)
        z = (W + dW) @ h
        h = np.tanh(z) if l < L - 1 else z
    return (h, inputs) if keep else h


def lora_dW(A, B):
    return [b @ a for a, b in zip(A, B)]


def train_lora(Ws, x, y, rng, steps, lr=1e-2, init=None):
    """Full-batch Adam on LoRA factors (A: r x d, B: d x r) with MSE loss."""
    if init is None:
        A = [rng.standard_normal((RANK, D)) / np.sqrt(D) for _ in range(L)]
        B = [np.zeros((D, RANK)) for _ in range(L)]
    else:
        A, B = [a.copy() for a in init[0]], [b.copy() for b in init[1]]
    params = A + B
    m = [np.zeros_like(q) for q in params]
    v = [np.zeros_like(q) for q in params]
    b1, b2, eps = 0.9, 0.999, 1e-8
    n = x.shape[1]
    for t in range(1, steps + 1):
        dW = lora_dW(A, B)
        hs, zs, h = [x], [], x
        for l in range(L):
            z = (Ws[l] + dW[l]) @ h
            zs.append(z)
            h = np.tanh(z) if l < L - 1 else z
            hs.append(h)
        g = 2 * (h - y) / (n * y.shape[0])
        gA, gB = [None] * L, [None] * L
        for l in reversed(range(L)):
            if l < L - 1:
                g = g * (1 - hs[l + 1] ** 2)
            gW = g @ hs[l].T
            gA[l] = B[l].T @ gW
            gB[l] = gW @ A[l].T
            g = (Ws[l] + dW[l]).T @ g
        grads = gA + gB
        for i, (q, gr) in enumerate(zip(params, grads)):
            m[i] = b1 * m[i] + (1 - b1) * gr
            v[i] = b2 * v[i] + (1 - b2) * gr * gr
            q -= lr * (m[i] / (1 - b1 ** t)) / (np.sqrt(v[i] / (1 - b2 ** t)) + eps)
    return A, B


def mse(Ws, dWs, x, y):
    return float(np.mean((forward(Ws, dWs, x) - y) ** 2))


# ---------------------------------------------------------------- upgrade
def partial_rotation(rng, s):
    """Orthogonal matrix exp(s K) with K skew-symmetric of unit spectral norm: max angle = s rad."""
    G = rng.standard_normal((D, D))
    K = G - G.T
    K /= np.abs(np.linalg.eigvals(K)).max()
    return expm(s * K)


def make_world(rng, s):
    Ws = [rng.standard_normal((D, D)) * (1.5 / np.sqrt(D)) for _ in range(L)]
    Qs = [np.eye(D)] + [partial_rotation(rng, s) for _ in range(L - 1)] + [np.eye(D)]
    Wt = [Qs[l + 1] @ (Ws[l] + rng.standard_normal((D, D)) * 0.3 * s / np.sqrt(D)) @ Qs[l].T
          for l in range(L)]
    dW_star = [rng.standard_normal((D, RANK)) @ rng.standard_normal((RANK, D)) * (0.6 / D)
               for _ in range(L)]
    return Ws, Wt, dW_star


def targets(Ws, Wt, dW_star, x):
    zero = [np.zeros((D, D))] * L
    ys = forward(Ws, dW_star, x)
    yt = forward(Wt, zero, x) + ys - forward(Ws, zero, x)
    return ys, yt


# ---------------------------------------------------------------- ACT
def act_layer(A_s, B_s, Xs, Xt, alpha, full=False, W_s=None, W_t=None):
    """Closed-form ACT for one layer. Returns new (A, B)."""
    lam = alpha * np.trace(Xt @ Xt.T) / D
    Gtt = Xt @ Xt.T + lam * np.eye(D)
    if not full:  # eq. A.2: A_t = A_s (X_s X_t^T + lam I)(X_t X_t^T + lam I)^{-1}
        rhs = A_s @ (Xs @ Xt.T + lam * np.eye(D))
        return np.linalg.solve(Gtt, rhs.T).T, B_s.copy()
    dWs = B_s @ A_s  # ACT-full: match (W+dW)X, then truncate to rank r
    rhs = ((W_s + dWs) @ Xs - W_t @ Xt) @ Xt.T + lam * dWs
    dW = np.linalg.solve(Gtt, rhs.T).T
    U, S, Vt = np.linalg.svd(dW)
    return Vt[:RANK], U[:, :RANK] * S[:RANK]


def act_val_err(A, B, A_s, B_s, Xs_v, Xt_v, full=False, W_s=None, W_t=None):
    """Validation change-matching error, computed from Gram matrices only."""
    Gtt, Gts, Gss = Xt_v @ Xt_v.T, Xt_v @ Xs_v.T, Xs_v @ Xs_v.T
    dW, dWs = B @ A, B_s @ A_s
    if full:
        dW, dWs = W_t + dW, W_s + dWs
    return (np.trace(dW @ Gtt @ dW.T) - 2 * np.trace(dW @ Gts @ dWs.T)
            + np.trace(dWs @ Gss @ dWs.T))


def act(Ws, Wt, A_s, B_s, xcal, rng, mode="seq", fixed_alpha=None):
    """mode: 'seq' (sequential, default), 'indep' (per-layer, inputs from copy), 'full'."""
    dWs = lora_dW(A_s, B_s)
    _, Xs_all = forward(Ws, dWs, xcal, keep=True)
    n = xcal.shape[1]
    perm = rng.permutation(n)
    fit, val = perm[: int(0.8 * n)], perm[int(0.8 * n):]
    A, B = [a.copy() for a in A_s], [b.copy() for b in B_s]
    _, Xt_copy = forward(Wt, dWs, xcal, keep=True)
    chosen, drift = [], []
    for l in range(L):
        if mode == "indep":
            Xt = Xt_copy[l]
        else:
            _, Xt_cur = forward(Wt, lora_dW(A, B), xcal, keep=True)
            Xt = Xt_cur[l]
        Xs = Xs_all[l]
        full = mode == "full"
        kw = dict(full=full, W_s=Ws[l], W_t=Wt[l])
        if fixed_alpha is not None:
            best = fixed_alpha
        else:
            errs = [act_val_err(*act_layer(A_s[l], B_s[l], Xs[:, fit], Xt[:, fit], a, **kw),
                                A_s[l], B_s[l], Xs[:, val], Xt[:, val], **kw) for a in ALPHAS]
            best = ALPHAS[int(np.argmin(errs))]
        A[l], B[l] = act_layer(A_s[l], B_s[l], Xs, Xt, best, **kw)
        chosen.append(best)
        drift.append(np.linalg.norm(Xt - Xs) / np.linalg.norm(Xs))
    return A, B, chosen, drift


# ---------------------------------------------------------------- experiment
def run_one(s, seed, steps, n_cal=256, extra=True):
    rng = np.random.default_rng(seed)
    Ws, Wt, dW_star = make_world(rng, s)
    x_tr, x_te = rng.standard_normal((D, 2000)), rng.standard_normal((D, 2000))
    ys_tr, _ = targets(Ws, Wt, dW_star, x_tr)
    _, yt_tr = targets(Ws, Wt, dW_star, x_tr)
    _, yt_te = targets(Ws, Wt, dW_star, x_te)
    zero = [np.zeros((D, D))] * L

    A_s, B_s = train_lora(Ws, x_tr, ys_tr, rng, steps)
    A_r, B_r = train_lora(Wt, x_tr, yt_tr, rng, steps)
    none, retr = mse(Wt, zero, x_te, yt_te), mse(Wt, lora_dW(A_r, B_r), x_te, yt_te)
    rec = lambda m: (none - m) / (none - retr)

    out = {"s": s, "seed": seed, "mse_none": none, "mse_retrain": retr}
    out["copy"] = rec(mse(Wt, lora_dW(A_s, B_s), x_te, yt_te))
    xcal = rng.standard_normal((D, n_cal))
    A, B, alphas, drift = act(Ws, Wt, A_s, B_s, xcal, rng, "seq")
    out["act"] = rec(mse(Wt, lora_dW(A, B), x_te, yt_te))
    out["alphas"], out["drift"] = alphas, drift
    if extra:
        for mode in ("indep", "full"):
            A, B, _, _ = act(Ws, Wt, A_s, B_s, xcal, rng, mode)
            out[f"act_{mode}"] = rec(mse(Wt, lora_dW(A, B), x_te, yt_te))
    return out, (Ws, Wt, A_s, B_s, x_te, yt_te, rec)


def summarize(rows, keys):
    by = {}
    for r in rows:
        by.setdefault(r["s"], []).append(r)
    table = []
    for s, rs in sorted(by.items()):
        e = {"drift": s}
        for k in keys:
            vals = np.array([r[k] for r in rs])
            e[k], e[k + "_sd"] = float(vals.mean()), float(vals.std())
        table.append(e)
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drifts", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.3, 0.5, 0.8])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default="results/act_toy.json")
    a = ap.parse_args()
    if a.quick:
        a.seeds, a.steps = 2, 500
    t0 = time.time()

    # --- B.2 main results: drift levels x seeds
    rows, worlds = [], {}
    for s in a.drifts:
        for seed in range(a.seeds):
            r, w = run_one(s, seed, a.steps)
            rows.append(r)
            worlds[(s, seed)] = w
    keys = ["copy", "act", "act_indep", "act_full"]
    table = summarize(rows, keys)
    print(f"\n== B.2 Recovery R (mean +- sd over {a.seeds} seeds) ==")
    print(f"{'drift':>6} " + " ".join(f"{k:>16}" for k in keys))
    for e in table:
        print(f"{e['drift']:6.1f} " + " ".join(f"{e[k]:8.3f} +- {e[k + '_sd']:.3f}" for k in keys))
    wins = {s: sum(r["act"] > r["copy"] for r in rows if r["s"] == s) for s in a.drifts}
    print("ACT > copy (seeds):", wins)

    # --- calibration size at s = 0.3
    s_cal = 0.3 if 0.3 in a.drifts else a.drifts[len(a.drifts) // 2]
    print(f"\n== Calibration size (s = {s_cal}) ==")
    cal = []
    for n in (8, 16, 32, 64, 256, 1024):
        Rs, beats = [], 0
        for seed in range(a.seeds):
            Ws, Wt, A_s, B_s, x_te, yt_te, rec = worlds[(s_cal, seed)]
            rng = np.random.default_rng(1000 + seed)
            A, B, _, _ = act(Ws, Wt, A_s, B_s, rng.standard_normal((D, n)), rng)
            R = rec(mse(Wt, lora_dW(A, B), x_te, yt_te))
            Rc = rec(mse(Wt, lora_dW(A_s, B_s), x_te, yt_te))
            Rs.append(R)
            beats += R > Rc
        cal.append({"n_cal": n, "R_A": float(np.mean(Rs)), "beats_copy": int(beats)})
        print(f"n={n:5d}: R_A={np.mean(Rs):.4f}  beats copy on {beats}/{a.seeds} seeds")

    # --- fixed-alpha sweep (limit property: alpha -> inf equals copy)
    print(f"\n== Fixed alpha sweep (s = {s_cal}) ==")
    sweep = []
    for alpha in (1e-3, 1e-1, 1e1, 1e3, 1e5):
        Rs = []
        for seed in range(a.seeds):
            Ws, Wt, A_s, B_s, x_te, yt_te, rec = worlds[(s_cal, seed)]
            rng = np.random.default_rng(2000 + seed)
            A, B, _, _ = act(Ws, Wt, A_s, B_s, rng.standard_normal((D, 256)), rng, fixed_alpha=alpha)
            Rs.append(rec(mse(Wt, lora_dW(A, B), x_te, yt_te)))
        sweep.append({"alpha": alpha, "R_A": float(np.mean(Rs))})
        print(f"alpha={alpha:8g}: R_A={np.mean(Rs):.4f}")
    print(f"copy: {table[[e['drift'] for e in table].index(s_cal)]['copy']:.4f}")

    # --- B.3 hypothesis: drift predicts correction strength
    la, dr = [], []
    for r in rows:
        if r["s"] == 0:
            continue
        for l in range(1, L):  # layer 0 input is identical (fixed input basis)
            la.append(np.log10(r["alphas"][l]))
            dr.append(r["drift"][l])
    rho, pval = spearmanr(la, dr)
    print(f"\n== B.3 Spearman(log alpha_l, activation drift) over {len(la)} layers: "
          f"rho={rho:.2f}, p={pval:.2f}")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    recovery = [{"drift": e["drift"], "R_C": e["copy"], "R_A": e["act"]} for e in table if e["drift"] > 0]
    json.dump({"recovery": recovery, "table": table, "calibration": cal, "alpha_sweep": sweep,
               "spearman": {"rho": float(rho), "p": float(pval), "n": len(la)}, "runs": rows},
              open(a.out, "w"), indent=2, default=float)
    print(f"\nsaved {a.out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
