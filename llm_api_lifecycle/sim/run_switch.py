import sys; sys.path.insert(0,'.')
from data import *; from samplers import weibull_pool
from sim import simulate
NAMED=[4.44,4.13,0.91,1.33,3.06,1.45]; MATCHED=[1.00,1.33,0.69,0.91,1.00,1.45]  # 3.5->3.6 Flash at standard (not introductory) price
d=SETS['Gemini API (stable)']; pool,_=weibull_pool(lifetimes(d)); nt=notice_days(d)
rows=[]
for lab,ratios,shock in [('named',NAMED,True),('matched',MATCHED,True),('unchanged',[1],False)]:
    for s in ([0.05,0.10,0.20,0.36] if lab!='unchanged' else [0.10]):
        o=simulate(pool,nt,ratios,N=8000,sigma=s,price_shock=shock,strategies=('rigid','flex','flex_npv','flex_thr'),seed=5)
        a=o['flex_npv']['total'];b=o['flex_thr']['total'];dd=a-b;se=dd.std(ddof=1)/np.sqrt(dd.size)
        rows.append(dict(prices=lab,sigma=s,theta=round(o['theta'],1),npv=round(a.mean()),thr=round(b.mean()),diff=round(dd.mean()),ci=f"[{dd.mean()-1.96*se:,.0f}, {dd.mean()+1.96*se:,.0f}]",
            gain_pct=round(100*dd.mean()/a.mean(),2),sw=f"{o['flex_npv']['nsw'].mean():.1f} / {o['flex_thr']['nsw'].mean():.1f}",
            early_vs_flex_pp=round(100*(o['flex']['total'].mean()-b.mean())/o['rigid']['total'].mean(),2)))
        print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv('results_switch.csv',index=False)
