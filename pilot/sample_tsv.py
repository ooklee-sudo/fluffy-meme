"""Shrink a huge PatentsView long-text TSV (or .zip) to a small random sample, locally.

Run this on your own computer, then upload the small output file.
    python sample_tsv.py pg_detail_desc_text_2021.tsv.zip desc_2021_sample.tsv.gz --n 3000
    python sample_tsv.py pg_brf_sum_text_2021.tsv.zip brf_2021_sample.tsv.gz --n 3000 --ids desc_2021_sample.tsv.gz

Keeps n random applications (reservoir sampling, one streaming pass) and, for each,
a random window of --window characters of the text, so the output stays a few
tens of MB. With --ids, keeps exactly the applications present in that sample file.
"""
import argparse, csv, gzip, io, random, re, sys, zipfile

csv.field_size_limit(sys.maxsize)


def open_text(path, mode="r"):
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = [n for n in z.namelist() if n.endswith((".tsv", ".txt"))][0]
        return io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace", newline="")
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8", errors="replace", newline="")
    return open(path, mode, encoding="utf-8", errors="replace", newline="")


def window(text, size, rng):
    if len(text) <= size:
        return text
    start = rng.randrange(len(text) - size)
    m = re.search(r"\s", text[start:start + 200])
    start += m.end() if m else 0
    return text[start:start + size]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--window", type=int, default=30000)
    ap.add_argument("--ids", help="sample file whose pgpub_ids to keep (overrides --n)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    keep = None
    if a.ids:
        keep = {r["pgpub_id"] for r in csv.DictReader(open_text(a.ids), delimiter="\t")}
    r = csv.DictReader(open_text(a.src), delimiter="\t")
    text_col = [c for c in r.fieldnames if c.endswith("_text")][0]
    res, seen = [], 0
    for row in r:
        if keep is not None:
            if row["pgpub_id"] in keep:
                row[text_col] = window(row[text_col], a.window, rng); res.append(row)
            continue
        seen += 1
        if len(res) < a.n:
            res.append(row)
        else:
            j = rng.randrange(seen)
            if j < a.n:
                res[j] = row
    with open_text(a.dst, "w") as f:
        w = csv.DictWriter(f, r.fieldnames, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for row in res:
            if keep is None:
                row[text_col] = window(row[text_col], a.window, rng)
            w.writerow(row)
    print(f"wrote {len(res)} rows to {a.dst}")


if __name__ == "__main__":
    main()
