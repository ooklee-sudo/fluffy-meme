"""Does measured drift predict user-reported errors? Uses outputs of wildchat_drift.py.

A. Weekly drift (JS divergence of first-prompt unigrams vs. a reference window) and the weekly
   correction rate, per model family, with time trend.
B. Conversation level: P(any correction | multi-turn) on post-cutoff-reference flags with week
   fixed effects and week-clustered SEs (controls: log length, code, #turns).
Restricted to models whose training cutoff is ~Sep 2021 so that year/entity flags mean "after cutoff".
"""
import sys, pickle, json
import numpy as np, pandas as pd
import statsmodels.api as sm

d = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "dissat_turns"
df = pd.read_csv(f"{d}/conv_features.csv.gz")
toks = pickle.load(open(f"{d}/weekly_tokens.pkl", "rb"))
print(df.model.value_counts().head(8).to_string())
old = df.model.str.startswith("gpt-3.5-turbo") | df.model.isin(["gpt-4-0314", "gpt-4-0613"])
df = df[old].copy(); df["fam"] = np.where(df.model.str.startswith("gpt-4"), "gpt4", "gpt35")
out = {}

# ---------- A. weekly ----------
def js(p, q):
    m = (p + q) / 2
    f = lambda a, b: np.sum(np.where(a > 0, a * np.log(a / b), 0.0))
    return 0.5 * f(p, m) + 0.5 * f(q, m)

rows = []
for fam in ["gpt35", "gpt4"]:
    wks = sorted(w for (w, f) in toks if f == fam)
    tot = pd.Series({w: sum(toks[(w, fam)].values()) for w in wks})
    wks = [w for w in wks if tot[w] >= 20000 and len(df[(df.week == w) & (df.fam == fam)]) >= 500]
    if len(wks) < 12: continue
    ref = sum((toks[(w, fam)] for w in wks[:4]), start=__import__("collections").Counter())
    vocab = [w for w, _ in ref.most_common(5000)]
    idx = {w: i for i, w in enumerate(vocab)}
    def vec(c):
        v = np.zeros(len(vocab)); 
        for k, n in c.items():
            if k in idx: v[idx[k]] = n
        return (v + 0.5) / (v + 0.5).sum()
    pref = vec(ref)
    for w in wks[4:]:
        g = df[(df.week == w) & (df.fam == fam)]
        lt = g.later_turns.sum()
        rows.append(dict(fam=fam, week=w, drift=js(vec(toks[(w, fam)]), pref), n=len(g),
                         corr=g[OUT].sum() / max(lt, 1), year_ref=g.year_ref.mean(),
                         ent_ref=g.ent_ref.mean(), code=g.code.mean(), jb=g.jb.mean(), len=np.log(g.first_len + 1).mean(),
                         turns=g.n_user.mean()))
W = pd.DataFrame(rows); W.to_csv(f"{d}/weekly_drift.csv", index=False)
print(W.groupby("fam")[["drift", "corr", "year_ref", "ent_ref"]].agg(["mean", "std"]).round(4).to_string())
for fam, g in W.groupby("fam"):
    g = g.reset_index(drop=True); t = np.arange(len(g)) / 52
    for name, X in [("drift only", g[["drift"]]), ("drift + trend", pd.DataFrame({"drift": g.drift, "t": t})),
                    ("drift + trend + mix", pd.DataFrame({"drift": g.drift, "t": t, "code": g.code, "len": g.len, "turns": g.turns, "jb": g.jb}))]:
        m = sm.WLS(g["corr"], sm.add_constant(X), weights=g.n).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        b, se = m.params["drift"], m.bse["drift"]
        out[f"weekly_{fam}_{name}"] = dict(b=float(b), se=float(se), p=float(m.pvalues["drift"]), weeks=len(g))
        print(f"[weekly {fam:5s} | {name:20s}] slope on drift = {b:8.4f}  (se {se:.4f}, p={m.pvalues['drift']:.3f}, weeks={len(g)})")
    print(f"   corr(drift, trend) = {np.corrcoef(g.drift, t)[0,1]:.2f}")

# ---------- B. conversation level ----------
c = df[df.later_turns >= 1].copy()
c["any"] = (c[OUT] > 0).astype(int)
c["loglen"] = np.log(c.first_len + 1); c["logturns"] = np.log(c.n_user)
for fam in ["gpt35", "gpt4"]:
    g = c[c.fam == fam]
    if len(g) < 5000: continue
    for flags in (["year_ref"], ["ent_ref"], ["year_ref", "ent_ref"]):
        X = pd.concat([g[flags + ["code", "jb", "loglen", "logturns"]], pd.get_dummies(g.week, drop_first=True, dtype=float)], axis=1)
        m = sm.Logit(g["any"], sm.add_constant(X)).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(g.week)[0]})
        for fl in flags:
            lo, hi = np.exp(m.conf_int().loc[fl])
            out[f"conv_{fam}_{'+'.join(flags)}_{fl}"] = dict(OR=float(np.exp(m.params[fl])), lo=float(lo), hi=float(hi), n=len(g))
            print(f"[conv {fam:5s} | {'+'.join(flags):15s}] {fl:8s} OR={np.exp(m.params[fl]):.3f} [{lo:.3f},{hi:.3f}] n={len(g)}  base rate={g['any'].mean():.3f}")
json.dump(out, open(f"{d}/drift_results.json", "w"), indent=1)
