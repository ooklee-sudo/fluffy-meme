"""Table 4, Test B (robustness): 22 Wikipedia editions worldwide x Google Trends interest in the ChatGPT topic.
Part 1 (session script wiki_an.py): DiD, pre-bot sample, exclusions, restricted markets, by-year, long differences.
Part 2 (session inline analysis): pre-/post-ChatGPT trend gap and DiD with edition-specific trends.
Inputs: data/raw/wiki_hours.csv, data/raw/chatgpt_topic_by_country.csv (Poland only).
Outputs: data/derived/wiki_panel.csv, data/derived/wiki_longdiff.csv
The AI dictionary below was typed in during the session from Google Trends 'ChatGPT topic' interest by the main
country of each edition (2023-01 to 2026-10). The multi-country values match simple means of the session's
country values (en: US 12, UK 13; es: Spain 24, Mexico 19; ar: Saudi Arabia 16, Egypt 18; zh: Taiwan 15, Hong Kong 5).
Also in data/hand_coded/wiki_edition_chatgpt_interest.csv."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf, sys
AI={"en":12.5,"de":13,"fr":19,"ja":9,"ko":29,"it":16,"es":21.5,"pt":24,"pl":None,"nl":15,"sv":13,"tr":12,"id":26,"vi":26,"th":18,"ru":5,"fa":8,"zh":10,"uk":14,"cs":13,"he":19,"ar":17}
c=pd.read_csv(RAW/"chatgpt_topic_by_country.csv",index_col=0).iloc[:,0]; AI["pl"]=float(c["Poland"])
w=pd.read_csv(RAW/"wiki_hours.csv")
w["month"]=pd.to_datetime(w.stamp.str[:6],format="%Y%m")
g=w.groupby(["lang","month","stamp"]).views.sum().reset_index().groupby(["lang","month"]).views.mean().reset_index()
g["y"]=np.log(g.views); g["ai"]=g.lang.map(AI); g["ai_z"]=(g.ai-np.mean(list(AI.values())))/np.std(list(AI.values()))
g["post"]=(g.month>="2022-12-01").astype(int); g["ym"]=g.month.dt.strftime("%Y-%m"); g["year"]=g.month.dt.year
g["restricted"]=g.lang.isin(["ru","fa","zh"]).astype(int)
g.to_csv(DER/"wiki_panel.csv",index=False)
def fit(f,d,lab):
    m=smf.ols(f,d).fit(cov_type="cluster",cov_kwds={"groups":d.lang})
    ks=[k for k in m.params.index if ("ai_z" in k or "restricted" in k) and "C(" not in k]
    print(lab,"N",int(m.nobs),{k:(round(m.params[k],4),round(m.bse[k],4),round(m.pvalues[k],4)) for k in ks}); return m
fit("y ~ ai_z:post + C(lang) + C(ym)",g,"(1) all")
fit("y ~ ai_z:post + C(lang) + C(ym)",g[g.month<"2025-05-01"],"(2) pre-bot-reclass")
fit("y ~ ai_z:post + C(lang) + C(ym)",g[~g.lang.isin(["pt","en"])],"(3) excl pt,en")
fit("y ~ restricted:post + C(lang) + C(ym)",g,"(4) restricted")
fit("y ~ ai_z:post + C(lang) + C(ym)",g[g.restricted==0],"(5) unrestricted only")
for yv in range(2019,2027):
    if yv!=2022: g[f"e{yv}"]=(g.year==yv)*g.ai_z
m=fit("y ~ "+" + ".join(f"e{yv}" for yv in range(2019,2027) if yv!=2022)+" + C(lang) + C(ym)",g,"event")
print(m.params[[f"e{y}" for y in range(2019,2027) if y!=2022]].round(4).to_dict()); print(m.pvalues[[f"e{y}" for y in range(2019,2027) if y!=2022]].round(3).to_dict())
# long differences
a=g[g.month.between("2021-09-01","2022-08-01")].groupby("lang").y.mean(); b=g[g.month.between("2025-09-01","2026-08-01")].groupby("lang").y.mean()
L=pd.DataFrame({"chg":(b-a)*100,"ai":pd.Series(AI)}).dropna(); print(L.sort_values("ai").round(1).to_string())
print(smf.ols("chg ~ ai",L).fit(cov_type="HC1").summary2().tables[1].round(3))
L.to_csv(DER/"wiki_longdiff.csv")

print("\n==== Part 2: trend checks (pre-ChatGPT trend gap; edition-specific trends)")
g=pd.read_csv(DER/"wiki_panel.csv",parse_dates=["month"])
g["t"]=(g.month.dt.year-2019)*12+g.month.dt.month
def fit(f,d,lab,keys):
    m=smf.ols(f,d).fit(cov_type="cluster",cov_kwds={"groups":d.lang})
    print(lab,int(m.nobs),{k:(round(m.params[k],4),round(m.bse[k],4),round(m.pvalues[k],3)) for k in keys})
pre=g.month<"2022-12-01"
fit("y ~ ai_z:post + C(lang) + C(ym) + C(lang):t",g,"trend-adj all",["ai_z:post"])
fit("y ~ ai_z:post + C(lang) + C(ym) + C(lang):t",g[~g.lang.isin(["fa","ru","zh","uk"])],"trend-adj excl conflict/censored",["ai_z:post"])
fit("y ~ ai_z:post + C(lang) + C(ym) + C(lang):t",g[g.month<"2025-05-01"],"trend-adj pre-bot",["ai_z:post"])
fit("y ~ restricted:post + C(lang) + C(ym) + C(lang):t",g,"restricted trend-adj",["restricted:post"])
# pre-trend test: slope differences by ai in pre-period
fit("y ~ ai_z:t + C(lang) + C(ym)",g[pre],"pretrend slope",["ai_z:t"])
fit("y ~ ai_z:t + C(lang) + C(ym)",g[~pre],"posttrend slope",["ai_z:t"])
