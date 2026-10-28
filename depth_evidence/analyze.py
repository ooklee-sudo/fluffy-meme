"""Cross-sectional test: among AI-using firms, does depth of use fall where acquisition is cheaper (more ready-to-use software)?"""
import pandas as pd, numpy as np, json, statsmodels.formula.api as smf
from scipy.stats import spearmanr
df=pd.read_csv('isoc_eb_ai_raw.csv')
agg={'EU27_2020','EA20','EU28','EA19'}
w=df.pivot_table(index=['geo','size_emp','time'],columns='indic_is',values='value').reset_index()
w=w[~w.geo.isin(agg)]
w['ready']=w.E_AI_ARDY/w.E_AI_TANY          # share of users on ready-to-use commercial software (low acquisition commitment)
w['own']=(w.E_AI_ADOWN+w.E_AI_AMOWN)/w.E_AI_TANY
w['p2']=w.E_AI_P1GE2/w.E_AI_P1ANY; w['p3']=w.E_AI_P1GE3/w.E_AI_P1ANY
w['t3']=w.E_AI_TGE3/w.E_AI_TANY
w['review']=w.E_AI_BIAS/w.E_AI_PDI
out={}
for yr in (2024,):
    d=w[(w.time==yr)&(w.size_emp=='GE10')].dropna(subset=['ready','p2'])
    for y in ['p2','p3','t3']:
        rho,pv=spearmanr(d.ready,d[y]); m=smf.ols(f'{y}~ready',d).fit(cov_type='HC1')
        out[f'{yr}_{y}']=dict(n=len(d),rho=rho,p=pv,b=m.params['ready'],se=m.bse['ready'])
    d2=d.dropna(subset=['review'])
    if len(d2)>8:
        rho,pv=spearmanr(d2.ready,d2.review); out[f'{yr}_review']=dict(n=len(d2),rho=rho,p=pv)
# adoption level vs depth (all years with data), GE10
for yr in (2023,2024,2025):
    d=w[(w.time==yr)&(w.size_emp=='GE10')].dropna(subset=['E_AI_TANY','p2'])
    rho,pv=spearmanr(d.E_AI_TANY,d.p2); out[f'{yr}_level_p2']=dict(n=len(d),rho=rho,p=pv)
# size classes within country (2024): small vs large
s=w[(w.time==2024)&(w.size_emp.isin(['10-49','50-249','GE250']))].dropna(subset=['ready','p2'])
out['size_means_2024']=s.groupby('size_emp')[['ready','p2','p3','t3','E_AI_TANY']].mean().round(3).to_dict()
# within-country size-class fixed effects
m=smf.ols('p2~ready+C(geo)',s).fit(cov_type='cluster',cov_kwds={'groups':s.geo}); out['size_fe_p2']=dict(n=len(s),b=m.params['ready'],se=m.bse['ready'],p=m.pvalues['ready'])
# technology comparison, EU, 2025: cheap-to-acquire vs costly
e=df[(df.geo=='EU27_2020')&(df.size_emp=='GE10')].pivot_table(index='indic_is',columns='time',values='value')
out['eu_tech_levels']=e.round(1).fillna(-1).to_dict()
json.dump(out,open('depth_results.json','w'),indent=1,default=float)
for k,v in out.items():
    if k not in ('eu_tech_levels',): print(k,{a:(round(b,3) if isinstance(b,float) else b) for a,b in v.items()} if all(not isinstance(x,dict) for x in v.values()) else v)
w.to_csv('depth_panel.csv',index=False)
