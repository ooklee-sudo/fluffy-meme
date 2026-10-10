"""Event-level text for the EDGAR 8-K experiment (direction C).

Each event is an 8-K filing; its text is the beginning of the filing's item text (from the first 'Item N.NN' heading).

    python -m semantic_hawkes.build_edgar_text fetch   # submissions (with accession numbers) + filing documents (cached)
    python -m semantic_hawkes.build_edgar_text embed   # sentence embeddings of the event texts
    python -m semantic_hawkes.build_edgar_text build   # event_text dataset (json + npy)

Uses a random subset of the S&P 500 companies already downloaded (budget: ~150 companies, ~14k filings).
Public SEC data; requests are throttled below the SEC limit.
"""
import html
import json
import os
import random
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = "semantic_hawkes/real_data/edgar"
OUT = "semantic_hawkes/real_data/edgar_text"
UA = {"User-Agent": "research ooklee@hanyang.ac.kr"}
START = "2019-01-01"
N_COMPANIES = 150
MAX_LEN = 150
MIN_EVENTS = 10
TEXT_CHARS = 1000
RATE_LOCK = threading.Lock()
LAST = [0.0]


def throttle(min_gap=0.14):  # ~7 requests/s overall
    with RATE_LOCK:
        wait = LAST[0] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        LAST[0] = time.time()


def http(url, rng=None):
    h = dict(UA)
    if rng:
        h["Range"] = rng
    err = None
    for a in range(4):
        try:
            throttle()
            return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60).read()
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 ** a)
    raise err


def companies():
    cos = json.load(open(f"{ROOT}/sp500.json"))
    have = {fn[:-5] for fn in os.listdir(f"{ROOT}/raw")}
    cos = [c for c in cos if c["CIK"].zfill(10) in have]
    random.Random(7).shuffle(cos)
    return cos[:N_COMPANIES]


def fetch_submissions():
    os.makedirs(f"{OUT}/sub", exist_ok=True)
    for c in companies():
        cik = c["CIK"].zfill(10)
        p = f"{OUT}/sub/{cik}.json"
        if os.path.exists(p):
            continue
        sub = json.loads(http(f"https://data.sec.gov/submissions/CIK{cik}.json"))
        rows = []

        def add(d):
            rows.extend(dict(zip(d.keys(), v)) for v in zip(*d.values()))

        add(sub["filings"]["recent"])
        for f in sub["filings"].get("files", []):
            if f["filingTo"] >= START:
                add(json.loads(http(f"https://data.sec.gov/submissions/{f['name']}")))
        keep = [dict(acc=r["accessionNumber"], doc=r["primaryDocument"], t=r["acceptanceDateTime"], items=r.get("items", ""))
                for r in rows if r["form"] == "8-K" and r["filingDate"] >= START]
        json.dump(dict(cik=cik, symbol=c["Symbol"], filings=keep), open(p, "w"))


def type_map():
    """Same 8 event types as the type-only EDGAR dataset (edgar-8k-filing)."""
    tr = json.load(open("semantic_hawkes/real_data/tppllm/edgar-8k-filing/train.json"))
    mp = {}
    for s in tr:
        for k, t in zip(s["type_event"], s["type_text"]):
            mp[k] = t
    code = {t[:4]: k for k, t in mp.items() if re.match(r"\d\.\d\d ", t)}
    rare = [k for k, t in mp.items() if t.startswith("Other rarely")][0]
    return code, rare, [mp[k] for k in sorted(mp)]


def events(sub):
    code, rare, _ = type_map()
    ev = []
    for r in sorted(sub["filings"], key=lambda r: r["t"]):
        codes = [c for c in r["items"].split(",") if c]
        codes = [c for c in codes if c != "9.01"] or (["9.01"] if codes else [])
        if not codes:
            continue
        ev.append(dict(acc=r["acc"], doc=r["doc"], t=r["t"], type=code.get(codes[0], rare), cik=sub["cik"]))
    return ev[-MAX_LEN:]


def extract_text(raw):
    t = re.sub(r"(?is)<ix:header>.*?</ix:header>|<script.*?</script>|<style.*?</style>", "", raw)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", " ", t))
    t = re.sub(r"\s+", " ", t)
    m = re.search(r"Item\s+\d\.\d\d", t)
    start = m.start() if m else min(1500, len(t))
    return t[start:start + TEXT_CHARS]


def fetch_docs():
    os.makedirs(OUT, exist_ok=True)
    cache_p = f"{OUT}/texts.jsonl"
    done = {}
    if os.path.exists(cache_p):
        for l in open(cache_p):
            r = json.loads(l)
            done[r["acc"]] = r
    todo = []
    for fn in sorted(os.listdir(f"{OUT}/sub")):
        sub = json.load(open(f"{OUT}/sub/{fn}"))
        ev = events(sub)
        if len(ev) >= MIN_EVENTS:
            todo += [e for e in ev if e["acc"] not in done]
    print(len(todo), "documents to fetch", flush=True)
    lock = threading.Lock()
    f = open(cache_p, "a")

    def one(e):
        url = f"https://www.sec.gov/Archives/edgar/data/{int(e['cik'])}/{e['acc'].replace('-', '')}/{e['doc']}"
        try:
            raw = http(url, "bytes=0-150000").decode("utf8", "ignore")
            text = extract_text(raw)
        except Exception as ex:  # noqa: BLE001
            text = ""
            print("FAIL", e["acc"], str(ex)[:60], flush=True)
        with lock:
            f.write(json.dumps(dict(acc=e["acc"], text=text)) + "\n")
            f.flush()

    with ThreadPoolExecutor(6) as ex:
        for i, _ in enumerate(ex.map(one, todo)):
            if i % 500 == 0:
                print(i, "/", len(todo), flush=True)


def embed():
    import torch
    from transformers import AutoModel, AutoTokenizer
    texts = {}
    for l in open(f"{OUT}/texts.jsonl"):
        r = json.loads(l)
        texts[r["acc"]] = r["text"]
    accs = sorted(texts)
    name = "sentence-transformers/all-MiniLM-L6-v2"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModel.from_pretrained(name).eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(accs), 64):
            b = tok([texts[a] or "empty" for a in accs[i:i + 64]], padding=True, truncation=True, max_length=192, return_tensors="pt")
            h = model(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).float()
            e = (h * m).sum(1) / m.sum(1)
            out.append(torch.nn.functional.normalize(e, dim=-1).numpy())
            if (i // 64) % 20 == 0:
                print("embedded", i, "/", len(accs), flush=True)
    np.save(f"{OUT}/emb.npy", np.concatenate(out).astype(np.float32))
    json.dump(accs, open(f"{OUT}/emb_accs.json", "w"))


def build():
    accs = json.load(open(f"{OUT}/emb_accs.json"))
    idx = {a: i for i, a in enumerate(accs)}
    code, rare, names = type_map()
    seqs = []
    for fn in sorted(os.listdir(f"{OUT}/sub")):
        ev = events(json.load(open(f"{OUT}/sub/{fn}")))
        ev = [e for e in ev if e["acc"] in idx]
        if len(ev) < MIN_EVENTS:
            continue
        t = [time.mktime(time.strptime(e["t"][:19], "%Y-%m-%dT%H:%M:%S")) for e in ev]
        tt = [(x - t[0]) / 86400.0 for x in t]
        seqs.append(dict(cik=ev[0]["cik"], times=tt, types=[e["type"] for e in ev], emb=[idx[e["acc"]] for e in ev]))
    rng = random.Random(2024)
    order = list(range(len(seqs)))
    rng.shuffle(order)
    n = len(order)
    split = {}
    for rank, i in enumerate(order):
        split[i] = "train" if rank < int(0.8 * n) else ("dev" if rank < int(0.9 * n) else "test")
    out = {"train": [], "dev": [], "test": []}
    for i, s in enumerate(seqs):
        out[split[i]].append(s)
    json.dump(dict(K=len(names), names=names, **out), open(f"{OUT}/dataset.json", "w"))
    print({k: (len(v), sum(len(s["times"]) for s in v)) for k, v in out.items()}, "K =", len(names))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch_submissions()
        fetch_docs()
    else:
        {"embed": embed, "build": build}[cmd]()
