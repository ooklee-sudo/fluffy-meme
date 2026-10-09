"""Calibration on longer public traces: BurstGPT v2.0 file 1 (121 days) and Azure LLM Inference 2024 code (7 days).

For each trace
  1. hour-of-day rate profile (peak/mean) and the residual burstiness left after removing that profile;
  2. queue replay of the real trace vs homogeneous Poisson vs hour-of-day inhomogeneous Poisson (NHPP), FCFS, c servers;
  3. pricing with 24 hour-of-day phases (long phases, so the quasi-static results of paper_notes/theory.md apply):
     loss of the best flat price, of a two-level (peak / off-peak) schedule, relative to hourly first-best prices.
Service time = 0.0005 s * prompt tokens + 0.03 s * generated tokens (assumption, as before); tau = mean service time.
Usage: python longtrace.py burst|azure PATH [OUT.md]"""
import sys

import numpy as np
import pandas as pd

import theory_check as th
import trace_calibration as tc
import theory_props as tpr

A, B = tc.PREFILL_S_PER_TOK, tc.DECODE_S_PER_TOK
rng = np.random.default_rng(3)


def load_burst(path):
    df = pd.read_csv(path, usecols=["Timestamp", "Request tokens", "Response tokens"])
    t = df["Timestamp"].to_numpy(float) + rng.random(len(df))  # 1-s resolution: spread uniformly in the second
    o = np.argsort(t, kind="stable")
    return t[o], (A * df["Request tokens"].to_numpy(float) + B * df["Response tokens"].to_numpy(float))[o]


def load_azure(path):
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["TIMESTAMP"], utc=True, format="ISO8601")
    t = (ts - ts.min()).dt.total_seconds().to_numpy(float)
    svc = A * df["ContextTokens"].to_numpy(float) + B * df["GeneratedTokens"].to_numpy(float)
    o = np.argsort(t, kind="stable")
    return t[o], svc[o]


def hourly_profile(t):
    T = t[-1]
    days = T / 86400.0
    h = ((t % 86400) // 3600).astype(int)
    return np.bincount(h, minlength=24) / (days * 3600.0)  # requests per second in each hour-of-day


def residual_idc(t, lam_h, windows):
    out = {}
    T = t[-1]
    for w in windows:
        n = int(T // w)
        cnt = np.bincount((t[t < n * w] // w).astype(int), minlength=n)
        start = np.arange(n) * w
        mu = lam_h[((start % 86400) // 3600).astype(int)] * w
        out[w] = float(np.var(cnt - mu, ddof=1) / cnt.mean())
    return out


def gen_nhpp(lam_h, T):
    segs = []
    for i in range(int(T // 3600)):
        lam = lam_h[i % 24]
        m = rng.poisson(lam * 3600)
        segs.append(i * 3600.0 + np.sort(rng.random(m)) * 3600.0)
    return np.concatenate(segs)


def replay(t, svc, lam_h, c, tau):
    T = t[-1]
    res = {}
    models = {"real": (t, svc),
              "Poisson": (np.sort(rng.random(len(t)) * T), None),
              "hour-of-day NHPP": (gen_nhpp(lam_h, T), None)}
    for name, (a, s) in models.items():
        if s is None:
            s = rng.choice(svc, len(a))
        w = tc.sim_queue(a, s, c)
        w = w[int(0.02 * len(w)):]
        res[name] = (w.mean(), float((w > tau).mean()), float((w > 10 * tau).mean()))
    return res


def pricing(lam_h, c, md):
    K = 24
    pis = np.full(K, 1.0 / K)
    Lams = 1.4 * c * lam_h / lam_h.mean()
    r = th.analyse_qs(Lams, pis, c)
    # table of W_k(p) for the two-level search
    grid = np.linspace(0, th.P, 81)
    Wt = np.array([[th.w_phase(th.eq_rate(p, Lams[k], c), Lams[k], c) for p in grid] for k in range(K)])
    order = np.argsort(Lams)
    best2 = (-1e18, None)
    for m in range(1, K):
        lo, hi = order[:m], order[m:]
        wl = Wt[lo].sum(0) / K
        wh = Wt[hi].sum(0) / K
        v = wl.max() + wh.max()
        if v > best2[0]:
            best2 = (v, (m, grid[wl.argmax()], grid[wh.argmax()]))
    wfb, wflat = r["wfb"], r["wflat"]
    tol = r["tol"]
    md.append(f"- Pricing with 24 hourly phases (c={c}): hourly first-best prices range {tol.min():.2f}-{tol.max():.2f}; best flat price "
              f"{r['pflat']:.2f} loses {100 * (wfb - wflat) / abs(wfb):.1f}% of first-best welfare; best two-level schedule "
              f"({best2[1][0]} off-peak hours at {best2[1][1]:.1f}, {24 - best2[1][0]} peak hours at {best2[1][2]:.1f}) loses "
              f"{100 * (wfb - best2[0]) / abs(wfb):.1f}%; no price loses {100 * (wfb - r['wnone']) / abs(wfb):.1f}%.")


def pricing_empirical(t, c, md):
    """Phases = every clock hour of the trace (each a long phase). Compare real-time first best, an hour-of-day schedule,
    a single flat price and no price (quasi-static model)."""
    n = int(t[-1] // 3600)
    cnt = np.bincount((t[t < n * 3600] // 3600).astype(int), minlength=n).astype(float)
    rate = np.maximum(cnt / 3600.0, 1e-4 * cnt.mean() / 3600.0)
    Lams = 1.4 * c * rate / rate.mean()
    grid = np.linspace(0, th.P, 81)
    Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams])
    wfb = sum(th.w_phase(th.first_best(L, c), L, c) for L in Lams)
    wflat = Wt.sum(0).max()
    hod = np.arange(n) % 24
    whod = sum(Wt[hod == g].sum(0).max() for g in range(24))
    wnone = Wt[:, 0].sum()
    loss = lambda w: 100 * (wfb - w) / abs(wfb)
    md.append(f"- Pricing with every clock hour as a phase ({n} hours, c={c}; hourly rate / mean: median {np.median(rate / rate.mean()):.2f}, "
              f"p95 {np.percentile(rate / rate.mean(), 95):.2f}, max {(rate / rate.mean()).max():.2f}): loss vs real-time first-best: "
              f"best flat price {loss(wflat):.1f}%, hour-of-day schedule {loss(whod):.1f}%, no price {loss(wnone):.1f}%.")


def main():
    kind, path = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else f"results/longtrace_{kind}.md"
    t, svc = (load_burst if kind == "burst" else load_azure)(path)
    T = t[-1]
    lam_h = hourly_profile(t)
    lbar = len(t) / T
    tau = svc.mean()
    md = [f"# Longer-trace calibration: {'BurstGPT v2.0 file 1' if kind == 'burst' else 'Azure LLM Inference 2024 (code)'}\n",
          f"{len(t):,} requests over {T / 86400:.1f} days; mean rate {lbar:.3f}/s; mean service {tau:.2f}s "
          f"(assumed token coefficients); offered load {lbar * tau:.1f} servers; service cs2 = {svc.var() / tau ** 2:.2f}.\n",
          f"Hour-of-day rate / mean: peak {lam_h.max() / lam_h.mean():.2f}, trough {lam_h.min() / lam_h.mean():.2f}; "
          "profile (x mean): " + ", ".join(f"{x:.2f}" for x in lam_h / lam_h.mean()) + "\n"]
    ridc = residual_idc(t, lam_h, [1, 10, 60, 300, 900, 3600])
    md.append("Residual IDC after removing the hour-of-day profile (Poisson / NHPP = 1): " +
              ", ".join(f"w={w}s: {v:.2f}" for w, v in ridc.items()) + "\n")
    rows, seen = [], set()
    for rho in (0.5, 0.7, 0.85):
        c = max(int(np.ceil(lbar * tau / rho)), 1)
        if c in seen:
            continue
        seen.add(c)
        res = replay(t, svc, lam_h, c, tau)
        for name, (m, p1, p10) in res.items():
            rows.append([f"{lbar * tau / c:.2f}", c, name, f"{m:.2f}", f"{p1:.4f}", f"{p10:.4f}"])
        print("replay", rho, c, flush=True)
    md.append(tc.table(rows, ["mean rho", "c", "arrivals", "E[wait] (s)", "P(wait>tau)", "P(wait>10 tau)"]))
    md.append("")
    cpr = max(int(np.ceil(lbar * tau / 0.7)), 1)
    pricing(lam_h, cpr, md)
    pricing_empirical(t, cpr, md)
    open(out, "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
