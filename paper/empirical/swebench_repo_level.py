"""Repository-level (SWE-bench) extension.
(A) Calibrate Beta-geometric (a,b) from published pass@1 / pass@k pairs (aggregate coverage curves).
(B) Cross-submission heterogeneity of instance difficulty from official results (proxy, NOT attempt-level)."""
import json, glob, os, sys, numpy as np
from scipy.optimize import brentq, minimize
from scipy.special import betaln, gammaln
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/user/swe-bench/experiments/evaluation"
out = []; P = out.append

cov = lambda a, b, k: 1 - np.exp(betaln(a, b+k) - betaln(a, b))
def calib(m, k, ck):                       # mean=m (pass@1), coverage at k = ck
    f = lambda la: cov(np.exp(la), np.exp(la)*(1-m)/m, k) - ck
    a = np.exp(brentq(f, -12, 6)); return a, a*(1-m)/m
nstar = lambda a, b, r: int(max(0, np.ceil(a*r - a - b)))
P("== (A) Calibration from published coverage points (aggregate; SWE-bench Verified=500 tasks unless noted) ==")
P("source                                   pass@1  pass@k   k     a      b     N*(H/c=30) N*(100) N*(300) N*(1000)")
pts = [("DeepSWE-Preview (Qwen3-32B), Verified", .422, 16, .710),
       ("Cortexa o3, Verified (pass@7=75%)", None, 7, .75),
       ("Large Language Monkeys, Lite, DS-Coder-V2", .159, 250, .56)]
for name, m, k, ck in pts:
    if m is None: P(f"{name:40s}  (pass@1 not stated in repo README; skipped)"); continue
    a, b = calib(m, k, ck)
    P(f"{name:40s}  {m:5.3f}  {ck:5.3f} {k:4d}  {a:5.3f}  {b:6.3f}   {nstar(a,b,30):6d}  {nstar(a,b,100):6d}  {nstar(a,b,300):6d}  {nstar(a,b,1000):6d}")
    ks = [1, 2, 4, 8, 16, 32, 64, 128, 250]
    P("    implied coverage: " + ", ".join(f"@{kk}={cov(a,b,kk):.2f}" for kk in ks))

P("")
P("== (B) Cross-submission instance heterogeneity (proxy; systems differ, not iid samples) ==")
for split, nexp in [("lite", 300), ("verified", 500)]:
    resolved, nsub = {}, 0
    for f in glob.glob(f"{ROOT}/{split}/*/results/results.json"):
        try: d = json.load(open(f))
        except Exception: continue
        r = d.get("resolved")
        if not r: continue
        nsub += 1
        for i in r: resolved[i] = resolved.get(i, 0) + 1
    ids = set(resolved)
    k = np.array(list(resolved.values()))
    never = nexp - len(ids)
    P(f"{split}: {nsub} submissions; instances resolved by >=1 submission: {len(ids)}/{nexp}; never resolved: {never} ({100*never/nexp:.1f}%)")
    q = np.percentile(k/nsub, [10, 25, 50, 75, 90]); P(f"   share-of-systems resolving an instance (resolved-by-some instances) percentiles 10/25/50/75/90: {np.round(q,2)}")
    # Beta-binomial over all instances incl. zeros, n = nsub
    kk = np.concatenate([k, np.zeros(never, int)]); n = nsub
    lc = gammaln(n+1) - gammaln(kk+1) - gammaln(n-kk+1)
    nll = lambda t: -(lc + betaln(kk+np.exp(t[0]), n-kk+np.exp(t[1])) - betaln(np.exp(t[0]), np.exp(t[1]))).sum()
    r_ = minimize(nll, np.log([.5, .5]), method="Nelder-Mead"); a, b = np.exp(r_.x)
    P(f"   Beta fit across systems: a={a:.2f}, b={b:.2f} (U-shaped if both<1), mean={a/(a+b):.2f}")
open("results_swebench.txt", "w").write("\n".join(out)); print("\n".join(out))
