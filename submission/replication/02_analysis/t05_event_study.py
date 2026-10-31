"""Table 5: abnormal returns around AI events, CAR[0,+1] (and [0,+5]) in %, market model estimated on
trading days [-280,-31] (benchmark SPY; KOSPI for Naver 035420.KS). Pooled standardized CAR by event type.
Event list: data/hand_coded/event_dates.csv (identical to the list below). Events in AFTERCLOSE were released
after the U.S. close, which matters only for the Korean listing.
Input: data/raw/prices.csv. Output: output/es_results.csv.
The final block prints the GOOGL/META rows of Table 5 (session inline step)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np
from scipy import stats
P=pd.read_csv(RAW/"prices.csv",index_col=0,parse_dates=True)
R=np.log(P).diff()
events=[("2022-11-30","ChatGPT launch","S"),("2025-05-07","Apple: Safari searches fell (Cue testimony)","S"),("2026-10-29","Alphabet Q3: AI Mode lower monetization","S"),
        ("2024-05-21","Google: ads coming to AI Overviews (GML 2024)","M"),("2025-05-21","Google: ads in AI Mode, AIO desktop (GML 2025)","M"),
        ("2026-01-16","OpenAI announces ChatGPT ads","M"),("2026-02-09","ChatGPT ads go live","M"),("2026-07-23","Alphabet Q2: capex raised (control)","C")]
AFTERCLOSE=[pd.Timestamp("2026-10-29"),pd.Timestamp("2026-07-23")]
firms={"GOOGL":"SPY","META":"SPY","BIDU":"SPY","035420.KS":"^KS11"}
def car(f,mk,d0,L):
    r=R[[f,mk]].dropna()
    idx=r.index
    d0=pd.Timestamp(d0)
    pos=idx.searchsorted(d0 + (pd.Timedelta(days=1) if (f.endswith(".KS") and d0 not in AFTERCLOSE) else pd.Timedelta(0)))
    if pos+L>=len(idx): return np.nan,np.nan,None
    est=r.iloc[pos-280:pos-30]
    b,a=np.polyfit(est[mk],est[f],1); sig=(est[f]-a-b*est[mk]).std(ddof=2)
    win=r.iloc[pos:pos+L+1]
    ar=win[f]-a-b*win[mk]
    c=ar.sum(); t=c/(sig*np.sqrt(len(ar)))
    return c*100,t,idx[pos].date()
rows=[]
for d,name,cat in events:
    for f,mk in firms.items():
        for L in [1,5]:
            c,t,dd=car(f,mk,d,L)
            rows.append(dict(date=d,event=name,cat=cat,firm=f,win=f"[0,+{L}]",car=c,t=t,p=2*(1-stats.norm.cdf(abs(t)))))
df=pd.DataFrame(rows); df.to_csv(OUT/"es_results.csv",index=False)
w=df[df.win=="[0,+1]"].pivot_table(index=["cat","date","event"],columns="firm",values=["car","t"]).round(2)
pd.set_option("display.width",250); print(w)
# spread GOOGL-META
print("\nGOOGL minus META CAR[0,+1]:")
x=df[df.win=="[0,+1]"].set_index(["cat","date","firm"]).car.unstack()
print((x.GOOGL-x.META).round(2))
print("\n[0,+5]:"); print(df[df.win=="[0,+5]"].pivot_table(index=["cat","date"],columns="firm",values="car").round(2))
# pooled standardized
for cat in "SM":
    z=df[(df.win=="[0,+1]")&(df.cat==cat)&(df.firm=="GOOGL")].t
    print(cat,"GOOGL pooled Z=",round(z.sum()/np.sqrt(len(z)),2),"mean CAR",round(df[(df.win=="[0,+1]")&(df.cat==cat)&(df.firm=="GOOGL")].car.mean(),2))

# ---- Table 5 rows (GOOGL and META, CAR[0,+1])
d=pd.read_csv(OUT/"es_results.csv"); d=d[d.win=="[0,+1]"]
print(d[d.firm.isin(["GOOGL","META"])][["date","cat","firm","car","t","p"]].round(3).to_string(index=False))
