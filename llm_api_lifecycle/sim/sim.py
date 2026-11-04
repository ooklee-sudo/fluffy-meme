"""Re-implementation of the 36-month LLM maintenance simulation described in the manuscript."""
import numpy as np

RATE = 91.5 * 40          # USD per person-week
def theta_of(sigma, r_m):
    # positive root of 0.5*s^2*b*(b-1) - r = 0 ; theta = b/(b-1)
    a = 0.5 * sigma**2
    b = (a + np.sqrt(a * a + 4 * a * r_m)) / (2 * a)
    return b / (b - 1)

def simulate(lifetimes, notices, ratios, N=20000, seed=1, H=36.0, dt=0.25,
             c=0.5, sigma=0.10, p0=1.25, vol_Mtok=1000.0, phi=0.5,
             premium_pw=6.0, tri=(2, 4, 10), surcharge=0.5, outage_usd=2000.0,
             r_annual=0.10, price_shock=True, interval_mode="fresh_aged",
             strategies=("rigid", "flex", "flex_npv", "flex_thr"), check_every=1.0):
    rng = np.random.default_rng(seed)
    lifetimes = np.asarray(lifetimes, float); notices = np.asarray(notices, float)
    ratios = np.asarray(ratios, float)
    r_m = r_annual / 12
    disc = lambda t: (1 + r_annual) ** (-t / 12)
    steps = int(round(H / dt))
    # ---- common random numbers ----
    maxR = 40
    L = rng.choice(lifetimes, (N, maxR)); U = rng.random((N, maxR))
    if interval_mode == "fresh_aged":
        iv = L * (1 - U)
    elif interval_mode == "fresh":
        iv = L.copy(); iv[:, 0] = L[:, 0] * (1 - U[:, 0])
    elif interval_mode == "same":
        iv = np.repeat(L[:, :1], maxR, 1); iv[:, 0] = L[:, 0] * (1 - U[:, 0])
    rt = np.cumsum(iv, 1)                                   # retirement times
    nt = rng.choice(notices, (N, maxR))                     # notice days
    R1 = rng.choice(ratios, (N, maxR)); same = rng.random((N, maxR)) < c
    R2 = np.where(same, R1, rng.choice(ratios, (N, maxR)))
    if not price_shock: R1[:] = 1; R2[:] = 1
    K = rng.triangular(*tri, (N, maxR))                     # effort at retirement k
    Ksw = rng.triangular(*tri, (N, 200))                    # effort for early switches
    zA = rng.standard_normal((N, steps)); zB = c * zA + np.sqrt(1 - c * c) * rng.standard_normal((N, steps))
    s = sigma * np.sqrt(dt)
    EK = sum(tri) / 3
    thr = theta_of(sigma, r_m)
    out = {}
    for strat in strategies:
        flex = strat != "rigid"
        f = phi if flex else 1.0
        pA = np.full(N, p0); pB = np.full(N, p0)
        v = np.zeros(N, int)
        cost_tok = np.zeros(N); cost_mig = np.zeros(N); cost_out = np.zeros(N)
        nxt = np.zeros(N, int); nmig = np.zeros(N); nsw = np.zeros(N, int)
        idx = np.arange(N)
        for k in range(steps):
            t0, t1 = k * dt, (k + 1) * dt
            # token spend over the step at current vendor price
            p = np.where(v == 0, pA, pB)
            cost_tok += p * vol_Mtok * dt * disc(t0 + dt / 2)
            # price walks
            pA *= np.exp(s * zA[:, k]); pB *= np.exp(s * zB[:, k])
            # retirements in (t0, t1]
            while True:
                j = nxt
                m = rt[idx, j] <= t1
                if not m.any(): break
                ii = idx[m]; jj = j[m]
                e = f * K[ii, jj]
                need = 10 * e                                   # calendar days
                short = nt[ii, jj] < need
                lab = e * RATE * np.where(short, 1 + surcharge, 1.0)
                outd = np.where(short, need - nt[ii, jj], 0.0)
                d = disc(rt[ii, jj])
                cost_mig[ii] += lab * d; cost_out[ii] += outd * outage_usd * d
                pA[ii] *= R1[ii, jj]; pB[ii] *= R2[ii, jj]
                if flex:
                    v[ii] = np.where(pB[ii] < pA[ii], 1, 0)
                nmig[ii] += 1; nxt[ii] += 1
            # early switching, checked every `check_every` months
            if strat in ("flex_npv", "flex_thr") and abs((t1 / check_every) - round(t1 / check_every)) < 1e-9 and t1 < H:
                rem = H - t1
                ann = sum(disc(t1 + u + 0.5) for u in range(int(np.ceil(rem)))) / disc(0)
                pc = np.where(v == 0, pA, pB); po = np.where(v == 0, pB, pA)
                pv = (pc - po) * vol_Mtok * ann
                C = phi * EK * RATE * disc(t1)
                trig = pv > (C if strat == "flex_npv" else thr * C)
                ii = idx[trig]
                if ii.size:
                    cost_mig[ii] += phi * Ksw[ii, np.minimum(nsw[ii], 199)] * RATE * disc(t1)
                    nsw[ii] += 1; v[ii] = 1 - v[ii]
        prem = premium_pw * RATE if flex else 0.0
        out[strat] = dict(total=cost_tok + cost_mig + cost_out + prem, tok=cost_tok, mig=cost_mig,
                          out=cost_out, prem=prem, nmig=nmig, nsw=nsw)
    out["theta"] = thr
    return out

def summarize(out, B=1000, seed=7):
    rng = np.random.default_rng(seed)
    rig = out["rigid"]["total"]; N = rig.size
    res = {"rigid_mean": rig.mean(), "migrations": out["rigid"]["nmig"].mean(), "theta": out["theta"]}
    bi = rng.integers(0, N, (B, N))
    for s in [k for k in out if k not in ("rigid", "theta")]:
        x = out[s]["total"]
        sav = 1 - x.mean() / rig.mean()
        bs = 1 - x[bi].mean(1) / rig[bi].mean(1)
        res[s] = dict(saving=100 * sav, ci=(100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5)),
                      mean=x.mean(), switches=out[s]["nsw"].mean())
        if s == "flex":
            d = (rig - (x - out[s]["prem"])) / RATE
            se = d.std(ddof=1) / np.sqrt(N)
            res[s]["breakeven_pw"] = d.mean(); res[s]["be_ci"] = (d.mean() - 1.96 * se, d.mean() + 1.96 * se)
    return res
