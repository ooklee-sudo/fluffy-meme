"""How concentrated are applications among applicants? (firm-level feasibility)

    python applicant_counts.py "C:\\Users\\...\\ipa261008.zip" [more.zip ...]
Reads only the bibliographic part of every application in a weekly file (fast), counts applications per
applicant organization, and prints a short table to paste into the chat.
"""
import collections, io, re, sys, zipfile
import xml.etree.ElementTree as ET


def orgs_of(doc):
    end = doc.find("</us-bibliographic-data-application>")
    if end < 0:
        return None
    head = doc[: end + len("</us-bibliographic-data-application>")]
    head = re.sub(r"<!DOCTYPE[^>]*(\[[^\]]*\])?[^>]*>", "", head, count=1)
    head = re.sub(r"^<\?xml[^>]*\?>", "", head.lstrip()) + "</us-patent-application>"
    try:
        root = ET.fromstring(head)
    except ET.ParseError:
        return None
    appl = root.find(".//application-reference")
    if appl is not None and appl.get("appl-type") not in (None, "utility"):
        return None
    names = []
    for a in root.findall(".//us-applicants/us-applicant"):
        ab = a.find(".//addressbook")
        org = ab.findtext("orgname") if ab is not None else None
        names.append((org or "").strip().upper())
    return [n for n in names if n] or ["(individual)"]


def main():
    for path in sys.argv[1:]:
        z = zipfile.ZipFile(path)
        name = [n for n in z.namelist() if n.lower().endswith((".xml", ".txt"))][0]
        stream = io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
        cnt, n_docs, buf = collections.Counter(), 0, []
        def flush(buf):
            nonlocal n_docs
            r = orgs_of("".join(buf)) if buf else None
            if r:
                n_docs += 1
                cnt[r[0]] += 1          # first-named applicant
        for line in stream:
            if line.startswith("<?xml") and buf:
                flush(buf); buf = []
            buf.append(line)
        flush(buf)
        orgs = {k: v for k, v in cnt.items() if k != "(individual)"}
        total_org = sum(orgs.values())
        print(f"\n## {path.split(chr(92))[-1]}: {n_docs} utility applications, {len(orgs)} distinct applicant organizations, "
              f"{cnt.get('(individual)', 0)} individual applicants")
        for t in (5, 10, 20, 50):
            big = [v for v in orgs.values() if v >= t]
            print(f"- organizations with at least {t} applications in the week: {len(big)} ({100 * sum(big) / max(1, n_docs):.1f}% of applications)")
        print("- top 10 applicants (weekly application counts): " + ", ".join(f"{k.title()[:28]} {v}" for k, v in cnt.most_common(10)))


if __name__ == "__main__":
    main()
