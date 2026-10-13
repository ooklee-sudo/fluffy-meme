"""Dynamic Bertrand competition with capacity investment: Markov perfect equilibrium.

Two LLM-inference platforms i in {A, B} (state: GPU nodes m_i, demand regime lambda).
Each period both firms simultaneously choose a price p_i (Bertrand) and a capacity
action k_i in {0: hold, 1: expand, 2: contract} (Rust/Ericson-Pakes).  Customers buy
from the cheaper firm until its capacity binds, the residual goes to the dearer firm
(capacity-constrained Bertrand / Bertrand-Edgeworth, efficient rationing).

Equilibrium: stationary MPE with additive Type-I extreme value shocks on every
(price, capacity) choice, i.e. a logit Markov perfect equilibrium.  The logit shocks
(a) match the paper's assumption and (b) guarantee existence in a game where pure
Bertrand equilibria fail (Edgeworth cycles).  Stage games are solved as logit QRE
inside an outer value-function iteration (nested fixed point).

Benchmarks: joint-profit-maximising cartel, and the original
paper's market-share (contest) competition with a single posted price.
"""
import argparse
import json
import os
from dataclasses import dataclass, field, replace

import numpy as np

EULER = 0.5772156649015329


@dataclass(frozen=True)
class Params:
    beta: float = 0.95
    rho: float = 1.0                 # scale of the extreme-value shocks
    M: int = 5                       # nodes 0..M-1
    kappa: float = 15.0              # requests served per node per period
    lam: tuple = (10.0, 25.0, 45.0)  # demand regimes (Low, Med, High)
    P_lam: tuple = ((0.7, 0.2, 0.1), (0.2, 0.6, 0.2), (0.1, 0.3, 0.6))
    prices: tuple = (0.4, 0.8, 1.2, 1.5)   # price grid; max = reservation price
    mc: float = 0.3                  # marginal cost per served request
    pk: float = 2.0                  # holding cost per node
    fc: tuple = (12.0, 15.0)         # expansion cost of A, B
    contract_frac: float = 0.3       # contraction cost = frac * fc
    sla: float = 0.3                 # penalty per rejected (directed but unserved) request
    competition: str = "bertrand"    # "bertrand" | "share"


def next_m(p):
    nm = np.zeros((p.M, 3), dtype=int)
    for m in range(p.M):
        nm[m] = [m, min(p.M - 1, m + 1), max(0, m - 1)]
    return nm


def allocation(p):
    """Quantities and rejected requests, arrays (M, M, L, NP, NP) for firms A and B."""
    M, L, NP = p.M, len(p.lam), len(p.prices)
    mA = np.arange(M)[:, None, None, None, None]
    mB = np.arange(M)[None, :, None, None, None]
    D = np.array(p.lam)[None, None, :, None, None]
    pa = np.array(p.prices)[None, None, None, :, None]
    pb = np.array(p.prices)[None, None, None, None, :]
    KA, KB = p.kappa * mA, p.kappa * mB
    shape = (M, M, L, NP, NP)
    if p.competition == "bertrand":
        # directed demand: whole market to the cheaper firm, half each on a tie
        dA = np.where(pa < pb, D, np.where(pa == pb, D / 2, 0.0))
        dB = D - dA
        # each firm serves its directed demand up to capacity; the rival's overflow spills over
        qA = np.minimum(KA, dA + np.maximum(0.0, dB - KB))
        qB = np.minimum(KB, dB + np.maximum(0.0, dA - KA))
    else:  # proportional market share (contest), price ignored
        tot = mA + mB
        sh = np.where(tot == 0, 0.5, mA / np.maximum(tot, 1))
        dA = D * sh
        dB = D - dA
        qA = np.minimum(KA, dA)
        qB = np.minimum(KB, dB)
    rejA = np.maximum(0.0, dA - KA)
    rejB = np.maximum(0.0, dB - KB)
    return [np.broadcast_to(x, shape) for x in (qA, qB, rejA, rejB)]


class Game:
    def __init__(self, p: Params):
        self.p = p
        self.M, self.L, self.NP = p.M, len(p.lam), len(p.prices)
        self.NA = self.NP * 3
        self.nm = next_m(p)
        self.P = np.array(p.P_lam)
        qA, qB, rejA, rejB = allocation(p)
        self.q = (qA, qB)
        pr = np.array(p.prices)
        mA = np.arange(self.M)[:, None, None, None, None]
        mB = np.arange(self.M)[None, :, None, None, None]
        pa = pr[None, None, None, :, None]
        pb = pr[None, None, None, None, :]
        self.profit = (
            (pa - p.mc) * qA - p.sla * rejA - p.pk * mA,
            (pb - p.mc) * qB - p.sla * rejB - p.pk * mB,
        )
        self.rej = (rejA, rejB)
        # adjustment cost by own capacity action
        self.adj = tuple(np.array([0.0, f, p.contract_frac * f]) for f in p.fc)

    # ---- stage payoffs given continuation value ------------------------------
    def cont(self, V):
        """beta * E[V(m'_A, m'_B, lambda')], shape (M, M, L, 3, 3) over (kA, kB)."""
        EV = np.einsum("lx,abx->abl", self.P, V)
        An = self.nm[:, None, None, :, None]
        Bn = self.nm[None, :, None, None, :]
        l = np.arange(self.L)[None, None, :, None, None]
        return self.p.beta * EV[An, Bn, l]

    def U(self, profit, adjA, adjB, V):
        """Joint-action payoff tensor (M, M, L, NA, NA) with a = price_idx * 3 + k."""
        M, L, NP = self.M, self.L, self.NP
        c = self.cont(V)[:, :, :, None, :, None, :]            # (...,1,kA,1,kB)
        pro = profit[:, :, :, :, None, :, None]                  # (...,pa,1,pb,1)
        adj = (adjA[:, None] + adjB[None, :])[None, None, None, None, :, None, :]
        u = pro - adj + c
        return u.reshape(M, M, L, self.NA, self.NA)

    # ---- logit MPE ---------------------------------------------------------------
    def solve_mpe(self, tol=1e-4, max_outer=8000, inner=500, damp=0.1, vdamp=0.3, verbose=False):
        p = self.p
        S = self.M * self.M * self.L
        VA = np.zeros((self.M, self.M, self.L))
        VB = np.zeros_like(VA)
        sA = np.full((S, self.NA), 1.0 / self.NA)
        sB = sA.copy()
        for it in range(max_outer):
            UA = self.U(self.profit[0], self.adj[0], np.zeros(3), VA).reshape(S, self.NA, self.NA)
            UB = self.U(self.profit[1], np.zeros(3), self.adj[1], VB).reshape(S, self.NA, self.NA)
            for _ in range(inner):
                vA = np.einsum("sab,sb->sa", UA, sB)
                vB = np.einsum("sab,sa->sb", UB, sA)
                nA, nB = softmax(vA / p.rho), softmax(vB / p.rho)
                d = max(np.abs(nA - sA).max(), np.abs(nB - sB).max())
                sA, sB = damp * nA + (1 - damp) * sA, damp * nB + (1 - damp) * sB
                if d < 1e-10:
                    break
            vA = np.einsum("sab,sb->sa", UA, sB)
            vB = np.einsum("sab,sa->sb", UB, sA)
            nVA = (p.rho * (logsumexp(vA / p.rho) + EULER)).reshape(VA.shape)
            nVB = (p.rho * (logsumexp(vB / p.rho) + EULER)).reshape(VB.shape)
            err = max(np.abs(nVA - VA).max(), np.abs(nVB - VB).max())
            VA, VB = VA + vdamp * (nVA - VA), VB + vdamp * (nVB - VB)   # damped update
            if verbose and it % 50 == 0:
                print(f"  iter {it:4d}  |dV|={err:.3e}  stage-gap={d:.1e}")
            if err < tol:
                break
        self.V = (VA, VB)
        self.sigma = (sA.reshape(self.M, self.M, self.L, self.NA), sB.reshape(self.M, self.M, self.L, self.NA))
        self.outer_iters, self.converged, self.stage_gap = it + 1, err < tol, d
        return self

    # ---- joint-profit-maximising cartel ------------------------------------------------
    def solve_cartel(self, tol=1e-9, max_outer=5000):
        W = np.zeros((self.M, self.M, self.L))
        profit = self.profit[0] + self.profit[1]
        for it in range(max_outer):
            U = self.U(profit, self.adj[0], self.adj[1], W)
            nW = U.max(axis=(3, 4))
            err = np.abs(nW - W).max()
            W = nW
            if err < tol:
                break
        U = self.U(profit, self.adj[0], self.adj[1], W)
        flat = U.reshape(self.M, self.M, self.L, -1)
        best = flat.argmax(axis=3)
        sA = np.zeros((self.M, self.M, self.L, self.NA))
        sB = np.zeros_like(sA)
        ia, ib = best // self.NA, best % self.NA
        for a in range(self.M):
            for b in range(self.M):
                for l in range(self.L):
                    sA[a, b, l, ia[a, b, l]] = 1.0
                    sB[a, b, l, ib[a, b, l]] = 1.0
        self.sigma, self.V = (sA, sB), (W, W)
        self.converged, self.outer_iters = err < tol, it + 1
        return self

    # ---- ergodic analysis ---------------------------------------------------------------
    def action_parts(self, s):
        """Split an action distribution (..., NA) into price (..., NP) and capacity (..., 3)."""
        r = s.reshape(s.shape[:-1] + (self.NP, 3))
        return r.sum(-1), r.sum(-2)

    def stationary(self):
        M, L = self.M, self.L
        sA, sB = self.sigma
        pA, kA = self.action_parts(sA)
        pB, kB = self.action_parts(sB)
        S = M * M * L
        T = np.zeros((S, S))
        idx = lambda a, b, l: (a * M + b) * L + l
        for a in range(M):
            for b in range(M):
                for l in range(L):
                    for ka in range(3):
                        for kb in range(3):
                            w = kA[a, b, l, ka] * kB[a, b, l, kb]
                            if w < 1e-14:
                                continue
                            for l2 in range(L):
                                T[idx(a, b, l), idx(self.nm[a, ka], self.nm[b, kb], l2)] += w * self.P[l, l2]
        pi = np.full(S, 1.0 / S)
        for _ in range(100000):
            nxt = pi @ T
            if np.abs(nxt - pi).max() < 1e-13:
                pi = nxt
                break
            pi = nxt
        return pi.reshape(M, M, L)

    def summary(self):
        p = self.p
        pi = self.stationary()
        sA, sB = self.sigma
        PA, KA = self.action_parts(sA)
        PB, KB = self.action_parts(sB)
        pr = np.array(p.prices)
        qA, qB = self.q
        jp = PA[..., :, None] * PB[..., None, :]            # (M,M,L,pa,pb)
        E = lambda x: float((pi * (jp * x).sum((3, 4))).sum())
        servedA, servedB = E(qA), E(qB)
        served = servedA + servedB
        pa = pr[None, None, None, :, None]
        pb = pr[None, None, None, None, :]
        rev = E(pa * qA + pb * qB)
        profA = E(self.profit[0]) - float((pi * (KA * self.adj[0]).sum(-1)).sum())
        profB = E(self.profit[1]) - float((pi * (KB * self.adj[1]).sum(-1)).sum())
        mA = np.arange(p.M)[:, None, None]
        mB = np.arange(p.M)[None, :, None]
        D = np.array(p.lam)[None, None, :]
        cap = p.kappa * (mA + mB)
        both_exp = float((pi * KA[..., 1] * KB[..., 1]).sum())
        any_exp = float((pi * (1 - (1 - KA[..., 1]) * (1 - KB[..., 1]))).sum())
        # expansion when installed capacity already covers current demand ("redundant" expansion)
        redundant = float((pi * (cap >= D) * KA[..., 1] * KB[..., 1]).sum())
        E_rej = E(self.rej[0] + self.rej[1])
        avg_price = rev / served
        return {
            "avg_price": avg_price,
            "lerner": (avg_price - p.mc) / avg_price,
            "profit_A": profA, "profit_B": profB, "profit_total": profA + profB,
            "consumer_surplus": float(p.prices[-1] * served - rev),
            "served": served,
            "rejected": E_rej,
            "mean_nodes_A": float((pi * mA).sum()), "mean_nodes_B": float((pi * mB).sum()),
            "mean_capacity": float((pi * cap).sum()),
            "excess_capacity": float((pi * np.maximum(cap - D, 0)).sum()),
            "p_both_expand": both_exp, "p_any_expand": any_exp,
            "p_redundant_both_expand": redundant,
            "stationary": pi.tolist(),
        }

    def state_report(self, mA, mB, l):
        sA, sB = self.sigma
        out = {}
        for name, s in (("A", sA), ("B", sB)):
            pp, kk = self.action_parts(s[mA, mB, l])
            out[name] = {"price": pp.tolist(), "capacity": kk.tolist(),
                         "E_price": float(pp @ np.array(self.p.prices))}
        kA, kB = np.array(out["A"]["capacity"]), np.array(out["B"]["capacity"])
        out["P_both_expand"] = float(kA[1] * kB[1])
        return out


def softmax(x):
    x = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=-1, keepdims=True)


def logsumexp(x):
    m = x.max(axis=-1, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=-1, keepdims=True)))[..., 0]


def run_all(p: Params, verbose=True):
    """Solve the main model and benchmarks."""
    res, games = {}, {}
    cases = {
        "dynamic_bertrand": (replace(p), "mpe"),
        "cartel (joint profit)": (replace(p), "cartel"),
        "market_share_contest (original)": (replace(p, competition="share", prices=(p.prices[-1],)), "mpe"),
    }
    for name, (pp, kind) in cases.items():
        if verbose:
            print(f"[{name}]")
        g = Game(pp)
        g.solve_mpe(verbose=verbose) if kind == "mpe" else g.solve_cartel()
        res[name] = g.summary()
        res[name]["converged"] = bool(g.converged)
        res[name]["iterations"] = int(g.outer_iters)
        games[name] = g
    return res, games


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--beta", type=float, default=0.95)
    ap.add_argument("--rho", type=float, default=1.0, help="scale of extreme-value shocks")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    ap.add_argument("--sweep", action="store_true", help="also run sensitivity over rho and marginal cost")
    a = ap.parse_args()
    p = Params(beta=a.beta, rho=a.rho)
    os.makedirs(a.out, exist_ok=True)
    res, games = run_all(p)
    g = games["dynamic_bertrand"]
    L = {"Low": 0, "Med": 1, "High": 2}
    states = {f"({ma},{mb},{n})": g.state_report(ma, mb, L[n])
              for ma, mb, n in [(1, 1, "Med"), (1, 1, "High"), (2, 2, "Med"), (3, 3, "Med"),
                                (3, 3, "Low"), (2, 2, "High"), (1, 3, "High")]}
    out = {"params": p.__dict__, "models": {k: {kk: vv for kk, vv in v.items() if kk != "stationary"}
                                            for k, v in res.items()},
           "states": states}
    if a.sweep:
        sw = []
        for rho in (0.5, 1.0, 2.0, 4.0):
            for mc in (0.3, 0.6):
                r, _ = run_all(replace(p, rho=rho, mc=mc), verbose=False)
                sw.append({"rho": rho, "mc": mc,
                           **{k: {m: v[m] for m in ("avg_price", "lerner", "profit_total", "mean_capacity",
                                                     "p_both_expand", "converged")}
                              for k, v in r.items()}})
        out["sweep"] = sw
    with open(os.path.join(a.out, "dynamic_bertrand.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n{'model':36s} {'price':>6s} {'Lerner':>7s} {'profit':>7s} {'CS':>7s} {'cap':>6s} {'excess':>6s} {'P(2exp)':>7s}")
    for k, v in res.items():
        print(f"{k:36s} {v['avg_price']:6.3f} {v['lerner']:7.3f} {v['profit_total']:7.2f} "
              f"{v['consumer_surplus']:7.2f} {v['mean_capacity']:6.1f} {v['excess_capacity']:6.1f} {v['p_both_expand']:7.3f}")
    try:
        plot(g, res, a.out)
    except ImportError:
        print("matplotlib not installed; skipping figures")


def plot(g, res, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    p = g.p
    pi = np.array(res["dynamic_bertrand"]["stationary"]).reshape(g.M, g.M, g.L)
    sA, sB = g.sigma
    PA, _ = g.action_parts(sA)
    PB, _ = g.action_parts(sB)
    pr = np.array(p.prices)
    EpA, EpB = PA @ pr, PB @ pr
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    for l, ax in enumerate(axs):
        im = ax.imshow(0.5 * (EpA + EpB)[:, :, l], origin="lower", vmin=pr.min(), vmax=pr.max(), cmap="viridis")
        ax.set_title(f"λ = {['Low', 'Med', 'High'][l]} ({p.lam[l]:g})")
        ax.set_xlabel("nodes of B")
        ax.set_xticks(range(g.M)); ax.set_yticks(range(g.M))
    axs[0].set_ylabel("nodes of A")
    fig.colorbar(im, ax=axs, label="expected posted price")
    fig.savefig(os.path.join(outdir, "price_by_state.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    names = list(res)
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.4))
    short = ["dynamic\nBertrand", "cartel", "share\ncontest"]
    for ax, key, title in zip(axs, ("avg_price", "mean_capacity", "profit_total"),
                              ("avg. transaction price", "mean total nodes×κ (capacity)", "industry profit / period")):
        ax.bar(short, [res[n][key] for n in names], color=["#3b6ea8", "#c9733a", "#8a8a8a"])
        ax.set_title(title, fontsize=10)
    fig.savefig(os.path.join(outdir, "benchmarks.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
