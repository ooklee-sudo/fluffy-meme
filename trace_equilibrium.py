"""Extension of trace_pricing.py: demand from self-interested users (equilibrium) instead of a planner.

Users observe the current traffic phase k (and the posted price p_k) but not the queue length.
A phase-k request is made iff its value exceeds p_k + expected sojourn d_k; with linear demand
    lam_k = Lam_k * (1 - (p_k + d_k) / P)_+ ,   d_k = E[sojourn of a phase-k arrival]  (fixed point).
Compared: no price, burst-blind flat price (optimal if arrivals were Poisson), best flat price, and
the phase prices that implement the planner optimum of trace_pricing.py (p_k = tau_k - d_k).
Welfare = sum_k pi_k * B_k(lam_k) - E[L]  (prices are transfers).
Usage: python trace_equilibrium.py DATA_DIR [OUT.md]"""
import sys

import numpy as np

import trace_calibration as tc
import trace_models as tm
import trace_pricing as tp

P, OVER = tp.PBAR, tp.OVER


def delays(q, c):
    n = np.arange(q.N + 1)
    own = np.where(n < c, 1.0, (n - c + 1) / c + 1.0)
    pk = q.P.sum(0)
    return (q.P * own[:, None]).sum(0) / pk


def equilibrium(prices, Lam, G, c, N, lam0=None, tol=2e-3):
    K = len(Lam)
    prices = np.broadcast_to(np.asarray(prices, float), (K,))
    lam = Lam * np.clip(1 - (prices + 1) / P, 0, 1) if lam0 is None else lam0.copy()
    alpha, prev = 0.5, 1e18
    for _ in range(60):
        q = tp.PhaseQueue(np.maximum(lam, 1e-9), G, c, N)
        new = Lam * np.clip(1 - (prices + delays(q, c)) / P, 0, 1)
        err = np.abs(new - lam).max() / Lam.max()
        if err < tol:
            return lam, q
        if err > prev:
            alpha = max(alpha / 2, 0.1)
        prev = err
        lam = (1 - alpha) * lam + alpha * new
    return lam, q


def welfare(lam, Lam, piK, q):
    return float(piK @ (P * (lam - lam ** 2 / (2 * Lam))) - q.L())


def run(name, lam_s, G, c, N, tau_opt, md):
    K = len(lam_s)
    piK = tp.stationary(G)
    lbar = float(piK @ lam_s)
    Lam = lam_s * OVER * c / lbar
    rows = []

    def record(label, prices, lam0=None):
        lam, q = equilibrium(prices, Lam, G, c, N, lam0)
        d = delays(q, c)
        rows.append([label, ", ".join(f"{x:.1f}" for x in np.broadcast_to(prices, (K,))),
                     ", ".join(f"{x:.1f}" for x in lam), f"{piK @ lam / c:.2f}",
                     ", ".join(f"{x:.1f}" for x in d), f"{welfare(lam, Lam, piK, q):.2f}", f"{q.top_mass():.1e}"])
        return welfare(lam, Lam, piK, q), lam

    w0, lam0 = record("no price", 0.0)
    # Poisson-blind flat price: optimal flat price if arrivals were Poisson with the same mean demand
    Lm = float(piK @ Lam)
    bestw, pb = -1e18, 0.0
    for p in np.linspace(0, P, 21):
        lam, q = equilibrium(p, np.array([Lm]), np.zeros((1, 1)), c, N)
        w = welfare(lam, np.array([Lm]), np.array([1.0]), q)
        if w > bestw:
            bestw, pb = w, p
    wb, _ = record(f"burst-blind flat (Poisson-optimal p={pb:.0f})", pb, lam0)
    best = (-1e18, 0.0)
    for p in np.linspace(0, P, 11):
        lam, q = equilibrium(p, Lam, G, c, N, lam0)
        best = max(best, (welfare(lam, Lam, piK, q), p))
    wf, _ = record(f"best flat (p={best[1]:.0f})", best[1], lam0)
    # prices implementing the planner optimum: p_k = tau_k - d_k(lam*)
    lam_star = Lam * np.clip(1 - np.asarray(tau_opt) / P, 0, 1)
    qs = tp.PhaseQueue(lam_star, G, c, N)
    p_impl = np.asarray(tau_opt) - delays(qs, c)
    ws, _ = record("phase prices implementing planner optimum", np.maximum(p_impl, 0), lam_star)
    md.append(f"## {name}\n")
    md.append(f"c={c}, unpriced demand = {OVER}x capacity, choke value P={P:.0f} service times. "
              f"Planner optimum welfare (trace_pricing.py): {ws:.2f}.\n")
    md.append(tc.table(rows, ["policy", "price by phase", "equilibrium rate by phase", "rho", "sojourn by phase", "welfare", "top mass"]))
    md.append(f"\nLoss vs implemented optimum: no price {100 * (ws - w0) / abs(ws):.0f}%, burst-blind flat "
              f"{100 * (ws - wb) / abs(ws):.0f}%, best flat {100 * (ws - wf) / abs(ws):.0f}%. "
              f"Implied optimal phase prices (before clipping at 0): " + ", ".join(f"{x:.1f}" for x in p_impl) + "\n")
    print("\n".join(md[-4:]), flush=True)


def main():
    data = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "results/trace_equilibrium.md"
    md = ["# Equilibrium demand on trace-calibrated bursty arrivals\n"]
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_code.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    p = tc.fit_mmpp2(len(t) / t[-1], tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300]))
    G = np.array([[-p["rHL"], p["rHL"]], [p["rLH"], -p["rLH"]]]) * tau
    run("Code trace: fitted MMPP(2)", np.array([p["lH"], p["lL"]]) * tau, G, 7, 7 + 2500, [18.0, 2.0], md)
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_conv.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    lam, Pm, _ = tm.fit_chain(t)
    run("Conversation trace: 5-state rate chain", lam * tau, tp.cont_generator(Pm, tm.BIN, tau), 45, 45 + 1000,
        [3.0, 4.0, 6.0, 8.0, 10.0], md)
    open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
