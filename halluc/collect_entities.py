"""Sample people from Wikipedia across popularity levels; store reference text and rarity (language-edition count).

Rarity proxy = number of Wikipedia language editions with an article (Wikidata sitelinks), log-scaled later.
"""
import argparse
import random
import time

import requests

from common import DATA, write_jsonl
import os

API = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
HDR = {"User-Agent": "halluc-pilot/0.1 (research; ooklee@hanyang.ac.kr)"}
CATS = ["American male film actors", "English footballers", "American novelists", "German politicians",
        "Indian cricketers", "French painters", "Japanese musicians", "Canadian ice hockey players",
        "Australian academics", "Brazilian footballers", "American physicists", "Italian composers"]


def get(url, **p):
    p["format"] = "json"
    for k in range(6):
        r = requests.get(url, params=p, headers=HDR, timeout=60)
        try:
            return r.json()
        except ValueError:
            print(f"  non-JSON ({r.status_code}): {r.text[:80]!r}; retry {k}")
            time.sleep(3 * 2 ** k)
    raise RuntimeError("API keeps failing: " + url)


def members(cat, n, rng):
    out, cont = [], {}
    while len(out) < 1500:
        d = get(API, action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="page", cmlimit=500, **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d:
            break
        cont = d["continue"]
    rng.shuffle(out)
    return out[:n]


def sitelinks(titles):
    res = {}
    for i in range(0, len(titles), 50):
        d = get(WD, action="wbgetentities", sites="enwiki", titles="|".join(titles[i:i + 50]), props="sitelinks")
        for e in d.get("entities", {}).values():
            t = e.get("sitelinks", {}).get("enwiki", {}).get("title")
            if t:
                res[t] = sum(1 for k in e["sitelinks"] if k.endswith("wiki") and k not in ("commonswiki", "specieswiki", "metawiki", "wikidatawiki"))
    return res


def extracts(titles):
    res = {}
    for i in range(0, len(titles), 20):
        d = get(API, action="query", prop="extracts", explaintext=1, exlimit=20, titles="|".join(titles[i:i + 20]))
        for p in d["query"]["pages"].values():
            if "extract" in p:
                res[p["title"]] = p["extract"]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cat", type=int, default=25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(DATA, "entities.jsonl"))
    a = ap.parse_args()
    rng = random.Random(a.seed)
    titles = []
    for c in CATS:
        titles += members(c, a.per_cat, rng)
    titles = sorted(set(titles))
    sl = sitelinks(titles)
    ex = extracts(titles)
    rows = [{"title": t, "sitelinks": sl[t], "reference": ex[t][:15000]} for t in titles
            if t in sl and t in ex and len(ex[t]) > 300]
    write_jsonl(a.out, rows)
    n = sorted(r["sitelinks"] for r in rows)
    print(f"{len(rows)} entities; sitelinks min/median/max = {n[0]}/{n[len(n)//2]}/{n[-1]}")


if __name__ == "__main__":
    main()
