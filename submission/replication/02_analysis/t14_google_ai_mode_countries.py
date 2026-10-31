"""Table 14: months until Google AI Mode by country (N = 47; HC1 p-values). Columns of the paper:
'mode ~ lgdp + lnet + eu_eea + english + reg' (any language), 'mode_loc ~ ...' (local language),
'nonEU mode' (outside EU and regulated markets, N = 30), 'gap ~ ...' (months from AI Overviews to AI Mode).
Rollout months (aio, mode, loc) were compiled from Google announcements and archived Google help pages listing
supported countries/languages (same data: data/hand_coded/google_rollout_by_country.csv).
Input: data/derived/country_covariates.csv (01_data_collection/13_worldbank_covariates.py). Output: data/derived/google_country_panel.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
C=pd.read_csv(DER/"country_covariates.csv",index_col=0)
# AIO (any language first) and AI Mode (any language first) months
aio={"US":"2024-05","GB":"2024-08","IN":"2024-08","JP":"2024-08","ID":"2024-08","MX":"2024-08","BR":"2024-08",
 **{k:"2024-10" for k in ["CA","AU","NZ","PK","BD","NG","KE","ZA","PH","SG","MY","TH","VN","TW","AR","CO","CL","PE"]},
 "KR":"2024-12", **{k:"2025-03" for k in ["AT","BE","DE","IE","IT","PL","PT","ES","CH"]},
 **{k:"2025-05" for k in ["HK","NL","SE","DK","NO","FI","CZ","SA","AE","EG","IL","UA"]}, "TR":"2026-02","FR":"2026-07"}
mode={"US":"2025-05","IN":"2025-07","GB":"2025-07",
 **{k:"2025-08" for k in ["CA","NZ","PK","BD","NG","KE","ZA","PH","SG","MY","ID","TH","VN","JP","KR","TW","HK","BR","MX","AR","CO","CL","PE","SA","AE","EG","IL","UA"]},
 **{k:"2025-10" for k in ["AU","IE","ES","PT","DE","AT","CH","IT","NL","BE","PL","SE","DK","NO","FI","CZ"]},"TR":"2026-02","FR":"2026-07"}
# local-language AI Mode month
loc={"US":"2025-05","GB":"2025-07","CA":"2025-08","AU":"2025-10","NZ":"2025-08","IE":"2025-10","IN":"2025-07","SG":"2025-08",
 "PK":"2025-10","BD":"2025-10","NG":"2026-02","KE":"2026-02","ZA":"2026-02","PH":"2026-02","MY":"2025-10","ID":"2025-09","TH":"2025-10","VN":"2025-10",
 "JP":"2025-09","KR":"2025-09","TW":"2025-10","HK":"2025-10","BR":"2025-09","MX":"2025-09","AR":"2025-09","CO":"2025-09","CL":"2025-09","PE":"2025-09",
 **{k:"2025-10" for k in ["ES","PT","DE","AT","CH","IT","NL","BE","PL","SE","DK","NO","FI","CZ","SA","AE","EG","IL","UA"]},"TR":"2026-02","FR":"2026-07"}
P=lambda s: pd.Period(s,"M")
C["aio"]=pd.Series(aio).map(lambda s:(P(s)-P("2024-05")).n)
C["mode"]=pd.Series(mode).map(lambda s:(P(s)-P("2025-05")).n)
C["mode_loc"]=pd.Series(loc).map(lambda s:(P(s)-P("2025-05")).n)
C["gap"]=pd.Series(mode).map(P).combine(pd.Series(aio).map(P),lambda a,b:(a-b).n)
C["lgdp"]=np.log(C.gdppc); C["lnet"]=np.log(C.net_users_m)
C["reg"]=C.index.isin(["FR","TR"]).astype(int)
D=C.dropna(subset=["lgdp","lnet"]); print("N",len(D))
for y in ["mode","mode_loc","aio","gap"]:
    for f in [f"{y} ~ lgdp + lnet",f"{y} ~ lgdp + lnet + eu_eea + english",f"{y} ~ lgdp + lnet + eu_eea + english + reg"]:
        m=smf.ols(f,D).fit(cov_type="HC1")
        print(f"{f:48s} R2={m.rsquared:.2f}",{k:(round(v,2),round(m.pvalues[k],3)) for k,v in m.params.items() if k!="Intercept"})
    print()
# non-EU, non-regulated only
N=D[(D.eu_eea==0)&(D.reg==0)&(D.index!="CH")]
for y in ["mode","mode_loc","gap"]:
    m=smf.ols(f"{y} ~ lgdp + lnet + english",N).fit(cov_type="HC1"); print("nonEU",y,"N",int(m.nobs),{k:(round(v,2),round(m.pvalues[k],3)) for k,v in m.params.items() if k!="Intercept"})
C.to_csv(DER/"google_country_panel.csv")
print(D[["mode","aio","gap","gdppc","net_users_m","eu_eea"]].sort_values("mode").to_string())
