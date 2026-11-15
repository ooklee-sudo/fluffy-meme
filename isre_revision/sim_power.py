"""
Power simulation for the verification experiment (experiment_protocol.md).

Design simulated: within-subject, two blocks of n_items AI-generated functions each,
one from a low-defect "assistant" (lambda_L) and one from a high-defect assistant
(lambda_H), order counterbalanced. Participants verify by running hidden unit tests
at an explicit per-test cost c and pay a penalty B for every defect they ship.

Behaviour: each participant has an idiosyncratic cost multiplier (lognormal) and
chooses the model-optimal number of tests per item, plus implementation noise.
The true detection technology is gamma-mixed with shape k and mean theta per test,
as estimated on HumanEval+ in the manuscript.

Estimand: eps_hat = ln(R_H / R_L) / ln(lambda_H / lambda_L) from pooled shipped
defects; inference by participant bootstrap.
Tests: H0_full_offset eps = 0 and H0_no_response eps = 1 (two-sided, 5%).
"""
import json
import os

import numpy as np

rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

K, THETA = 0.63, 0.40          # tail index and mean per-test detection prob
LAM_L, LAM_H = 0.15, 0.60      # defects per function (Haiku-like vs 8B-like)
B, C = 1.00, 0.02              # $ penalty per shipped defect, $ per test
MAX_TESTS = 40


def optimal_tests(lam, cmult):
    z = B * lam * THETA / (C * cmult)
    eps = 1 / (1 + K)
    e = np.where(z > 1, K * (z**eps - 1) / THETA, 0.0)
    return e


def simulate(n_part, n_items, adjust=1.0, sd_c=0.5, sd_noise=0.5, item_sd=0.0):
    """adjust in [0,1]: share of the optimal effort response participants actually make
    (1 = model-optimal, 0 = same effort under both tools). item_sd: lognormal
    heterogeneity in defect rates across functions (difficulty)."""
    cm = np.exp(rng.normal(0, sd_c, n_part))
    shipped = {}
    e_mid = optimal_tests(np.sqrt(LAM_L * LAM_H), cm)
    for lam in (LAM_L, LAM_H):
        e_star = np.exp(adjust * np.log(np.maximum(optimal_tests(lam, cm), 1e-3))
                        + (1 - adjust) * np.log(np.maximum(e_mid, 1e-3)))
        e = e_star[:, None] * np.exp(rng.normal(0, sd_noise, (n_part, n_items)))
        e = np.clip(np.rint(e), 0, MAX_TESTS)
        lam_i = lam * np.exp(rng.normal(-item_sd**2 / 2, item_sd, (n_part, n_items)))
        n_def = rng.poisson(lam_i)
        tot = np.zeros((n_part, n_items))
        maxd = n_def.max()
        for j in range(maxd):
            present = n_def > j
            rho = np.clip(rng.gamma(K, THETA / K, (n_part, n_items)), 0, 1)
            surv = rng.random((n_part, n_items)) < (1 - rho) ** e
            tot += present & surv
        shipped[lam] = tot.sum(1)
    return shipped[LAM_L], shipped[LAM_H]


def eps_hat(rl, rh):
    return np.log(rh.sum() / rl.sum()) / np.log(LAM_H / LAM_L)


def power(n_part, n_items, sims=400, boots=300, **kw):
    rej0 = rej1 = 0
    ests = []
    for _ in range(sims):
        rl, rh = simulate(n_part, n_items, **kw)
        est = eps_hat(rl, rh)
        idx = rng.integers(0, n_part, (boots, n_part))
        bl, bh = rl[idx].sum(1), rh[idx].sum(1)
        ok = (bl > 0) & (bh > 0)
        be = np.log(bh[ok] / bl[ok]) / np.log(LAM_H / LAM_L)
        lo, hi = np.quantile(be, [0.025, 0.975])
        rej0 += lo > 0
        rej1 += hi < 1
        ests.append(est)
    return dict(n_part=n_part, n_items=n_items, mean_eps_hat=float(np.mean(ests)),
                sd_eps_hat=float(np.std(ests)), power_vs_full_offset=rej0 / sims,
                power_vs_no_response=rej1 / sims)


if __name__ == "__main__":
    print("Predicted tests per item (median participant):",
          f"low-defect tool {optimal_tests(LAM_L, 1.0):.2f}, high-defect tool {optimal_tests(LAM_H, 1.0):.2f}")
    print("Predicted eps = 1/(1+k) =", round(1 / (1 + K), 3))
    scenarios = {
        "baseline (optimal response)": dict(adjust=1.0, sd_c=0.5, sd_noise=0.5, item_sd=0.0),
        "stress: half response, noisy, item heterogeneity": dict(adjust=0.5, sd_c=1.0, sd_noise=1.0, item_sd=0.8),
        "stress: quarter response, noisy, item heterogeneity": dict(adjust=0.25, sd_c=1.0, sd_noise=1.0, item_sd=0.8),
    }
    rows = []
    for label, kw in scenarios.items():
        print("--", label)
        for n_items in (12, 20):
            for n in (60, 120, 240):
                r = power(n, n_items, **kw)
                r["scenario"] = label
                rows.append(r)
                print(f"N={n:4d} items/block={n_items}: eps_hat {r['mean_eps_hat']:.3f} (sd {r['sd_eps_hat']:.3f}); "
                      f"power vs eps=0 {r['power_vs_full_offset']:.2f}, vs eps=1 {r['power_vs_no_response']:.2f}")
    with open(os.path.join(OUT, "power.json"), "w") as f:
        json.dump(rows, f, indent=1)
