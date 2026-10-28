"""Prepare the FActScore human-annotated biographies (183 entities x InstructGPT / ChatGPT / PerplexityAI) for our judges.

Input: data/labeled/*.jsonl from the FActScore release (Min et al., 2023; downloaded separately, not stored in this repo).
Output (data/human/, git-ignored): one gen file per source with the *annotators' own sentence segmentation* (field 'sents', so
judge and human labels refer to the same sentences) and entities_human.jsonl with a Wikipedia reference text per entity.
References: reused from data/entities.jsonl when the entity is there, otherwise fetched from the live English Wikipedia API
(the annotators used the 2023-04-01 dump, so some drift is possible).
"""
import argparse
import json
import os
import time

import requests

from common import DATA, read_jsonl, write_jsonl

API = "https://en.wikipedia.org/w/api.php"
HDR = {"User-Agent": "halluc-pilot/0.1 (research; ooklee@hanyang.ac.kr)"}


def wiki_extracts(titles):
    """Plain text of many pages in few requests: wikitext (up to 50 titles per call) -> mwparserfromhell.strip_code.
    (TextExtracts returns only one full-page extract per request, which is far too slow under the rate limit.)"""
    import re

    import mwparserfromhell as mw
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        for k in range(12):
            time.sleep(1.5)
            r = requests.get(API, params=dict(action="query", prop="revisions", rvprop="content", rvslots="main", redirects=1,
                                              titles="|".join(chunk), format="json", formatversion=2), headers=HDR, timeout=90)
            if r.status_code == 429:
                w = float(r.headers.get("retry-after", 20)) + 2
                print(f"  429; waiting {w:.0f}s", flush=True)
                time.sleep(w)
                continue
            d = r.json()["query"]
            alias = {}
            for key in ("normalized", "redirects"):
                for m in d.get(key, []):
                    alias[m["from"]] = m["to"]
            pages = {}
            for p in d["pages"]:
                if p.get("revisions"):
                    wt = p["revisions"][0]["slots"]["main"]["content"]
                    pages[p["title"]] = re.sub(r"\n{3,}", "\n\n", mw.parse(wt).strip_code(normalize=True, collapse=True)).strip()
            for t in chunk:
                t2 = alias.get(t, t)
                t2 = alias.get(t2, t2)
                if pages.get(t2):
                    out[t] = pages[t2]
            break
        print(f"  wikipedia {min(i + 50, len(titles))}/{len(titles)}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True, help="folder with ChatGPT.jsonl, InstructGPT.jsonl, PerplexityAI.jsonl")
    a = ap.parse_args()
    out_dir = os.path.join(DATA, "human")
    os.makedirs(out_dir, exist_ok=True)
    topics = set()
    for src in ("InstructGPT", "ChatGPT", "PerplexityAI"):
        rows = [json.loads(l) for l in open(os.path.join(a.labeled_dir, src + ".jsonl"))]
        gens = []
        for r in rows:
            sents = [x["text"] for x in (r.get("annotations") or [])]
            if sents:
                gens.append({"title": r["topic"], "model": "human-annotated:" + src, "text": r["output"], "sents": sents})
                topics.add(r["topic"])
        write_jsonl(os.path.join(out_dir, f"gen_{src}.jsonl"), gens)
        print(src, "responses with annotations:", len(gens), "of", len(rows))
    have = {e["title"]: e for e in read_jsonl(os.path.join(DATA, "entities.jsonl"))}
    refs = {t: have[t]["reference"] for t in topics if t in have}
    print("reference reused from our entity set:", len(refs), "of", len(topics))
    missing = sorted(t for t in topics if t not in refs)
    refs.update(wiki_extracts(missing))
    ents = [{"title": t, "sitelinks": 1, "reference": refs[t][:15000]} for t in sorted(topics) if refs.get(t)]
    write_jsonl(os.path.join(out_dir, "entities_human.jsonl"), ents)
    print(f"entities with a reference: {len(ents)} of {len(topics)}; without: {sorted(t for t in topics if t not in refs)[:10]}")


if __name__ == "__main__":
    main()
