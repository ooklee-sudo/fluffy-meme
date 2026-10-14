import re,json,numpy as np,pandas as pd,statsmodels.api as sm
# signals (same definitions as analysis_poisson.py)
d=pd.read_csv("raw/truth_archive.csv"); d["t"]=pd.to_datetime(d.created_at,utc=True); d=d[(d.t>="2026-03-01")&(d.t<"2026-10-14")].copy(); d["c"]=d.content.fillna("").str.lower()
d=d[~d.c.str.fullmatch(r"\s*rt:?\s*https?://\S+\s*")]
IR=re.compile(r"\biran"); TH=re.compile(r"attack|strik|bomb|destroy|obliterat|annihilat|wipe[sd]? out|blow(n)? up|kill|ultimatum|very hard"); MO=re.compile(r"\bwill\b|\bwould\b|going to|\bif |unless|or else|tonight|\bsoon\b|\bnext\b")
d["S1"]=d.c.apply(lambda s:bool(IR.search(s)) and bool(TH.search(s))); d["S2"]=d.S1&d.c.apply(lambda s:bool(MO.search(s)))
d["day"]=d.t.dt.tz_convert(None).dt.normalize()
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); R=np.log(P).diff()*100
S=["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","AVGO"]; est=R.loc["2025-03-03":"2026-01-30"]
ab=pd.DataFrame({s:R[s]-(np.polyfit(est["^GSPC"],est[s],1)[1]+np.polyfit(est["^GSPC"],est[s],1)[0]*R["^GSPC"]) for s in S}).mean(axis=1)
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]
dd=pd.DataFrame({"S1":d.groupby("day").S1.sum(),"S2":d.groupby("day").S2.sum()}).reindex(pd.date_range("2026-03-01","2026-10-13"),fill_value=0)
# daily frame on trading days
T=pd.DataFrame({"gspc":R["^GSPC"],"ixic":R["^IXIC"],"tech":R[S].mean(axis=1),"techAR":ab}); T["wti"]=np.log(oil).diff().reindex(T.index)*100
T=T.loc["2026-03-02":]
# weekly: Friday-to-Friday (sum of daily log returns over Mon..Fri), signals Mon..Sun of same week
T["wk"]=T.index.to_period("W-SUN"); W=T.groupby("wk")[["gspc","ixic","tech","techAR","wti"]].sum(min_count=3)
sig=dd.copy(); sig["wk"]=sig.index.to_period("W-SUN"); Ws=sig.groupby("wk")[["S1","S2"]].sum(); W=W.join(Ws).dropna(); W=W.iloc[:32]
print("weeks",len(W),W.index.min(),W.index.max())
res={}
def ols(y,x,lags,data):
    X=sm.add_constant(data[x]); m=sm.OLS(data[y],X).fit(cov_type="HAC",cov_kwds={"maxlags":lags}); return dict(b=float(m.params[x]),se=float(m.bse[x]),p=float(m.pvalues[x]),n=int(m.nobs))
rng=np.random.default_rng(5)
for sg in["S1","S2"]:
    for y in["wti","gspc","ixic","tech","techAR"]:
        res[f"weekly {sg} -> {y}"]=ols(y,sg,2,W)
        L=W.copy(); L["lag"]=L[sg].shift(1); L=L.dropna(); res[f"weekly lag {sg} -> {y}"]=ols(y,"lag",2,L)
hi=(W.S1>=W.S1.quantile(.75)); 
for y in["wti","gspc","ixic","tech","techAR"]:
    diff=W.loc[hi,y].mean()-W.loc[~hi,y].mean(); sim=[]
    for _ in range(5000):
        h=rng.permutation(hi.values); sim.append(W.loc[h,y].mean()-W.loc[~h,y].mean())
    res[f"high-signal weeks (top quartile) {y}"]=dict(diff=float(diff),n_high=int(hi.sum()),p_perm=float(np.mean(np.abs(sim)>=abs(diff))))
D=T.join(dd).dropna(subset=["gspc"])
for sg in["S1"]:
    for y in["wti","gspc","ixic","tech","techAR"]:
        Dd=D.dropna(subset=[y]); res[f"daily {sg} -> {y}"]=ols(y,sg,5,Dd)
json.dump(res,open("results_markets.json","w"),indent=1)
print(W.assign(S1=W.S1).round(2).head(12).to_string())
for k,v in res.items():
    print("%-44s %s"%(k,"b=%+.3f se=%.3f p=%.3f n=%d"%(v["b"],v["se"],v["p"],v["n"]) if "b" in v else "diff=%+.3f n_high=%d perm p=%.3f"%(v["diff"],v["n_high"],v["p_perm"])))
