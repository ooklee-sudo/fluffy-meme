"""Download each parquet part of adde023/steam-reviews, aggregate to game-month cells, delete the part.
Usage: python aggregate_steam.py WORKDIR [nworkers]   -> WORKDIR/agg/part_N.csv.gz  (not committed: large)"""
import sys, os, subprocess, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq
from multiprocessing import Pool
W = sys.argv[1]; NW = int(sys.argv[2]) if len(sys.argv) > 2 else 6
os.makedirs(f"{W}/agg", exist_ok=True); os.makedirs(f"{W}/raw", exist_ok=True)
COLS = ["appid", "timestamp_created", "steam_purchase", "received_for_free", "voted_up", "language"]
def work(i):
    out = f"{W}/agg/part_{i}.csv.gz"
    if os.path.exists(out): return i, 0
    f = f"{W}/raw/part.{i}.parquet"
    for attempt in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "600", "-L", "-f", "-o", f, f"https://huggingface.co/datasets/adde023/steam-reviews/resolve/main/part.{i}.parquet"])
        if r.returncode == 0: break
    else: return i, -1
    d = pq.read_table(f, columns=COLS).to_pandas(); os.remove(f)
    ts = pd.to_datetime(d.timestamp_created, unit="s", errors="coerce"); n_bad = int(ts.isna().sum())
    g = pd.DataFrame({"appid": d.appid, "ym": ts.dt.strftime("%Y-%m"), "sp": d.steam_purchase.fillna(-1).astype("int8"),
                      "rff": d.received_for_free.fillna(-1).astype("int8"), "up": d.voted_up.fillna(-1).astype("int8"),
                      "en": (d.language == "english").astype("int8")}).dropna(subset=["appid", "ym"])
    g.groupby(["appid", "ym", "sp", "rff", "up", "en"]).size().rename("n").reset_index().to_csv(out, index=False)
    return i, n_bad
if __name__ == "__main__":
    with Pool(NW) as p:
        for k, (i, bad) in enumerate(p.imap_unordered(work, range(663))):
            if bad != 0: print("part", i, "status", bad, flush=True)
            if k % 50 == 0: print("done", k, flush=True)
    print("ALL DONE", len(glob.glob(f"{W}/agg/*.csv.gz")), flush=True)
