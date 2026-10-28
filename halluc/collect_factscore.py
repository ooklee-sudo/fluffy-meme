"""Entities + Wikipedia reference text from the FActScore entity set (HF: dskar/FActScore), no Wikipedia API needed.

Rarity proxy = number of Wikipedia language editions (Wikidata sitelinks), fetched in ~10 Wikidata calls.
"""
import argparse
import json
import os
import time

import requests

from common import DATA, write_jsonl

SRC = "https://huggingface.co/datasets/dskar/FActScore/resolve/main/factscore_eval_20250729_222645.jsonl"
WD = "https://www.wikidata.org/w/api.php"
HDR = {"User-Agent": "halluc-pilot/0.1 (research; ooklee@hanyang.ac.kr)"}
SKIP = ("commonswiki", "specieswiki", "metawiki", "wikidatawiki", "mediawikiwiki", "wikimaniawiki")


def wd_get(**p):
    p["format"] = "json"
    for k in range(10):
        time.sleep(1.5)
        r = requests.get(WD, params=p, headers=HDR, timeout=60)
        if r.status_code == 429:
            w = float(r.headers.get("retry-after", 20)) + 2
            print(f"  429; waiting {w:.0f}s", flush=True)
            time.sleep(w)
            continue
        return r.json()
    raise RuntimeError("wikidata keeps failing")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(DATA, "entities.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    raw = requests.get(SRC, timeout=120).text.splitlines()
    rows = [json.loads(l) for l in raw if l.strip()][: a.limit or None]
    sl = {}
    for i in range(0, len(rows), 50):
        titles = [r["entity"] for r in rows[i:i + 50]]
        d = wd_get(action="wbgetentities", sites="enwiki", titles="|".join(titles), props="sitelinks", normalize=1)
        for e in d.get("entities", {}).values():
            t = e.get("sitelinks", {}).get("enwiki", {}).get("title")
            if t:
                sl[t] = sum(1 for k in e["sitelinks"] if k.endswith("wiki") and k not in SKIP)
        print(f"  {min(i + 50, len(rows))}/{len(rows)}", flush=True)
    out = [{"title": r["entity"], "sitelinks": sl[r["entity"]], "reference": r["wikipedia_text"][:15000]}
           for r in rows if r["entity"] in sl and len(r["wikipedia_text"]) > 300]
    write_jsonl(a.out, out)
    s = sorted(r["sitelinks"] for r in out)
    print(f"{len(out)} entities; sitelinks min/median/max = {s[0]}/{s[len(s)//2]}/{s[-1]}")


if __name__ == "__main__":
    main()
