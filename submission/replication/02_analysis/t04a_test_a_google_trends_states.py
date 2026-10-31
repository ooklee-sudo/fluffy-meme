"""Table 4, Test A: U.S. states, Google Trends (N = 4,743 state-months).
y = log share of question-type queries ('how to','what is') relative to 'weather','near me';
treatment = standardized state ChatGPT interest (2023-2026) x post-December 2022; state and month FE; clustered by state.
Inputs: data/raw/trends/US-*.csv, data/raw/chatgpt_by_state.csv. Output: data/derived/panel.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, glob, statsmodels.formula.api as smf
names={"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}
ai=pd.read_csv(RAW/"chatgpt_by_state.csv",index_col=0)["ChatGPT"]
fr=[]
for f in glob.glob(str(RAW/"trends"/"US-*.csv")):
    s=f.split("US-")[1][:2]; d=pd.read_csv(f,parse_dates=["date"]); d["state"]=s; fr.append(d)
P=pd.concat(fr); P=P[P.date<"2026-10-01"]
L=lambda v: np.log(v.clip(lower=1))
P["info"]=0.5*(L(P["how to"])+L(P["what is"]))
P["ctrl"]=0.5*(L(P["weather"])+L(P["near me"]))
P["y"]=P["info"]-P["ctrl"]
P["ai"]=P.state.map(lambda s: ai[names[s]])
P["ai_z"]=(P.ai-ai.mean())/ai.std()
P["year"]=P.date.dt.year; P["ym"]=P.date.dt.strftime("%Y-%m")
P["post"]=(P.date>="2022-12-01").astype(int)
P.to_csv(DER/"panel.csv",index=False)
# 1) DiD continuous
m=smf.ols("y ~ ai_z:post + C(state) + C(ym)",P).fit(cov_type="cluster",cov_kwds={"groups":P.state})
print("DiD ai_z x post:",round(m.params["ai_z:post"],4),round(m.bse["ai_z:post"],4),round(m.pvalues["ai_z:post"],4),"N",int(m.nobs))
# separate components
for dv in ["info","ctrl"]:
    m2=smf.ols(f"{dv} ~ ai_z:post + C(state) + C(ym)",P).fit(cov_type="cluster",cov_kwds={"groups":P.state})
    print(dv, round(m2.params["ai_z:post"],4), round(m2.pvalues["ai_z:post"],4))
for kw in ["how to","what is","weather","near me"]:
    P["v"]=L(P[kw]); m2=smf.ols("v ~ ai_z:post + C(state) + C(ym)",P).fit(cov_type="cluster",cov_kwds={"groups":P.state})
    print(kw, round(m2.params["ai_z:post"],4), round(m2.pvalues["ai_z:post"],4))
# 2) event study by year (base 2022)
for yv in range(2019,2027):
    if yv!=2022: P[f"e{yv}"]=(P.year==yv)*P.ai_z
f="y ~ "+" + ".join(f"e{yv}" for yv in range(2019,2027) if yv!=2022)+" + C(state) + C(ym)"
m=smf.ols(f,P).fit(cov_type="cluster",cov_kwds={"groups":P.state})
print(m.summary2().tables[1].loc[[c for c in m.params.index if c.startswith("e")],["Coef.","Std.Err.","P>|z|"]].round(4))
