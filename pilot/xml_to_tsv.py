"""Turn a USPTO weekly application-publication XML file (ipaYYMMDD.zip) into a sampled TSV.

    python xml_to_tsv.py ipa261008.zip desc_ipa261008.tsv.gz --n 1000

Output columns (compatible with build_chunks.py / estimate_prevalence.py):
  pgpub_id (publication number, same form as PatentsView), pub_date, filing_date, appl_type, title,
  applicant_orgs/types/countries, assignee_orgs, n_inventors, agent_orgs, agent_names, cpc_main,
  description_length, description_text
Structure confirmed on ipa261008 (DTD v4.6): applicants sit under us-parties/us-applicants; the first
application had no agents element, so the printed statistics show whether agents exist at all. Documents that fail to parse are counted and skipped. DOCTYPE lines are removed
before parsing (the file is untrusted input). Tables, math and chemistry are left out of the text.
"""
import argparse, csv, gzip, io, random, re, sys, zipfile
import xml.etree.ElementTree as ET

SKIP = {"tables", "table", "maths", "math", "chemistry", "figref-dummy"}


def text_of(el, out):
    if el.tag in SKIP:
        if el.tail:
            out.append(el.tail)
        return
    if el.text:
        out.append(el.text)
    for c in el:
        text_of(c, out)
    if el.tail:
        out.append(el.tail)


def para_text(root):
    d = root.find(".//description")
    if d is None:
        return ""
    paras = []
    for p in d.iter("p"):
        buf = []
        if p.text:
            buf.append(p.text)
        for c in p:
            text_of(c, buf)
        paras.append("".join(buf).strip())
    return "\n".join(x for x in paras if x)


def first(root, path):
    e = root.find(path)
    return (e.text or "").strip() if e is not None and e.text else ""


def party_names(el):
    ab = el.find(".//addressbook") if el is not None else None
    if ab is None:
        return "", ""
    org = first(ab, "orgname")
    name = " ".join(x for x in (first(ab, "first-name"), first(ab, "last-name")) if x)
    return org, name


def parse_doc(xml):
    root = ET.fromstring(xml)
    bib = root.find(".//us-bibliographic-data-application")
    if bib is None:
        bib = root
    pub = bib.find("publication-reference/document-id")
    app = bib.find("application-reference/document-id")
    appl_type = (bib.find("application-reference").get("appl-type") if bib.find("application-reference") is not None else "") or ""
    applicants = bib.findall(".//applicants/applicant") or bib.findall(".//us-applicants/us-applicant")
    app_orgs = [party_names(a)[0] or party_names(a)[1] for a in applicants]
    app_ctry = [first(a, ".//address/country") for a in applicants]
    agents = bib.findall(".//agents/agent") or bib.findall(".//us-parties//agent")
    assignees = bib.findall(".//assignees/assignee")
    ag_orgs = [party_names(a)[0] for a in agents]
    ag_names = [party_names(a)[1] for a in agents]
    cpc = bib.find(".//classifications-cpc/main-cpc/classification-cpc")
    cpc_main = ""
    if cpc is not None:
        cpc_main = "".join(first(cpc, t) for t in ("section", "class", "subclass"))
    desc = para_text(root)
    return {
        "pgpub_id": (first(pub, "date")[:0] if pub is None else (first(pub, "doc-number") or "")),
        "pub_date": first(pub, "date") if pub is not None else "",
        "filing_date": first(app, "date") if app is not None else "",
        "appl_type": appl_type,
        "title": first(bib, "invention-title"),
        "applicant_orgs": ";".join(x for x in app_orgs if x),
        "applicant_types": ";".join("org" if party_names(a)[0] else "person" for a in applicants),
        "assignee_orgs": ";".join(x for x in (party_names(a)[0] for a in assignees) if x),
        "n_inventors": len(bib.findall(".//inventors/inventor")),
        "applicant_countries": ";".join(x for x in app_ctry if x),
        "agent_orgs": ";".join(x for x in ag_orgs if x),
        "agent_names": ";".join(x for x in ag_names if x),
        "cpc_main": cpc_main,
        "description_length": len(desc),
        "description_text": desc,
    }


def iter_docs(stream):
    buf = []
    for line in stream:
        if line.startswith("<?xml") and buf:
            yield "".join(buf)
            buf = []
        buf.append(line)
    if buf:
        yield "".join(buf)


def window(text, size, rng):
    if len(text) <= size:
        return text
    start = rng.randrange(len(text) - size)
    m = re.search(r"\s", text[start:start + 200])
    start += m.end() if m else 0
    return text[start:start + size]


def open_xml(path):
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = [n for n in z.namelist() if n.lower().endswith((".xml", ".txt"))][0]
        return io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--n", type=int, default=1000); ap.add_argument("--window", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--utility-only", action="store_true", default=True)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)
    res, seen, bad = [], 0, 0
    org_count = {}
    for xml in iter_docs(open_xml(a.src)):
        xml = re.sub(r"<!DOCTYPE[^>]*(\[[^\]]*\])?[^>]*>", "", xml, count=1)
        xml = re.sub(r"^<\?xml[^>]*\?>", "", xml.lstrip())
        try:
            rec = parse_doc(xml)
        except ET.ParseError:
            bad += 1
            continue
        if not rec["pgpub_id"] or len(rec["description_text"]) < 3000:
            continue
        if a.utility_only and rec["appl_type"] not in ("utility", ""):
            continue
        seen += 1
        first_org = (rec["applicant_orgs"].split(";")[0] or "(individual)").upper()
        rec["_org_key"] = first_org
        org_count[first_org] = org_count.get(first_org, 0) + 1
        if len(res) < a.n:
            res.append(rec)
        else:
            j = rng.randrange(seen)
            if j < a.n:
                res[j] = rec
    cols = ["pgpub_id", "pub_date", "filing_date", "appl_type", "title", "applicant_orgs", "applicant_types",
            "applicant_countries", "assignee_orgs", "n_inventors", "agent_orgs", "agent_names", "cpc_main",
            "description_length", "cpc_section", "org_week_count", "description_text"]
    opener = gzip.open(a.dst, "wt", encoding="utf-8", newline="") if a.dst.endswith(".gz") else open(a.dst, "w", encoding="utf-8", newline="")
    with opener as f:
        w = csv.DictWriter(f, cols, delimiter="\t")
        w.writeheader()
        for r in res:
            r = dict(r); r["description_text"] = window(r["description_text"], a.window, rng)
            r["cpc_section"] = r["cpc_main"][:1]
            r["org_week_count"] = 0 if r.pop("_org_key") == "(INDIVIDUAL)" else org_count[r["applicant_orgs"].split(";")[0].upper()]
            w.writerow(r)
    print(f"parsed {seen} usable applications ({bad} unparsable); wrote {len(res)} rows to {a.dst}")
    if res:
        share = lambda f: 100 * sum(bool(f(r)) for r in res) / len(res)
        print(f"  with agent/law firm : {share(lambda r: r['agent_orgs'] or r['agent_names']):5.1f}%")
        print(f"  with assignee org   : {share(lambda r: r['assignee_orgs']):5.1f}%")
        print(f"  applicant is an org : {share(lambda r: 'org' in r['applicant_types'].split(';')):5.1f}%")
        print(f"  any non-US applicant: {share(lambda r: any(c and c != 'US' for c in r['applicant_countries'].split(';'))):5.1f}%")
        print(f"  with CPC            : {share(lambda r: r['cpc_main']):5.1f}%")
        print(f"  with filing date    : {share(lambda r: r['filing_date']):5.1f}%")


if __name__ == "__main__":
    main()
