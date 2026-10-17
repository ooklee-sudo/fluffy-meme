"""Offline test of mean calibration for the hybrid design D (no API calls; reads runs*/ folders).

For every (model, anchor) cell the model's expected counts lambda_i (design D) are used in three ways:
  raw        : as in the main experiment (external gamma multiplier, Proposition 2)
  calibrated : lambda_i rescaled so that their average equals the historical mean count of the reference
               (the firm's own customer file supplies this number), then the same gamma multiplier
  no_persona : every customer gets the reference mean (no information from the model); gamma multiplier
               with the full reference alpha. This is the baseline that shows what the model adds.
Each variant is compared with the reference on mean, variance/mean, zero share, and alpha (95% bootstrap CI over
customers; * = CI excludes the reference). Scaling does not change the rank order of lambda_i, so the rank
correlation with the real counts (demographic personas) is identical for raw and calibrated.

  python calibrate_hybrid.py --runs runs
  python calibrate_hybrid.py --runs runs_grocery
  python calibrate_hybrid.py --runs runs_grocery_demo
"""
import argparse, glob, json, os
import numpy as np, pandas as pd
import run_pilot as rp
import analyze_ci as ac


def simulate(lam, alpha_total, rng):
    a_w, c2 = rp.alpha_within(lam, alpha_total)
    return rng.poisson(lam * rng.gamma(1 / a_w, a_w, size=len(lam))), c2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    frames = []
    for d in sorted(glob.glob(os.path.join(a.runs, "*"))):
        f, c = os.path.join(d, "raw_counts.csv"), os.path.join(d, "config.json")
        if not (os.path.exists(f) and os.path.exists(c)):
            continue
        cfg = json.load(open(c))
        ac.REF.update(cfg["ref"])
        df = pd.read_csv(f); df = df[df.cond == "D"].dropna(subset=["lam"])
        df["model"], df["anchor"] = cfg["model"], bool(cfg["anchor"])
        df["alpha_total"] = cfg["ref"]["alpha"]
        frames.append(df)
    if not frames:
        raise SystemExit("no design D runs found")
    df = pd.concat(frames)
    ref = ac.REF
    rows = []
    for (m, an), g in df.groupby(["model", "anchor"]):
        lam = g.lam.astype(float).values
        variants = {"raw": lam, "calibrated": lam * ref["mean"] / lam.mean(),
                    "no_persona": np.full(len(lam), ref["mean"])}
        for name, l in variants.items():
            x, c2 = simulate(l, ref["alpha"], rng)
            x = x.astype(float)
            est, ci = ac.stats_of(x), ac.boot(x, a.boot, rng)
            rec = dict(model=m, anchor=an, variant=name, n=len(x), cv2_lambda=round(float(c2), 3))
            ok = True
            for k in ref:
                rec[k] = ac.fmt(k, est[k], ci[k])
                ok &= not rec[k].endswith("*")
            rec["all4"] = ok
            rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(a.runs, "calibration_summary.csv"), index=False)
    print(f"reference: mean {ref['mean']:.2f}, var/mean {ref['var_mean']:.2f}, zero {ref['zero']:.2f}, alpha {ref['alpha']:.2f}")
    print("estimate [95% bootstrap CI]; * = CI excludes the reference; cv2_lambda = squared CV of the model's lambda\n")
    print(out.to_string(index=False))
    print("\ncells matching all four statistics:")
    print(out.groupby("variant").all4.agg(["sum", "count"]).to_string())


if __name__ == "__main__":
    main()
