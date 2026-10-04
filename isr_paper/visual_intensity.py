"""Occupation-level visual intensity from O*NET Abilities (1.A.4.a.1-7: Near/Far Vision, Visual Color Discrimination,
Night/Peripheral Vision, Depth Perception, Glare Sensitivity). Importance (IM, 1-5) rescaled to 0-1, averaged over the
7 abilities; O*NET-SOC codes collapsed to 6-digit SOC by simple mean.  Output: data/visual_intensity_soc.csv"""
import csv, collections, statistics as st, json, sys
VIS={"1.A.4.a.%d"%i for i in range(1,8)}
rows=list(csv.DictReader(open("data/Abilities.txt",encoding="utf-8"),delimiter="\t"))
titles={r["O*NET-SOC Code"]:r["Title"] for r in csv.DictReader(open("data/Occupation_Data.txt",encoding="utf-8"),delimiter="\t")}
per=collections.defaultdict(dict)   # onet-soc -> element -> IM
for r in rows:
    if r["Element ID"] in VIS and r["Scale ID"]=="IM": per[r["O*NET-SOC Code"]][r["Element ID"]]=float(r["Data Value"])
onet={s:st.mean((v-1)/4 for v in d.values()) for s,d in per.items() if len(d)==7}
soc=collections.defaultdict(list)
for s,v in onet.items(): soc[s[:7]].append(v)
soc={k:st.mean(v) for k,v in soc.items()}
if __name__=="__main__":
    with open("data/visual_intensity_soc.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["soc6","visual_intensity"])
        for k in sorted(soc): w.writerow([k,round(soc[k],4)])
    # internal consistency (Cronbach's alpha) across O*NET-SOC occupations
    items=sorted(VIS); X=[[per[s][e] for e in items] for s in onet]
    k=7; var=[st.pvariance([x[i] for x in X]) for i in range(k)]; tot=st.pvariance([sum(x) for x in X])
    print("O*NET-SOC occupations",len(onet),"-> SOC6",len(soc),"| Cronbach alpha",round(k/(k-1)*(1-sum(var)/tot),3))
    vals=sorted(soc.values()); q=lambda p:vals[int(p*(len(vals)-1))]
    print("composite quantiles p10/50/90",[round(q(p),2) for p in (.1,.5,.9)])
    byt={s:v for s,v in onet.items()}
    top=sorted(byt,key=byt.get,reverse=True); 
    print("TOP:",[(titles[s][:30],round(byt[s],2)) for s in top[:6]]); print("BOTTOM:",[(titles[s][:30],round(byt[s],2)) for s in top[-6:]])
