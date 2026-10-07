"""Collect human-authored English papers (pre-LLM era, 2015-2019) from PMC OA and arXiv.
Usage: python3 fetch_human.py --pmc 10 --arxiv 10 --out data/human.jsonl
"""
import argparse, json, random, re, subprocess, tempfile, time, os
import requests
from lxml import etree

EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SESSION = requests.Session()

def get(url, **kw):
    for i in range(4):
        try:
            r = SESSION.get(url, timeout=60, **kw)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    return None

def pmc(n, rng):
    ids = []
    for year in range(2015, 2020):
        term = f'open access[filter] AND {year}[pdat] AND journal article[pt] AND english[lang]'
        r = get(EU + "esearch.fcgi", params=dict(db="pmc", term=term, retmax=2000, retmode="json", sort="relevance"))
        if r:
            ids += r.json()["esearchresult"]["idlist"]
    rng.shuffle(ids)
    out = []
    for pid in ids:
        if len(out) >= n: break
        r = get(EU + "efetch.fcgi", params=dict(db="pmc", id=pid, retmode="xml"))
        time.sleep(0.4)
        if not r: continue
        try:
            root = etree.fromstring(r.content)
        except etree.XMLSyntaxError:
            continue
        paras = []
        for sec in root.xpath("//body//sec"):
            for p in sec.xpath("./p"):
                t = " ".join("".join(p.itertext()).split())
                if len(t) > 80: paras.append(t)
        title = " ".join("".join(root.xpath("string(//article-title)")).split())
        abstract = " ".join("".join(root.xpath("string(//abstract)")).split())
        text = "\n\n".join(paras)
        if len(text.split()) < 1500: continue
        out.append(dict(id=f"PMC{pid}", source="pubmed", field="medicine", title=title, abstract=abstract, text=text))
        print("pmc", len(out), pid, flush=True)
    return out

def arxiv(n, rng):
    cats = ["cs.LG", "cs.CL", "cs.CV", "cs.SE", "cs.DB", "cs.IR", "cs.CR", "cs.SI"]
    cands = []
    for cat in cats:
        for start in (0, 100, 200):
            q = f"cat:{cat} AND submittedDate:[201501010000 TO 201912312359]"
            r = get("https://export.arxiv.org/api/query", params=dict(search_query=q, start=start, max_results=100))
            time.sleep(3)
            if not r: continue
            root = etree.fromstring(r.content)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for e in root.xpath("//a:entry", namespaces=ns):
                aid = e.xpath("string(a:id)", namespaces=ns).split("/abs/")[-1]
                cands.append(dict(id=aid, title=" ".join(e.xpath("string(a:title)", namespaces=ns).split()),
                                  abstract=" ".join(e.xpath("string(a:summary)", namespaces=ns).split())))
    rng.shuffle(cands)
    out = []
    for c in cands:
        if len(out) >= n: break
        r = get(f"https://arxiv.org/pdf/{c['id']}")
        time.sleep(3)
        if not r: continue
        with tempfile.TemporaryDirectory() as d:
            pdf = os.path.join(d, "p.pdf")
            open(pdf, "wb").write(r.content)
            try:
                subprocess.run(["pdftotext", "-nopgbrk", pdf, pdf + ".txt"], check=True, timeout=120, capture_output=True)
                raw = open(pdf + ".txt", errors="ignore").read()
            except Exception:
                continue
        text = re.split(r"\n\s*(?:References|REFERENCES|Bibliography)\s*\n", raw)[0]
        text = re.sub(r"-\n(?=[a-z])", "", text)
        paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
        paras = [p for p in paras if len(p) > 120]
        text = "\n\n".join(paras)
        if len(text.split()) < 1500: continue
        out.append(dict(id=f"arXiv:{c['id']}", source="arxiv", field="computer_science",
                        title=c["title"], abstract=c["abstract"], text=text))
        print("arxiv", len(out), c["id"], flush=True)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmc", type=int, default=0); ap.add_argument("--arxiv", type=int, default=0)
    ap.add_argument("--out", default="data/human.jsonl"); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows = pmc(a.pmc, rng) if a.pmc else []
    rows += arxiv(a.arxiv, rng) if a.arxiv else []
    with open(a.out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", len(rows))
