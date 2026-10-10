import json, glob, re, numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
P='/tmp/claude-0/-home-user-fluffy-meme/4eacae0f-a18f-5230-98e4-dc485b935205/scratchpad/p4/'
# aider rows in same schema
CM=json.load(open(P+'commits3.json')); B=json.load(open(P+'blobcounts.json'))
cnt=lambda sha: 0 if set(sha)=={'0'} else B.get(sha,{}).get('all',0)
rows=[]
for c in CM:
    if c['date']<'2024-06-18': continue
    dn=0
    for f in c['files']: dn+=max(0,cnt(f['new'])-cnt(f['old']))
    la=sum(f['added'] for f in c['files']); 
    if la==0: continue
    an=c['an']; base=re.sub(r'\s*\(aider\)','',an).replace('paul-gauthier','Paul Gauthier').strip()
    rows.append(dict(repo='Aider-AI/aider',h=c['h'],ae=base.lower(),an=an,agent=0,date=c['date'],llm=int('(aider)' in an),debt=dn,lines=la,
        satd=sum(f['satd'] for f in c['files']),broad=sum(f['broad'] for f in c['files']),comm=sum(f['comm'] for f in c['files']),
        testonly=int(all(f['path'].startswith(('tests/','benchmark/')) for f in c['files']))))
A=pd.DataFrame(rows)
cn=A.groupby('ae').llm.agg(['sum','count']); keep=cn[(cn['sum']>=8)&((cn['count']-cn['sum'])>=8)].index
A=A[A.ae.isin(keep)]
D=pd.concat([A]+[pd.read_csv(f) for f in sorted(glob.glob('out_*.csv'))],ignore_index=True)
D=D[(D.lines>0)&(D.agent==0)].copy()
D['author']=D.repo+'|'+D.ae
D['q']=D.repo+'|'+pd.PeriodIndex(D.date,freq='Q').astype(str)
D['month']=D.date.str[:7]
D['loglines']=np.log1p(D.lines); D['logcomm']=np.log1p(D.comm)
D.to_csv('pooled.csv',index=False)
print(D.groupby('repo').agg(commits=('h','size'),authors=('author','nunique'),llm=('llm','sum'),lines=('lines','sum'),satd=('satd','sum'),broad=('broad','sum')))
def fit(d,col,f,label,cl='author'):
    d=d.copy()
    # drop authors/quarters with no events (Poisson FE is uninformative there) to keep estimation stable
    ev=d.groupby('author')[col].transform('sum'); d=d[ev>0]
    try:
        m=smf.glm(f,data=d,family=sm.families.Poisson()).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(d[cl])[0]},maxiter=200)
        b,se=m.params['llm'],m.bse['llm']
        print(f"{label:46s} n={len(d):6d} ev={int(d[col].sum()):5d} IRR={np.exp(b):.2f} [{np.exp(b-1.96*se):.2f},{np.exp(b+1.96*se):.2f}] p={m.pvalues['llm']:.3f}")
        return b,se
    except Exception as e:
        print(label,'ERR',str(e)[:80]); return None
base='{c} ~ llm + debt + loglines + C(author) + C(q)'
for col in ('satd','broad'):
    print('=====',col)
    fit(D,col,base.format(c=col),'pooled, author FE + repo-quarter FE')
    fit(D,col,(base+' + logcomm').format(c=col),'pooled, + comment control')
    D2=D.copy(); D2['loglines']=np.log1p(D2.lines.clip(upper=5000)); fit(D2,col,base.format(c=col),'pooled, added lines capped at 5,000')
    for r in D.repo.unique(): fit(D[D.repo!=r],col,base.format(c=col),'pooled, leave out '+r)
    fit(D[D.testonly==0],col,base.format(c=col),'pooled, excl. test-only commits')
    res=[]
    for r,d in D.groupby('repo'):
        o=fit(d,col,'{c} ~ llm + debt + loglines + C(author) + C(q)'.format(c=col),'  '+r,cl='month')
        if o: res.append((r,)+o)
    # random-effects meta-analysis of repo-level log IRRs
    if len(res)>=2:
        b=np.array([x[1] for x in res]);se=np.array([x[2] for x in res]);w=1/se**2
        fe=(w*b).sum()/w.sum(); Q=(w*(b-fe)**2).sum(); k=len(b); tau2=max(0,(Q-(k-1))/(w.sum()-(w**2).sum()/w.sum()))
        wr=1/(se**2+tau2); re_=(wr*b).sum()/wr.sum(); sre=np.sqrt(1/wr.sum())
        print(f"  random-effects meta (k={k}) IRR={np.exp(re_):.2f} [{np.exp(re_-1.96*sre):.2f},{np.exp(re_+1.96*sre):.2f}] tau2={tau2:.2f} I2={max(0,(Q-(k-1))/Q)*100:.0f}%")
