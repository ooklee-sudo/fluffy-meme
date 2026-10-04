"""Eurostat 2025 enterprise AI survey (10+ employees): adoption of picture/video/audio-generating AI (E_AI_TPVSG), text generation (E_AI_TNLG),
barriers among enterprises that considered AI (unit PC_ENT_AI_EC), and the exposure gradient across sectors.
Sector creation exposure = EU27 2021 employment-weighted mean over ISCO major groups of O*NET creation exposure (LLM-coded, mapped O*NET -> ISCO-08)."""
import json, collections, random, numpy as np, pandas as pd
import uk_exposure as UX, classify_onet as C
def jload(f):
    d=json.load(open(f)); ids=d["id"]; size=d["size"]
    idx={k:d["dimension"][k]["category"]["index"] for k in ids}; inv={k:{i:c for c,i in idx[k].items()} for k in ids}
    rows=[]
    for pos,v in d["value"].items():
        p=int(pos); key={}
        for k,s in reversed(list(zip(ids,size))): key[k]=inv[k][p%s]; p//=s
        key["v"]=v; rows.append(key)
    return pd.DataFrame(rows)
# time series (EU27, 10+): TPVSG available which years?
a=jload("data/eurostat/isoc_eb_ain2.json"); s_=jload("data/eurostat/isoc_eb_ai.json")
eu=s_[(s_.geo=="EU27_2020")&(s_.nace_r2=="C10-S951_X_K")&(s_.unit=="PC_ENT")&(s_.size_emp=="GE10")]
print("EU27 10+ adoption by year (% of enterprises):")
print(eu[eu.indic_is.isin(["E_AI_TPVSG","E_AI_TNLG","E_AI_TIR","E_AI_TANY"])].pivot(index="indic_is",columns="time",values="v").round(2).to_string())
# size gradient 2025 and barriers
sz=s_[(s_.geo=="EU27_2020")&(s_.time=="2025")&(s_.nace_r2=="C10-S951_X_K")&(s_.size_emp.isin(["10-49","50-249","GE250"]))]
print("\n2025 adoption by size class (% of enterprises):"); print(sz[(sz.unit=="PC_ENT")&sz.indic_is.isin(["E_AI_TPVSG","E_AI_TNLG"])].pivot(index="indic_is",columns="size_emp",values="v").round(1).to_string())
B={"E_AI_BLE":"lack of expertise","E_AI_BLEG":"unclear legal consequences","E_AI_BCDP":"data protection/privacy","E_AI_BCST":"cost too high","E_AI_BDDT":"data availability/quality","E_AI_BINC":"incompatibility","E_AI_BEC":"ethical considerations","E_AI_BNU":"AI not useful"}
bar=s_[(s_.geo=="EU27_2020")&(s_.time=="2025")&(s_.nace_r2=="C10-S951_X_K")&(s_.unit=="PC_ENT_AI_EC")&(s_.size_emp=="GE10")&s_.indic_is.isin(B)].set_index("indic_is").v
print("\nBarriers cited by enterprises that considered AI but do not use it (EU27, 10+, 2025; % of considerers):")
for k,v in bar.sort_values(ascending=False).items(): print(f"  {B[k]:32s} {v:5.1f}")
# sector exposure
tasks=pd.DataFrame(C.load())[["id","soc"]]; cre=pd.DataFrame([json.loads(l) for l in open("data/all_creation_llm.jsonl")])[["id","s"]]
t=tasks.merge(cre,on="id"); occ=(t.s/2).groupby(t.soc).mean().to_dict()
o2i=UX.onet_to_isco(); byg=collections.defaultdict(list)
for soc,v in occ.items():
    for i in o2i.get(soc,()): byg["OC"+i[0]].append(v)
Eg={g:np.mean(v) for g,v in byg.items()}
e=jload("data/eurostat/lfsa_eisn2.json"); e=e[(e.geo=="EU27_2020")&(e.time=="2021")&(e.age=="Y_GE15")&(e.sex=="T")&(e.isco08.isin(Eg))]
SECT=["C","D","E","F","G","H","I","J","L","M","N"]; rows=[]
for sct in SECT:
    x=e[e.nace_r2==sct].set_index("isco08").v.dropna(); w=x/x.sum(); rows.append((sct,float((w*pd.Series(Eg)[w.index]).sum())))
ex=pd.DataFrame(rows,columns=["nace","E"]); ex["zE"]=(ex.E-ex.E.mean())/ex.E.std()
print("\nSector creation exposure (employment-weighted):",ex.assign(E=ex.E.round(4)).set_index("nace").E.to_dict())
# first stage: adoption vs exposure across sectors (EU27) and country-sector cells
sec=a[(a.unit=="PC_ENT")&(a.size_emp=="GE10")&(a.time=="2025")&(a.nace_r2.isin(SECT))]
def cs(ind): return sec[(sec.indic_is==ind)].merge(ex,left_on="nace_r2",right_on="nace")
for ind,nm in (("E_AI_TPVSG","picture/video/audio generation"),("E_AI_TNLG","text generation"),("E_AI_TIR","image recognition")):
    d=cs(ind); eu_=d[d.geo=="EU27_2020"]; print(f"{nm}: EU27 across {len(eu_)} sectors, corr(adoption, creation exposure) = {eu_.v.corr(eu_.E):.2f}, Spearman = {eu_.v.rank().corr(eu_.E.rank()):.2f}")
# country-sector cells with country FE; permutation over sector labels
def fe_slope(d,lab="zE"):
    d=d[(d.geo!="EU27_2020")&(~d.geo.isin(["EA","EA19","EA20"]))].dropna(subset=["v"]); d=d[d.v>0].copy(); d["y"]=np.log(d.v)
    d=d[d.geo.isin(d.groupby("geo").nace_r2.nunique()[lambda s:s>=8].index)]
    X=np.column_stack([d[lab].values,pd.get_dummies(d.geo).astype(float).values]); return np.linalg.lstsq(X,d.y.values,rcond=None)[0][0],len(d),d.geo.nunique()
rnd=random.Random(2); secs=list(ex.nace)
print("\nCountry-sector cells (country FE): ln adoption per 1 SD sector creation exposure, with permutation p (sector labels shuffled, 2000 draws):")
for ind,nm in (("E_AI_TPVSG","picture/video/audio generation"),("E_AI_TNLG","text generation"),("E_AI_TIR","image recognition")):
    d=cs(ind); b,n,k=fe_slope(d); cnt=0
    for _ in range(2000):
        p=secs[:]; rnd.shuffle(p); m=dict(zip(secs,[float(ex.set_index("nace").zE[x]) for x in p])); dd=d.copy(); dd["zE"]=dd.nace_r2.map(m); cnt+=abs(fe_slope(dd)[0])>=abs(b)
    print(f"  {nm:34s} b = {b:+.3f}  (N={n}, countries={k}), permutation p = {(cnt+1)/2001:.3f}")
# country-level: do barrier citation shares predict adoption?
bc=s_[(s_.time=="2025")&(s_.nace_r2=="C10-S951_X_K")&(s_.size_emp=="GE10")&(s_.unit=="PC_ENT_AI_EC")&s_.indic_is.isin(["E_AI_BLEG","E_AI_BCDP","E_AI_BLE","E_AI_BCST"])].pivot(index="geo",columns="indic_is",values="v")
ad=s_[(s_.time=="2025")&(s_.nace_r2=="C10-S951_X_K")&(s_.size_emp=="GE10")&(s_.unit=="PC_ENT")&(s_.indic_is=="E_AI_TPVSG")].set_index("geo").v.rename("tpvsg")
cc=bc.join(ad,how="inner").dropna(); cc=cc[~cc.index.isin(["EU27_2020","EA","EA19","EA20"])]
print(f"\nAcross {len(cc)} countries (2025): corr of picture/video/audio-generation adoption with share of considerers citing:")
for k in ("E_AI_BLEG","E_AI_BCDP","E_AI_BLE","E_AI_BCST"): print(f"  {B[k]:28s} Pearson {cc.tpvsg.corr(cc[k]):+.2f}  Spearman {cc.tpvsg.rank().corr(cc[k].rank()):+.2f}")
cc.to_csv("data/eurostat/country_barriers_adoption_2025.csv"); ex.to_csv("data/eurostat/sector_creation_exposure.csv",index=False)
