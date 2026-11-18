"""Illustrative case for the Electronic Markets manuscript: a provider with 100 clients applies the decision
framework. Annual volume of each client = its number of replies in the corpus x 6 (the corpus covers about
two months), for the 100 largest brands. Usage: python case_portfolio.py data/twcs_pairs.jsonl [scale]
"""
import collections, json, sys
import numpy as np
vol = collections.Counter(json.loads(l)["tenant"] for l in open(sys.argv[1] if len(sys.argv) > 1 else "data/twcs_pairs.jsonl"))
SCALE = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0  # 0.1 = a provider whose clients are ten times smaller
V = np.array(sorted(vol.values(), reverse=True)[:100], float) * 6 * SCALE
c_R, c_A, F = 0.06335, 0.02643, 45.0          # GPU-s per request (retrieval, adapter); GPU-s per training run
mu_up, mu_drift = 2.0, 52 / 7                  # base-model upgrades and drift episodes per year
q_R, q_A, R = 0.351, 0.460, 0.885              # relative gain: retrieval, fresh adapter; recovery of a stale adapter
lam, v_star = 0.03985 / 0.284, 3284.785        # value of quality (lower bound) and retraining threshold (GPU-s/yr)
q_stale = q_A * R
f_fresh_up = mu_up / (mu_up + mu_drift)        # share of time an adapter rebuilt only at upgrades is fresh
q_up = f_fresh_up * q_A + (1 - f_fresh_up) * q_stale
be = F * mu_up / (c_R - c_A)                   # break-even volume with upgrade rebuilds only
V_thr = v_star / (lam * 0.441)                 # volume above which drift rebuilds pay (Table 6, q of E4)

def policy(adapter, rebuild_drift):
    gpu = np.where(adapter, c_A * V + F * (mu_up + np.where(rebuild_drift, mu_drift, 0)), c_R * V)
    q = np.where(adapter, np.where(rebuild_drift, q_A, q_up), q_R)
    return gpu.sum() / 3600, (q * V).sum() / V.sum(), adapter.sum(), (adapter & rebuild_drift).sum()

allA, none = np.ones(100, bool), np.zeros(100, bool)
fw_adapter = V > be; fw_drift = fw_adapter & (V >= V_thr)
rows = [("A. Retrieval for every client", *policy(none, none)),
        ("B. Adapter for every client, rebuilt at model upgrades", *policy(allA, none)),
        ("C. Adapter for every client, also rebuilt at every drift episode", *policy(allA, allA)),
        ("D. Decision framework", *policy(fw_adapter, fw_drift))]
print(f"clients {len(V)}, annual volume {V.min():,.0f}-{V.max():,.0f} (median {np.median(V):,.0f}, total {V.sum():,.0f})")
print(f"break-even {be:,.0f} requests/yr; drift-rebuild threshold {V_thr:,.0f}; stale quality {q_stale:.3f}; upgrade-only quality {q_up:.3f}")
for name, gpu, q, na, nd in rows:
    print(f"{name}: {gpu:,.1f} GPU-h/yr, volume-weighted gain {q:.3f}, adapters {na}, drift rebuilds {nd}")
small = V[~fw_adapter]; print(f"retrieval clients: {len(small)}, their share of volume {small.sum() / V.sum():.2%}")
mid = V[fw_adapter & ~fw_drift]; print(f"adapter, upgrade rebuild only: {len(mid)}, share {mid.sum() / V.sum():.2%}")
big = V[fw_drift]; print(f"adapter, drift rebuild: {len(big)}, share {big.sum() / V.sum():.2%}")
gA, qA_ = rows[0][1], rows[0][2]; gD, qD = rows[3][1], rows[3][2]
print(f"D vs A: GPU-h {gD / gA - 1:+.1%}, gain {qD - qA_:+.3f}; D vs C: GPU-h {gD / rows[2][1] - 1:+.1%}, gain {qD - rows[2][2]:+.3f}")
# training share
tr = F * (mu_up * fw_adapter.sum() + mu_drift * fw_drift.sum()) / 3600; print(f"D training GPU-h {tr:.2f}")
