"""UK ONS/Textkernel online job adverts (snapshot stock, monthly Jan 2017-Dec 2022) by ~4,400 occupation titles.
Treated groups fixed a priori from title names only (before looking at outcomes):
 PROD  = visual-content production titles (graphic/visual/advertising design, illustration, photography, retouching, video/film editing, animation, 3D/multimedia design)
 DIRECT= creative direction/producing titles (art director, audio-visual producer, multimedia producer)  [higher quality threshold: H2 contrast]
 TEXT  = text-production titles (copywriter, journalist, editor, author...)  [separates image from text channel]
Statistic: difference-in-YoY-growth: [ln A(2022H2)-ln A(2021H2)] - [ln A(2022H1)-ln A(2021H1)], i.e. growth in YoY growth after mid-2022
 (Midjourney/DALL-E 2 beta ~Jul 2022, Stable Diffusion Aug 2022, ChatGPT Nov 2022; dates to be verified).
Inference: randomization - draw random title sets of equal size from the control pool (10,000 draws)."""
import csv, re, random, numpy as np, pandas as pd
r=pd.read_csv("data/ons/ons_total_uk_most_detailed.csv")
mcols=[c for c in r.columns if re.match(r"[A-Z][a-z]{2} \d\d$",c)]
for c in mcols: r[c]=pd.to_numeric(r[c],errors="coerce")
PROD=["Graphic Designer","Illustrator","Visual Designer","Advertising Designer","Advertising Artist","Commercial Artist","Cartoonist/Comic Artist","Photographer","Fashion Photographer","Portrait Photographer","Retoucher","Video Editor","Film Editor","Digital Video Editor","Multimedia Editor","Animator","3D Designer","Multimedia Designer","Digital Media Designer"]
DIRECT=["Art Director","Art Director Advertising","Audio Visual Producer","Multimedia Producer"]
TEXT=["Copywriter","Journalist","Author","Editor","Editor Books","Editorial Assistant","Medical Writer","Columnist","Freelance Journalist","Business Journalist","Biographer","Assistant Journalist","Chief Editor","Editor in Chief","Newsmagazine Editor","National Newspaper Editor","Foreign Correspondent","Home Affairs Journalist"]
r=r.drop_duplicates("most_detailed").set_index("most_detailed")
def avg(y,h): 
    cols=[f"{m} {y%100:02d}" for m in (["Jan","Feb","Mar","Apr","May","Jun"] if h==1 else ["Jul","Aug","Sep","Oct","Nov","Dec"])]; return r[cols].mean(axis=1,skipna=False)
def dyoy(y):  # growth in YoY growth, year y
    return (np.log(avg(y,2))-np.log(avg(y-1,2)))-(np.log(avg(y,1))-np.log(avg(y-1,1)))
vol=r[[f"{m} 21" for m in ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")]].mean(axis=1)
ok=(vol>=100)&np.isfinite(dyoy(2022))&np.isfinite(dyoy(2019))
groups={"PROD":PROD,"DIRECT":DIRECT,"TEXT":TEXT}
for g,l in groups.items():
    have=[t for t in l if t in r.index and ok.get(t,False)]
    print(f"{g}: {len(have)}/{len(l)} titles pass volume filter (>=100 avg ads in 2021); mean 2021 ads {vol[have].mean():.0f}; dropped: {[t for t in l if t not in have]}")
excl=set(PROD)|set(DIRECT)|set(TEXT)
pool=[t for t in r.index if ok.get(t,False) and t not in excl]
white=set(r[r.summary.isin(["Information and Communication Technology","Communication, Marketing and Public Relations","Insurance and Finance","Management, Policy and Governance","Legal, Human Resources and Social Services","Administration and Customer Service","Engineering"])].index)
poolW=[t for t in pool if t in white]
print(f"control pools: all other titles n={len(pool)}, white-collar n={len(poolW)}")
rng=random.Random(11)
def test(group,pl,yr=2022,R=10000):
    d=dyoy(yr); have=[t for t in groups[group] if t in r.index and ok.get(t,False)]
    obs=d[have].mean()-d[pl].mean(); k=len(have); dd=d[pl].values; cnt=0
    for _ in range(R):
        smp=rng.sample(range(len(pl)),k); cnt+=abs(dd[smp].mean()-dd.mean())>=abs(obs)
    return obs,(cnt+1)/(R+1),len(have)
print("\nStatistic: growth in YoY growth after mid-2022 (2022H2-vs-2021H2 minus 2022H1-vs-2021H1), group minus controls [placebo = same for 2019]")
print("group".ljust(8),"pool".ljust(12),"2022 est (RI p)".rjust(18),"placebo 2019 est (RI p)".rjust(26))
for g in ("PROD","DIRECT","TEXT"):
    for nm,pl in (("all",pool),("white-collar",poolW)):
        o,p,k=test(g,pl,2022); o0,p0,_=test(g,pl,2019); print(g.ljust(8),nm.ljust(12),f"{o:+.3f} ({p:.3f}) n={k}".rjust(18),f"{o0:+.3f} ({p0:.3f})".rjust(26))
# contrasts within creative
d=dyoy(2022); P=[t for t in PROD if ok.get(t,False)]; D=[t for t in DIRECT if ok.get(t,False)]; T=[t for t in TEXT if ok.get(t,False)]
print(f"\nPROD minus DIRECT: {d[P].mean()-d[D].mean():+.3f}   PROD minus TEXT: {d[P].mean()-d[T].mean():+.3f}")
print("title-level 2022 values (PROD):",{t:round(float(d[t]),2) for t in P})
print("title-level 2022 values (DIRECT):",{t:round(float(d[t]),2) for t in D})
print("control distribution: median %.3f  p10 %.3f  p90 %.3f"%(d[pool].median(),d[pool].quantile(.1),d[pool].quantile(.9)))
# monthly YoY path: treated minus control, 2021-01..2022-12
mons=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
rows=[]
for y in (2021,2022):
    for m in mons:
        a=np.log(r[f"{m} {y%100:02d}"])-np.log(r[f"{m} {(y-1)%100:02d}"])
        rows.append((f"{y}-{m}",a[P].mean()-a[pool].mean(),a[T].mean()-a[pool].mean(),a[D].mean()-a[pool].mean()))
path=pd.DataFrame(rows,columns=["month","PROD_minus_ctrl_yoy","TEXT_minus_ctrl_yoy","DIRECT_minus_ctrl_yoy"]); path.to_csv("data/ons/uk_yoy_path.csv",index=False); print(path.round(3).to_string(index=False))
