"""Study 1 re-analysis with improved experience measure (see MEASUREMENT_PLAN.md).
Usage: python analyze_improved.py WORKDIR PAIRS_JSONL REVIEWS_JSONL REVIEWS_SEL_CSV"""
import sys, json, re, warnings
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, ".")
from analyze_study1 import build_P, zs
warnings.filterwarnings("ignore")
AT = {"cleanliness": "clean", "spaciousness": "space", "brightness": "bright", "furnishing_condition": "furn"}

def main(work, pairs, rev_path, rev_sel):
    s = pd.read_csv(f"{work}/sample.csv"); s["gid"] = s.city + "|" + s.room_type
    scores, rev_rate = build_P(s, pairs)
    for att, k in {**AT, "photographic_quality": "Q"}.items():
        s[f"P_{k}"] = s.id.map(scores[att]); s[f"zP_{k}"] = s.groupby("gid")[f"P_{k}"].transform(zs)
    keep = set(pd.read_csv(rev_sel).id); rng = np.random.default_rng(9); rows = []
    for l in open(rev_path):
        x = json.loads(l)
        if x["id"] not in keep: continue
        h = int(rng.integers(2))
        for att, k in AT.items():
            v = x["res"].get(att)
            if v in (-1, 0, 1): rows.append((x["listing_id"], k, v, h))
    e = pd.DataFrame(rows, columns=["id", "k", "v", "h"])
    share = {}
    for k in AT.values():
        g = e[e.k == k].groupby("id").v.agg(["mean", "count"]); g = g[g["count"] >= 3]
        s[f"E_{k}"] = s.id.map(g["mean"]); share[k] = s[f"E_{k}"].notna().mean()
        for h in (0, 1):
            gh = e[(e.k == k) & (e.h == h)].groupby("id").v.agg(["mean", "count"]); gh = gh[gh["count"] >= 2]
            s[f"E_{k}_h{h}"] = s.id.map(gh["mean"])
        s[f"zE_{k}"] = s.groupby("gid")[f"E_{k}"].transform(zs)
    print("share of listings with each text-based E attribute (>=3 mentions):", {k: round(v, 3) for k, v in share.items()})
    A = [k for k, v in share.items() if v >= 0.10]; print("attributes in composite:", A)
    # Spec B: cleanliness also uses the platform cleanliness subscore
    zc = s.groupby("gid").review_scores_cleanliness.transform(zs)
    s["zE_clean_B"] = pd.concat([s.zE_clean, zc], axis=1).mean(axis=1, skipna=True).where(s.zE_clean.notna() | zc.notna())
    def build(spec):
        cols = [("zE_clean_B" if (spec == "B" and k == "clean") else f"zE_{k}") for k in A]
        E = s[cols].mean(axis=1, skipna=True)
        O = pd.concat([s[f"zP_{k}"] - s[c] for k, c in zip(A, cols)], axis=1).mean(axis=1, skipna=True)
        d = s.copy(); d["zE"] = zs(E); d["O"] = zs(O.where(E.notna()))
        d["zP"] = zs(s[[f"zP_{k}" for k in A]].mean(axis=1)); d["zQ"] = s.zP_Q
        d["acc"] = s.review_scores_accuracy; d["acc_below"] = (d.acc < 4.8).astype(float).where(d.acc.notna())
        return d.dropna(subset=["zE", "zP", "zQ"])
    # reliability of composite E from halves (text-based)
    h = []
    for hh in (0, 1):
        cols = []
        for k in A:
            c = s[f"E_{k}_h{hh}"]; cols.append(c.groupby(s.gid).transform(zs))
        h.append(pd.concat(cols, axis=1).mean(axis=1, skipna=True))
    ok = h[0].notna() & h[1].notna(); r = np.corrcoef(h[0][ok], h[1][ok])[0, 1]; rel = 2 * r / (1 + r)
    print(f"composite text-E split-half r={r:.3f}, Spearman-Brown reliability={rel:.3f}, n={int(ok.sum())}")
    err_var_half = np.var((h[0] - h[1])[ok]) / 4   # error variance of full-sample composite (z units)
    ctl = "C(room_type)+accommodates+bedrooms+superhost+multi_listing_host+host_tenure_yrs"
    def fit(f, d, logit=False):
        mod = (smf.logit if logit else smf.ols)(f, d); grp = pd.factorize(d.loc[mod.data.row_labels, "neighbourhood_cleansed"])[0]
        return mod.fit(cov_type="cluster", cov_kwds={"groups": grp}, disp=0)
    def show(m, names):
        print("   " + "  ".join(f"{n}: {m.params[n]:.3f} ({m.bse[n]:.3f}, p={m.pvalues[n]:.3g})" for n in names) + f"  n={int(m.nobs)}")
    def run(d, tag):
        print(f"\n== {tag}: N={len(d)}, bookable={int(d.is_bookable.sum())}; share O>1SD={(d.O>1).mean():.3f}; corr(zP,zE)={d.zP.corr(d.zE):.3f}")
        b = d[d.is_bookable & d.ln_price.notna()]
        print(" H1b  ln(price)~zP+zE+zQ"); show(fit(f"ln_price~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", b), ["zP", "zE", "zQ"])
        m2 = fit(f"ln_price~zP*ln_reviews+zE*ln_reviews+zQ+{ctl}+C(neighbourhood_cleansed)", b)
        print(" H2b  interactions"); show(m2, ["zP", "zP:ln_reviews", "zE:ln_reviews"])
        print("      premium at 5 / 120 reviews: %.1f%% / %.1f%%" % tuple(100 * np.expm1(m2.params["zP"] + m2.params["zP:ln_reviews"] * np.log(n)) for n in (5, 120)))
        print(" H3b  accuracy~O+zE+zQ"); show(fit(f"acc~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d), ["O", "zE", "zQ"])
        m4 = fit(f"acc_below~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d, logit=True)
        print("      logit accuracy<4.8: OR(O)=%.3f  95%% CI %.3f-%.3f" % (np.exp(m4.params["O"]), *np.exp(m4.conf_int().loc["O"])))
        print(" H3b' accuracy ~ zP + zE + zQ (same test, no O):"); show(fit(f"acc~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d), ["zP", "zE"])
        print(" H4   O ~ ln comp density"); d = d.assign(ct=d.gid); show(fit(f"O~ln_comp_density_500m+zQ+{ctl}+C(ct)", d), ["ln_comp_density_500m"])
        print("      multi-listing host difference in O: %.3f" % (d[d.multi_listing_host == 1].O.mean() - d[d.multi_listing_host == 0].O.mean()))
    dA, dB = build("A"), build("B"); run(dA, "Spec A (primary)"); run(dB, "Spec B (cleanliness + platform subscore)")
    # Spec C: regression calibration for zE
    def calib(d):
        X = f"zP+zQ+{ctl}+C(neighbourhood_cleansed)"; m = smf.ols(f"zE~{X}", d).fit()
        resid = d.zE - m.fittedvalues; lam = max(0.0, 1 - err_var_half / resid.var())
        return d.assign(zE=m.fittedvalues + lam * resid), lam
    dC, lam = calib(dA); print(f"\nSpec C calibration factor (conditional reliability) = {lam:.3f}")
    bC = dC[dC.is_bookable & dC.ln_price.notna()]; print(" H1b with calibrated E (point estimates; SEs by bootstrap below)")
    f1 = f"ln_price~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)"; pt = smf.ols(f1, bC).fit().params[["zP", "zE"]]
    bs = []; base = dA[dA.is_bookable & dA.ln_price.notna()]
    for i in range(100):
        bb = base.sample(len(base), replace=True, random_state=i).reset_index(drop=True); bb = calib(bb)[0]
        try: bs.append(smf.ols(f1, bb).fit().params[["zP", "zE"]].values)
        except Exception: pass
    bs = np.array(bs); print("   zP: %.3f (boot se %.3f)   zE: %.3f (boot se %.3f)  [boot draws=%d]" % (pt["zP"], bs[:, 0].std(), pt["zE"], bs[:, 1].std(), len(bs)))
    s_acc = dC; m = smf.ols(f"acc~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", s_acc).fit()
    bs = []
    for i in range(100):
        bb = calib(dA.sample(len(dA), replace=True, random_state=i).reset_index(drop=True))[0]
        try: bs.append(smf.ols(f"acc~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", bb).fit().params["zP"])
        except Exception: pass
    print(" H3b' with calibrated E: zP coefficient on accuracy %.4f (boot se %.4f)" % (m.params["zP"], np.std(bs)))

if __name__ == "__main__":
    main(*sys.argv[1:5])
