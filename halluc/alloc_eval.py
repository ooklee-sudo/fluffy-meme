"""Out-of-sample evaluation of verification-allocation policies on the observed sentence-level error labels.

Unit = sentence with at least one claim (as in analyze_sent.py, mode 'all'); y = 1 if it contains a contradicted claim.
Model (fitted on training documents by marginal likelihood, Gauss-Hermite over the document factor Z):
    logit p_dt = x_dt' gamma + Z_d,   Z_d ~ N(0, tau^2),   x = [1, lead sentence, pos, pos^2, rarity]
Cost: 1 per sentence (--cost unit) or the sentence's number of claims (--cost claims; policies rank by p/c).
Verification of a unit detects an error in it with probability delta (and repairs it). Outcome: share of all errors caught.

Settings
  within : every document gets its own budget phi * n_d.     Policies: uniform, lead-only, tail-only, static (model)
  pooled : one budget phi * N over all test documents.      Policies: uniform, static (prior p), adaptive (Bayes-greedy)
Static ranks units by the prior predictive p_dt = E[sigma(x'gamma + Z)]. Adaptive re-ranks after each verification by the
posterior of the verified document's Z. Cross-fitting: documents are split into K folds; policies for a fold use a model
fitted on the other folds only. CIs: bootstrap over test documents (policy sets fixed).
"""
import argparse
import os

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp

from common import DATA, read_jsonl

GH_X, GH_W = np.polynomial.hermite.hermgauss(21)
LOGW = np.log(GH_W / np.sqrt(np.pi))


def load(path, cost="unit"):
    docs = []
    for r in read_jsonl(path):
        by = {}
        for c in r["claims"]:
            by.setdefault(c["sent"], []).append(c["label"])
        y = np.array([int("C" in by[s]) for s in sorted(by)])
        k = np.array([len(by[s]) for s in sorted(by)], float)
        n = len(y)
        if n < 6:
            continue
        rank = np.arange(1, n + 1)
        pos = (rank - 0.5) / n
        cols = [np.ones(n), (rank == 1).astype(float), pos - 0.5, (pos - 0.5) ** 2, np.full(n, np.log(r["sitelinks"] + 1))]
        if cost == "claims":
            cols.append(np.log(k))
        docs.append({"title": r["title"], "y": y, "X": np.column_stack(cols), "c": k if cost == "claims" else np.ones(n)})
    m = np.mean([d["X"][0, 4] for d in docs])
    for d in docs:
        d["X"][:, 4] -= m
    if cost == "claims":
        mk = np.mean(np.concatenate([d["X"][:, 5] for d in docs]))
        for d in docs:
            d["X"][:, 5] -= mk
    return docs


def stack(docs):
    X = np.vstack([d["X"] for d in docs])
    y = np.concatenate([d["y"] for d in docs])
    g = np.concatenate([np.full(len(d["y"]), i) for i, d in enumerate(docs)])
    return X, y, g


def negll(theta, X, y, g, ndoc):
    gam, tau = theta[:-1], np.exp(theta[-1])
    eta = X @ gam
    z = eta[:, None] + np.sqrt(2) * tau * GH_X[None, :]
    ll = y[:, None] * z - np.logaddexp(0, z)
    S = np.zeros((ndoc, len(GH_X)))
    np.add.at(S, g, ll)
    return -logsumexp(S + LOGW[None, :], axis=1).sum()


def fit(docs):
    X, y, g = stack(docs)
    th0 = np.zeros(X.shape[1] + 1)
    th0[0] = np.log(y.mean() / (1 - y.mean()))
    res = minimize(negll, th0, args=(X, y, g, len(docs)), method="L-BFGS-B")
    return res.x[:-1], float(np.exp(res.x[-1]))


def prior_p(eta, tau):
    return (expit(eta[:, None] + np.sqrt(2) * tau * GH_X[None, :]) * np.exp(LOGW)[None, :]).sum(1)


def greedy(order, c, budget):
    """Walk `order`, take every unit that still fits in the remaining budget."""
    take, left = [], budget
    for i in order:
        if c[i] <= left + 1e-9:
            take.append(i)
            left -= c[i]
    return np.array(take, int)


def eval_within(docs, gam, tau, phi):
    """Caught-error counts per doc under per-document budgets (cost-aware: rank by p/c)."""
    out = {k: np.zeros(len(docs)) for k in ("uniform", "lead", "tail", "static")}
    tot = np.array([d["y"].sum() for d in docs], float)
    for i, d in enumerate(docs):
        y, c = d["y"], d["c"]
        n = len(y)
        B = round(phi * c.sum())
        out["uniform"][i] = y.sum() * min(B / c.sum(), 1.0)
        out["lead"][i] = y[greedy(range(n), c, B)].sum()
        out["tail"][i] = y[greedy(range(n - 1, -1, -1), c, B)].sum()
        q = prior_p(d["X"] @ gam, tau)
        out["static"][i] = y[greedy(np.argsort(-q / c, kind="stable"), c, B)].sum()
    return out, tot


def eval_pooled(docs, gam, tau, phi, delta, rng):
    X, y, g = stack(docs)
    c = np.concatenate([d["c"] for d in docs])
    B = round(phi * c.sum())
    eta = X @ gam
    q0 = prior_p(eta, tau)
    tot = np.array([d["y"].sum() for d in docs], float)
    caught = {k: np.zeros(len(docs)) for k in ("uniform", "static", "adaptive")}
    caught["uniform"] = tot * min(B / c.sum(), 1.0) * delta
    top = greedy(np.argsort(-q0 / c, kind="stable"), c, B)
    np.add.at(caught["static"], g[top], y[top] * delta)

    # adaptive: Bayes-greedy on p/c, posterior of Z on the Gauss-Hermite grid
    sig = expit(eta[:, None] + np.sqrt(2) * tau * GH_X[None, :])
    lw = np.tile(LOGW, (len(docs), 1))
    q = q0.copy()
    idx = [np.where(g == i)[0] for i in range(len(docs))]
    free_mask = np.ones(len(y), bool)
    left = float(B)
    while True:
        score = np.where(free_mask & (c <= left + 1e-9), q / c, -np.inf)
        u = int(np.argmax(score))
        if not np.isfinite(score[u]):
            break
        d = g[u]
        free_mask[u] = False
        left -= c[u]
        det = y[u] == 1 and rng.random() < delta
        p_obs = sig[u] * delta
        lw[d] += np.log(p_obs) if det else np.log1p(-p_obs)
        caught["adaptive"][d] += y[u] * delta
        post = np.exp(lw[d] - logsumexp(lw[d]))
        f = idx[d][free_mask[idx[d]]]
        q[f] = sig[f] @ post
    return caught, tot


def boot(num_a, num_b, tot, B=2000, seed=0):
    rng = np.random.default_rng(seed)
    n = len(tot)
    diffs = []
    for _ in range(B):
        k = rng.integers(0, n, n)
        diffs.append((num_a[k].sum() - num_b[k].sum()) / tot[k].sum())
    return np.percentile(diffs, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default=os.path.join(DATA, "labs_gemma-3-27b-it.jsonl"))
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cost", choices=["unit", "claims"], default="unit",
                    help="unit: every sentence costs 1; claims: cost = number of claims in the sentence (log k enters the model)")
    a = ap.parse_args()
    docs = load(a.lab, a.cost)
    rng = np.random.default_rng(a.seed)
    perm = rng.permutation(len(docs))
    fold = np.zeros(len(docs), int)
    fold[perm] = np.arange(len(docs)) % a.folds
    gam, tau = fit(docs)
    print(f"{os.path.basename(a.lab)}: {len(docs)} docs, {sum(len(d['y']) for d in docs)} units, error rate {np.mean(np.concatenate([d['y'] for d in docs])):.3f}")
    print(f"cost = {a.cost}; full-sample fit: gamma [const, lead, pos, pos^2, rarity{', log k' if a.cost == 'claims' else ''}] =", np.round(gam, 2), " tau =", round(tau, 2))

    print("\n== WITHIN-document budgets (share of all errors caught) ==")
    print(f"{'phi':>5}{'uniform':>9}{'lead':>8}{'tail':>8}{'static':>8}   static-uniform [95% CI]")
    for phi in (0.1, 0.2, 0.3, 0.5):
        agg = {k: np.zeros(len(docs)) for k in ("uniform", "lead", "tail", "static")}
        tot = np.zeros(len(docs))
        for f in range(a.folds):
            te = np.where(fold == f)[0]
            gf, tf = fit([docs[i] for i in np.where(fold != f)[0]])
            c, t = eval_within([docs[i] for i in te], gf, tf, phi)
            for k in agg:
                agg[k][te] = c[k]
            tot[te] = t
        lo, hi = boot(agg["static"], agg["uniform"], tot)
        print(f"{phi:5.1f}" + "".join(f"{agg[k].sum()/tot.sum():9.3f}" for k in ("uniform", "lead", "tail", "static")) + f"   {(agg['static'].sum()-agg['uniform'].sum())/tot.sum():+.3f} [{lo:+.3f},{hi:+.3f}]")

    for delta in (1.0, 0.8):
        print(f"\n== POOLED budget, detection prob delta={delta} (share of all errors; caught = delta x verified errors) ==")
        print(f"{'phi':>5}{'uniform':>9}{'static':>8}{'adaptive':>9}   static-uniform [CI]        adaptive-static [CI]")
        for phi in (0.1, 0.2, 0.3, 0.5):
            agg = {k: np.zeros(len(docs)) for k in ("uniform", "static", "adaptive")}
            tot = np.zeros(len(docs))
            for f in range(a.folds):
                te = np.where(fold == f)[0]
                gf, tf = fit([docs[i] for i in np.where(fold != f)[0]])
                c, t = eval_pooled([docs[i] for i in te], gf, tf, phi, delta, np.random.default_rng(a.seed + f))
                for k in agg:
                    agg[k][te] = c[k]
                tot[te] = t
            s_u = boot(agg["static"], agg["uniform"], tot)
            a_s = boot(agg["adaptive"], agg["static"], tot)
            T = tot.sum()
            print(f"{phi:5.1f}{agg['uniform'].sum()/T:9.3f}{agg['static'].sum()/T:8.3f}{agg['adaptive'].sum()/T:9.3f}"
                  f"   {(agg['static'].sum()-agg['uniform'].sum())/T:+.3f} [{s_u[0]:+.3f},{s_u[1]:+.3f}]"
                  f"   {(agg['adaptive'].sum()-agg['static'].sum())/T:+.3f} [{a_s[0]:+.3f},{a_s[1]:+.3f}]")


if __name__ == "__main__":
    main()
