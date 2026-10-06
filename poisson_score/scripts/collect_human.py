"""Collect human-authored papers published before the LLM era (default < 2022-11-01).

  python scripts/collect_human.py --out data/human --n-pmc 20 --n-arxiv 20 --email you@uni.ac.kr

PMC: open-access full text via NCBI E-utilities (abstract + intro + discussion).
arXiv: IDs via the arXiv API, full text via ar5iv HTML (not every paper converts; skipped if it fails).
Writes <id>.txt and meta.csv (id, source, field, title, abstract). Sampling is random within field.
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from lxml import html as LH

CUTOFF = "2022/10/31"
ARXIV_CATS = {"cs": "cs.CL", "physics": "physics.soc-ph", "econ": "econ.GN", "stat": "stat.ML"}
PMC_TERMS = {"biomedicine": "open access[filter] AND journal article[pt]"}
HEAD = {"User-Agent": "poisson-score-research/0.1"}


def get(url, **kw):
    for i in range(4):
        r = requests.get(url, headers=HEAD, timeout=60, **kw)
        if r.status_code == 200:
            return r
        time.sleep(2 ** i)
    r.raise_for_status()


def pmc_sample(n, email, seed):
    q = f'({PMC_TERMS["biomedicine"]}) AND ("2015/01/01"[PDAT] : "{CUTOFF}"[PDAT])'
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = get(base + "esearch.fcgi", params={"db": "pmc", "term": q, "retmax": 0, "retmode": "json", "email": email})
    total = int(r.json()["esearchresult"]["count"])
    rng = random.Random(seed)
    ids = []
    for start in rng.sample(range(min(total, 9000)), min(n * 3, 9000)):
        r = get(base + "esearch.fcgi", params={"db": "pmc", "term": q, "retstart": start, "retmax": 1,
                                                "retmode": "json", "email": email})
        ids += r.json()["esearchresult"]["idlist"]
        time.sleep(0.34)
        if len(ids) >= n * 3:
            break
    out = []
    for pid in ids:
        x = get(base + "efetch.fcgi", params={"db": "pmc", "id": pid, "retmode": "xml", "email": email}).content
        time.sleep(0.34)
        try:
            root = ET.fromstring(x)
        except ET.ParseError:
            continue
        title = " ".join(root.findtext(".//article-title", "").split())
        abstract = " ".join("".join(root.find(".//abstract").itertext()).split()) if root.find(".//abstract") is not None else ""
        parts = [abstract]
        for sec in root.iter("sec"):
            st = (sec.findtext("title") or "").lower()
            if any(k in st for k in ("introduction", "background", "discussion")):
                parts.append(" ".join("".join(p.itertext()) for p in sec.findall("p")))
        text = re.sub(r"\s+", " ", " ".join(parts)).strip()
        if len(text.split()) >= 1200:
            out.append((f"pmc{pid}", "pmc", "biomedicine", title, abstract, text))
        if len(out) >= n:
            break
    return out


def arxiv_sample(n, seed):
    per = max(1, n // len(ARXIV_CATS)) + 1
    rng = random.Random(seed)
    out = []
    for field, cat in ARXIV_CATS.items():
        q = f"cat:{cat} AND submittedDate:[201501010000 TO 202210312359]"
        got = []
        offs = rng.sample(range(0, 3000), per * 4)
        for off in offs:
            r = get("https://export.arxiv.org/api/query",
                    params={"search_query": q, "start": off, "max_results": 1})
            time.sleep(3)  # arXiv API etiquette
            e = ET.fromstring(r.content)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            ent = e.find("a:entry", ns)
            if ent is None:
                continue
            aid = ent.findtext("a:id", "", ns).rsplit("/abs/", 1)[-1]
            title = " ".join(ent.findtext("a:title", "", ns).split())
            abstract = " ".join(ent.findtext("a:summary", "", ns).split())
            try:
                page = LH.fromstring(get(f"https://ar5iv.labs.arxiv.org/html/{aid}").content)
            except Exception:
                continue
            paras = [" ".join(p.text_content().split()) for p in page.xpath("//article//p")]
            text = " ".join([abstract] + paras)
            if len(text.split()) >= 1200:
                got.append((f"arxiv{aid.replace('/', '_')}", "arxiv", field, title, abstract, text))
            if len(got) >= per:
                break
        out += got
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/human")
    ap.add_argument("--n-pmc", type=int, default=20)
    ap.add_argument("--n-arxiv", type=int, default=20)
    ap.add_argument("--email", required=True, help="contact email for NCBI")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = (pmc_sample(a.n_pmc, a.email, a.seed) if a.n_pmc else []) + \
           (arxiv_sample(a.n_arxiv, a.seed) if a.n_arxiv else [])
    with open(out / "meta.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "source", "field", "title", "abstract"])
        for i, s, fl, t, ab, text in rows:
            (out / f"{i}.txt").write_text(text)
            w.writerow([i, s, fl, t, ab])
    print(f"wrote {len(rows)} documents to {out}")


if __name__ == "__main__":
    main()
