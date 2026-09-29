"""Numerical analysis for Proposition 4 (delay length vs. delay cost). Writes p4_stats.json and fig1.png."""
import json, math
import numpy as np

RHO, MU, K, SK, LAM = 0.25, 0.15, 1.0, 0.5, 2.25


def beta(s, rho=RHO, mu=MU):
    a = 0.5 - mu / s**2
    return a + math.sqrt(a * a + 2 * rho / s**2)


def phi(theta, lam=LAM, sk=SK):
    return 1 + (1 - theta) * (lam - 1) * (1 + sk)


def D(b, f):
    return 1 - f ** (-b) * (1 + b * (f - 1))


def delta(f, s, mu=MU):
    a = mu - s * s / 2
    return math.log(f) / a if a > 0 else float("nan")


def ETR(s, rho=RHO, mu=MU):
    b = beta(s, rho, mu)
    xr = b / (b - 1) * (rho - mu) * K
    x0 = 0.8 * (rho - mu) * K
    return math.log(xr / x0) / (mu - s * s / 2)


out = {"params": dict(rho=RHO, mu=MU, K=K, SK=SK, lam=LAM)}
rows = []
for s in (0.10, 0.20, 0.30, 0.40, 0.50):
    b = beta(s)
    r = dict(sigma=s, beta=b, mult=b / (b - 1), ETR=ETR(s))
    for th in (0.2, 0.5, 0.8):
        f = phi(th)
        r[f"delta_{th}"] = delta(f, s)
        r[f"D_{th}"] = D(b, f)
    r["D_per_year_0.2"] = r["D_0.2"] / r["delta_0.2"]
    r["gov_value_pp"] = 100 * (r["D_0.2"] - r["D_0.8"])
    rows.append(r)
out["table1"] = rows
b0 = RHO / MU
out["limit_sigma0"] = {th: D(b0, phi(th)) for th in (0.2, 0.5, 0.8)}
out["beta0"] = b0
out["phis"] = {th: phi(th) for th in (0.2, 0.5, 0.8)}

# lambda that gives at sigma=.5 the same D as lambda=2.25 gives at sigma=.2 (theta=.2)
target = D(beta(0.2), phi(0.2))
lo, hi = 1.0, 50.0
for _ in range(200):
    m = (lo + hi) / 2
    if D(beta(0.5), phi(0.2, lam=m)) < target:
        lo = m
    else:
        hi = m
out["lam_equiv_sigma05"] = lo

# sensitivity (theta=.2), sigma .2 vs .4
sens = []
def add(label, lam=LAM, sk=SK, rho=RHO, mu=MU):
    f = phi(0.2, lam, sk)
    r = dict(label=label, phi=f)
    for s in (0.2, 0.4):
        b = beta(s, rho, mu)
        r[f"delta_{s}"] = delta(f, s, mu)
        r[f"D_{s}"] = D(b, f)
    sens.append(r)
add("Baseline")
add("λ = 1.5", lam=1.5); add("λ = 3.0", lam=3.0)
add("S/K = 0", sk=0.0); add("S/K = 1.0", sk=1.0)
add("ρ = 0.20", rho=0.20); add("ρ = 0.30", rho=0.30)
add("μ = 0.10", mu=0.10); add("μ = 0.18", mu=0.18)
out["table2"] = sens

# grid check: D decreasing in sigma and increasing in Phi over a wide grid
viol = 0; n = 0
for rho in np.linspace(0.05, 0.5, 10):
    for mu in np.linspace(-0.1, rho - 0.01, 10):
        for f in np.linspace(1.01, 5, 10):
            prev = None
            for s in np.linspace(0.05, 1.5, 30):
                d = D(beta(s, rho, mu), f); n += 1
                if prev is not None and d > prev + 1e-12:
                    viol += 1
                prev = d
out["grid_check"] = dict(points=n, violations=viol)
json.dump(out, open("p4_stats.json", "w"), indent=1)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "serif", "font.size": 10})
ss = np.linspace(0.05, 0.52, 200)
fig, ax = plt.subplots(1, 2, figsize=(7.5, 3.2))
for th, ls in ((0.2, "-"), (0.5, "--"), (0.8, ":")):
    f = phi(th)
    ax[0].plot(ss, [delta(f, s) for s in ss], "k" + ls, label=f"θ = {th}")
    ax[1].plot(ss, [100 * D(beta(s), f) for s in ss], "k" + ls, label=f"θ = {th}")
ax[0].set_xlabel("Volatility σ"); ax[0].set_ylabel("Excess delay Δ (years)"); ax[0].set_title("(a) Delay length", fontsize=10)
ax[1].set_xlabel("Volatility σ"); ax[1].set_ylabel("Relative value loss D (%)"); ax[1].set_title("(b) Delay cost", fontsize=10)
ax[0].set_ylim(0, 40); ax[1].set_ylim(0, 25)
for a in ax: a.legend(frameon=False)
fig.tight_layout(); fig.savefig("fig1.png", dpi=300)
print(json.dumps(out, indent=1, default=float))
