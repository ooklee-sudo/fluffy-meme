import sys; sys.path.insert(0,".")
"""Pre-registered chain analysis (ANALYSIS_PLAN_CHAINS.md). Quarters 2023Q1..2026Q2 only; Q4 2022 / Q3 2026 rows dropped."""
import json,glob,numpy as np,pandas as pd
from scipy import stats
Q=[f"Q{q} {y}" for y in range(2023,2027) for q in range(1,5)][:14]  # Q1 2023..Q2 2026
from chain_loader import load
D=load()
P=pd.DataFrame(D).reindex(Q).astype(float)
print(P.round(1).to_string())
def rank_p(vals,shock): return (np.sum(np.array(vals)<=shock))/len(vals)
res={}
# primary: delta_t = mean_c(comps_t - comps_{t-1}); placebo t=Q2 2023..Q4 2025; shock Q2 2026
dl=P.diff()
d=dl.mean(axis=1,skipna=True); n=dl.notna().sum(axis=1)
plac=d.loc["Q2 2023":"Q4 2025"]; shock=d.loc["Q2 2026"]
allv=list(plac.values)+[shock]
res['primary']=dict(delta_shock=float(shock),n_chains=int(n["Q2 2026"]),placebo=[round(float(v),2) for v in plac],rank_p_onesided=float(rank_p(allv,shock)),rank_of_shock_from_lowest=int(1+np.sum(plac.values<shock)))
# C2 level shift vs previous four quarters
m=P.mean(axis=1,skipna=True)
c2={}
for i,q in enumerate(Q):
    if i>=4 and q!="Q1 2026": c2[q]=float(m.iloc[i]-m.iloc[i-4:i].mean())
ref=[v for k,v in c2.items() if k not in("Q2 2026",)]
sh=c2["Q2 2026"]
res['C2']=dict(shock=sh,placebo_n=len(ref),rank_p=float(rank_p(ref+[sh],sh)),vals={k:round(v,2) for k,v in c2.items()})
# C3 cross-chain
x=dl.loc["Q2 2026"].dropna()
t=stats.ttest_1samp(x,0)
res['C3']=dict(mean=float(x.mean()),n=int(len(x)),t=float(t.statistic),p_two=float(t.pvalue),share_decrease=float((x<0).mean()),per_chain=x.round(1).to_dict())
# checks: (ii) two-year stacked comps; (iii) weights unavailable -> unweighted only
S=P+P.shift(4)  # stacked: current + year-ago growth
ds=S.diff().mean(axis=1,skipna=True)
pl2=ds.loc["Q2 2024":"Q4 2025"]; s2=ds.loc["Q2 2026"]
res['check_stacked']=dict(shock=float(s2),placebo_n=len(pl2),rank_p=float(rank_p(list(pl2.values)+[s2],s2)))
# (i) exclude one-offs: none identified in extraction notes -> reported as not applicable unless flagged
res['check_median']=dict(shock=float(dl.median(axis=1).loc["Q2 2026"]),rank_p=float(rank_p(list(dl.median(axis=1).loc["Q2 2023":"Q4 2025"].values)+[dl.median(axis=1).loc["Q2 2026"]],dl.median(axis=1).loc["Q2 2026"])))
# also report Q1 2026 transitional delta (descriptive)
res['descriptive_Q1_2026_delta']=float(d.loc["Q1 2026"])
json.dump(res,open('chains_results_calendar.json','w'),indent=1,default=str)
print(json.dumps(res,indent=1,default=str))
