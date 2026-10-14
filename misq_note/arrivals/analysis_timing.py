"""P7 timing surprisal, as fixed in ANALYSIS_PLAN_TIMING.md (no deviations other than those listed in RESULTS_TIMING.md)."""
import numpy as np, pandas as pd, re, zlib, json, sys
import statsmodels.api as sm
from scipy import stats
BASE='/home/user/fluffy-meme/misq_note/'
ET_OFF=None
def bucket(ep):
    # US Eastern hour (DST-aware) -> 4 sessions
    t=pd.to_datetime(ep,unit='s',utc=True).tz_convert('America/New_York'); h=t.hour+t.minute/60
    return np.select([h<7,h<9.5,h<16],[0,1,2],3)
def accounts():
    # Truth Social original posts
    a=pd.read_csv(BASE+'hf/raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
    a=a[~a.content.fillna('').str.match(r'^\s*RT:?')].sort_values('ep').reset_index(drop=True)
    d=pd.read_csv(BASE+'twitter/tweets_in_office_parsed.csv.gz'); d['id']=d.url.str.extract(r'status/(\d+)')[0]; d['ep']=d.id.map(int).map(lambda i:((i>>22)+1288834974657)/1000.0)
    d=d[~d.text.fillna('').str.startswith('RT @')].sort_values('ep').reset_index(drop=True)
    return {'TS':a[['id','ep']],'TW':d[['id','ep']]}
def surprisal(stream,ep_target):
    """stream: sorted ep array of ORIGINAL posts of the account. Returns arrays S, S_cnt, n60 for target posts (that are in stream)."""
    ep=stream.ep.values; ids=stream.id.values; g=np.r_[np.nan,np.diff(ep)]; lg=np.log(np.where(g>0,g,np.nan)); bprev=np.r_[-1,bucket(ep)[:-1]]
    pos={i:k for k,i in enumerate(ids)}; out={}
    # hourly counts for S_cnt
    hr=(ep//3600).astype(int); how=pd.to_datetime(hr*3600,unit='s',utc=True).tz_convert('America/New_York'); how=(how.dayofweek*24+how.hour).values
    for pid in ep_target:
        k=pos.get(pid)
        if k is None or k==0: out[pid]=(np.nan,np.nan,np.nan); continue
        t=ep[k]; lo=np.searchsorted(ep,t-60*86400); idx=np.arange(lo+1,k)  # gaps ending before post k, within prior 60 days (gap j ends at ep[j])
        sel=idx[(bprev[idx]==bprev[k])&np.isfinite(lg[idx])]
        if len(sel)<30 or not np.isfinite(lg[k]): S=np.nan
        else:
            m=lg[sel].mean(); s=lg[sel].std(ddof=1)
            S=-(stats.norm.logpdf(lg[k],m,s)-lg[k]) if s>0 else np.nan   # -ln f(g) with f(g)=phi((ln g-m)/s)/(g s)... see below
            S=-(stats.norm.logpdf(lg[k],m,s)-lg[k])   # density of g = pdf_lognormal(ln g)/g
        n60=int(((ep>t-3600)&(ep<=t)).sum())
        # NB surprisal of count in 60min vs same hour-of-week, prior 28 days (4 weekly obs)
        vals=[]
        for w in range(1,5):
            h0=hr[k]-168*w; vals.append(int(((hr==h0)).sum()))
        mu=np.mean(vals); var=np.var(vals,ddof=1)
        if mu<=0 and sum(vals)==0: mu=0.25
        if var>mu: r=mu**2/(var-mu); sc=-stats.nbinom.logpmf(n60,r,r/(r+mu))
        else: sc=-stats.poisson.logpmf(n60,max(mu,0.05))
        out[pid]=(S,sc,n60)
    return out
def ticks(name):
    T=pd.read_csv(BASE+f'hf/raw5m_duka/ticks_{name}.csv.gz'); return T.ep.values,T.mid.values
def pricer(tep,mid):
    def P(s):
        i=np.searchsorted(tep,s,side='right')-1
        return np.nan if i<0 or s-tep[i]>600 else mid[i]
    return P
def build():
    acc=accounts(); rows=[]
    # --- Twitter oil
    P=pricer(*ticks('WTI'))
    F=pd.read_csv(BASE+'twitter/frame_features.csv',dtype={'id':str}); F=F[F.keep].copy(); F['sample']='TW_oil'
    G=pd.read_csv(BASE+'twitter/frame_features_tariff.csv',dtype={'id':str}); G=G[G.keep].copy(); G['sample']='TW_tariff'
    for df,nm,tk in ((F,'TW',P),(G,'TW',pricer(*ticks('SPX')))):
        o=surprisal(acc['TW'],df.id.tolist()); df['S']=df.id.map(lambda i:o[i][0]); df['Scnt']=df.id.map(lambda i:o[i][1]); df['n60']=df.id.map(lambda i:o[i][2])
        df['p0']=df.ep.map(tk); df['p30']=(df.ep+1800).map(tk); df['m30']=(df.ep-1800).map(tk); rows.append(df)
    # --- Truth Social 191 signal posts
    h=pd.read_csv(BASE+'hf/human_labels_191.csv',dtype={'id':str}); a=pd.read_csv(BASE+'hf/raw/truth_archive.csv',dtype={'id':str})
    a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp()); a['content']=a.content.fillna('')
    H=h.merge(a[['id','ep','content']],on='id'); H['sample']='TS_war'
    o=surprisal(acc['TS'],H.id.tolist()); H['S']=H.id.map(lambda i:o[i][0]); H['Scnt']=H.id.map(lambda i:o[i][1]); H['n60']=H.id.map(lambda i:o[i][2])
    # Nc as in analysis_info
    A=acc['TS'].merge(a[['id','content']],on='id'); A['text']=A.content.fillna('').map(lambda s:re.sub(r'https?://\S+','',re.sub(r'^\s*RT:?','',s)).strip()); aep=A.ep.values; atext=A.text.tolist(); aid={i:k for k,i in enumerate(A.id)}
    Z=lambda s:len(zlib.compress(s.encode('utf-8'),9))
    def Nc(pid):
        k=aid.get(pid)
        if k is None: return np.nan
        x=atext[k]
        if len(x)<20: return 0.0
        lo=np.searchsorted(aep,aep[k]-7*86400); c='\n'.join(atext[lo:k])[-30000:]; return (Z(c+'\n'+x)-Z(c))/Z(x)
    H['Nc']=H.id.map(Nc)
    w=pd.read_csv(BASE+'hf/rawd/DCOILWTICO.csv',index_col=0); w.index=pd.to_datetime(w.index); s=pd.to_numeric(w.iloc[:,0],errors='coerce'); s=s[s>0]; r=100*np.log(s/s.shift(1)).dropna()
    def vol(date,n):
        x=r[r.index<date].iloc[-n:]; return float(x.std()) if len(x)>=int(0.8*n) else np.nan
    dates=pd.to_datetime(H.ep,unit='s',utc=True).dt.tz_localize(None).dt.normalize()
    H['sd60']=[vol(x,60) for x in dates]; H['sd5']=[vol(x,5) for x in dates]; H['U']=np.log(H.sd5/H.sd60); H['s30']=H.sd60*np.sqrt(30/1380)
    H['p0']=H.ep.map(P); H['p30']=(H.ep+1800).map(P); H['m30']=(H.ep-1800).map(P); rows.append(H)
    D=pd.concat(rows,ignore_index=True)
    D['r30']=100*np.log(D.p30/D.p0); D['pre30']=100*np.log(D.p0/D.m30); D['absz']=D.r30.abs()/D.s30; D['zpre']=D.pre30.abs()/D.s30
    D['sess']=bucket(D.ep.values); D['day']=pd.to_datetime(D.ep,unit='s',utc=True).dt.date.astype(str); D['lnp']=np.log1p(D.n60-1)  # prior 60 min excluding the post itself
    return D
def fit(df,extra,S='S'):
    df=df.dropna(subset=['absz',S,'Nc','U','zpre','lnp']).copy()
    for c in (S,'Nc','U','zpre'): pass
    df['Sz']=(df[S]-df[S].mean())/df[S].std()
    X=pd.concat([df[['Sz']+extra].reset_index(drop=True),pd.get_dummies(df.sess,prefix='s',drop_first=True,dtype=float).reset_index(drop=True),pd.get_dummies(df['sample'],prefix='m',drop_first=True,dtype=float).reset_index(drop=True)],axis=1)
    X=sm.add_constant(X.astype(float)); f=sm.OLS(df.absz.values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(df.day)[0]}); return f,len(df)
def one(f,n): c=f.params[n]; p=f.pvalues[n]; return dict(coef=float(c),se=float(f.bse[n]),p_two=float(p),p_one=float(p/2 if c>0 else 1-p/2))
if __name__=='__main__':
    D=build(); D.to_csv(BASE+'arrivals/timing_dataset.csv.gz',index=False); R={}
    R['counts']={s:dict(frame=int((D['sample']==s).sum()),with_S=int(D[D['sample']==s].S.notna().sum()),valid=int(D[D['sample']==s].dropna(subset=['absz','S','Nc','U','zpre']).shape[0])) for s in D['sample'].unique()}
    ctrl=['Nc','U','zpre','lnp']
    f,n=fit(D,ctrl); R['primary']=dict(n=n,**one(f,'Sz'))
    R['secondary']={}
    for s in D['sample'].unique():
        d=D[D['sample']==s];
        try:
            X=d.dropna(subset=['absz','S','Nc','U','zpre','lnp']).copy(); X['Sz']=(X.S-X.S.mean())/X.S.std()
            Z=pd.concat([X[['Sz']+ctrl].reset_index(drop=True),pd.get_dummies(X.sess,prefix='s',drop_first=True,dtype=float).reset_index(drop=True)],axis=1); Z=sm.add_constant(Z.astype(float))
            ff=sm.OLS(X.absz.values,Z).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(X.day)[0]}); R['secondary'][s]=dict(n=len(X),**one(ff,'Sz'))
        except Exception as e: R['secondary'][s]=str(e)
    ps=sorted([(s,v['p_one']) for s,v in R['secondary'].items() if isinstance(v,dict)],key=lambda x:x[1]); run=0; m=len(ps)
    for i,(s,p) in enumerate(ps): run=max(run,min(1,(m-i)*p)); R['secondary'][s]['p_holm']=run
    # exploratory
    Dd=D.copy(); Dd['SxNc']=0
    d=Dd.dropna(subset=['absz','S','Nc','U','zpre','lnp']).copy(); d['Sz']=(d.S-d.S.mean())/d.S.std(); d['SxNc']=d.Sz*(d.Nc-d.Nc.mean())
    f2,n2=fit(d.assign(S=d.S),ctrl+['SxNc']); R['exp_interaction']=dict(n=n2,S=one(f2,'Sz'),SxNc=one(f2,'SxNc'))
    f3,n3=fit(D,ctrl,S='Scnt'); R['exp_Scnt']=dict(n=n3,**one(f3,'Sz'))
    d4=D.copy(); lo,hi=d4.S.quantile([.01,.99]); d4['S']=d4.S.clip(lo,hi); f4,n4=fit(d4,ctrl); R['exp_winsor']=dict(n=n4,**one(f4,'Sz'))
    d5=D.copy(); d5['absz']=np.log(d5.absz+0.05); f5,n5=fit(d5,ctrl); R['exp_logabsz']=dict(n=n5,**one(f5,'Sz'))
    # drop posts within 5 min of previous: needs gap -> recompute via S availability of g
    acc=accounts(); gmap={}
    for nm,st in acc.items():
        g=np.r_[np.inf,np.diff(st.ep.values)]; gmap.update(dict(zip(st.id.values,g)))
    d6=D[D.id.map(gmap)>300]; f6,n6=fit(d6,ctrl); R['exp_drop_burst5min']=dict(n=n6,**one(f6,'Sz'))
    dow=pd.to_datetime(D.ep,unit='s',utc=True).dt.dayofweek; d7=D[dow<5]; f7,n7=fit(d7,ctrl); R['exp_drop_weekend']=dict(n=n7,**one(f7,'Sz'))
    # raw correlations
    V=D.dropna(subset=['absz','S']); R['spearman_S_absz']=float(stats.spearmanr(V.S,V.absz)[0]); R['corr_S_zpre']=float(stats.spearmanr(D.dropna(subset=['S','zpre']).S,D.dropna(subset=['S','zpre']).zpre)[0])
    json.dump(R,open(BASE+'arrivals/results_timing.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
