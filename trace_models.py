"""Which arrival model reproduces the real queueing delay of the Azure traces?

Compared on 1-hour paths (same length as the trace), service times resampled from the trace:
  real        replay of the actual trace (one path)
  block-boot  moving-block bootstrap of the real arrivals (300 s blocks): sampling noise of `real`
  poisson     homogeneous Poisson, same mean rate
  mmpp2       MMPP(2) fitted to IDC(w)   (trace_calibration.fit_mmpp2)
  rate-chain  K-state Markov-modulated Poisson; states = quantiles of the 30-s rate, transition
              matrix and state rates estimated from the trace
Usage: python trace_models.py DATA_DIR [OUT.md]"""
import math
import sys

import numpy as np

import trace_calibration as tc

BIN, K, BLOCK, REPS = 30.0, 5, 300.0, 100
rng = np.random.default_rng(7)


def block_bootstrap(t, H):
    nb = int(H // BLOCK)
    edges = np.arange(0, t[-1] - BLOCK, BLOCK)
    out = []
    for j in range(nb):
        s = rng.choice(edges)
        seg = t[(t >= s) & (t < s + BLOCK)] - s
        out.append(seg + j * BLOCK)
    return np.concatenate(out)


def fit_chain(t):
    n = int(t[-1] // BIN)
    cnt = np.bincount((t[t < n * BIN] // BIN).astype(int), minlength=n)
    rate = cnt / BIN
    q = np.quantile(rate, np.linspace(0, 1, K + 1))
    st = np.clip(np.searchsorted(q[1:-1], rate, side="right"), 0, K - 1)
    lam = np.array([rate[st == k].mean() if (st == k).any() else rate.mean() for k in range(K)])
    P = np.full((K, K), 0.5 / K)  # light smoothing
    for a, b in zip(st[:-1], st[1:]):
        P[a, b] += 1
    return lam, P / P.sum(1, keepdims=True), st


def gen_chain(lam, P, st, H):
    n = int(math.ceil(H / BIN))
    s = rng.choice(st)
    segs = []
    for i in range(n):
        m = rng.poisson(lam[s] * BIN)
        segs.append(i * BIN + np.sort(rng.random(m)) * BIN)
        s = rng.choice(K, p=P[s])
    return np.concatenate(segs)


def stats(arrs, svc, c, tau):
    r = []
    for a in arrs:
        w = tc.sim_queue(a, rng.choice(svc, len(a)), c)
        r.append((w.mean(), (w > tau).mean()))
    r = np.array(r)
    return r[:, 0].mean(), np.median(r[:, 0]), r[:, 1].mean(), np.percentile(r[:, 1], [10, 90])


def main():
    data = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "results/trace_models.md"
    md = ["# Arrival-model comparison on the Azure traces (1-hour paths, 100 replications per model)\n"]
    for name, f, cs in (("Conversation trace", "AzureLLMInferenceTrace_conv.csv", (64, 51, 45, 42)),
                        ("Code trace", "AzureLLMInferenceTrace_code.csv", (9, 8, 7, 6))):
        t, ctx, gen = tc.load(f"{data}/{f}")
        svc = tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen
        lbar, tau, H = len(t) / t[-1], svc.mean(), t[-1]
        idc = tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300])
        p2 = tc.fit_mmpp2(lbar, idc)
        lam, P, st = fit_chain(t)
        paths = {
            "block-boot": [block_bootstrap(t, H) for _ in range(REPS)],
            "poisson": [tc.gen_poisson(lbar, H, rng) for _ in range(REPS)],
            "mmpp2": [tc.gen_mmpp(p2, H, rng) for _ in range(REPS)],
            "rate-chain": [gen_chain(lam, P, st, H) for _ in range(REPS)],
        }
        md.append(f"## {name}\n")
        md.append(f"rate {lbar:.2f}/s, mean service {tau:.2f}s (tau). rate-chain states (req/s): "
                  + ", ".join(f"{x:.1f}" for x in lam) + "; stay-probabilities per 30 s: "
                  + ", ".join(f"{P[k, k]:.2f}" for k in range(K)) + "\n")
        rows = []
        for c in cs:
            w = tc.sim_queue(t, svc, c)
            rows.append([c, f"{lbar * tau / c:.2f}", "real", f"{w.mean():.2f}", "-", f"{(w > tau).mean():.3f}", "-"])
            for m, arrs in paths.items():
                mean, med, pm, (lo, hi) = stats(arrs, svc, c, tau)
                rows.append(["", "", m, f"{mean:.2f}", f"{med:.2f}", f"{pm:.3f}", f"{lo:.3f}-{hi:.3f}"])
        md.append(tc.table(rows, ["c", "rho", "arrivals", "E[wait] mean", "E[wait] median", "P(wait>tau) mean", "P 10-90%"]))
        # servers needed for P(wait>tau)<=5% (mean over replications)
        need = {}
        for m, arrs in paths.items():
            ok = lambda c: np.mean([(tc.sim_queue(a, rng.choice(svc, len(a)), c) > tau).mean() for a in arrs[:30]]) <= 0.05
            lo = int(lbar * tau)
            hi = lo + 1
            while not ok(hi):
                lo, hi = hi, hi + max(1, hi // 4)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if ok(mid) else (mid, hi)
            need[m] = hi
        real_ok = next(c for c in range(int(lbar * tau) + 1, 400) if (tc.sim_queue(t, svc, c) > tau).mean() <= 0.05)
        md.append(f"\nServers needed for P(wait>tau) <= 5%: real replay {real_ok}; "
                  + "; ".join(f"{m} {v}" for m, v in need.items()) + "\n")
        print("\n".join(md[-4:]), flush=True)
    open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
