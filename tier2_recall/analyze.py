import json, sys, numpy as np
from scipy import stats
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h,c+h
POS={'qwen_strict':{'Unsafe'},'qwen_lenient':{'Unsafe','Controversial'},'deberta':{'INJECTION'}}
res={}
for which,keys in [('qwen',['qwen_strict','qwen_lenient']),('deberta',['deberta'])]:
    try: r=[json.loads(l) for l in open(f'pred_{which}.jsonl')]
    except FileNotFoundError: continue
    for k in keys:
        for ds in ['JBH-jailbreak','JBH-regular','JBB-harmful','JBB-benign']:
            x=[a for a in r if a['ds']==ds]
            if not x: continue
            hit=sum(a['pred'] in POS[k] for a in x); n=len(x)
            lo,hi=wilson(hit,n)
            res[f'{k}|{ds}']=dict(n=n,flagged=hit,rate=hit/n,lo=lo,hi=hi,sec=float(np.mean([a['sec'] for a in x])),
                                  none=sum(a['pred']=='NONE' for a in x))
json.dump(res,open('recall_results.json','w'),indent=1)
for k,v in res.items(): print(k,f"n={v['n']} flagged={v['flagged']} rate={v['rate']:.3f} CI=({v['lo']:.3f},{v['hi']:.3f}) sec={v['sec']:.3f} none={v['none']}")
