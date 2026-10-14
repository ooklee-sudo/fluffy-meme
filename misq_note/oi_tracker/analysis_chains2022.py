"""Pre-registered 2022 chain comps analysis (ANALYSIS_PLAN_CHAINS_2022.md)."""
import json,glob,re,numpy as np,pandas as pd
from scipy import stats
CIK={'MCD':'63908','WEN':'30697','QSR':'1618756','YUM':'1041061','DPZ':'1286681','WING':'1636222','CMG':'1058090','SBUX':'829224','JACK':'807882','PZZA':'901491','SHAK':'1620533','CAVA':'1639438','SG':'1477815'}
def cal(r):
    m=pd.Timestamp(r['fiscal_quarter_end'])-pd.Timedelta(days=45); return f"Q{m.quarter} {m.year}"
D={}; bad=0
for f in sorted(glob.glob('chains2022/*.json')):
    t=f.split('/')[1][:-5]
    for r in json.load(open(f)):
        if r['comps_pct'] is None: continue
        v=abs(r['comps_pct']); ok=any(re.search(r'(?<![\d.])'+re.escape(c)+r'(?!\d)',r['quote']) for c in {f"{v:g}",f"{v:.1f}",f"{v:.0f}"}) or v==0
        if f"/data/{CIK[t]}/" not in r['source_url'] or not ok: bad+=1; print("CHECK FAIL",t,r['quarter_label'],r['comps_pct'],r['source_url'])
        D.setdefault(t,{})[cal(r)]=r['comps_pct']
for f in sorted(glob.glob('../oil_income/chains/*.json')):
    t=f.split('/')[-1][:-5]
    for r in json.load(open(f)):
        if r['comps_pct'] is None: continue
        q=cal(r)
        if int(q[-4:])>=2023: D.setdefault(t,{})[q]=r['comps_pct']
print("number/URL check failures:",bad)
QS=["Q4 2021"]+[f"Q{q} {y}" for y in (2022,2023,2024,2025) for q in range(1,5)]+["Q1 2026","Q2 2026"]
P=pd.DataFrame(D).reindex(QS).astype(float)
print(P.round(1).to_string())
dl=P.diff(); d=dl.mean(axis=1); n=dl.notna().sum(axis=1)
ref=d.loc["Q2 2023":"Q4 2025"]
res={"n_by_quarter":{q:int(n[q]) for q in ["Q1 2022","Q2 2022","Q3 2022","Q4 2022"]}}
for q in["Q2 2022","Q3 2022"]:
    refq=ref; sh=d[q]; allv=list(refq.values)+[sh]
    x=dl.loc[q].dropna(); t=stats.ttest_1samp(x,0)
    res[q]=dict(delta=float(sh),n=int(len(x)),rank_p_onesided=float(np.mean(np.array(allv)<=sh+1e-12)),rank_from_lowest=int(1+(refq.values<sh).sum()),n_ref=len(refq),t=float(t.statistic),p_t=float(t.pvalue),share_decrease=float((x<0).mean()),per_chain=x.round(1).to_dict())
res["mean_comps_by_quarter"]={q:round(float(v),2) for q,v in P.mean(axis=1).items()}
res["delta_by_quarter"]={q:round(float(v),2) for q,v in d.dropna().items()}
json.dump(res,open("results_chains2022.json","w"),indent=1)
print(json.dumps({k:res[k] for k in["n_by_quarter","Q2 2022","Q3 2022","mean_comps_by_quarter","delta_by_quarter"]},indent=1))
