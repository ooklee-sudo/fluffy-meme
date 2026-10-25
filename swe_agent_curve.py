"""Pilot: cumulative issue-resolution coverage vs. number of attempts for LLM agents.

Data: nebius/SWE-agent-trajectories (Hugging Face, CC-BY-4.0), one parquet shard.
  Columns used: instance_id, model_name, target (resolved), exit_status.
Coverage(k) = share of instances solved at least once within k random attempts (averaged over shuffles).
  - reach a  = asymptote of the curve (share of instances this agent can ever solve),
  - rate  b  = how fast it saturates.
Fits Goel-Okumoto  m(k)=a(1-exp(-b k))  and Musa-Okumoto  m(k)=a*ln(1+b k) (no finite asymptote).

Usage: python3 -I swe_agent_curve.py <path to train-0000x-of-00012.parquet> [KMAX=12]
"""
import sys
import numpy as np
import pyarrow.parquet as pq
from scipy.optimize import curve_fit

df = pq.read_table(sys.argv[1], columns=["instance_id", "model_name", "target"]).to_pandas()
rng = np.random.default_rng(0)
KMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 12
K = list(range(1, KMAX + 1))
# Fixed instance set: only instances with >= KMAX attempts, so every k uses the same instances.
# (Letting the set change with k mixes populations and distorts the curve.)
groups = [g.target.values for _, g in df.groupby("instance_id") if len(g) >= KMAX]
print(f"fixed set: {len(groups)} instances with >= {KMAX} attempts (of {df.instance_id.nunique()})")


def coverage(arrs, k, reps=300):
    return float(np.mean([np.mean([rng.permutation(a)[:k].any() for a in arrs]) for _ in range(reps)]))


ks = np.array(K, float)
cov = np.array([coverage(groups, k) for k in K])
print("attempts k | coverage(k)")
for k, c in zip(ks, cov):
    print(f"   {int(k):3d}     |  {c:.3f}")

go = lambda k, a, b: a * (1 - np.exp(-b * k))
mo = lambda k, a, b: a * np.log1p(np.abs(b) * k)
for name, f, p0, bounds in (("Goel-Okumoto", go, (0.3, 0.3), ([0, 0], [1, 10])),
                            ("Musa-Okumoto", mo, (0.1, 1.0), ([0, 0], [10, 100]))):
    p, _ = curve_fit(f, ks, cov, p0=p0, bounds=bounds, maxfev=20000)
    sse = float(((f(ks, *p) - cov) ** 2).sum())
    tail = "" if name.startswith("Goel") else f"  coverage extrapolated to k=100: {f(100.0, *p):.3f}"
    print(f"{name:13s} a={p[0]:.3f} b={p[1]:.3f}  SSE={sse:.5f}{tail}")
# instance heterogeneity: share of instances never solved and per-instance solve-rate quantiles
rate = np.array([a.mean() for a in groups])
print(f"never solved: {np.mean(rate == 0):.2f} | solved in every attempt: {np.mean(rate == 1):.2f} | "
      f"median per-instance solve rate {np.median(rate):.2f}")
