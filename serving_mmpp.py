"""Poisson vs. bursty (MMPP) arrivals in LLM inference serving.

Exact CTMC analysis of an MMPP(2)/M/c queue (c = number of GPU replicas, each serving one
request at rate mu) and of Poisson M/M/c with the same mean rate.  Four experiments:

  E1  mean delay and tail P(wait > tau) at equal utilisation        (Poisson is the null)
  E2  replicas needed to meet a delay SLO                           (Erlang-C sizing error)
  E3  congestion externality: average vs. state-dependent toll      (Vickrey-style pricing)
  E4  welfare loss of flat per-token pricing vs. burst-aware pricing under elastic demand

Run:  python serving_mmpp.py            (numpy only, ~1-2 minutes)
"""
import json
import math
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

MU = 1.0  # service rate per replica: time is measured in mean service times


# ----------------------------------------------------------------------------- CTMC core
class MMPPQueue:
    """MMPP(2)/M/c.  phases: 0 = H (burst), 1 = L.  State index i = 2*n + s, n = 0..N."""

    def __init__(self, lam, rates, c, N=None):
        # lam = (lam_H, lam_L); rates = (r_HL, r_LH); equal lam => plain Poisson
        self.lam = np.asarray(lam, float)
        self.r = np.asarray(rates, float)
        self.c = c
        self.piS = np.array([self.r[1], self.r[0]]) / self.r.sum()  # (pi_H, pi_L)
        self.lbar = float(self.piS @ self.lam)
        rho = self.lbar / (c * MU)
        if rho >= 1:
            raise ValueError("unstable")
        N = N or self._pick_N(rho)
        while True:
            self._build(N)
            if self.pi[-2:].sum() < 1e-9 or N > 4000:
                break
            N *= 2
        self.N = N

    def _pick_N(self, rho):
        burst = max(0.0, (self.lam.max() - self.c * MU)) / max(self.r.min(), 1e-9)
        return int(min(3000, 60 + 12 * self.c + 8 / (1 - rho) + 2 * burst))

    def _build(self, N):
        c, lam, r = self.c, self.lam, self.r
        M = 2 * (N + 1)
        n = np.repeat(np.arange(N + 1), 2)
        ph = np.tile([0, 1], N + 1)
        i = np.arange(M)
        up = n < N
        dn = n > 0
        rows = np.concatenate([i[up], i[dn], i])
        cols = np.concatenate([i[up] + 2, i[dn] - 2, 2 * n + (1 - ph)])
        vals = np.concatenate([lam[ph[up]], np.minimum(n[dn], c) * MU, r[ph]])
        Q = sp.csr_matrix((vals, (rows, cols)), shape=(M, M))
        Q = Q - sp.diags(np.asarray(Q.sum(axis=1)).ravel())
        self.Q = Q.tocsr()
        A = sp.lil_matrix(self.Q.T)
        A[M - 1, :] = 1.0
        b = np.zeros(M)
        b[-1] = 1.0
        self.pi = spl.spsolve(A.tocsc(), b)

    # -- performance measures
    def n_dist(self):
        return self.pi.reshape(-1, 2)  # [n, s]

    def mean_L(self):
        P = self.n_dist()
        return float((np.arange(P.shape[0])[:, None] * P).sum())

    def mean_W(self):  # sojourn time via Little's law
        return self.mean_L() / self.lbar

    def wait_tail(self, tau):
        """P(queueing delay > tau) for an arriving request (FCFS, exact).
        Arrivals see (s,n) with probability proportional to lam_s * pi(s,n) (not PASTA)."""
        P = self.n_dist()
        w = P * self.lam[None, :]
        w = w / w.sum()
        tot = 0.0
        for n in range(self.c, P.shape[0]):
            k = n - self.c + 1  # must wait for k departures at rate c*mu
            tot += w[n].sum() * erlang_sf(k, self.c * MU, tau)
        return tot

    def mean_wait_q(self):
        P = self.n_dist()
        w = P * self.lam[None, :]
        w = w / w.sum()
        return float(sum(w[n].sum() * (n - self.c + 1) / (self.c * MU) for n in range(self.c, P.shape[0])))

    def idc(self):
        d = self.lam[0] - self.lam[1]
        return 1 + 2 * d * d * self.piS[0] * self.piS[1] / (self.r.sum() * self.lbar)


def erlang_sf(k, rate, t):
    """P(Erlang(k, rate) > t) = P(Poisson(rate*t) < k)."""
    x = rate * t
    term, s = math.exp(-x), 0.0
    for j in range(k):
        s += term
        term *= x / (j + 1)
    return min(1.0, s)


def mmpp(lbar, rho_c, kappa, TH, pH=0.2):
    """Burst process with mean lbar, burst/off ratio kappa, fraction pH of time bursting,
    mean burst length TH (in service times)."""
    lL = lbar / (pH * kappa + 1 - pH)
    lH = kappa * lL
    r_HL = 1.0 / TH
    r_LH = r_HL * pH / (1 - pH)
    return (lH, lL), (r_HL, r_LH)


# ----------------------------------------------------------------------------- experiments
def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def e1(c, tau):
    rows = []
    for rho in (0.5, 0.7, 0.8, 0.9):
        lbar = rho * c * MU
        base = MMPPQueue((lbar, lbar), (1.0, 0.25), c)
        w0, t0 = base.mean_W(), base.wait_tail(tau)
        rows.append([rho, "Poisson", 1.0, f"{w0:.2f}", "1.00", f"{t0:.4f}", "1.0"])
        for kappa, TH in ((3, 2), (3, 20), (6, 2), (6, 20), (6, 100)):
            lam, rt = mmpp(lbar, rho, kappa, TH)
            q = MMPPQueue(lam, rt, c)
            rows.append([rho, f"MMPP k={kappa},T={TH}", f"{q.idc():.1f}", f"{q.mean_W():.2f}",
                         f"{q.mean_W() / w0:.2f}", f"{q.wait_tail(tau):.4f}",
                         f"{q.wait_tail(tau) / max(t0, 1e-12):.1f}"])
    return table(rows, ["rho", "arrivals", "IDC(inf)", "E[sojourn]", "ratio vs Poisson",
                        f"P(wait>{tau})", "tail ratio"])


def min_c(lbar, tau, eps, proc):
    ok = lambda c: MMPPQueue(*proc(lbar), c).wait_tail(tau) <= eps
    lo = int(math.ceil(lbar / MU))  # infeasible (rho >= 1)
    hi = lo + 1
    while not ok(hi):
        lo, hi = hi, 2 * hi
    while hi - lo > 1:  # tail probability is monotone in c
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def e2(lbar, tau, eps):
    rows = []
    c0 = min_c(lbar, tau, eps, lambda l: ((l, l), (1.0, 0.25)))
    rows.append(["Poisson", "1.0", c0, 0, "0%"])
    for kappa, TH in ((2, 5), (3, 5), (3, 20), (6, 5), (6, 20)):
        proc = lambda l, k=kappa, T=TH: mmpp(l, None, k, T)
        c = min_c(lbar, tau, eps, proc)
        idc = MMPPQueue(*proc(lbar), c).idc()
        rows.append([f"MMPP k={kappa},T={TH}", f"{idc:.1f}", c, c - c0, f"{100 * (c - c0) / c0:.0f}%"])
    return table(rows, ["arrivals", "IDC(inf)", "replicas needed", "extra", "extra %"]), c0


def externality(q, v=1.0):
    """Pigouvian toll for an arrival in (phase s, n in system).  h solves the Poisson equation
    Q h = g - v*n  (relative cost-to-go); toll = h(s,n+1) - h(s,n) - own expected delay cost."""
    N, c = q.N, q.c
    M = q.Q.shape[0]
    f = v * np.repeat(np.arange(N + 1), 2)
    g = q.pi @ f
    A = sp.lil_matrix(q.Q)
    b = g - f
    A[M - 1, :] = q.pi
    b[-1] = 0.0
    h = spl.spsolve(A.tocsc(), b).reshape(-1, 2)
    toll = np.zeros((N, 2))
    for n in range(N):
        own = v * (1 / MU if n < c else (n - c + 1) / (c * MU) + 1 / MU)
        toll[n] = h[n + 1] - h[n] - own
    return toll


def e3(c):
    lbar = 0.8 * c * MU
    rows, prof = [], []
    base = MMPPQueue((lbar, lbar), (1.0, 0.25), c)
    tp = externality(base)
    pw = base.n_dist() * base.lam[None, :]
    pw = pw / pw.sum()
    avg_p = float((pw[:tp.shape[0]] * tp).sum())
    rho = lbar / (c * MU)
    rows.append(["Poisson", f"{avg_p:.2f}", f"{avg_p:.2f}", "-", "-"])
    for kappa, TH in ((3, 5), (3, 20), (6, 5), (6, 20)):
        lam, rt = mmpp(lbar, rho, kappa, TH)
        q = MMPPQueue(lam, rt, c)
        t = externality(q)
        w = q.n_dist() * q.lam[None, :]
        w = w / w.sum()
        avg = float((w[:t.shape[0]] * t).sum())
        # average toll by phase
        sH = float((w[:t.shape[0], 0] * t[:, 0]).sum() / w[:t.shape[0], 0].sum())
        sL = float((w[:t.shape[0], 1] * t[:, 1]).sum() / w[:t.shape[0], 1].sum())
        # cross-check with finite-difference d(v L)/d lbar - W
        eps = 1e-3
        lam2 = tuple(np.array(lam) * (1 + eps))
        q2 = MMPPQueue(lam2, rt, c)
        fd = (q2.mean_L() - q.mean_L()) / (lbar * eps) - q.mean_W()
        rows.append([f"MMPP k={kappa},T={TH}", f"{avg:.2f} (fd {fd:.2f})", f"{avg / avg_p:.1f}x",
                     f"{sH:.2f}", f"{sL:.2f}"])
    return table(rows, ["arrivals", "mean toll / arrival", "vs Poisson", "toll in burst", "toll off-burst"])


def welfare(c, Lam, pH, rt, lamS, Pbar, v=1.0):
    """Welfare rate = sum_s pi_s * B_s(lam_s) - v*L ; B_s(l) = Pbar*(l - l^2/(2 Lam_s))."""
    q = MMPPQueue(tuple(lamS), rt, c)
    piS = q.piS
    B = sum(piS[s] * Pbar * (lamS[s] - lamS[s] ** 2 / (2 * Lam[s])) for s in range(2))
    return B - v * q.mean_L()


def e4(c, kappa, TH, Pbar):
    pH = 0.2
    Lbar = 1.4 * c * MU  # unpriced demand exceeds capacity
    lam, rt = mmpp(Lbar, None, kappa, TH, pH)
    Lam = np.array(lam)
    shares = np.linspace(0.05, 0.95, 37)
    rate_from_toll = lambda tau: Lam * np.clip(1 - tau / Pbar, 0, 1)

    def feasible(l):
        return float(np.array([rt[1], rt[0]]) @ l / (rt[0] + rt[1])) < 0.995 * c * MU

    def W(l):
        return welfare(c, Lam, pH, rt, l, Pbar) if feasible(l) else -1e9

    # (a) burst-blind flat: toll set as if arrivals were Poisson with the same mean
    best, tau_b = -1e18, 0
    for tau in np.linspace(0, Pbar, 30):
        l = rate_from_toll(tau)
        m = float((np.array([rt[1], rt[0]]) / (rt[0] + rt[1])) @ l)
        if m >= 0.995 * c * MU:
            continue
        pq = MMPPQueue((m, m), (1.0, 0.25), c)
        Bm = (np.array([rt[1], rt[0]]) / (rt[0] + rt[1])) @ (Pbar * (l - l ** 2 / (2 * Lam)))
        val = Bm - pq.mean_L()
        if val > best:
            best, tau_b = val, tau
    w_blind = W(rate_from_toll(tau_b))
    # (b) best flat toll under true MMPP
    w_flat, tau_f = max((W(rate_from_toll(t)), t) for t in np.linspace(0, Pbar, 40))
    # (c) best two-price (toll depends on observed phase)
    w2, taus = -1e18, None
    for tH in np.linspace(0, Pbar, 21):
        for tL in np.linspace(0, Pbar / 2, 11):
            val = W(Lam * np.clip(1 - np.array([tH, tL]) / Pbar, 0, 1))
            if val > w2:
                w2, taus = val, (tH, tL)
    return dict(kappa=kappa, TH=TH, w_blind=w_blind, w_flat=w_flat, w_two=w2, tau_blind=tau_b,
                tau_flat=tau_f, tau_H=taus[0], tau_L=taus[1])


def main():
    out = {}
    md = ["# MMPP vs. Poisson in inference serving: numerical results\n"]
    c1, tau1 = 8, 1.0
    md += [f"## E1  Delay at equal utilisation (c={c1} replicas, mu=1; time in mean service times)\n",
           "Burst process: 20% of time in burst, rate k x off-rate, mean burst length T service times.\n", e1(c1, tau1), ""]
    lbar, tau2, eps = 10.0, 1.0, 0.01
    t2, c0 = e2(lbar, tau2, eps)
    print("\n".join(md), flush=True)
    md += [f"## E2  Replicas needed for P(wait > {tau2}) <= {eps} at mean load {lbar} (mu=1)\n", t2, ""]
    md += ["## E3  Congestion externality per request (cost unit: one service time of one user's delay), rho=0.8, c=8\n",
           e3(8), ""]
    rows = []
    for kappa, TH in ((1.0001, 5), (3, 5), (3, 20), (6, 20)):
        r = e4(4, kappa, TH, Pbar=20.0)
        out[f"E4_k{kappa}_T{TH}"] = r
        wb, wf, w2 = r["w_blind"], r["w_flat"], r["w_two"]
        rows.append([f"k={kappa:.0f},T={TH}", f"{wb:.2f}", f"{wf:.2f}", f"{w2:.2f}",
                     f"{100 * (w2 - wb) / abs(w2):.1f}%", f"{100 * (w2 - wf) / abs(w2):.1f}%",
                     f"{r['tau_H']:.1f}/{r['tau_L']:.1f}"])
    md += ["## E4  Welfare under elastic demand (c=4, unpriced demand = 1.4 x capacity, P_max = 20 service-time delay costs)\n",
           table(rows, ["arrivals", "W burst-blind flat", "W best flat", "W burst-aware 2-price",
                        "loss of blind flat", "loss of best flat", "tolls H/L"]), ""]
    text = "\n".join(md)
    print(text)
    with open("results/mmpp_serving.md", "w") as fh:
        fh.write(text)
    with open("results/mmpp_serving.json", "w") as fh:
        json.dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
