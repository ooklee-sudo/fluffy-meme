"""Numerical checks for the proofs of Appendix D: (i) increments of the expected maximum decrease; (ii) uniqueness of the team's
equilibrium under the weak-feedback condition psi*kappa > beta^2 theta^2 phi^2 N and above beta_u; (iii) a multiplicity example.
Run: python uniqueness_check.py"""
import numpy as np
import endogenous_exploit as E
MN = E.MN

def roots(N, phi, beta, p, n=20001):
    """All roots e in [0,1] of kappa*e = beta*(1-e)^(N-1)*max(g(e),0), g(e)=G0 - beta*theta^2*phi/psi*(1-phi*Q(e)); plus their stability."""
    G0 = (1 - phi) * p['Delta'] - phi * p['sig'] * MN[N]
    kt = beta * p['theta'] ** 2 * phi / p['psi']
    es = np.linspace(0, 1, n); Q = 1 - (1 - es) ** N
    g = G0 - kt * (1 - phi * Q)
    f = p['kappa'] * es - beta * (1 - es) ** (N - 1) * np.maximum(g, 0.0)
    out = []
    if abs(f[0]) < 1e-14: out.append(0.0)
    for i in np.flatnonzero(f[:-1] * f[1:] < 0):
        lo, hi = es[i], es[i + 1]; flo = f[i]
        for _ in range(60):
            m = (lo + hi) / 2; q = 1 - (1 - m) ** N; gm = G0 - kt * (1 - phi * q)
            fm = p['kappa'] * m - beta * (1 - m) ** (N - 1) * max(gm, 0.0)
            if fm * flo <= 0: hi = m
            else: lo, flo = m, fm
        out.append((lo + hi) / 2)
    return out

if __name__ == '__main__':
    # (i) increments of E[max] strictly decreasing for the normal (a proof for any distribution is in Appendix D)
    inc = np.diff([MN[n] for n in range(1, 301)]); print("m_N increasing:", bool(np.all(inc > 0)), "| increments decreasing:", bool(np.all(np.diff(inc) < 0)))
    rng = np.random.default_rng(1); base = dict(sig=1.0, Delta=1.0, kappa=4.0, psi=1.0, theta=0.7)
    # (ii) uniqueness under the weak-feedback condition, and for beta >= beta_u
    viol_cond = viol_u = tried_cond = tried_u = 0; multi_outside = None; n_multi_outside = n_outside = 0
    for _ in range(4000):
        p = {**base, 'Delta': rng.uniform(0.2, 3), 'kappa': rng.uniform(0.5, 30), 'psi': rng.uniform(0.3, 3), 'theta': rng.uniform(0.2, 1)}
        N = int(rng.integers(1, 40)); phi = float(rng.uniform(0.05, 0.95)); beta = float(rng.uniform(0.05, 8))
        G0 = (1 - phi) * p['Delta'] - phi * p['sig'] * MN[N]; beta_u = p['psi'] * G0 / (p['theta'] ** 2 * phi * (1 - phi)) if G0 > 0 else 0.0
        r = roots(N, phi, beta, p); k = len(r)
        if p['psi'] * p['kappa'] > beta ** 2 * p['theta'] ** 2 * phi ** 2 * N:
            tried_cond += 1; viol_cond += (k != 1)
        elif beta >= beta_u:
            tried_u += 1; viol_u += (k != 1)
        else:
            n_outside += 1
            if k > 1:
                n_multi_outside += 1
                if multi_outside is None: multi_outside = (N, phi, beta, p, r)
    print(f"weak-feedback condition: {tried_cond} draws, violations of uniqueness = {viol_cond}")
    print(f"beta >= beta_u (condition fails): {tried_u} draws, violations = {viol_u}")
    print(f"outside both: {n_outside} draws, with several equilibria: {n_multi_outside}")
    if multi_outside:
        N, phi, beta, p, r = multi_outside
        print("example with several equilibria:", dict(N=N, phi=round(phi, 3), beta=round(beta, 3), **{k: round(v, 3) for k, v in p.items()}), "roots e =", [round(x, 5) for x in r])

    # (iv) the multiplicity example of Appendix D, Theorem 4(vi): N=5, zeta=0.6, beta=6.5, Delta=2.5, kappa=1.5, psi=2, theta=0.4
    p = dict(sig=1.0, Delta=2.5, kappa=1.5, psi=2.0, theta=0.4); N, zeta, beta = 5, 0.6, 6.5
    G0 = (1 - zeta) * p['Delta'] - zeta * p['sig'] * MN[N]
    print("\nexample: beta_d =", round(p['psi'] * G0 / (p['theta'] ** 2 * zeta), 2), " beta_u =", round(p['psi'] * G0 / (p['theta'] ** 2 * zeta * (1 - zeta)), 2),
          " weak-feedback lhs/rhs =", p['psi'] * p['kappa'], round(beta ** 2 * p['theta'] ** 2 * zeta ** 2 * N, 2), " roots:", [round(float(x), 4) for x in roots(N, zeta, beta, p)])
