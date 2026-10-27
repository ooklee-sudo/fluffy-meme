"""Turn fetch_releases.py output into the releases.csv that confirmatory_analysis.py reads.

Usage: python build_inputs.py releases_all.csv releases.csv [END=2026-10-11]
Drops prereleases, tags without an x.y.z version (junk/test tags) and anything after END (the end of the
ISO week of 5 Oct 2026, the last complete week in the original study). Keeps is_hotfix.
"""
import csv, re, sys

src, out = sys.argv[1:3]
end = (sys.argv[3] if len(sys.argv) > 3 else "2026-10-11") + "T23:59:59Z"
keep = dropped_pre = dropped_junk = 0
with open(src, newline="") as f, open(out, "w", newline="") as g:
    w = csv.writer(g); w.writerow(["repo", "published_at", "is_hotfix"])
    for r in csv.DictReader(f):
        if r["published_at"] > end:
            continue
        if r["is_prerelease"] == "1":
            dropped_pre += 1; continue
        if not re.search(r"\d+\.\d+\.\d+", r["tag"]):
            dropped_junk += 1; continue
        w.writerow([r["repo"], r["published_at"], r["is_hotfix"]]); keep += 1
print(f"kept {keep}, dropped prerelease {dropped_pre}, dropped tags without x.y.z {dropped_junk}")
