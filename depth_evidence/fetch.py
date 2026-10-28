"""Fetch Eurostat isoc_eb_ai indicators used for the acquisition-cost / depth-of-use evidence (Section 3.8)."""
import requests, json, pandas as pd
EU='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ai'
IND=['E_AI_TANY','E_AI_TNLG','E_AI_TPVSG','E_AI_TML','E_AI_TAR','E_AI_TGE2','E_AI_TGE3','E_AI_P1ANY','E_AI_P1GE2','E_AI_P1GE3',
     'E_AI_ARDY','E_AI_ADOWN','E_AI_AMOWN','E_AI_AEXT','E_AI_PDI','E_AI_BIAS']
q='?format=JSON&lang=en&unit=PC_ENT&nace_r2=C10-S951_X_K&'+'&'.join('indic_is='+i for i in IND)
rows=[]
for size in ['GE10','10-49','50-249','GE250']:
    r=requests.get(EU+q+'&size_emp='+size,timeout=120)
    if r.status_code!=200: print(size,r.status_code,r.text[:150]); continue
    j=r.json(); ids=j['id']; sz=j['size']; dim=j['dimension']
    idx={k:list(dim[k]['category']['index']) for k in ids}
    import itertools
    for n,combo in enumerate(itertools.product(*[range(s) for s in sz])):
        v=j['value'].get(str(n))
        if v is None: continue
        rec={k:idx[k][c] for k,c in zip(ids,combo)}; rec['value']=v; rows.append(rec)
df=pd.DataFrame(rows); df.to_csv('isoc_eb_ai_raw.csv',index=False)
print(df.groupby(['size_emp','time']).geo.nunique())
