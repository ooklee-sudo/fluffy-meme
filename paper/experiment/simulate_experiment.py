"""Pre-registration support: (A) structural recovery of (Lambda, gamma, tau) from simulated stop/continue data; (B) power for the main reduced-form tests.
Participant at state n (failures so far on a defect) decides to continue with P = logistic((q_n X - (1-gamma*1[n>=1]) Y)/tau)
A: X=H, Y=Lambda*w+v ;  B: X=H-f, Y=v.  q_n = a/(a+b+n) (displayed to participants)."""
import numpy as np
from scipy.optimize import minimize
rng = np.random.default_rng(2026)
a, b = 0.2, 0.5
TRUE = dict(lam=1.8, gam=0.25, tau=1.5)
def design(nsub, ndef):
    rows = []
    for s in range(nsub):
        order = rng.permutation(2)                           # within-subject crossover of the contract form
        for d in range(ndef):
            kind = "AB"[order[d % 2]]
            H = rng.choice([60., 100., 150.]); v = 1.0
            w = rng.choice([1., 2., 4.]) if kind == "A" else 0.; f = rng.choice([.3, .5, .7])*H if kind == "B" else 0.
            rows.append((s, d, kind, H, v, w, f))
    return rows
def simulate(rows, p):
    data = []
    for (s, d, kind, H, v, w, f) in rows:
        X = H if kind == "A" else H - f; Y = (p['lam']*w + v) if kind == "A" else v
        pstar = rng.beta(a, b); n = 0
        while n < 15:
            q = a/(a+b+n); gate = 1 - (p['gam'] if n >= 1 else 0.)
            u = (q*X - gate*Y)/p['tau']; pc = 1/(1+np.exp(-u)); cont = rng.random() < pc
            data.append((s, n, kind == "A", X, Y/(p['lam'] if kind == "A" else 1.)*1.0, w, v, cont))
            if not cont: break
            if rng.random() < pstar: break                    # success ends the defect
            n += 1
    return data
def nll(theta, arr):
    lam, gam, tau = np.exp(theta[0]), 1/(1+np.exp(-theta[1])), np.exp(theta[2])
    n, isA, X, w, v, cont = arr['n'], arr['isA'], arr['X'], arr['w'], arr['v'], arr['cont']
    Y = np.where(isA, lam*w + v, v); q = a/(a+b+n); gate = 1 - gam*(n >= 1)
    u = (q*X - gate*Y)/tau; ll = np.where(cont, -np.logaddexp(0, -u), -np.logaddexp(0, u)); return -ll.sum()
def to_arr(data):
    d = np.array(data, dtype=float)
    return dict(s=d[:, 0], n=d[:, 1], isA=d[:, 2] > 0, X=d[:, 3], w=d[:, 5], v=d[:, 6], cont=d[:, 7] > 0)
def fit(arr):
    r = min((minimize(nll, x0, args=(arr,), method="Nelder-Mead", options=dict(maxiter=4000, xatol=1e-4, fatol=1e-6)) for x0 in ([0., -1., 0.], [.5, 0., .5], [-.3, -2., -.3])), key=lambda r: r.fun)
    return np.exp(r.x[0]), 1/(1+np.exp(-r.x[1])), np.exp(r.x[2])
out = []; P = out.append
P(f"True parameters: Lambda={TRUE['lam']}, gamma={TRUE['gam']}, tau={TRUE['tau']}  (Beta(a={a}, b={b}) displayed)")
for nsub, ndef in [(100, 12), (200, 12), (400, 12)]:
    ests = []
    for rep in range(40):
        rows = design(nsub, ndef); arr = to_arr(simulate(rows, TRUE)); ests.append(fit(arr))
    e = np.array(ests)
    P(f"N={nsub:4d} participants x {ndef} defects: Lambda mean {e[:,0].mean():.2f} (sd {e[:,0].std():.2f}); gamma mean {e[:,1].mean():.2f} (sd {e[:,1].std():.2f}); tau mean {e[:,2].mean():.2f} (sd {e[:,2].std():.2f}); n decisions ~ {len(arr['n'])}")
# power for reduced-form tests via two-sample t on within-subject differences (analytic)
from math import ceil
def n_per_group(d, alpha=.05, power=.8):
    from scipy.stats import norm
    return ceil(2*((norm.ppf(1-alpha/2)+norm.ppf(power))/d)**2)
P("")
P("Power (two-sided alpha=.05, 80%): participants per cell for between-subject effects d=0.20/0.30/0.40: " + ", ".join(f"d={d}: {n_per_group(d)}" for d in (.2, .3, .4)))
P("Within-subject (crossover) paired test, effect dz=0.20/0.30: participants: " + ", ".join(f"dz={d}: {ceil(((1.96+.8416)/d)**2)}" for d in (.2, .3)))
open("results_experiment_sim.txt", "w").write("\n".join(out)); print("\n".join(out))
