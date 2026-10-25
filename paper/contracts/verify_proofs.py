"""Numerical verification of the rigorous versions of Proposition 4 (integer budget) and Proposition 6(b) (convergence rate)."""
import numpy as np
from scipy.special import betaln
from contracts import Mkt, solve
from diff_bertrand import curves, summarize, share
out = []; P = out.append
def parts(m):
    a, b, H, v, k = m.a, m.b, m.H, m.v, m.k
    phi = lambda n: H - v*(n + a + b)/a                    # fee at which attempt n+1 becomes unattractive: q_n (H-f) = v
    S = lambda j: m.S[j]; q = lambda n: a/(a+b+n)
    L = lambda n: phi(n)*m.P(n) - k*m.att(n)                # profit at left end of step n (attained)
    R = lambda n: phi(n-1)*m.P(n) - k*m.att(n)              # sup of profit within step n (approached from below)
    return phi, S, q, L, R
# ---------- (1) Proposition 4: identities and the dominance chain ----------
rng = np.random.default_rng(21); bad = dict(identity=0, sign=0, chain=0, argmax=0, n=0, strict_under=0, in_step=0)
for t in range(300):
    a = rng.uniform(.05, .6); b = np.exp(rng.uniform(np.log(.1), np.log(4))); H = np.exp(rng.uniform(np.log(30), np.log(500)))
    v = H*np.exp(rng.uniform(np.log(.001), np.log(.03))); k = v*np.exp(rng.uniform(np.log(.1), np.log(3)))
    m = Mkt(a, b, H, v, k, J=3000); fb = m.first_best(); n0 = fb['N']; fe = H*k/(k+v)
    if n0 < 1: continue
    bad['n'] += 1; phi, S, q, L, R = parts(m)
    top = min(m.Nstar(H/v), 2999) + 1
    for n in range(1, min(top, 400)):
        D = R(n) - L(n-1) if n-1 >= 0 else None
        pred = S(n-1)*(phi(n-1)*q(n-1) - k)
        if abs(D - pred) > 1e-7*max(1, abs(pred)): bad['identity'] += 1
        if (D > 1e-9) != (phi(n-1) > fe + 1e-9) and abs(D) > 1e-9: bad['sign'] += 1
    # chain: R(n) < R(n0) for all n > n0
    for n in range(n0+1, min(top, n0+200)):
        if not R(n) < R(n0) + 1e-9: bad['chain'] += 1
    # argmax of R over n equals brute-force optimum budget (success-fee monopoly)
    nmax = int(min(m.Nstar(H/v), 2999))
    Rs = [(R(n), n) for n in range(1, nmax+1)]
    nhat = max(Rs)[1]
    fs = np.linspace(0, H, 4000); prof = [m.success_fee(f)['vend'] for f in fs]; bf_budget = m.success_fee(fs[int(np.argmax(prof))])['N']
    if abs(bf_budget - nhat) > 1 and not (R(nhat) - max(prof) > -1e-3*max(1, max(prof))): bad['argmax'] += 1
    bad['strict_under'] += nhat < n0; bad['in_step'] += nhat == n0
P("== Proposition 4 (integer budget): verification ==")
P(f"{bad['n']} draws with N^FB >= 1")
P(f"identity R(n) - L(n-1) = S(n-1)(phi_(n-1) q_(n-1) - k): violations {bad['identity']}")
P(f"sign(R(n) - L(n-1)) = sign(phi_(n-1) - f^e): violations {bad['sign']}")
P(f"chain R(n) < R(N^FB) for all n > N^FB: violations {bad['chain']}")
P(f"vendor's best step n_hat = argmax R(n): strictly below N^FB in {bad['strict_under']} draws, equal to N^FB in {bad['in_step']} draws; argmax/brute-force mismatches {bad['argmax']}")
# ---------- (2) Proposition 6(b): convergence rate ----------
P("")
P("== Proposition 6(b): convergence in sigma (RepairBench-like, H=100, v=1, k=0.2, n=5) ==")
m = Mkt(.12, .39, 100., 1., .2); fb = m.first_best(); Gbar = fb['surplus']
P(f"G_bar <= S^FB = {Gbar:.1f};  rho = exp(G_bar/sigma) - 1;  coverage limit n/(n+1) = {5/6:.3f}")
P(" sigma | rho  | bound (1-rho)/(1+rho) | A: Pi(p_hat)/Pi_m  N  coverage | B: Pi(p_hat)/Pi_m  N  coverage | monopoly N_A N_B")
cvs = {kk: curves(m, kk) for kk in "AB"}
mono = {}
for kk in "AB":
    ps, F, Pi, N, Wm = cvs[kk]; i = int(np.argmax(Pi)); mono[kk] = (Pi[i], N[i], ps[i])
for sig in [30., 100., 300., 1000., 3000.]:
    rho = np.exp(Gbar/sig) - 1; row = []
    for kk in "AB":
        r = summarize(m, kk, 5, sig, cvs[kk]); row.append((r['Pi']/mono[kk][0], r['N'], r['cover']))
    P(f" {sig:6.0f} | {rho:5.2f} | {max((1-rho)/(1+rho), 0):6.3f}               | {row[0][0]:.3f}        {row[0][1]:3d}   {row[0][2]:.3f}    | {row[1][0]:.3f}        {row[1][1]:3d}   {row[1][2]:.3f}    | {mono['A'][1]:3d} {mono['B'][1]:3d}")
open("results_verify_proofs.txt", "w").write("\n".join(out)); print("\n".join(out))
