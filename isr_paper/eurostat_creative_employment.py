"""Exploratory: EU27 employment (thousand persons, LFS) by NACE 2-digit, 2015-2025. Treated (a priori): J59 film/video/TV/sound,
M73 advertising & market research, M74 other professional/scientific/technical (incl. specialised design, photography).
Statistic: change in ln employment, mean(2023-25) minus mean(2019-21); pre-trend: mean(2019-21) minus mean(2015-17).
Inference: randomization over all sets of 3 sectors."""
import json, itertools, numpy as np, pandas as pd
d=json.load(open("data/eurostat/lfsa_egan22d.json")); ids=d["id"]; size=d["size"]
idx={k:d["dimension"][k]["category"]["index"] for k in ids}; inv={k:{i:c for c,i in idx[k].items()} for k in ids}
rows=[]
for pos,v in d["value"].items():
    p=int(pos); key={}
    for k,s in reversed(list(zip(ids,size))): key[k]=inv[k][p%s]; p//=s
    key["v"]=v; rows.append(key)
df=pd.DataFrame(rows); df=df[df.geo=="EU27_2020"]
print("EU27 sectors with data:",df.nace_r2.nunique(),"years",df.time.min(),df.time.max())
E=df.pivot(index="time",columns="nace_r2",values="v").drop(columns=["TOTAL","NRP"],errors="ignore")
E=E.loc["2015":"2025"]; E=E.dropna(axis=1); L=np.log(E)
w=lambda a,b:L.loc[a:b].mean()
post=w("2023","2025")-w("2019","2021"); pre=w("2019","2021")-w("2015","2017")
TREAT=["J59","M73","M74"]; sectors=list(L.columns); print("sectors in complete panel:",len(sectors),"treated present:",all(t in sectors for t in TREAT))
KNOW=[s for s in sectors if s[0] in "JKMN" or s in ("L68",)]
def ri(delta,pool):
    t=TREAT; obs=delta[t].mean()-delta[[s for s in pool if s not in t]].mean(); cnt=tot=0
    for tri in itertools.combinations(pool,3):
        tot+=1; cnt+=abs(delta[list(tri)].mean()-delta[[s for s in pool if s not in tri]].mean())>=abs(obs)
    return obs,cnt/tot
for name,pool in (("all NACE 2-digit sectors",sectors),("knowledge-service sectors (J,K,L68,M,N)",KNOW)):
    pool=sorted(set(pool)|set(TREAT)); o1,p1=ri(pre,pool); o2,p2=ri(post,pool)
    print(f"{name} (n={len(pool)}): pre-trend {o1:+.3f} (p={p1:.3f}) | change 2019-21 -> 2023-25: {o2:+.3f} (p={p2:.3f})")
print("\nper-sector ln change 2019-21 -> 2023-25 (treated):",{t:round(float(post[t]),3) for t in TREAT},"| median all:",round(float(post.median()),3))
print("rank of treated among",len(sectors),"(1=largest fall):",{t:int((post.rank()[t])) for t in TREAT})
print("employment 2019/2021/2025 (thousand):",{t:[round(float(E.loc[y,t])) for y in ("2019","2021","2025")] for t in TREAT})
E.to_csv("data/eurostat/eu27_nace2_employment.csv")
