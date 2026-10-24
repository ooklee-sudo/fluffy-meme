"""Stream Amazon Reviews 2023 *meta* files and keep only the products (parent_asin) found in a review sample.
The meta files are unsorted and large (GBs), so they are read as a stream and filtered on the fly; nothing but the
matching rows is stored. Keeps: title, main_category, categories, store, price, ratings, short features/description.
Usage: python tools/fetch_amazon_meta.py --sample amazon_sample.parquet --category Office_Products --out meta_Office_Products.jsonl
Cite Hou et al. (2024); do not redistribute the raw metadata."""
import argparse
import json
import re
import time

import pandas as pd
import requests

URL = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/meta_{}.jsonl"
PAT = re.compile(r'"parent_asin":\s*"([A-Z0-9]{10})"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True); ap.add_argument("--category", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = pd.read_parquet(a.sample, columns=["parent_asin", "product_category"])
    want = set(d.loc[d["product_category"] == a.category, "parent_asin"].astype(str))
    found, t0, seen = 0, time.time(), 0
    with requests.get(URL.format(a.category), stream=True, timeout=120) as r, open(a.out, "w") as f:
        r.raise_for_status()
        for line in r.iter_lines(chunk_size=1 << 20):
            seen += 1
            if not line:
                continue
            m = PAT.search(line[:200000].decode("utf8", "ignore"))
            if not m or m.group(1) not in want:
                continue
            o = json.loads(line)
            keep = {k: o.get(k) for k in ("parent_asin", "title", "main_category", "categories", "store", "price",
                                         "average_rating", "rating_number")}
            keep["features"] = (o.get("features") or [])[:6]
            keep["description"] = " ".join(o.get("description") or [])[:600]
            f.write(json.dumps(keep) + "\n")
            found += 1
            want.discard(m.group(1))
            if found % 500 == 0:
                print(f"{a.category}: found {found}, scanned {seen} lines, {time.time()-t0:.0f}s", flush=True)
    print(f"{a.category}: DONE found {found}, still missing {len(want)}, scanned {seen} lines, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
