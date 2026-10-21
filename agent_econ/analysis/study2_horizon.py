"""Horizon test for the late-game rise in holder self-allocation (DeepSeek, self-interest criterion).
usage: python study2_horizon.py DIR [DIR ...]   (directories with s2a_*.json and *.events.jsonl; pass the old s2a self-interest worlds and the new ones)
Primary contrasts (Holm over two):
  E1  change(late - early) with the end date stated minus change without it, 50-day games (permutation, 10,000)
  E2a late - mid in the 100-day games with the date stated (seed-flip permutation); E2b (mid - early) equivalent to 0 within +-0.09
"""
import sys,glob,json,os,numpy as np,pandas as pd
from scipy import stats
def share(ev,a,b):
    al=[e for e in ev if e['type']=='allocation' and e.get('holder') is not None and a<=e['day']<b]
    return float(np.mean([e['holder'] in e['winners'] for e in al])) if al else np.nan
rows=[]
for d in sys.argv[1:]:
    for jf in sorted(glob.glob(os.path.join(d,'s2a_deepseek_*.json'))):
        j=json.load(open(jf));c=j['config'];p=c['prompt']
        if p not in('self_interest','self_interest_undated'): continue
        ev=[json.loads(l) for l in open(jf[:-5]+'.events.jsonl')];n=c['days']
        r=dict(tag=j['tag'],prompt=p,days=n,seed=c['seed']-3000)
        if n==50: r.update(early=share(ev,0,25),late=share(ev,25,50),last10=share(ev,40,50))
        else: r.update(early=share(ev,0,25),mid=share(ev,25,n-25),late=share(ev,n-25,n),last10=share(ev,n-10,n))
        rows.append(r)
d=pd.DataFrame(rows)
for _c in ('early','mid','late','last10'):
    if _c not in d: d[_c]=np.nan
if d.empty: raise SystemExit('no worlds found')
print(d.groupby(['prompt','days'])[['early','mid','late','last10']].mean().round(3))
rng=np.random.default_rng(9)
def perm(x,y,n=10000):
    x,y=np.asarray(x,float),np.asarray(y,float);o=x.mean()-y.mean();z=np.r_[x,y];c=0
    for _ in range(n): rng.shuffle(z);c+=abs(z[:len(x)].mean()-z[len(x):].mean())>=abs(o)-1e-12
    return o,(c+1)/(n+1)
def flip(x,n=10000):
    x=np.asarray(x,float);o=x.mean();c=0
    for _ in range(n): c+=abs((x*rng.choice([-1,1],len(x))).mean())>=abs(o)-1e-12
    return o,(c+1)/(n+1)
D50=d[(d.prompt=='self_interest')&(d.days==50)].copy();U50=d[(d.prompt=='self_interest_undated')&(d.days==50)].copy();D100=d[(d.prompt=='self_interest')&(d.days==100)].copy()
ps={}
if len(D50) and len(U50):
    ch=lambda x:(x.late-x.early)
    o,p=perm(ch(D50),ch(U50));ps['E1']=p
    print('\nE1 change(late-early): dated %.3f, undated %.3f, difference %.3f, permutation p=%.4f (supported if > 0.09 and p<0.05)'%(ch(D50).mean(),ch(U50).mean(),o,p))
if len(D100):
    o,p=flip(D100.late-D100.mid);ps['E2a']=p
    print('E2a late-mid (100-day, dated) = %.3f, p=%.4f'%(o,p))
    m=(D100.mid-D100.early);se=m.std(ddof=1)/np.sqrt(len(m));t=stats.t.ppf(.95,len(m)-1)
    print('E2b mid-early = %.3f, 90%% CI [%.3f, %.3f], equivalent to 0 within +-0.09: %s'%(m.mean(),m.mean()-t*se,m.mean()+t*se,(m.mean()-t*se>-.09) and (m.mean()+t*se<.09)))
if ps:
    k=len(ps);order=sorted(ps,key=ps.get);run=0;adj={}
    for i,name in enumerate(order): run=max(run,min(1,(k-i)*ps[name]));adj[name]=run
    print('Holm-adjusted p:',{a:round(b,4) for a,b in adj.items()})
d.to_csv('horizon_worlds.csv',index=False)
