"""Congestion pricing on trace-calibrated bursty arrivals (re-runs E3/E4 of serving_mmpp.py).

Arrival models (time unit = mean service time of the trace, service ~ exponential):
  conv  5-state rate-chain fitted to the conversation trace (30-s rate quantiles), c = 45 (rho = 0.85)
  code  2-state MMPP fitted to the code trace IDC, c = 7 (rho = 0.68)
Phase-modulated Poisson arrivals / M / c, solved exactly as a CTMC.

E3  Pigouvian toll per request = h(k, n+1) - h(k, n) - own delay, averaged over arrivals, per phase.
E4  Elastic demand (linear, choke price P = 20 service-time delay costs, unpriced demand = 1.4 x capacity).
    Toll policies: burst-blind flat, best flat, phase-dependent tolls (coordinate search).
Usage: python trace_pricing.py DATA_DIR [OUT.md]"""
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

import trace_calibration as tc
import trace_models as tm

PBAR, OVER = 20.0, 1.4


class PhaseQueue:
    """Phase-modulated Poisson / M / c.  State i = n*K + k.  mu = 1."""

    def __init__(self, lam, G, c, N):
        self.lam, self.G, self.c, self.N = np.asarray(lam, float), np.asarray(G, float), c, N
        K = len(lam)
        self.K = K
        M = K * (N + 1)
        n = np.repeat(np.arange(N + 1), K)
        k = np.tile(np.arange(K), N + 1)
        i = np.arange(M)
        up, dn = n < N, n > 0
        r, cl, v = [i[up]], [i[up] + K], [self.lam[k[up]]]
        r.append(i[dn]); cl.append(i[dn] - K); v.append(np.minimum(n[dn], c).astype(float))
        for j in range(K):
            for a in range(K):
                if a != j and self.G[a, j] > 0:
                    sel = k == a
                    r.append(i[sel]); cl.append(n[sel] * K + j); v.append(np.full(sel.sum(), self.G[a, j]))
        Q = sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(cl))), shape=(M, M))
        self.Q = (Q - sp.diags(np.asarray(Q.sum(axis=1)).ravel())).tocsr()
        A = sp.lil_matrix(self.Q.T)
        A[M - 1, :] = 1.0
        b = np.zeros(M); b[-1] = 1.0
        self.pi = spl.spsolve(A.tocsc(), b)
        self.P = self.pi.reshape(-1, K)

    def top_mass(self):
        return self.P[-3:].sum()

    def L(self):
        return float((np.arange(self.N + 1)[:, None] * self.P).sum())

    def phase_dist(self):
        return self.P.sum(0)

    def toll(self):
        f = np.repeat(np.arange(self.N + 1), self.K).astype(float)
        g = self.pi @ f
        A = sp.lil_matrix(self.Q)
        b = g - f
        A[-1, :] = self.pi
        b[-1] = 0.0
        h = spl.spsolve(A.tocsc(), b).reshape(-1, self.K)
        n = np.arange(self.N)
        own = np.where(n < self.c, 1.0, (n - self.c + 1) / self.c + 1.0)[:, None]
        return h[1:] - h[:-1] - own  # [n, k]


def cont_generator(Pm, bin_s, tau):
    return (Pm - np.eye(len(Pm))) / bin_s * tau


def welfare(lam_eff, Lam, G, c, N, piK, strict=True):
    q = PhaseQueue(lam_eff, G, c, N)
    if (strict and q.top_mass() > 1e-3) or lam_eff @ piK >= 0.995 * c:
        return -1e9
    B = piK @ (PBAR * (lam_eff - lam_eff ** 2 / (2 * Lam)))
    return B - q.L()


def stationary(G):
    K = len(G)
    A = G.T.copy(); A[-1, :] = 1.0
    b = np.zeros(K); b[-1] = 1.0
    return np.linalg.solve(A, b)


def run(name, lam_s, G, c, N, md):
    K = len(lam_s)
    piK = stationary(G)
    lbar = float(piK @ lam_s)
    q = PhaseQueue(lam_s, G, c, N)
    assert q.top_mass() < 1e-3, f"truncation too small ({q.top_mass():.2e})"
    qp = PhaseQueue([lbar], np.zeros((1, 1)), c, N)
    md.append(f"## {name}\n")
    md.append(f"c={c}, mean load {lbar:.1f} (rho={lbar / c:.2f}); phase rates (per service time): "
              + ", ".join(f"{x:.1f}" for x in lam_s) + f"; phase probabilities: "
              + ", ".join(f"{x:.2f}" for x in piK) + f"; E[sojourn] bursty {q.L() / lbar:.2f} vs Poisson {qp.L() / lbar:.2f}\n")
    # --- E3: toll of a phase-k request = (dL/dlam_k)/pi_k - E_k[own sojourn]   (finite differences;
    # the Poisson-equation solve is ill-conditioned for long queues)
    def phase_toll(qq, lam_v):
        piK_ = qq.phase_dist()
        L0, out = qq.L(), []
        n = np.arange(qq.N + 1)
        own = np.where(n < c, 1.0, (n - c + 1) / c + 1.0)
        for k in range(len(lam_v)):
            l2 = np.array(lam_v, float); l2[k] *= 1.001
            q2 = PhaseQueue(l2, G if len(lam_v) > 1 else np.zeros((1, 1)), c, N)
            marg = (q2.L() - L0) / (lam_v[k] * 0.001) / piK_[k]
            out.append(marg - float((qq.P[:, k] * own).sum() / piK_[k]))
        return np.array(out), piK_
    byk, _ = phase_toll(q, lam_s)
    avg = float(((piK * lam_s) @ byk) / lbar)
    avg_p = float(phase_toll(qp, [lbar])[0][0])
    md.append(f"### E3  Pigouvian toll per request (units: one service time of delay)\n")
    md.append(f"Poisson (same mean): {avg_p:.2f}; bursty average: {avg:.1f} ({avg / avg_p:.0f}x); by phase "
              + ", ".join(f"{b:.1f}" for b in byk) + "\n")
    # --- E4
    Lam = lam_s * OVER * c / lbar
    pol = {}
    rate = lambda taus: Lam * np.clip(1 - np.asarray(taus) / PBAR, 0, 1)
    # burst-blind flat toll: optimise as if Poisson with the same mean
    best, tb = -1e18, 0.0
    for tau in np.linspace(0, PBAR, 30):
        lam_eff = rate(np.full(K, tau))
        m = float(piK @ lam_eff)
        if m >= 0.995 * c:
            continue
        pq = PhaseQueue([m], np.zeros((1, 1)), c, N)
        val = float(piK @ (PBAR * (lam_eff - lam_eff ** 2 / (2 * Lam)))) - pq.L()
        if val > best:
            best, tb = val, tau
    pol["burst-blind flat (lower bound on loss: queue cap reached)"] = (welfare(rate(np.full(K, tb)), Lam, G, c, N, piK, strict=False), np.full(K, tb))
    grid = np.linspace(0, PBAR, 25)
    ev = [(welfare(rate(np.full(K, x)), Lam, G, c, N, piK), x) for x in grid]
    wf, xf = max(ev)
    pol["best flat"] = (wf, np.full(K, xf))
    taus = np.full(K, xf)
    cur = wf
    for sweep in range(2):
        for k in range(K):
            cand = []
            for x in np.linspace(0, PBAR, 21):
                tt = taus.copy(); tt[k] = x
                cand.append((welfare(rate(tt), Lam, G, c, N, piK), x))
            v, x = max(cand)
            if v > cur:
                cur, taus[k] = v, x
    pol["phase-dependent"] = (cur, taus.copy())
    top = pol["phase-dependent"][0]
    rows = [[k, f"{v:.2f}", f"{100 * (top - v) / abs(top):.1f}%", ", ".join(f"{x:.1f}" for x in tt)]
            for k, (v, tt) in pol.items()]
    md.append("### E4  Welfare under elastic demand (tolls in service-time delay costs)\n")
    md.append(tc.table(rows, ["policy", "welfare", "loss vs phase-dependent", "tolls by phase"]))
    md.append("")
    print("\n".join(md[-8:]), flush=True)


def main():
    data = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "results/trace_pricing.md"
    md = ["# Pricing on trace-calibrated bursty arrivals\n"]
    # conversation: rate chain
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_conv.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    lam, P, _ = tm.fit_chain(t)
    run("Conversation trace: 5-state rate chain", lam * tau, cont_generator(P, tm.BIN, tau), 45, 45 + 1500, md)
    # code: MMPP(2)
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_code.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    lbar = len(t) / t[-1]
    p = tc.fit_mmpp2(lbar, tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300]))
    G = np.array([[-p["rHL"], p["rHL"]], [p["rLH"], -p["rLH"]]]) * tau
    run("Code trace: fitted MMPP(2)", np.array([p["lH"], p["lL"]]) * tau, G, 7, 7 + 2500, md)
    open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
