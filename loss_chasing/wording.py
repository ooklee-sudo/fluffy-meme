"""Wording-robustness report: does a frame effect survive paraphrasing the headline?
usage: python wording.py log.jsonl [--fails 0]   (logs written with run_experiment.py --variants 0 1 2 3)"""
import argparse, json
import numpy as np, pandas as pd
from scipy import stats
from env import SKIPS
from analyze import logit


def load(p):
    rows = []
    for line in open(p):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("--fails", type=int, default=0)
    a = ap.parse_args()
    df = load(a.log)
    if "variant" not in df: df["variant"] = 0
    df = df[(df.turn == 0) & (df.n_fails == a.fails)].copy()
    df["skip"] = df.action.isin(SKIPS).astype(int)
    for mid, g in df.groupby("model_id"):
        print(f"== {mid}: first-choice skip rate, {a.fails} injected failures (N per cell = {int(g.groupby(['frame','variant']).size().min())}), parse-fail {g.parse_fail.mean():.3f}")
        t = g.pivot_table(index="variant", columns="frame", values="skip", aggfunc="mean")[["gain", "loss", "neutral"]]
        t["loss-gain (pp)"] = 100 * (t.loss - t.gain); t["neutral-mean(gain,loss) (pp)"] = 100 * (t.neutral - (t.gain + t.loss) / 2)
        print((t.drop(columns=["loss-gain (pp)", "neutral-mean(gain,loss) (pp)"]) * 100).round(1).assign(**{
            "loss-gain (pp)": t["loss-gain (pp)"].round(1), "neutral-mean(gain,loss) (pp)": t["neutral-mean(gain,loss) (pp)"].round(1)}).to_string())
        y = g.skip.values.astype(float)
        if y.min() == y.max():
            print("  no variation in skipping: frame effects not estimable (floor)\n"); continue
        V = sorted(g.variant.unique())
        X = np.column_stack([np.ones(len(g)), (g.frame == "loss") * 1., (g.frame == "neutral") * 1.] + [(g.variant == v) * 1. for v in V[1:]])
        b, se, l1 = logit(X, y)
        for nm, i in (("loss vs gain", 1), ("neutral vs gain", 2)):
            print(f"  logit, variant fixed effects: {nm}: coef {b[i]:+.2f} (se {se[i]:.2f}), p = {2 * (1 - stats.norm.cdf(abs(b[i] / se[i]))):.3g}")
        _, _, l0 = logit(np.column_stack([np.ones(len(g))] + [(g.variant == v) * 1. for v in V[1:]]), y)
        lr = 2 * (l1 - l0); print(f"  frame effect overall: LR = {lr:.1f}, df = 2, p = {1 - stats.chi2.cdf(lr, 2):.3g}")
        n_neu = int((t["neutral"] > t[["gain", "loss"]].max(axis=1)).sum()); n_lg = int((t["loss"] > t["gain"]).sum())
        print(f"  variants where neutral is the highest frame: {n_neu} of {len(V)}; where loss exceeds gain: {n_lg} of {len(V)}\n")


if __name__ == "__main__":
    main()
