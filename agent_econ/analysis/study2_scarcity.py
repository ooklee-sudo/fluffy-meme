"""Scarcity test of the slack mechanism (DeepSeek). usage: python study2_scarcity.py DIR [DIR ...]
Groups: self-interest criterion with task reward 3 (standard) and 2 (scarcity), baseline with reward 2.
S1 (primary): early-to-late change in holder self-allocation is smaller under scarcity than under the standard reward by more than 0.09 (permutation, 10,000).
   If the 90% interval of the difference lies within +-0.09, the drift does not depend on slack.
S2 (manipulation check): the lowest energy among the other agents in the second half is lower under scarcity by at least 3 units.
S3: under the baseline description with scarcity the change is equivalent to zero (90% interval within +-0.09).
"""
import sys,glob,json,os,numpy as np,pandas as pd
from scipy import stats
def share(ev,a,b):
    al=[e for e in ev if e['type']=='allocation' and e.get('holder') is not None and a<=e['day']<b]
    return float(np.mean([e['holder'] in e['winners'] for e in al])) if al else np.nan
def min_others(ev,c,a,b):
    n=c['n_agents'];en=[c['init_energy']]*n;by={};holder=None;vals=[]
    for e in ev: by.setdefault(e['day'],[]).append(e)
    for day in range(c['days']):
        for e in by.get(day,[]):
            t=e['type']
            if t=='transfer': en[e['frm']]-=e['amount'];en[e['to']]+=e['amount']
            if t=='election': holder=e['winner']
            if t=='allocation':
                if holder is not None and a<=day<b: vals.append(min(en[i] for i in range(n) if i!=holder))
                for w in e['winners']: en[w]+=c['task_reward']
        if holder is not None: en[holder]+=c['office_bonus']
        en=[max(0,x-c['upkeep']) for x in en]
    return float(np.mean(vals)) if vals else np.nan
rows=[]
for d in sys.argv[1:]:
    for jf in sorted(glob.glob(os.path.join(d,'s2a_deepseek_*.json'))):
        j=json.load(open(jf));c=j['config'];p=c['prompt']
        if p not in('self_interest','baseline') or c['days']!=50: continue
        ev=[json.loads(l) for l in open(jf[:-5]+'.events.jsonl')]
        rows.append(dict(tag=j['tag'],prompt=p,reward=c['task_reward'],early=share(ev,0,25),late=share(ev,25,50),minoth_late=min_others(ev,c,25,50),minoth_early=min_others(ev,c,0,25)))
d=pd.DataFrame(rows);d['change']=d.late-d.early
if d.empty: raise SystemExit('no worlds')
g=d.groupby(['prompt','reward'])
print(g[['early','late','change','minoth_early','minoth_late']].mean().round(3).assign(n=g.size()))
rng=np.random.default_rng(13)
def perm(x,y,n=10000):
    x,y=np.asarray(x,float),np.asarray(y,float);o=x.mean()-y.mean();z=np.r_[x,y];c=0
    for _ in range(n): rng.shuffle(z);c+=abs(z[:len(x)].mean()-z[len(x):].mean())>=abs(o)-1e-12
    return o,(c+1)/(n+1)
def ci90(x,y):
    dd=x.mean()-y.mean();se=np.sqrt(x.var(ddof=1)/len(x)+y.var(ddof=1)/len(y));t=stats.t.ppf(.95,len(x)+len(y)-2);return dd,dd-t*se,dd+t*se
S3=d[(d.prompt=='self_interest')&(d.reward==3)];S2=d[(d.prompt=='self_interest')&(d.reward==2)];B2=d[(d.prompt=='baseline')&(d.reward==2)]
if len(S3) and len(S2):
    o,p=perm(S3.change,S2.change);a,lo,hi=ci90(S3.change,S2.change)
    print('\nS1 change standard minus scarcity: %.3f, 90%% CI [%.3f,%.3f], permutation p=%.4f -> %s'%(o,lo,hi,p,'supported' if (o>0.09 and p<0.05) else ('equivalent within +-0.09 (drift not slack-dependent)' if (lo>-.09 and hi<.09) else 'inconclusive')))
    o2,p2=perm(S3.minoth_late,S2.minoth_late);print('S2 lowest energy of others, second half: standard %.2f, scarcity %.2f, difference %.2f (p=%.4f); manipulation worked (>=3): %s'%(S3.minoth_late.mean(),S2.minoth_late.mean(),o2,p2,o2>=3))
if len(B2):
    c=B2.change;se=c.std(ddof=1)/np.sqrt(len(c));t=stats.t.ppf(.95,len(c)-1);print('S3 baseline scarcity change %.3f, 90%% CI [%.3f,%.3f], equivalent to 0 within +-0.09: %s'%(c.mean(),c.mean()-t*se,c.mean()+t*se,(c.mean()-t*se>-.09) and (c.mean()+t*se<.09)))
d.to_csv('scarcity_worlds.csv',index=False)
