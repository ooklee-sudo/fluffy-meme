"""Extract human-written reference chunks from PatentsView pre-grant long-text tables.

Inputs (TSV, optionally .zip with one file inside; tab-separated, double-quote quoted):
  --desc   detailed-description table (one row per application)
  --meta   table with application id and filing date (and optionally an assignee/country column)
  --brief  (optional) brief-summary table, used as the 'disclosure' for the draft/expand prompts

Column names differ between releases, so they are passed explicitly or auto-detected
from common names. CONFIRM THEM against the data dictionary of the release you download;
this script has only been tested on synthetic files so far.

Only applications filed before --cutoff (default 2022-11-30) are used, one random chunk
per application, so the human corpus pre-dates ChatGPT.
"""
import argparse, csv, io, json, random, re, sys, zipfile

csv.field_size_limit(sys.maxsize)
ID_CANDIDATES = ["pgpub_id", "document_number", "publication_number", "application_id"]
TEXT_CANDIDATES = ["description_text", "detail_desc_text", "text", "summary_text", "brief_summary_text"]
DATE_CANDIDATES = ["filing_date", "application_date", "date_filed"]


def open_tsv(path):
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = [n for n in z.namelist() if n.endswith((".tsv", ".txt"))][0]
        return io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace", newline="")
    return open(path, encoding="utf-8", errors="replace", newline="")


def pick(cols, given, candidates, what):
    if given:
        if given not in cols:
            sys.exit(f"{what} column '{given}' not in {cols}")
        return given
    for c in candidates:
        if c in cols:
            return c
    sys.exit(f"Cannot detect {what} column in {cols}; pass it explicitly.")


def read_meta(path, id_col, date_col):
    f = open_tsv(path)
    r = csv.DictReader(f, delimiter="\t")
    idc = pick(r.fieldnames, id_col, ID_CANDIDATES, "meta id")
    dc = pick(r.fieldnames, date_col, DATE_CANDIDATES, "filing date")
    return {row[idc]: row[dc] for row in r}


def clean(t):
    t = re.sub(r"<[^>]+>", " ", t)                      # stray markup
    t = re.sub(r"\[\d{4}\]", " ", t)                    # paragraph numbers like [0012]
    return re.sub(r"\s+", " ", t).strip()


def chunks_of(text, target_words, min_words):
    """Split on sentence boundaries into chunks of about target_words words."""
    sents = re.split(r"(?<=[.;])\s+", text)
    out, cur, n = [], [], 0
    for s in sents:
        w = len(s.split())
        if n + w > target_words and n >= min_words:
            out.append(" ".join(cur)); cur, n = [], 0
        cur.append(s); n += w
    if n >= min_words:
        out.append(" ".join(cur))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--desc", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--brief")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=3000, help="number of chunks (one per application)")
    ap.add_argument("--cutoff", default="2022-11-30")
    ap.add_argument("--min-year", default="2018")
    ap.add_argument("--target-words", type=int, default=1100, help="~1,500 tokens")
    ap.add_argument("--min-words", type=int, default=500)
    ap.add_argument("--id-col"); ap.add_argument("--text-col"); ap.add_argument("--date-col")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    filed = read_meta(a.meta, a.id_col, a.date_col)
    eligible = {i for i, d in filed.items() if a.min_year <= d[:4] and d < a.cutoff}
    print(f"{len(eligible)} applications filed {a.min_year}..{a.cutoff}")

    briefs = {}
    if a.brief:
        r = csv.DictReader(open_tsv(a.brief), delimiter="\t")
        bi = pick(r.fieldnames, a.id_col, ID_CANDIDATES, "brief id")
        bt = pick(r.fieldnames, None, ["brief_summary_text", "summary_text", "text"], "brief text")
        for row in r:
            if row[bi] in eligible:
                briefs[row[bi]] = clean(row[bt])[:600]

    r = csv.DictReader(open_tsv(a.desc), delimiter="\t")
    idc = pick(r.fieldnames, a.id_col, ID_CANDIDATES, "desc id")
    tc = pick(r.fieldnames, a.text_col, TEXT_CANDIDATES, "desc text")
    res, seen = [], 0
    for row in r:                                         # reservoir sample, one chunk per application
        if row[idc] not in eligible:
            continue
        cs = chunks_of(clean(row[tc]), a.target_words, a.min_words)
        if not cs:
            continue
        item = {"id": row[idc], "filing_date": filed[row[idc]], "text": rng.choice(cs)}
        if row[idc] in briefs:
            item["disclosure"] = briefs[row[idc]]
        seen += 1
        if len(res) < a.n:
            res.append(item)
        else:
            j = rng.randrange(seen)
            if j < a.n:
                res[j] = item
    with open(a.out, "w") as f:
        for it in res:
            f.write(json.dumps(it) + "\n")
    print(f"wrote {len(res)} chunks from {seen} usable applications to {a.out}")


if __name__ == "__main__":
    main()
