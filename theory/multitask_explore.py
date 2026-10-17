import numpy as np
import endogenous_exploit as E
MN = E.MN
def equilibria(N, phi, beta, p):
    """All Nash equilibria (a,e) of the team's game: honest effort a, exploit effort e."""
    sig, Delta, kappa, psi, th = p['sig'], p['Delta'], p['kappa'], p['psi'], p['theta']
    G0 = (1 - phi) * Delta - phi * sig * MN[N]
    def G(e):
        Q = 1 - (1 - e) ** N
        return G0 - beta * th ** 2 * phi / psi * (1 - Q * phi)
    f = lambda e: kappa * e - beta * (1 - e) ** (N - 1) * max(G(e), 0.0)   # best-response condition on e given a(e)
    es = np.linspace(0, 1, 100001); fs = np.array([f(e) for e in es])
    roots = [es[i] for i in range(len(es) - 1) if fs[i] == 0 or fs[i] * fs[i + 1] < 0]
    if fs[0] == 0 and G(0) <= 0: pass
    out = []
    for e in roots:
        Q = 1 - (1 - e) ** N; a = beta * th * (1 - Q * phi) / psi
        out.append((round(float(e), 4), round(float(a), 4)))
    return sorted(set(out))
if __name__ == '__main__':
    p = dict(sig=1.0, Delta=1.0, kappa=4.0, psi=1.0, theta=0.7)
    for phi in (0.4,):
        for N in (4, 8):
            print(f"phi={phi}, N={N}")
            for beta in (0.25, 0.5, 1, 1.5, 2, 3, 4, 6):
                print('  beta', beta, equilibria(N, phi, beta, p))

def payoff(N, phi, beta, p, e, a):
    """Organization's net value: gold (honest effort gain g*a plus selection value) less exploit damage, payment, search and inspection cost."""
    Q = 1 - (1 - e) ** N; top = p['sig'] * MN[N]
    gold = (1 - Q) * (p['g'] * a + p['rho_s'] * MN[N]) - Q * (1 - phi) * p['d']
    J_ship = (p['theta'] * a + top) * (1 - Q * phi) + Q * (1 - phi) * p['Delta']
    return gold - beta * J_ship - p['cs'] * N - (p['cG'] if phi > 0 else 0.0)

def best_beta(N, phi, p, betas):
    rows = []
    for b in betas:
        eq = equilibria(N, phi, b, p)
        # pessimistic selection: the equilibrium with the largest exploit effort
        e, a = max(eq, key=lambda x: x[0]) if eq else (0.0, b * p['theta'] / p['psi'])
        rows.append((b, e, a, payoff(N, phi, b, p, e, a), len(eq)))
    return rows

def beta_d(N, phi, p):
    G0 = (1 - phi) * p['Delta'] - phi * p['sig'] * MN[N]
    return p['psi'] * G0 / (p['theta'] ** 2 * phi) if phi > 0 else float('inf')

if __name__ == '__main__':
    p = dict(sig=1.0, Delta=1.0, kappa=4.0, psi=1.0, theta=0.7, g=1.0, rho_s=0.6, d=2.0, cs=0.01, cG=0.05)
    betas = np.round(np.arange(0.1, 2.01, 0.1), 2)
    N = 4
    for phi in (0.0, 0.2, 0.4):
        print(f"\nN={N}, phi={phi}, beta_d={beta_d(N, phi, p):.3f}")
        rows = best_beta(N, phi, p, betas)
        for b, e, a, w, k in rows[::2]: print(f"  beta={b:.1f}  e={e:.4f}  a={a:.3f}  Pi={w:+.3f}  #eq={k}")
        b, e, a, w, k = max(rows, key=lambda r: r[3]); print(f"  best beta={b:.1f}, Pi={w:+.3f}, e={e:.4f}")
