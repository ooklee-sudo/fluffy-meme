import csv, json, os, random, tempfile
import build_chunks as bc

d = tempfile.mkdtemp(); rng = random.Random(0)
sent = "The device comprises a housing and a sensor coupled to the housing. "
with open(f"{d}/desc.tsv", "w", newline="") as f, open(f"{d}/meta.tsv", "w", newline="") as g:
    w = csv.writer(f, delimiter="\t"); m = csv.writer(g, delimiter="\t")
    w.writerow(["pgpub_id", "description_text"]); m.writerow(["pgpub_id", "filing_date"])
    for i in range(200):
        year = rng.choice([2017, 2019, 2021, 2023])
        w.writerow([f"p{i}", "[0001] " + sent * rng.randint(100, 400)])
        m.writerow([f"p{i}", f"{year}-0{rng.randint(1,9)}-15"])
out = f"{d}/chunks.jsonl"
bc.main(["--desc", f"{d}/desc.tsv", "--meta", f"{d}/meta.tsv", "--out", out, "--n", "50"])
rows = [json.loads(l) for l in open(out)]
assert len(rows) == 50 and len({r["id"] for r in rows}) == 50
assert all("2018" <= r["filing_date"][:4] and r["filing_date"] < "2022-11-30" for r in rows)
assert all(len(r["text"].split()) >= 500 and "[0001]" not in r["text"] for r in rows)
print("OK")
