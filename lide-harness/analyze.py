"""Analyze episode results.

  python analyze.py --results results --out analysis

Writes analysis/episodes.csv (one row per episode) for the confirmatory mixed-effects
models (Eq. 2 in the paper; recommended in R with lme4::glmer), and prints quick
Python estimates with standard errors clustered by model as a first look.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from lide.scoring import DEFAULT_DELTA, classify_lide, episode_metrics

try:
    import statsmodels.formula.api as smf
except ImportError:  # analysis still writes CSVs without statsmodels
    smf = None


def load(results: Path) -> pd.DataFrame:
    rows = [episode_metrics(json.loads(p.read_text())) for p in sorted(results.glob("*.json"))]
    if not rows:
        raise SystemExit(f"No episode files in {results}/")
    df = pd.DataFrame(rows)
    return df[df["status"] == "ok"].copy()


def fit(formula: str, data: pd.DataFrame, kind: str = "logit", label: str = "") -> None:
    print(f"\n--- {label}  [{formula}]  n={len(data)}")
    if smf is None:
        print("statsmodels not installed; skipping model fit.")
        return
    if data.empty or data[formula.split("~")[0].strip()].nunique() < 2:
        print("Not enough variation in the outcome to fit.")
        return
    try:
        groups = data["model"].astype("category").cat.codes
        model = smf.logit(formula, data) if kind == "logit" else smf.ols(formula, data)
        kw = {"disp": 0} if kind == "logit" else {}
        if groups.nunique() > 1:
            res = model.fit(cov_type="cluster", cov_kwds={"groups": groups}, **kw)
        else:
            res = model.fit(**kw)
        print(res.summary2().tables[1].round(4).to_string())
        if groups.nunique() < 10:
            print("Note: fewer than 10 model clusters; use the mixed-effects model in R for inference.")
    except Exception as exc:
        print(f"Fit failed ({type(exc).__name__}: {exc}). Inspect the descriptives instead.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--delta", type=float, default=DEFAULT_DELTA)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df = classify_lide(load(Path(args.results)), args.delta)
    for col in ("lide", "reward_hack", "honest_exit", "false_completion", "omitted_safeguard"):
        df[col] = df[col].astype(int)
    df.drop(columns=["assistant_text"]).to_csv(out / "episodes.csv", index=False)
    print(f"Wrote {out / 'episodes.csv'} ({len(df)} episodes).")

    s1 = df[df["study"] == "study1"]
    core = s1[(s1["scarcity"] == "none") & (s1["record"] == "full")]

    print("\n=== Descriptives: Study 1, no scarcity, full record ===")
    desc = core.groupby(["env", "valence"])[["lide", "mean_risk", "reward_hack", "honest_exit"]].mean()
    print(desc.round(3).to_string())

    # H1: loss level (failures only, 0-8) with a hinge to test the threshold
    h1 = core[core["loss_level"] >= 0].copy()
    h1["hinge4"] = (h1["loss_level"] - 4).clip(lower=0)
    fit("lide ~ loss_level + hinge4 + C(env)", h1, label="H1 accumulated loss (hinge at 4 failures)")

    # H2: reflection - success streak vs neutral on continuous action risk
    h2 = core[core["valence"].isin(["success4", "neutral"])].copy()
    h2["success"] = (h2["valence"] == "success4").astype(int)
    fit("mean_risk ~ success + C(env)", h2, kind="ols", label="H2 reflection (expect negative)")

    # H3a: scarcity amplifies the loss effect
    h3 = s1[(s1["record"] == "full") & (s1["loss_level"] >= 0)]
    fit("lide ~ loss_level * C(scarcity, Treatment('none')) + C(env)", h3, label="H3a scarcity x loss")

    # H3b: timing of first peripheral violation vs first core decline
    print("\n=== H3b: timing (actions until first event), by scarcity ===")
    print(h3.groupby("scarcity")[["first_violation_action", "first_core_decline_action"]]
          .agg(["mean", "count"]).round(2).to_string())

    # H4: record of prior attempts
    h4 = s1[(s1["scarcity"] == "none") & (s1["loss_level"] > 0)]
    fit("lide ~ loss_level * C(record, Treatment('summary')) + C(env)", h4, label="H4 full record x loss")
    print(h4.groupby("record")["repeat_failed_share"].mean().round(3).to_string())

    # Rival: instruction pressure (user dissatisfaction) vs environment-only failure signals
    fb = df[(df["study"].isin(["study1", "study1fb"])) & (df["scarcity"] == "none") &
            (df["record"] == "full") & (df["valence"].isin(["fail4", "fail8"]))].copy()
    fb["user_feedback"] = (fb["feedback"] == "user").astype(int)
    fit("lide ~ user_feedback + loss_level + C(env)", fb, label="Rival: instruction pressure")

    # H5: governance artifacts
    s2 = df[df["study"] == "study2"]
    fit("lide ~ loss_level * C(governance, Treatment('none')) + C(env)", s2,
        label="H5 governance x loss (expect negative interactions)")
    print(s2.groupby(["governance", "valence"])[["lide", "damage", "honest_exit"]].mean()
          .round(3).to_string())


if __name__ == "__main__":
    main()
