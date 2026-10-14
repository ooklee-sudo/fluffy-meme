import json,numpy as np,pandas as pd,statsmodels.api as sm
exec(open("analysis_hf2.py").read().split("ES=sig.ep.values")[0])   # gives ev (clustered coded posts) with ep, cls
# Korean sessions: trading dates from Korean index prices
P=pd.read_csv("../airlines/raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
S=pd.read_csv("../semis/raw/prices.csv",index_col=0,parse_dates=True); S=S.groupby(level=0).last()
for c in["^SOX","005930.KS","000660.KS"]: P[c]=S[c]
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})
kr=R["^KS11"].dropna().loc["2026-03-02":].index
def close_ts(dt): return int((pd.Timestamp(dt,tz="UTC")+pd.Timedelta(hours=6,minutes=30)).timestamp())
cl=pd.read_csv("raw/CL_1h.csv").sort_values("t").reset_index(drop=True)
# price at time T = close of the last bar with start+3600 <= T
def px(T):
    k=np.searchsorted(cl.t.values+3600,T,side="right")-1
    return cl.close.iloc[k] if k>=0 and T-(cl.t.values[k]+3600)<4*3600 else np.nan
kr_list=list(R["^KS11"].dropna().index); rows=[]
for i,d in enumerate(kr_list):
    if d<pd.Timestamp("2026-03-02"): continue
    prev=kr_list[i-1]; t0=close_ts(prev); t1=close_ts(d)
    p0,p1=px(t0),px(t1); w=100*np.log(p1/p0) if p0==p0 and p1==p1 else np.nan
    inw=ev[(ev.ep>t0)&(ev.ep<=t1)]
    rows.append(dict(date=d,dwti=w,ZD=int((inw.cls=="DEESC").any()),ZE=int((inw.cls=="ESC").any()),nD=int((inw.cls=="DEESC").sum()),nE=int((inw.cls=="ESC").sum())))
W=pd.DataFrame(rows).set_index("date")
def prev_us(ser,idx): ser=ser.dropna(); v=ser.index.values; k=np.searchsorted(v,idx.values,side="left")-1; return pd.Series(np.where(k>=0,ser.values[np.clip(k,0,None)],np.nan),index=idx)
W["sp"]=prev_us(R["^GSPC"],W.index); W["sox"]=prev_us(R["^SOX"],W.index); W["chip"]=((R["005930.KS"]+R["000660.KS"])/2).reindex(W.index)
for c,n in[("003490.KS","KoreanAir"),("272450.KS","JinAir"),("089590.KS","JejuAir"),("^KS11","KOSPI")]: W[n]=R[c].reindex(W.index)
W=W.dropna(subset=["dwti","sp","sox","chip"]); print("sessions",len(W),"with DEESC:",int(W.ZD.sum()),"ESC:",int(W.ZE.sum()),"both:",int(((W.ZD==1)&(W.ZE==1)).sum()))
def ols(y,X,data): return sm.OLS(data[y],sm.add_constant(data[X])).fit(cov_type="HC1")
res={}
ctrl=["sp","sox","chip"]
fs=ols("dwti",["ZD","ZE","sp","sox"],W); res["first_stage_dwti"]={"pi_ZD":float(fs.params["ZD"]),"se":float(fs.bse["ZD"]),"p":float(fs.pvalues["ZD"]),"F_ZD":float((fs.params["ZD"]/fs.bse["ZD"])**2),"delta_ZE":float(fs.params["ZE"]),"p_ZE":float(fs.pvalues["ZE"]),"mean_dwti_ZD1":float(W[W.ZD==1].dwti.mean()),"mean_dwti_none":float(W[(W.ZD==0)&(W.ZE==0)].dwti.mean()),"n":int(fs.nobs)}
for y in["KoreanAir","JinAir","JejuAir","KOSPI"]:
    X=["ZD","ZE","sp","sox","chip"]; rf=ols(y,X,W)
    # 2SLS manual (just-identified with ZD; ZE as exogenous control)
    d1=sm.add_constant(W[["ZD","ZE","sp","sox","chip"]]); fsd=sm.OLS(W.dwti,d1).fit(); W["dwti_hat"]=fsd.fittedvalues
    t=sm.OLS(W[y],sm.add_constant(W[["dwti_hat","ZE","sp","sox","chip"]])).fit()
    # correct SEs: use residuals with actual dwti
    Xa=sm.add_constant(W[["dwti","ZE","sp","sox","chip"]]).values; Xh=sm.add_constant(W[["dwti_hat","ZE","sp","sox","chip"]]).values
    b=np.linalg.solve(Xh.T@Xa,Xh.T@W[y].values); u=W[y].values-Xa@b; Ainv=np.linalg.inv(Xh.T@Xa); meat=(Xh*u[:,None]).T@(Xh*u[:,None]); V=Ainv@meat@Ainv.T*len(W)/(len(W)-Xa.shape[1])
    se=np.sqrt(np.diag(V)); 
    res[y]={"reduced_form_ZD":{"coef":float(rf.params["ZD"]),"se":float(rf.bse["ZD"]),"p":float(rf.pvalues["ZD"])},"reduced_form_ZE":{"coef":float(rf.params["ZE"]),"p":float(rf.pvalues["ZE"])},"2SLS_dwti":{"coef":float(b[1]),"se":float(se[1]),"p":float(2*(1-__import__('scipy').stats.norm.cdf(abs(b[1]/se[1]))))},"OLS_dwti":{"coef":float(ols(y,["dwti","sp","sox","chip"],W).params["dwti"]),"p":float(ols(y,["dwti","sp","sox","chip"],W).pvalues["dwti"])}}
# placebo: chip factor outcome without chip control
rfc=ols("chip",["ZD","ZE","sp","sox"],W); res["chip_placebo"]={"ZD":float(rfc.params["ZD"]),"se":float(rfc.bse["ZD"]),"p":float(rfc.pvalues["ZD"]),"ZE":float(rfc.params["ZE"]),"p_ZE":float(rfc.pvalues["ZE"])}
json.dump(res,open("results_iv.json","w"),indent=1); W.to_csv("iv_sessions.csv")
print(json.dumps(res["first_stage_dwti"],indent=1))
for y in["KoreanAir","JinAir","JejuAir","KOSPI"]:
    v=res[y]; print(y,"RF ZD %+.2f (p=%.2f) | RF ZE %+.2f (p=%.2f) | 2SLS %+.3f (se %.3f, p=%.2f) | OLS %+.3f (p=%.2f)"%(v["reduced_form_ZD"]["coef"],v["reduced_form_ZD"]["p"],v["reduced_form_ZE"]["coef"],v["reduced_form_ZE"]["p"],v["2SLS_dwti"]["coef"],v["2SLS_dwti"]["se"],v["2SLS_dwti"]["p"],v["OLS_dwti"]["coef"],v["OLS_dwti"]["p"]))
print("chip placebo",res["chip_placebo"])
