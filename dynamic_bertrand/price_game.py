"""Alternating-move price competition at fixed capacities (Maskin-Tirole 1988 with capacity constraints).

Capacities (m_A, m_B) are held fixed, so the game is purely about prices, which are state variables:
the mover's rival price is the state.  Demand regime lambda follows the Markov chain of the main model.
The logit equilibrium is tracked from a large noise scale rho down to a small one with Newton
continuation, because plain value iteration cycles for small rho.

python price_game.py            # writes results/price_game.json and figures
"""
import json
import os
from dataclasses import replace

import numpy as np

from bertrand_mpe import EULER, Game, Params, logsumexp, softmax

HERE = os.path.dirname(os.path.abspath(__file__))


class PriceGame:
    def __init__(self, p: Params, mA: int, mB: int):
        self.p, self.mA, self.mB = p, mA, mB
        g = Game(p)
        self.g = g
        self.L, self.NP = len(p.lam), len(p.prices)
        self.P = g.P
        # flows for the two movers, indexed (l, rival_price, own_price)
        pa_ = g.profit[0][mA, mB]              # (l, pa, pb)
        pb_ = g.profit[1][mA, mB]
        self.flow = {0: (pa_.transpose(0, 2, 1), pb_.transpose(0, 2, 1)),   # A moves: rival = pB, own = pa
                     1: (pa_, pb_)}                                         # B moves: rival = pA, own = pb
        self.qa, self.qb = g.q[0][mA, mB], g.q[1][mA, mB]
        self.ra, self.rb = g.rej[0][mA, mB], g.rej[1][mA, mB]

    def _phi(self, x, rho):
        L, NP, P, b = self.L, self.NP, self.P, self.p.beta
        n = L * NP
        V = {(q, i): x[(2 * q + i) * n:(2 * q + i + 1) * n].reshape(L, NP) for q in (0, 1) for i in (0, 1)}
        E = {k: P @ v for k, v in V.items()}                      # expected next-period value, (l, rival price)
        out = np.empty_like(x)
        for q in (0, 1):
            fa, fb = self.flow[q]                                 # (l, rival, own)
            nxt = 1 - q
            cm = b * E[(nxt, q)][:, None, :]                      # next state: other moves, its rival price = my new price
            co = b * E[(nxt, 1 - q)][:, None, :]
            fm, fo = (fa, fb) if q == 0 else (fb, fa)
            vm, vo = fm + cm, fo + co
            s = softmax(vm / rho)
            out[(2 * q + q) * n:(2 * q + q + 1) * n] = (rho * (logsumexp(vm / rho) + EULER)).ravel()
            out[(2 * q + 1 - q) * n:(2 * q + 2 - q) * n] = (s * vo).sum(-1).ravel()
        return out

    def _sigma(self, x, rho):
        L, NP, b = self.L, self.NP, self.p.beta
        n = L * NP
        V = {(q, i): x[(2 * q + i) * n:(2 * q + i + 1) * n].reshape(L, NP) for q in (0, 1) for i in (0, 1)}
        E = {k: self.P @ v for k, v in V.items()}
        sig = {}
        for q in (0, 1):
            fa, fb = self.flow[q]
            fm = fa if q == 0 else fb
            sig[q] = softmax((fm + b * E[(1 - q, q)][:, None, :]) / rho)   # (l, rival, own price)
        return sig

    def newton(self, rho, x, tol=1e-11, max_iter=60, eps=1e-7):
        n = len(x)
        for _ in range(max_iter):
            F = self._phi(x, rho) - x
            nrm = np.abs(F).max()
            if nrm < tol:
                return x, True
            J = np.empty((n, n))
            for j in range(n):
                xe = x.copy(); xe[j] += eps
                J[:, j] = (self._phi(xe, rho) - xe - F) / eps
            try:
                dx = np.linalg.solve(J, -F)
            except np.linalg.LinAlgError:
                return x, False
            t = 1.0
            while t > 1e-5:
                if np.abs(self._phi(x + t * dx, rho) - (x + t * dx)).max() < nrm * (1 - 1e-4 * t):
                    break
                t /= 2
            x = x + t * dx
        return x, bool(np.abs(self._phi(x, rho) - x).max() < tol)

    def solve(self, rho_target, rho_start=4.0, steps=14):
        """Value iteration at rho_start, then Newton continuation (with step bisection) to rho_target."""
        n = 4 * self.L * self.NP
        x = np.zeros(n)
        for _ in range(20000):                                    # damped value iteration at large rho
            nx = x + 0.5 * (self._phi(x, rho_start) - x)
            if np.abs(nx - x).max() < 1e-11:
                x = nx
                break
            x = nx
        rhos = list(np.geomspace(rho_start, rho_target, steps + 1))[1:]
        cur = rho_start
        stack = rhos[::-1]
        while stack:
            r = stack.pop()
            x_new, ok = self.newton(r, x)
            if ok:
                x, cur = x_new, r
            else:
                if abs(np.log(r / cur)) < 1e-3:
                    self.ok, self.rho = False, cur
                    self.x = x
                    return self
                stack.append(r)
                stack.append(float(np.sqrt(r * cur)))
        self.x, self.rho, self.ok = x, cur, True
        self.sigma = self._sigma(x, cur)
        return self

    # ---- statistics -------------------------------------------------------------------
    def stationary(self):
        L, NP = self.L, self.NP
        S1 = L * NP
        T = np.zeros((2 * S1, 2 * S1))
        for q in (0, 1):
            s = self.sigma[q]                                    # (l, rival, own)
            for l in range(L):
                for r in range(NP):
                    for o in range(NP):
                        w = s[l, r, o]
                        for l2 in range(L):
                            T[q * S1 + l * NP + r, (1 - q) * S1 + l2 * NP + o] += w * self.P[l, l2]
        pi = np.full(2 * S1, 1.0 / (2 * S1))
        for _ in range(200000):
            nx = pi @ T
            if np.abs(nx - pi).max() < 1e-13:
                pi = nx
                break
            pi = nx
        return pi.reshape(2, L, NP)

    def stats(self):
        p = self.p
        pr = np.array(p.prices)
        pi = self.stationary()
        tot = dict(rev=0.0, q=0.0, pA=0.0, pB=0.0, ceil=0.0, below=0.0, above=0.0, eq=0.0, price=0.0)
        by_l = np.zeros((self.L, 2))                              # revenue, served by regime
        for q in (0, 1):
            w = pi[q][:, :, None] * self.sigma[q]                 # (l, rival, own)
            if q == 0:                                            # own = pa, rival = pb
                pa, pb = pr[None, None, :], pr[None, :, None]
                qa, qb = self.qa.transpose(0, 2, 1), self.qb.transpose(0, 2, 1)
                ra, rb = self.ra.transpose(0, 2, 1), self.rb.transpose(0, 2, 1)
                own, riv = pa, pb
            else:
                pa, pb = pr[None, :, None], pr[None, None, :]
                qa, qb, ra, rb = self.qa, self.qb, self.ra, self.rb
                own, riv = pb, pa
            rev = pa * qa + pb * qb
            tot["rev"] += (w * rev).sum(); tot["q"] += (w * (qa + qb)).sum()
            tot["pA"] += (w * ((pa - p.mc) * qa - p.sla * ra)).sum()
            tot["pB"] += (w * ((pb - p.mc) * qb - p.sla * rb)).sum()
            tot["ceil"] += (w * np.isclose(own, pr[-1])).sum()
            tot["below"] += (w * (own < riv - 1e-9)).sum(); tot["above"] += (w * (own > riv + 1e-9)).sum()
            tot["eq"] += (w * np.isclose(own, riv)).sum(); tot["price"] += (w * own).sum()
            by_l[:, 0] += (w * rev).sum((1, 2)); by_l[:, 1] += (w * (qa + qb)).sum((1, 2))
        hold = p.pk * (self.mA + self.mB)
        return dict(avg_price=tot["rev"] / tot["q"], served=tot["q"],
                    profit_total=tot["pA"] + tot["pB"] - hold, profit_A=tot["pA"] - p.pk * self.mA, profit_B=tot["pB"] - p.pk * self.mB,
                    consumer_surplus=p.prices[-1] * tot["q"] - tot["rev"],
                    share_at_ceiling=tot["ceil"], share_undercut=tot["below"], share_above_rival=tot["above"], share_match=tot["eq"],
                    avg_price_by_regime=(by_l[:, 0] / np.maximum(by_l[:, 1], 1e-12)).tolist(), rho=self.rho)

    def modal_path(self, l, start=0, first=0, n=24):
        path, rival, mover = [], start, first
        for _ in range(n):
            o = int(self.sigma[mover][l, rival].argmax())
            path.append((mover, float(self.p.prices[o])))
            rival, mover = o, 1 - mover
        return path


def static_benchmark(p: Params, mA, mB):
    """Simultaneous-move logit pricing game at the same capacities, same rho, same demand chain."""
    g = Game(p)
    L, NP = len(p.lam), len(p.prices)
    pa_, pb_ = g.profit[0][mA, mB], g.profit[1][mA, mB]
    out = {}
    # stationary distribution over lambda only (prices are re-chosen every period)
    P = np.array(p.P_lam)
    w, v = np.linalg.eig(P.T); pi = np.real(v[:, np.argmin(abs(w - 1))]); pi /= pi.sum()
    rev = q = pA = pB = 0.0
    avg = []
    pr = np.array(p.prices)
    for l in range(L):
        sA = np.full(NP, 1 / NP); sB = sA.copy()
        for _ in range(100000):
            nA = softmax(pa_[l] @ sB / p.rho); nB = softmax(pb_[l].T @ sA / p.rho)
            d = max(abs(nA - sA).max(), abs(nB - sB).max())
            sA, sB = 0.1 * nA + 0.9 * sA, 0.1 * nB + 0.9 * sB
            if d < 1e-13:
                break
        jp = sA[:, None] * sB[None, :]
        qa, qb = g.q[0][mA, mB, l], g.q[1][mA, mB, l]
        ra, rb = g.rej[0][mA, mB, l], g.rej[1][mA, mB, l]
        r_l = (jp * (pr[:, None] * qa + pr[None, :] * qb)).sum(); q_l = (jp * (qa + qb)).sum()
        rev += pi[l] * r_l; q += pi[l] * q_l
        pA += pi[l] * (jp * ((pr[:, None] - p.mc) * qa - p.sla * ra)).sum()
        pB += pi[l] * (jp * ((pr[None, :] - p.mc) * qb - p.sla * rb)).sum()
        avg.append(r_l / max(q_l, 1e-12))
    hold = p.pk * (mA + mB)
    return dict(avg_price=rev / q, profit_total=pA + pB - hold, consumer_surplus=p.prices[-1] * q - rev,
                avg_price_by_regime=avg, served=q)


def main():
    nprices = 8
    prices = tuple(np.round(np.linspace(0.4, 1.5, nprices), 4))
    base = replace(Params(), prices=prices)
    caps = [(1, 1), (2, 2), (3, 3), (4, 4), (1, 3)]
    rhos = [1.0, 0.3, 0.1]
    res = {"prices": list(prices), "cases": []}
    for (a, b) in caps:
        for rho in rhos:
            p = replace(base, rho=rho)
            g = PriceGame(p, a, b).solve(rho)
            entry = {"mA": a, "mB": b, "rho_target": rho, "rho_reached": float(g.rho), "converged": bool(g.ok)}
            if g.ok:
                entry["alt"] = g.stats()
                entry["paths"] = {int(l): g.modal_path(l) for l in range(len(p.lam))}
                entry["reaction"] = {int(l): g.sigma[0][l].tolist() for l in range(len(p.lam))}
                entry["static"] = static_benchmark(p, a, b)
            res["cases"].append(entry)
            print(a, b, rho, g.ok, round(float(g.rho), 3),
                  (round(entry["alt"]["avg_price"], 3), round(entry["static"]["avg_price"], 3)) if g.ok else "", flush=True)
    json.dump(res, open(os.path.join(HERE, "results", "price_game.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
