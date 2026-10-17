"""Optimal judge-linked pay with a participation constraint (Appendix G).
The organization offers w = alpha + beta*J_ship; a risk-neutral team with outside option 0 accepts, and alpha is set so that the
participation constraint binds, so the organization's payoff is total surplus S(beta) given the team's equilibrium (a, e).
Run: python optimal_pay.py"""
import numpy as np
import endogenous_exploit as E
from multitask_explore import beta_d
MN = E.MN
def equilibria(N, phi, beta, p, n=2001):
    """Fast version of multitask_explore.equilibria: roots of kappa*e = beta*(1-e)^(N-1)*max(G(e),0), with a(e) from (F1)."""
    G0 = (1 - phi) * p['Delta'] - phi * p['sig'] * MN[N]
    def f(e):
        q = 1 - (1 - e) ** N
        g = G0 - beta * p['theta'] ** 2 * phi / p['psi'] * (1 - q * phi)
        return p['kappa'] * e - beta * (1 - e) ** (N - 1) * np.maximum(g, 0.0)
    es = np.linspace(0, 1, n); fs = f(es); out = []
    if fs[0] == 0: out.append(0.0)
    for i in np.flatnonzero(fs[:-1] * fs[1:] < 0):
        lo, hi = es[i], es[i + 1]; flo = fs[i]
        for _ in range(50):
            m = (lo + hi) / 2; fm = f(m)
            if fm * flo <= 0: hi = m
            else: lo, flo = m, fm
        out.append((lo + hi) / 2)
    res = []
    for e in sorted(set(round(float(x), 7) for x in out)):
        q = 1 - (1 - e) ** N; res.append((e, beta * p['theta'] * (1 - q * phi) / p['psi']))
    return res

BASE = dict(sig=1.0, Delta=1.0, kappa=4.0, psi=1.0, theta=0.7, g=1.0, rho_s=0.6, d=2.0, cs=0.01, cG=0.05)

def surplus(beta, N, phi, p):
    eq = equilibria(N, phi, beta, p)
    e, a = max(eq, key=lambda x: x[0]) if eq else (0.0, beta * p['theta'] / p['psi'])   # pessimistic if several
    Q = 1 - (1 - e) ** N
    return ((1 - Q) * (p['g'] * a + p['rho_s'] * MN[N]) - Q * (1 - phi) * p['d'] - p['psi'] / 2 * a ** 2
            - N * p['kappa'] / 2 * e ** 2 - p['cs'] * N - (p['cG'] if phi > 0 else 0.0)), e, a

def first_best(N, phi, p):
    return p['g'] ** 2 / (2 * p['psi']) + p['rho_s'] * MN[N] - p['cs'] * N - (p['cG'] if phi > 0 else 0.0)

if __name__ == '__main__':
    N = 4; fb_beta = BASE['g'] / BASE['theta']
    # 1. surplus never exceeds the first best; equality only at e=0, a=g/psi
    rng = np.random.default_rng(0); worst = -1e9
    for _ in range(400):
        p = {**BASE, 'kappa': rng.uniform(1, 20), 'Delta': rng.uniform(0.3, 2), 'theta': rng.uniform(0.3, 1), 'd': rng.uniform(0.5, 4)}
        phi = rng.choice([0.0, 0.2, 0.4]); b = rng.uniform(0, 3)
        s = surplus(b, N, phi, p)[0]; worst = max(worst, s - first_best(N, phi, p))
    print("max (S - S_FB) over random draws (must be <= 0):", round(worst, 6))
    # 2. no inspection: beta* < g/theta ; S strictly decreasing beyond g/theta
    for kappa in (4.0, 20.0):
        p = {**BASE, 'kappa': kappa}
        betas = np.round(np.linspace(0, 3.0, 301), 3); S = np.array([surplus(b, N, 0.0, p)[0] for b in betas])
        bstar = betas[int(np.argmax(S))]; thr = p['g'] * p['theta'] * p['kappa'] / (p['psi'] * N * p['Delta'] * (p['rho_s'] * MN[N] + p['d']))
        beyond = S[betas >= fb_beta]
        print(f"kappa={kappa}: beta*={bstar:.3f} (< g/theta={fb_beta:.3f}), S*={S.max():+.4f}, S(0)={S[0]:+.4f}, "
              f"condition g*theta*kappa/(psi*N*Delta*(rho*m+d)) = {thr:.2f} (>1 means interior), decreasing beyond: {bool(np.all(np.diff(beyond) < 0))}")
    # 3. with inspection: first best implementable iff beta_d <= g/theta
    for phi in (0.2, 0.4):
        p = BASE; bd = beta_d(N, phi, p)
        s_fb_pay, e, a = surplus(fb_beta, N, phi, p)
        print(f"phi={phi}: beta_d={bd:.3f}; at beta=g/theta: e={e:.4f}, a={a:.3f}, S={s_fb_pay:+.4f}, S_FB={first_best(N, phi, p):+.4f}")
    # value of inspection (kappa=4)
    p = BASE; s0 = max(surplus(b, N, 0.0, p)[0] for b in np.linspace(0, 3, 301))
    for phi in (0.2, 0.4):
        s1 = max(surplus(b, N, phi, p)[0] for b in np.linspace(0, 3, 301)); print(f"value of inspection at phi={phi}: {s1 - s0:+.4f} (cost {p['cG']})")
    # 4. regime where deterrence needs over-incentivizing: beta_d > g/theta
    p = {**BASE, 'Delta': 3.0}; phi = 0.4; bd = beta_d(N, phi, p); betas = np.linspace(0, 6, 601)
    S = np.array([surplus(b, N, phi, p)[0] for b in betas]); bs = betas[int(np.argmax(S))]
    print(f"Delta=3: beta_d={bd:.3f} > g/theta={fb_beta:.3f}; beta*={bs:.3f}, S*={S.max():+.4f}, S_FB={first_best(N, phi, p):+.4f}, S(beta_d)={surplus(bd, N, phi, p)[0]:+.4f}")
