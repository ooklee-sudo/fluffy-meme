"""Monopoly-owner model (Section 5, static limit sigma = g = 0): parameter grid and value distributions.

Checks, for many (b, psi, c, theta, rho) and several distributions F of adapter values v with the same mean:
  - Proposition 6:  d mu_V / dR > 0                  (strategic complementarity, 'for any F')
  - Proposition 5:  mu_V > mu_P  iff  E[s_mu(mu_V)] < 0   (over-release criterion)
  - Proposition 7c: mean enterprise surplus can fall as R rises
The owner maximizes  psi*mu - c*mu^2/2 + theta*n*(b*mu - E[m](mu)),  the planner the same with theta = 1,
where E[m](mu) = (mu C_N/rho) (1 - F(vh)) + (1-R) mu/(rho (rho+mu)) * int_0^vh v dF,  vh = C_N (rho+mu)/(1-R).

  python vendor_sensitivity.py            # writes results/sensitivity.json and results/sensitivity.png
  python vendor_sensitivity.py --check    # reproduces Tables 3 and 5 (static columns) only
"""
import argparse
import itertools
import json
import math
import os

import numpy as np
from scipy import special, stats

C_N = 1.0
N = 1.0
MEAN_V = 20.0  # mean of the paper's U[0, 40]


# ---- value distributions: (cdf, partial expectation  int_0^x v dF)  ----
def uniform(vbar=40.0):
    return (lambda x: np.clip(x / vbar, 0, 1),
            lambda x: np.where(x < vbar, x ** 2 / (2 * vbar), vbar / 2))


def gamma(k, mean=MEAN_V):
    th = mean / k
    return (lambda x: special.gammainc(k, x / th),
            lambda x: mean * special.gammainc(k + 1, x / th))


def lognormal(s, mean=MEAN_V):
    m = math.log(mean) - s * s / 2
    return (lambda x: stats.norm.cdf((np.log(np.maximum(x, 1e-300)) - m) / s),
            lambda x: mean * stats.norm.cdf((np.log(np.maximum(x, 1e-300)) - m - s * s) / s))


def pareto(a, mean=MEAN_V):
    xm = mean * (a - 1) / a
    def pe(x):
        x = np.maximum(x, xm)
        return a * xm ** a * (x ** (1 - a) - xm ** (1 - a)) / (1 - a)
    return (lambda x: np.where(x > xm, 1 - (xm / np.maximum(x, xm)) ** a, 0.0), pe)


DISTS = {"uniform [0,40]": uniform(), "exponential": gamma(1.0), "gamma k=3": gamma(3.0),
         "lognormal s=0.5": lognormal(0.5), "lognormal s=1.0": lognormal(1.0), "Pareto a=2.5": pareto(2.5)}

MU = np.concatenate([np.linspace(1e-3, 6, 1500), np.linspace(6, 30, 600)[1:]])


def Em(mu, R, rho, dist):
    cdf, pe = dist
    vh = C_N * (rho + mu) / (1 - R)
    return mu * C_N / rho * (1 - cdf(vh)) + (1 - R) * mu / (rho * (rho + mu)) * pe(vh)


def surplus_mean(mu, R, rho, b, dist):
    return b * mu - Em(mu, R, rho, dist)


def best(R, rho, b, psi, c, theta, dist):
    """Global maximizer on the grid, refined. Returns (mu, globally_concave, interior).

    globally_concave: the objective has nonpositive second divided differences on the whole grid, i.e. the
    hypothesis 'the planner's objective is concave' of Propositions 5 and 10 holds (and the owner's
    first-order condition identifies the maximizer)."""
    obj = psi * MU - c * MU ** 2 / 2 + theta * N * surplus_mean(MU, R, rho, b, dist)
    h1, h2 = np.diff(MU)[:-1], np.diff(MU)[1:]
    dd = 2 * ((obj[2:] - obj[1:-1]) / h2 - (obj[1:-1] - obj[:-2]) / h1) / (h1 + h2)
    concave = bool(dd.max() <= 1e-9)
    i = int(np.argmax(obj))
    if i == 0 or i == len(MU) - 1:
        return MU[i], concave, False
    lo, hi = MU[i - 1], MU[i + 1]
    f = lambda m: psi * m - c * m ** 2 / 2 + theta * N * surplus_mean(m, R, rho, b, dist)
    g = (math.sqrt(5) - 1) / 2
    a, d = lo, hi
    for _ in range(60):
        x1, x2 = d - g * (d - a), a + g * (d - a)
        if f(x1) > f(x2):
            d = x2
        else:
            a = x1
    return (a + d) / 2, concave, True


def s_mu(mu, R, rho, b, dist):  # d/dmu of mean surplus, central difference
    h = 1e-4 * max(mu, 1.0)
    return (surplus_mean(mu + h, R, rho, b, dist) - surplus_mean(mu - h, R, rho, b, dist)) / (2 * h)


def check():
    d = DISTS["uniform [0,40]"]
    print("Table 3/7 static columns  (rho=0.10, C_N=1, v~U[0,40], b=7, psi=6, c=2, theta=0.5, n=1)")
    print(f"{'R':>4} {'mu_V':>7} {'mu_P':>7}   paper(static): mu_V mu_P")
    ref = {0.3: (2.475, 1.837), 0.5: (2.579, 2.017), 0.7: (2.855, 2.607), 0.8: (3.295, 4.083)}
    for R, (rv, rp) in ref.items():
        mv = best(R, 0.10, 7, 6, 2, 0.5, d)[0]
        mp = best(R, 0.10, 7, 6, 2, 1.0, d)[0]
        print(f"{R:4.1f} {mv:7.3f} {mp:7.3f}   {rv:14.3f} {rp:6.3f}")


def grid():
    Rs = [0.1, 0.3, 0.5, 0.7, 0.8]
    axes = dict(rho=[0.05, 0.10, 0.20], b=[2, 4, 7, 10, 14], psi=[0, 3, 6, 9], c=[1, 2, 4], theta=[0.25, 0.5, 0.75])
    rows = []
    for name, dist in DISTS.items():
        for rho, b, psi, c, th in itertools.product(*axes.values()):
            mv = [best(R, rho, b, psi, c, th, dist) for R in Rs]
            mp = [best(R, rho, b, psi, c, 1.0, dist) for R in Rs]
            for j, R in enumerate(Rs):
                ok = mv[j][1] and mv[j][2] and mp[j][1] and mp[j][2]
                row = dict(dist=name, rho=rho, b=b, psi=psi, c=c, theta=th, R=R, mu_V=mv[j][0], mu_P=mp[j][0], valid=ok, conc_V=mv[j][1], conc_P=mp[j][1])
                if ok:
                    row["over"] = bool(mv[j][0] > mp[j][0] + 1e-6)
                    row["Es_mu"] = float(s_mu(mv[j][0], R, rho, b, dist))
                    tie = abs(mv[j][0] - mp[j][0]) < 1e-6 and abs(row["Es_mu"]) < 1e-6  # mu_V = mu_P and E[s_mu] = 0: the criterion is silent
                    row["crit_agrees"] = bool(tie or ((row["Es_mu"] < 0) == row["over"]))
                if ok and j + 1 < len(Rs) and mv[j + 1][1] and mv[j + 1][2]:
                    row["slope"] = (mv[j + 1][0] - mv[j][0]) / (Rs[j + 1] - Rs[j])
                rows.append(row)
    return rows


def summarize(rows):
    out = {}
    for name in DISTS:
        r = [x for x in rows if x["dist"] == name]
        v = [x for x in r if x["valid"]]
        sl = [x for x in v if "slope" in x]
        out[name] = dict(
            cases=len(r), valid=len(v),
            complementarity_holds=sum(x["slope"] > 1e-6 for x in sl), flat=sum(abs(x["slope"]) <= 1e-6 for x in sl), violations=sum(x["slope"] < -1e-6 for x in sl), slope_cases=len(sl),
            min_slope=min((x["slope"] for x in sl), default=None),
            invalid_nonconcave=sum(1 for x in r if not x['valid'] and not (x['conc_V'] and x['conc_P'])),
            invalid_corner=sum(1 for x in r if not x['valid'] and (x['conc_V'] and x['conc_P'])),
            over_release_share=sum(x["over"] for x in v) / max(len(v), 1),
            criterion_agrees=sum(x["crit_agrees"] for x in v), criterion_cases=len(v))
    return out


def plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    base = dict(rho=0.10, b=7, psi=6, c=2, theta=0.5)
    Rg = np.linspace(0.1, 0.85, 31)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for name, dist in DISTS.items():
        ax[0].plot(Rg, [best(R, base["rho"], base["b"], base["psi"], base["c"], base["theta"], dist)[0] for R in Rg], label=name)
    ax[0].set_xlabel("Recovery rate R"); ax[0].set_ylabel(r"Monopoly intensity $\mu_V$")
    ax[0].set_title("(a) Complementarity under six value distributions"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    bs = np.linspace(2, 14, 25)
    Z = np.zeros((len(bs), len(Rg)))
    d = DISTS["uniform [0,40]"]
    for i, b in enumerate(bs):
        for j, R in enumerate(Rg):
            mv = best(R, 0.10, b, 6, 2, 0.5, d)[0]; mp = best(R, 0.10, b, 6, 2, 1.0, d)[0]
            Z[i, j] = mv - mp
    im = ax[1].contourf(Rg, bs, Z, levels=np.linspace(-max(abs(Z.min()), Z.max()), max(abs(Z.min()), Z.max()), 21), cmap="RdBu_r")
    ax[1].contour(Rg, bs, Z, levels=[0], colors="k", linewidths=1.5)
    ax[1].axhline(10, color="grey", ls=":"); ax[1].text(0.11, 10.2, r"$b=C_N/\rho$", fontsize=8)
    ax[1].set_xlabel("Recovery rate R"); ax[1].set_ylabel(r"Value of a unit intensity $b$")
    ax[1].set_title(r"(b) Over-release ($\mu_V-\mu_P>0$, red) region, uniform $F$")
    fig.colorbar(im, ax=ax[1]); fig.tight_layout(); fig.savefig(path, dpi=200)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default="results/sensitivity.json"); ap.add_argument("--plot", default="results/sensitivity.png")
    a = ap.parse_args()
    check()
    if not a.check:
        rows = grid()
        s = summarize(rows)
        for k, v in s.items():
            print(f"{k:>16}: valid {v['valid']}/{v['cases']}  d mu/dR>0 in {v['complementarity_holds']}/{v['slope_cases']} (flat {v['flat']}) "
                  f"(min slope {v['min_slope']:.2g}, violations {v['violations']})  over-release share {v['over_release_share']:.2f}  "
                  f"Prop5 criterion agrees {v['criterion_agrees']}/{v['criterion_cases']}  invalid: nonconcave {v['invalid_nonconcave']}, corner {v['invalid_corner']}")
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump({"summary": s, "rows": rows}, open(a.out, "w"), default=lambda o: o.item())
        plot(rows, a.plot); print("saved", a.out, a.plot)
