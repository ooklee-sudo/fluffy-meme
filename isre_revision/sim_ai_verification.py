"""Numerical check of Corollary 3 (AI-assisted verification): under linear cost,
d ln R*/d ln c = 1 - eps, so R* is locally proportional to lambda^eps (theta/c)^-(1-eps), and when
c ∝ lambda^g and theta ∝ lambda^eta, d ln R*/d ln lambda = eps + (g - eta)(1 - eps).
Also checks Corollary 2(b): with full extraction of private value, lambda_C/lambda_S = psi^(1/(1+eps))."""
import json, os
import numpy as np
from scipy import optimize
import sim_cv_elasticity as S

rows = []
B = 50.0
for d in [S.DISTS[0], S.DISTS[4], S.DISTS[5], S.DISTS[2]]:
    _, e0 = S.residual(d, 1.0, B)
    eps, _ = S.formula_elasticity(d, e0)
    h = 1e-4
    # elasticity w.r.t. verification cost c
    rp, _ = S.residual(d, 1.0, B, c=np.exp(h)); rm, _ = S.residual(d, 1.0, B, c=np.exp(-h))
    el_c = (np.log(rp) - np.log(rm)) / (2 * h)
    for g, eta in [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5), (1.0, 0.43)]:
        def lnR(l):
            lam = np.exp(l)
            ds = S.Scaled(d, lam ** eta)
            return np.log(S.residual(ds, lam, B, c=lam ** g)[0])
        tot = (lnR(h) - lnR(-h)) / (2 * h)
        rows.append(dict(dist=d.name, eps=float(eps), dlnR_dlnc_numeric=float(el_c), dlnR_dlnc_formula=float(1 - eps),
                         g=g, eta=eta, total_numeric=float(tot), total_formula=float(eps + (g - eta) * (1 - eps))))
for r in rows:
    print(f"{r['dist']:30s} g={r['g']:.2f} eta={r['eta']:.2f}  dlnR/dlnc {r['dlnR_dlnc_numeric']:.5f} vs {r['dlnR_dlnc_formula']:.5f}"
          f"  total {r['total_numeric']:+.5f} vs {r['total_formula']:+.5f}")
err = max(max(abs(r["dlnR_dlnc_numeric"] - r["dlnR_dlnc_formula"]), abs(r["total_numeric"] - r["total_formula"])) for r in rows)
print("max abs error", err)

# Corollary 2(b): vendor with full extraction maximises N*nubar*G(lam)/2 - K0/lam
k, nub, N, K0, lam0 = 0.6587, 1.0, 100.0, 1.0, 5.0
eps = 1 / (1 + k)
G = lambda lam: (lam0 ** eps - lam ** eps) / eps
for delta in (1.0, 0.5, 0.2):
    psi = (k + 1 / delta) / (k + 1)
    lc = optimize.minimize_scalar(lambda l: -(N * nub * G(l) / 2 - K0 / l), bounds=(1e-4, lam0), method="bounded", options=dict(xatol=1e-12)).x
    ls = optimize.minimize_scalar(lambda l: -(psi * N * nub * G(l) / 2 - K0 / l), bounds=(1e-4, lam0), method="bounded", options=dict(xatol=1e-12)).x
    print(f"delta={delta}: lam_C/lam_S numeric {lc/ls:.4f}, formula psi^(1/(1+eps)) {psi**(1/(1+eps)):.4f}")
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "ai_verification_checks.json"), "w"), indent=1)
