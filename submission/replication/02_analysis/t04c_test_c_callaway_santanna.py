"""Table 4, Test C and Figure 1: staggered launch of Google AI Overviews, Callaway-Sant'Anna (2021) group-time ATTs
with not-yet-treated controls, 25 Wikipedia editions, bootstrap over editions (499 draws, seed 7).
Usage: python t04c_test_c_callaway_santanna.py <platform: all|desktop|mobile> [comma-separated editions to exclude]
Environment variables: EMIN, EMAX (event window, default -12..12), ONLYG (restrict to one cohort, e.g. 2024-09).
The specifications reported in the paper are listed in run_t04c.sh.
Cohorts (first full month with AI Overviews in the edition's language/main market), G below; editions in languages
added on 2025-05-20 are not-yet-treated controls censored from 2025-05 (CENS); Persian is never treated.
Inputs: data/raw/wiki_hours.csv, data/raw/wiki_hours_extra.csv. Outputs: output/cs_es_<platform>[_excl].csv, output/cs_gt_<platform>.csv
Runtime: roughly 3-10 minutes per specification (bootstrap)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, sys
rng=np.random.default_rng(7)
import os
EMIN=int(os.environ.get("EMIN",-12)); EMAX=int(os.environ.get("EMAX",12)); ONLYG=os.environ.get("ONLYG","")
w=pd.concat([pd.read_csv(RAW/"wiki_hours.csv"),pd.read_csv(RAW/"wiki_hours_extra.csv")])
w["month"]=pd.to_datetime(w.stamp.str[:6],format="%Y%m")
PLAT=sys.argv[1] if len(sys.argv)>1 else "all"
if PLAT!="all": w=w[w.platform==PLAT]
g=w.groupby(["lang","month","stamp"]).views.sum().reset_index().groupby(["lang","month"]).views.mean().reset_index()
g["y"]=np.log(g.views)
M=lambda s: pd.Period(s,"M")
G={"en":"2024-06","ja":"2024-09","id":"2024-09","pt":"2024-09","es":"2024-09","hi":"2024-09","de":"2025-04","it":"2025-04","pl":"2025-04","fr":"2026-08"}
CENS={l:"2025-05" for l in ["ko","nl","sv","cs","tr","vi","th","he","ar","zh","uk","ru","ms","bn"]}
NEVER=["fa"]
EXCL=set(sys.argv[2].split(",")) if len(sys.argv)>2 and sys.argv[2] else set()
g["p"]=g.month.dt.to_period("M")
units=[u for u in list(G)+list(CENS)+NEVER if u in set(g.lang) and u not in EXCL]
Y=g.pivot(index="p",columns="lang",values="y")[units]
cohort={u:(M(G[u]) if u in G else None) for u in units}
cens={u:(M(CENS[u]) if u in CENS else None) for u in units}
def att_gt(Y,units):
    res=[]
    for gr in sorted(set(c for c in cohort.values() if c is not None)):
        tr=[u for u in units if cohort[u]==gr]
        if not tr: continue
        base=gr-1
        for t in Y.index:
            e=(t-gr).n
            if e<EMIN or e>EMAX: continue
            if ONLYG and str(gr)!=ONLYG: continue
            ctrl=[u for u in units if (cohort[u] is None or cohort[u]>max(t,base)) and (cens[u] is None or cens[u]>max(t,base))]
            if len(ctrl)<2 or base not in Y.index: continue
            dt=(Y.loc[t,tr]-Y.loc[base,tr]).mean(); dc=(Y.loc[t,ctrl]-Y.loc[base,ctrl]).mean()
            if np.isnan(dt) or np.isnan(dc): continue
            res.append((gr,t,e,len(tr),dt-dc,len(ctrl)))
    return pd.DataFrame(res,columns=["g","t","e","n","att","nctrl"])
def agg(r):
    es=r.groupby("e").apply(lambda d: np.average(d.att,weights=d.n),include_groups=False)
    post=r[r.e>=0]; overall=np.average(post.att,weights=post.n)
    pre=r[(r.e<-1)]
    pre=pre if len(pre) else r; pre_avg=np.average(pre.att,weights=pre.n)
    return es,overall,pre_avg
r=att_gt(Y,units); es,ov,pre=agg(r)
B=[]
for b in range(499):
    s=list(rng.choice(units,len(units),replace=True))
    # rebuild with duplicated units
    Yb=pd.concat({f"{u}#{i}":Y[u] for i,u in enumerate(s)},axis=1)
    cb={f"{u}#{i}":cohort[u] for i,u in enumerate(s)}; ce={f"{u}#{i}":cens[u] for i,u in enumerate(s)}
    co0,ce0=cohort.copy(),cens.copy(); cohort.update(cb); cens.update(ce)
    try:
        rb=att_gt(Yb,list(Yb.columns)); esb,ovb,preb=agg(rb); B.append((ovb,preb,esb))
    except Exception: pass
    cohort.clear(); cohort.update(co0); cens.clear(); cens.update(ce0)
ovs=np.array([x[0] for x in B]); pres=np.array([x[1] for x in B])
ESB=pd.DataFrame([x[2] for x in B])
se=ESB.std()
out=pd.DataFrame({"att":es,"se":se.reindex(es.index)})
print(f"[{PLAT}] excl={EXCL or '-'} units={len(units)} overall ATT (e>=0) = {ov:.4f}  SE {ovs.std():.4f}  95%CI [{np.percentile(ovs,2.5):.4f},{np.percentile(ovs,97.5):.4f}]  pre-period avg = {pre:.4f} SE {pres.std():.4f}")
print(out.round(4).T.to_string())
out.to_csv(OUT/f"cs_es_{PLAT}{'_'+'_'.join(sorted(EXCL)) if EXCL else ''}.csv")
r.to_csv(OUT/f"cs_gt_{PLAT}.csv",index=False)
print(r.groupby("g").apply(lambda d: pd.Series({"n":d.n.iloc[0],"att_post":d[d.e>=0].att.mean(),"att_pre":d[d.e<-1].att.mean(),"nctrl_min":d.nctrl.min()}),include_groups=False).round(4))
