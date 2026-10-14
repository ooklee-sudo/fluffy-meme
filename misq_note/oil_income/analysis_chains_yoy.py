import json,glob,numpy as np,pandas as pd
from scipy import stats
Q=[f"Q{q} {y}" for y in range(2023,2027) for q in range(1,5)][:14]
D={f.split('/')[1][:-5]:{r['quarter_label']:r['comps_pct'] for r in json.load(open(f)) if r['comps_pct'] is not None} for f in sorted(glob.glob('chains/*.json'))}
P=pd.DataFrame(D).reindex(Q).astype(float)
def tt(x):
    x=x.dropna(); t=stats.ttest_1samp(x,0); w=stats.wilcoxon(x)
    return dict(n=int(len(x)),mean=float(x.mean()),median=float(x.median()),t=float(t.statistic),p_t=float(t.pvalue),p_wilcoxon=float(w.pvalue),share_pos=float((x>0).mean()))
res={}
# Y1
res['Y1_2026Q2']=tt(P.loc['Q2 2026']); res['Y1_2026Q1']=tt(P.loc['Q1 2026'])
m=P.mean(axis=1); ref=m.loc['Q2 2023':'Q1 2026']
res['Y1_means_by_quarter']={k:round(float(v),2) for k,v in m.items()}
res['Y1_rank_2026Q2_among_prior']=int(1+(ref.values>m['Q2 2026']).sum())  # rank from highest
# Y2
d4=P-P.shift(4)
res['Y2_2026Q2']=tt(d4.loc['Q2 2026']); res['Y2_2026Q1']=tt(d4.loc['Q1 2026'])
mm=d4.mean(axis=1); cnt=d4.notna().sum(axis=1)
pl=mm.loc['Q1 2024':'Q1 2026'][cnt.loc['Q1 2024':'Q1 2026']>=10]
res['Y2_means_by_quarter']={k:round(float(v),2) for k,v in mm.dropna().items()}
res['Y2_rank_from_lowest']=int(1+(pl.values<mm['Q2 2026']).sum()); res['Y2_n_placebo']=int(len(pl))
res['Y2_per_chain']=d4.loc['Q2 2026'].round(1).to_dict()
json.dump(res,open('chains_yoy_results.json','w'),indent=1)
print(json.dumps(res,indent=1))
