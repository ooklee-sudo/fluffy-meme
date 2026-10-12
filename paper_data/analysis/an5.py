import pandas as pd, numpy as np, re, json, statsmodels.api as sm, warnings
warnings.filterwarnings('ignore')
rng=np.random.default_rng(5)
D='x/data/'
w=pd.read_csv(D+'weekly.csv',parse_dates=['week']).sort_values(['repo','week']).reset_index(drop=True)
r=pd.read_csv(D+'releases.csv',parse_dates=['published_at']).sort_values(['repo','published_at']).reset_index(drop=True)
# ---- (1) hot-fix: version-only (same tag prefix, same major.minor, patch increases), no 7-day condition
def parse(t):
    m=re.search(r'^(.*?)v?(\d+)\.(\d+)(?:\.(\d+))?',t)
    return (m.group(1),int(m.group(2)),int(m.group(3)),int(m.group(4) or 0)) if m else None
r['v']=r.tag.map(parse);vo=[];gap=[]
for repo,g in r.groupby('repo'):
    prev=None
    for i,row in g.iterrows():
        f=False;gp=np.nan
        if prev is not None and row.v and prev[0]:
            same=row.v[0]==prev[0][0] and row.v[1:3]==prev[0][1:3] and row.v[3]>prev[0][3]
            f=same;gp=(row.published_at-prev[1]).days
        vo.append((i,f,gp));prev=(row.v,row.published_at)
V=pd.DataFrame(vo,columns=['i','vonly','gap']).set_index('i');r['vonly']=V.vonly;r['gap']=V.gap
out={'n_all':len(r),'share_version_only':round(float(r.vonly.mean()),3)}
pv=r[r.vonly]
out['patch_only_gap_days_quantiles']=pv.gap.quantile([.25,.5,.75,.9]).round(1).to_dict()
out['share_patch_only_within7']=round(float((pv.gap<=7).mean()),3)
# among version-only (patch) releases, hazard by age of previous release in weeks
pv=pv.assign(gw=(pv.gap//7).clip(upper=8))
out['patch_only_by_gap_week']=pv.groupby('gw').size().to_dict()
# share of patch-only among all releases by gap week bucket (all releases with parsable prev)
al=r[r.gap.notna()].assign(gw=lambda d:(d.gap//7).clip(upper=8))
out['patch_only_share_by_gap_week']=al.groupby('gw').vonly.mean().round(3).to_dict()
out['n_by_gap_week']=al.groupby('gw').size().to_dict()
# ---- (2) wild cluster score bootstrap for RQ3 (Webb weights, 19 clusters)
g=w.groupby('repo')
w['a']=g.age.shift(1)+1;w['lb']=np.log1p(w.bugs);w['li']=np.log1p(w.issues);w['share']=np.where(w.issues>0,w.bugs/w.issues.clip(lower=1),np.nan)
for c in ['lb','li','share']: w[c+'_z']=g[c].transform(lambda s:(s-s.mean())/s.std())
for k in (1,2,3): w[f'lb{k}']=w.groupby('repo').lb_z.shift(k)
w['li1']=w.groupby('repo').li_z.shift(1);w['sh1']=w.groupby('repo').share_z.shift(1);w['bug_ma']=w[['lb1','lb2','lb3']].mean(axis=1);w['t']=w.groupby('repo').cumcount()/52.
h=w.dropna(subset=['a','lb1','lb2','lb3','li1','sh1']).copy();h['a']=h.a.clip(upper=8)
cl=pd.factorize(h.repo)[0];G=cl.max()+1
webb=np.array([-np.sqrt(1.5),-1,-np.sqrt(.5),np.sqrt(.5),1,np.sqrt(1.5)])
def wcb(df,test,controls,B=9999):
    X=pd.concat([df[[test]+controls],pd.get_dummies(df.repo,drop_first=True,dtype=float)],axis=1);X=sm.add_constant(X).astype(float)
    y=df.release.values.astype(float);Xn=X.drop(columns=[test]).values
    m0=sm.Logit(y,Xn).fit(disp=0);p0=m0.predict(Xn)
    full=sm.Logit(y,X.values).fit(disp=0,cov_type='cluster',cov_kwds={'groups':cl})
    j=list(X.columns).index(test);t_obs=float(full.params[j]/full.bse[j])
    Xf=X.values;res=y-p0;wt=p0*(1-p0)
    Hf=(Xf*wt[:,None]).T@Xf;Hinv=np.linalg.inv(Hf)
    # per-cluster scores, one-step Newton for coefficient j
    S=np.zeros((G,Xf.shape[1]))
    for gi in range(G):
        m=cl==gi;S[gi]=(Xf[m]*res[m][:,None]).sum(0)
    # efficient influence of coefficient j: row j of Hinv times scores
    infl=S@Hinv[j]
    tstar=[]
    for _ in range(B):
        wg=webb[rng.integers(0,6,G)];d=(wg*infl)
        # bootstrap t using restricted-score variance
        tstar.append(d.sum()/np.sqrt((d**2).sum()))
    t0=infl.sum()/np.sqrt((infl**2).sum())
    pv=float((np.abs(tstar)>=abs(t0)).mean())
    return dict(coef=round(float(full.params[j]),3),se=round(float(full.bse[j]),3),p_cluster=round(float(full.pvalues[j]),3),p_wcb=round(pv,3))
out['wcb_lb1']=wcb(h,'lb1',['li1','a','t'])
out['wcb_li1_in_A']=wcb(h,'li1',['lb1','a','t'])
out['wcb_bugMA']=wcb(h,'bug_ma',['li1','a','t'])
out['wcb_lb1_given_lag23']=wcb(h,'lb1',['lb2','lb3','li1','a','t'])
print(len(h));json.dump(out,open('out5.json','w'),indent=1,default=str);print(json.dumps(out,indent=1,default=str))
