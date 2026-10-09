"""Pricing results (trace_equilibrium.py) re-done for non-exponential service times, by simulation.

Phase-modulated Poisson arrivals / G / c, FCFS, mean service = 1.  Service shape: gamma (cs2 < 1),
exponential, lognormal (cs2 > 1).  Users see phase and price (not the queue): lam_k = Lam_k (1-(p_k+d_k)/P)_+
with d_k the simulated mean sojourn of phase-k requests (fixed point; common random numbers via thinning).
Policies: no price, Poisson-blind flat (optimal flat price if arrivals were Poisson), best flat,
phase-dependent (planner rates found by coordinate search, implemented with p_k = tau_k - d_k).
Welfare = sum_k pi_k B_k(lam_k) - sum_k pi_k lam_k d_k.
Usage: python trace_service_pricing.py DATA_DIR [OUT.md] [--quick]"""
import math
import sys

import numpy as np

import trace_calibration as tc
import trace_models as tm
import trace_pricing as tp

P, OVER = tp.PBAR, tp.OVER


def service(cs2, n, rng):
    if cs2 == 1.0:
        return rng.exponential(1.0, n)
    if cs2 < 1:
        return rng.gamma(1 / cs2, cs2, n)
    s2 = math.log(1 + cs2)
    return rng.lognormal(-s2 / 2, math.sqrt(s2), n)


class World:
    """Max-rate (unpriced demand) points with fixed marks / service times; a policy thins them."""

    def __init__(self, Lam, G, T, cs2, rng):
        K = len(Lam)
        self.Lam = np.asarray(Lam, float)
        piK = tp.stationary(G) if K > 1 else np.array([1.0])
        self.piK = piK
        k = rng.choice(K, p=piK)
        t, ts, ks = 0.0, [], []
        while t < T:
            dur = rng.exponential(1 / -G[k, k]) if K > 1 else T
            dur = min(dur, T - t)
            m = rng.poisson(self.Lam[k] * dur)
            if m:
                ts.append(t + np.sort(rng.random(m)) * dur)
                ks.append(np.full(m, k))
            t += dur
            if K > 1:
                row = np.maximum(G[k], 0)
                k = rng.choice(K, p=row / row.sum())
        self.t, self.k = np.concatenate(ts), np.concatenate(ks)
        self.mark = rng.random(len(self.t))
        self.svc = service(cs2, len(self.t), rng)
        self.T = T

    def run(self, lam, c, warm=0.1):
        keep = self.mark < (np.asarray(lam) / self.Lam)[self.k]
        a, s, kk = self.t[keep], self.svc[keep], self.k[keep]
        w = tc.sim_queue(a, s, c)
        ok = a > warm * self.T
        soj = (w + s)
        d = np.array([soj[ok & (kk == j)].mean() if (ok & (kk == j)).any() else 1.0 for j in range(len(lam))])
        return d


def welfare(lam, d, Lam, piK):
    return float(piK @ (P * (lam - lam ** 2 / (2 * Lam))) - piK @ (lam * d))


def equilibrium(world, prices, c, lam0=None, tol=0.01):
    Lam = world.Lam
    prices = np.broadcast_to(np.asarray(prices, float), Lam.shape)
    lam = Lam * np.clip(1 - (prices + 1) / P, 0, 1) if lam0 is None else lam0.copy()
    alpha, prev = 0.5, 1e18
    for _ in range(25):
        d = world.run(lam, c)
        new = Lam * np.clip(1 - (prices + d) / P, 0, 1)
        err = np.abs(new - lam).max() / Lam.max()
        if err < tol:
            break
        if err > prev:
            alpha = max(alpha / 2, 0.15)
        prev = err
        lam = (1 - alpha) * lam + alpha * new
    d = world.run(lam, c)
    return lam, d, welfare(lam, d, Lam, world.piK)


def study(name, lam_s, G, c, T, cs2s, quick, md, seed=0):
    K = len(lam_s)
    piK = tp.stationary(G)
    lbar = float(piK @ lam_s)
    Lam = lam_s * OVER * c / lbar
    Lm = float(piK @ Lam)
    rows = []
    for cs2 in cs2s:
        rng = np.random.default_rng(seed)
        wb = World(Lam, G, T, cs2, rng)
        wp = World(np.array([Lm]), np.zeros((1, 1)), T, cs2, rng)
        # no price
        lam0, d0, w0 = equilibrium(wb, 0.0, c)
        # Poisson-blind flat price
        pb, best = 0.0, -1e18
        for p in np.linspace(0, 12, 7 if not quick else 4):
            _, _, w = equilibrium(wp, p, c)
            if w > best:
                best, pb = w, p
        _, _, wbl = equilibrium(wb, pb, c, lam0)
        # best flat
        pf, wf = 0.0, -1e18
        for p in np.linspace(0, 12, 7 if not quick else 4):
            _, _, w = equilibrium(wb, p, c, lam0)
            if w > wf:
                wf, pf = w, p
        # phase-dependent: planner rates by coordinate search, then implied prices
        taus = np.full(K, pf + 1.0)
        cur = welfare(Lam * np.clip(1 - taus / P, 0, 1), wb.run(Lam * np.clip(1 - taus / P, 0, 1), c), Lam, piK)
        for _ in range(2):
            for j in range(K):
                for x in np.linspace(0, P, 11 if not quick else 6):
                    tt = taus.copy(); tt[j] = x
                    lam = Lam * np.clip(1 - tt / P, 0, 1)
                    if piK @ lam >= 0.995 * c:
                        continue
                    v = welfare(lam, wb.run(lam, c), Lam, piK)
                    if v > cur:
                        cur, taus = v, tt
        lam_star = Lam * np.clip(1 - taus / P, 0, 1)
        p_impl = np.maximum(taus - wb.run(lam_star, c), 0)
        _, _, wopt = equilibrium(wb, p_impl, c, lam_star)
        top = max(wopt, cur)
        rows.append([cs2, f"{w0:.1f}", f"{wbl:.1f} (p={pb:.0f})", f"{wf:.1f} (p={pf:.0f})", f"{wopt:.1f}",
                     ", ".join(f"{x:.1f}" for x in p_impl),
                     f"{100 * (top - w0) / abs(top):.0f}% / {100 * (top - wbl) / abs(top):.0f}% / {100 * (top - wf) / abs(top):.0f}%"])
        print(name, rows[-1], flush=True)
    md.append(f"## {name}\n")
    md.append(f"c={c}, horizon {T:.0f} service times, unpriced demand {OVER}x capacity, P={P:.0f}. Welfare by policy "
              "(equilibrium demand) and loss relative to the best phase-dependent welfare.\n")
    md.append(tc.table(rows, ["service cs2", "no price", "Poisson-blind flat", "best flat", "phase-dependent",
                              "implied phase prices", "loss: none / blind / flat"]))
    md.append("")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    data = args[0]
    out = args[1] if len(args) > 1 else "results/trace_service_pricing.md"
    cs2s = (0.5, 1.0, 4.0, 16.0)
    md = ["# Pricing under non-exponential service times (simulation, equilibrium demand)\n"]
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_code.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    p = tc.fit_mmpp2(len(t) / t[-1], tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300]))
    G = np.array([[-p["rHL"], p["rHL"]], [p["rLH"], -p["rLH"]]]) * tau
    study("Code trace: fitted MMPP(2)", np.array([p["lH"], p["lL"]]) * tau, G, 7, 40000 if not quick else 8000, cs2s, quick, md)
    open(out, "w").write("\n".join(md))
    t, ctx, gen = tc.load(f"{data}/AzureLLMInferenceTrace_conv.csv")
    tau = (tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen).mean()
    lam, Pm, _ = tm.fit_chain(t)
    study("Conversation trace: 5-state rate chain", lam * tau, tp.cont_generator(Pm, tm.BIN, tau), 45,
          15000 if not quick else 3000, cs2s, quick, md)
    open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
