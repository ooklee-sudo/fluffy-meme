"""Simulation-based power analysis for the within-subjects warning-label experiment.

Design simulated (one participant):
  K posts, half misinformation and half accurate. Within each type, half of the posts carry the
  HBM explanation warning. Two counterbalanced lists swap which half is warned, so every post
  appears with and without a warning across participants (Latin square).

Data-generating model for belief that a post is accurate, in SD units of the rating:
  y_ij = b0 + b_mis * mis_j
         + warn_ij * (d_mis * mis_j + d_acc * (1 - mis_j))   <- warning effects
         + u_i + s_i * warn_ij                               <- participant intercept and slope
         + v_j                                               <- post (item) effect
         + e_ij
  d_mis < 0: the warning lowers belief in misinformation (the hypothesis).
  d_acc < 0: spill-over, the warning also lowers belief in accurate posts (backfire check).
  With --likert, y is cut into a 1-7 scale before analysis.

Tests of H (warning lowers belief in misinformation), one-sided by default:
  by-participant   paired t-test on each participant's warned-minus-unwarned mean (misinfo posts)
  min-F'           Clark (1973) combination of by-participant and by-item tests; also generalizes
                   over posts, so it is the safer criterion when posts are a sample of many
  mixed            linear mixed model with participant intercept+slope and post intercept
                   (statsmodels; slow, use --method mixed with fewer --sims)

Examples
  python power_sim.py                                   # default grid, d_mis = -0.30
  python power_sim.py --d-mis -0.25 --posts 16 24 --participants 60 80 100 120 150 200
  python power_sim.py --participants 100 --posts 16 --method mixed --sims 200
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats


def simulate(P: int, K: int, a, rng: np.random.Generator) -> dict:
    """One simulated data set as arrays (participant, item, mis, warn, y)."""
    if K % 4:
        raise ValueError("posts must be a multiple of 4 (2 types x 2 warning halves)")
    items = np.arange(K)
    mis = (items < K // 2).astype(float)
    # Within each type, half A / half B; list 0 warns half A, list 1 warns half B.
    half = (items % (K // 2)) < (K // 4)
    lists = np.arange(P) % 2
    warn = np.where(lists[:, None] == 0, half[None, :], ~half[None, :]).astype(float)

    u = rng.normal(0, a.sd_participant, P)[:, None]
    s = rng.normal(0, a.sd_slope, P)[:, None]
    v = rng.normal(0, a.sd_item, K)[None, :]
    e = rng.normal(0, a.sd_resid, (P, K))
    effect = warn * (a.d_mis * mis[None, :] + a.d_acc * (1 - mis[None, :]))
    y = a.b_mis * mis[None, :] + effect + u + s * warn + v + e
    if a.likert:  # 7-point scale centred on the latent mean
        y = np.clip(np.round(4 + 1.2 * y), 1, 7)
    return {"y": y, "warn": warn, "mis": mis}


def _t_test(diff: np.ndarray, alternative: str):
    diff = diff[~np.isnan(diff)]
    t, p = stats.ttest_1samp(diff, 0.0, alternative=alternative)
    return t, p, len(diff) - 1


def analyze(d: dict, alternative: str, method: str) -> dict:
    y, warn, mis = d["y"], d["warn"], d["mis"]
    m = mis.astype(bool)
    ym, wm = y[:, m], warn[:, m]
    # By participant: mean(warned) - mean(unwarned) on misinformation posts.
    by_p = (ym * wm).sum(1) / wm.sum(1) - (ym * (1 - wm)).sum(1) / (1 - wm).sum(1)
    t1, p1, df1 = _t_test(by_p, alternative)
    # By item: the same contrast computed across participants for each misinformation post.
    by_i = (ym * wm).sum(0) / wm.sum(0) - (ym * (1 - wm)).sum(0) / (1 - wm).sum(0)
    t2, p2, df2 = _t_test(by_i, alternative)
    # min-F' (Clark, 1973) from F1 = t1^2 and F2 = t2^2; direction must agree with the hypothesis.
    F1, F2 = t1 ** 2, t2 ** 2
    minf = F1 * F2 / (F1 + F2)
    df_minf = (F1 + F2) ** 2 / (F1 ** 2 / df2 + F2 ** 2 / df1)
    p_minf = stats.f.sf(minf, 1, df_minf)
    same_dir = (t1 < 0 and t2 < 0) if alternative == "less" else (t1 > 0 and t2 > 0) if alternative == "greater" else True
    if alternative != "two-sided":
        p_minf = p_minf / 2 if same_dir else 1 - p_minf / 2
    out = {"p_participant": p1, "p_minF": p_minf, "effect_est": float(np.mean(by_p))}

    # Spill-over on accurate posts (two-sided, reported, not powered for).
    ya, wa = y[:, ~m], warn[:, ~m]
    acc = (ya * wa).sum(1) / wa.sum(1) - (ya * (1 - wa)).sum(1) / (1 - wa).sum(1)
    out["p_backfire"] = stats.ttest_1samp(acc, 0.0).pvalue

    if method == "mixed":
        import pandas as pd
        import statsmodels.formula.api as smf

        P, K = ym.shape
        df = pd.DataFrame({"y": ym.ravel(), "warn": wm.ravel(),
                           "pid": np.repeat(np.arange(P), K), "item": np.tile(np.arange(K), P)})
        df["one"] = 1
        import warnings

        warnings.filterwarnings("ignore")  # boundary fits (slope variance near 0) are common and expected
        try:
            fit = smf.mixedlm("y ~ warn", df, groups="one", re_formula="0",
                              vc_formula={"pid": "0 + C(pid)", "pid_slope": "0 + C(pid):warn",
                                          "item": "0 + C(item)"}).fit(reml=True, method="lbfgs")
            z, p = fit.tvalues["warn"], fit.pvalues["warn"]
            if alternative == "less":
                p = p / 2 if z < 0 else 1 - p / 2
            elif alternative == "greater":
                p = p / 2 if z > 0 else 1 - p / 2
            out["p_mixed"] = p
        except Exception:  # noqa: BLE001 - a failed fit counts as non-significant
            out["p_mixed"] = 1.0
    return out


def power(P: int, K: int, a, rng) -> dict:
    keys = ["p_participant", "p_minF", "p_backfire"] + (["p_mixed"] if a.method == "mixed" else [])
    hits = {k: 0 for k in keys}
    est = []
    for _ in range(a.sims):
        r = analyze(simulate(P, K, a, rng), a.alternative, a.method)
        for k in keys:
            hits[k] += r[k] < a.alpha
        est.append(r["effect_est"])
    res = {k.replace("p_", "power_"): hits[k] / a.sims for k in keys}
    res["mean_effect_est"] = float(np.mean(est))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--participants", type=int, nargs="+", default=[40, 60, 80, 100, 120, 150, 200])
    ap.add_argument("--posts", type=int, nargs="+", default=[8, 16, 24], help="multiples of 4")
    ap.add_argument("--d-mis", type=float, default=-0.30, help="warning effect on misinformation belief (SD units)")
    ap.add_argument("--d-acc", type=float, default=0.0, help="spill-over effect on accurate posts")
    ap.add_argument("--b-mis", type=float, default=-0.5, help="baseline difference, misinformation vs accurate")
    ap.add_argument("--sd-participant", type=float, default=0.5)
    ap.add_argument("--sd-slope", type=float, default=0.2, help="between-participant SD of the warning effect")
    ap.add_argument("--sd-item", type=float, default=0.4)
    ap.add_argument("--sd-resid", type=float, default=0.75)
    ap.add_argument("--likert", action="store_true", help="analyze 1-7 ratings instead of a continuous score")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--alternative", choices=["less", "two-sided", "greater"], default="less")
    ap.add_argument("--method", choices=["fast", "mixed"], default="fast")
    ap.add_argument("--sims", type=int, default=1000)
    ap.add_argument("--target", type=float, default=0.80)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="runs/power/power_grid.json")
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    crit = "power_mixed" if a.method == "mixed" else "power_minF"
    print(f"d_mis={a.d_mis}  d_acc={a.d_acc}  sd: participant={a.sd_participant} slope={a.sd_slope} "
          f"item={a.sd_item} resid={a.sd_resid}  alpha={a.alpha} ({a.alternative})  sims={a.sims}"
          f"{'  likert' if a.likert else ''}\n")
    head = f"{'posts':>5} {'N':>5} {'by-participant':>15} {'min-F':>7}" + (f" {'mixed':>7}" if a.method == "mixed" else "") + f" {'backfire':>9}"
    print(head)
    rows, minimum = [], {}
    for K in a.posts:
        for P in a.participants:
            r = power(P, K, a, rng)
            rows.append({"posts": K, "participants": P, **r})
            line = f"{K:>5} {P:>5} {r['power_participant']:>15.2f} {r['power_minF']:>7.2f}"
            if a.method == "mixed":
                line += f" {r['power_mixed']:>7.2f}"
            print(line + f" {r['power_backfire']:>9.2f}")
            if K not in minimum and r[crit] >= a.target:
                minimum[K] = P
        print()
    for K in a.posts:
        msg = f"N = {minimum[K]}" if K in minimum else f"more than {max(a.participants)}"
        print(f"posts={K:<3} smallest N in grid with {crit.replace('power_', '')} power >= {a.target:.2f}: {msg}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"params": vars(a), "grid": rows, "minimum_n": minimum}, indent=2), encoding="utf-8")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
