"""Monte Carlo checks of the detectability bound (see detectability/bound.py).
Usage: python simulate.py [REPS] [OUT_JSON]
Data-generating process: J occupations with true task shares s_j ~ Beta (mean m, SD sigma_s); observed exposure e_j = s_j + u_j with
reliability R; outcome in cell (country c, occupation j): y = A*beta*s_j [+ binomial assimilation noise] + eta_j + eps_cj; OLS of y on the
sample-standardized exposure with standard errors clustered by occupation, t critical value with J-1 degrees of freedom.
Checks: (1) mean estimate vs gamma* = A beta sigma_s sqrt(R); (2) empirical SD vs the analytic SE; (3) rejection rate at gamma* vs the
normal-power formula; (4) rejection rate when |gamma*| = MDE (should be about 0.80); (5) size under the null."""
import sys, json
import numpy as np
from statistics import NormalDist
from detectability import gamma_star, se_from_design, mde, required_effect_scale
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
OUT = sys.argv[2] if len(sys.argv) > 2 else 'results/simulation_results.json'
rng = np.random.default_rng(20261028)
J, C, SIG_ETA, SIG_EPS, MEAN_S = 96, 6, 0.12, 0.31, 0.10
from scipy import stats

def draw_shares(sigma_s):
    var = sigma_s ** 2; ab = MEAN_S * (1 - MEAN_S) / var - 1
    return rng.beta(MEAN_S * ab, (1 - MEAN_S) * ab, J)

def one_rep(sigma_s, R, A, beta, micro=False, M=50):
    s = draw_shares(sigma_s)
    u = rng.normal(0, np.sqrt(sigma_s ** 2 * (1 - R) / R) if R < 1 else 0.0, J)    # var(u) = var(s)(1-R)/R
    e = s + u; z = (e - e.mean()) / e.std(ddof=1)
    eta = rng.normal(0, SIG_ETA, J)[:, None]; eps = rng.normal(0, SIG_EPS, (J, C))
    if micro:   # employer-level assimilation: fraction f of M employers assimilates, demand change beta per assimilator
        f = rng.binomial(M, A, (J, C)) / M; signal = beta * s[:, None] * f
    else:       signal = A * beta * s[:, None] * np.ones((J, C))
    y = signal + eta + eps
    X = np.column_stack([np.ones(J * C), np.repeat(z, C)]); Y = y.ravel(); XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ Y; res = Y - X @ b
    meat = sum(np.outer(X[i * C:(i + 1) * C].T @ res[i * C:(i + 1) * C], X[i * C:(i + 1) * C].T @ res[i * C:(i + 1) * C]) for i in range(J))
    V = XtX_inv @ meat @ XtX_inv * (J / (J - 1)) * ((J * C - 1) / (J * C - 2))
    return b[1], np.sqrt(V[1, 1])

def scenario(sigma_s, R, A, beta, micro=False):
    g = gamma_star(A, beta, sigma_s=sigma_s, R=R); se_an = se_from_design(J, SIG_EPS, SIG_ETA, C, A=A, beta=beta, sigma_s=sigma_s, R=R)
    est = np.array([one_rep(sigma_s, R, A, beta, micro) for _ in range(REPS)]); tcrit = stats.t.ppf(0.975, J - 1)
    rej = (np.abs(est[:, 0] / est[:, 1]) > tcrit).mean()
    power_formula = NormalDist().cdf(abs(g) / se_an - 1.96)
    # rescale beta so that |gamma*| equals the MDE computed from the analytic SE
    scale = required_effect_scale(J, SIG_EPS, SIG_ETA, C, R)             # |A*beta*sigma_s| at which |gamma*| = MDE (self-consistent SE)
    beta_m = np.sign(beta) * scale / (A * sigma_s)
    est_m = np.array([one_rep(sigma_s, R, A, beta_m, micro) for _ in range(REPS)])
    return {'sigma_s': sigma_s, 'R': R, 'A': A, 'beta': beta, 'micro': micro, 'gamma_star': g, 'mean_estimate': float(est[:, 0].mean()),
            'ratio_mean_to_gamma_star': float(est[:, 0].mean() / g), 'empirical_sd': float(est[:, 0].std(ddof=1)), 'analytic_se': se_an,
            'mean_cluster_se': float(est[:, 1].mean()), 'rejection_rate_at_gamma_star': float(rej), 'power_formula_at_gamma_star': float(power_formula),
            'rejection_rate_when_gamma_equals_mde': float((np.abs(est_m[:, 0] / est_m[:, 1]) > tcrit).mean())}

def null_size():
    est = np.array([one_rep(0.19, 0.7, 0.3, 0.0) for _ in range(REPS)]); tcrit = stats.t.ppf(0.975, J - 1)
    return float((np.abs(est[:, 0] / est[:, 1]) > tcrit).mean())

if __name__ == '__main__':
    out = {'reps': REPS, 'J': J, 'cells_per_occupation': C, 'scenarios': []}
    for sigma_s in (0.10, 0.19):
        for R in (1.0, 0.7, 0.5):
            for A, beta in ((0.0955, -0.19), (0.3618, -0.5), (0.7, -0.5)):
                out['scenarios'].append(scenario(sigma_s, R, A, beta)); print(out['scenarios'][-1]['sigma_s'], R, A, beta, round(out['scenarios'][-1]['ratio_mean_to_gamma_star'], 3), flush=True)
    out['scenarios'].append(scenario(0.19, 0.7, 0.3618, -0.5, micro=True))
    out['size_under_null'] = null_size()
    json.dump(out, open(OUT, 'w'), indent=1); print('size under the null', out['size_under_null'])
