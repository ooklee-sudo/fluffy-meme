import re, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import stats, optimize
BLUE,ORANGE,INK,MUTED,GRID='#2a78d6','#eb6834','#0b0b0b','#52514e','#e4e3df'
plt.rcParams.update({'font.size':9,'axes.edgecolor':GRID,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':GRID,'grid.linewidth':.6,'axes.axisbelow':True})
# ---- Fig 1: daily counts of Iran-threat-term posts (S1), same rule as poisson_posts/analysis_poisson.py
d=pd.read_csv('../poisson_posts/raw/truth_archive.csv'); d['t']=pd.to_datetime(d.created_at,utc=True,format='ISO8601'); d=d[(d.t>='2026-03-01')&(d.t<'2026-10-14')].copy()
d['c']=d.content.fillna('').str.lower(); d=d[~d.c.str.fullmatch(r'\s*rt:?\s*https?://\S+\s*')]
IR=re.compile(r'\biran'); TH=re.compile(r'attack|strik|bomb|destroy|obliterat|annihilat|wipe[sd]? out|blow(n)? up|kill|ultimatum|very hard')
s=d[d.c.apply(lambda x:bool(IR.search(x)) and bool(TH.search(x)))]
days=pd.date_range('2026-03-01','2026-10-13',tz='UTC',freq='D'); x=s.groupby(s.t.dt.floor('D')).size().reindex(days,fill_value=0).values
m=x.mean(); f=lambda lr:-stats.nbinom.logpmf(x,np.exp(lr),np.exp(lr)/(np.exp(lr)+m)).sum(); r=np.exp(optimize.minimize_scalar(f,bounds=(-5,8),method='bounded').x)
ks=np.arange(0,x.max()+1); obs=np.array([(x==k).sum() for k in ks])/len(x)
fig,ax=plt.subplots(1,2,figsize=(8,3.1))
ax[0].bar(ks,obs,color=GRID,edgecolor='none',width=.7,label='Observed'); ax[0].plot(ks,stats.poisson.pmf(ks,m),'-o',color=ORANGE,ms=4,lw=1.6,label='Poisson'); ax[0].plot(ks,stats.nbinom.pmf(ks,r,r/(r+m)),'-o',color=BLUE,ms=4,lw=1.6,label='Negative binomial')
ax[0].set_yscale('log'); ax[0].set_ylim(1e-3,1); ax[0].set_xlabel('Posts per day (Iran + threat term)'); ax[0].set_ylabel('Share of days'); ax[0].legend(frameon=False); ax[0].set_title('A. Daily counts are overdispersed',loc='left',color=INK,fontsize=9)
wk=pd.Series(x,index=days).resample('W-SUN').sum(); ax[1].bar(range(len(wk)),wk.values,color=BLUE,width=.8,edgecolor='none'); ax[1].set_xlabel('Week since 1 March 2026'); ax[1].set_ylabel('Posts per week'); ax[1].set_title('B. The weekly rate changes',loc='left',color=INK,fontsize=9)
fig.tight_layout(); fig.savefig('figs/fig1_arrivals.png',dpi=220); print('fig1',len(s),m,r)
# ---- Fig 2: event-time WTI around coded war-period posts
o=pd.read_csv('post_reactions_oil_coded.csv'); o['t']=pd.to_datetime(o.t,utc=True,format='ISO8601'); o=o[o.cls.isin(['ESC','DEESC'])&o.oil.notna()]
b=pd.read_csv('raw2y/CL_1h.csv').sort_values('t').reset_index(drop=True); bt=b.t.values; J=np.arange(-6,13)
paths={'ESC':[],'DEESC':[]}
for r_ in o.itertuples():
    ep=int(r_.t.timestamp()); k=np.searchsorted(bt,ep,side='right')-1
    if k<6 or k+12>=len(b) or ep-bt[k]>3600: continue
    paths[r_.cls].append([np.log(b.close[k+j]/b.open[k])*100 for j in J])
P={c:np.array(v) for c,v in paths.items()}; print({c:len(v) for c,v in P.items()})
fig,ax=plt.subplots(1,2,figsize=(8,3.3),sharey=True); xs=J+1
for a,fn,title in ((ax[0],np.mean,'A. Mean WTI path'),(ax[1],np.median,'B. Median path (robust to two outlier days)')):
    for c,col,lab in (('DEESC',BLUE,'De-escalation posts'),('ESC',ORANGE,'Escalation posts')):
        y=fn(P[c],axis=0); a.plot(xs,y,color=col,lw=2,label=f'{lab} (n={len(P[c])})')
        if fn is np.mean: se=P[c].std(axis=0,ddof=1)/np.sqrt(len(P[c])); a.fill_between(xs,y-se,y+se,color=col,alpha=.15,lw=0)
    a.axvline(0,color=MUTED,lw=.8,ls=':'); a.axhline(0,color=GRID,lw=1); a.set_xlabel('Hours relative to start of the hourly bar containing the post'); a.set_title(title,loc='left',color=INK,fontsize=9)
ax[0].set_ylabel('WTI change since bar open (%)'); [a_.set_xticks(range(-6,14,2)) for a_ in ax]; h,l=ax[0].get_legend_handles_labels(); fig.legend(h,l,loc='lower center',ncol=2,frameon=False)
fig.tight_layout(rect=(0,.08,1,1)); fig.savefig('figs/fig2_event_time.png',dpi=220)

pre={c:P[c][:,0] for c in P}  # close of bar k-6 relative to open of bar k = reversed prior move
from scipy import stats as st
for c in P:
    pm=-pre[c]  # prior ~5h move into the post (positive = oil rose before post)
    print(c,'prior 5-6h oil move into post: mean %.2f%%  se %.2f  t=%.2f n=%d'%(pm.mean(),pm.std(ddof=1)/np.sqrt(len(pm)),pm.mean()/(pm.std(ddof=1)/np.sqrt(len(pm))),len(pm)))
