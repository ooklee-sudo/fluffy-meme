"""Sanity check on simulated data: recovery of alpha and null false-positive rate."""
import numpy as np
from mixture import fit_reference, estimate_alpha, null_threshold

rng = np.random.default_rng(1)
V = 1500
p_true = rng.beta(0.6, 6.0, V)
q_true = p_true.copy()
shift = rng.choice(V, 150, replace=False)              # LLM over-uses 10% of words
q_true[shift] = np.clip(p_true[shift] * rng.uniform(1.5, 3.0, 150), 1e-4, 0.95)

def draw(n, a):
    from_llm = rng.random(n) < a
    P = np.where(from_llm[:, None], q_true, p_true)
    return (rng.random((n, V)) < P).astype(float)

# reference corpora (finite samples, as in practice)
p_hat = fit_reference(draw(3000, 0.0))
q_hat = fit_reference(draw(3000, 1.0))
holdout = draw(3000, 0.0)

print("alpha recovery (n=200 docs per group):")
for a in [0.0, 0.05, 0.10, 0.20, 0.40]:
    est = [estimate_alpha(draw(200, a), p_hat, q_hat) for _ in range(30)]
    print(f"  true {a:.2f}  mean est {np.mean(est):.3f}  sd {np.std(est):.3f}")

print("null false-positive rate with permutation threshold:")
for n in [5, 20, 200]:
    thr = null_threshold(holdout, p_hat, q_hat, n, n_perm=300, quantile=0.99)
    fp = np.mean([estimate_alpha(draw(n, 0.0), p_hat, q_hat) > thr for _ in range(300)])
    pw = np.mean([estimate_alpha(draw(n, 0.2), p_hat, q_hat) > thr for _ in range(300)])
    print(f"  n={n:>3}  threshold {thr:.3f}  FPR {fp:.3f}  power at alpha=0.20: {pw:.2f}")
