"""Empirical test of the optimal-stopping model on RepairBench (n=10 samples per bug, test-pass = success).
Models: Binomial (homogeneous p), Beta-Binomial (heterogeneous), Zero-inflated Beta-Binomial (unsolvable mass)."""
import json, numpy as np, hashlib
from scipy.optimize import minimize
from scipy.special import betaln, gammaln, expit
rows = [r for r in json.load(open("bug_counts.json")) if r["n"] == 10]
N = 10
lchoose = lambda n, k: gammaln(n+1) - gammaln(k+1) - gammaln(n-k+1)

def ll_bin(k, p): return lchoose(N, k) + k*np.log(p) + (N-k)*np.log1p(-p)
def ll_bb(k, a, b): return lchoose(N, k) + betaln(k+a, N-k+b) - betaln(a, b)
def ll_zi(k, a, b, pi):
    base = np.exp(ll_bb(k, a, b)); return np.log(pi*(k == 0) + (1-pi)*base)

def fit_bin(k): p = np.clip(k.mean()/N, 1e-6, 1-1e-6); return p, ll_bin(k, p).sum()
def fit_bb(k):
    f = lambda t: -ll_bb(k, *np.exp(t)).sum()
    best = min((minimize(f, np.log(s), method="Nelder-Mead") for s in ([.5, 1.], [1., 3.], [.2, .5])), key=lambda r: r.fun)
    return np.exp(best.x), -best.fun
def fit_zi(k):
    f = lambda t: -ll_zi(k, np.exp(t[0]), np.exp(t[1]), expit(t[2])).sum()
    best = min((minimize(f, [np.log(s[0]), np.log(s[1]), s[2]], method="Nelder-Mead", options=dict(maxiter=2000)) for s in ([.8, 1.5, 0.], [2., 3., -1.], [.5, .5, 1.])), key=lambda r: r.fun)
    return (np.exp(best.x[0]), np.exp(best.x[1]), expit(best.x[2])), -best.fun

def nstar_bb(a, b, r, cap=100000):  # attempts allowed; r = H/c
    return int(max(0, np.ceil(a*r - a - b)))
def nstar_zi(a, b, pi, r, cap=5000):
    n = np.arange(cap)
    S = np.exp(betaln(a, b+n) - betaln(a, b))
    w = (1-pi)*S / (pi + (1-pi)*S)
    q = w * a/(a+b+n)
    idx = np.nonzero(q*r <= 1)[0]; return int(idx[0]) if len(idx) else cap

def emp_cost(ks, j, r):  # exact expected cost (in units of c) using exchangeability of the 10 samples; cap j<=10
    pfail = lambda i: np.array([np.exp(lchoose(N-k, i) - lchoose(N, i)) if N-k >= i else 0.0 for k in ks])
    att = sum(pfail(i) for i in range(j))          # E[min(T,j)]
    return float((att + r*pfail(j)).mean())

out = []
P = out.append
by = {}
for r_ in rows: by.setdefault((r_["model"], r_["dataset"]), []).append(r_)
res = []
for (m, ds), L in sorted(by.items()):
    if len(L) < 80: continue
    k = np.array([x["k"] for x in L])
    # deterministic 50/50 split by bug id hash
    tr = np.array([int(hashlib.md5(x["bug"].encode()).hexdigest(), 16) % 2 == 0 for x in L])
    p, l0 = fit_bin(k); (a, b), l1 = fit_bb(k); (az, bz, pz), l2 = fit_zi(k)
    # held-out log-lik per bug
    pt, _ = fit_bin(k[tr]); (at, bt), _ = fit_bb(k[tr]); (azt, bzt, pzt), _ = fit_zi(k[tr])
    te = ~tr
    res.append(dict(model=m, ds=ds, nb=len(L), mean_succ=k.mean()/N, frac0=(k == 0).mean(), a=a, b=b, az=az, bz=bz, pz=pz,
        aic_bin=2-2*l0, aic_bb=4-2*l1, aic_zi=6-2*l2,
        te_bin=ll_bin(k[te], pt).mean(), te_bb=ll_bb(k[te], at, bt).mean(), te_zi=ll_zi(k[te], azt, bzt, pzt).mean()))
json.dump(res, open("fits.json", "w"))
R = res
P(f"Fitted (model x dataset) combos: {len(R)}  (n=10 samples/bug, >=80 bugs)")
P(f"Beta-Binomial beats Binomial by AIC: {sum(x['aic_bb'] < x['aic_bin'] for x in R)}/{len(R)};  held-out loglik: {sum(x['te_bb'] > x['te_bin'] for x in R)}/{len(R)}")
P(f"Zero-inflated beats Beta-Binomial by AIC: {sum(x['aic_zi'] < x['aic_bb'] for x in R)}/{len(R)};  held-out loglik: {sum(x['te_zi'] > x['te_bb'] for x in R)}/{len(R)}")
P(f"Median fraction of bugs with 0/10 successes: {np.median([x['frac0'] for x in R]):.2f};  median mean success rate: {np.median([x['mean_succ'] for x in R]):.3f}")
P(f"Median fitted (a, b) Beta-Binomial: a={np.median([x['a'] for x in R]):.2f}, b={np.median([x['b'] for x in R]):.2f}")
P(f"Median ZI: a={np.median([x['az'] for x in R]):.2f}, b={np.median([x['bz'] for x in R]):.2f}, pi={np.median([x['pz'] for x in R]):.2f}")
P("")
P("== Reservation threshold N* by H/c (median across combos) ==")
P("H/c   N*_BB(median)  N*_ZI(median)  [N*_BB IQR]")
for r in [5, 10, 30, 100, 300]:
    nb_ = [nstar_bb(x['a'], x['b'], r) for x in R]; nz = [nstar_zi(x['az'], x['bz'], x['pz'], r) for x in R]
    P(f"{r:4d}  {np.median(nb_):8.0f}  {np.median(nz):12.0f}   [{np.percentile(nb_,25):.0f}, {np.percentile(nb_,75):.0f}]")

# ---- out-of-sample policy evaluation on held-out bugs, caps within observed range (<=10) ----
P("")
P("== Held-out cost (units of c) per bug, caps restricted to 0..10 (exact, from real outcomes) ==")
P("H/c  policy                          mean cost over combos   %vs human-only   best-in-hindsight")
for r in [3, 5, 8, 10]:
    acc = {"human-only": [], "fixed k=1": [], "fixed k=3": [], "fixed k=5": [], "fixed k=10": [], "BB reservation (train fit)": [], "ZI reservation (train fit)": [], "hindsight best fixed": [], "train-best fixed": []}
    for (m, ds), L in sorted(by.items()):
        if len(L) < 80: continue
        k = np.array([x["k"] for x in L]); tr = np.array([int(hashlib.md5(x["bug"].encode()).hexdigest(), 16) % 2 == 0 for x in L]); te = ~tr
        (at, bt), _ = fit_bb(k[tr]); (azt, bzt, pzt), _ = fit_zi(k[tr])
        cost = lambda j: emp_cost(k[te], j, r)
        acc["human-only"].append(cost(0))
        for j in (1, 3, 5, 10): acc[f"fixed k={j}"].append(cost(j))
        acc["BB reservation (train fit)"].append(cost(min(10, nstar_bb(at, bt, r))))
        acc["ZI reservation (train fit)"].append(cost(min(10, nstar_zi(azt, bzt, pzt, r))))
        acc["hindsight best fixed"].append(min(cost(j) for j in range(11)))
        acc["train-best fixed"].append(cost(int(np.argmin([emp_cost(k[tr], j, r) for j in range(11)]))))
    base = np.mean(acc["human-only"])
    for kk, v in acc.items(): P(f"{r:4d}  {kk:30s}  {np.mean(v):10.3f}              {100*(1-np.mean(v)/base):6.1f}%")
    P("")
# ---- cross-model heterogeneity in implied N* & token cost ----
tok = {}
for x in rows: tok.setdefault(x["model"], []).append(x["comp_tok"])
P("== Selected models: fits (all bugs) ==")
sel = ["o4-mini-2025-04-16-high", "deepseek-v3", "gpt-4o-2024-11-20", "qwen-2.5-coder-32b-instruct", "llama-3.3-70b-instruct", "claude-3-7-sonnet-20250219"]
P("model/dataset                           nbugs  mean_succ  frac0   a      b     N*_BB(H/c=30)  N*_BB(100)  pi_ZI  N*_ZI(30)  N*_ZI(100)")
for x in R:
    if x['model'] in sel:
        P(f"{x['model'][:28]+'/'+x['ds']:40s} {x['nb']:4d}  {x['mean_succ']:8.3f}  {x['frac0']:5.2f} {x['a']:6.2f} {x['b']:6.2f}  {nstar_bb(x['a'],x['b'],30):8d}  {nstar_bb(x['a'],x['b'],100):9d}  {x['pz']:5.2f}  {nstar_zi(x['az'],x['bz'],x['pz'],30):6d}  {nstar_zi(x['az'],x['bz'],x['pz'],100):7d}")
open("results_empirical.txt", "w").write("\n".join(out))
print("\n".join(out))
