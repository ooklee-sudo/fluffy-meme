"""Wikimedia hourly projectviews dumps for the trust-shock analysis (Table 15, Figure 5):
every day of April-July 2023 and April-July 2024, four U.S.-daytime hours (14, 17, 20, 23 UTC),
27 editions, desktop vs. mobile web. Output: data/trust/hours.csv (included in the package; ~1.7 MB).
976 dump files; about 10-15 minutes in the original session. Resumable."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, time, os, pandas as pd
LANG=["en","de","fr","es","it","ja","pt","pl","nl","ru","sv","cs","ko","zh","ar","tr","vi","id","fa","uk","he","hu","fi","da","no","ro","el"]
UA={"User-Agent":UA_STRING}
TRUST=ROOT/"data"/"trust"; TRUST.mkdir(parents=True, exist_ok=True)
out=TRUST/"hours.csv"; done=set()
if os.path.exists(out): done=set(pd.read_csv(out).stamp.unique())
f=open(out,"a")
if not done: f.write("stamp,lang,platform,views\n")
days=list(pd.date_range("2024-04-01","2024-07-31"))+list(pd.date_range("2023-04-01","2023-07-31"))
for d in days:
    for h in [14,17,20,23]:
        st=f"{d:%Y%m%d}-{h:02d}0000"
        if st in done: continue
        u=f"https://dumps.wikimedia.org/other/pageviews/{d:%Y}/{d:%Y-%m}/projectviews-{st}"
        r=None
        for k in range(5):
            try:
                r=requests.get(u,headers=UA,timeout=60)
                if r.status_code==200: break
            except Exception: pass
            time.sleep(4*(k+1))
        if r is None or r.status_code!=200: print("miss",st,flush=True); continue
        for line in r.text.splitlines():
            p=line.split(" ")
            if len(p)>=3:
                code=p[0].split(".")
                if code[0] in LANG and len(code)<=2 and code[-1] in (code[0],"m"):
                    f.write(f"{st},{code[0]},{'mobile' if code[-1]=='m' else 'desktop'},{p[2]}\n")
        f.flush(); time.sleep(0.15)
    print("day",d.date(),flush=True)
