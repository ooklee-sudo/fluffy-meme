"""Does the strength of the affect verb in the loss wordings explain the low skipping under loss text?

The 16 loss wordings differ in how emotive their verb is ("knocked", "took a hit", "eroded" versus "reduced", "dropped",
"decreased"). If emotive verbs alone lowered skipping, the loss-minus-gain and loss skip rates should differ between the two groups.
The grouping below was fixed from the wording text alone, before any wording-level result was inspected.

usage: python affect16.py log1.jsonl [log2.jsonl ...] [--fails 0] [--ci 95] [--md out.md]
Reads first choices (turn 0) from w16 logs, one block per model and turns-left condition. Intervals resample wordings within group.
"""
import argparse, json
import numpy as np, pandas as pd
from env import SKIPS

# Loss wording index -> verb phrase (see wordings.json). STRONG = emotive verbs; the others are plain descriptive verbs.
VERB = {0: "reduced", 1: "knocked down", 2: "slipped", 3: "degraded", 4: "dropped", 5: "took a hit", 6: "decline", 7: "drop",
        8: "fall", 9: "decreased", 10: "reduced", 11: "dropped", 12: "eroded", 13: "reduction", 14: "lowered", 15: "worsened"}
STRONG = {1, 2, 3, 5, 12, 15}
CI = 95.0


def load(paths):
    rows = []
    for p in paths:
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return pd.DataFrame(rows)


def boot_diff(a, b, B=4000, seed=1):
    rng = np.random.default_rng(seed); a, b = np.asarray(a), np.asarray(b)
    m = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(B)])
    return np.percentile(m, [(100 - CI) / 2, 100 - (100 - CI) / 2])


def boot_mean(a, B=4000, seed=2):
    rng = np.random.default_rng(seed); a = np.asarray(a)
    m = np.array([rng.choice(a, len(a)).mean() for _ in range(B)])
    return np.percentile(m, [(100 - CI) / 2, 100 - (100 - CI) / 2])


def analyse(df, fails):
    df = df[(df.turn == 0) & (df.n_fails == fails)].copy()
    df["skip"] = df.action.isin(SKIPS).astype(int)
    L = []
    for (mid, t), g in df.groupby(["model_id", "t"]):
        rate = g.pivot_table(index="variant", columns="frame", values="skip", aggfunc="mean")
        if not {"loss", "gain"} <= set(rate.columns) or rate["loss"].sum() + rate["gain"].sum() == 0:
            continue
        rate["group"] = ["strong" if i in STRONG else "plain" for i in rate.index]
        rate["verb"] = [VERB.get(i, "?") for i in rate.index]
        rate["lg"] = rate["loss"] - rate["gain"]
        S, P = rate[rate.group == "strong"], rate[rate.group == "plain"]
        pct = lambda x: f"{100 * x:.1f}%"
        L.append(f"\n**{mid} | {12 - int(t)} turns left | strong-verb wordings n={len(S)}, plain-verb wordings n={len(P)}**\n")
        L.append("| Group | Loss skip rate | Loss minus gain, pp [CI over wordings] | Wordings with loss below gain |\n|---|---|---|---|")
        for name, grp in (("Strong verbs (knocked, slipped, degraded, took a hit, eroded, worsened)", S), ("Plain verbs (reduced, dropped, decline, drop, fall, decreased, reduction, lowered)", P)):
            lo, hi = boot_mean(grp["lg"].values)
            L.append(f"| {name} | {pct(grp['loss'].mean())} | {100 * grp['lg'].mean():+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] | {(grp['lg'] < 0).sum()} of {len(grp)} |")
        lo, hi = boot_diff(S["lg"].values, P["lg"].values)
        L.append(f"\nDifference in loss-minus-gain, strong minus plain: {100 * (S['lg'].mean() - P['lg'].mean()):+.1f} pp [{100 * lo:+.1f}, {100 * hi:+.1f}].")
        lo, hi = boot_diff(S["loss"].values, P["loss"].values)
        L.append(f"Difference in loss-frame skip rate, strong minus plain: {100 * (S['loss'].mean() - P['loss'].mean()):+.1f} pp [{100 * lo:+.1f}, {100 * hi:+.1f}].\n")
        L.append("| Index | Verb | Group | Loss | Gain | Neutral |\n|---|---|---|---|---|---|")
        for i, r in rate.sort_index().iterrows():
            L.append(f"| {i} | {r.verb} | {r.group} | {pct(r['loss'])} | {pct(r['gain'])} | {pct(r.get('neutral', np.nan))} |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("logs", nargs="+"); ap.add_argument("--fails", type=int, default=0)
    ap.add_argument("--ci", type=float, default=95.0); ap.add_argument("--md", default=None)
    a = ap.parse_args()
    global CI; CI = a.ci
    md = analyse(load(a.logs), a.fails)
    if not md.strip():
        raise SystemExit("no cell with skipping in both loss and gain frames")
    print(md)
    if a.md:
        open(a.md, "w").write(md + "\n")


if __name__ == "__main__":
    main()
