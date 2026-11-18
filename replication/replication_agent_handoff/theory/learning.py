"""Learning value under task heterogeneity, and contagion value, per model.
Heterogeneity only (alpha = 0): mu_i ~ Gamma(shape a, scale s); after t steps with N errors the posterior is
Gamma(a + N, rate 1/s + t), so the state is (t, N). Predictive errors per step are negative binomial.
Contagion only: mu fixed at its mean, Hawkes excitation (alpha, delta) as in numerics.py.
Costs as in numerics.py. Writes learning.json."""
import json
import numpy as np
from scipy.stats import nbinom
from model_core import solve, CU
k, c, q, H = 1.0, 5.0, 0.06, 40.0
def learn(a, s, T=300, Nmax=120, emax=25):
    b = 1 / s; N = np.arange(Nmax + 1); e = np.arange(emax + 1)
    W = np.full(Nmax + 1, H)                       # value at the horizon (reached with prob. < 1e-8)
    thr = {}
    for t in range(T - 1, -1, -1):
        r = a + N; p = (b + t) / (b + t + 1)       # predictive: NegBin(r, p), mean r / (b + t)
        P = nbinom.pmf(e[None, :], r[:, None], p); P /= P.sum(1, keepdims=True)
        Nn = np.minimum(N[:, None] + e[None, :], Nmax)
        cont = k + c * r / (b + t) + (1 - q) * (P * W[Nn]).sum(1)
        stop = cont >= H
        thr[t] = int(N[np.argmax(stop)]) if stop.any() else None
        W = np.minimum(H, cont)
    static = min(H, (k + c * a * s) / q)
    return dict(W0=float(W[0]), static=float(static), learning_value=float(static - W[0]),
                count_threshold={t: thr[t] for t in (0, 5, 10, 20, 40, 80)})
def main():
  est = json.load(open("../hawkes_re_results_all.json"))
  out = {}
  for m in ("swe-agent-llama-8b", "swe-agent-llama-70b", "swe-agent-llama-405b"):
      r = est[m]["re_hawkes"]; a, s = r["re_shape"], r["re_scale"]; mu = a * s
      L = learn(a, s)
      sol, _ = solve(mu, r["alpha"], r["delta"], k, c, q, H); cu = CU(mu, r["alpha"], r["delta"], k, c, q)
      out[m] = dict(branching=r["branching"], mu_mean=mu, re_cv=r["re_cv"],
                    contagion_value=float(min(H, cu) - sol["W0"]), contagion_x_star=sol["x_star"], **L)
  # heterogeneity sensitivity: same mean as 70B, varying CV
  r = est["swe-agent-llama-70b"]["re_hawkes"]; mu = r["re_shape"] * r["re_scale"]; sens = []
  for cv in (0.5, 1.0, 1.41, 2.0, 3.0):
      a = 1 / cv ** 2; s = mu / a; L = learn(a, s); sens.append(dict(cv=cv, learning_value=round(L["learning_value"], 3), W0=round(L["W0"], 3)))
  out["cv_sensitivity_70b_mean"] = sens
  json.dump(out, open("learning.json", "w"), indent=1); print(json.dumps(out, indent=1))

if __name__ == "__main__":
  main()
