"""Dynamic price competition with alternating moves (Maskin-Tirole 1988) and capacity.

Prices are now state variables.  In each period exactly one firm moves (A, B, A, B, ...).
The mover chooses a new price and a capacity action; the price then stays in force until
that firm moves again, two periods later.  Both firms earn flow profit every period from the
prices in force, with the same capacity-constrained Bertrand allocation as in bertrand_mpe.py.

State seen by the mover q:  (m_A, m_B, lambda, p_rival)  -- the mover's own old price is
payoff-irrelevant because it is re-chosen.  The mover's choices carry additive Type-I
extreme-value shocks of scale rho (logit MPE); rho -> 0 approaches a pure-strategy MPE.

python alternating.py            # base run + comparison with simultaneous-move pricing
"""
import argparse
import json
import os
from dataclasses import replace

import numpy as np

from bertrand_mpe import EULER, Game, Params, logsumexp, softmax

HERE = os.path.dirname(os.path.abspath(__file__))


class AltGame:
    def __init__(self, p: Params, k_allowed=(0, 1, 2)):
        self.p = p
        g = Game(p)                       # reuse allocation, profits, adjustment costs, transitions
        self.g = g
        self.M, self.L, self.NP = p.M, len(p.lam), len(p.prices)
        self.nm, self.P = g.nm, g.P
        self.profit = g.profit            # (profit_A, profit_B), each (M, M, L, pa, pb), net of holding cost
        self.adj = g.adj
        self.ks = list(k_allowed)
        self.NK = len(self.ks)
        self.NA = self.NP * self.NK       # actions of the mover: (price, capacity action)

    # ---- one Bellman sweep ----------------------------------------------------------
    def _tensors(self, V, mover):
        """Per-action values for the mover; returns (v_mover, v_other), each (M, M, L, NPrival, NA)."""
        p, M, L, NP, NK = self.p, self.M, self.L, self.NP, self.NK
        ks = np.array(self.ks)
        P = self.P
        # expected continuation over next demand regime: E[q'][i][m_A, m_B, l, rival_price]
        E = {(q, i): np.einsum("lx,abxp->ablp", P, V[q][i]) for q in (0, 1) for i in (0, 1)}
        l_idx = np.arange(L)[None, None, :, None, None, None]
        mA_idx = np.arange(M)[:, None, None, None, None, None]
        mB_idx = np.arange(M)[None, :, None, None, None, None]
        pr_idx = np.arange(NP)
        out = []
        if mover == 0:                    # A moves; rival price = p_B; next mover is B whose rival price is A's new price
            A_next = self.nm[:, ks][:, None, None, None, None, :]            # (M,1,1,1,1,NK)
            flow = [self.profit[0].transpose(0, 1, 2, 4, 3)[..., None],       # (M,M,L,pB,pa,1)
                    self.profit[1].transpose(0, 1, 2, 4, 3)[..., None]]
            adj = (self.adj[0][ks])[None, None, None, None, None, :]
            nxt = lambda i: self.p.beta * E[(1, i)][A_next, mB_idx, l_idx, pr_idx[None, None, None, None, :, None]]
            vm = flow[0] - adj + nxt(0)
            vo = flow[1] + nxt(1)
        else:                             # B moves; rival price = p_A; next mover is A whose rival price is B's new price
            B_next = self.nm[:, ks][None, :, None, None, None, :]            # (1,M,1,1,1,NK)
            flow = [self.profit[0][..., None], self.profit[1][..., None]]    # (M,M,L,pA,pb,1)
            adj = (self.adj[1][ks])[None, None, None, None, None, :]
            nxt = lambda i: self.p.beta * E[(0, i)][mA_idx, B_next, l_idx, pr_idx[None, None, None, None, :, None]]
            vm = flow[1] - adj + nxt(1)
            vo = flow[0] + nxt(0)
        sh = (M, M, L, NP, NP * NK)
        return vm.reshape(sh), vo.reshape(sh)

    def solve(self, tol=1e-6, max_iter=20000, vdamp=1.0, verbose=False, V0=None, rho=None):
        p, M, L, NP = self.p, self.M, self.L, self.NP
        rho = p.rho if rho is None else rho
        V = {q: {i: np.zeros((M, M, L, NP)) for i in (0, 1)} for q in (0, 1)} if V0 is None else {q: {i: V0[q][i].copy() for i in (0, 1)} for q in (0, 1)}
        sigma = {}
        for it in range(max_iter):
            new = {q: {} for q in (0, 1)}
            for q in (0, 1):
                vm, vo = self._tensors(V, q)
                s = softmax(vm / rho)
                sigma[q] = s
                new[q][q] = rho * (logsumexp(vm / rho) + EULER)
                new[q][1 - q] = (s * vo).sum(-1)
            err = max(np.abs(new[q][i] - V[q][i]).max() for q in (0, 1) for i in (0, 1))
            for q in (0, 1):
                for i in (0, 1):
                    V[q][i] = V[q][i] + vdamp * (new[q][i] - V[q][i])
            if verbose and it % 200 == 0:
                print(f"  iter {it:5d} |dV|={err:.3e}")
            if err < tol:
                break
        self.V, self.sigma = V, sigma
        self.converged, self.iters = bool(err < tol), it + 1
        return self

    # ---- Newton solver with continuation in rho ---------------------------------------
    def _pack(self, V):
        return np.concatenate([V[q][i].ravel() for q in (0, 1) for i in (0, 1)])

    def _unpack(self, x):
        n = self.M * self.M * self.L * self.NP
        V = {q: {} for q in (0, 1)}
        for k, (q, i) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            V[q][i] = x[k * n:(k + 1) * n].reshape(self.M, self.M, self.L, self.NP)
        return V

    def _phi(self, x, rho):
        V = self._unpack(x)
        new = {q: {} for q in (0, 1)}
        for q in (0, 1):
            vm, vo = self._tensors(V, q)
            s = softmax(vm / rho)
            new[q][q] = rho * (logsumexp(vm / rho) + EULER)
            new[q][1 - q] = (s * vo).sum(-1)
        return self._pack(new)

    def solve_newton(self, rho, x0, tol=1e-9, max_iter=40, eps=1e-6, verbose=False):
        x = x0.copy()
        n = len(x)
        for it in range(max_iter):
            F = self._phi(x, rho) - x
            nrm = np.abs(F).max()
            if verbose:
                print(f"    newton {it} |F|={nrm:.2e}", flush=True)
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
            while t > 1e-4:                              # backtracking line search on the residual norm
                if np.abs(self._phi(x + t * dx, rho) - (x + t * dx)).max() < nrm * (1 - 1e-4 * t):
                    break
                t /= 2
            x = x + t * dx
        F = self._phi(x, rho) - x
        return x, bool(np.abs(F).max() < tol)

    def solve_path(self, rhos, x0=None, verbose=False, tol=1e-9):
        """Continuation in rho: value iteration at the first (large) rho, Newton afterwards."""
        if x0 is None:
            self.solve(tol=1e-9, vdamp=0.5, max_iter=20000, rho=rhos[0])
            x = self._pack(self.V)
            if not self.converged:
                return self
        else:
            x = x0
        for r in rhos[1:]:
            x_new, ok = self.solve_newton(r, x, tol=tol)
            if verbose:
                print(f"  rho={r:<6} newton converged={ok}", flush=True)
            if not ok:
                self.converged, self.rho_reached = False, r
                self.V = self._unpack(x)
                return self
            x = x_new
        self.V = self._unpack(x)
        rho = rhos[-1]
        vo = {}
        for q in (0, 1):
            vm, _ = self._tensors(self.V, q)
            vo[q] = softmax(vm / rho)
        self.sigma = vo
        self.converged, self.iters, self.rho_reached = True, 0, rho
        self.p = replace(self.p, rho=rho)
        return self

    def solve_homotopy(self, rhos, tol=1e-8, vdamp=0.5, max_iter=20000, verbose=False):
        """Track the logit equilibrium from a large rho (unique, easy) down to p.rho."""
        V0 = None
        for r in rhos:
            self.solve(tol=tol, max_iter=max_iter, vdamp=vdamp, V0=V0, rho=r)
            if verbose:
                print(f"  rho={r:<5} converged={self.converged} iters={self.iters}", flush=True)
            if not self.converged:
                return self
            V0 = self.V
        return self

    # ---- ergodic distribution and statistics -----------------------------------------
    def stationary(self):
        p, M, L, NP, NK = self.p, self.M, self.L, self.NP, self.NK
        ks = np.array(self.ks)
        S1 = M * M * L * NP
        idx = lambda a, b, l, r: ((a * M + b) * L + l) * NP + r
        T = np.zeros((2 * S1, 2 * S1))
        for q in (0, 1):
            s = self.sigma[q].reshape(M, M, L, NP, NP, NK)               # (.., price, capacity)
            for a in range(M):
                for b in range(M):
                    for l in range(L):
                        for r in range(NP):
                            row = q * S1 + idx(a, b, l, r)
                            for pr in range(NP):
                                for kk in range(NK):
                                    w = s[a, b, l, r, pr, kk]
                                    if w < 1e-14:
                                        continue
                                    k = ks[kk]
                                    a2, b2 = (self.nm[a, k], b) if q == 0 else (a, self.nm[b, k])
                                    for l2 in range(L):
                                        T[row, (1 - q) * S1 + idx(a2, b2, l2, pr)] += w * self.P[l, l2]
        pi = np.full(2 * S1, 1.0 / (2 * S1))
        for _ in range(200000):
            nx = pi @ T
            if np.abs(nx - pi).max() < 1e-13:
                pi = nx
                break
            pi = nx
        return pi.reshape(2, M, M, L, NP)

    def summary(self):
        p, M, L, NP, NK = self.p, self.M, self.L, self.NP, self.NK
        ks = np.array(self.ks)
        pi = self.stationary()
        pr = np.array(p.prices)
        qA, qB = self.g.q
        out = dict(pA=0.0, rev=0.0, served=0.0, profA=0.0, profB=0.0, rej=0.0, cap=0.0, excess=0.0,
                   nA=0.0, nB=0.0, p_at_ceiling=0.0, mean_price_charged=0.0, jump_up=0.0, undercut=0.0)
        mA = np.arange(M)[:, None, None]
        mB = np.arange(M)[None, :, None]
        D = np.array(p.lam)[None, None, :]
        for q in (0, 1):
            s = self.sigma[q].reshape(M, M, L, NP, NP, NK)
            w = pi[q][..., None, None] * s                               # (M,M,L,rival,price,k)
            wp = w.sum(-1)                                               # (M,M,L,rival,price)
            if q == 0:                                                   # prices (pa = new, pB = rival)
                qa = qA.transpose(0, 1, 2, 4, 3); qb = qB.transpose(0, 1, 2, 4, 3)
                ra = self.g.rej[0].transpose(0, 1, 2, 4, 3); rb = self.g.rej[1].transpose(0, 1, 2, 4, 3)
                pa = pr[None, None, None, None, :]; pb = pr[None, None, None, :, None]
                ha = (self.adj[0][ks][None, None, None, None, None, :] * w).sum()
                hb = 0.0
                mover_price = pa; rival_price = pb
            else:
                qa, qb = qA, qB; ra, rb = self.g.rej
                pa = pr[None, None, None, :, None]; pb = pr[None, None, None, None, :]
                ha = 0.0
                hb = (self.adj[1][ks][None, None, None, None, None, :] * w).sum()
                mover_price = pb; rival_price = pa
            out["served"] += (wp * (qa + qb)).sum()
            out["rev"] += (wp * (pa * qa + pb * qb)).sum()
            out["profA"] += (wp * ((pa - p.mc) * qa - p.sla * ra - p.pk * mA[..., None, None])).sum() - ha
            out["profB"] += (wp * ((pb - p.mc) * qb - p.sla * rb - p.pk * mB[..., None, None])).sum() - hb
            out["rej"] += (wp * (ra + rb)).sum()
            out["jump_up"] += (wp * (mover_price > rival_price + 1e-9)).sum()      # mover prices above the rival
            out["undercut"] += (wp * (mover_price < rival_price - 1e-9)).sum()
            out["p_at_ceiling"] += (wp * (np.isclose(mover_price, pr[-1]))).sum()
            out["mean_price_charged"] += (wp * mover_price).sum()
        pis = pi.sum(0)                                                  # marginal over mover
        cap = p.kappa * (mA + mB)
        out["cap"] = float((pis.sum(-1) * cap).sum())
        out["excess"] = float((pis.sum(-1) * np.maximum(cap - D, 0)).sum())
        out["nA"] = float((pis.sum(-1) * mA).sum()); out["nB"] = float((pis.sum(-1) * mB).sum())
        res = dict(avg_price=out["rev"] / out["served"], served=out["served"], profit_A=out["profA"], profit_B=out["profB"],
                   profit_total=out["profA"] + out["profB"],
                   consumer_surplus=p.prices[-1] * out["served"] - out["rev"], mean_capacity=out["cap"], excess_capacity=out["excess"],
                   mean_nodes_A=out["nA"], mean_nodes_B=out["nB"], rejected=out["rej"],
                   share_moves_at_ceiling=out["p_at_ceiling"], share_moves_above_rival=out["jump_up"], share_moves_below_rival=out["undercut"],
                   converged=self.converged, iterations=self.iters)
        return res

    # ---- reaction function and cycles at fixed capacities --------------------------------
    def reaction(self, mA, mB, l, mover):
        """Mover's price distribution as a function of the rival's committed price, at one state."""
        s = self.sigma[mover][mA, mB, l].reshape(self.NP, self.NP, self.NK).sum(-1)   # (rival, price)
        return s

    def best_response_cycle(self, mA, mB, l, start_price_idx=0, first_mover=0, n=40):
        """Iterate the modal reaction at a fixed state (capacity and demand frozen); returns price path."""
        path, rival, mover = [], start_price_idx, first_mover
        for _ in range(n):
            r = self.reaction(mA, mB, l, mover)[rival]
            pnew = int(r.argmax())
            path.append((mover, self.p.prices[pnew]))
            rival, mover = pnew, 1 - mover
        return path


def run(p, label, k_allowed=(0, 1, 2), verbose=False, **kw):
    g = AltGame(p, k_allowed).solve(verbose=verbose, **kw)
    return g, g.summary()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rho", type=float, default=0.3)
    ap.add_argument("--nprices", type=int, default=8)
    a = ap.parse_args()
    prices = tuple(np.round(np.linspace(0.4, 1.5, a.nprices), 4))
    p = replace(Params(), prices=prices, rho=a.rho)
    g, sm = run(p, "alternating", verbose=True)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in sm.items()})


if __name__ == "__main__":
    main()
