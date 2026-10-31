"""Copies the small series transcribed from the original analysis session (data/transcribed/) to the locations
where the analysis scripts expect downloaded/derived data, so that Tables 6-9 and Figures 2-4 can be run without
re-collecting data from SEC EDGAR and StatCounter:
  data/transcribed/quarterly.csv      -> data/derived/quarterly.csv   (normally built by 01_data_collection/04_build_quarterly.py)
  data/transcribed/search_raw.csv     -> data/raw/search_raw.csv
  data/transcribed/clicks.csv         -> data/raw/clicks.csv
  data/transcribed/sc_desktop.csv     -> data/raw/sc_desktop.csv      (Date, bing only)
  data/transcribed/sc_us.csv          -> data/raw/sc_us.csv           (Date, bing only)
  data/transcribed/eurostat_*.csv     -> data/raw/
Existing files are NOT overwritten unless --force is given."""
import shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; T=ROOT/"data"/"transcribed"
(ROOT/"data"/"raw").mkdir(parents=True,exist_ok=True); (ROOT/"data"/"derived").mkdir(parents=True,exist_ok=True)
plan={"quarterly.csv":"derived","search_raw.csv":"raw","clicks.csv":"raw","sc_desktop.csv":"raw","sc_us.csv":"raw",
      "eurostat_genai_2025.csv":"raw","eurostat_daily_internet_2022.csv":"raw"}
force="--force" in sys.argv
for f,dest in plan.items():
    tgt=ROOT/"data"/dest/f
    if tgt.exists() and not force: print("exists, skipped:",tgt); continue
    shutil.copy(T/f,tgt); print("copied",f,"->",tgt.relative_to(ROOT))
