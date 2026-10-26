import pickle, json, numpy as np, pandas as pd
from scipy.stats import ks_2samp
from poisson_sns import hourly
DATA='/tmp/claude-0/-home-user-fluffy-meme/85836436-e025-583a-b00a-2fcdeefc7114/scratchpad/data/'
sim=pickle.load(open('sim_study1.pkl','rb'))
# ---- real references ----
D=pd.read_parquet(DATA+'bsky_tid.parquet'); D=D[D.ts.notna()]
full=D[D.ts.dt.floor('D').isin(pd.to_datetime(['2024-11-28','2024-11-29','2024-12-03','2024-12-04']))]
bs_prof=np.histogram(full.ts.dt.hour+full.ts.dt.minute/60,bins=np.arange(25))[0]
rep=D[D.is_reply&(D.pt>0)]; bs_delay=((rep.t-rep.pt)/3.6e9)
bs_delay_all=bs_delay[(bs_delay>=0)]; bs_delay=bs_delay[(bs_delay>=0)&(bs_delay<=48)].values
real={'Bluesky (UTC, 4 full days)':dict(prof=bs_prof,delay=bs_delay,n=len(full),
        med_all=float(bs_delay_all.median()),n_delay=len(bs_delay))}
for s,lab in (('money','Money.SE (US Eastern)'),('law','Law.SE (US Eastern)'),('workplace','Workplace.SE (US Eastern)')):
    z=np.load(DATA+f'{s}_ref.npz'); d=z['com']; 
    real[lab]=dict(prof=z['prof_et'],delay=d[(d>=0)&(d<=48)],n=int(z['prof_et'].sum()),med_all=float(np.median(d)),n_delay=int(((d>=0)&(d<=48)).sum()))
def norm(p): p=np.asarray(p,float); return p/p.sum()
def pear(a,b): return float(np.corrcoef(a,b)[0,1])
def tv(a,b): return float(.5*np.abs(norm(a)-norm(b)).sum())
def amp(p):  # first-harmonic amplitude relative to the mean (phase free)
    p=norm(p)*24; f=np.fft.rfft(p)/24; return float(2*abs(f[1])/abs(f[0]))
def ptr(p): p=norm(p); return float(p.max()/p.min())
def rmax(a,b): return max(pear(np.roll(a,k),b) for k in range(24))
out={}
for sch in ('ipp','hpp','poll'):
    runs=sim[sch]; H=np.array([hourly(r['posts']) for r in runs]); mean_h=H.mean(0)
    delays=np.concatenate([(r['comments'][:,1]-r['comments'][:,0]) for r in runs]); delays=delays[(delays>=0)&(delays<=48)]
    row={'amp':amp(mean_h),'ptr':ptr(mean_h),'med_delay':float(np.median(delays)),'within5min':float((delays<=5/60).mean()),'n_delay':len(delays),'vmr':float(np.mean([hourly(r['posts']).var()/hourly(r['posts']).mean() for r in runs]))}
    for lab,rl in real.items():
        rp=rl['prof']
        row[lab]=dict(r_aligned=pear(mean_h,rp),tv=tv(mean_h,rp),r_shiftfree=rmax(mean_h,rp),ks=float(ks_2samp(delays,rl['delay']).statistic))
    out[sch]=row; out[sch]['hourly']=norm(mean_h).tolist()
out['real']={lab:dict(amp=amp(v['prof']),ptr=ptr(v['prof']),med_delay=float(np.median(v['delay'])),within5min=float((v['delay']<=5/60).mean()),med_all=v['med_all'],n=v['n'],n_delay=v['n_delay'],hourly=norm(v['prof']).tolist()) for lab,v in real.items()}
json.dump(out,open('study1_real_validation.json','w'),indent=1)
for sch in ('ipp','hpp','poll'):
    o=out[sch]; print(sch,'amp %.2f ptr %.2f med %.2f 5min %.3f vmr %.0f'%(o['amp'],o['ptr'],o['med_delay'],o['within5min'],o['vmr']))
    for lab in real: x=o[lab]; print('   ',lab,' r=%.2f TV=%.2f rshiftfree=%.2f KS=%.2f'%(x['r_aligned'],x['tv'],x['r_shiftfree'],x['ks']))
for lab,v in out['real'].items(): print(lab,'amp %.2f ptr %.2f med %.2f 5min %.3f medAll %.2f n %d nd %d'%(v['amp'],v['ptr'],v['med_delay'],v['within5min'],v['med_all'],v['n'],v['n_delay']))
