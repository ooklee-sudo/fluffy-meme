"""Calibrate the MMPP serving model on a real LLM inference trace and test other service times.

Data: Azure LLM inference trace (2023): arrival timestamp, prompt tokens, generated tokens.
  conv = chat-style, code = code-completion.  Downloaded to --data (see README of the Azure
  Public Dataset); run `python trace_calibration.py --data DIR`.

Parts
  A  Arrival burstiness of the trace: inter-arrival CV^2 and IDC(w) at window sizes w.
  B  Fit MMPP(2) to the IDC curve (closed form for MMPP(2)), compare with Poisson.
  C  Validation: replay the real trace through a c-server FCFS queue (service time from tokens)
     and compare with simulated Poisson and fitted MMPP arrivals at the same mean rate.
  D  Service-time sensitivity (MMPP/G/c by simulation): exponential, lognormal cs^2=4,16, trace-based;
     delay, tail and replicas needed for a delay SLO, Poisson vs fitted MMPP.
  X  Cross-check of the simulator against the exact CTMC of serving_mmpp.py (exponential service).
"""
import argparse
import heapq
import math
import os

import numpy as np

# service time model: prefill + decode (seconds).  Only the *shape* matters once load/SLO are
# expressed relative to the mean service time.
PREFILL_S_PER_TOK = 0.0005
DECODE_S_PER_TOK = 0.03


def load(path):
    ts, ctx, gen = [], [], []
    with open(path) as fh:
        next(fh)
        for line in fh:
            t, a, b = line.strip().split(",")
            ts.append(t)
            ctx.append(int(a))
            gen.append(int(b))
    d = np.array(ts, dtype="datetime64[us]")
    t = (d - d.min()).astype("timedelta64[us]").astype(float) / 1e6
    o = np.argsort(t)
    return t[o], np.array(ctx)[o], np.array(gen)[o]


# ---------------------------------------------------------------- arrival statistics / MMPP
def idc_curve(t, windows):
    out = {}
    for w in windows:
        n = int(t[-1] // w)
        if n < 8:
            continue
        cnt = np.bincount((t[t < n * w] // w).astype(int), minlength=n)
        out[w] = cnt.var(ddof=1) / cnt.mean()
    return out


def idc_mmpp2(w, lbar, pH, delta, r):
    g = 1.0 / r - (1 - np.exp(-r * w)) / (r * r * w)
    return 1 + 2 * pH * (1 - pH) * delta ** 2 / lbar * g


def fit_mmpp2(lbar, idc):
    ws = np.array(sorted(idc))
    y = np.array([idc[w] - 1 for w in ws])
    y = np.maximum(y, 1e-3)
    best = (1e18,)
    for pH in (0.05, 0.1, 0.2, 0.3, 0.5):
        for r in np.logspace(-3.5, 1.5, 200):
            g = 1.0 / r - (1 - np.exp(-r * ws)) / (r * r * ws)
            X = 2 * pH * (1 - pH) / lbar * g / y
            d2 = X.sum() / (X * X).sum()
            d = math.sqrt(d2)
            d = min(d, 0.98 * lbar / pH)  # keep lambda_L >= ~0
            err = np.sum((2 * pH * (1 - pH) * d * d / lbar * g / y - 1) ** 2)
            if err < best[0]:
                best = (err, pH, d, r)
    _, pH, d, r = best
    lL = lbar - pH * d
    lH = lL + d
    rHL = r * (1 - pH)  # mean burst length 1/rHL
    rLH = r * pH
    return dict(lH=lH, lL=lL, rHL=rHL, rLH=rLH, pH=pH, fit_err=best[0])


def gen_mmpp(p, horizon, rng):
    """Arrival times of MMPP(2) on [0, horizon]."""
    lam = (p["lH"], p["lL"])
    rate = (p["rHL"], p["rLH"])
    s = 0 if rng.random() < p["pH"] else 1
    t, out = 0.0, []
    while t < horizon:
        dur = rng.exponential(1 / rate[s])
        dur = min(dur, horizon - t)
        n = rng.poisson(lam[s] * dur)
        if n:
            out.append(t + np.sort(rng.random(n)) * dur)
        t += dur
        s = 1 - s
    return np.concatenate(out)


def gen_poisson(lbar, horizon, rng):
    n = rng.poisson(lbar * horizon)
    return np.sort(rng.random(n) * horizon)


# ---------------------------------------------------------------- queue simulation
def sim_queue(arr, svc, c):
    free = [0.0] * c
    heapq.heapify(free)
    wait = np.empty(len(arr))
    push, pop = heapq.heapreplace, None
    for i in range(len(arr)):
        f = free[0]
        a = arr[i]
        st = f if f > a else a
        wait[i] = st - a
        heapq.heapreplace(free, st + svc[i])
    return wait


def summarize(wait, tau, warm=0.05):
    w = wait[int(len(wait) * warm):]
    return w.mean(), (w > tau).mean()


def svc_sampler(kind, mean, rng, base=None):
    if kind == "exp":
        return lambda n: rng.exponential(mean, n)
    if kind.startswith("logn"):
        cs2 = float(kind[4:])
        s2 = math.log(1 + cs2)
        mu = math.log(mean) - s2 / 2
        return lambda n: rng.lognormal(mu, math.sqrt(s2), n)
    if kind == "trace":
        return lambda n: rng.choice(base, n)
    raise ValueError(kind)


def servers_needed(arr_fn, svc_fn, lbar, mean_s, tau, eps, reps, rng):
    ok = lambda c: np.mean([(sim_queue(a, svc_fn(len(a)), c)[len(a) // 20:] > tau).mean()
                            for a in reps]) <= eps
    lo = int(math.ceil(lbar * mean_s))
    hi = lo + 1
    while not ok(hi):
        lo, hi = hi, 2 * hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def analyse(name, path, md, rng, horizon_scale=20):
    t, ctx, gen = load(path)
    svc_trace = PREFILL_S_PER_TOK * ctx + DECODE_S_PER_TOK * gen
    lbar = len(t) / t[-1]
    ia = np.diff(t)
    mean_s = svc_trace.mean()
    cs2 = svc_trace.var() / mean_s ** 2
    md.append(f"## {name}\n")
    md.append(f"{len(t)} requests over {t[-1]:.0f}s: mean rate {lbar:.2f}/s, inter-arrival CV^2 = "
              f"{ia.var() / ia.mean() ** 2:.2f} (Poisson: 1), mean service {mean_s:.2f}s, "
              f"service-time cs^2 = {cs2:.2f} (exponential: 1), offered load {lbar * mean_s:.1f} servers.\n")
    wins = [1, 2, 5, 10, 30, 60, 120, 300]
    idc = idc_curve(t, wins)
    p = fit_mmpp2(lbar, idc)
    rows = [[w, f"{idc[w]:.2f}", f"{idc_mmpp2(w, lbar, p['pH'], p['lH'] - p['lL'], p['rHL'] + p['rLH']):.2f}"]
            for w in idc]
    md.append("### A/B  Arrival burstiness and MMPP(2) fit\n")
    md.append(table(rows, ["window (s)", "IDC trace (Poisson = 1)", "IDC fitted MMPP(2)"]))
    md.append(f"\nFitted MMPP(2): burst rate {p['lH']:.2f}/s ({p['lH'] / lbar:.1f}x mean) for {100 * p['pH']:.0f}% "
              f"of time, mean burst {1 / p['rHL']:.1f}s; off rate {p['lL']:.2f}/s.\n")

    # --- C validation (trace replay vs Poisson vs fitted MMPP) at several loads
    md.append("### C  Replay vs. models (service times from tokens; tau = one mean service time)\n")
    tau = mean_s
    horizon = t[-1] * horizon_scale
    rows = []
    for rho in (0.6, 0.75, 0.85, 0.92):
        c = int(math.ceil(lbar * mean_s / rho))
        r_real = summarize(sim_queue(t, svc_trace, c), tau)
        rp, rm = [], []
        for _ in range(3):
            ap = gen_poisson(lbar, horizon, rng)
            sp = rng.choice(svc_trace, len(ap))
            rp.append(summarize(sim_queue(ap, sp, c), tau))
            am = gen_mmpp(p, horizon, rng)
            sm = rng.choice(svc_trace, len(am))
            rm.append(summarize(sim_queue(am, sm, c), tau))
        rp, rm = np.mean(rp, axis=0), np.mean(rm, axis=0)
        rows.append([f"{lbar * mean_s / c:.2f}", c,
                     f"{r_real[0]:.2f} / {r_real[1]:.3f}", f"{rm[0]:.2f} / {rm[1]:.3f}", f"{rp[0]:.2f} / {rp[1]:.3f}"])
    md.append(table(rows, ["rho", "c", "real trace: E[wait] / P(wait>tau)", "fitted MMPP", "Poisson"]))
    md.append("\n(real trace = one 1-hour path; models = mean of 3 long paths of the same rate)\n")

    # --- D service-time sensitivity
    md.append("### D  Service-time sensitivity (fitted MMPP vs Poisson; tau = one mean service time)\n")
    rho = 0.8
    c = int(math.ceil(lbar * mean_s / rho))
    rows = []
    for kind in ("exp", "logn4", "logn16", "trace"):
        sf = svc_sampler(kind, mean_s, rng, base=svc_trace)
        res = {}
        for lab, fn in (("Poisson", lambda: gen_poisson(lbar, horizon, rng)),
                        ("MMPP", lambda: gen_mmpp(p, horizon, rng))):
            reps = [fn() for _ in range(2)]
            w = np.mean([summarize(sim_queue(a, sf(len(a)), c), tau) for a in reps], axis=0)
            res[lab] = (w, servers_needed(None, sf, lbar, mean_s, tau, 0.05, reps, rng))
        (wp, cp), (wm, cm) = res["Poisson"], res["MMPP"]
        rows.append([kind, f"{wp[0]:.2f} / {wp[1]:.3f}", f"{wm[0]:.2f} / {wm[1]:.3f}",
                     f"{wm[0] / max(wp[0], 1e-9):.1f}x", cp, cm, f"{100 * (cm - cp) / cp:.0f}%"])
    md.append(f"At c={c} servers (rho=0.8). Servers needed for P(wait>tau)<=5%.\n")
    md.append(table(rows, ["service", "Poisson: E[wait] / P>tau", "MMPP: E[wait] / P>tau", "delay ratio",
                           "c Poisson", "c MMPP", "extra"]))
    md.append("")


def crosscheck(md, rng):
    """Simulator vs exact CTMC (exponential service) -- rho=0.8, c=8, k=3, T=2 -> E[sojourn] = 2.91."""
    lbar, c = 6.4, 8
    pH, kappa, TH = 0.2, 3, 2
    lL = lbar / (pH * kappa + 1 - pH)
    p = dict(lH=kappa * lL, lL=lL, rHL=1 / TH, rLH=(1 / TH) * pH / (1 - pH), pH=pH)
    a = gen_mmpp(p, 400000 / lbar, rng)
    s = rng.exponential(1.0, len(a))
    w = sim_queue(a, s, c)[len(a) // 20:]
    md.append("## X  Simulator cross-check\n")
    md.append(f"MMPP(k=3,T=2)/M/8 at rho=0.8: simulated E[sojourn] = {w.mean() + 1:.2f} "
              f"(exact CTMC in results/mmpp_serving.md: 2.91).\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="results/trace_calibration.md")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    md = ["# Calibration on the Azure LLM inference trace and non-exponential service times\n"]
    crosscheck(md, rng)
    print("\n".join(md), flush=True)
    for name, f in (("Conversation trace", "AzureLLMInferenceTrace_conv.csv"),
                    ("Code trace", "AzureLLMInferenceTrace_code.csv")):
        analyse(name, os.path.join(a.data, f), md, rng)
        print(md[-1][:0], flush=True)
    text = "\n".join(md)
    print(text)
    with open(a.out, "w") as fh:
        fh.write(text)


if __name__ == "__main__":
    main()
