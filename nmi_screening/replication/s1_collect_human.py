"""Step 1: sample human-written papers from 2015-2019 (before LLMs were common in scientific writing).
Medicine: Europe PMC open-access full-text XML (random PMCIDs). Computer science: arXiv PDFs (random IDs, cs.* primary)
converted to text. Keeps papers with at least 1,500 words. Output: data/human.jsonl (id, source, title, abstract, text).
python3 s1_collect_human.py --pmc 330 --arxiv 220
"""
import argparse, json, os, random, re, subprocess, sys, tempfile, time
import xml.etree.ElementTree as ET
from common import *

def pmc_try(pmcid):
    x = http(f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{pmcid}/fullTextXML", timeout=40, tries=2)
    if not x or "<article" not in x: return None
    try: root = ET.fromstring(x)
    except ET.ParseError: return None
    yr = None
    for pd in root.iter("pub-date"):
        y = pd.findtext("year")
        if y and y.isdigit(): yr = int(y); break
    if yr is None or not (2015 <= yr <= 2019): return None
    lang = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("lang") or "en"
    if not lang.startswith("en"): return None
    body = root.find(".//body")
    if body is None: return None
    for tag in ("table-wrap", "fig", "table", "disp-formula", "supplementary-material"):
        for parent in body.iter():
            for ch in list(parent):
                if ch.tag == tag: parent.remove(ch)
    paras = ["".join(p.itertext()).strip() for p in body.iter("p")]
    text = "\n\n".join(re.sub(r"\s+", " ", p) for p in paras if p)
    title = "".join(root.find(".//article-title").itertext()).strip() if root.find(".//article-title") is not None else ""
    ab = root.find(".//abstract"); abstract = re.sub(r"\s+", " ", "".join(ab.itertext())).strip() if ab is not None else ""
    if words(text) < 1500 or not title or not abstract: return None
    return dict(id=f"PMC{pmcid}", source="pmc", year=yr, title=title, abstract=abstract, text=text)

def arxiv_try(aid, field="(cs."):
    page = http(f"https://arxiv.org/abs/{aid}", timeout=30, tries=2)
    if not page: return None
    m = re.search(r'primary-subject">([^<]*)', page)
    if not m or field not in m.group(1): return None
    t = re.search(r'<h1 class="title[^>]*>\s*<span[^>]*>[^<]*</span>(.*?)</h1>', page, re.S)
    a = re.search(r'<blockquote class="abstract[^>]*>\s*<span[^>]*>[^<]*</span>(.*?)</blockquote>', page, re.S)
    if not t or not a: return None
    title = re.sub(r"<[^>]+>|\s+", " ", t.group(1)).strip(); abstract = re.sub(r"<[^>]+>|\s+", " ", a.group(1)).strip()
    pdf = http(f"https://arxiv.org/pdf/{aid}", timeout=90, tries=2, binary=True)
    if not pdf: return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(pdf); f.flush()
        r = subprocess.run(["pdftotext", "-nopgbrk", f.name, "-"], capture_output=True, text=True)
    txt = r.stdout
    cut = None
    for mm in re.finditer(r"(?m)^\s*(References|REFERENCES|Bibliography)\s*$", txt): cut = mm.start()
    if cut and cut > 0.4 * len(txt): txt = txt[:cut]
    txt = re.sub(r"-\n(?=[a-z])", "", txt); txt = re.sub(r"(?<![.\n:])\n(?!\n)", " ", txt); txt = re.sub(r"[ \t]+", " ", txt)
    if words(txt) < 1500: return None
    return dict(id=f"arXiv:{aid}", source="arxiv", year=2000 + int(aid[:2]), title=title, abstract=abstract, text=txt.strip())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pmc", type=int, default=330); ap.add_argument("--arxiv", type=int, default=220); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); rng = random.Random(a.seed); out = os.path.join(DATA, "human.jsonl")
    have = [json.loads(l) for l in open(out)] if os.path.exists(out) else []
    seen = {h["id"] for h in have}
    n_pmc = sum(h["source"] == "pmc" for h in have); n_ar = sum(h["source"] == "arxiv" for h in have)
    f = open(out, "a"); tries = 0
    while n_pmc < a.pmc:
        pid = rng.randint(4_300_000, 6_700_000); tries += 1
        if f"PMC{pid}" in seen: continue
        r = pmc_try(pid); seen.add(f"PMC{pid}")
        if r: f.write(json.dumps(r) + "\n"); f.flush(); n_pmc += 1; print("pmc", n_pmc, r["id"], words(r["text"]), f"(tries {tries})", flush=True)
        time.sleep(0.2)
    tries = 0
    while n_ar < a.arxiv:
        yy, mm = rng.randint(15, 19), rng.randint(1, 12); aid = f"{yy:02d}{mm:02d}.{rng.randint(1, 9000):05d}"; tries += 1
        if f"arXiv:{aid}" in seen: continue
        r = arxiv_try(aid); seen.add(f"arXiv:{aid}")
        if r: f.write(json.dumps(r) + "\n"); f.flush(); n_ar += 1; print("arxiv", n_ar, r["id"], words(r["text"]), f"(tries {tries})", flush=True)
        time.sleep(3.0)
