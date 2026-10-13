"""Controlled timing experiment: what drives the capacity difference between simultaneous and alternating pricing?

The alternating-move game of alternating.py differs from the baseline in two ways: prices are committed for two
periods, and each firm adjusts capacity only every second period, in alternation.  This script adds two designs that
keep simultaneous pricing every period but change only the timing of capacity decisions, so that the two channels can
be separated:

  C0  simultaneous prices, capacity every period            (baseline, bertrand_mpe.Game.solve_decoupled)
  C1  simultaneous prices, capacity staggered: A adjusts in even periods, B in odd periods
  C1s simultaneous prices, capacity synchronised every other period (both adjust in even periods)
  C2  alternating prices (committed), capacity at own move   (alternating.AltGame)

C1 vs C0 isolates capacity timing; C2 vs C1 isolates price commitment (both stagger capacity identically).
Pricing is a static logit QRE in every state in C0, C1 and C1s, because prices do not enter the state there
(Proposition 1), so these three designs are solved exactly like the baseline.

python timing_experiment.py
"""
import json
import os
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from alternating import AltGame
from bertrand_mpe import EULER, Game, Params, logsumexp, softmax

HERE = os.path.dirname(os.path.abspath(__file__))
NEG = -1e9


class PhaseGame:
    """Two-phase capacity timing with simultaneous pricing every period."""

    def __init__(self, p: Params, mode: str):
        self.p, self.mode = p, mode
        self.g = Game(p)
        self.M, self.L, self.NP = p.M, len(p.lam), len(p.prices)
        self.S = self.M * self.M * self.L
        # phase -> (A may adjust capacity, B may adjust capacity)
        self.active = {"staggered": [(True, False), (False, True)], "sync": [(True, True), (False, False)]}[mode]

    def _price_stage(self):
        p, S, NP = self.p, self.S, self.NP
        PA = self.g.profit[0].reshape(S, NP, NP)
        PB = self.g.profit[1].reshape(S, NP, NP)
        pA = np.full((S, NP), 1.0 / NP); pB = pA.copy()
        for _ in range(30000):
            nA = softmax(np.einsum("sab,sb->sa", PA, pB) / p.rho)
            nB = softmax(np.einsum("sab,sa->sb", PB, pA) / p.rho)
            d = max(np.abs(nA - pA).max(), np.abs(nB - pB).max())
            pA, pB = 0.1 * nA + 0.9 * pA, 0.1 * nB + 0.9 * pB
            if d < 1e-12:
                break
        fA = np.einsum("sab,sb->sa", PA, pB); fB = np.einsum("sab,sa->sb", PB, pA)
        self.WA = (p.rho * logsumexp(fA / p.rho)).reshape(self.M, self.M, self.L)
        self.WB = (p.rho * logsumexp(fB / p.rho)).reshape(self.M, self.M, self.L)
        self.pA, self.pB = pA, pB

    def solve(self, tol=1e-7, max_outer=20000, inner=500, cap_damp=0.3, vdamp=0.3, V0=None):
        p, M, L, S = self.p, self.M, self.L, self.S
        self._price_stage()
        aA, aB = self.g.adj
        V = {ph: [np.zeros((M, M, L)), np.zeros((M, M, L))] for ph in (0, 1)}
        if V0 is not None:
            V = {ph: [V0[ph][0].copy(), V0[ph][1].copy()] for ph in (0, 1)}
        k = {ph: [np.full((S, 3), 1 / 3), np.full((S, 3), 1 / 3)] for ph in (0, 1)}
        for it in range(max_outer):
            err = 0.0
            newV = {}
            for ph in (0, 1):
                nxt = 1 - ph
                actA, actB = self.active[ph]
                CA = self.g.cont(V[nxt][0]).reshape(S, 3, 3)           # beta * E V_A(next), index (kA, kB)
                CB = self.g.cont(V[nxt][1]).reshape(S, 3, 3)
                maskA = np.array([0.0, 0.0, 0.0]) if actA else np.array([0.0, NEG, NEG])
                maskB = np.array([0.0, 0.0, 0.0]) if actB else np.array([0.0, NEG, NEG])
                kA, kB = k[ph]
                for _ in range(inner):
                    gA = -aA[None, :] + (CA @ kB[:, :, None])[:, :, 0] + maskA[None, :]
                    gB = -aB[None, :] + (kA[:, None, :] @ CB)[:, 0, :] + maskB[None, :]
                    nA, nB = softmax(gA / p.rho), softmax(gB / p.rho)
                    d = max(np.abs(nA - kA).max(), np.abs(nB - kB).max())
                    kA, kB = cap_damp * nA + (1 - cap_damp) * kA, cap_damp * nB + (1 - cap_damp) * kB
                    if d < 1e-10:
                        break
                k[ph] = [kA, kB]
                gA = -aA[None, :] + (CA @ kB[:, :, None])[:, :, 0]
                gB = -aB[None, :] + (kA[:, None, :] @ CB)[:, 0, :]
                vA = (self.WA + (p.rho * (logsumexp((gA + maskA) / p.rho) + EULER)).reshape(M, M, L) if actA
                      else self.WA + gA[:, 0].reshape(M, M, L))
                vB = (self.WB + (p.rho * (logsumexp((gB + maskB) / p.rho) + EULER)).reshape(M, M, L) if actB
                      else self.WB + gB[:, 0].reshape(M, M, L))
                newV[ph] = [vA, vB]
                err = max(err, np.abs(vA - V[ph][0]).max(), np.abs(vB - V[ph][1]).max())
            for ph in (0, 1):
                for i in (0, 1):
                    V[ph][i] = V[ph][i] + vdamp * (newV[ph][i] - V[ph][i])
            if err < tol:
                break
        self.V, self.k = V, k
        self.converged, self.iters = bool(err < tol), it + 1
        return self

    # ---- ergodic statistics -------------------------------------------------------------
    def summary(self):
        p, M, L, S, NP = self.p, self.M, self.L, self.S, self.NP
        nm = self.g.nm
        idx = lambda a, b, l: (a * M + b) * L + l
        T = np.zeros((2 * S, 2 * S))
        for ph in (0, 1):
            kA, kB = self.k[ph]
            for a in range(M):
                for b in range(M):
                    for l in range(L):
                        s = idx(a, b, l)
                        for ka in range(3):
                            for kb in range(3):
                                w = kA[s, ka] * kB[s, kb]
                                if w < 1e-14:
                                    continue
                                for l2 in range(L):
                                    T[ph * S + s, (1 - ph) * S + idx(nm[a, ka], nm[b, kb], l2)] += w * self.g.P[l, l2]
        pi = np.full(2 * S, 1.0 / (2 * S))
        for _ in range(200000):
            nx = pi @ T
            if np.abs(nx - pi).max() < 1e-13:
                pi = nx
                break
            pi = nx
        pi = pi.reshape(2, M, M, L)
        pr = np.array(p.prices)
        qA, qB = self.g.q
        jp = (self.pA.reshape(M, M, L, NP)[..., :, None] * self.pB.reshape(M, M, L, NP)[..., None, :])
        E = lambda x: (jp * x).sum((3, 4))                                    # expectation over simultaneous prices
        pa, pb = pr[None, None, None, :, None], pr[None, None, None, None, :]
        rev = E(pa * qA + pb * qB); served = E(qA + qB)
        profA = E(self.g.profit[0]); profB = E(self.g.profit[1])
        aA, aB = self.g.adj
        res = dict(rev=0.0, served=0.0, profit=0.0, cap=0.0, excess=0.0, nA=0.0, nB=0.0)
        mA = np.arange(M)[:, None, None]; mB = np.arange(M)[None, :, None]
        D = np.array(p.lam)[None, None, :]
        for ph in (0, 1):
            kA = self.k[ph][0].reshape(M, M, L, 3); kB = self.k[ph][1].reshape(M, M, L, 3)
            w = pi[ph]
            res["rev"] += (w * rev).sum(); res["served"] += (w * served).sum()
            res["profit"] += (w * (profA + profB - (kA * aA).sum(-1) - (kB * aB).sum(-1))).sum()
            cap = p.kappa * (mA + mB)
            res["cap"] += (w * cap).sum(); res["excess"] += (w * np.maximum(cap - D, 0)).sum()
            res["nA"] += (w * mA).sum(); res["nB"] += (w * mB).sum()
        return dict(avg_price=res["rev"] / res["served"], profit_total=res["profit"],
                    consumer_surplus=p.prices[-1] * res["served"] - res["rev"], mean_capacity=res["cap"],
                    excess_capacity=res["excess"], mean_nodes_A=res["nA"], mean_nodes_B=res["nB"],
                    converged=self.converged, iterations=self.iters)


KEYS = ("avg_price", "profit_total", "consumer_surplus", "mean_capacity", "excess_capacity", "mean_nodes_A", "mean_nodes_B")


def run_design(item):
    name, p, design, start = item
    M, L, NP = p.M, len(p.lam), len(p.prices)
    rng = np.random.default_rng(900 + start)
    if design == "C0":
        S = M * M * L
        kw = dict(init_k=(rng.dirichlet(np.ones(3), S), rng.dirichlet(np.ones(3), S)),
                  init_V=(rng.uniform(0, 150, (M, M, L)), rng.uniform(0, 150, (M, M, L)))) if start else {}
        g = Game(p).solve_decoupled(**kw)
        s = g.summary()
    elif design in ("C1", "C1s"):
        V0 = {ph: [rng.uniform(0, 150, (M, M, L)), rng.uniform(0, 150, (M, M, L))] for ph in (0, 1)} if start else None
        g = PhaseGame(p, "staggered" if design == "C1" else "sync").solve(V0=V0)
        s = g.summary()
    else:  # C2: alternating committed prices
        V0 = {q: {i: rng.uniform(0, 150, (M, M, L, NP)) for i in (0, 1)} for q in (0, 1)} if start else None
        g = AltGame(p).solve(tol=1e-9, vdamp=0.5, max_iter=30000, V0=V0)
        s = g.summary()
    return dict(scenario=name, design=design, start=start, converged=bool(g.converged), **{k: float(s[k]) for k in KEYS})


if __name__ == "__main__":
    prices = tuple(np.round(np.linspace(0.4, 1.5, 8), 4))
    base = replace(Params(), prices=prices, rho=2.0)
    scenarios = {"base (rho=2)": base, "rho=3": replace(base, rho=3.0), "mc=0.4": replace(base, mc=0.4),
                 "fc x2": replace(base, fc=(24.0, 30.0)), "demand iid": replace(base, P_lam=((1 / 3,) * 3,) * 3),
                 "beta=0.9": replace(base, beta=0.9)}
    tasks = [(n, p, d, s) for n, p in scenarios.items() for d in ("C0", "C1", "C1s", "C2") for s in (0, 1, 2)]
    with Pool(4) as pool:
        out = pool.map(run_design, tasks, chunksize=1)
    json.dump(out, open(os.path.join(HERE, "results", "timing_experiment.json"), "w"), indent=1)
    import collections
    by = collections.OrderedDict()
    for r in out:
        by.setdefault((r["scenario"], r["design"]), []).append(r)
    for (sc, d), rs in by.items():
        cap = [r["mean_capacity"] for r in rs]; pr = [r["avg_price"] for r in rs]; cv = all(r["converged"] for r in rs)
        print(f"{sc:14s} {d:4s} cap {min(cap):5.1f}-{max(cap):5.1f}  price {min(pr):.3f}-{max(pr):.3f}  conv={cv}")
