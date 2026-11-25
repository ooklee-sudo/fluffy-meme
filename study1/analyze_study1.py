"""Study 1, step 5: measures and regressions on the sampled listings.

Usage: python analyze_study1.py WORKDIR PAIRS_JSONL REVIEWS_JSONL REVIEWS_CSV
Reads WORKDIR/sample.csv. No human validation sample is used here, so estimates are NOT PPI-corrected.
"""
import sys, json, re, warnings
import numpy as np, pandas as pd, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
ATT = {"cleanliness": "clean", "spaciousness": "space", "brightness": "bright", "furnishing_condition": "furn", "photographic_quality": "Q"}

def bradley_terry(wins, n_iter=200, prior=1.0):
    """wins: dict (i,j)->wins of i over j (0.5 for ties). Returns log-strengths; ridge via prior vs. a virtual average player."""
    ids = sorted({k for p in wins for k in p}); ix = {k: n for n, k in enumerate(ids)}
    m = len(ids); W = np.full(m, prior / 2.0); N = {}
    for (i, j), w in wins.items():
        a, b = ix[i], ix[j]; W[a] += w
        N[(a, b)] = N.get((a, b), 0) + 1; N[(b, a)] = N.get((b, a), 0) + 1
    for (i, j), w in wins.items():
        pass
    # total wins for j over i are accounted through the wins dict being keyed both ways
    p = np.ones(m)
    rows = np.array([k[0] for k in N]); cols = np.array([k[1] for k in N]); cnt = np.array(list(N.values()), float)
    for _ in range(n_iter):
        den = np.full(m, prior / (p + 1.0) if False else 0.0)
        den = np.bincount(rows, weights=cnt / (p[rows] + p[cols]), minlength=m) + prior / (p + 1.0)
        p = W / den; p = p / np.exp(np.log(p).mean())
    return dict(zip(ids, np.log(p)))

def build_P(s, pairs_path):
    raw = {}
    for l in open(pairs_path):
        x = json.loads(l); raw.setdefault((x["a"], x["b"]), {})[x["order"]] = x["res"]
    out = {}
    for att in ATT:
        wins = {}
        for (a, b), v in raw.items():
            if len(v) < 2: continue
            w1 = v["AB"].get(att) == "A"; w2 = v["BA"].get(att) == "B"
            if v["AB"].get(att) not in ("A", "B") or v["BA"].get(att) not in ("A", "B"): continue
            wa = 1.0 if (w1 and w2) else (0.0 if (not w1 and not w2) else 0.5)
            wins[(a, b)] = wa; wins[(b, a)] = 1 - wa
        out[att] = wins
    reversals = {att: np.mean([ (v["AB"].get(att) == "A") != (v["BA"].get(att) == "B") for v in raw.values() if len(v) == 2 and v["AB"].get(att) in "AB" and v["BA"].get(att) in "AB"]) for att in ATT}
    # BT within city x room_type groups
    grp = s.set_index("id")[["city", "room_type"]].apply(tuple, axis=1).to_dict()
    scores = {att: {} for att in ATT}
    for att, wins in out.items():
        byg = {}
        for (a, b), w in wins.items():
            if grp.get(a) == grp.get(b): byg.setdefault(grp[a], {})[(a, b)] = w
        for g, wg in byg.items():
            scores[att].update(bradley_terry(wg))
    return scores, reversals

def zs(x): return (x - x.mean()) / x.std()

def main(work, pairs_path, rev_path, rev_csv):
    s = pd.read_csv(f"{work}/sample.csv")
    scores, reversals = build_P(s, pairs_path)
    print("order reversal rate by attribute:", {k: round(v, 3) for k, v in reversals.items()})
    s["gid"] = s.city + "|" + s.room_type
    for att, k in ATT.items():
        s[f"P_{k}"] = s.id.map(scores[att])
        s[f"zP_{k}"] = s.groupby("gid")[f"P_{k}"].transform(zs)
    # experienced quality
    rows = []
    for l in open(rev_path):
        x = json.loads(l)
        for att in ["cleanliness", "spaciousness", "brightness", "furnishing_condition"]:
            v = x["res"].get(att)
            if v in (-1, 0, 1): rows.append((x["listing_id"], ATT[att], v))
    e = pd.DataFrame(rows, columns=["id", "k", "v"])
    g = e.groupby(["id", "k"]).v.agg(["mean", "count"]).reset_index(); g = g[g["count"] >= 3]
    for k in ["clean", "space", "bright", "furn"]:
        s[f"E_{k}"] = s.id.map(g[g.k == k].set_index("id")["mean"])
        s[f"zE_{k}"] = s.groupby("gid")[f"E_{k}"].transform(zs)
    A = ["clean", "space", "bright", "furn"]
    for k in A: s[f"O_{k}"] = s[f"zP_{k}"] - s[f"zE_{k}"]
    s["O"] = s[[f"O_{k}" for k in A]].mean(axis=1)
    s["zP"] = zs(s[[f"zP_{k}" for k in A]].mean(axis=1)); s["zE"] = zs(s[[f"zE_{k}" for k in A]].mean(axis=1))
    s["zQ"] = s.groupby("gid").zP_Q.transform(lambda x: x)
    s["O"] = zs(s.O) * 1.0
    # complaints
    rv = pd.read_csv(rev_csv)
    pat = re.compile(r"mislead|not as (pictured|shown|advertised|described)|(smaller|darker|dirtier|older|worse) than (the )?(pictur|photo|shown|appear|expect|advertis)|photos? (are|were) (not|misleading)|does ?n[o']t look like|nothing like the (photo|pictur)", re.I)
    rv["c"] = rv.comments.fillna("").map(lambda t: bool(pat.search(t)))
    s["complaint_rate"] = s.id.map(rv.groupby("listing_id").c.mean())
    s["acc"] = s.review_scores_accuracy; s["acc_below"] = (s.acc < 4.8).astype(float).where(s.acc.notna())
    s.to_csv(f"{work}/analysis_frame.csv", index=False)
    d = s.dropna(subset=["zP", "zE", "zQ"]).copy()
    print("analysis N", len(d), "bookable", int(d.is_bookable.sum()), "| listings with E:", s.zE.notna().sum())
    print("O: mean %.2f sd(before rescale n/a); share >1 SD: %.3f" % (d.O.mean(), (d.O > 1).mean()))
    print("corr(O, accuracy) =", round(d[["O", "acc"]].corr().iloc[0, 1], 3), "| corr(zP,zE) =", round(d[["zP", "zE"]].corr().iloc[0, 1], 3))
    ctl = "C(room_type)+accommodates+bedrooms+superhost+multi_listing_host+host_tenure_yrs"
    def fit(f, df, logit=False):
        mod = (smf.logit if logit else smf.ols)(f, df)
        grp = pd.factorize(df.loc[mod.data.row_labels, "neighbourhood_cleansed"])[0]
        return mod.fit(cov_type="cluster", cov_kwds={"groups": grp}, disp=0)
    def show(m, names):
        for n in names: print(f"    {n:24s} b={m.params[n]:8.3f}  se={m.bse[n]:6.3f}  p={m.pvalues[n]:.3g}")
        print("    n =", int(m.nobs))
    b = d[(d.is_bookable) & d.ln_price.notna()]
    print("Col1 ln(price) ~ zP + zE + zQ"); m1 = fit(f"ln_price~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", b); show(m1, ["zP", "zE", "zQ"])
    print("Col2 + interactions with ln(reviews)"); m2 = fit(f"ln_price~zP*ln_reviews+zE*ln_reviews+zQ+{ctl}+C(neighbourhood_cleansed)", b)
    show(m2, ["zP", "zE", "zP:ln_reviews", "zE:ln_reviews"])
    for n in (5, 120): print(f"    implied premium at {n} reviews: {100*np.expm1(m2.params['zP']+m2.params['zP:ln_reviews']*np.log(n)):.1f}%")
    print("Col3 accuracy ~ O"); m3 = fit(f"acc~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d); show(m3, ["O", "zE", "zQ"])
    print("Col4 logit accuracy<4.8"); m4 = fit(f"acc_below~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d, logit=True)
    print("    OR O = %.3f  (95%% CI %.3f-%.3f)  n=%d" % (np.exp(m4.params["O"]), *np.exp(m4.conf_int().loc["O"]), m4.nobs))
    print("Complaints"); m6 = fit(f"complaint_rate~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d); show(m6, ["O"])
    print("Col5 O ~ ln competitor density"); d["ct"] = d.gid; m5 = fit(f"O~ln_comp_density_500m+zQ+{ctl}+C(ct)", d); show(m5, ["ln_comp_density_500m", "zQ"])
    print("O by city/room type:\n", d.groupby("city").O.agg(["mean", "std", "count"]).round(3))
    print("multi-listing host diff in O:", round(d[d.multi_listing_host == 1].O.mean() - d[d.multi_listing_host == 0].O.mean(), 3))
    print("share of listings with each E attribute (>=3 mentions):", {k: round(s[f'E_{k}'].notna().mean(), 3) for k in A})

if __name__ == "__main__":
    main(*sys.argv[1:5])
