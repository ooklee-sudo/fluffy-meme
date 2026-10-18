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

# no-meta mode: ids carry the publication year (pgpub_id like 20210012345)
with open(f"{d}/desc2.tsv", "w", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["pgpub_id", "description_length", "description_text"])
    for i in range(100):
        y = rng.choice([2016, 2019, 2022, 2023, 2024])
        w.writerow([f"{y}{i:07d}", 0, "[0001] " + sent * 200])
out2 = f"{d}/chunks2.jsonl"
bc.main(["--desc", f"{d}/desc2.tsv", "--out", out2, "--n", "20"])
r2 = [json.loads(l) for l in open(out2)]
assert r2 and all("2018" <= r["pub_year"] <= "2022" for r in r2)
print("OK no-meta")
