"""Customer concentration of simulated vs real purchase counts (no API calls; reads runs*/ folders).

For every (model, anchor, design) cell: the share of all simulated purchases made by the top 10% of customers
(ranked by their count), with a 95% bootstrap interval, next to the same statistic for the reference distribution.
A simulator with compressed heterogeneity under-represents heavy buyers, so its top-decile share is too low.

  python concentration.py --runs runs
  python concentration.py --runs runs_grocery
  python concentration.py --runs runs_grocery_demo
"""
import argparse, glob, json, os
import numpy as np, pandas as pd
import run_pilot as rp


def top_share(x, q=0.1):
    x = np.sort(np.asarray(x, float))[::-1]
    return x[: max(1, int(round(q * len(x))))].sum() / x.sum() if x.sum() > 0 else np.nan


def reference_sample(cfg, rng, n=200000):
    sc = rp.get_scenario(cfg.get("scenario", "retail"))
    if cfg.get("personas") == "demographic":
        _, counts = rp.load_journey_households()
        return counts.ravel().astype(float)
    return np.asarray(rp.reference(n, rng, sc), float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    frames, ref = [], None
    for d in sorted(glob.glob(os.path.join(a.runs, "*"))):
        f, c = os.path.join(d, "raw_counts.csv"), os.path.join(d, "config.json")
        if not (os.path.exists(f) and os.path.exists(c)):
            continue
        cfg = json.load(open(c))
        if ref is None:
            ref = top_share(reference_sample(cfg, rng))
        df = pd.read_csv(f); df = df[df.cond != "real(ref)"]
        df["model"], df["anchor"] = cfg["model"], bool(cfg["anchor"])
        frames.append(df)
    df = pd.concat(frames)
    rows = []
    for (m, an, c), g in df.groupby(["model", "anchor", "cond"]):
        x = g["count"].dropna().astype(float).values
        if len(x) < 20 or x.sum() == 0:
            rows.append(dict(model=m, anchor=an, cond=c, n=len(x), top10_share="n/a")); continue
        est = top_share(x)
        bs = np.array([top_share(x[rng.integers(0, len(x), len(x))]) for _ in range(a.boot)])
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        rows.append(dict(model=m, anchor=an, cond=c, n=len(x),
                         top10_share=f"{est:.2f} [{lo:.2f},{hi:.2f}]" + ("*" if not (lo <= ref <= hi) else "")))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(a.runs, "concentration_summary.csv"), index=False)
    print(f"reference: top 10% of customers make {ref:.2f} of all purchases; * = interval excludes the reference\n")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
