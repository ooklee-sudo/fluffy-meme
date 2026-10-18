import csv, os, random, tempfile, zipfile, subprocess, sys, gzip
import sample_tsv as st, build_chunks as bc
d = tempfile.mkdtemp(); rng = random.Random(0)
sent = "The device comprises a housing and a sensor. "
rows = [[f"2021{i:07d}", 1, "[0001] " + sent * rng.randint(2000, 3000) + "\n\nSecond paragraph; with \"quotes\"."] for i in range(300)]
p = f"{d}/pg_detail_desc_text_2021.tsv"
with open(p, "w", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["pgpub_id", "description_length", "description_text"]); w.writerows(rows)
with zipfile.ZipFile(p + ".zip", "w") as z: z.write(p, os.path.basename(p))
out = f"{d}/s.tsv.gz"
st.main([p + ".zip", out, "--n", "100"])
assert os.path.getsize(out) < os.path.getsize(p + ".zip")
bc.main(["--desc", out, "--out", f"{d}/c.jsonl", "--n", "40"])
print(len(open(f"{d}/c.jsonl").readlines()), "chunks from sampled gz")
