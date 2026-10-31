"""Wikimedia hourly project-level pageview dumps (projectviews), four sampled hours per month
(days 5 and 19 x 08:00 and 20:00 UTC), January 2019 - September 2026, desktop vs. mobile web, per edition.
Usage:  python 10_wikimedia_projectviews_monthly.py main    -> data/raw/wiki_hours.csv       (22 editions)
        python 10_wikimedia_projectviews_monthly.py extra   -> data/raw/wiki_hours_extra.csv (hi, ms, bn)
        python 10_wikimedia_projectviews_monthly.py eu      -> data/raw/wiki_hours_eu.csv    (16 European editions)
(In the original session the 'extra' and 'eu' variants were separate copies of this script with LANG/out
changed; they are merged here behind a command-line argument.)
The Wikimedia REST pageviews API was rate-limited (HTTP 429) from our environment, so the public dumps are used.
Resumable: stamps already in the output file are skipped.
Note: in the original run, the first months of 2019 were collected with a denser grid
(days 5/12/19/26 x hours 02/08/14/20) before the grid was reduced; analysis scripts average over
whatever hours are present in each month."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, gzip, io, os, time, pandas as pd, itertools, sys
SETS={"main":(["en","de","fr","ja","ko","it","es","pt","pl","nl","sv","tr","id","vi","th","ru","fa","zh","uk","cs","he","ar"],"wiki_hours.csv"),
      "extra":(["hi","ms","bn"],"wiki_hours_extra.csv"),
      "eu":(["hu","ro","el","fi","da","bg","hr","sk","sl","lt","lv","et","no","sr","mk","sq"],"wiki_hours_eu.csv")}
LANG,outname=SETS[sys.argv[1] if len(sys.argv)>1 else "main"]
UA={"User-Agent":UA_STRING}
out=RAW/outname
done=set()
if os.path.exists(out):
    done=set(pd.read_csv(out).stamp.unique())
f=open(out,"a")
if not done: f.write("stamp,lang,platform,views\n")
for m in pd.date_range("2019-01-01","2026-09-01",freq="MS"):
    for d,h in itertools.product([5,19],[8,20]):
        st=f"{m.year}{m.month:02d}{d:02d}-{h:02d}0000"
        if st in done: continue
        u=f"https://dumps.wikimedia.org/other/pageviews/{m.year}/{m.year}-{m.month:02d}/projectviews-{st}"
        for k in range(4):
            r=requests.get(u,headers=UA,timeout=60)
            if r.status_code==200: break
            time.sleep(5*(k+1))
        if r.status_code!=200: print("miss",st,r.status_code,flush=True); continue
        for line in r.text.splitlines():
            p=line.split(" ")
            if len(p)>=3 and p[0].split(".")[0] in LANG and p[0].split(".")[-1] in (p[0].split(".")[0],"m") and len(p[0].split("."))<=2:
                f.write(f"{st},{p[0].split('.')[0]},{'mobile' if p[0].endswith('.m') else 'desktop'},{p[2]}\n")
        f.flush(); time.sleep(0.2)
    print("month",m.strftime("%Y-%m"),flush=True)
