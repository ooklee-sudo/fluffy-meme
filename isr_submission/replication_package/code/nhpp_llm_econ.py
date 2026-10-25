"""Hierarchical NHPP (Goel-Okumoto) + count regression + testing-economics layer.

Pipeline: simulate paired (human vs LLM-assisted) test campaigns -> fit Poisson and
NegBin hierarchical models in PyMC -> check parameter recovery -> derive the
cost-minimising testing budget T* and the economic value of LLM adoption from the
posterior.

Run: python3 nhpp_llm_econ.py
"""
import numpy as np
import pymc as pm
import arviz as az

RNG = np.random.default_rng(42)

# ---------------------------------------------------------------- simulation
P, K, DT = 30, 20, 1.0                      # projects, intervals, budget units per interval
TRUE = dict(b0=3.0, b_llm=-0.10, b_cx=0.20, b_int=0.15,       # log a (total detectable faults)
            g0=np.log(0.12), g_llm=0.45, g_cx=-0.10,           # log b (discovery rate)
            s_u=0.30, s_v=0.20, alpha=6.0)                     # RE sds, NB dispersion
C_F = 3.0                                    # cost of a residual (field) fault
C_T = {0: 1.0, 1: 1.3}                       # cost per budget unit: human, LLM (incl. tokens)


def simulate():
    cx = RNG.normal(size=P)
    u = RNG.normal(0, TRUE["s_u"], P)
    v = RNG.normal(0, TRUE["s_v"], P)
    proj, llm, Y = [], [], []
    t = np.arange(K + 1) * DT
    for i in range(P):
        for L in (0, 1):                      # within-project paired design
            la = TRUE["b0"] + TRUE["b_llm"] * L + TRUE["b_cx"] * cx[i] + TRUE["b_int"] * L * cx[i] + u[i]
            lb = TRUE["g0"] + TRUE["g_llm"] * L + TRUE["g_cx"] * cx[i] + v[i]
            a, b = np.exp(la), np.exp(lb)
            dm = a * (np.exp(-b * t[:-1]) - np.exp(-b * t[1:]))   # expected increments
            lam = RNG.gamma(TRUE["alpha"], dm / TRUE["alpha"])      # gamma-Poisson = NB
            Y.append(RNG.poisson(lam)); proj.append(i); llm.append(L)
    return cx, np.array(proj), np.array(llm), np.array(Y), t


# --------------------------------------------------------------------- model
def build(cx, proj, llm, Y, t, negbin):
    with pm.Model() as m:
        b0 = pm.Normal("b0", 3, 1.5); b_llm = pm.Normal("b_llm", 0, 0.5)
        b_cx = pm.Normal("b_cx", 0, 0.5); b_int = pm.Normal("b_int", 0, 0.5)
        g0 = pm.Normal("g0", -2, 1); g_llm = pm.Normal("g_llm", 0, 0.5); g_cx = pm.Normal("g_cx", 0, 0.5)
        s_u = pm.HalfNormal("s_u", 0.5); s_v = pm.HalfNormal("s_v", 0.5)
        # non-centred random effects
        u = pm.Normal("u", 0, 1, shape=P) * s_u
        v = pm.Normal("v", 0, 1, shape=P) * s_v
        x = cx[proj]
        a = pm.math.exp(b0 + b_llm * llm + b_cx * x + b_int * llm * x + u[proj])
        b = pm.math.exp(g0 + g_llm * llm + g_cx * x + v[proj])
        tt = t[None, :]
        mval = a[:, None] * (1 - pm.math.exp(-b[:, None] * tt))       # Goel-Okumoto m(t)
        dm = mval[:, 1:] - mval[:, :-1]
        if negbin:
            alpha = pm.Gamma("alpha", 2, 0.2)
            pm.NegativeBinomial("y", mu=dm + 1e-9, alpha=alpha, observed=Y)
        else:
            pm.Poisson("y", mu=dm + 1e-9, observed=Y)
    return m


# ------------------------------------------------------------------ economics
# Residual faults after testing T: (N - a) unreachable + a*exp(-bT) reachable, N = system fault pool.
# C(T) = ct*T + cf*[(N - a) + a*exp(-bT)].  N is common to both arms and cancels in any
# comparison, so we report cost net of cf*N:  ct*T + cf*a*(exp(-bT) - 1).
def t_star(a, b, ct, cf=C_F):
    """Minimise C(T)  ->  T*=max(0, ln(a b cf/ct)/b)   (reach term does not affect T*)."""
    return np.maximum(0.0, np.log(a * b * cf / ct) / b)


def cost(T, a, b, ct, cf=C_F):
    return ct * T + cf * a * (np.exp(-b * T) - 1.0)


def params(draws, cx0):
    """(a, b) per arm from a dict-like of parameter draws (or true values)."""
    a = {L: np.exp(draws["b0"] + draws["b_llm"] * L + (draws["b_cx"] + draws["b_int"] * L) * cx0) for L in (0, 1)}
    b = {L: np.exp(draws["g0"] + draws["g_llm"] * L + draws["g_cx"] * cx0) for L in (0, 1)}
    return a, b


def evaluate(a, b, cf=C_F, ct=C_T):
    Ts = {L: t_star(a[L], b[L], ct[L], cf) for L in (0, 1)}
    Cs = {L: cost(Ts[L], a[L], b[L], ct[L], cf) for L in (0, 1)}
    # regret of planning an LLM campaign with human-campaign parameters
    T_wrong = t_star(a[0], b[0], ct[1], cf)
    regret = cost(T_wrong, a[1], b[1], ct[1], cf) - Cs[1]
    return Ts, Cs, regret


def economics(post, cx0=0.0, cf=C_F, ct=C_T):
    """Posterior of T*, minimal cost, and value of LLM adoption for a project with complexity cx0."""
    s = post.to_dataset().stack(s=("chain", "draw"))
    draws = {k: s[k].values for k in ("b0", "b_llm", "b_cx", "b_int", "g0", "g_llm", "g_cx")}
    return evaluate(*params(draws, cx0), cf=cf, ct=ct)


def truth(cx0=0.0, cf=C_F, ct=C_T):
    return evaluate(*params(TRUE, cx0), cf=cf, ct=ct)[:2]


def summ(x):
    lo, hi = np.percentile(x, [5.5, 94.5])
    return f"{np.mean(x):7.2f} [{lo:6.2f}, {hi:6.2f}]"


if __name__ == "__main__":
    cx, proj, llm, Y, t = simulate()
    print(f"simulated {len(Y)} campaigns, mean total found = {Y.sum(1).mean():.1f}")
    print(f"var/mean of interval counts = {Y.var() / Y.mean():.2f}  (>1 => overdispersion)")

    fits = {}
    for name, nb in (("poisson", False), ("negbin", True)):
        m = build(cx, proj, llm, Y, t, nb)
        with m:
            idata = pm.sample(1000, tune=1500, chains=4, cores=4, target_accept=0.9,
                              random_seed=1, progressbar=False)
            pm.compute_log_likelihood(idata)
        fits[name] = idata
        div = int(idata.sample_stats["diverging"].sum())
        print(f"\n=== {name}: divergences={div}")

    # parameter recovery (NegBin = data-generating family)
    idata = fits["negbin"]
    keys = ["b0", "b_llm", "b_cx", "b_int", "g0", "g_llm", "g_cx", "s_u", "s_v", "alpha"]
    summary = az.summary(idata, var_names=keys, ci_prob=0.89)
    print("\nParameter recovery (negbin):")
    print(f"{'param':7s}{'true':>8s}{'post.mean':>10s}{'89% interval':>20s}{'rhat':>7s}{'ess':>7s}  covered")
    for k in keys:
        r = summary.loc[k]
        lo, hi = r['eti89_lb'], r['eti89_ub']
        tv = TRUE[k]
        print(f"{k:7s}{tv:8.3f}{r['mean']:10.3f}   [{lo:6.3f},{hi:6.3f}]{r['r_hat']:7.2f}{r['ess_bulk']:7.0f}  {lo <= tv <= hi}")

    # model comparison: Poisson vs NegBin
    cmp = az.compare(fits)
    print("\nLOO comparison (higher elpd = better):")
    print(cmp[["rank", "elpd", "p", "elpd_diff", "dse", "weight"]].round(2))

    # economics
    for cx0 in (-1.0, 0.0, 1.0):
        Ts, Cs, regret = economics(idata.posterior, cx0)
        tT, tC = truth(cx0)
        print(f"\n--- Economic layer, complexity cx={cx0:+.0f} (C_F={C_F}, c_t human={C_T[0]}, LLM={C_T[1]})")
        print(f"T* human   post {summ(Ts[0])}   true {tT[0]:.2f}")
        print(f"T* LLM     post {summ(Ts[1])}   true {tT[1]:.2f}")
        val = Cs[0] - Cs[1]
        print(f"Adoption value (C*_h - C*_LLM) post {summ(val)}   true {tC[0] - tC[1]:.2f}")
        print(f"P(adoption value > 0) = {(val > 0).mean():.2f}")
        print(f"Regret of using human params for LLM campaign: {summ(regret)}")
