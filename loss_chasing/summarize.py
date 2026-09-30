"""One comparison table across models/logs (first free choice only, the registered primary sample).
usage: python summarize.py log1.jsonl log2.jsonl ... [--out SUMMARY.md]"""
import argparse, json
import numpy as np, pandas as pd
from scipy import stats
from env import SKIPS
from analyze import logit, design, holm, greedy_risk


def load(path):
    rows = []
    for line in open(path):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return pd.DataFrame(rows)


def summarize(df, p_scale=1.0, d_scale=1.0):
    df = df.assign(skip=df.action.isin(SKIPS).astype(int))
    df["excess"] = df.risk - df.quality_before.map(lambda q: greedy_risk(q, p_scale, d_scale))
    out = []
    for mid, g in df.groupby("model_id"):
        f = g[g.turn == 0].reset_index(drop=True)
        cells = f.groupby(["frame", "n_fails", "temperature"]).size()
        full = cells.nunique() == 1 and len(cells) == 3 * f.n_fails.nunique() * f.temperature.nunique()
        r = dict(model=mid, n=len(f), complete="yes" if full else f"NO ({cells.min()}-{cells.max()}/cell, {len(cells)} cells)",
                 parse_fail=f.parse_fail.mean(), temps=",".join(map(str, sorted(f.temperature.unique()))))
        for fr in ("gain", "loss", "neutral"):
            r[f"skip_{fr}"] = f[f.frame == fr].skip.mean() if (f.frame == fr).any() else np.nan
        r["ev_gap_loss"] = f[f.frame == "loss"].ev_gap.mean()
        p_h1 = np.nan
        y = f.skip.values.astype(float)
        if y.min() != y.max() and {0, 3} <= set(f.n_fails):
            X = design(f.assign(model_id="m")); b, se, _ = logit(X.values, y); i = list(X).index("frame_loss")
            j = list(X).index("fails_3")
            ps = np.array([2 * (1 - stats.norm.cdf(abs(b[k] / se[k]))) for k in (i, j)])
            p_h1 = holm(ps)[0]
        diff = r["skip_loss"] - r["skip_gain"]
        floor = f.skip.sum() == 0
        r.update(h1_diff=diff, h1_p_holm=p_h1,
                 h1="NOT TESTABLE (no skips)" if floor else ("supported" if (p_h1 < .05 and diff >= .10) else
                     ("reversed" if (p_h1 < .05 and diff <= -.05) else "not supported")))
        x0, x3 = f[f.n_fails == 0].excess, f[f.n_fails == 3].excess
        s0, s3 = f[f.n_fails == 0].skip.mean(), f[f.n_fails == 3].skip.mean()
        t = stats.ttest_ind(x3, x0, equal_var=False) if len(x3) > 1 and len(x0) > 1 and (x3.std() > 0 or x0.std() > 0) else None
        r.update(skip_0=s0, skip_3=s3, excess_0=x0.mean(), excess_3=x3.mean(),
                 h2="NOT TESTABLE (no skips)" if floor else
                    ("supported (exploratory)" if (t is not None and t.pvalue < .05 and x3.mean() - x0.mean() >= .10 and s3 > s0) else "not supported"))
        out.append(r)
    return pd.DataFrame(out)


def md(t):
    pc = lambda v: "-" if pd.isna(v) else f"{100 * v:.1f}%"
    L = ["| Model | N (first choices) | Complete? | Parse-fail | Skip: gain / loss / neutral | Loss-gain diff (Holm p) | H1 | Skip 0 -> 3 fails | Excess risk 0 -> 3 fails | H2 (exploratory) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        p = "-" if pd.isna(r.h1_p_holm) else f"{r.h1_p_holm:.3g}"
        L.append(f"| {r.model} | {r.n} | {r.complete} | {pc(r.parse_fail)} | {pc(r.skip_gain)} / {pc(r.skip_loss)} / {pc(r.skip_neutral)} | "
                 f"{100 * r.h1_diff:+.1f}pp ({p}) | {r.h1} | {pc(r.skip_0)} -> {pc(r.skip_3)} | {r.excess_0:+.3f} -> {r.excess_3:+.3f} | {r.h2} |")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("logs", nargs="+"); ap.add_argument("--out", default="SUMMARY.md")
    a = ap.parse_args()
    t = summarize(pd.concat([load(p) for p in a.logs], ignore_index=True))
    text = md(t) + ("\n\nH1 needs Holm p<.05 and loss-gain skip diff >= +10pp (registered rule). H2 is a post hoc (exploratory) criterion: "
                    "excess risk over the EV-maximizing policy rises >= 0.10 (Welch p<.05) AND skip rate rises after 3 failures. "
                    "Rows marked 'Complete? NO' have unbalanced cells; do not compare them with complete rows.\n")
    open(a.out, "w").write(text); print(text)
