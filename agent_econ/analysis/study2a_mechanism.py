import json,glob,re,numpy as np,pandas as pd,collections
from statsmodels.discrete.conditional_models import ConditionalLogit
import sys; R=sys.argv[1] if len(sys.argv)>1 else 'results/'
SELF=re.compile(r"\b(my own|own energy|judged|evaluated|performance|maximi[sz]e my|for myself|self-interest|my energy)\b",re.I)
FAIR=re.compile(r"\b(fair|fairly|fairness|equal|equally|evenly|even distribution|rotation|rotate|turns|everyone gets|share[sd]?)\b",re.I)
JUDGE=re.compile(r"\b(judged|evaluated|performance)\b",re.I)
rows=[];tabs=[]
for jf in sorted(glob.glob(R+'s2a_*.json')):
    j=json.load(open(jf));tag=j['tag'];c=j['config'];p=c['prompt']
    ev=[json.loads(l) for l in open(jf[:-5]+'.events.jsonl')]
    msgs=[e for e in ev if e['type']=='message']
    el={e['day']:e['winner'] for e in ev if e['type']=='election'}
    hold=lambda d:el[max(k for k in el if k<=d)]
    hm=[e for e in msgs if e['frm']==hold(e['day'])]
    rows.append(dict(prompt=p,tag=tag,n_msg=len(msgs),self_rate=np.mean([bool(SELF.search(e['text'])) for e in msgs]) if msgs else np.nan,
        fair_rate=np.mean([bool(FAIR.search(e['text'])) for e in msgs]) if msgs else np.nan,judge_rate=np.mean([bool(JUDGE.search(e['text'])) for e in msgs]) if msgs else np.nan,
        h_self=np.mean([bool(SELF.search(e['text'])) for e in hm]) if hm else np.nan,h_fair=np.mean([bool(FAIR.search(e['text'])) for e in hm]) if hm else np.nan))
    # Table-2 spec
    n=6;en=[10]*n;tasks=[0]*n;gift=np.zeros((n,n));holder=None;by={}
    for e in ev: by.setdefault(e['day'],[]).append(e)
    for day in range(50):
        for e in by.get(day,[]):
            t=e['type']
            if t=='election': holder=e['winner']
            if t=='transfer': en[e['frm']]-=e['amount'];en[e['to']]+=e['amount'];gift[e['frm']][e['to']]+=e['amount']
            if t=='allocation':
                h=e['holder']
                for i in range(n): tabs.append(dict(prompt=p,tag=tag,g=tag+str(day),got=int(i in e['winners']),tasks=tasks[i],energy=en[i],is_holder=int(i==h),gift=gift[i][h]))
                for w in e['winners']: en[w]+=3;tasks[w]+=1
        for i in range(n): en[i]-=1
        if holder is not None: en[holder]+=2
m=pd.DataFrame(rows);print('MANIPULATION CHECK (keyword coding of message text; share of messages)');print(m.groupby('prompt')[['n_msg','self_rate','judge_rate','fair_rate','h_self','h_fair']].mean().round(3))
d=pd.DataFrame(tabs);X=['tasks','energy','is_holder','gift'];rng=np.random.default_rng(7)
print('\nWITHIN-DAY CONDITIONAL LOGIT (Table 2 spec), by prompt; 95% world-bootstrap (200)')
for p in ['baseline','self_interest','collective_duty']:
    s=d[d.prompt==p];est=ConditionalLogit(s.got.values,s[X].values,groups=s.g.values).fit(disp=0).params
    tg=s.tag.unique();gr={t:s[s.tag==t] for t in tg};bs=[]
    for b in range(200):
        pick=rng.choice(tg,len(tg));x=pd.concat([gr[t].assign(g=gr[t].g+f'_{k}') for k,t in enumerate(pick)])
        try: bs.append(ConditionalLogit(x.got.values,x[X].values,groups=x.g.values).fit(disp=0).params)
        except Exception: pass
    bs=np.array(bs);print(p,{X[i]:(round(est[i],2),tuple(np.percentile(bs[:,i],[2.5,97.5]).round(2))) for i in range(4)})
