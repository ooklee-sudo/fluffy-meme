import sys; sys.path.insert(0,".")
import json,glob,numpy as np,pandas as pd
def cal(r):
    m=pd.Timestamp(r['fiscal_quarter_end'])-pd.Timedelta(days=45); return f"Q{m.quarter} {m.year}"
D={}
for f in sorted(glob.glob('../oi_tracker/chains2022/*.json'))+sorted(glob.glob('chains/*.json')):
    t=f.split('/')[-1][:-5]
    for r in json.load(open(f)):
        if r['comps_pct'] is not None: D.setdefault(t,{}).setdefault(cal(r),r['comps_pct'])   # first source wins (2022 file for <=2022; chains for rest)
QS=["Q4 2021"]+[f"Q{q} {y}" for y in range(2022,2026) for q in range(1,5)]+["Q1 2026","Q2 2026"]
P=pd.DataFrame(D).reindex(QS).astype(float); M=P.MCD; O=P.drop(columns="MCD")
print(M.round(1).to_dict())
dM=M.diff(); res={}
ref=dM.loc["Q2 2022":"Q4 2025"]; res["M1_2026Q2"]=dict(delta=float(dM["Q2 2026"]),rank_from_lowest=int(1+(ref.values<dM["Q2 2026"]).sum()),n_ref=len(ref),p_onesided=float(np.mean(list(ref.values)+[dM["Q2 2026"]]<=dM["Q2 2026"]+1e-12)))
ref2=dM.loc["Q2 2023":"Q4 2025"]; res["M1_2022Q2"]=dict(delta=float(dM["Q2 2022"]),rank_from_lowest=int(1+(ref2.values<dM["Q2 2022"]).sum()),n_ref=len(ref2))
dO=O.diff(); Rt=dM-dO.mean(axis=1); refR=Rt.loc["Q2 2023":"Q4 2025"]
sd=dO.loc["Q2 2026"].std()
res["M2_2026Q2"]=dict(R=float(Rt["Q2 2026"]),rank_from_lowest=int(1+(refR.values<Rt["Q2 2026"]).sum()),n_ref=len(refR),p_onesided=float(np.mean(list(refR.values)+[Rt["Q2 2026"]]<=Rt["Q2 2026"]+1e-12)),z_vs_peer_cross_section=float((dM["Q2 2026"]-dO.loc["Q2 2026"].mean())/sd),peer_mean_delta=float(dO.loc["Q2 2026"].mean()),peer_sd=float(sd))
res["M2_2022Q2"]=dict(R=float(Rt["Q2 2022"]),peer_mean=float(dO.loc["Q2 2022"].mean()))
st=M+M.shift(4)
res["M3"]=dict(yoy_change_2026Q2=float(M["Q2 2026"]-M["Q2 2025"]),yoy_change_2026Q1=float(M["Q1 2026"]-M["Q1 2025"]),stack_2026Q1=float(st["Q1 2026"]),stack_2026Q2=float(st["Q2 2026"]),stack_change=float(st["Q2 2026"]-st["Q1 2026"]),stack_series={k:round(float(v),1) for k,v in st.dropna().items()},
  peers_stack_change=float(((O+O.shift(4)).loc["Q2 2026"]-(O+O.shift(4)).loc["Q1 2026"]).mean()))
res["delta_series_MCD"]={k:round(float(v),1) for k,v in dM.dropna().items()}
json.dump(res,open("results_mcd.json","w"),indent=1); print(json.dumps(res,indent=1))
