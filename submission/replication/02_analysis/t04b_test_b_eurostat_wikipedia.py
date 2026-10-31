"""Table 4, Test B: 24 European Wikipedia editions x Eurostat 2025 generative-AI use (isoc_ai_iaiu).
Edition and month FE, clustered by edition; (2) adds 2022 daily-internet use (isoc_ci_ifp_fu) x post;
pre/post trend slopes; edition trends; pre-bot-reclassification sample; by-year coefficients; long differences.
Rows of Table 4 (B): (1) DiD all platforms; (2) + daily internet; desktop (1); (6) before April 2025;
'by year' event coefficients; long difference with and without daily internet.
Inputs: data/raw/wiki_hours.csv, data/raw/wiki_hours_eu.csv, data/raw/eurostat_genai_2025.csv,
data/raw/eurostat_daily_internet_2022.csv. Output: data/derived/eu_longdiff.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
MAP={"de":"DE","fr":"FR","it":"IT","pl":"PL","nl":"NL","sv":"SE","cs":"CZ","tr":"TR","hu":"HU","ro":"RO","el":"EL","fi":"FI","da":"DK","bg":"BG","hr":"HR","sk":"SK","sl":"SI","lt":"LT","lv":"LV","et":"EE","no":"NO","sr":"RS","mk":"MK","sq":"AL"}
ai=pd.read_csv(RAW/"eurostat_genai_2025.csv").set_index("geo").v
net=pd.read_csv(RAW/"eurostat_daily_internet_2022.csv").set_index("geo").v
w=pd.concat([pd.read_csv(RAW/"wiki_hours.csv"),pd.read_csv(RAW/"wiki_hours_eu.csv")])
w=w[w.lang.isin(MAP)]
w["month"]=pd.to_datetime(w.stamp.str[:6],format="%Y%m")
def build(plat):
    x=w if plat=="all" else w[w.platform==plat]
    g=x.groupby(["lang","month","stamp"]).views.sum().reset_index().groupby(["lang","month"]).views.mean().reset_index()
    g["y"]=np.log(g.views); g["geo"]=g.lang.map(MAP); g["ai"]=g.geo.map(ai); g["net"]=g.geo.map(net)
    g["ai_z"]=(g.ai-ai[list(MAP.values())].mean())/ai[list(MAP.values())].std()
    g["net_z"]=(g.net-g.net.mean())/g.net.std()
    g["post"]=(g.month>="2022-12-01").astype(int); g["ym"]=g.month.dt.strftime("%Y-%m"); g["year"]=g.month.dt.year
    g["t"]=(g.month.dt.year-2019)*12+g.month.dt.month
    return g
def fit(f,d,lab,keys):
    m=smf.ols(f,d).fit(cov_type="cluster",cov_kwds={"groups":d.lang})
    print(f"  {lab:38s} N={int(m.nobs):5d} "+"  ".join(f"{k}={m.params[k]:+.4f} (se {m.bse[k]:.4f}, p={m.pvalues[k]:.3f})" for k in keys))
    return m
for plat in ["all","desktop","mobile"]:
    g=build(plat); print(f"== {plat}: {g.lang.nunique()} editions, missing net: {g[g.net.isna()].lang.unique()}")
    fit("y ~ ai_z:post + C(lang) + C(ym)",g,"(1) DiD",["ai_z:post"])
    gg=g.dropna(subset=["net"]); fit("y ~ ai_z:post + net_z:post + C(lang) + C(ym)",gg,"(2) + daily-internet x post",["ai_z:post","net_z:post"])
    pre=g.month<"2022-12-01"
    fit("y ~ ai_z:t + C(lang) + C(ym)",g[pre],"(3) pre-trend slope",["ai_z:t"])
    fit("y ~ ai_z:t + C(lang) + C(ym)",g[~pre],"(4) post-trend slope",["ai_z:t"])
    fit("y ~ ai_z:post + C(lang) + C(ym) + C(lang):t",g,"(5) DiD + edition trends",["ai_z:post"])
    fit("y ~ ai_z:post + C(lang) + C(ym)",g[g.month<"2025-05-01"],"(6) DiD, before bot reclassification",["ai_z:post"])
    for yv in range(2019,2027):
        if yv!=2022: g[f"e{yv}"]=(g.year==yv)*g.ai_z
    m=smf.ols("y ~ "+" + ".join(f"e{yv}" for yv in range(2019,2027) if yv!=2022)+" + C(lang) + C(ym)",g).fit(cov_type="cluster",cov_kwds={"groups":g.lang})
    print("  event:", {k:(round(m.params[k],3),round(m.pvalues[k],3)) for k in m.params.index if k.startswith("e20")})
    if plat=="all":
        a=g[g.month.between("2021-09-01","2022-08-01")].groupby("lang").y.mean(); b=g[g.month.between("2025-09-01","2026-08-01")].groupby("lang").y.mean()
        L=pd.DataFrame({"chg":(b-a)*100}); L["ai"]=L.index.map(lambda l: ai[MAP[l]]); L["net"]=L.index.map(lambda l: net.get(MAP[l],np.nan))
        print(L.sort_values("ai").round(1).to_string()); L.to_csv(DER/"eu_longdiff.csv")
        print(smf.ols("chg ~ ai",L).fit(cov_type="HC1").summary2().tables[1].round(3))
        print(smf.ols("chg ~ ai + net",L.dropna()).fit(cov_type="HC1").summary2().tables[1].round(3))
