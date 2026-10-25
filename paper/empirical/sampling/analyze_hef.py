"""HumanEvalFix(Python): n=40 samples/bug from 3 small models. Tests (i) heterogeneity, (ii) reservation rule vs fixed caps up to 40, (iii) calibration of the extrapolation from the first 10 samples to caps up to 40."""
import json, glob, hashlib, numpy as np
from scipy.optimize import minimize
from scipy.special import betaln, gammaln, comb, expit
NS = 40
lc = lambda n, k: gammaln(n+1) - gammaln(k+1) - gammaln(n-k+1)
def ll_bb(k, n, a, b): return lc(n, k) + betaln(k+a, n-k+b) - betaln(a, b)
def ll_bin(k, n, p): return lc(n, k) + k*np.log(p) + (n-k)*np.log1p(-p)
def fit_bb(k, n):
    f = lambda t: -ll_bb(k, n, *np.exp(t)).sum()
    r = min((minimize(f, np.log(s), method="Nelder-Mead") for s in ([.5, 1.], [1., 3.], [.2, .5], [2., .5])), key=lambda r: r.fun)
    return np.exp(r.x), -r.fun
nstar = lambda a, b, r: int(max(0, np.ceil(a*r - a - b)))
def ll_zi(k, n, a, b, pi): return np.log(pi*(k == 0) + (1-pi)*np.exp(ll_bb(k, n, a, b)))
def fit_zi(k, n):
    f = lambda t: -ll_zi(k, n, np.exp(t[0]), np.exp(t[1]), expit(t[2])).sum()
    r = min((minimize(f, [np.log(s[0]), np.log(s[1]), s[2]], method="Nelder-Mead", options=dict(maxiter=3000)) for s in ([.8, 1.5, 0.], [2., 3., -1.], [.5, .5, 1.], [.5, .1, -2.])), key=lambda r: r.fun)
    return (np.exp(r.x[0]), np.exp(r.x[1]), expit(r.x[2])), -r.fun
def nstar_zi(a, b, pi, r, cap=5000):
    n = np.arange(cap); S = np.exp(betaln(a, b+n) - betaln(a, b)); w = (1-pi)*S/(pi + (1-pi)*S)
    idx = np.nonzero(w*a/(a+b+n)*r <= 1)[0]; return int(idx[0]) if len(idx) else cap
def pfail(k, n, j):  # P(no success in first j of n exchangeable samples | k successes)
    return np.where(n-k >= j, np.exp(lc(n-k, j) - lc(n, j)), 0.0) if True else None
def lcomb(n, k): return gammaln(n+1)-gammaln(k+1)-gammaln(n-k+1)
def pf(k, n, j):
    k = np.asarray(k); out = np.zeros(k.shape)
    m = (n-k) >= j; out[m] = np.exp(lcomb(n-k[m], j) - lcomb(n, j)); return out
def cost(k, n, j, r): return float((sum(pf(k, n, i) for i in range(j)) + r*pf(k, n, j)).mean())
out = []; P = out.append
for f in sorted(glob.glob("raw_*.jsonl")):
    model = f[4:-6]; per = {}
    for l in open(f):
        x = json.loads(l)
        if x.get("error"): continue
        per.setdefault(x["task"], []).append(bool(x["ok"]))
    tasks = {t: v for t, v in per.items() if len(v) >= NS}
    if len(tasks) < 100: P(f"{model}: only {len(tasks)} complete tasks; skipped"); continue
    ks = np.array([sum(v[:NS]) for v in tasks.values()]); k10 = np.array([sum(v[:10]) for v in tasks.values()])
    ids = list(tasks)
    P(f"=== {model}: {len(tasks)} bugs x {NS} samples; mean success {ks.mean()/NS:.3f}; share with 0/{NS}: {(ks==0).mean():.2f}; share with {NS}/{NS}: {(ks==NS).mean():.2f}")
    p = np.clip(ks.mean()/NS, 1e-6, 1-1e-6); (a, b), l1 = fit_bb(ks, NS); l0 = ll_bin(ks, NS, p).sum()
    (az, bz, pz), l2 = fit_zi(ks, NS)
    P(f"    Beta-binomial a={a:.3f} b={b:.3f}; AIC bin={2-2*l0:.0f} vs BB={4-2*l1:.0f} vs ZI-BB={6-2*l2:.0f} (ZI: a={az:.3f} b={bz:.3f} pi={pz:.3f})")
    (a10, b10), _ = fit_bb(k10, 10)
    P(f"    Fit from first 10 samples only: a={a10:.3f} b={b10:.3f}")
    for r in [10, 30, 100, 300]:
        P(f"    H/c={r:4d}: N* BB (n=40)={nstar(a,b,r):3d}  N* BB (first 10)={nstar(a10,b10,r):3d}  N* ZI (n=40)={nstar_zi(az,bz,pz,r):3d}")
    # held-out cost vs cap with n=40 data
    tr = np.array([int(hashlib.md5(t.encode()).hexdigest(), 16) % 2 == 0 for t in ids]); te = ~tr
    P("    Held-out cost (units of c) by H/c: human-only | fixed k=1 | k=5 | k=10 | BB reservation | ZI reservation | best fixed in hindsight")
    for r in [10, 30, 100]:
        (at, bt), _ = fit_bb(ks[tr], NS); Nr = min(NS, nstar(at, bt, r))
        (azt, bzt, pzt), _ = fit_zi(ks[tr], NS); Nz = min(NS, nstar_zi(azt, bzt, pzt, r))
        hind = min(range(NS+1), key=lambda j: cost(ks[te], NS, j, r))
        P(f"      H/c={r:4d}: {r:6.1f} | {cost(ks[te],NS,1,r):6.2f} | {cost(ks[te],NS,5,r):6.2f} | {cost(ks[te],NS,10,r):6.2f} | {cost(ks[te],NS,Nr,r):6.2f} (N={Nr}) | {cost(ks[te],NS,Nz,r):6.2f} (N={Nz}) | {cost(ks[te],NS,hind,r):6.2f} (k={hind})")
    # calibration of extrapolation: predict coverage at j=40 from model fit on first 10, compare to observed coverage
    obs = [1 - pf(ks, NS, j).mean() for j in (1, 5, 10, 20, 40)]
    pred = [1 - np.exp(betaln(a10, b10+j) - betaln(a10, b10)) for j in (1, 5, 10, 20, 40)]
    (az10, bz10, pz10), _ = fit_zi(k10, 10)
    predz = [(1-pz10)*(1 - np.exp(betaln(az10, bz10+j) - betaln(az10, bz10))) for j in (1, 5, 10, 20, 40)]
    P("    Coverage at j=1,5,10,20,40  observed: " + ", ".join(f"{x:.3f}" for x in obs) + "   BB first-10 fit: " + ", ".join(f"{x:.3f}" for x in pred) + "   ZI first-10 fit: " + ", ".join(f"{x:.3f}" for x in predz))
    P("")
open("results_hef.txt", "w").write("\n".join(out)); print("\n".join(out))
