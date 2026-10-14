import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(20261014)
sox=pd.read_csv('sox_daily.csv',index_col=0,parse_dates=True).iloc[:,0]; spx=pd.read_csv('spx_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
D=pd.concat([sox.rename('sox'),spx.rename('spx')],axis=1).dropna(); R=100*np.log(D/D.shift(1)).dropna(); days=R.index
def beta(day):
    i=days.get_loc(day); x=R.iloc[max(0,i-250):i]
    if len(x)<150: return 1.0
    return float(np.polyfit(x.spx.values,x.sox.values,1)[0])
F=pd.read_csv('frame_features_tariff.csv',dtype={'id':str}); m1=json.load(open('labels_tariff_1.json')); m2=json.load(open('labels_tariff_2.json'))
F['c1']=F.id.map(lambda i:m1[i]['cls']); F['c2']=F.id.map(lambda i:m2[i]['cls']); F=F[F.keep&(F.c1==F.c2)&F.c1.isin(['ESC','DEESC'])].copy(); F['cls']=F.c1
txt=pd.read_csv('frame_tariff.csv',dtype={'id':str}).set_index('id').text; F['text']=F.id.map(txt)
F['china']=F.text.str.contains(r"china|chinese|beijing|\bxi\b|huawei|zte|currency",case=False,regex=True)
F['et']=pd.to_datetime(F.ep,unit='s',utc=True).dt.tz_convert('America/New_York')
def map_day(t):
    d=t.normalize().tz_localize(None); hm=t.hour+t.minute/60; wd=t.weekday()
    trading=d in days
    if trading and 9.5<=hm<16: return None,'in_session'
    if trading and hm<9.5: return d,'pre_open'
    nxt=days[days>d]; return (nxt[0] if len(nxt) else None),'after_close_or_closed'
mp=[map_day(t) for t in F.et]; F['rday']=[m[0] for m in mp]; F['when']=[m[1] for m in mp]
Rr={'n_agreed_kept':len(F),'when':F.when.value_counts().to_dict()}
E=F[F.rday.notna()&(F.when!='in_session')].copy(); E=E[E.rday.isin(days)]
E['beta']=E.rday.map(beta); E['rs']=E.rday.map(R.sox); E['rp']=E.rday.map(R.spx); E['A']=E.rs-E.beta*E.rp; E['Adiff']=E.rs-E.rp
E['s']=np.where(E.cls=='DEESC',1,-1); E['dirA']=E.s*E.A; E['dirDiff']=E.s*E.Adiff; E['dirSPX']=E.s*E.rp
Rr['n_outside_hours']=len(E); Rr['by_class']=E.cls.value_counts().to_dict(); Rr['china_n']=int(E.china.sum())
def collapse(df):  # one obs per (reaction day, class)
    return df.groupby(['rday','cls']).agg(dirA=('dirA','mean'),dirDiff=('dirDiff','mean'),dirSPX=('dirSPX','mean'),s=('s','mean')).reset_index()
def test(df,name):
    c=collapse(df); o={'n_obs':int(len(c)),'n_events':int(len(df))}
    if len(c)>=6:
        o.update(mean_dirA=float(c.dirA.mean()),median_dirA=float(c.dirA.median()),mean_dirDiff=float(c.dirDiff.mean()),wilcoxon_p_greater=float(stats.wilcoxon(c.dirA,alternative='greater').pvalue),mean_dirSPX=float(c.dirSPX.mean()))
        x=c.dirA.values; obs=x.mean(); cnt=sum((x*rng.choice([-1,1],len(x))).mean()>=obs for _ in range(10000)); o['signflip_p']=float((cnt+1)/10001)
        d=(c.dirA-c.dirSPX); o['H13c_paired_mean']=float(d.mean()); o['H13c_wilcoxon_p']=float(stats.wilcoxon(d,alternative='greater').pvalue)
        for cl in ('DEESC','ESC'):
            s=c[c.cls==cl]; o[cl]=dict(n=int(len(s)),mean=float(s.dirA.mean()) if len(s) else None)
    Rr[name]=o
test(E[E.china],'H13_china'); test(E,'H13b_all')
p13=[Rr['H13_china'].get('wilcoxon_p_greater'),Rr['H13b_all'].get('wilcoxon_p_greater')]; srt=sorted([(p,i) for i,p in enumerate(p13) if p is not None]); adj={}; run=0
for k,(p,i) in enumerate(srt): run=max(run,min(1,(len(srt)-k)*p)); adj[['H13','H13b'][i]]=run
Rr['holm']=adj
# exploratory: Truth Social tariff signal posts, hourly SOX vs S&P 500 (2-hour reaction), beta = 1 difference and estimated beta on hourly returns
hs=pd.read_csv('../hf/holdout_signal_posts.csv',dtype={'id':str}); hs=hs[(hs.topic=='T')&hs.cls.isin(['ESC','DEESC'])].copy(); hs['t']=pd.to_datetime(hs.t,utc=True,format='ISO8601')
bs=pd.read_csv('../hf/raw2y/SOX_1h.csv').sort_values('t').reset_index(drop=True); bp=pd.read_csv('../hf/raw2y/SPX_1h.csv').sort_values('t').reset_index(drop=True)
bs['r']=np.log(bs.close/bs.open)*100; bp['r']=np.log(bp.close/bp.open)*100; M=bs[['t','r']].merge(bp[['t','r']],on='t',suffixes=('_sox','_spx')); M=M.sort_values('t').reset_index(drop=True); mt=M.t.values
bhat=float(np.polyfit(M.r_spx.values,M.r_sox.values,1)[0]); rows=[]
for r in hs.itertuples():
    ep=int(r.t.timestamp()); k=np.searchsorted(mt,ep,side='right')-1
    if k<0 or k+1>=len(M) or ep-mt[k]>3600 or mt[k+1]-mt[k]>3600*2: continue
    rs=M.r_sox[k]+M.r_sox[k+1]; rp=M.r_spx[k]+M.r_spx[k+1]; s=1 if r.cls=='DEESC' else -1; rows.append(dict(cls=r.cls,dirA=s*(rs-bhat*rp),dirSPX=s*rp,dirSOX=s*rs))
T=pd.DataFrame(rows); o={'n':int(len(T)),'beta_hourly':bhat}
if len(T)>=6: o.update(mean_dirA=float(T.dirA.mean()),median_dirA=float(T.dirA.median()),wilcoxon_p_greater=float(stats.wilcoxon(T.dirA,alternative='greater').pvalue),mean_dirSOX=float(T.dirSOX.mean()),mean_dirSPX=float(T.dirSPX.mean()),by_class=T.groupby('cls').dirA.agg(['count','mean']).round(3).to_dict('index'))
Rr['exploratory_truth_social_hourly']=o
json.dump(Rr,open('results_sox.json','w'),indent=1,default=str); print(json.dumps(Rr,indent=1,default=str))
