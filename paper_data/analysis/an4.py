import pandas as pd, numpy as np, statsmodels.api as sm, json, warnings
warnings.filterwarnings('ignore')
w=pd.read_csv('x/data/weekly.csv',parse_dates=['week']).sort_values(['repo','week']).reset_index(drop=True)
g=w.groupby('repo')
w['a']=g.age.shift(1)+1
w['lb']=np.log1p(w.bugs);w['li']=np.log1p(w.issues)
w['share']=np.where(w.issues>0,w.bugs/w.issues.clip(lower=1),np.nan)
for c in ['lb','li','share']:
    w[c+'_z']=g[c].transform(lambda s:(s-s.mean())/s.std())
for k in (1,2,3): 
    w[f'lb{k}']=w.groupby('repo').lb_z.shift(k);w[f'sh{k}']=w.groupby('repo').share_z.shift(k)
w['li1']=w.groupby('repo').li_z.shift(1)
w['bug_ma']=w[['lb1','lb2','lb3']].mean(axis=1)
w['t']=w.groupby('repo').cumcount()/52.
h=w.dropna(subset=['a','lb1','lb2','lb3','li1','sh1']).copy();h['a']=h.a.clip(upper=8);h['ac']=h.a
out={}
def fe(df,xs,y='release'):
    X=pd.concat([df[xs],pd.get_dummies(df.repo,drop_first=True,dtype=float)],axis=1);X=sm.add_constant(X)
    m=sm.Logit(df[y],X).fit(disp=0,cov_type='cluster',cov_kwds={'groups':pd.factorize(df.repo)[0]})
    return {k:(round(float(m.params[k]),4),round(float(m.bse[k]),4),round(float(m.pvalues[k]),3)) for k in xs}
out['A_lag1_bugs']=fe(h,['lb1','li1','a','t'])
out['B_lag1to3_bugs']=fe(h,['lb1','lb2','lb3','li1','a','t'])
out['C_lag1_share']=fe(h,['sh1','li1','a','t'])
out['D_bugMA']=fe(h,['bug_ma','li1','a','t'])
h2=h[h.a>=2];out['E_after_first_week']=fe(h2,['lb1','li1','a','t'])
# regular releases only: age since last regular -> reuse hotfix def would need rerun; skip
# per-repo lag1 bug effect, pooled by DL
rows=[]
for repo,d in h.groupby('repo'):
    try:
        m=sm.Logit(d.release,sm.add_constant(d[['lb1','li1','a','t']])).fit(disp=0,cov_type='HC0');rows.append((repo,m.params['lb1'],m.bse['lb1']))
    except Exception: pass
R=pd.DataFrame(rows,columns=['repo','b','se']);R=R[(R.se<2)]
def dl(b,se):
    b=np.array(b);se=np.array(se);wi=1/se**2;m=(wi*b).sum()/wi.sum();Q=(wi*(b-m)**2).sum();k=len(b);t2=max(0,(Q-(k-1))/(wi.sum()-(wi**2).sum()/wi.sum()));ws=1/(se**2+t2);mu=(ws*b).sum()/ws.sum();s=ws.sum()**-.5
    return dict(b=round(mu,3),lo=round(mu-1.96*s,3),hi=round(mu+1.96*s,3),tau2=round(t2,3),k=k)
out['F_perrepo_lag1_DL']=dl(R.b,R.se);out['F_pos']=int((R.b>0).sum());out['F_sigpos']=R[R.b/R.se>1.96].repo.tolist();out['F_signeg']=R[R.b/R.se<-1.96].repo.tolist()
# spike event study: bug-count spike = lb_z>1.5 (within-repo), compare release prob in next 1..4 weeks with non-spike weeks, FE
w['spike']=(w.lb_z>1.5).astype(int)
for k in (1,2,3,4): w[f'rel_f{k}']=w.groupby('repo').release.shift(-k)
ev={}
for k in (1,2,3,4):
    d=w.dropna(subset=[f'rel_f{k}','li_z']).copy()
    d=d.merge(w[['repo','week']],on=['repo','week'])
    X=pd.concat([d[['spike','li_z']],pd.get_dummies(d.repo,drop_first=True,dtype=float)],axis=1);X=sm.add_constant(X)
    m=sm.Logit(d[f'rel_f{k}'],X).fit(disp=0,cov_type='cluster',cov_kwds={'groups':pd.factorize(d.repo)[0]})
    ev[k]=dict(b=round(float(m.params['spike']),3),se=round(float(m.bse['spike']),3),base=round(float(d[d.spike==0][f'rel_f{k}'].mean()),3),after_spike=round(float(d[d.spike==1][f'rel_f{k}'].mean()),3),n_spike=int(d.spike.sum()))
out['G_spike_event']=ev
json.dump(out,open('out4.json','w'),indent=1);print(json.dumps(out,indent=1));print(len(h))
