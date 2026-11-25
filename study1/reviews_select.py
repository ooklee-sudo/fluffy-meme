"""Study 1, step 4a: select English reviews for the sampled listings.

Usage: python reviews_select.py SAMPLE_CSV IA_DIR OUT_CSV [MAX_PER_LISTING=15] [SCAN=40]
Looks at the SCAN most recent reviews per listing, keeps English ones (langdetect), requires at
least 5 English reviews among them, and keeps up to MAX_PER_LISTING of the most recent English reviews.
"""
import sys, pandas as pd
from multiprocessing import Pool
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
KEY = {"Amsterdam": "ams", "London": "lon", "New York City": "nyc", "Tokyo": "tok"}

def lang(t):
    try: return detect(t)
    except Exception: return "xx"

def main(sample_csv, ia_dir, out, maxper=15, scan=40):
    s = pd.read_csv(sample_csv); ids = set(s.id)
    parts = []
    for city, k in KEY.items():
        for ch in pd.read_csv(f"{ia_dir}/{k}_reviews.csv.gz", chunksize=500000):
            ch = ch[ch.listing_id.isin(ids)]
            if len(ch): parts.append(ch)
    r = pd.concat(parts, ignore_index=True)
    r = r[r.comments.notna() & (r.comments.str.len() >= 20)]
    r = r.sort_values(["listing_id", "date"], ascending=[True, False]).groupby("listing_id").head(scan)
    with Pool(8) as p: r["lang"] = p.map(lang, r.comments.tolist(), chunksize=500)
    r = r[r.lang == "en"]
    cnt = r.groupby("listing_id").size()
    ok = cnt[cnt >= 5].index
    r = r[r.listing_id.isin(ok)].groupby("listing_id").head(maxper)
    r[["listing_id", "id", "date", "comments"]].to_csv(out, index=False)
    print("listings kept", r.listing_id.nunique(), "of", len(ids), "reviews", len(r))

if __name__ == "__main__":
    a = sys.argv; main(a[1], a[2], a[3], *(int(x) for x in a[4:6]))
