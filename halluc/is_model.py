"""Decision-theoretic illustration (MODEL.md section 8): when to verify at all, and how much targeting is worth.

Per unit: verification costs c (=1), detects an error w.p. delta, an undetected error costs L. With the cross-fitted
predictive error probability q_t of each unit (5-fold, content features), the cost-minimising rule is
    verify unit t  <=>  delta * L * q_t >= c         (Proposition 5)
Realised cost = c * #verified + L * sum_t y_t * (1 - delta * v_t)   (expected over detection; y = observed labels).
Baselines: verify nothing, verify everything. Uniform random verification of a fraction is linear in the fraction, so its
best choice is one of those two corners; 'best baseline' = min(none, all).
Closed form for the model's own value of targeting:  V = min(sum a+, sum a-),  a_t = delta*L*q_t - c   (Prop. 5).
"""
import argparse

import numpy as np

import alloc_eval as ae


def crossfit_q(docs, seed=0, folds=5):
    rg = np.random.default_rng(seed)
    fold = np.zeros(len(docs), int)
    fold[rg.permutation(len(docs))] = np.arange(len(docs)) % folds
    qs, ys, tests = [None] * len(docs), [None] * len(docs), [None] * len(docs)
    for f in range(folds):
        g, t = ae.fit([docs[i] for i in np.where(fold != f)[0]])
        for i in np.where(fold == f)[0]:
            qs[i] = ae.prior_p(docs[i]["X"] @ g, t)
            ys[i] = docs[i]["y"]
    return np.concatenate(qs), np.concatenate(ys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="task:event:path")
    ap.add_argument("--deltas", nargs="+", type=float, default=[1.0, 0.8])
    ap.add_argument("--ratios", nargs="+", type=float, default=[2, 3, 5, 8, 12, 20, 50])
    a = ap.parse_args()
    for spec in a.runs:
        task, event, path = spec.split(":", 2)
        docs = ae.load(path, "unit", event, True)
        q, y = crossfit_q(docs)
        print(f"\n{task}/{path.split('labs_')[-1]}: {len(y)} units, error rate {y.mean():.3f}, mean cross-fitted q {q.mean():.3f}, "
              f"q range (5%-95%) {np.percentile(q, 5):.2f}-{np.percentile(q, 95):.2f}")
        for delta in a.deltas:
            print(f"\n  delta = {delta}")
            print(f"  {'L/c':>5}{'none':>8}{'all':>8}{'targeted':>10}{'verified':>10}{'saving vs best baseline':>26}{'  closed-form V':>16}")
            for L in a.ratios:
                none = L * y.sum() / len(y)
                allv = 1.0 + L * (1 - delta) * y.sum() / len(y)
                v = delta * L * q >= 1.0
                tgt = (v.sum() + L * (y * (1 - delta * v)).sum()) / len(y)
                best = min(none, allv)
                aa = delta * L * q - 1.0
                V = min(aa[aa > 0].sum(), -aa[aa < 0].sum()) / len(y)
                print(f"  {L:5.0f}{none:8.3f}{allv:8.3f}{tgt:10.3f}{v.mean():10.2f}{(best - tgt) / best:25.1%}{V:16.3f}")


if __name__ == "__main__":
    main()
