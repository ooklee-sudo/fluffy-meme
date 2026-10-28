import sys,json,numpy as np,pandas as pd
sys.path.insert(0,'.')
import agreement_creation as ac
R='../reproduction/results/'
A=ac.read('human_creation_sample_filled_coderA.xlsx').rename(columns={'h':'a'})
C=ac.read('human_creation_sample_filled_coderC.xlsx').rename(columns={'h':'c'})
d=ac.key.merge(A,on='row').merge(C,on='row'); print(len(d))
for n,f in [('haiku','task_scores_claude-haiku-5.5.jsonl'),('luna','task_scores_gpt-5.6-luna.jsonl')]:
    sc={json.loads(l)['task'].strip():json.loads(l)['visual'] for l in open(R+f)}
    d[n]=d.text.str.strip().map(sc)
w=d.weight
ac.report('A vs C (human-human)',d.a,d.c,w)
print('linear-weighted unweighted-sample kappa', ac.kappa(d.a,d.c,np.ones(len(d))), ac.kappa(d.a,d.c,np.ones(len(d)),True))
print(pd.crosstab(d.a,d.c))
ac.report('C vs original LLM',d.c,d.s,w)
ac.report('C vs haiku',d.c,d.haiku.astype(int),w)
ac.report('C vs luna',d.c,d.luna.astype(int),w)
ac.report('A vs haiku',d.a,d.haiku.astype(int),w)
# spearman-brown reliability of mean of two coders
from scipy.stats import spearmanr
print('spearman A,C',spearmanr(d.a,d.c)[0])
d.to_csv('results/two_coder_scores.csv',index=False)
