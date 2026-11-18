"""Check the multi-type version of Proposition 6' against value iteration on the count vector (N_1, N_2).
Types j=1..J: errors e_j ~ Poisson(mu_j); each type-j error derails with prob tw_j and triggers self-transfer with th_j.
Closed form: continue iff  prod_j (1-tw_j)^{N_j} >= RHS,
  RHS = exp(sum_j mu_j * tt_j) * [ (k + c*sum mu_j)/(qF) - rho * (H-F)/F ],  tt_j = tw_j + th_j - tw_j*th_j,  rho = exp(-sum mu_j th_j)
i.e. stop iff  sum_j w_j N_j >= -ln RHS  with w_j = -ln(1-tw_j)."""
import math, itertools
import numpy as np

def pm(mu, emax=8): return np.array([math.exp(-mu) * mu**i / math.factorial(i) for i in range(emax + 1)])

def run(seed):
    rng = np.random.default_rng(seed)
    k = rng.uniform(0.5, 2); c = rng.uniform(1, 8); q = rng.uniform(0.04, 0.3); H = rng.uniform(15, 80); F = rng.uniform(30, 200)
    mu = rng.uniform(0.02, 0.25, 2); tw = rng.uniform(0.0, 0.6, 2); th = rng.choice([0.0, 1.0], 2) * rng.uniform(0.02, 0.6, 2)
    G = 10; emax = 6
    P = [pm(mu[0], emax), pm(mu[1], emax)]
    P = [p / p.sum() for p in P]
    V = np.full((G + emax + 1, G + emax + 1), H)
    def cont(V, n1, n2):
        tot = k + c * (mu[0] + mu[1])
        for e1 in range(emax + 1):
            for e2 in range(emax + 1):
                pr = P[0][e1] * P[1][e2]
                s = 1 - (1 - th[0]) ** e1 * (1 - th[1]) ** e2
                m1, m2 = n1 + e1, n2 + e2
                pi = 1 - (1 - tw[0]) ** m1 * (1 - tw[1]) ** m2
                tot += pr * (s * H + (1 - s) * (q * F * pi + (1 - q) * V[min(m1, V.shape[0]-1), min(m2, V.shape[1]-1)]))
        return tot
    for _ in range(3000):
        Vn = V.copy()
        for n1 in range(G + 1):
            for n2 in range(G + 1):
                Vn[n1, n2] = min(H, cont(V, n1, n2))
        d = np.max(np.abs(Vn - V)); V = Vn
        if d < 1e-11: break
    tt = tw + th - tw * th; rho = math.exp(-float(np.sum(mu * th)))
    rhs = math.exp(float(np.sum(mu * tt))) * ((k + c * mu.sum()) / (q * F) - rho * (H - F) / F)
    bad = tot = 0
    for n1 in range(G + 1):
        for n2 in range(G + 1):
            stop_vi = H <= cont(V, n1, n2) + 1e-9
            lhs = (1 - tw[0]) ** n1 * (1 - tw[1]) ** n2
            stop_cf = lhs <= rhs + 1e-12
            # skip states within numerical noise of the boundary
            if abs(lhs - rhs) < 1e-7: continue
            tot += 1; bad += (stop_vi != stop_cf)
    return bad, tot

if __name__ == "__main__":
    B = T = 0
    for sd in range(25):
        b, t = run(sd); B += b; T += t
    print(f"multi-type closed form vs value iteration over 25 random 2-type models: mismatching states {B} of {T}")
