"""Valence x goal salience: is the gain-to-goal effect about gain/loss wording or about the target being stated?

Frames (each uses the same independently generated wording index i):
  neutral        quality + last result                     (no valence, no target in the headline)
  loss           quality drop + unrealized loss            (valence, no target in the headline)
  gain           distance to the target                    (target in the headline)
  neutral_goal   neutral headline + the target headline    (no valence, target)
  loss_goal      loss headline + the target headline       (valence, target)
usage: python goal2x2.py log1.jsonl [log2.jsonl ...] [--fails 0] [--md out.md]
Contrasts are means over wordings, with 95% cluster-bootstrap intervals that resample wordings.
"""
import argparse, json
import numpy as np, pandas as pd
from env import SKIPS

FR = ["neutral", "loss", "gain", "neutral_goal", "loss_goal"]
CONTRASTS = [
    ("Goal effect, neutral wording (neutral_goal - neutral)", lambda r: r["neutral_goal"] - r["neutral"]),
    ("Goal effect, loss wording (loss_goal - loss)", lambda r: r["loss_goal"] - r["loss"]),
    ("Valence without goal (loss - neutral)", lambda r: r["loss"] - r["neutral"]),
    ("Valence with goal (loss_goal - neutral_goal)", lambda r: r["loss_goal"] - r["neutral_goal"]),
    ("Interaction: valence with goal minus without", lambda r: (r["loss_goal"] - r["neutral_goal"]) - (r["loss"] - r["neutral"])),
    ("Registered H1 contrast (loss - gain)", lambda r: r["loss"] - r["gain"]),
    ("Check: gain - neutral_goal (both state the target)", lambda r: r["gain"] - r["neutral_goal"]),
]


def load(paths):
    rows = []
    for p in paths:
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return pd.DataFrame(rows)


CI = 95.0


def boot(v, B=4000, seed=1):
    rng = np.random.default_rng(seed); v = np.asarray(v)
    m = np.array([rng.choice(v, len(v)).mean() for _ in range(B)])
    return np.percentile(m, [(100 - CI) / 2, 100 - (100 - CI) / 2])


def analyse(df, fails):
    df = df[(df.turn == 0) & (df.n_fails == fails)].copy()
    if "hide_target" not in df:
        df["hide_target"] = False
    df["skip"] = df.action.isin(SKIPS).astype(int)
    out = []
    for (mid, hide, t), g in df.groupby(["model_id", "hide_target", "t"]):
        rate = g.pivot_table(index="variant", columns="frame", values="skip", aggfunc="mean")
        missing = [f for f in FR if f not in rate]
        if missing:
            continue
        rate = rate[FR]
        rec = dict(model=mid, hide_target=bool(hide), turns_left=12 - int(t), wordings=len(rate),
                   episodes=int(g.groupby(["frame", "variant"]).size().min()),
                   **{f"rate_{f}": rate[f].mean() for f in FR})
        for name, fn in CONTRASTS:
            v = fn(rate).values
            lo, hi = boot(v)
            rec[name] = (v.mean(), lo, hi, int((v > 0).sum()), int((v < 0).sum()))
        out.append(rec)
    return out


def to_md(res):
    pct = lambda x: f"{100 * x:.1f}%"
    L = []
    for r in res:
        L.append(f"\n**{r['model']} | facts line {'WITHOUT' if r['hide_target'] else 'with'} target | {r['turns_left']} turns left | "
                 f"{r['wordings']} wordings x {r['episodes']} episodes**\n")
        L.append("| Frame | " + " | ".join(FR) + " |\n|---|" + "---|" * len(FR))
        L.append("| Skip rate (mean over wordings) | " + " | ".join(pct(r[f"rate_{f}"]) for f in FR) + " |\n")
        L.append("| Contrast | Mean difference, pp [CI over wordings] | Wordings positive / negative |\n|---|---|---|")
        for name, _ in CONTRASTS:
            m, lo, hi, pos, neg = r[name]
            L.append(f"| {name} | {100 * m:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] | {pos} / {neg} of {r['wordings']} |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("logs", nargs="+"); ap.add_argument("--fails", type=int, default=0); ap.add_argument("--md", default=None)
    ap.add_argument("--ci", type=float, default=95.0, help="bootstrap interval level in percent")
    a = ap.parse_args()
    global CI; CI = a.ci
    res = analyse(load(a.logs), a.fails)
    if not res:
        raise SystemExit("no complete 5-frame cells found (run with --extra-frames)")
    md = to_md(res); print(md)
    if a.md:
        open(a.md, "w").write(md + "\n")


if __name__ == "__main__":
    main()
