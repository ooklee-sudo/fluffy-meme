"""Analysis of first choices (Section 4.5).

    python analyze.py results/study4__haiku45__s4.jsonl
    python analyze.py results/*.jsonl --out report.md
    python analyze.py results/study1__*.jsonl --study1

Studies 2-7: wording is the unit of replication. Contrasts are taken within
wording and averaged; intervals are percentile intervals from a bootstrap
over wordings (4,000 resamples), at 95% and at 99.6% (Bonferroni over 12).
A condition with no skipping in any cell is reported as a floor, not a null.
Study 1: logistic model with Holm adjustment over the two registered contrasts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

N_BOOT = 4000
LEVELS = (95.0, 99.6)

CONTRASTS_F3 = [("loss minus gain", "loss", "gain"), ("neutral minus gain", "neutral", "gain")]
CONTRASTS_F5 = [  # Table 8
    ("goal effect, neutral text (neutral_goal - neutral)", "neutral_goal", "neutral"),
    ("goal effect, loss text (loss_goal - loss)", "loss_goal", "loss"),
    ("valence without target (loss - neutral)", "loss", "neutral"),
    ("valence with target (loss_goal - neutral_goal)", "loss_goal", "neutral_goal"),
    ("registered contrast (loss - gain)", "loss", "gain"),
    ("gain - neutral_goal (both state the target)", "gain", "neutral_goal"),
]


def load(paths) -> pd.DataFrame:
    rows = []
    for p in paths:
        with open(p) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("t") == 0:
                    d["run"] = Path(p).stem
                    rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("no first choices found")
    df["skip"] = df["skip"].astype(int)
    return df


def cell_table(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Skip rate and n per wording (rows) x frame (columns)."""
    g = d.groupby(["headline_id", "frame"])["skip"]
    return g.mean().unstack(), g.size().unstack()


def boot_ci(diffs: np.ndarray, rng) -> dict:
    idx = rng.integers(0, len(diffs), size=(N_BOOT, len(diffs)))
    means = diffs[idx].mean(axis=1)
    out = {}
    for lv in LEVELS:
        a = (100 - lv) / 2
        out[lv] = (np.percentile(means, a), np.percentile(means, 100 - a))
    return out


def contrast(rate: pd.DataFrame, n: pd.DataFrame, a: str, b: str, rng) -> dict | None:
    if a not in rate or b not in rate:
        return None
    diffs = (rate[a] - rate[b]).dropna().to_numpy()
    if len(diffs) == 0:
        return None
    pa, pb = rate[a], rate[b]
    noise_var = (pa * (1 - pa) / n[a] + pb * (1 - pb) / n[b]).mean()
    sd = diffs.std(ddof=1) if len(diffs) > 1 else 0.0
    return {
        "mean": diffs.mean(), "ci": boot_ci(diffs, rng),
        "above": int((diffs > 0).sum()), "below": int((diffs < 0).sum()),
        "sd": sd, "sd_excess": float(np.sqrt(max(0.0, sd ** 2 - noise_var))),
    }


def variance_shares(rate: pd.DataFrame, n: pd.DataFrame, frames) -> dict | None:
    R = rate[frames].to_numpy()
    N = n[frames].to_numpy()
    if np.isnan(R).any():
        return None
    grand = R.mean()
    total = ((R - grand) ** 2).sum()
    if total == 0:
        return None
    W, F = R.shape
    ss_frame = W * ((R.mean(axis=0) - grand) ** 2).sum()
    ss_word = F * ((R.mean(axis=1) - grand) ** 2).sum()
    ss_int = total - ss_frame - ss_word
    noise = (R * (1 - R) / N).sum()
    return {"frame": ss_frame / total, "wording": ss_word / total,
            "interaction": ss_int / total, "noise_floor": noise / total}


def pp(x: float) -> str:
    return f"{100 * x:+.1f}"


def fmt_contrast(name: str, c: dict) -> str:
    lo, hi = c["ci"][95.0]
    lo2, hi2 = c["ci"][99.6]
    return (f"| {name} | {pp(c['mean'])} | [{pp(lo)}, {pp(hi)}] | [{pp(lo2)}, {pp(hi2)}] | "
            f"{c['above']} / {c['below']} | {100 * c['sd']:.1f} ({100 * c['sd_excess']:.1f}) |")


def report_condition(d: pd.DataFrame, title: str, rng) -> list[str]:
    out = [f"### {title}", ""]
    n_tot, k = len(d), int(d["skip"].sum())
    pf = d["parse_fail"].mean()
    rate, n = cell_table(d)
    out.append(f"First choices: {n_tot}; skip rate {100 * k / n_tot:.1f}% "
               f"(cells {100 * np.nanmin(rate.values):.1f}%–{100 * np.nanmax(rate.values):.1f}%); "
               f"parse failures {100 * pf:.2f}%.")
    by_frame = d.groupby("frame")["skip"].mean()
    out.append("Skip rate by frame: " + ", ".join(f"{f} {100 * v:.1f}%" for f, v in by_frame.items()) + ".")
    acts = d["action"].value_counts(normalize=True)
    out.append("Actions: " + ", ".join(f"{a} {100 * v:.1f}%" for a, v in acts.items()) + ".")
    out.append("")
    if k == 0:
        out += ["**Floor**: no skipping in any cell; contrasts not estimable (not a null).", ""]
        return out
    frames = set(rate.columns)
    spec = CONTRASTS_F5 if {"neutral_goal", "loss_goal"} & frames else CONTRASTS_F3
    out += ["| Contrast | Mean, pp | 95% CI | 99.6% CI | Wordings + / − | SD across wordings (excess over noise) |",
            "|---|---|---|---|---|---|"]
    for name, a, b in spec:
        c = contrast(rate, n, a, b, rng)
        if c is not None:
            out.append(fmt_contrast(name, c))
    shares = variance_shares(rate, n, sorted(frames))
    if shares:
        out += ["", "Variation in the wording × frame table: " + ", ".join(
            f"{k_} {100 * v:.1f}%" for k_, v in shares.items()) + "."]
    out.append("")
    return out


def report(df: pd.DataFrame, seed: int = 0) -> str:
    rng = np.random.default_rng(seed)
    lines = ["# Results", ""]
    for run, d in df.groupby("run"):
        lines += [f"## {run}", ""]
        keys = [k for k in ["turns_left", "hide_target", "show_ev", "n_fails"] if d[k].nunique() > 1]
        if keys:
            for vals, dd in d.groupby(keys):
                vals = vals if isinstance(vals, tuple) else (vals,)
                lines += report_condition(dd, ", ".join(f"{k}={v}" for k, v in zip(keys, vals)), rng)
        else:
            lines += report_condition(d, "all cells", rng)
    return "\n".join(lines)


# ---------------------------------------------------------------- Study 1
def study1(df: pd.DataFrame) -> str:
    import statsmodels.formula.api as smf
    from statsmodels.stats.multitest import multipletests

    lines = ["# Study 1 (registered analysis)", ""]
    for run, d in df.groupby("run"):
        lines += [f"## {run}", ""]
        tab = d.pivot_table(index="n_fails", columns="frame", values="skip", aggfunc="mean")
        lines += ["Skip rate (first choice):", "", (100 * tab).round(1).to_markdown(), ""]
        if d["skip"].sum() == 0 or d["skip"].sum() == len(d):
            lines += ["No variation in skipping; the test is not informative.", ""]
            continue
        d = d.assign(frame=pd.Categorical(d["frame"], ["gain", "loss", "neutral"]),
                     nf=pd.Categorical(d["n_fails"]))
        p = {}
        try:
            m1 = smf.logit("skip ~ C(frame)", d).fit(disp=0)
            p["loss vs gain"] = (m1.params.get("C(frame)[T.loss]"), m1.pvalues.get("C(frame)[T.loss]"))
            m2 = smf.logit("skip ~ C(nf)", d[d["n_fails"].isin([0, 3])]).fit(disp=0)
            p["3 vs 0 failures"] = (m2.params.get("C(nf)[T.3]"), m2.pvalues.get("C(nf)[T.3]"))
            mi = smf.logit("skip ~ C(frame) * C(nf)", d).fit(disp=0)
            m0 = smf.logit("skip ~ C(frame) + C(nf)", d).fit(disp=0)
            from scipy.stats import chi2
            lr = 2 * (mi.llf - m0.llf)
            p_int = chi2.sf(lr, mi.df_model - m0.df_model)
        except Exception as e:  # separation etc.
            lines += [f"Logit failed: {e}", ""]
            continue
        adj = multipletests([v[1] for v in p.values()], method="holm")[1]
        diff = d[d.frame == "loss"]["skip"].mean() - d[d.frame == "gain"]["skip"].mean()
        lines.append(f"Loss minus gain (pooled): {pp(diff)} pp.")
        for (name, (coef, _)), pa in zip(p.items(), adj):
            lines.append(f"- {name}: logit coef {coef:+.2f}, Holm p = {pa:.3f}")
        lines.append(f"- frame × failures interaction: LR test p = {p_int:.2f}")
        supported = diff >= 0.10 and adj[0] < 0.05
        lines += [f"H1 supported (≥10 pp and Holm p < .05): {'yes' if supported else 'no'}", ""]
        g = d.groupby("n_fails")[["risk", "excess_risk", "skip"]].mean()
        lines += ["Risk, excess risk, and skip rate by injected failures:", "", g.round(3).to_markdown(), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- action order
def by_order(df: pd.DataFrame, seed: int = 0) -> str:
    """Skip rate by which action is listed first, and frame contrasts within each order."""
    rng = np.random.default_rng(seed)
    lines = ["# Action-order robustness", ""]
    for run, d in df.groupby("run"):
        lines += [f"## {run}", ""]
        tab = d.pivot_table(index="first_listed", columns="frame", values="skip", aggfunc="mean")
        tab["all"] = d.groupby("first_listed")["skip"].mean()
        tab["n"] = d.groupby("first_listed").size()
        lines += ["Skip rate (%) by the action listed first:", "",
                  (tab.drop(columns="n") * 100).round(1).assign(n=tab["n"]).to_markdown(), ""]
        frames = set(d["frame"])
        spec = CONTRASTS_F5 if {"neutral_goal", "loss_goal"} & frames else CONTRASTS_F3
        lines += ["Contrasts pooled over the six orders (within wording, bootstrap over wordings):", "",
                  "| Contrast | Mean, pp | 95% CI | 99.6% CI | Wordings + / − | SD (excess) |",
                  "|---|---|---|---|---|---|"]
        rate, n = cell_table(d)
        for name, a, b in spec:
            c = contrast(rate, n, a, b, rng)
            if c is not None:
                lines.append(fmt_contrast(name, c))
        lines += ["", "Main contrast within each order (mean over wordings, pp):", ""]
        name, a, b = spec[0]
        rows = []
        for fl, dd in d.groupby("first_listed"):
            r_, n_ = cell_table(dd)
            c = contrast(r_, n_, a, b, rng)
            if c is not None and dd["skip"].sum() > 0:
                lo, hi = c["ci"][95.0]
                rows.append(f"| {fl} | {pp(c['mean'])} | [{pp(lo)}, {pp(hi)}] |")
            else:
                rows.append(f"| {fl} | floor | – |")
        lines += [f"| First listed | {name} | 95% CI |", "|---|---|---|"] + rows + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--study1", action="store_true")
    ap.add_argument("--by-order", action="store_true", help="action-order robustness tables")
    ap.add_argument("--out")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    df = load(args.paths)
    if args.study1:
        text = study1(df)
    elif args.by_order:
        text = by_order(df, args.seed)
    else:
        text = report(df, args.seed)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
