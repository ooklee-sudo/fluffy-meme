"""Robustness analyses for the Electronic Markets manuscript (not preregistered).

Brand-volume terciles for H5 (judge win rate, NLL gap) and H7 (decay slopes, horizon), judge tie and position
checks, alternative client traits and targeting shares for H10, and sensitivity of the maintenance threshold.

Usage: python analyze_robustness.py data/twcs_pairs.jsonl   (run from tt_entropy/, after H5 and H7)
"""
import collections, glob, json, os, sys
import numpy as np
from scipy.stats import spearmanr, wilcoxon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from real_options import Params, beta, v_star
from dataclasses import replace

vol = collections.Counter(json.loads(l)["tenant"] for l in open(sys.argv[1] if len(sys.argv) > 1 else "data/twcs_pairs.jsonl"))
gens = {json.load(open(p))["brand"]: json.load(open(p)) for p in glob.glob("results/h5_gen/*.json")}
recs = [json.loads(l) for l in open("results/h5_judge.jsonl")]

def winner(r):
    a, b = (r["second"], r["first"]) if r["flip"] else (r["first"], r["second"])
    x = str(r["verdict"].get("overall", "tie")).strip().upper()
    return a if x == "A" else b if x == "B" else "tie"

wr, pos, ties, n = collections.defaultdict(list), collections.defaultdict(list), 0, 0
for r in recs:
    if r["judge"] != "anthropic/claude-haiku-5.5" or (r["first"], r["second"]) != ("lora:1", "rag-8"):
        continue
    w = winner(r); n += 1; ties += w == "tie"
    s = 1.0 if w == "lora:1" else 0.5 if w == "tie" else 0.0
    wr[r["brand"]].append(s); pos["adapter shown second" if r["flip"] else "adapter shown first"].append(s)
print(f"H5 judge: ties {ties / n:.3f} of {n}; " + "; ".join(f"{k} {np.mean(v):.3f} (n={len(v)})" for k, v in pos.items()))
names = sorted(wr)
W = np.array([np.mean(wr[b]) for b in names]); V = np.array([vol[b] for b in names])
G = np.array([gens[b]["rel_gain"]["lora:1"] - gens[b]["rel_gain"]["rag-8"] for b in names])
We = np.array([np.mean([s for s in wr[b] if s != 0.5]) for b in names])
print(f"win rate excluding ties {We.mean():.3f}, p = {wilcoxon(We - 0.5).pvalue:.4f}; win~volume rho = {spearmanr(W, V)[0]:.2f} (p = {spearmanr(W, V)[1]:.2f})")
g = np.digitize(V, np.quantile(V, [1 / 3, 2 / 3]))
for k, lab in enumerate(("small", "medium", "large")):
    m = g == k
    print(f"H5 {lab}: n={m.sum()} replies {V[m].min()}-{V[m].max()} win {W[m].mean():.3f} (p = {wilcoxon(W[m] - 0.5).pvalue:.3f}), "
          f"above/below {(W[m] > 0.5).sum()}/{(W[m] < 0.5).sum()}, NLL gap {G[m].mean():.3f} ({(G[m] > 0).sum()} of {m.sum()})")

rows = [json.load(open(p)) for p in sorted(glob.glob("results/h7_drift/*.json"))]
def slope(r, k):
    x, y = np.array([(int(w), v[k]) for w, v in r["weeks"].items() if w.isdigit()], float).T
    return np.polyfit(x, y, 1)[0]
SA = np.array([slope(r, "lora_stale_rel") for r in rows]); SR = np.array([slope(r, "rag_fresh_rel") for r in rows])
V7 = np.array([vol[r.get("brand") or r.get("tenant")] for r in rows])
lead2 = np.array([r["weeks"]["2"]["lora_stale_rel"] - r["weeks"]["2"]["rag_fresh_rel"] for r in rows])
g = np.digitize(V7, np.quantile(V7, [1 / 3, 2 / 3]))
for k, lab in enumerate(("small", "medium", "large")):
    m = g == k; d = SA[m] - SR[m]
    print(f"H7 {lab}: n={m.sum()} replies {V7[m].min()}-{V7[m].max()} slopes {SA[m].mean():.4f} vs {SR[m].mean():.4f}, "
          f"faster {(d < 0).sum()} (p = {wilcoxon(d).pvalue:.4f}), horizon {2 + lead2[m].mean() / (SR[m].mean() - SA[m].mean()):.1f} weeks")

b10 = sorted(gens); gain = np.array([gens[b]["rel_gain"]["lora:1"] for b in b10])
for f in ("response_type_token_ratio", "distinct_response_share", "mean_response_tokens"):
    x = np.array([gens[b]["features"][f] for b in b10]); print(f"H10 {f} ~ gain: rho = {spearmanr(x, gain)[0]:.2f}")
ttr = np.array([gens[b]["features"]["response_type_token_ratio"] for b in b10]); rng = np.random.default_rng(0)
for k in (10, 17, 25):
    share = gain[np.argsort(ttr, kind="stable")[:k]].sum() / gain.sum()
    draws = np.array([gain[rng.choice(len(gain), k, replace=False)].sum() / gain.sum() for _ in range(20000)])
    print(f"H10 top {k}: rule {share:.3f}, random {draws.mean():.3f}, oracle {np.sort(gain)[::-1][:k].sum() / gain.sum():.3f}, share of draws >= rule {(draws >= share).mean():.4f}")

p0 = Params(rho=0.10, mu=52 / 7, g=0.20, sigma=0.40, C_N=45.0); q0, lam = 0.441, 0.03985 / 0.284  # as in real_options_econ.py
cases = [("base", p0, 0.887), ("sigma 0.2", replace(p0, sigma=0.2), 0.887), ("sigma 0.6", replace(p0, sigma=0.6), 0.887),
         ("g 0", replace(p0, g=0.0), 0.887), ("g 0.4", replace(p0, g=0.4), 0.887), ("rho 0.05", replace(p0, rho=0.05), 0.887),
         ("rho 0.2", replace(p0, rho=0.2), 0.887), ("R 0.80", p0, 0.80), ("R 0.95", p0, 0.95)]
for name, p, R in cases:
    vs = v_star(R, p); print(f"maintenance {name}: beta {beta(p):.2f}, v* {vs:,.0f} GPU-s/yr, volume threshold {vs / (lam * q0):,.0f} requests/yr")
