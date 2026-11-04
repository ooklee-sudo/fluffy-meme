"""Value of notice: same lifetimes, different notice policies (channel choice)."""
import sys; sys.path.insert(0,'.')
from data import *; from samplers import weibull_pool
from sim import simulate, RATE
ot=load([R+'other_lifecycle.csv']); bed=ot[ot.platform=='AWS Bedrock']
bed_notice=notice_days(bed[~bed.notes.str.contains('STRAGGLER')])
rows=[]
cases=[('Anthropic lifetimes','Anthropic API notice',SETS['Anthropic API'],notice_days(SETS['Anthropic API'])),
       ('Anthropic lifetimes','Bedrock notice',SETS['Anthropic API'],bed_notice),
       ('Gemini stable lifetimes','Gemini stable notice',SETS['Gemini API (stable)'],notice_days(SETS['Gemini API (stable)'])),
       ('Gemini preview lifetimes','Gemini preview notice',SETS['Gemini API (preview/exp.)'],notice_days(SETS['Gemini API (preview/exp.)']))]
for lt,nl,d,nt in cases:
    pool,_=weibull_pool(lifetimes(d))
    o=simulate(pool,nt,[1],N=20000,price_shock=False,strategies=('rigid','flex'))
    rig=o['rigid']; fl=o['flex']
    short=lambda s: (s['out']>0).mean()
    rows.append(dict(lifetimes=lt,notice=nl,median_notice=float(np.median(nt)),migrations=round(rig['nmig'].mean(),2),
        rigid_cost=round(rig['total'].mean()),rigid_surcharge_outage=round((rig['mig'].mean()-(rig['nmig'].mean() and 0))+rig['out'].mean()),
        rigid_outage=round(rig['out'].mean()),flex_outage=round(fl['out'].mean()),
        rigid_short_share=round(short(rig),3),flex_short_share=round(short(fl),3),
        breakeven_pw=round(((rig['total']-(fl['total']-fl['prem'])).mean())/RATE,1)))
    print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv(os.path.join(RES,'results_notice.csv'),index=False)
