"""Does matching IDC(w) make a 2-state MMPP predict the real trace's queueing delay?
Conversation trace: replay vs. MMPP(2) fits with burst-time fraction pH = 5% (grid optimum) and 50%.
Usage: python trace_fit_sensitivity.py DATA_DIR"""
import math
import sys

import numpy as np

import trace_calibration as tc

rng = np.random.default_rng(1)
t, ctx, gen = tc.load(sys.argv[1] + "/AzureLLMInferenceTrace_conv.csv")
svc = tc.PREFILL_S_PER_TOK * ctx + tc.DECODE_S_PER_TOK * gen
lbar, m, H = len(t) / t[-1], svc.mean(), t[-1]
idc = tc.idc_curve(t, [1, 2, 5, 10, 30, 60, 120, 300])
r = np.bincount((t // 60).astype(int))[:-1] / 60
print("60s-window rate: min %.2f p10 %.2f median %.2f p90 %.2f max %.2f" % (r.min(), *np.percentile(r, [10, 50, 90]), r.max()))


def fit_sym():
    ws = np.array(sorted(idc))
    y = np.array([idc[w] - 1 for w in ws])
    best = (1e18,)
    for rr in np.logspace(-3.5, 1.5, 300):
        g = 1 / rr - (1 - np.exp(-rr * ws)) / (rr * rr * ws)
        X = 2 * .25 / lbar * g / y
        d = min(math.sqrt(X.sum() / (X * X).sum()), 0.98 * lbar / .5)
        e = np.sum((2 * .25 * d * d / lbar * g / y - 1) ** 2)
        if e < best[0]:
            best = (e, d, rr)
    _, d, rr = best
    lL = lbar - .5 * d
    return dict(lH=lL + d, lL=lL, rHL=rr * .5, rLH=rr * .5, pH=.5)


for label, p in (("pH=5% (grid optimum)", tc.fit_mmpp2(lbar, idc)), ("pH=50% (symmetric)", fit_sym())):
    print(label, "burst %.1f/s off %.1f/s mean burst %.0fs" % (p["lH"], p["lL"], 1 / p["rHL"]))
    for c in (64, 51, 45, 42):
        res = np.array([(lambda w: (w.mean(), (w > m).mean()))(
            tc.sim_queue(a, rng.choice(svc, len(a)), c)) for a in (tc.gen_mmpp(p, H, rng) for _ in range(40))])
        w = tc.sim_queue(t, svc, c)
        print("  c=%d  real: E[wait] %.2f P %.3f | MMPP 1-hour paths: E[wait] mean %.2f median %.2f, P mean %.3f"
              % (c, w.mean(), (w > m).mean(), res[:, 0].mean(), np.median(res[:, 0]), res[:, 1].mean()))
