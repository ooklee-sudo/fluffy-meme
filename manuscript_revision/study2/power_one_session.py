"""Power for the cheapest design: ONE session, conditions C (choose before code exists) and A (artifact in hand) only.
Tests H1, the possession effect tau_A - tau_C = ln(lam/beta) > 0. Cannot separate beta from lam, and cannot test the lapse (H2).
Same decision model and noise assumptions as power_simulation.py."""
import numpy as np, statsmodels.api as sm, sys
rng = np.random.default_rng(77)
X = np.array([-0.2, 0.3, 0.8, 1.3]); REPS = 2
def sim(n, beta, lam, s, rr):
    lb = np.log(beta) + 0.2 * rng.standard_normal(n) if beta < 1 else np.zeros(n)
    ll = np.log(lam) + 0.2 * rng.standard_normal(n) if lam > 1 else np.zeros(n)
    tC = 0.05 + 0.4 * rng.standard_normal(n); x = np.repeat(X, REPS); rows = []
    for cond, tau in (("C", tC), ("A", tC + ll - lb)):
        for i in range(n):
            y = (x + rng.logistic(0, s, len(x)) > tau[i]).astype(int)
            if rr: y = np.where(rng.random(len(x)) < rr, rng.integers(0, 2, len(x)), y)
            rows.append(np.column_stack([np.full(len(x), i), x, np.full(len(x), cond == "A"), y]))
    return np.vstack(rows)
def reject(d):
    m = sm.Logit(d[:, 3], sm.add_constant(d[:, [1, 2]])).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d[:, 0].astype(int)})
    return m.params[2] / m.bse[2] < -1.96            # gamma_A < 0  <=>  threshold shifts up under possession
SIMS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
SC = {"rational (beta=1, lam=1)": (1, 1), "mild (beta=.85, lam=1.2)": (.85, 1.2), "weaker (beta=.9, lam=1.1)": (.9, 1.1), "both (beta=.7, lam=1.5)": (.7, 1.5)}
NO = {"baseline (s=0.5)": dict(s=0.5, rr=0.0), "noisy (s=0.9, 15% random)": dict(s=0.9, rr=0.15)}
print(f"{SIMS} simulations per cell; 16 decisions per participant (8 C + 8 A); power of H1 (possession effect), two-sided 5%\n")
for nn, kw in NO.items():
    print("===", nn); print(f"{'scenario':32s}" + "".join(f"{n:>7d}" for n in (40, 60, 80, 100, 120)))
    for sc, (b, l) in SC.items():
        print(f"{sc:32s}" + "".join(f"{np.mean([reject(sim(n, b, l, **kw)) for _ in range(SIMS)]):7.2f}" for n in (40, 60, 80, 100, 120)))
    print()
