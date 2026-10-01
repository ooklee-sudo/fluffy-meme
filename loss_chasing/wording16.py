"""Frame effect over many wordings: wording as the unit of replication.

usage: python wording16.py log1.jsonl [log2.jsonl ...] [--fails 0] [--md out.md]

For every (model, condition) it reports
  * overall skip rate and the loss-minus-gain and neutral-minus-gain differences averaged over wordings, with a
    95% cluster bootstrap interval that resamples WORDINGS (so the interval reflects wording-to-wording variation)
  * the spread of the loss-minus-gain difference across wordings, and how much of it exceeds binomial sampling noise
  * the share of variation in the wording x frame table of skip rates due to frame, wording, and their interaction
  * how many wordings put the loss frame above the gain frame
Condition = turns already spent when the first choice is made (column t); wording = column variant.
"""
import argparse, json
import numpy as np, pandas as pd
from env import SKIPS

FR = ["gain", "loss", "neutral"]


def load(paths):
    rows = []
    for p in paths:
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return pd.DataFrame(rows)


def table(g):
    """skip-rate matrix [wording x frame] and the matching counts."""
    rate = g.pivot_table(index="variant", columns="frame", values="skip", aggfunc="mean")[FR]
    n = g.pivot_table(index="variant", columns="frame", values="skip", aggfunc="count")[FR]
    return rate, n


def decompose(R, n):
    R = R.values; W = R.shape[0]
    grand = R.mean(); rm = R.mean(1, keepdims=True); cm = R.mean(0, keepdims=True)
    ss_frame = W * ((cm - grand) ** 2).sum(); ss_word = 3 * ((rm - grand) ** 2).sum()
    ss_int = ((R - rm - cm + grand) ** 2).sum(); tot = ((R - grand) ** 2).sum()
    noise = (R * (1 - R) / n.values).sum() * (W - 1) / W          # expected SS from sampling noise in cell rates (approx.)
    return dict(total=tot, frame=ss_frame / tot if tot else np.nan, wording=ss_word / tot if tot else np.nan,
                interaction=ss_int / tot if tot else np.nan, noise=min(1.0, noise / tot) if tot else np.nan)


def boot(vals, B=4000, seed=1):
    rng = np.random.default_rng(seed); v = np.asarray(vals)
    m = np.array([rng.choice(v, len(v)).mean() for _ in range(B)])
    return np.percentile(m, [2.5, 97.5])


def analyse(df, fails):
    df = df[(df.turn == 0) & (df.n_fails == fails)].copy()
    df["skip"] = df.action.isin(SKIPS).astype(int)
    out = []
    for (mid, t), g in df.groupby(["model_id", "t"]):
        if not set(FR) <= set(g.frame):
            print(f"[{mid}, {12 - int(t)} turns left] skipped: frames present {sorted(set(g.frame))}; the run was interrupted, rerun the batch file (it resumes)")
            continue
        rate, n = table(g)
        lg = (rate["loss"] - rate["gain"]).values; ng = (rate["neutral"] - rate["gain"]).values
        noise_var = ((rate["loss"] * (1 - rate["loss"]) / n["loss"]) + (rate["gain"] * (1 - rate["gain"]) / n["gain"])).mean()
        d = decompose(rate, n)
        rec = dict(model=mid, turns_left=12 - int(t), wordings=len(rate), episodes_per_cell=int(n.values.min()), skip=g.skip.mean(),
                   loss_minus_gain=lg.mean(), lg_lo=boot(lg)[0], lg_hi=boot(lg)[1], neutral_minus_gain=ng.mean(), ng_lo=boot(ng)[0], ng_hi=boot(ng)[1],
                   sd_loss_gain=lg.std(ddof=1), sd_excess=np.sqrt(max(0.0, lg.var(ddof=1) - noise_var)),
                   loss_above_gain=int((lg > 0).sum()), loss_below_gain=int((lg < 0).sum()), floor=bool(g.skip.sum() == 0),
                   min_rate=rate.values.min(), max_rate=rate.values.max(), **{f"share_{k}": v for k, v in d.items() if k != "total"})
        out.append(rec)
    return pd.DataFrame(out)


def pct(x): return "-" if pd.isna(x) else f"{100 * x:.1f}%"
def pp(x): return "-" if pd.isna(x) else f"{100 * x:+.1f}"


def to_md(t):
    L = ["| Model | Turns left | Wordings x episodes | Skip rate (min-max over cells) | Loss minus gain, pp [95% CI over wordings] | Neutral minus gain, pp [95% CI] | SD across wordings (excess over noise), pp | Loss above gain | Variation due to frame / wording / interaction (noise floor) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        if r.floor:
            L.append(f"| {r.model} | {r.turns_left} | {r.wordings} x {r.episodes_per_cell} | 0% (no skipping in any cell) | not estimable | not estimable | - | - | floor effect |"); continue
        L.append(f"| {r.model} | {r.turns_left} | {r.wordings} x {r.episodes_per_cell} | {pct(r.skip)} ({pct(r.min_rate)}-{pct(r.max_rate)}) | "
                 f"{pp(r.loss_minus_gain)} [{pp(r.lg_lo)}, {pp(r.lg_hi)}] | {pp(r.neutral_minus_gain)} [{pp(r.ng_lo)}, {pp(r.ng_hi)}] | "
                 f"{100 * r.sd_loss_gain:.1f} ({100 * r.sd_excess:.1f}) | {r.loss_above_gain} of {r.wordings} (below: {r.loss_below_gain}) | "
                 f"{pct(r.share_frame)} / {pct(r.share_wording)} / {pct(r.share_interaction)} ({pct(r.share_noise)}) |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("logs", nargs="+"); ap.add_argument("--fails", type=int, default=0); ap.add_argument("--md", default=None)
    a = ap.parse_args()
    t = analyse(load(a.logs), a.fails)
    md = to_md(t); print(md)
    if a.md:
        open(a.md, "w").write(md + "\n\nIntervals resample wordings (the unit of replication). Variation shares are shares of the total squared deviation of "
                              "the wording x frame table of skip rates; the interaction share and the noise floor both include sampling noise.\n")


if __name__ == "__main__":
    main()
