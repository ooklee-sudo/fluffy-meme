"""Simulation-based power analysis for Study 2, refactoring module (see study2_protocol.md).

Model (paper, Section 4): with stated rework cost R and time cost c of improving the code, a developer improves iff
    choice (C, before any code exists):     v*c < delta*R                      -> threshold  tau_C = ln(c/delta)
    plan   (P, commit now for next week):   lam*v*c < delta*R   (naive plan)   -> threshold  tau_P = tau_C + ln(lam)
    accept (A, artifact in hand, decide):   lam*v*c < beta*delta*R             -> threshold  tau_A = tau_C + ln(lam) - ln(beta)
Observed decision: improve iff x + eps > tau, with x = ln(R/c) set by the design and eps ~ Logistic(0, s) response noise.
Identification:  ln(lam) = tau_P - tau_C ;  -ln(beta) = tau_A - tau_P ;  possession effect = tau_A - tau_C = ln(lam/beta).
"""
import numpy as np, statsmodels.api as sm, sys, time
rng = np.random.default_rng(2026)
X_GRID = np.array([-0.2, 0.3, 0.8, 1.3])      # ln(R/c) design points
REPS = 2                                       # repetitions of each design point per condition
S_NOISE = 0.5                                  # logistic response-noise scale
SD_TASTE, SD_BETA, SD_LAM = 0.4, 0.2, 0.2      # between-participant heterogeneity (log scale)
ATTRITION = 0.20                               # lose session 2 (condition A) for this share of participants

def simulate(n, beta, lam, rng, s_noise=None, random_resp=0.0, lam_in_plan=True):
    s_noise = S_NOISE if s_noise is None else s_noise
    ln_b = np.log(beta) + SD_BETA * rng.standard_normal(n) if beta < 1 else np.zeros(n)
    ln_l = np.log(lam) + SD_LAM * rng.standard_normal(n) if lam > 1 else np.zeros(n)
    taste = SD_TASTE * rng.standard_normal(n); tau_C = 0.05 + taste
    tau = {"C": tau_C, "P": tau_C + (ln_l if lam_in_plan else 0), "A": tau_C + ln_l - ln_b}
    rows = []
    x = np.tile(np.repeat(X_GRID, REPS), 1)
    keep_A = rng.random(n) > ATTRITION
    for cond in ("C", "P", "A"):
        for i in range(n):
            if cond == "A" and not keep_A[i]: continue
            eps = rng.logistic(0, s_noise, len(x))
            y = (x + eps > tau[cond][i]).astype(int)
            if random_resp: y = np.where(rng.random(len(x)) < random_resp, rng.integers(0, 2, len(x)), y)
            rows.append(np.column_stack([np.full(len(x), i), x, np.full(len(x), cond == "P"), np.full(len(x), cond == "A"), y]))
    return np.vstack(rows)

def analyse(d):
    X = sm.add_constant(d[:, [1, 2, 3]]); m = sm.Logit(d[:, 4], X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d[:, 0].astype(int)})
    b, gP, gA = m.params[1], m.params[2], m.params[3]
    # contrasts (thresholds shift = -gamma/b); delta method via the covariance matrix
    V = m.cov_params(); idx = [1, 2, 3]
    def contrast(grad):                      # grad over (b, gP, gA)
        return grad @ m.params[idx], np.sqrt(grad @ V[np.ix_(idx, idx)] @ grad)
    out = {}
    # ln(lam) = tau_P - tau_C = -gP/b ;  -ln(beta) = tau_A - tau_P = -(gA - gP)/b ;  ln(lam/beta) = -gA/b
    for name, g in (("ln_lam", lambda b, gP, gA: -gP / b), ("neg_ln_beta", lambda b, gP, gA: -(gA - gP) / b), ("possession", lambda b, gP, gA: -gA / b)):
        h = 1e-5; p0 = np.array([b, gP, gA]); val = g(*p0)
        grad = np.array([(g(*(p0 + h * np.eye(3)[k])) - g(*(p0 - h * np.eye(3)[k]))) / (2 * h) for k in range(3)])
        est, se = contrast(grad)
        out[name] = (val, se)
    return out

SCEN = {"rational (beta=1, lam=1)": dict(be=1.0, la=1.0),
        "both (beta=.7, lam=1.5)": dict(be=0.7, la=1.5),
        "mild (beta=.85, lam=1.2)": dict(be=0.85, la=1.2),
        "[caveat] beta=1, lam=1.5, plan ignores lam": dict(be=1.0, la=1.5, lam_in_plan=False)}
COND = {"baseline (s=0.5, no random)": dict(), "noisier (s=0.9, 15% random responders)": dict(s_noise=0.9, random_resp=0.15)}
NS = [120, 160, 240, 320]; SIMS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
print(f"{SIMS} simulated experiments per cell; 24 decisions per participant; 20% attrition in session 2")
print("power = share of simulations with a significant (|z|>1.96) estimate of the correct sign (for rational/caveat rows: false-positive rate)\n")
t0 = time.time()
for cname, cond in COND.items():
    print(f"=== {cname}")
    print(f"{'scenario':46s}{'N':>5s}  {'possession>0':>13s}{'ln(lam)>0':>11s}{'-ln(beta)>0':>13s}")
    for sc, kw in SCEN.items():
        be, la = kw["be"], kw["la"]; extra = {k: v for k, v in kw.items() if k not in ("be", "la")}
        for n in NS:
            hit = {"possession": 0, "ln_lam": 0, "neg_ln_beta": 0}; tot = 0
            for _ in range(SIMS):
                try: r = analyse(simulate(n, be, la, rng, **cond, **extra))
                except Exception: continue
                tot += 1
                for k in hit:
                    v, se = r[k]; hit[k] += (v / se > 1.96)
            print(f"{sc:46s}{n:5d}  {hit['possession']/tot:13.2f}{hit['ln_lam']/tot:11.2f}{hit['neg_ln_beta']/tot:13.2f}")
    print()
print(f"(elapsed {time.time()-t0:.0f}s)")
