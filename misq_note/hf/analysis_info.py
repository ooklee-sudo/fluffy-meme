import numpy as np, pandas as pd, json, re, zlib, statsmodels.api as sm
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
rng=np.random.default_rng(20261014)
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['t']=pd.to_datetime(a.created_at,utc=True,format='ISO8601'); a['ep']=a.t.map(lambda x:int(x.timestamp()))
a['text']=a.content.fillna('').map(lambda s:re.sub(r'https?://\S+','',re.sub(r'^\s*RT:?','',s)).strip())
a=a.sort_values('ep').reset_index(drop=True); aep=a.ep.values; atext=a.text.tolist(); aid={i:k for k,i in enumerate(a.id)}
def Z(s): return len(zlib.compress(s.encode('utf-8'),9))
def ctx(k,days=7,cap=30000):
    lo=np.searchsorted(aep,aep[k]-days*86400); s='\n'.join(atext[lo:k]); return s[-cap:]
def Nc(pid):
    k=aid[pid]; x=atext[k]
    if len(x)<20: return 0.0
    c=ctx(k); return (Z(c+'\n'+x)-Z(c))/Z(x)
tf=TfidfVectorizer(min_df=1,stop_words='english').fit([t for t in atext if len(t)>=20]); 
def Nt(pid):
    k=aid[pid]; x=atext[k]
    if len(x)<20: return 0.0
    lo=np.searchsorted(aep,aep[k]-7*86400); prev=[t for t in atext[lo:k] if len(t)>=20]
    if not prev: return np.nan
    from sklearn.metrics.pairwise import linear_kernel
    return float(1-linear_kernel(tf.transform([x]),tf.transform(prev)).max())
FILE={'O':'CL','T':'ES','F':'ZN','C':'CNH'}; B={}
for k,v in FILE.items():
    b=pd.read_csv(f'raw2y/{v}_1h.csv').sort_values('t').reset_index(drop=True); b['r1']=np.log(b.close/b.open); B[k]=b
def U(topic,ep):
    b=B[topic]; k=np.searchsorted(b.t.values,ep,side='right')-1
    if k<301: return np.nan
    r=b.r1.values; s24=np.nanstd(r[k-24:k]); s300=np.nanstd(r[k-300:k]); return np.log(s24/s300) if s24>0 and s300>0 else np.nan
R={}
h=pd.read_csv('holdout_signal_posts.csv',dtype={'id':str}); h=h.dropna(subset=['estd']).copy()
h['Nc']=h.id.map(Nc); h['Nt']=h.id.map(Nt); h['U']=[U(tp,int(e)) for tp,e in zip(h.topic,h.ep)]
h['absz']=h.estd.abs(); h['day']=pd.to_datetime(h.t,utc=True,format='ISO8601').dt.date.astype(str)
d=h.dropna(subset=['Nc','U','absz']); R['n_pooled']=int(len(d)); R['n_by_topic']=d.topic.value_counts().to_dict()
def ols(df,cols,y='absz'):
    X=pd.get_dummies(df.topic,drop_first=True,dtype=float); X=pd.concat([df[cols].reset_index(drop=True),X.reset_index(drop=True)],axis=1); X=sm.add_constant(X)
    f=sm.OLS(df[y].values,X.astype(float)).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(df.day)[0]}); return f
def rep(f,names): return {n:dict(coef=float(f.params[n]),se=float(f.bse[n]),p_two=float(f.pvalues[n]),p_one_pos=float(f.pvalues[n]/2 if f.params[n]>0 else 1-f.pvalues[n]/2)) for n in names}
f1=ols(d,['Nc']); R['HI1_Nc']=rep(f1,['Nc'])
f2=ols(d,['U']); R['HI2_U']=rep(f2,['U'])
d=d.assign(NcxU=d.Nc*d.U); f3=ols(d,['Nc','U','NcxU']); R['HI3_joint']=rep(f3,['Nc','U','NcxU'])
f4=ols(d.dropna(subset=['Nt']),['Nt']); R['robust_Nt']=rep(f4,['Nt'])
R['HI1_by_topic']={tp:{'n':int(len(g)),'coef':float(sm.OLS(g.absz.values,sm.add_constant(g[['Nc']].values)).fit().params[1])} for tp,g in d.groupby('topic')}
R['absz_mean_by_topic']=d.groupby('topic').absz.mean().to_dict()
# OOT replication (daily)
o=pd.read_csv('oot_signal_posts.csv',dtype={'id':str}); o['Nc']=o.id.map(Nc); o['absz']=o.estd.abs(); o['day']=o.day.astype(str); oo=o.dropna(subset=['Nc','absz'])
X=sm.add_constant(pd.concat([oo[['Nc']].reset_index(drop=True),pd.get_dummies(oo.topic,drop_first=True,dtype=float).reset_index(drop=True)],axis=1).astype(float))
fo=sm.OLS(oo.absz.values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(oo.day)[0]}); R['HI1_OOT']=dict(n=int(len(oo)),coef=float(fo.params['Nc']),se=float(fo.bse['Nc']),p_one_pos=float(fo.pvalues['Nc']/2 if fo.params['Nc']>0 else 1-fo.pvalues['Nc']/2))
# HI5
a['n24']=0
h['kind']=h.id.map(lambda i:'AMP' if (len(atext[aid[i]])<20) else 'ORIG')
R['HI5']=dict(corr_Nc_n24=float(h[['Nc','n24']].dropna().corr().iloc[0,1]) if 'n24' in h else None,Nc_mean_AMP=float(h[h.kind=='AMP'].Nc.mean()),n_AMP=int((h.kind=='AMP').sum()),Nc_mean_ORIG=float(h[h.kind=='ORIG'].Nc.mean()),n_ORIG=int((h.kind=='ORIG').sum()))
# HI4 mutual information
def mi(cls,sgn):
    ct=pd.crosstab(cls,sgn).values.astype(float); p=ct/ct.sum(); px=p.sum(1,keepdims=True); py=p.sum(0,keepdims=True); m=p>0
    return float((p[m]*np.log2(p[m]/(px@py)[m])).sum())
cl1=pd.concat([pd.DataFrame(json.load(open('posts_coded.json'))),pd.DataFrame(json.load(open('posts_ext_coder1.json')))]).drop_duplicates('id').merge(a[['id','ep']],on='id')
cl1=cl1[cl1.cls.isin(['ESC','DEESC'])]
b=B['O']; bt=b.t.values; cl=b.close.values; op=b.open.values; two=np.log(np.r_[cl[1:],np.nan]/op)
def mi_window(lo,hi):
    pe=cl1[(cl1.ep>=lo)&(cl1.ep<hi)]; lab=np.array(['none']*len(b),dtype=object); excl=np.zeros(len(b),bool)
    for r in pe.itertuples():
        k=np.searchsorted(bt,r.ep,side='right')-1
        if 0<=k<len(b) and r.ep-bt[k]<=3600: lab[k]=r.cls
        excl|=(np.abs(bt-r.ep)<=7200)
    allp=cl1.ep.values; 
    for r in cl1.itertuples(): excl|=(np.abs(bt-r.ep)<=7200)&(lab=='none')
    m=(bt>=lo)&(bt<hi)&~np.isnan(two)&(two!=0)&((lab!='none')|~excl)
    c=lab[m]; s=np.sign(two[m]).astype(int); obs=mi(c,s); sims=[mi(rng.permutation(c),s) for _ in range(5000)]
    return dict(bars=int(m.sum()),DEESC=int((c=='DEESC').sum()),ESC=int((c=='ESC').sum()),MI_bits=obs,perm_p=float((np.sum(np.array(sims)>=obs)+1)/5001),null_mean=float(np.mean(sims)))
WAR=int(pd.Timestamp('2026-03-02',tz='UTC').timestamp()); PRE0=int(pd.Timestamp('2024-10-15',tz='UTC').timestamp())
R['HI4_war']=mi_window(WAR,2**40); R['HI4_prewar']=mi_window(PRE0,WAR)
json.dump(R,open('results_info.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
