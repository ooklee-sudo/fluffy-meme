"""Exploratory stock reaction to LLM releases, as fixed in ANALYSIS_PLAN_LLM_STOCK.md."""
import numpy as np, pandas as pd, json, urllib.request, os, warnings
from scipy import stats
warnings.filterwarnings('ignore'); rng=np.random.default_rng(20261014)
MAP={'Google':'GOOGL','Google DeepMind':'GOOGL','Meta':'META','Meta AI':'META','Alibaba':'BABA','Alibaba Cloud':'BABA','Microsoft':'MSFT','Nvidia':'NVDA','Baidu':'BIDU','Amazon':'AMZN','Xiaomi':'1810.HK','Tencent':'0700.HK'}
IDX={'GOOGL':'^GSPC','META':'^GSPC','BABA':'^GSPC','MSFT':'^GSPC','NVDA':'^GSPC','BIDU':'^GSPC','AMZN':'^GSPC','1810.HK':'^HSI','0700.HK':'^HSI'}
os.makedirs('llm/px',exist_ok=True)
def px(sym):
    f=f'llm/px/{sym.replace("^","_")}.csv'
    if not os.path.exists(f):
        u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1640995200&period2=1792000000&interval=1d&events=div,split'
        j=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read())['chart']['result'][0]
        ts=pd.to_datetime(j['timestamp'],unit='s'); ac=j['indicators'].get('adjclose',[{}])[0].get('adjclose') or j['indicators']['quote'][0]['close']
        pd.DataFrame({'date':(ts+pd.to_timedelta(j['meta'].get('gmtoffset',0),unit='s')).normalize(),'p':ac}).dropna().to_csv(f,index=False)
    d=pd.read_csv(f,parse_dates=['date']).drop_duplicates('date').set_index('date').p; return d
D=pd.read_csv('llm/llm_releases.csv'); D=D[D.day.notna()&(D.day>='2023-01-01')].copy(); D['d']=pd.to_datetime(D.day); D['sym']=D.developer.map(MAP); L=D[D.sym.notna()].sort_values('d')
R={'listed_rows':int(len(L)),'rows_by_symbol':L.sym.value_counts().to_dict()}
def returns(sym):
    p=px(sym); m=px(IDX[sym]); r=np.log(p).diff().dropna(); mr=np.log(m).diff().dropna(); df=pd.concat([r,mr],axis=1,join='inner'); df.columns=['r','m']; return df
def scar(df,i0):
    """i0 = integer position of day 0. returns CAR[0,1], SCAR, CAR0, CAR[-1,1] or None."""
    lo,hi=i0-250,i0-30
    if lo<0 or i0+1>=len(df): return None
    est=df.iloc[lo:hi]
    if len(est)<120: return None
    b,a=np.polyfit(est.m.values,est.r.values,1); res=est.r.values-a-b*est.m.values; sd=res.std(ddof=2)
    ar=lambda k: df.r.iloc[i0+k]-a-b*df.m.iloc[i0+k]
    car=ar(0)+ar(1); return dict(car=car,scar=car/(sd*np.sqrt(2)),car0=ar(0),car_m1=ar(-1)+ar(0)+ar(1))
ev=[]; last={}
for _,x in L.iterrows():
    sym=x.sym; df=returns(sym); dates=df.index
    i0=dates.searchsorted(x.d)
    if i0>=len(dates): continue
    if sym in last and i0-last[sym]<=3: continue   # clustering rule: first of releases within 3 trading days
    last[sym]=i0; s=scar(df,i0)
    if s: ev.append(dict(sym=sym,name=x['name'],date=str(x.d.date()),day0=str(dates[i0].date()),**s))
E=pd.DataFrame(ev); R['n_events']=int(len(E)); R['events_by_symbol']=E.sym.value_counts().to_dict()
car=E.car.values*100; R['H_L1']=dict(mean_car_pct=float(car.mean()),se=float(car.std(ddof=1)/np.sqrt(len(car))),t=float(stats.ttest_1samp(car,0).statistic),p_t=float(stats.ttest_1samp(car,0).pvalue),p_wilcoxon=float(stats.wilcoxon(car).pvalue),median=float(np.median(car)),share_positive=float((car>0).mean()))
# null pools: random 2-day windows per firm avoiding release days (+-3 trading days)
pool={}
for sym in E.sym.unique():
    df=returns(sym); dates=df.index; rel=[dates.searchsorted(x) for x in L[L.sym==sym].d]; bad=set()
    for r_ in rel: bad|=set(range(r_-3,r_+4))
    cand=[i for i in range(len(dates)) if dates[i]>=pd.Timestamp('2023-01-01') and i not in bad and i+1 not in bad]
    pick=rng.choice(cand,min(300,len(cand)),replace=False); vals=[scar(df,i) for i in pick]; pool[sym]=np.array([abs(v['scar']) for v in vals if v])
obs=np.abs(E.scar.values).mean(); sims=np.array([np.mean([rng.choice(pool[s]) for s in E.sym]) for _ in range(5000)])
R['H_L2']=dict(mean_abs_scar_events=float(obs),mean_abs_scar_random=float(sims.mean()),p_one_sided=float((sims>=obs).mean()),pool_sizes={k:int(len(v)) for k,v in pool.items()})
ps=sorted([('H_L1',R['H_L1']['p_t']),('H_L2',R['H_L2']['p_one_sided'])],key=lambda x:x[1]); run=0
for i,(k,p) in enumerate(ps): run=max(run,min(1,(2-i)*p)); R[k]['p_holm']=float(run)
R['robust']=dict(car0_mean_pct=float(E.car0.mean()*100),car0_p=float(stats.ttest_1samp(E.car0,0).pvalue),car_m1_1_mean_pct=float(E.car_m1.mean()*100),car_m1_1_p=float(stats.ttest_1samp(E.car_m1,0).pvalue),leave_one_firm_out={s:float(E[E.sym!=s].car.mean()*100) for s in E.sym.unique()},by_firm_mean_car_pct={s:float(g.car.mean()*100) for s,g in E.groupby('sym')})
E.to_csv('results_llm_stock_events.csv',index=False); json.dump(R,open('results_llm_stock.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float)); print(E.round(4).to_string())
