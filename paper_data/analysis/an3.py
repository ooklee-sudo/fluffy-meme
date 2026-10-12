import pandas as pd, numpy as np, statsmodels.api as sm, json, re, warnings
from scipy import optimize
warnings.filterwarnings('ignore')
rng=np.random.default_rng(11)
D='x/data/'
T=pd.read_csv('table1.csv')
def dl(b,se):
    b=np.array(b);se=np.array(se);wi=1/se**2;m=(wi*b).sum()/wi.sum();Q=(wi*(b-m)**2).sum();k=len(b)
    t2=max(0,(Q-(k-1))/(wi.sum()-(wi**2).sum()/wi.sum()));ws=1/(se**2+t2);mu=(ws*b).sum()/ws.sum();s=ws.sum()**-.5
    return dict(b=round(mu,4),lo=round(mu-1.96*s,4),hi=round(mu+1.96*s,4),tau2=round(t2,4),k=k)
T['weekly']=T.median_cycle<=1
out={}
out['bug']=dl(T.bug_b,T.bug_se);out['bugno']=dl(T.bugno_b,T.bugno_se)
out['bug_pos']=int((T.bug_b>0).sum());out['bug_sigpos']=T[(T.bug_b/T.bug_se>1.96)].repo.tolist();out['bug_signeg']=T[(T.bug_b/T.bug_se<-1.96)].repo.tolist()
out['bugno_signeg']=int((T.bugno_b/T.bugno_se<-1.96).sum())
out['haz']=dl(T.haz_b,T.haz_se);out['haz_pos']=int((T.haz_b>0).sum())
out['haz_sigpos']=T[T.haz_b/T.haz_se>1.96].repo.tolist();out['haz_signeg']=T[T.haz_b/T.haz_se<-1.96].repo.tolist()
out['haz_maxratio']=T.assign(z=T.haz_b/T.haz_se).sort_values('z').tail(2)[['repo','z']].values.tolist()
out['weekly_repos']=T[T.weekly].repo.tolist();out['n_weekly']=int(T.weekly.sum())
out['haz_signeg_weekly']=int(T[T.weekly&(T.haz_b/T.haz_se<-1.96)].shape[0])
nw=T[~T.weekly];out['haz_noweekly']=dl(nw.haz_b,nw.haz_se)
out['haz_noweekly_signeg']=int((nw.haz_b/nw.haz_se<-1.96).sum())
# a>=2 : require >=10 events
w=pd.read_csv(D+'weekly.csv',parse_dates=['week']).sort_values(['repo','week']).reset_index(drop=True)
w['a']=w.groupby('repo').age.shift(1)+1
h=w.dropna(subset=['a']).copy();h['a']=h.a.clip(upper=8)
ev2=h[h.a>=2].groupby('repo').release.sum();T['ev2']=T.repo.map(ev2)
t2=T[(T.ev2>=10)&(T.haz2_se<1)];out['haz2']=dl(t2.haz2_b,t2.haz2_se);out['haz2_dropped']=T[~T.index.isin(t2.index)].repo.tolist()
# ---- hot-fix classification
r=pd.read_csv(D+'releases.csv',parse_dates=['published_at']).sort_values(['repo','published_at']).reset_index(drop=True)
def ver(t):
    m=re.search(r'(\d+)\.(\d+)(?:\.(\d+))?',t); return tuple(int(x) if x else 0 for x in m.groups()) if m else None
r['v']=r.tag.map(ver);hf={}
for repo,g in r.groupby('repo'):
    prev=None
    for i,row in g.iterrows():
        f=False
        if prev is not None and row.v and prev[0]: f=(row.published_at-prev[1]).days<=7 and row.v[:2]==prev[0][:2] and row.v[2]>prev[0][2]
        hf[i]=f;prev=(row.v,row.published_at)
r['hotfix']=pd.Series(hf)
out['hotfix_share']=round(float(r.hotfix.mean()),3);out['n_releases_all']=len(r)
r['week']=r.published_at.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
reg=r[~r.hotfix].groupby(['repo','week']).size().rename('reg_rel').reset_index()
w=w.merge(reg,on=['repo','week'],how='left');w['reg']=(w.reg_rel.fillna(0)>0).astype(int)
w['hot']=0
hot=r[r.hotfix].groupby(['repo','week']).size().rename('n').reset_index();w=w.merge(hot,on=['repo','week'],how='left');w['hot']=(w.n.fillna(0)>0).astype(int)
# age since last REGULAR release
def reg_age(g):
    a=[];last=None
    for wk,rg in zip(g.week,g.reg):
        a.append(np.nan if last is None else (wk-last).days//7)
        if rg: last=wk
    return pd.Series(a,index=g.index)
w['ar']=w.groupby('repo',group_keys=False).apply(reg_age)
hr=w.dropna(subset=['ar']).copy();hr=hr[hr.ar>=1];hr['ar']=hr.ar.clip(upper=8)
hr['cyc']=hr.groupby('repo').reg.cumsum().shift(1).fillna(0)
def fit(g,col,x):
    y=g[col].values
    if y.sum()<3 or y.sum()==len(y): return np.nan
    return np.asarray(sm.Logit(y,sm.add_constant(g[[x]].values)).fit(disp=0).params)[1]
def boot(g,col,x,B=300):
    est=fit(g,col,x);cy=[c for _,c in g.groupby(g.cyc.values)];v=[]
    for _ in range(B):
        idx=rng.integers(0,len(cy),len(cy))
        try: z=fit(pd.concat([cy[i] for i in idx]),col,x)
        except Exception: continue
        if np.isfinite(z): v.append(z)
    return est,np.std(v,ddof=1)
rows=[]
for repo,g in hr.groupby('repo'):
    if g.reg.sum()<10: continue
    b,s=boot(g,'reg','ar');rows.append((repo,b,s,int(g.reg.sum())))
R=pd.DataFrame(rows,columns=['repo','b','se','ev']);R=R[R.se<1]
out['reg_hazard_age_since_regular']=dl(R.b,R.se);out['reg_haz_pos']=int((R.b>0).sum());out['reg_haz_sigpos']=R[R.b/R.se>1.96].repo.tolist();out['reg_haz_signeg']=int((R.b/R.se<-1.96).sum())
out['reg_haz_excluded']=sorted(set(T.repo)-set(R.repo))
out['reg_haz_by_age']=hr.groupby('ar').reg.mean().round(3).to_dict()
# hot-fix hazard in week after any release vs later
h2=h.merge(w[['repo','week','hot','reg']],on=['repo','week'],how='left',suffixes=('','_x'))
out['hot_by_age']=h2.groupby(h2.a.astype(int)).hot.mean().round(3).to_dict()
out['any_by_age']=h2.groupby(h2.a.astype(int)).release.mean().round(3).to_dict()
# ---- frailty
gx,gw=np.polynomial.hermite.hermgauss(30)
def frailty(df,col,x):
    gs=[(g[col].values.astype(float),g[x].values.astype(float)) for _,g in df.groupby('repo')]
    def nll(p):
        b0,b1,ls=p;s=np.exp(ls);tot=0
        for y,a in gs:
            eta=b0+b1*a[:,None]+np.sqrt(2)*s*gx[None,:];ll=(y[:,None]*eta-np.logaddexp(0,eta)).sum(0)
            tot+=np.log((gw*np.exp(ll-ll.max())).sum()/np.sqrt(np.pi))+ll.max()
        return -tot
    f=optimize.minimize(nll,[-1,0,0],method='BFGS')
    return dict(b=round(float(f.x[1]),4),se=round(float(np.sqrt(f.hess_inv[1,1])),4),sigma=round(float(np.exp(f.x[2])),3),n=int(sum(len(y) for y,_ in gs)))
out['fr_any']=frailty(h,'release','a')
out['fr_any_noweekly']=frailty(h[~h.repo.isin(T[T.weekly].repo)],'release','a')
out['fr_any_a>=2']=frailty(h[h.a>=2],'release','a')
out['fr_reg_age_since_regular']=frailty(hr,'reg','ar')
out['fr_reg_age_since_regular_noweekly']=frailty(hr[~hr.repo.isin(T[T.weekly].repo)],'reg','ar')
# plain pooled logit (no frailty) for comparison
out['pooled_logit_any']=round(float(np.asarray(sm.Logit(h.release,sm.add_constant(h[['a']])).fit(disp=0).params)[1]),4)
# ---- CV
iv=lambda s:s.diff().dt.total_seconds().div(86400).dropna()
cvt=r.groupby('repo').published_at.apply(lambda s:iv(s).std()/iv(s).mean())
cvr=r[~r.hotfix].groupby('repo').published_at.apply(lambda s:iv(s).std()/iv(s).mean())
meanr=r[~r.hotfix].groupby('repo').published_at.apply(lambda s:iv(s).mean())
C=pd.DataFrame(dict(n=r.groupby('repo').size(),hotfix_share=r.groupby('repo').hotfix.mean(),cv_all=cvt,cv_regular=cvr,mean_days_regular=meanr))
C.to_csv('cv2.csv')
out['cv']=dict(median_all=round(float(cvt.median()),2),median_reg=round(float(cvr.median()),2),min_reg=round(float(cvr.min()),2),max_reg=round(float(cvr.max()),2),n_reg_lt1=int((cvr<1).sum()),n_all_gt1=int((cvt>1).sum()))
T.to_csv('table1_full.csv',index=False);json.dump(out,open('out2.json','w'),indent=1,default=str)
print(json.dumps(out,indent=1,default=str));print(C.round(2).to_string());print(T[['repo','weeks','releases','median_cycle']].to_string())
