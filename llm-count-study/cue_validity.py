"""Stage 2: do the cues a user can see predict the errors that matter for a decision? (existing data, no API calls)

For every (setting, model, prompt, design) cell of the transaction experiments:
  user-visible cues : relative error of the mean, relative width of the 95% interval of the mean, parse-failure rate
  decision errors   : |log((1+alpha_sim)/(1+alpha_ref))|  and  |top-decile share - reference share|
For the email experiment (probability design): cue = correct sign of the lift for both emails; decision error = |log(lift ratio)|.
Face-validity rule (fixed in advance, change only before looking at results): mean within +-50% of the reference, parse
failures below 5%, and (email) correct sign. "Large" decision error: alpha error above 0.5 or top-decile error above 0.15
(email: lift ratio outside [0.5, 2]).

  python cue_validity.py --runs runs,runs_grocery,runs_grocery_demo --hillstrom runs_hillstrom
Inference: Spearman correlations are computed over cells and re-computed over model means with an exact permutation test
(models are the unit of dependence); a bootstrap over models gives an interval for the cell-level correlation.
"""
import argparse, glob, itertools, json, os, warnings
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings('ignore')
import run_pilot as rp
import concentration as cc

REAL_RD = {("visit", "mens"): 0.0766, ("visit", "womens"): 0.0452, ("purchase", "mens"): 0.0068, ("purchase", "womens"): 0.0031}


def cell_stats(x):
    x = x[~np.isnan(x)]
    if len(x) < 20 or x.mean() <= 0:
        return None
    m, v = x.mean(), x.var(ddof=1)
    return dict(mean=m, alpha=(v - m) / m ** 2, ci_rel=3.92 * x.std(ddof=1) / np.sqrt(len(x)) / m, top10=cc.top_share(x))


def transaction_cells(folder, rng):
    frames, ref = [], None
    for d in sorted(glob.glob(os.path.join(folder, "*"))):
        f, c = os.path.join(d, "raw_counts.csv"), os.path.join(d, "config.json")
        if not (os.path.exists(f) and os.path.exists(c)):
            continue
        cfg = json.load(open(c))
        r = cfg["ref"] if "ref" in cfg else rp.ref_stats(rp.get_scenario(cfg.get("scenario", "retail")))
        if ref is None:
            ref = dict(r, top10=cc.top_share(cc.reference_sample(cfg, rng)))
        df = pd.read_csv(f); df = df[df.cond != "real(ref)"]
        df["model"], df["anchor"] = cfg["model"], bool(cfg["anchor"])
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames); rows = []
    for (m, an, c), g in df.groupby(["model", "anchor", "cond"]):
        x = g["count"].astype(float).values; st = cell_stats(x)
        if st is None:
            continue
        rows.append(dict(setting=os.path.basename(folder.rstrip("/\\")), model=m, anchor=an, design=c, parse_fail=float(np.isnan(x).mean()),
                         mean_err=abs(st["mean"] / ref["mean"] - 1), ci_rel=st["ci_rel"],
                         alpha_err=abs(np.log((1 + st["alpha"]) / (1 + ref["alpha"]))) if st["alpha"] > -1 else np.nan,
                         top10_err=abs(st["top10"] - ref["top10"])))
    return pd.DataFrame(rows)


def email_cells(folder):
    rows = []
    for f in glob.glob(os.path.join(folder, "*", "hillstrom_summary.csv")):
        s = pd.read_csv(f); s = s[s.method == "C_prob"]
        s["tag"] = os.path.basename(os.path.dirname(f))
        rows.append(s)
    if not rows:
        return pd.DataFrame()
    s = pd.concat(rows)
    out = []
    for (m, an, o), g in s.groupby(["model", "anchor", "outcome"]):
        rd = {e: g[f"rate_{e}"].mean() - g.rate_ctrl.mean() for e in ("mens", "womens")}
        ok = all(v > 0 for v in rd.values())
        ratio = np.mean([rd[e] / REAL_RD[(o, e)] for e in rd])
        out.append(dict(model=m, anchor=an, outcome=o, sign_ok=ok, parse_fail=g.parse_fail.mean(), lift_ratio=ratio,
                        lift_err=abs(np.log(ratio)) if ratio > 0 else np.log(30)))
    return pd.DataFrame(out)


def perm_test(model, x, y, nperm=20000, rng=None):
    """Spearman over model means with exact (<= 8 models) or Monte-Carlo permutation of the pairing."""
    mm = pd.DataFrame(dict(model=model, x=x, y=y)).groupby("model").mean()
    obs = stats.spearmanr(mm.x, mm.y)[0]; n = len(mm)
    perms = list(itertools.permutations(range(n))) if n <= 8 else [rng.permutation(n) for _ in range(nperm)]
    cnt = sum(abs(stats.spearmanr(mm.x, mm.y.values[list(p)])[0]) >= abs(obs) - 1e-12 for p in perms)
    return obs, cnt / len(perms), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs,runs_grocery,runs_grocery_demo"); ap.add_argument("--hillstrom", default="runs_hillstrom")
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    T = pd.concat([transaction_cells(f, rng) for f in a.runs.split(",")], ignore_index=True)
    print(f"transaction cells: {len(T)}")
    T["face_pass"] = (T.mean_err <= 0.5) & (T.parse_fail < 0.05)
    T["large_err"] = (T.alpha_err > 0.5) | (T.top10_err > 0.15)
    print("\nFace-validity pass rate and share of passing cells with a large decision error, by design")
    print(T.groupby("design").apply(lambda g: pd.Series(dict(cells=len(g), pass_rate=g.face_pass.mean(),
          large_error_among_pass=g[g.face_pass].large_err.mean() if g.face_pass.any() else np.nan))).round(3).to_string())
    print(f"overall: pass {T.face_pass.mean():.3f}; large error among passing cells {T[T.face_pass].large_err.mean():.3f}; among failing cells {T[~T.face_pass].large_err.mean():.3f}")
    print("\nSpearman between visible cues and decision errors (cells; model-level permutation p in brackets)")
    for cue in ("mean_err", "ci_rel", "parse_fail"):
        for err in ("alpha_err", "top10_err"):
            d = T.dropna(subset=[cue, err])
            r = stats.spearmanr(d[cue], d[err])[0]
            ms = d.model.unique(); bs = []
            for _ in range(a.boot):
                pick = rng.choice(ms, len(ms)); dd = pd.concat([d[d.model == m] for m in pick])
                bs.append(stats.spearmanr(dd[cue], dd[err])[0])
            obs, p, n = perm_test(d.model.values, d[cue].values, d[err].values, rng=rng)
            print(f"  {cue:>10s} vs {err:>9s}: rho={r:+.2f} cluster-bootstrap [{np.nanpercentile(bs,2.5):+.2f},{np.nanpercentile(bs,97.5):+.2f}]; model means rho={obs:+.2f} (p={p:.3f}, {n} models)")
    E = email_cells(a.hillstrom)
    if len(E):
        E["face_pass"] = E.sign_ok & (E.parse_fail < 0.05); E["large_err"] = (E.lift_ratio < 0.5) | (E.lift_ratio > 2)
        print(f"\nEmail experiment (probability design): configurations {len(E)}; face-validity pass {E.face_pass.mean():.3f}; "
              f"large lift error among passing configurations {E[E.face_pass].large_err.mean():.3f}")
        print(E.groupby("outcome").apply(lambda g: pd.Series(dict(configs=len(g), pass_rate=g.face_pass.mean(), large_error_among_pass=g[g.face_pass].large_err.mean()))).round(3).to_string())
    T.to_csv("cue_validity_cells.csv", index=False)
    if len(E): E.to_csv("cue_validity_email.csv", index=False)


if __name__ == "__main__":
    main()
