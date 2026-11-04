import sys, json; sys.path.insert(0,'.')
from data import *; from samplers import weibull_pool
from sim import simulate, summarize
NAMED=[4.44,4.13,0.91,1.33,3.06,1.45]; MATCHED=[1.00,1.33,0.69,0.91,1.00,1.45]  # 3.5->3.6 Flash at standard (not introductory) price
oa_notice=notice_days(SETS['OpenAI API (chat/text)'])
scen={'Gemini life + OpenAI notice (manuscript design)':(SETS['Gemini API (stable)'],oa_notice),
      'Gemini API (stable), own notice':(SETS['Gemini API (stable)'],None),
      'OpenAI API, own notice':(SETS['OpenAI API (chat/text)'],None),
      'Anthropic API, own notice':(SETS['Anthropic API'],None)}
rows=[]
for name,(d,nt) in scen.items():
    pool,_=weibull_pool(lifetimes(d)); nt=notice_days(d) if nt is None else nt
    def run(**kw):
        r=summarize(simulate(pool,nt,kw.pop('ratios',NAMED),N=20000,strategies=('rigid','flex'),**kw),B=400)
        f=r['flex']; return r['migrations'],f['saving'],f['ci'],f['breakeven_pw'],f['be_ci']
    for lab,kw in [('unchanged',dict(price_shock=False)),('named c=1',dict(c=1.0)),('named c=0.5',dict(c=0.5)),('named c=0',dict(c=0.0)),
                   ('matched c=1',dict(c=1.0,ratios=MATCHED)),('matched c=0.5',dict(c=0.5,ratios=MATCHED)),('matched c=0',dict(c=0.0,ratios=MATCHED))]:
        m,s,ci,be,bci=run(**kw)
        rows.append(dict(scenario=name,price=lab,migrations=round(m,2),saving=round(s,1),saving_ci=f"[{ci[0]:.1f}, {ci[1]:.1f}]",breakeven=round(be,1),be_ci=f"[{bci[0]:.1f}, {bci[1]:.1f}]"))
        print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv('results_scenarios.csv',index=False)
