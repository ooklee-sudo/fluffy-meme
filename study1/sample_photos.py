"""Study 1, step 2: draw a stratified listing sample and archive resized cover photos.

Usage: python sample_photos.py SAMPLE_CSV OUT_DIR [PER_CITY=1200] [SEED=20260101]
Per city: 2/3 bookable listings (price analyses need them), 1/3 other; random within strata.
Photos are downloaded, resized to a 512 px long edge, hashed (SHA-256 of the resized file, pHash)
and stored as OUT_DIR/photos/<id>.jpg. Writes OUT_DIR/sample.csv.
"""
import sys, os, io, hashlib, concurrent.futures as cf
import numpy as np, pandas as pd, requests, imagehash
from PIL import Image

def main(sample_csv, out_dir, per_city=1200, seed=20260101):
    rng = np.random.default_rng(seed)
    d = pd.read_csv(sample_csv)
    parts = []
    for city, g in d.groupby("city"):
        nb = int(per_city * 2 / 3)
        gb, go = g[g.is_bookable], g[~g.is_bookable]
        parts.append(gb.sample(min(nb, len(gb)), random_state=int(rng.integers(1e9))))
        parts.append(go.sample(min(per_city - min(nb, len(gb)), len(go)), random_state=int(rng.integers(1e9))))
    s = pd.concat(parts, ignore_index=True)
    os.makedirs(f"{out_dir}/photos", exist_ok=True)

    def fetch(row):
        path = f"{out_dir}/photos/{row.id}.jpg"
        if os.path.exists(path):
            im = Image.open(path)
        else:
            r = requests.get(row.picture_url, timeout=40); r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512))
            im.save(path, quality=88)
        return (row.id, hashlib.sha256(open(path, "rb").read()).hexdigest(), str(imagehash.phash(im)))

    res = {}
    with cf.ThreadPoolExecutor(16) as ex:
        futs = {ex.submit(fetch, r): r.id for r in s.itertuples()}
        for i, f in enumerate(cf.as_completed(futs)):
            try: res[futs[f]] = f.result()
            except Exception as e: res[futs[f]] = (futs[f], None, None)
            if i % 500 == 0: print(i, flush=True)
    s["sha256"] = s.id.map(lambda i: res[i][1]); s["phash"] = s.id.map(lambda i: res[i][2])
    bad = s.sha256.isna().sum(); print("failed photos:", bad)
    s = s[s.sha256.notna()]
    s.to_csv(f"{out_dir}/sample.csv", index=False); print("saved", len(s))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(int(x) for x in sys.argv[3:]))
