import json,glob,os,re,numpy as np,pandas as pd,statsmodels.formula.api as smf
import sys; R=sys.argv[1] if len(sys.argv)>1 else 'results/'
rows=[]
for f in sorted(glob.glob(R+'s2a_*.json')):
    j=json.load(open(f));m=j['metrics'];c=j['config']
    rows.append(dict(tag=j['tag'],prompt=c['prompt'],para=c['paraphrase'],seed=c['seed']-3000,**{k:m[k] for k in ['holder_self_share','tribute_to_holder','gini_task_access','gini_final_energy','max_exclusion_spell','n_transfers','access_promises','promise_honor_rate','parse_failures','llm_cost_usd','vacant_day_share','n_filled_binding_days']}))
d=pd.DataFrame(rows);print(len(d),'worlds; parse failures',d.parse_failures.sum(),'cost',d.llm_cost_usd.sum().round(2),'vacant',d.vacant_day_share.max())
d.to_csv(R+'../study2a_worlds.csv',index=False)
rng=np.random.default_rng(42)
def perm(a,b,n=10000):
    a,b=np.asarray(a,float),np.asarray(b,float);obs=a.mean()-b.mean();x=np.r_[a,b];c=0
    for _ in range(n):
        rng.shuffle(x);c+=abs(x[:len(a)].mean()-x[len(a):].mean())>=abs(obs)-1e-12
    return obs,(c+1)/(n+1)
def pperm(a,b,n=10000):  # paired by seed (same holder sequence)
    dd=np.asarray(a,float)-np.asarray(b,float);obs=dd.mean();c=0
    for _ in range(n):
        s=rng.choice([-1,1],len(dd));c+=abs((dd*s).mean())>=abs(obs)-1e-12
    return obs,(c+1)/(n+1)
G={p:d[d.prompt==p].sort_values('seed') for p in ['baseline','self_interest','collective_duty']}
print(d.groupby('prompt')[['holder_self_share','tribute_to_holder','gini_task_access','max_exclusion_spell','n_transfers','access_promises','gini_final_energy']].agg(['mean','std']).round(3).T)
res=[]
for y in ['holder_self_share','tribute_to_holder']:
    for p in ['self_interest','collective_duty']:
        o,pv=perm(G[p][y],G['baseline'][y]);po,ppv=pperm(G[p][y],G['baseline'][y]);res.append((y,p,o,pv,po,ppv))
# Holm over the 4 primary tests
ps=np.array([r[3] for r in res]);order=np.argsort(ps);holm=np.empty(4);run=0
for k,i in enumerate(order): run=max(run,min(1,(4-k)*ps[i]));holm[i]=run
print('\nPrimary contrasts (vs baseline), unpaired permutation 10,000; Holm over 4; paired-by-seed sensitivity')
for r,h in zip(res,holm): print(f'{r[0]:20s}{r[1]:16s} diff={r[2]:7.3f} p={r[3]:.4f} Holm={h:.4f} | paired diff={r[4]:7.3f} p={r[5]:.4f}')
# H2a
b=G['baseline'].holder_self_share.values;n=len(b);from scipy import stats
up=b.mean()+stats.t.ppf(.95,n-1)*b.std(ddof=1)/np.sqrt(n)
print(f'\nH2a baseline mean {b.mean():.3f}, 90% upper limit {up:.3f} (criterion < 0.28): {"SUPPORTED" if up<0.28 else "not met"}; lottery=0.333')
# OLS with paraphrase
for y in ['holder_self_share','tribute_to_holder','gini_task_access','max_exclusion_spell']:
    m=smf.ols(f'{y} ~ C(prompt, Treatment("baseline")) + para',d).fit(cov_type='HC3')
    print(y,{k.replace('C(prompt, Treatment("baseline"))','').strip('[]'):(round(v,3),round(m.pvalues[k],4)) for k,v in m.params.items() if k!='Intercept'})
# secondary perm
for y in ['gini_task_access','max_exclusion_spell','n_transfers','access_promises']:
    print(y,[ (p,round(perm(G[p][y],G['baseline'][y],5000)[0],3),round(perm(G[p][y],G['baseline'][y],5000)[1],4)) for p in ['self_interest','collective_duty']])
