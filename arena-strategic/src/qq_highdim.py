"""Higher-dimensional quantum models for two sequential binary questions.
State: mixed density matrix rho (N x N complex). Q, B: projectors of rank kQ, kB (all ranks tried). Lueders rule.
Compares max log-likelihood with (i) the QQ-constrained saturated model and (ii) the unconstrained saturated model."""
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import chi2
from scipy.linalg import expm
rng = np.random.default_rng(1)
d = pd.read_pickle('/home/user/data/qq_llm.pkl')
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]   # (Q, B)
def counts(g): return {o: np.array([((g.order == o) & (g.Q == a) & (g.B == b)).sum() for a, b in CELLS], float) for o in ('QB', 'BQ')}
def ll(p, c): return float((c * np.log(np.clip(p, 1e-12, 1))).sum())
def unpack(x, N):
    h = x[:N * N] + 1j * x[N * N:2 * N * N]; H = (h.reshape(N, N) + h.reshape(N, N).conj().T) / 2
    V = expm(1j * H)                                   # unitary rotating B's basis relative to Q's
    a = (x[2 * N * N:3 * N * N] + 1j * x[3 * N * N:]).reshape(N, N); rho = a @ a.conj().T; rho /= np.trace(rho).real
    return V, rho
def probs(x, N, kQ, kB):
    V, rho = unpack(x, N)
    PQ = np.diag([1.0] * kQ + [0.0] * (N - kQ)); PB = V @ np.diag([1.0] * kB + [0.0] * (N - kB)) @ V.conj().T
    I = np.eye(N); Qy, Qn, By, Bn = PQ, I - PQ, PB, I - PB
    seq = lambda A, B: np.trace(B @ A @ rho @ A).real      # P(A then B) = tr(B A rho A)
    qb = np.array([seq(Qy, By), seq(Qy, Bn), seq(Qn, By), seq(Qn, Bn)])
    bq = np.array([seq(By, Qy), seq(Bn, Qy), seq(By, Qn), seq(Bn, Qn)])
    return qb, bq
def fit_quantum(c, N, restarts=12):
    best = -np.inf
    for kQ in range(1, N):
        for kB in range(1, N):
            if kB < kQ: continue   # symmetry is not exact (Q and B differ), but keep search small: also try swapped below
            for (a, b) in {(kQ, kB), (kB, kQ)}:
                f = lambda x: -(ll(probs(x, N, a, b)[0], c['QB']) + ll(probs(x, N, a, b)[1], c['BQ']))
                for _ in range(restarts):
                    r = minimize(f, rng.normal(size=4 * N * N), method='L-BFGS-B')
                    best = max(best, -r.fun)
    return best
def fit_qq_constrained(c):
    """Max likelihood over two free 4-cell distributions subject to q = disagree_QB - disagree_BQ = 0."""
    def f(z):
        p = np.exp(z[:4]); p /= p.sum(); r = np.exp(z[4:]); r /= r.sum()
        return -(ll(p, c['QB']) + ll(r, c['BQ']))
    cons = {'type': 'eq', 'fun': lambda z: (lambda p, r: (p[1] + p[2]) - (r[1] + r[2]))(np.exp(z[:4]) / np.exp(z[:4]).sum(), np.exp(z[4:]) / np.exp(z[4:]).sum())}
    return max(-minimize(f, rng.normal(size=8), constraints=[cons], method='SLSQP').fun for _ in range(10))
rows = []
for (m, disc), g in d.groupby(['model', 'disc']):
    c = counts(g)
    sat = ll(c['QB'] / c['QB'].sum(), c['QB']) + ll(c['BQ'] / c['BQ'].sum(), c['BQ'])
    pooled = c['QB'] + c['BQ']; cls = ll(pooled / pooled.sum(), c['QB']) + ll(pooled / pooled.sum(), c['BQ'])
    qq = fit_qq_constrained(c)
    row = dict(model=m, disclosure=['none', 'brand'][disc], n=int(pooled.sum()), LL_saturated=round(sat, 1), LL_QQbound=round(qq, 1), LL_classical=round(cls, 1))
    for N in (2, 3, 4):
        row[f'LL_q{N}D'] = round(fit_quantum(c, N, restarts=4 if N >= 4 else 8), 1)
    G = 2 * (sat - qq); row['LR_QQ_vs_sat'] = round(G, 1); row['p_QQ'] = float(f'{chi2.sf(G, 1):.2g}')
    G2 = 2 * (qq - cls); row['LR_QQbound_vs_classical'] = round(G2, 1); row['p_vs_classical'] = float(f'{chi2.sf(G2, 2):.2g}')
    rows.append(row); print(row, flush=True)
R = pd.DataFrame(rows); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(R.to_string(index=False))
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_highdim.csv', index=False)
