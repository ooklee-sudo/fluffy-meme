import re,numpy as np,pandas as pd
exec(open("analysis_hf.py").read().split("def load(n):")[0])
def load(n):
    b=pd.read_csv(f"raw/{n}_1h.csv").sort_values("t").reset_index(drop=True); b["r2"]=100*np.log(b.close.shift(-1)/b.open); b["cont"]=(b.t.shift(-1)-b.t)==3600; b.loc[~b.cont,"r2"]=np.nan
    b["pre2"]=100*np.log(b.close.shift(1)/b.open.shift(2)); b["cont_pre"]=(b.t-b.t.shift(2))==7200; b.loc[~b.cont_pre,"pre2"]=np.nan; return b
for n in["CL","SPX"]:
    b=load(n)
    for typ in["N","P"]:
        rows=[]
        for ep in ev[ev.typ==typ].ep.values:
            k=np.searchsorted(b.t.values,ep,side="right")-1
            if k<2 or ep>=b.t.values[k]+3600: continue
            rows.append((b.pre2.iloc[k],b.r2.iloc[k]))
        a=np.array(rows); a=a[~np.isnan(a).any(axis=1)]
        print(n,typ,"n=%d  pre-post move (2h before the bar) mean=%+.2f | reaction mean=%+.2f | corr(pre,post)=%+.2f | share pre>0=%.2f"%(len(a),a[:,0].mean(),a[:,1].mean(),np.corrcoef(a[:,0],a[:,1])[0,1],(a[:,0]>0).mean()))
# sample of N posts with oil reaction
b=load("CL"); samp=ev[ev.typ=="N"].copy(); samp["oil"]=[b.r2.iloc[max(0,np.searchsorted(b.t.values,e,side='right')-1)] for e in samp.ep]
big=samp.reindex(samp.oil.abs().sort_values(ascending=False).index).head(8)
for _,r in big.iterrows(): print(r.t.strftime("%m-%d %H:%MZ"),"oil %+.1f"%r.oil,"|",re.sub(r"\s+"," ",d.loc[r.name,"content"] if r.name in d.index else "")[:170])
