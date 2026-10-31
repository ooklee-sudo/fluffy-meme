"""Table 13: legacy search advertising revenue, 2022 (US$ billions in 'rev'; collected from annual reports and filings,
converted at IRS 2022 average exchange rates; sources in Table 13 of the paper), Spearman correlations with months until
full AI answers, and regressions on log revenue (text of Section 5.6).
Same data: data/hand_coded/legacy_search_revenue_2022.csv. Input: data/derived/firm_panel.csv. Output: data/derived/firm_panel_rev.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
from scipy import stats
D=pd.read_csv(DER/"firm_panel.csv")
rev={"Google":162.45,"Bing":12.02,"Baidu":10.33,"Yandex":3.21,"Naver":2.76,"Yahoo! JAPAN":1.48,"Sogou":0.84,"360 Search":0.70,"Daum":0.33,"Seznam":0.25,"DuckDuckGo":0.10,"Ecosia":0.036,"Brave":0.02}
D["rev"]=D.firm.map(rev); E=D.dropna(subset=["rev"]).copy(); E["lr"]=np.log10(E.rev*1000)  # log10 $M
print(E[["firm","rev","share","mA","llm"]].sort_values("rev",ascending=False).to_string(index=False))
def sp(d,lab):
    r=stats.spearmanr(d.rev,d.mA); print(f"{lab:48s} N={len(d):2d} rho={r.statistic:+.2f} p={r.pvalue:.3f}")
sp(E,"All with revenue"); sp(E[E.mkt!="CN"],"Excl. China"); sp(E[E.llm==1],"In-house model"); sp(E[E.llm==0],"No in-house model")
for f in ["mA ~ lr","mA ~ lr + llm","mA ~ lr + I(lr**2)","mA ~ lr + I(lr**2) + llm"]:
    m=smf.ols(f,E).fit(cov_type="HC1"); print(f"{f:28s} N={int(m.nobs)} R2={m.rsquared:.2f}",{k:(round(v,2),round(m.pvalues[k],3)) for k,v in m.params.items() if k!="Intercept"})
E2=E.copy(); E2.loc[E2.firm=="Baidu","mA"]=31
m=smf.ols("mA ~ lr + I(lr**2) + llm",E2).fit(cov_type="HC1"); print("Baidu=Jul2025",{k:(round(v,2),round(m.pvalues[k],3)) for k,v in m.params.items() if k!="Intercept"})
m=smf.ols("mA ~ lr + I(lr**2) + llm",E[E.mkt!="CN"]).fit(cov_type="HC1"); print("excl China N",int(m.nobs),{k:(round(v,2),round(m.pvalues[k],3)) for k,v in m.params.items() if k!="Intercept"})
E.to_csv(DER/"firm_panel_rev.csv",index=False)
