"""Sample every weekly file in a folder in one go.

    python make_samples.py "C:\\Users\\Mikyung Kim\\Downloads" --n 2000
For each ipaYYMMDD.zip (revision files *_r1.zip are skipped) writes week_YYMMDD.tsv.gz in the current folder;
existing outputs are skipped, so the command can be repeated after new downloads.
"""
import argparse, glob, os, re
import xml_to_tsv

ap = argparse.ArgumentParser()
ap.add_argument("folder"); ap.add_argument("--n", type=int, default=2000)
a = ap.parse_args()
for path in sorted(glob.glob(os.path.join(a.folder, "ipa*.zip"))):
    m = re.search(r"ipa(\d{6})\.zip$", path)
    if not m:
        continue
    out = f"week_{m.group(1)}.tsv.gz"
    if os.path.exists(out):
        print("skip (exists):", out); continue
    print("==", path, flush=True)
    xml_to_tsv.main([path, out, "--n", str(a.n)])
