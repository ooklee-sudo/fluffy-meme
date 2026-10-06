"""Collect English-language Information Systems (IS) papers that have a legal open-access copy.

  python scripts/collect_is.py --out data/is_human --n 50 --email you@uni.ac.kr

Pipeline (no API keys needed): Crossref lists articles of IS journals (by ISSN, published before
2022-11) -> random sample -> Unpaywall finds a legal OA PDF (publisher or repository/preprint)
-> pdftotext -> body cleanup (drops references, headers, hyphenation) -> keep if >= --min-words.
meta.csv records DOI, journal, year, OA status and OA *version* (published/accepted/submitted).
Preprint versions can differ in wording from the published paper: report this, or filter
on --versions publishedVersion,acceptedVersion.
Texts are for local feature extraction; do not redistribute them (copyright).
Requires: poppler's `pdftotext` on PATH.
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import subprocess
import tempfile
import time
from pathlib import Path

import requests

JOURNALS = {  # ISSN -> name (print ISSN as registered with Crossref)
    "0276-7783": "MIS Quarterly", "1047-7047": "Information Systems Research",
    "0742-1222": "J. Management Information Systems", "1536-9323": "J. Association for Information Systems",
    "1529-3181": "Communications of the AIS", "0960-085X": "European J. Information Systems",
    "1350-1917": "Information Systems J.", "0963-8687": "J. Strategic Information Systems",
    "0268-3962": "J. Information Technology", "0378-7206": "Information & Management",
    "0167-9236": "Decision Support Systems",
}
HEAD = {"User-Agent": "poisson-score-research/0.1"}
UNTIL = "2022-10-31"


def get_json(url, **kw):
    for i in range(4):
        r = requests.get(url, headers=HEAD, timeout=60, **kw)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 ** i)
    return None


def crossref_candidates(issn, year_from, email, cap):
    out, cursor = [], "*"
    while len(out) < cap:
        j = get_json(f"https://api.crossref.org/journals/{issn}/works", params={
            "filter": f"type:journal-article,from-pub-date:{year_from},until-pub-date:{UNTIL}",
            "rows": 200, "cursor": cursor, "mailto": email, "select": "DOI,title,issued"})
        if not j or not j["message"]["items"]:
            break
        for it in j["message"]["items"]:
            if it.get("title") and it.get("issued", {}).get("date-parts", [[None]])[0][0]:
                out.append(it)
        cursor = j["message"]["next-cursor"]
    return out


def clean_pdf_text(raw: str) -> str:
    raw = raw.replace("\f", "\n")
    raw = re.sub(r"-\n(?=[a-z])", "", raw)                       # de-hyphenate
    head = re.search(r"^\s*(abstract|(1\.?\s*)?introduction)\s*$", raw[:25000], re.I | re.M)
    if head:
        raw = raw[head.start():]                                    # skip cover page / repository boilerplate
    m = list(re.finditer(r"\n\s*(references|bibliography|works cited)\s*\n", raw, re.I))
    if m:
        raw = raw[: m[-1].start()]                                 # cut at last "References"
    lines = [l.strip() for l in raw.split("\n")]
    lines = [l for l in lines if len(l.split()) >= 6]             # drops headers, page numbers, table debris
    return re.sub(r"\s+", " ", " ".join(lines))


def english_ratio(t: str) -> float:
    w = re.findall(r"[A-Za-z]+", t)
    return sum(x.lower() in {"the", "of", "and", "to", "in", "is", "that", "for"} for x in w) / max(1, len(w))


def fetch_text(url):
    r = requests.get(url, headers=HEAD, timeout=90)
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(r.content); f.flush()
        p = subprocess.run(["pdftotext", "-enc", "UTF-8", f.name, "-"], capture_output=True, timeout=120)
    return clean_pdf_text(p.stdout.decode("utf-8", "ignore")) if p.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/is_human")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--email", required=True)
    ap.add_argument("--issn", nargs="*", default=list(JOURNALS))
    ap.add_argument("--year-from", type=int, default=2010)
    ap.add_argument("--min-words", type=int, default=1500)
    ap.add_argument("--versions", default="publishedVersion,acceptedVersion,submittedVersion")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    ok_versions = set(a.versions.split(","))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)

    pool = []
    for issn in a.issn:
        c = crossref_candidates(issn, a.year_from, a.email, cap=1500)
        for it in c:
            it["_issn"] = issn
        print(f"{JOURNALS.get(issn, issn)}: {len(c)} candidates")
        pool += c
    rng.shuffle(pool)

    kept, tried = [], 0
    for it in pool:
        if len(kept) >= a.n or tried > a.n * 40:
            break
        tried += 1
        doi = it["DOI"]
        u = get_json(f"https://api.unpaywall.org/v2/{doi}", params={"email": a.email})
        time.sleep(0.12)
        if not u or not u.get("is_oa"):
            continue
        loc = next((l for l in u.get("oa_locations", []) if l.get("url_for_pdf") and l.get("version") in ok_versions), None)
        if not loc:
            continue
        try:
            text = fetch_text(loc["url_for_pdf"])
        except Exception:
            continue
        if not text or len(text.split()) < a.min_words or english_ratio(text) < 0.04:
            continue
        sid = "is_" + re.sub(r"[^A-Za-z0-9]+", "_", doi)
        (out / f"{sid}.txt").write_text(text)
        kept.append((sid, doi, JOURNALS.get(it["_issn"], it["_issn"]), it["issued"]["date-parts"][0][0],
                     it["title"][0], u.get("oa_status"), loc["version"], len(text.split())))
        print(f"  [{len(kept)}/{a.n}] {doi} ({loc['version']}, {len(text.split())} words)")

    with open(out / "meta.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "doi", "journal", "year", "title", "oa_status", "oa_version", "n_words"])
        w.writerows(kept)
    print(f"wrote {len(kept)} documents to {out}")


if __name__ == "__main__":
    main()
