"""Does the skipping survive when the dominance of verification is visible to the operator?

usage: python compare_reveal.py baseline.jsonl reveal.jsonl [--ci 95] [--md out.md]
baseline = the 5-frame run without expected values (g2x2_haiku.jsonl); reveal = the same design with --reveal-ev.
Both: Haiku 4.5, 3 turns left, no injected failures, 16 wordings x 30 episodes per frame. Intervals resample wordings (paired by wording).
"""
import argparse, json
import numpy as np, pandas as pd
from env import SKIPS

FR = ["neutral", "loss", "gain", "neutral_goal", "loss_goal"]
CI = 95.0


def load(p):
    rows = []
    for line in open(p):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    d = pd.DataFrame(rows)
    d = d[(d.turn == 0) & (d.n_fails == 0)]
    d["skip"] = d.action.isin(SKIPS).astype(int)
    return d.pivot_table(index="variant", columns="frame", values="skip", aggfunc="mean")[FR]


def boot(v, B=4000, seed=1):
    rng = np.random.default_rng(seed); v = np.asarray(v)
    m = np.array([rng.choice(v, len(v)).mean() for _ in range(B)])
    return np.percentile(m, [(100 - CI) / 2, 100 - (100 - CI) / 2])


def main():
    global CI
    ap = argparse.ArgumentParser(); ap.add_argument("baseline"); ap.add_argument("reveal"); ap.add_argument("--ci", type=float, default=95.0); ap.add_argument("--md", default=None)
    a = ap.parse_args(); CI = a.ci
    b, r = load(a.baseline), load(a.reveal)
    idx = b.index.intersection(r.index); b, r = b.loc[idx], r.loc[idx]
    pct = lambda x: f"{100 * x:.1f}%"
    L = [f"**Haiku 4.5, 3 turns left, {len(idx)} wordings**\n", "| Frame | " + " | ".join(FR) + " |", "|---|" + "---|" * len(FR),
         "| Baseline (no expected values) | " + " | ".join(pct(b[f].mean()) for f in FR) + " |",
         "| Expected values shown | " + " | ".join(pct(r[f].mean()) for f in FR) + " |"]
    d = r - b
    row = []
    for f in FR:
        lo, hi = boot(d[f].values); row.append(f"{100 * d[f].mean():+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]")
    L += ["| Change, pp [CI over wordings] | " + " | ".join(row) + " |\n", "| Contrast within the expected-value run | Mean difference, pp [CI over wordings] | Wordings positive / negative |", "|---|---|---|"]
    for name, fn in [("Goal effect, neutral text (neutral_goal - neutral)", lambda x: x.neutral_goal - x.neutral), ("Goal effect, loss text (loss_goal - loss)", lambda x: x.loss_goal - x.loss),
                     ("Valence without target (loss - neutral)", lambda x: x.loss - x.neutral), ("Registered contrast (loss - gain)", lambda x: x.loss - x.gain)]:
        v = fn(r).values; lo, hi = boot(v); L.append(f"| {name} | {100 * v.mean():+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] | {(v > 0).sum()} / {(v < 0).sum()} of {len(v)} |")
    md = "\n".join(L); print(md)
    if a.md:
        open(a.md, "w").write(md + "\n")


if __name__ == "__main__":
    main()
