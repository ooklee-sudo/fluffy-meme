"""Medical knowledge base for the veracity module.

Two evidence sources:
  * MedlinePlus health topics (NLM), downloaded once and indexed locally with BM25.
    Runs on CPU; no GPU memory used.
  * PubMed abstracts via NCBI E-utilities, queried live per claim (optional).

Build the local index:
    python kb.py build --out data/kb_medlineplus.jsonl
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from rank_bm25 import BM25Okapi

MEDLINEPLUS_INDEX = "https://medlineplus.gov/xml.html"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "hbm-misinfo-prototype/0.1"}

_STOP = set("""a an and are as at be but by for from has have if in into is it its of on or
that the their there these this to was were will with not no can may your you""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1]


def _get(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def build_medlineplus(out: Path, words_per_chunk: int = 120) -> int:
    page = _get(MEDLINEPLUS_INDEX).decode("utf-8", "ignore")
    m = re.search(r'href="(https://medlineplus\.gov/xml/mplus_topics_compressed_[0-9-]+\.zip)"', page)
    if not m:
        raise RuntimeError("could not find the MedlinePlus XML link")
    zf = zipfile.ZipFile(io.BytesIO(_get(m.group(1), timeout=300)))
    root = ET.fromstring(zf.read([n for n in zf.namelist() if n.endswith(".xml")][0]))
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as f:
        for t in root.findall("health-topic"):
            if t.get("language") != "English":
                continue
            title = t.get("title", "")
            aliases = [a.text for a in t.findall("also-called") if a.text]
            words = _strip_html(t.findtext("full-summary") or "").split()
            for k in range(0, len(words), words_per_chunk):
                chunk = " ".join(words[max(0, k - 20):k + words_per_chunk])  # 20-word overlap
                f.write(json.dumps({"id": f"mplus-{t.get('id')}-{k // words_per_chunk}", "source": "MedlinePlus",
                                    "title": title, "url": t.get("url"),
                                    "text": f"{title} ({'; '.join(aliases)}): {chunk}" if aliases else f"{title}: {chunk}"}) + "\n")
                n += 1
    return n


def build_scifact(corpus_parquet: Path, out: Path) -> int:
    """Index the SciFact abstract corpus (Wadden et al., 2020), one passage per abstract."""
    import ast

    import pandas as pd

    df = pd.read_parquet(corpus_parquet)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in df.itertuples():
            sents = ast.literal_eval(r.abstract) if isinstance(r.abstract, str) else list(r.abstract)
            f.write(json.dumps({"id": f"scifact-{r.doc_id}", "source": "SciFact corpus (PubMed)", "title": r.title,
                                "url": "",
                                "text": f"{r.title}: {' '.join(sents)}"[:2500]}) + "\n")
    return len(df)


class LocalKB:
    def __init__(self, path: str | Path):
        self.docs = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
        self.bm25 = BM25Okapi([tokenize(d["text"]) for d in self.docs])

    def search(self, query: str, k: int = 4) -> list[dict]:
        scores = self.bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [dict(self.docs[i], score=float(scores[i])) for i in top if scores[i] > 0]


_last_ncbi = [0.0]
_ncbi_lock = threading.Lock()


def _ncbi(url: str) -> bytes:
    """NCBI allows ~3 requests/s without an API key: space calls out and retry on errors."""
    for attempt in range(4):
        with _ncbi_lock:
            wait = 0.4 - (time.time() - _last_ncbi[0])
            if wait > 0:
                time.sleep(wait)
            _last_ncbi[0] = time.time()
        try:
            return _get(url, 30)
        except Exception:  # noqa: BLE001
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError("NCBI request failed")


def pubmed_search(query: str, k: int = 3) -> list[dict]:
    """Top-k PubMed abstracts for a claim, preferring reviews and guidelines.

    Tries the first 6 content words, then the first 4 if nothing matches.
    """
    toks = tokenize(query)
    try:
        ids = []
        for n in (6, 4):
            q = urllib.parse.quote(f"({' '.join(toks[:n])}) AND (review[pt] OR systematic[sb] OR guideline[pt])")
            res = json.loads(_ncbi(f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax={k}&sort=relevance&term={q}"))
            ids = res["esearchresult"]["idlist"]
            if ids:
                break
        if not ids:
            return []
        xml = ET.fromstring(_ncbi(f"{EUTILS}/efetch.fcgi?db=pubmed&retmode=xml&id={','.join(ids)}"))
    except Exception:  # noqa: BLE001 - PubMed is optional; fall back to local evidence
        return []
    out = []
    for art in xml.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        abstract = " ".join("".join(a.itertext()) for a in art.findall(".//AbstractText"))
        if abstract:
            out.append({"id": f"pmid-{pmid}", "source": "PubMed", "title": title,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "text": f"{title}: {abstract[:1500]}"})
    return out


if __name__ == "__main__":
    # Windows consoles (cp949 etc.) cannot show every character in Reddit text; never crash on print.
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", default="data/kb_medlineplus.jsonl")
    b.add_argument("--scifact-corpus", help="build from the SciFact corpus parquet instead of MedlinePlus")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--kb", default="data/kb_medlineplus.jsonl")
    s.add_argument("--pubmed", action="store_true")
    a = ap.parse_args()
    if a.cmd == "build":
        n = build_scifact(Path(a.scifact_corpus), Path(a.out)) if a.scifact_corpus else build_medlineplus(Path(a.out))
        print(f"wrote {n} passages to {a.out}")
    else:
        for d in LocalKB(a.kb).search(a.query) + (pubmed_search(a.query) if a.pubmed else []):
            print(f"[{d['source']}] {d['title']} {d.get('score', '')}\n  {d['text'][:200]}\n")
