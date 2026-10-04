"""Exploratory event study: Indeed US postings by sector (total postings, SA, Feb-2020=100).
Treated (fixed a priori): Arts & Entertainment, Media & Communications, Marketing.  Outcome: ln(index), monthly mean.
Base window 2022-01..03 (before DALL-E 2 / Midjourney / Stable Diffusion / ChatGPT).  Inference: randomization over all
possible sets of 3 'treated' sectors among the 47 (exact, 16,215 triples)."""
import csv, itertools, collections, numpy as np, pandas as pd
r=[x for x in csv.DictReader(open("data/indeed/job_postings_by_sector_US.csv")) if x["variable"]=="total postings"]
df=pd.DataFrame(r); df["v"]=df.indeed_job_postings_index.astype(float); df["m"]=df.date.str[:7]
M=df.groupby(["display_name","m"]).v.mean().unstack(0); L=np.log(M)
TREAT=["Arts & Entertainment","Media & Communications","Marketing"]; TECH=["Software Development","IT Infrastructure, Operations & Support","IT Systems & Solutions","Data & Analytics"]
def win(a,b): return L.loc[a:b].mean()
base=win("2022-01","2022-03")
W={"W1 2022-10..2023-03 (after image-gen + ChatGPT)":("2022-10","2023-03"),"W2 2023-10..2024-03 (DALL-E 3, pre-video)":("2023-10","2024-03"),"W3 2024-10..2025-03 (after video-gen)":("2024-10","2025-03"),"W4 2025-10..2026-03":("2025-10","2026-03")}
pre=win("2022-01","2022-03")-win("2021-01","2021-03")
sectors=list(L.columns); n=len(sectors)
def stat(delta,treated,controls): return delta[treated].mean()-delta[controls].mean()
def ri(delta,controls_pool):
    t=[s for s in TREAT]; obs=stat(delta,t,[s for s in controls_pool if s not in t])
    cnt=tot=0
    for tri in itertools.combinations(controls_pool+t,3):
        c=[s for s in controls_pool+t if s not in tri]; tot+=1; cnt+=abs(stat(delta,list(tri),c))>=abs(obs)
    return obs,cnt/tot
pool_all=[s for s in sectors if s not in TREAT]; pool_notech=[s for s in pool_all if s not in TECH]
print("PRE-TREND (2021Q1 -> 2022Q1 ln change): treated minus controls = %.3f  (RI p=%.3f)"%ri(pre,pool_all)[0:2] if False else "")
o,p=ri(pre,pool_all); print(f"PRE-TREND ln change 2021Q1->2022Q1, treated minus other sectors: {o:+.3f} (randomization p={p:.3f})")
print("\nln change vs 2022Q1 base: treated avg minus control avg; randomization p over all triples\n")
print("window".ljust(48),"all controls".rjust(22),"excl. IT/data controls".rjust(26))
out=[]
for k,(a,b) in W.items():
    d=win(a,b)-base
    o1,p1=ri(d,pool_all); o2,p2=ri(d,pool_notech)
    print(k.ljust(48),f"{o1:+.3f} (p={p1:.3f})".rjust(22),f"{o2:+.3f} (p={p2:.3f})".rjust(26)); out.append((k,o1,p1,o2,p2))
print("\nSector ranks of ln change (W3) among",n,"sectors (1 = largest fall):")
d3=(win("2024-10","2025-03")-base).sort_values()
for s in TREAT+TECH: print(f"  {s.ljust(40)} change {d3[s]:+.3f}  rank {list(d3.index).index(s)+1}/{n}")
print("  sector median change: %+.3f"%d3.median())
pd.DataFrame(out,columns=["window","diff_all","p_all","diff_excl_tech","p_excl_tech"]).to_csv("data/indeed/event_study_summary.csv",index=False)
# event-study path (quarterly): treated minus controls, relative to base
q=(L.sub(base,axis=1)); path=pd.DataFrame({"treated":q[TREAT].mean(axis=1),"controls":q[pool_all].mean(axis=1),"controls_excl_tech":q[pool_notech].mean(axis=1)})
path["gap"]=path.treated-path.controls; path["gap_excl_tech"]=path.treated-path.controls_excl_tech; path.to_csv("data/indeed/event_study_path.csv")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8,4)); x=pd.to_datetime(path.index+"-01")
ax.plot(x,path.gap,label="vs all other sectors",color="#1f77b4"); ax.plot(x,path.gap_excl_tech,label="vs other sectors excl. IT/data",color="#d62728")
for d,lab in (("2022-07-01","DALL-E 2 beta / SD"),("2022-11-30","ChatGPT"),("2023-10-01","DALL-E 3"),("2024-12-01","Sora release")): ax.axvline(pd.Timestamp(d),color="gray",ls=":",lw=1)
ax.axhline(0,color="black",lw=.6); ax.set_ylabel("ln gap in postings index,\ntreated minus controls (base 2022Q1)"); ax.legend(frameon=False); ax.set_title("Creative sectors vs others: Indeed US postings (exploratory)",fontsize=10)
plt.tight_layout(); plt.savefig("data/indeed/event_study_gap.png",dpi=130)
