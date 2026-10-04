"""Back-of-envelope calibration: aggregate effect = adoption share x effect among adopters (a stylized assumption; employer-level adoption of an occupation is not observed).
Takes the dose-response coefficient (per SD of occupational creation exposure), converts to a predicted log change for specific occupations, and divides by assumed adoption shares."""
import json, numpy as np, pandas as pd
import uk_exposure as UX, classify_onet as C
t=pd.DataFrame(C.load())[["id","soc"]].merge(pd.DataFrame([json.loads(l) for l in open("data/all_creation_llm.jsonl")])[["id","s"]],on="id")
E,_=UX.uk_exposure((t.s/2).groupby(t.soc).mean().to_dict())
sd,mu=E.std(),E.mean(); occ={"2142":"graphic & multimedia designers","3411":"artists","3417":"photographers/AV operators","2141":"web design professionals"}
r=pd.read_csv("data/ons/uk_dose_response_llm.csv"); print("SD of occupational exposure: %.4f, mean %.4f (across %d UK occupations)"%(sd,mu,len(E)))
for sp in ("sub-major FE, controls L","sub-major FE, no L control"):
    print("\nSpec:",sp)
    for y in (2025,2026):
        x=r[(r.spec==sp)&(r.t==y)].iloc[0]; lo,hi=x.b_E-1.96*x.se,x.b_E+1.96*x.se
        print(f" year {y}: b={x.b_E:+.3f} (95% CI {lo:+.3f}, {hi:+.3f}) per SD")
        for s_,nm in occ.items():
            z=(E[s_]-mu)/sd; pred=x.b_E*z; worst=lo*z
            print(f"    {s_} {nm:34s} z={z:4.1f}  predicted log change {pred:+.2f} (CI lower end {worst:+.2f}) -> implied effect among adopters if adoption share = 10%: {pred/.10:+.2f} (lower end {worst/.10:+.2f}); 20%: {pred/.2:+.2f} ({worst/.2:+.2f}); 36%: {pred/.36:+.2f} ({worst/.36:+.2f})")
