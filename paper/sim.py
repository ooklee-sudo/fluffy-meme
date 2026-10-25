"""Optimal-stopping simulation: LLM repair attempts with human fallback (Beta-Geometric heterogeneity).
All parameters are SYNTHETIC; no empirical data are used."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln
rng = np.random.default_rng(42)
A, B, CAP = 0.4, 3.0, 300      # true Beta(a,b) heterogeneity of per-attempt success prob
H, c = 100.0, 1.0              # human fallback cost (outside option), cost per LLM attempt

def draw(n, cap):
    p = rng.beta(A, B, n); t = rng.geometric(p)
    return np.where(t <= cap, t, cap + 1)

def cost(t, k):                 # expected total cost under "try up to k, then human"
    return np.where(t <= k, c * t, c * k + H)

def fit(t, cap):
    s = t <= cap
    def nll(th):
        a, b = np.exp(th)
        ll = np.sum(betaln(a + 1, b + t[s] - 1) - betaln(a, b))
        ll += (~s).sum() * (betaln(a, b + cap) - betaln(a, b))
        return -ll
    return np.exp(minimize(nll, np.log([0.5, 2.0]), method="Nelder-Mead").x)

def n_star(a, b): return int(max(0, np.ceil(a * H / c - a - b)))   # attempt n+1 is made iff a*H/(a+b+n) > c

T = draw(400_000, CAP)
ns = n_star(A, B)
print(f"Theory: n* = ceil(aH/c - a - b) = {ns}")
rows = {}
rows["human only (k=0)"] = cost(T, 0).mean()
for k in [1, 3, 5, 10, 20, 40, 80, 160]: rows[f"fixed k={k}"] = cost(T, k).mean()
rows[f"optimal stopping n*={ns}"] = cost(T, ns).mean()
# brute-force check of optimum
ks = np.arange(0, 120); best = ks[np.argmin([cost(T, k).mean() for k in ks])]
print("brute-force optimal k:", best)
# naive homogeneous-p policy: p = pooled 1/mean(t) -> continue iff pH>c always -> never stop (cap)
p_hat = 1 / T[T <= CAP].mean(); print(f"homogeneous p_hat={p_hat:.3f}, p_hat*H={p_hat*H:.2f} > c -> 'never stop'")
rows["homogeneous-p policy (k=CAP)"] = cost(T, CAP).mean()
# estimated prior
for N in [50, 200, 1000]:
    out = []
    for _ in range(100):
        a, b = fit(draw(N, 30), 30); out.append(cost(T[:50000], n_star(a, b)).mean())
    rows[f"estimated prior, N={N} (mean±sd)"] = f"{np.mean(out):.2f} ± {np.std(out):.2f}"
for k, v in rows.items(): print(f"{k:42s}", v if isinstance(v, str) else round(float(v), 2))
print("P(solve by LLM | n*) =", round(float((T <= ns).mean()), 3))
# comparative statics
print("comparative statics n*(H):", {h: int(max(0, np.ceil(A*h/c - A - B))) for h in [10, 50, 100, 200, 500]})
print("value of heterogeneity: n* with homog. p=a/(a+b) known per-bug =", "never stops if pH>c")

from scipy.special import betaln as bl
def exact(k):
    surv = np.exp([bl(A, B+j)-bl(A, B) for j in range(k+1)])
    return c*surv[:k].sum() + H*surv[k]
print("EXACT expected cost: k=36", round(exact(36),3), " k=37", round(exact(37),3), " k=0", exact(0))
print("exact argmin:", min(range(0,200), key=exact), " P(solve)=", round(1-np.exp(bl(A,B+37)-bl(A,B)),3))
print("savings vs human-only: %.1f%%" % (100*(1-exact(37)/H)), " vs best fixed k=10: %.1f%%"%(100*(1-exact(37)/exact(10))))
