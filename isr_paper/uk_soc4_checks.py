"""Robustness for uk_soc4_event_study: individual occupations, leave-one-out, placebo design occupations, rank among all occupations."""
import numpy as np, pandas as pd
import uk_soc4_event_study as U
S,ok,pool,r,G=U.S,U.ok,U.pool,U.r,U.G
base=U.base
def d(t,date): return np.log(S.loc[t,pd.Timestamp(date)])-np.log(S.loc[t,base])
dates={"Y1 Jul22-Jun23":"2023-06-01","Y3 Jul24-Jun25":"2025-06-01","Y4 Jul25-Jun26":"2026-06-01"}
print("\nIndividual occupations: ln change vs base; (rank among",len(pool)+len(sum(G.values(),[])),"occupations, 1 = largest fall)")
allt=pool+sum(G.values(),[])
for dn,dt in dates.items():
    vals=pd.Series({t:d(t,dt) for t in allt}); rk=vals.rank()
    print(" ",dn,"| control median %+.3f"%vals[pool].median())
    for g,l in G.items():
        print("    ",g.ljust(7),", ".join(f"{t} {r.loc[t,'label'][:28]} {vals[t]:+.2f} (#{int(rk[t])})" for t in l))
# leave-one-out for PROD (all-pool)
print("\nLeave-one-occupation-out, PROD minus controls (all pool):")
for dn,dt in dates.items():
    vals=pd.Series({t:d(t,dt) for t in allt}); out={}
    for drop in G["PROD"]: out[drop]=round(float(vals[[t for t in G["PROD"] if t!=drop]].mean()-vals[pool].mean()),3)
    print(" ",dn,out)
# placebo: physical/product design and craft-like creative occupations not targeted by image generators
PLAC=[t for t in ["3421","3422","3429"] if t in r.index and ok.get(t,False)]
print("\nPlacebo design occupations (interior, clothing/fashion, other design):",[(t,r.loc[t,'label'][:30]) for t in PLAC])
for dn,dt in dates.items():
    vals=pd.Series({t:d(t,dt) for t in allt+PLAC}); print(" ",dn,"placebo minus controls %+.3f"%(vals[PLAC].mean()-vals[pool].mean()))
