import json,sys
from analyze import load,pairs
from scipy.stats import binomtest
import glob
for band in [None,(10,300)]:
  ps=[]; 
  for f in sorted(glob.glob('out/*.jsonl')): ps+=pairs(load(f),band)
  for k in ['satd','net','dup']:
    d=[p[1][k]-p[2][k] for p in ps]; up=sum(x>0 for x in d); dn=sum(x<0 for x in d)
    print(band,k,'authors',len(ps),'AI higher',up,'AI lower',dn,'ties',len(d)-up-dn,'sign p=%.3g'%binomtest(up,up+dn).pvalue)
# pooled raw rates among paired authors
ps=[];rows_all={}
for f in sorted(glob.glob('out/*.jsonl')):
  rows=load(f); pp=pairs(rows); au={p[0] for p in pp}
  for r in rows:
    if r['author'] in au: ps.append(r)
import collections
first={}
for r in ps:
  if r['ai']: first[r['author']]=min(first.get(r['author'],1e18),r['ts'])
g=collections.defaultdict(lambda:[0,0,0,0,0,0])
for r in ps:
  if not r['ai'] and r['ts']<first[r['author']]: continue
  x=g[r['ai']]; x[0]+=r['add'];x[1]+=r['dele'];x[2]+=r['satd'];x[3]+=r['elig'];x[4]+=r['dup'];x[5]+=1
for k,(a,d,s,e,du,n) in g.items(): print('AI' if k else 'other', 'commits',n,'add',a,'del',d,'net %.3f'%(a/(a+d)),'satd/kloc %.3f'%(1000*s/a),'dup%% %.2f'%(100*du/e))
