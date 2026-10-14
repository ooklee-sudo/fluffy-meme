"""Download state series from FRED (public csv endpoint). Usage: python fetch_fred.py OUTDIR"""
import sys, os, io, time, urllib.request
import pandas as pd
O = sys.argv[1]; os.makedirs(O, exist_ok=True)
ST = {"AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09","DE":"10","DC":"11","FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18","IA":"19","KS":"20","KY":"21","LA":"22","ME":"23","MD":"24","MA":"25","MI":"26","MN":"27","MS":"28","MO":"29","MT":"30","NE":"31","NV":"32","NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39","OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47","TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54","WI":"55","WY":"56"}
import subprocess
def get(sid):
    f = f"{O}/{sid}.csv"
    if os.path.exists(f) and os.path.getsize(f) > 100: return pd.read_csv(f)
    for k in range(6):
        r = subprocess.run(["curl", "-sS", "--http1.1", "-m", "40", "-L", "-A", "Mozilla/5.0 (research)", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"], capture_output=True, text=True)
        raw = r.stdout
        if raw.startswith("observation_date") or raw.startswith("DATE"): open(f, "w").write(raw); time.sleep(1.2); return pd.read_csv(io.StringIO(raw))
        time.sleep(3 * (k + 1))
    print("FAIL", sid, flush=True); return None
rows = []
for ab, fips in ST.items():
    for kind, sid in (("rest", f"SMU{fips}000007072200001"), ("nonfarm", f"SMU{fips}000000000000001"), ("pov", f"PPAA{ab}{fips}000A156NCEN"), ("inc", f"MEHOINUS{ab}A646N")):
        d = get(sid)
        if d is None: continue
        d.columns = ["date", "value"]; d["state"] = ab; d["kind"] = kind; rows.append(d)
all_ = pd.concat(rows); all_.to_csv(f"{O}/all_states.csv", index=False)
print(all_.groupby("kind").agg(n=("value", "size"), states=("state", "nunique"), last=("date", "max")))
