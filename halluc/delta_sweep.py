"""Sensitivity to the verifier's detection probability delta (static gain is linear in delta by construction; the
informative part is whether the adaptive policy keeps its edge when outcomes are observed with less certainty).
Pooled budget, cross-fitted, content features; share of ALL errors caught (= delta x verified errors)."""
import argparse

import numpy as np

import alloc_eval as ae


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="task:event:path")
    ap.add_argument("--deltas", nargs="+", type=float, default=[1.0, 0.8, 0.6, 0.4])
    ap.add_argument("--phis", nargs="+", type=float, default=[0.3, 0.5])
    a = ap.parse_args()
    for spec in a.runs:
        task, event, path = spec.split(":", 2)
        docs = ae.load(path, "unit", event, True)
        rg = np.random.default_rng(0)
        fold = np.zeros(len(docs), int)
        fold[rg.permutation(len(docs))] = np.arange(len(docs)) % 5
        fits = [ae.fit([docs[i] for i in np.where(fold != f)[0]]) for f in range(5)]
        print(f"\n{task}/{path.split('labs_')[-1]}  ({len(docs)} docs, content features)")
        print(f"{'delta':>6}{'phi':>5}{'uniform':>9}{'static':>8}{'adaptive':>9}   adaptive-static [95% CI]")
        for delta in a.deltas:
            for phi in a.phis:
                agg = {k: np.zeros(len(docs)) for k in ("uniform", "static", "adaptive")}
                tot = np.zeros(len(docs))
                for f in range(5):
                    te = np.where(fold == f)[0]
                    c, t = ae.eval_pooled([docs[i] for i in te], fits[f][0], fits[f][1], phi, delta, np.random.default_rng(f))
                    for k in agg:
                        agg[k][te] = c[k]
                    tot[te] = t
                lo, hi = ae.boot(agg["adaptive"], agg["static"], tot, B=1000)
                T = tot.sum()
                print(f"{delta:6.1f}{phi:5.1f}{agg['uniform'].sum()/T:9.3f}{agg['static'].sum()/T:8.3f}{agg['adaptive'].sum()/T:9.3f}   "
                      f"{(agg['adaptive'].sum()-agg['static'].sum())/T:+.3f} [{lo:+.3f},{hi:+.3f}]", flush=True)


if __name__ == "__main__":
    main()
