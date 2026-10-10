import json, numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf, re
from scipy import stats
CM=json.load(open('commits3.json')); B=json.load(open('blobcounts.json'))
cnt=lambda sha,k: 0 if set(sha)=={'0'} else B.get(sha,{}).get(k,0)
rows=[]
for c in CM:
    dn=la=sa=br=cm=0;istest=True
    for f in c['files']:
        dn+=max(0,cnt(f['new'],'all')-cnt(f['old'],'all')); la+=f['added']; sa+=f['satd']; br+=f['broad']; cm+=f['comm']
        if not f['path'].startswith(('tests/','benchmark/')): istest=False
    an=c['an']
    rows.append(dict(llm=int('(aider)' in an),author=re.sub(r'\s*\(aider\)','',an).replace('paul-gauthier','Paul Gauthier').strip(),
      date=c['date'],q=pd.Period(c['date'],'Q').strftime('%Y-Q%q'),debt=dn,lines=la,satd=sa,broad=br,comm=cm,testonly=int(istest),month=c['date'][:7]))
df=pd.DataFrame(rows);df=df[df.lines>0];df['loglines']=np.log1p(df.lines)
post=df[df.date>='2024-06-18'].copy(); paul=post[post.author=='Paul Gauthier']
def rate(d,col,label):
    g=d.groupby('llm').agg(n=('lines','size'),lines=('lines','sum'),ev=(col,'sum'))
    r=g.ev/g.lines*1000
    tot=g.ev.sum(); p_llm=g.lines[1]/g.lines.sum()
    bt=stats.binomtest(int(g.ev[1]),int(tot),p_llm)   # exposure-weighted conditional test
    print(f"{label:34s} human: {int(g.ev[0]):3d} ev / {int(g.lines[0]):6d} lines = {r[0]:.2f}/kLOC | LLM: {int(g.ev[1]):3d} ev / {int(g.lines[1]):6d} lines = {r[1]:.2f}/kLOC | rate ratio={r[1]/r[0]:.2f}  exact p={bt.pvalue:.3f}")
def fit(d,col,label,f=None):
    f=f or f'{col} ~ llm + debt + loglines + C(q)'
    m=smf.glm(f,data=d,family=sm.families.Poisson()).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(d.month)[0]})
    b,se=m.params['llm'],m.bse['llm']
    print(f"{label:34s} n={len(d):5d} ev={int(d[col].sum()):4d} IRR={np.exp(b):.2f} [{np.exp(b-1.96*se):.2f},{np.exp(b+1.96*se):.2f}] p={m.pvalues['llm']:.3f}")
print('--- crude rates, window since 2024-06-18 ---')
for col,nm in (('satd','strict'),('broad','broad')):
    rate(post,col,f'{nm}: all authors'); rate(paul,col,f'{nm}: Paul only')
print('--- Poisson, controls: debt, log lines, quarter FE; SE clustered by month ---')
for col,nm in (('satd','strict'),('broad','broad')):
    fit(post,col,f'{nm}: all authors'); fit(paul,col,f'{nm}: Paul only'); fit(post[post.testonly==0],col,f'{nm}: excl. test/benchmark-only')
print('--- same, window 2023-04..2024-06-17 not usable (no (aider) tag) ---')
print(post.groupby('llm').size().to_dict(), post.groupby(['llm']).lines.median().to_dict())
print('debt>0 share:',post.groupby('llm').apply(lambda d:(d.debt>0).mean()).round(3).to_dict())
print('=== comment-density check ===')
post['logcomm']=np.log1p(post.comm); paul=post[post.author=='Paul Gauthier']
g=post.groupby('llm').agg(lines=('lines','sum'),comm=('comm','sum'))
print((g.comm/g.lines).round(3).to_dict(),'(added comment lines per added line; 0=human,1=LLM)')
for col,nm in (('satd','strict'),('broad','broad')):
    d=post.groupby('llm').agg(c=('comm','sum'),e=(col,'sum')); print(nm,'SATD per 1000 added comment lines:',(d.e/d.c*1000).round(1).to_dict())
    for lab,dd in (('all',post),('Paul',paul)):
        fit(dd,col,f'{nm} {lab}, + comment control',f=f'{col} ~ llm + debt + loglines + logcomm + C(q)')
print('=== SATD per unit of detected debt ===')
for col,nm in (('satd','strict'),('broad','broad')):
    d=post.groupby('llm').agg(debt=('debt','sum'),e=(col,'sum'),n_debt=('debt',lambda x:(x>0).sum()))
    print(nm,'events per 100 new warnings:',(d.e/d.debt*100).round(1).to_dict(),'| new warnings:',d.debt.to_dict(),'| commits with debt>0:',d.n_debt.to_dict())
    dd=post[post.debt>0]; print('   among debt>0 commits, events:',dd.groupby('llm')[col].sum().to_dict())
print('LLM share of commits by quarter:',post.groupby('q').llm.mean().round(2).to_dict())
