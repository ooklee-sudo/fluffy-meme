"""Conditional projection: when could displacement become detectable with this paper's design?
Eq. (2): aggregate log change in an occupation = A_t * beta (A_t adoption share among its employers, beta effect among adopters).
Adoption path: logit(A_t) grows linearly after 2025 at a scenario slope; slopes anchored on the Eurostat 2023-2025 growth of text-generation AI (logit slope) and any-AI.
Detection: coefficient per SD of exposure (= A_t*beta / z) must exceed 1.96 x SE, with SE = 0.017 (UK 2026, sub-major FE + LLM control) and z = 8.0 (graphic and multimedia designers).
beta is NOT identified by the data; the table is a scenario analysis, not a forecast."""
import json, numpy as np, pandas as pd
d=json.load(open("data/eurostat/isoc_eb_ai.json")); ids=d["id"]; size=d["size"]; idx={k:d["dimension"][k]["category"]["index"] for k in ids}
def get(**kw):
    n=0
    for k,s in zip(ids,size): n=n*s+idx[k][kw[k]]
    return d["value"].get(str(n))
logit=lambda p:np.log(p/(1-p)); inv=lambda x:1/(1+np.exp(-x))
for ind in ("E_AI_TNLG","E_AI_TANY"):
    s={t:get(freq="A",size_emp="GE10",nace_r2="C10-S951_X_K",indic_is=ind,unit="PC_ENT",geo="EU27_2020",time=t)/100 for t in ("2021","2023","2024","2025")}
    l={t:logit(v) for t,v in s.items()}; print(ind,{t:round(v*100,1) for t,v in s.items()},"| logit slope 2021-23 per yr: %.2f, 2023-24: %.2f, 2024-25: %.2f, 2023-25 avg: %.2f"%((l["2023"]-l["2021"])/2,l["2024"]-l["2023"],l["2025"]-l["2024"],(l["2025"]-l["2023"])/2))
SE=0.017; Z=8.0; thr=1.96*SE; print("\ndetection threshold: |b| >= %.3f per SD -> |A*beta| >= %.2f for z=%.1f"%(thr,thr*Z,Z))
slopes={"fast (0.75/yr)":0.75,"medium (0.50/yr)":0.50,"slow (0.25/yr)":0.25}
starts={"all firms 10+ (9.6% in 2025)":0.0955,"publishing, film, broadcasting (36.2% in 2025)":0.362}
betas=[-0.1,-0.3,-0.5,-0.8]; yrs=list(range(2025,2036)); rows=[]
for sn,a0 in starts.items():
    print("\n== baseline adoption:",sn)
    for kn,k in slopes.items():
        A={y:inv(logit(a0)+k*(y-2025)) for y in yrs}
        print(f" diffusion {kn}: adoption 2026-2030:",[f"{A[y]*100:.0f}%" for y in range(2026,2031)])
        for b in betas:
            need=thr*Z/abs(b); yr_=next((y for y in yrs if A[y]>=need),None)
            rows.append((sn,kn,b,round(need,3),yr_)); print(f"    beta={b:+.1f} (adopter demand {100*(np.exp(b)-1):+.0f}%): needs adoption >= {need*100:5.0f}% -> detectable from {yr_ if yr_ else 'after 2035 / never (needs >100%)' if need>1 else 'after 2035'}")
pd.DataFrame(rows,columns=["baseline","diffusion","beta","adoption_needed","first_detectable_year"]).to_csv("data/projection_detectability.csv",index=False)
# predicted aggregate log change for graphic designers (z=8) under scenarios, medium diffusion, all-firms baseline
print("\nPredicted aggregate log change for graphic and multimedia designers (z = 8), medium diffusion, 9.6% start; (per-SD coefficient in brackets):")
A={y:inv(logit(0.0955)+0.5*(y-2025)) for y in yrs}
for b in betas: print(f" beta={b:+.1f}: "+", ".join(f"{y}: {A[y]*b:+.2f} [{A[y]*b/Z:+.3f}]" for y in (2026,2028,2030)))
