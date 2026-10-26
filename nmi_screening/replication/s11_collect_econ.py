"""Step 11: a third field (economics / quantitative social science) as an out-of-field test set.
Lists arXiv econ.* papers submitted 2017-2019 through the arXiv API, samples at random, converts PDFs to text (same filters as Step 1).
python3 s11_collect_econ.py --n 130   ->  data/human_econ.jsonl
"""
import argparse, json, os, random, re, time, urllib.parse
from common import *
from s1_collect_human import arxiv_try, words

def list_ids(rng, pages=8, per=400):
    ids = []
    for p in range(pages):
        q = urllib.parse.quote("(cat:econ.GN OR cat:econ.EM OR cat:econ.TH) AND submittedDate:[201701010000 TO 201912312359]", safe=":()")
        x = http(f"http://export.arxiv.org/api/query?search_query={q}&start={p*per}&max_results={per}&sortBy=submittedDate", timeout=60, tries=3)
        if not x: break
        got = re.findall(r"<id>http://arxiv.org/abs/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?</id>", x); ids += got; print("page", p, len(got), flush=True)
        if len(got) < per: break
        time.sleep(4)
    ids = sorted(i for i in set(ids) if 17 <= int(i[:2]) <= 19); rng.shuffle(ids); return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=130); ap.add_argument("--seed", type=int, default=2); a = ap.parse_args()
    rng = random.Random(a.seed); out = os.path.join(DATA, "human_econ.jsonl")
    have = [json.loads(l) for l in open(out)] if os.path.exists(out) else []; seen = {h["id"] for h in have}; n = len(have)
    ids = list_ids(rng); print(len(ids), "candidate ids", flush=True)
    f = open(out, "a")
    for aid in ids:
        if n >= a.n: break
        if f"arXiv:{aid}" in seen: continue
        r = arxiv_try(aid, field="(econ."); seen.add(f"arXiv:{aid}")
        if r: r["source"] = "arxiv-econ"; f.write(json.dumps(r) + "\n"); f.flush(); n += 1; print(n, r["id"], words(r["text"]), flush=True)
        time.sleep(3.0)
