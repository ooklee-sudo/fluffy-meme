import pandas as pd, numpy as np, re, json
from scipy import stats
rng=np.random.default_rng(20261014)
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str})[['id','content']]
def kind(s):
    s=(s if isinstance(s,str) else '').strip()
    if re.match(r'^RT\b',s): return 'AMP'
    if re.fullmatch(r'(https?://\S+\s*)+',s): return 'AMP'
    return 'ORIG'
a['kind']=a.content.map(kind)
res={}
# ---- Q1
o=pd.read_csv('oot_signal_posts.csv',dtype={'id':str}); o['ds']='OOT'
h=pd.read_csv('holdout_signal_posts.csv',dtype={'id':str}); h=h[h.topic.isin(['F','C'])].copy(); h['ds']='HOLD'
d=pd.concat([o[['id','topic','ds','estd','typ']],h[['id','topic','ds','estd','typ']]]).merge(a[['id','kind']],on='id')
d['stratum']=d.ds+d.topic
n_all=len(d); d=d.dropna(subset=['estd']); res['Q1_n_all']=n_all; res['Q1_n_used']=len(d)
res['Q1_counts']=d.groupby('kind').size().to_dict()
x=d[d.kind=='ORIG'].estd.values; y=d[d.kind=='AMP'].estd.values
diff=x.mean()-y.mean(); lab=d.kind.values.copy(); st=d.stratum.values; ev=d.estd.values
def stat(l): return ev[l=='ORIG'].mean()-ev[l=='AMP'].mean()
cnt=0; B=20000
for _ in range(B):
    l=lab.copy()
    for s in np.unique(st):
        m=np.where(st==s)[0]; l[m]=rng.permutation(l[m])
    cnt+= stat(l)>=diff
res['Q1_mean_ORIG']=float(x.mean()); res['Q1_mean_AMP']=float(y.mean()); res['Q1_diff']=float(diff); res['Q1_perm_p_onesided']=float((cnt+1)/(B+1))
se=np.sqrt(x.var(ddof=1)/len(x)+y.var(ddof=1)/len(y)); res['Q1_diff_CI95']=[float(diff-1.96*se),float(diff+1.96*se)]
sdp=d.estd.std(); res['Q1_MDE_80pct_onesided']=float((1.645+0.84)*sdp*np.sqrt(1/len(x)+1/len(y)))
t=stats.ttest_1samp(y,0); res['Q1b_AMP_mean']=float(y.mean()); res['Q1b_AMP_p_two']=float(t.pvalue); se_y=y.std(ddof=1)/np.sqrt(len(y)); res['Q1b_AMP_CI95']=[float(y.mean()-1.96*se_y),float(y.mean()+1.96*se_y)]
res['Q1_by_stratum']={s:{k:[int(len(g)),float(g.estd.mean())] for k,g in dd.groupby('kind')} for s,dd in d.groupby('stratum')}
act=d[(d.kind=='ORIG')&(d.typ=='ACTION')].estd; res['Q1_sens_ORIG_ACTION_only']={'n':int(len(act)),'mean':float(act.mean()) if len(act) else None}
# ---- Q4
p=pd.read_csv('paper_signal_posts.csv',dtype={'id':str}); p=p[(p.topic=='O')&p.cls.isin(['ESC','DEESC'])].drop_duplicates('id').copy()
b=pd.read_csv('raw2y/CL_1h.csv').sort_values('t').reset_index(drop=True)
b['et']=pd.to_datetime(b.t,unit='s',utc=True).dt.tz_convert('America/New_York')
bt=b.t.values; rows=[]
for r in p.itertuples():
    ep=int(r.ep); i=np.searchsorted(bt,ep,side='right')-1
    if i<0 or i+1>=len(b) or ep-bt[i]>3600: continue
    pt=pd.Timestamp(ep,unit='s',tz='UTC').tz_convert('America/New_York'); hm=pt.hour+pt.minute/60
    rth=(pt.weekday()<5)and(9.5<=hm<16)
    sgn=1 if r.cls=='ESC' else -1
    own=np.log(b.close[i+1]/b.open[i])*100*sgn
    cand=b[(b.t>ep)&(b.et.dt.hour==9)&(b.et.dt.weekday<5)]
    if len(cand)==0: continue
    j=cand.index[0]; reopen=np.log(b.close[j]/b.open[i])*100*sgn
    rows.append(dict(id=r.id,rth=rth,own=own,reopen=reopen))
q=pd.DataFrame(rows); res['Q4_n_total']=len(q); res['Q4_n_after_hours']=int((~q.rth).sum())
ah=q[~q.rth]; dd=(ah.reopen-ah.own).values
res['Q4_mean_own']=float(ah.own.mean()); res['Q4_mean_reopen']=float(ah.reopen.mean()); res['Q4_mean_diff']=float(dd.mean())
obs=dd.mean(); c=0
for _ in range(20000):
    s=rng.choice([-1,1],len(dd)); c+= (dd*s).mean()>=obs
res['Q4_perm_p_onesided']=float((c+1)/20001)
rt=q[q.rth]; res['Q4_inRTH_n']=int(len(rt)); res['Q4_inRTH_mean_own']=float(rt.own.mean()) if len(rt) else None
json.dump(res,open('results_qual_tests.json','w'),indent=1); print(json.dumps(res,indent=1))
