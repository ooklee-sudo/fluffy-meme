"""Study 2 preregistered analysis (draft; run unchanged on the final data).

Usage:  python analysis.py DATA.csv [OUT_DIR]      |      python analysis.py --selftest

Expected columns (one row per participant x room evaluation, 6 rows per participant):
  participant_id, room_id, trial_order (1-6), exaggerated (0/1),
  b1_perceived_quality_idx, b1_initial_trust, b1_pre_reveal_wtp, b1_book_at_130 (0/1),
  b2_disconfirmation, b2_star_rating, b2_host_honesty, b2_post_reveal_wtp, b2_rebook_intention.
Optional: delta_wtp (computed if absent); wtp_invalid (1 if a WTP value is outside [$10, $1000]; computed if absent).
Exclusions for attention checks, completion and time are applied upstream and counted in the paper.

Confirmatory family (Holm-adjusted): pre-reveal WTP (+), perceived quality index (+), WTP revision (-),
disconfirmation (-), star rating (-), host honesty (-). Everything else is exploratory.
Mixed models: crossed random intercepts for participant and room (statsmodels MixedLM variance components,
Wald z tests, since Satterthwaite df are not available in Python; this is the one deviation from the
registration text and should be stated there if this script is used).
"""
import sys, os, warnings
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")

CONF = [("b1_pre_reveal_wtp", +1, "H1(a)"), ("b1_perceived_quality_idx", +1, "H1(a)"), ("delta_wtp", -1, "H2(a)"),
        ("b2_disconfirmation", -1, "H3(a)"), ("b2_star_rating", -1, "H3(a)"), ("b2_host_honesty", -1, "H3(a)")]
EXPL = ["b1_initial_trust", "b1_book_at_130", "b2_post_reveal_wtp", "b2_rebook_intention"]

def prepare(d):
    d = d.copy()
    if "delta_wtp" not in d: d["delta_wtp"] = d.b2_post_reveal_wtp - d.b1_pre_reveal_wtp
    if "wtp_invalid" not in d:
        d["wtp_invalid"] = ((d.b1_pre_reveal_wtp < 10) | (d.b1_pre_reveal_wtp > 1000) | (d.b2_post_reveal_wtp < 10) | (d.b2_post_reveal_wtp > 1000)).astype(int)
    d["participant_id"] = d.participant_id.astype(str); d["room_id"] = d.room_id.astype(str)
    return d

def mixed(y, d, binary=False):
    """Crossed random intercepts (participant, room). Binary outcomes: linear probability model (logistic mixed model is
    run in R/lme4 if preferred; see note in README)."""
    d = d.assign(_g=1)
    m = smf.mixedlm(f"{y} ~ exaggerated + trial_order", d, groups="_g", re_formula="0",
                    vc_formula={"participant": "0 + C(participant_id)", "room": "0 + C(room_id)"})
    try: r = m.fit(reml=True, method="lbfgs")
    except Exception: r = m.fit(reml=True)
    return r

def effect_size(y, d, r):
    var_tot = d[y].var(); return r.params["exaggerated"] / np.sqrt(var_tot)

def holm(p):
    p = np.asarray(p); o = np.argsort(p); adj = np.empty(len(p)); run = 0
    for rank, i in enumerate(o):
        run = max(run, (len(p) - rank) * p[i]); adj[i] = min(1, run)
    return adj

def two_way_cluster(y, d):
    f = f"{y} ~ exaggerated + trial_order"
    m = smf.ols(f, d)
    g = np.column_stack([pd.factorize(d.participant_id)[0], pd.factorize(d.room_id)[0]])
    return m.fit(cov_type="cluster", cov_kwds={"groups": g})

def main(d, out=None, n_boot=5000, seed=1):
    d = prepare(d); lines = []
    P = lambda *a: (print(*a), lines.append(" ".join(str(x) for x in a)))
    P(f"N participants = {d.participant_id.nunique()}, evaluations = {len(d)}, rooms = {d.room_id.nunique()}, flagged WTP rows = {int(d.wtp_invalid.sum())}")
    # --- confirmatory
    rows = []
    for y, sign, h in CONF:
        dd = d[d.wtp_invalid == 0] if "wtp" in y else d
        r = mixed(y, dd); b, se, p = r.params["exaggerated"], r.bse["exaggerated"], r.pvalues["exaggerated"]
        rows.append(dict(hypothesis=h, outcome=y, b1=b, se=se, p=p, ci_lo=b - 1.96 * se, ci_hi=b + 1.96 * se,
                         d=effect_size(y, dd, r), predicted_sign=sign, sign_ok=bool(np.sign(b) == sign),
                         mean_L0=dd[dd.exaggerated == 0][y].mean(), mean_L2=dd[dd.exaggerated == 1][y].mean()))
    T = pd.DataFrame(rows); T["p_holm"] = holm(T.p.values)
    T["supported"] = T.sign_ok & (T.p_holm < .05)
    P("\n== Confirmatory tests (two-sided, Holm across 6) =="); P(T.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    h3 = T[T.hypothesis == "H3(a)"]
    P("H1(a) supported:", bool(T[T.hypothesis == "H1(a)"].supported.all()), "| H2(a) supported:", bool(T[T.hypothesis == "H2(a)"].supported.all()),
      "| H3(a) supported (all three):", bool(h3.supported.all()), "| H3(a) significant outcomes:", list(h3[h3.supported].outcome))
    # --- exploratory outcomes
    ex = []
    for y in EXPL:
        dd = d[d.wtp_invalid == 0] if "wtp" in y else d
        r = mixed(y, dd); ex.append(dict(outcome=y, b1=r.params["exaggerated"], se=r.bse["exaggerated"], p=r.pvalues["exaggerated"]))
    P("\n== Exploratory outcomes (not in Holm family) =="); P(pd.DataFrame(ex).round(4).to_string(index=False))
    # --- robustness
    P("\n== Robustness ==")
    rb = []
    for y, sign, h in CONF:
        dd = d[d.wtp_invalid == 0] if "wtp" in y else d
        t = two_way_cluster(y, dd); r_all = mixed(y, d) if "wtp" in y else None
        inter = smf.ols(f"{y} ~ exaggerated*trial_order + C(room_id)", dd).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(dd.participant_id)[0]})
        t1 = dd[dd.trial_order == 1]; m1 = smf.ols(f"{y} ~ exaggerated", t1).fit(cov_type="HC1")
        row = dict(outcome=y, twoway_b1=t.params["exaggerated"], twoway_p=t.pvalues["exaggerated"],
                   order_interaction_p=inter.pvalues["exaggerated:trial_order"], trial1_b=m1.params["exaggerated"], trial1_p=m1.pvalues["exaggerated"], trial1_n=len(t1))
        if r_all is not None: row["with_flagged_b1"] = r_all.params["exaggerated"]; row["with_flagged_p"] = r_all.pvalues["exaggerated"]
        rb.append(row)
    P(pd.DataFrame(rb).to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    dl = d[d.wtp_invalid == 0].assign(log_pre=lambda x: np.log(x.b1_pre_reveal_wtp), log_post=lambda x: np.log(x.b2_post_reveal_wtp))
    dl["dlog"] = dl.log_post - dl.log_pre
    for y in ("log_pre", "dlog"):
        r = mixed(y, dl); P(f"log WTP sensitivity, {y}: b1 = {r.params['exaggerated']:.4f}, p = {r.pvalues['exaggerated']:.4g}")
    long = pd.concat([dl.assign(post=0, wtp=dl.b1_pre_reveal_wtp), dl.assign(post=1, wtp=dl.b2_post_reveal_wtp)], ignore_index=True)
    mm = smf.ols("wtp ~ exaggerated*post + C(room_id)", long).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(long.participant_id)[0]})
    P(f"repeated-measures WTP, exaggerated x post interaction: {mm.params['exaggerated:post']:.3f} (p = {mm.pvalues['exaggerated:post']:.4g}); compare with the DeltaWTP effect")
    # --- exploratory mediation (participant bootstrap)
    P("\n== Exploratory mediation of the post-reveal penalty (bootstrap over participants) ==")
    rng = np.random.default_rng(seed); ids = d.participant_id.unique(); groups = {i: g for i, g in d.groupby("participant_id")}
    def med(df, y, ms=("b2_disconfirmation", "b2_host_honesty")):
        X = pd.get_dummies(df[["exaggerated"]].join(df.room_id), columns=["room_id"], drop_first=True).astype(float); X.insert(0, "c", 1.0)
        a = [np.linalg.lstsq(X.values, df[m].values, rcond=None)[0][1] for m in ms]
        Z = X.join(df[list(ms)]).values; coef = np.linalg.lstsq(Z, df[y].values, rcond=None)[0]
        b = coef[-len(ms):]; return float(np.dot(a, b)), float(coef[1])
    for y in ("b2_star_rating", "b2_post_reveal_wtp"):
        dd = d[d.wtp_invalid == 0] if "wtp" in y else d
        est, direct = med(dd, y); bs = []
        for _ in range(n_boot):
            samp = pd.concat([groups[i] for i in rng.choice(ids, len(ids))], ignore_index=True); samp = samp[samp.wtp_invalid == 0] if "wtp" in y else samp
            try: bs.append(med(samp, y)[0])
            except Exception: pass
        lo, hi = np.percentile(bs, [2.5, 97.5]); P(f"  {y}: indirect = {est:.3f}, 95% CI [{lo:.3f}, {hi:.3f}], direct = {direct:.3f}")
    if out:
        os.makedirs(out, exist_ok=True); T.to_csv(f"{out}/confirmatory.csv", index=False); open(f"{out}/report.txt", "w").write("\n".join(lines))
    return T

def simulate(n=120, seed=0, effects=None):
    """Self-test data generator (NOT data; used only to check that the code runs and recovers a known effect)."""
    rng = np.random.default_rng(seed); eff = effects or dict(pre=18, dwtp=-24, disc=-1.7, star=-0.8, honest=-2.7, qual=1.2)
    u = rng.normal(0, 8, n); v = rng.normal(0, 10, 24); rows = []
    for i in range(n):
        rooms = rng.permutation(24)[:6]; cond = np.array([0, 0, 0, 1, 1, 1]); rng.shuffle(cond)
        for t, (r, c) in enumerate(zip(rooms, cond), 1):
            pre = 115 + u[i] + v[r] + eff["pre"] * c + rng.normal(0, 25); dw = -5 + eff["dwtp"] * c + rng.normal(0, 14)
            rows.append(dict(participant_id=i, room_id=r, trial_order=t, exaggerated=c, b1_perceived_quality_idx=4.4 + eff["qual"] * c + rng.normal(0, 1),
                             b1_initial_trust=4.6 + .6 * c + rng.normal(0, 1), b1_pre_reveal_wtp=pre, b1_book_at_130=int(pre > 130 + rng.normal(0, 20)),
                             b2_disconfirmation=np.clip(3.9 + eff["disc"] * c + rng.normal(0, 1), 1, 7), b2_star_rating=np.clip(3.8 + eff["star"] * c + rng.normal(0, .8), 1, 5),
                             b2_host_honesty=np.clip(5.5 + eff["honest"] * c + rng.normal(0, 1.2), 1, 7), b2_post_reveal_wtp=pre + dw,
                             b2_rebook_intention=np.clip(4.2 - 1.5 * c + rng.normal(0, 1.2), 1, 7)))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        main(simulate(), n_boot=200)
    else:
        main(pd.read_csv(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
