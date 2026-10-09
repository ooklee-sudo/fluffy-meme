"""Analytic reinforcement for the flat-vs-phase pricing result.

Quasi-static (slow-modulation) model: in traffic phase k (probability pi_k, demand potential Lam_k) the
queue is in the stationary M/M/c state for the phase's request rate.  Users face price p_k and see phase
and price, so  lam_k = Lam_k (1 - (p_k + d(lam_k))/P)_+,  d = mean sojourn (Erlang-C), welfare per phase
w_k(lam) = P(lam - lam^2/(2 Lam_k)) - lam d(lam).

A  Harberger formula.  First best = Pigouvian phase tolls t_k = lam_k d'(lam_k).  With one flat price the
   welfare loss is, to second order,  Loss ~= 1/2 * sum_k pi_k kappa_k (t_k - tbar)^2,  kappa_k = -d lam_k/dp,
   tbar = kappa-weighted mean toll: i.e. the (kappa-weighted) variance of the Pigouvian toll across phases.
   Checked against the exact quasi-static loss and swept over demand dispersion (burstiness).
B  Provider view.  Monopolist profit with flat price vs. phase prices, and the welfare each delivers.
C  Switching speed.  Exact CTMC (trace_pricing.PhaseQueue) with the code-trace MMPP and dwell times scaled by
   f: loss of best flat price vs phase-dependent prices as f grows, compared with the quasi-static limit.
Usage: python theory_check.py DATA_DIR [OUT.md] [--skipC]"""
import sys

import numpy as np

import trace_calibration as tc
import trace_equilibrium as te
import trace_models as tm
import trace_pricing as tp

P = tp.PBAR


# ---------------------------------------------------------------- quasi-static model
def sojourn(lam, c):
    if lam <= 0:
        return 1.0
    if lam >= c:
        return np.inf
    B = 1.0
    for n in range(1, c + 1):
        B = lam * B / (n + lam * B)
    C = B / (1 - (lam / c) * (1 - B))
    return 1.0 + C / (c - lam)


def eq_rate(p, Lam, c):
    lo, hi = 0.0, min(Lam, c - 1e-9)
    g = lambda l: Lam * max(0.0, 1 - (p + sojourn(l, c)) / P) - l
    if g(hi) >= 0:
        return hi
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if g(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def w_phase(lam, Lam, c):
    return P * (lam - lam ** 2 / (2 * Lam)) - lam * sojourn(lam, c)


def first_best(Lam, c):
    ls = np.linspace(0, min(Lam, c - 1e-6), 2001)
    ws = np.array([w_phase(l, Lam, c) for l in ls])
    i = int(ws.argmax())
    a, b = ls[max(i - 1, 0)], ls[min(i + 1, len(ls) - 1)]
    for _ in range(50):  # golden-section refinement
        m1, m2 = a + (b - a) * 0.382, a + (b - a) * 0.618
        if w_phase(m1, Lam, c) < w_phase(m2, Lam, c):
            a = m1
        else:
            b = m2
    return (a + b) / 2


def analyse_qs(Lams, pis, c):
    """Return dict with exact and Harberger losses for the quasi-static model."""
    Lams, pis = np.asarray(Lams, float), np.asarray(pis, float)
    K = len(Lams)
    lfb = np.array([first_best(Lams[k], c) for k in range(K)])
    wfb = sum(pis[k] * w_phase(lfb[k], Lams[k], c) for k in range(K))
    h = 1e-4
    tol = np.array([lfb[k] * (sojourn(lfb[k] + h, c) - sojourn(lfb[k] - h, c)) / (2 * h) for k in range(K)])
    # equilibrium response to the price (kappa) at the first best price p_k = tol_k
    kap = np.array([-(eq_rate(tol[k] + 0.01, Lams[k], c) - eq_rate(tol[k] - 0.01, Lams[k], c)) / 0.02
                    for k in range(K)])
    tbar = float((pis * kap) @ tol / (pis * kap).sum())
    harb = 0.5 * float(pis @ (kap * (tol - tbar) ** 2))
    best = (-1e18, 0.0)
    for p in np.linspace(0, P, 401):
        w = sum(pis[k] * w_phase(eq_rate(p, Lams[k], c), Lams[k], c) for k in range(K))
        best = max(best, (w, p))
    wnone = sum(pis[k] * w_phase(eq_rate(0.0, Lams[k], c), Lams[k], c) for k in range(K))
    return dict(wfb=wfb, wflat=best[0], pflat=best[1], wnone=wnone, harb=harb, tol=tol, kap=kap, lfb=lfb,
                loss=wfb - best[0], tstd=float(np.sqrt(pis @ (tol - pis @ tol) ** 2)))


def provider(Lams, pis, c):
    Lams, pis = np.asarray(Lams, float), np.asarray(pis, float)
    K = len(Lams)
    ps = np.linspace(0, P, 401)
    prof = lambda k, p: p * eq_rate(p, Lams[k], c)
    flat = max((sum(pis[k] * prof(k, p) for k in range(K)), p) for p in ps)
    ph = [max((prof(k, p), p) for p in ps) for k in range(K)]
    w = lambda prices: sum(pis[k] * w_phase(eq_rate(prices[k], Lams[k], c), Lams[k], c) for k in range(K))
    return dict(profit_flat=flat[0], p_flat=flat[1], w_flat=w([flat[1]] * K),
                profit_phase=sum(pis[k] * ph[k][0] for k in range(K)), p_phase=[x[1] for x in ph],
                w_phase=w([x[1] for x in ph]))


# ---------------------------------------------------------------- scenarios
def scenario_conv(data):
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_conv.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    lam, Pm, _ = tm.fit_chain(t)
    G = tp.cont_generator(Pm, tm.BIN, tau)
    return lam * tau, G, 45


def scenario_code(data):
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_code.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    p = tc.fit_mmpp2(len(t) / t[-1], tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300]))
    G = np.array([[-p["rHL"], p["rHL"]], [p["rLH"], -p["rLH"]]]) * tau
    return np.array([p["lH"], p["lL"]]) * tau, G, 7


def lam_potential(lam_s, G, c, spread):
    """Phase demand potentials with mean OVER*c, relative spread scaled by `spread` (1 = trace)."""
    pi = tp.stationary(G)
    m = pi @ lam_s
    rel = lam_s / m
    rel = 1 + spread * (rel - 1)
    return tp.OVER * c * np.maximum(rel, 0.02), pi


def part_AB(name, lam_s, G, c, md):
    md.append(f"## {name}: quasi-static analysis (c={c})\n")
    rows, prow = [], []
    for spread in (0.0, 0.25, 0.5, 0.75, 1.0):
        Lams, pi = lam_potential(lam_s, G, c, spread)
        r = analyse_qs(Lams, pi, c)
        cv = float(np.sqrt(pi @ (Lams - pi @ Lams) ** 2) / (pi @ Lams))
        rows.append([spread, f"{cv:.2f}", f"{r['tstd']:.2f}", f"{r['pflat']:.1f}", f"{r['loss']:.2f}",
                     f"{r['harb']:.2f}", f"{100 * r['loss'] / abs(r['wfb']):.1f}%",
                     f"{100 * (r['wfb'] - r['wnone']) / abs(r['wfb']):.1f}%"])
        if spread == 1.0:
            pv = provider(Lams, pi, c)
            prow = [["flat price", f"{pv['p_flat']:.1f}", f"{pv['profit_flat']:.1f}", f"{pv['w_flat']:.1f}"],
                    ["phase prices", ", ".join(f"{x:.1f}" for x in pv["p_phase"]), f"{pv['profit_phase']:.1f}",
                     f"{pv['w_phase']:.1f}"]]
            prow.append(["(welfare first best)", "-", "-", f"{r['wfb']:.1f}"])
    md.append("### A  Flat-price loss vs. demand dispersion (spread 1 = fitted trace, 0 = Poisson)\n")
    md.append(tc.table(rows, ["spread", "CV of demand potential", "std of Pigouvian toll", "best flat p",
                              "exact loss", "Harberger 1/2 sum pi k (t-tbar)^2", "loss % of first best",
                              "no-price loss %"]))
    md.append("\n### B  Monopolist pricing (spread 1)\n")
    md.append(tc.table(prow, ["policy", "price(s)", "profit rate", "welfare"]))
    md.append("")
    print("\n".join(md[-6:]), flush=True)


def part_C(lam_s, G, c, N, md):
    md.append("## C  Switching speed, code-trace MMPP (exact CTMC; f = dwell-time multiplier)\n")
    pi = tp.stationary(G)
    Lams = lam_s * tp.OVER * c / (pi @ lam_s)
    rows = []
    for f in (0.2, 1.0, 5.0):
        Gf = G / f
        Nf = int(N * max(1, f ** 0.5))
        lam_flat, wflat, pflat = None, -1e18, 0
        for p in np.linspace(0, 16, 9):
            lam, q = te.equilibrium(p, Lams, Gf, c, Nf, lam_flat)
            w = te.welfare(lam, Lams, pi, q)
            if q.top_mass() < 1e-3 and w > wflat:
                wflat, pflat = w, p
        # phase-dependent optimum: planner rates, 2-D grid + refine
        def W(tt):
            lam = Lams * np.clip(1 - np.asarray(tt) / P, 0, 1)
            return tp.welfare(lam, Lams, Gf, c, Nf, pi)
        best = max((W([a, b]), a, b) for a in np.linspace(0, P, 11) for b in np.linspace(0, P, 11))
        _, a0, b0 = best
        best = max((W([a, b]), a, b) for a in np.linspace(a0 - 2, a0 + 2, 9) for b in np.linspace(max(b0 - 2, 0), b0 + 2, 9))
        rows.append([f, f"{1 / (-Gf[0, 0]):.1f}", f"{wflat:.2f} (p={pflat:.0f})", f"{best[0]:.2f}",
                     f"{100 * (best[0] - wflat) / abs(best[0]):.1f}%"])
        print("C", rows[-1], flush=True)
    md.append(tc.table(rows, ["f", "mean burst length (service times)", "best flat welfare", "phase-dependent welfare",
                              "flat loss"]))
    md.append("")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = args[0]
    out = args[1] if len(args) > 1 else "results/theory_check.md"
    md = ["# Analytic reinforcement: Harberger loss of flat pricing under bursty demand\n"]
    for name, sc in (("Conversation trace", scenario_conv), ("Code trace", scenario_code)):
        lam_s, G, c = sc(data)
        part_AB(name, lam_s, G, c, md)
        open(out, "w").write("\n".join(md))
    if "--skipC" not in sys.argv:
        lam_s, G, c = scenario_code(data)
        part_C(lam_s, G, c, 7 + 2500, md)
    open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
