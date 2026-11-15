"""
Numerical checks for the distribution-free offsetting result.

Claims checked
--------------
(P1) For any mixture-of-exponentials detection technology S(e) = E[exp(-rho e)],
     the hazard is the survivor mean and its slope is minus the survivor variance:
         h(e) = E_e[rho],   h'(e) = -Var_e[rho].
(P2) Hence the elasticity of expected residual defects w.r.t. defect intensity is
         eps = (g + V/m) / (g + E2/m),   g = C''/C', m = E_e[rho], V = Var_e[rho], E2 = E_e[rho^2]
     and with linear cost eps = CV^2 / (1 + CV^2), CV computed among survivors at e*.
(P3) If the density of rho behaves like rho^(k-1) near zero, eps(e) -> 1/(1+k) as e -> inf;
     if rho is bounded away from zero, eps(e) -> 0.
(P4) If a better tool also scales detectability, rho = theta * xi with theta ∝ lambda^eta,
     then (linear cost) d ln R*/d ln lambda = eps - eta (1 - eps); residual defects fall
     with tool quality iff eta < eps/(1-eps) = CV^2.
(P5) Agent-level Monte Carlo of Poisson defects + independent detection reproduces R*.

Run:  python3 sim_cv_elasticity.py      (writes results/ next to this file)
"""
import json
import os

import numpy as np
from scipy import integrate, optimize, stats

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261115)


# ---------------------------------------------------------------------------
# Detectability distributions (all with mean 1, so theta = 1 is the scale)
# ---------------------------------------------------------------------------
class Continuous:
    def __init__(self, name, dist, k_zero):
        self.name, self.dist, self.k_zero = name, dist, k_zero

    def moments(self, e):
        """Return E[rho^j exp(-rho e)] for j = 0, 1, 2, integrating over quantiles
        on a log scale so that singular densities and large e are handled well."""
        out = []
        for j in range(3):
            def f(t):
                u = np.exp(t)
                r = self.dist.ppf(u)
                return r**j * np.exp(-r * e) * u
            val, _ = integrate.quad(f, -700.0, 0.0, limit=800, epsabs=0, epsrel=1e-11)
            out.append(val)
        return np.array(out)

    def sample(self, n):
        return self.dist.rvs(size=n, random_state=rng)


class Discrete:
    def __init__(self, name, values, probs):
        self.name = name
        self.v, self.p = np.asarray(values, float), np.asarray(probs, float)
        self.k_zero = None

    def moments(self, e):
        w = self.p * np.exp(-self.v * e)
        return np.array([w.sum(), (w * self.v).sum(), (w * self.v**2).sum()])

    def sample(self, n):
        return rng.choice(self.v, size=n, p=self.p)


K_HAT = 0.63
DISTS = [
    Continuous("gamma k=0.63", stats.gamma(a=K_HAT, scale=1 / K_HAT), K_HAT),
    Continuous("gamma k=2", stats.gamma(a=2.0, scale=0.5), 2.0),
    Continuous("scaled beta(0.63, 1.89) on [0,4]", stats.beta(K_HAT, 3 * K_HAT, scale=4.0), K_HAT),
    Continuous("uniform on [0,2]", stats.uniform(0.0, 2.0), 1.0),
    Continuous("lognormal sigma=1", stats.lognorm(s=1.0, scale=np.exp(-0.5)), np.inf),
    Discrete("two-point {0.2, 1.8}", [0.2, 1.8], [0.5, 0.5]),
]


def survivor_stats(d, e):
    m0, m1, m2 = d.moments(e)
    mean = m1 / m0
    e2 = m2 / m0
    return dict(S=m0, h=mean, var=e2 - mean**2, E2=e2, cv2=(e2 - mean**2) / mean**2)


# ---------------------------------------------------------------------------
# Developer problem: min_e C(e) + B * lambda * S(e),  B = delta * l * s
# Linear cost C = c e; convex cost C = c e^gamma / gamma.
# FOC: C'(e) = B lambda E[rho exp(-rho e)]
# ---------------------------------------------------------------------------
def solve_effort(d, lam, B, c=1.0, gamma=1.0):
    def foc(e):
        cp = c * e ** (gamma - 1.0) if gamma != 1.0 else c
        return cp - B * lam * d.moments(e)[1]
    lo, hi = 1e-9, 1.0
    while foc(hi) < 0:
        hi *= 2.0
        if hi > 1e7:
            raise RuntimeError("no interior optimum")
    return optimize.brentq(foc, lo, hi, xtol=1e-13, rtol=1e-13)


def residual(d, lam, B, s=1.0, **kw):
    e = solve_effort(d, lam, B, **kw)
    return lam * s * d.moments(e)[0], e


def numeric_elasticity(d, lam, B, step=1e-4, **kw):
    rp, _ = residual(d, lam * np.exp(step), B, **kw)
    rm, _ = residual(d, lam * np.exp(-step), B, **kw)
    return (np.log(rp) - np.log(rm)) / (2 * step)


def formula_elasticity(d, e, gamma=1.0):
    st = survivor_stats(d, e)
    g = (gamma - 1.0) / e
    return (g + st["var"] / st["h"]) / (g + st["E2"] / st["h"]), st


# ---------------------------------------------------------------------------
# (P1) hazard identities, by finite differences of ln S
# ---------------------------------------------------------------------------
def check_p1():
    rows = []
    for d in DISTS:
        for e in [0.5, 3.0, 20.0]:
            dh = 1e-4 * max(e, 1)
            lnS = lambda x: np.log(d.moments(x)[0])
            h_fd = -(lnS(e + dh) - lnS(e - dh)) / (2 * dh)
            hfun = lambda x: survivor_stats(d, x)["h"]
            hp_fd = (hfun(e + dh) - hfun(e - dh)) / (2 * dh)
            st = survivor_stats(d, e)
            rows.append(dict(dist=d.name, e=e, h_fd=h_fd, h_formula=st["h"],
                             hprime_fd=hp_fd, minus_var=-st["var"]))
    return rows


# ---------------------------------------------------------------------------
# (P2) elasticity formula vs numerical comparative statics
# ---------------------------------------------------------------------------
def check_p2():
    rows = []
    for d in DISTS:
        for gamma in [1.0, 1.5, 2.5]:
            for B in [5.0, 50.0, 500.0]:
                lam = 1.0
                try:
                    _, e = residual(d, lam, B, gamma=gamma)
                except RuntimeError:
                    continue
                eps_num = numeric_elasticity(d, lam, B, gamma=gamma)
                eps_f, st = formula_elasticity(d, e, gamma=gamma)
                rows.append(dict(dist=d.name, gamma=gamma, B=B, e_star=e,
                                 cv2_survivors=st["cv2"],
                                 eps_numeric=eps_num, eps_formula=eps_f,
                                 eps_cv_linear=st["cv2"] / (1 + st["cv2"]) if gamma == 1.0 else None,
                                 abs_err=abs(eps_num - eps_f)))
    return rows


# ---------------------------------------------------------------------------
# (P3) large-effort limit of eps(e) under linear cost
# ---------------------------------------------------------------------------
def check_p3():
    grid = np.logspace(-2, 3, 41)
    curves = {}
    for d in DISTS:
        eps = []
        for e in grid:
            st = survivor_stats(d, e)
            eps.append(st["cv2"] / (1 + st["cv2"]))
        lim = None
        if d.k_zero is not None and np.isfinite(d.k_zero):
            lim = 1 / (1 + d.k_zero)
        elif d.k_zero is not None:
            lim = 0.0
        curves[d.name] = dict(e=grid.tolist(), eps=eps, predicted_limit=lim)
    return curves


# ---------------------------------------------------------------------------
# (P4) quality that also changes detectability: rho = theta * xi, theta = lambda^eta
# ---------------------------------------------------------------------------
class Scaled:
    """rho = theta * xi; moments in e follow from the base distribution at theta*e."""
    def __init__(self, base, theta):
        self.base, self.theta, self.name = base, theta, base.name
    def moments(self, e):
        m = self.base.moments(self.theta * e)
        return np.array([m[0], self.theta * m[1], self.theta**2 * m[2]])


def check_p4():
    rows = []
    B = 50.0
    for d in [DISTS[0], DISTS[4], DISTS[5]]:
        _, e0 = residual(d, 1.0, B)
        eps0, st0 = formula_elasticity(d, e0)
        for eta in [0.0, 0.5, 1.0, st0["cv2"], 2.0, 3.0]:
            step = 1e-4
            def lnR(lnlam):
                lam = np.exp(lnlam)
                ds = Scaled(d, lam**eta)
                return np.log(residual(ds, lam, B)[0])
            total = (lnR(step) - lnR(-step)) / (2 * step)
            rows.append(dict(dist=d.name, eta=eta, eps=eps0, cv2=st0["cv2"],
                             total_numeric=total, total_formula=eps0 - eta * (1 - eps0),
                             threshold_eta=st0["cv2"]))
    return rows


# ---------------------------------------------------------------------------
# (P5) agent-level Monte Carlo
# ---------------------------------------------------------------------------
def check_p5(reps=40000, lam_s=40.0):
    rows = []
    B = 50.0
    for d in [DISTS[0], DISTS[4], DISTS[5]]:
        out = {}
        for lam in [1.0, 0.8]:
            _, e = residual(d, lam, B)
            n = rng.poisson(lam * lam_s, size=reps)
            tot = n.sum()
            rho = d.sample(tot)
            survive = rng.random(tot) < np.exp(-rho * e)
            idx = np.repeat(np.arange(reps), n)
            r = np.bincount(idx, weights=survive, minlength=reps)
            out[lam] = dict(e=e, mc_mean=r.mean(), mc_se=r.std(ddof=1) / np.sqrt(reps),
                            analytic=lam * lam_s * d.moments(e)[0],
                            mc_var_over_mean=r.var(ddof=1) / r.mean())
        arc_mc = np.log(out[1.0]["mc_mean"] / out[0.8]["mc_mean"]) / np.log(1 / 0.8)
        arc_an = np.log(out[1.0]["analytic"] / out[0.8]["analytic"]) / np.log(1 / 0.8)
        rows.append(dict(dist=d.name, lam1=out[1.0], lam08=out[0.8],
                         arc_elasticity_mc=arc_mc, arc_elasticity_analytic=arc_an))
    return rows


def main():
    res = dict(P1=check_p1(), P2=check_p2(), P3=check_p3(), P4=check_p4(), P5=check_p5())
    with open(os.path.join(OUT, "cv_elasticity_checks.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)

    print("== P1: h = survivor mean, h' = -survivor variance ==")
    print(f"max |h_fd - h|      = {max(abs(r['h_fd']-r['h_formula']) for r in res['P1']):.2e}")
    print(f"max |h'_fd + Var|   = {max(abs(r['hprime_fd']-r['minus_var']) for r in res['P1']):.2e}")

    print("\n== P2: elasticity formula vs numerical comparative statics ==")
    print(f"{'distribution':34s} {'gam':>4s} {'B':>5s} {'e*':>8s} {'CV2':>7s} {'eps_num':>8s} {'eps_form':>8s}")
    for r in res["P2"]:
        print(f"{r['dist']:34s} {r['gamma']:4.1f} {r['B']:5.0f} {r['e_star']:8.3f} "
              f"{r['cv2_survivors']:7.3f} {r['eps_numeric']:8.5f} {r['eps_formula']:8.5f}")
    print(f"max abs error = {max(r['abs_err'] for r in res['P2']):.2e}")

    print("\n== P3: eps(e) at e = 1e3 vs predicted limit (linear cost) ==")
    for name, c in res["P3"].items():
        print(f"{name:34s} eps(0.01)={c['eps'][0]:.3f} eps(10)={c['eps'][24]:.3f} "
              f"eps(1000)={c['eps'][-1]:.3f}  limit={c['predicted_limit']}")

    print("\n== P4: quality also scales detectability, theta ∝ lambda^eta ==")
    for r in res["P4"]:
        print(f"{r['dist']:22s} eta={r['eta']:5.2f}  dlnR/dlnlam num={r['total_numeric']:+.5f} "
              f"formula={r['total_formula']:+.5f}  (threshold eta*={r['threshold_eta']:.3f})")

    print("\n== P5: agent-level Monte Carlo ==")
    for r in res["P5"]:
        a, b = r["lam1"], r["lam08"]
        print(f"{r['dist']:22s} R(1): MC {a['mc_mean']:.4f}±{a['mc_se']:.4f} vs {a['analytic']:.4f}; "
              f"R(.8): MC {b['mc_mean']:.4f}±{b['mc_se']:.4f} vs {b['analytic']:.4f}; "
              f"arc eps MC {r['arc_elasticity_mc']:.3f} vs {r['arc_elasticity_analytic']:.3f}; "
              f"Var/Mean {a['mc_var_over_mean']:.3f}")

    # figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for name, c in res["P3"].items():
        line, = ax.semilogx(c["e"], c["eps"], label=name)
        if c["predicted_limit"] is not None:
            ax.axhline(c["predicted_limit"], color=line.get_color(), ls=":", lw=0.8)
    ax.set_xlabel("verification effort e (mean detection rate = 1)")
    ax.set_ylabel(r"$\varepsilon(e)=\mathrm{CV}_e^2/(1+\mathrm{CV}_e^2)$")
    ax.set_title("Elasticity of residual defects, linear cost; dotted = predicted limits")
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "eps_vs_effort.png"), dpi=200)


if __name__ == "__main__":
    main()
