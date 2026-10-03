"""Stricter revert definition + diff-inversion linking -> revert_links_v2.csv.

Revert (stricter): title STARTS with revert/rollback/undo/restore/back out (not 'Upload|Add|Create ... rollback'),
not in an archive repo, and the commit changes a non-docs artifact (needs label2=='revert' from add_file_diffs).
Link: for each revert, scan up to LOOKBACK earlier commits in the same repo; score = fraction of the candidate's
removed lines that reappear as added lines in the revert, over shared files (LFS pointer oids count, so weights work).
Pick the best-scoring candidate (score >= THRESH) -> method 'inversion'. Explicit hash/PR links are kept
and also scored. Confidence: high if score>=THRESH, else low."""
import csv, re, sys, datetime
from collections import defaultdict
import requests
S = requests.Session()
THRESH, LOOKBACK = 0.5, 50
STRICT = re.compile(r"^\s*(revert|reverting|rollback|roll back|undo|restore|back ?out)\b", re.I)
_cache = {}
DOCS = re.compile(r"\.(md|txt|png|jpg|jpeg|gif|svg|pdf)$|\.gitattributes$|LICENSE|NOTICE", re.I)

def diff_by_file(repo, sha):
    k = (repo, sha)
    if k in _cache: return _cache[k]
    r = S.get(f"https://huggingface.co/api/models/{repo}/compare/{sha}^..{sha}", timeout=60)
    out = {}
    if r.status_code == 200:
        for chunk in re.split(r"^diff --git ", r.text, flags=re.M)[1:]:
            name = re.match(r"a/(\S+) b/", chunk)
            if not name: continue
            rem = {l[1:].strip() for l in chunk.splitlines() if l.startswith("-") and not l.startswith("---")}
            add = {l[1:].strip() for l in chunk.splitlines() if l.startswith("+") and not l.startswith("+++")}
            triv = {"", "{", "}", "[", "]", "},", "],"}
            out[name.group(1)] = (rem - triv, add - triv)
    _cache[k] = out
    return out

def inversion(repo, ship_id, rev_id):
    s, r = diff_by_file(repo, ship_id), diff_by_file(repo, rev_id)
    best = 0.0
    for f in set(s) & set(r):
        if DOCS.search(f): continue  # docs/metadata files do not count as artifact inversion
        rem = s[f][0]
        if rem: best = max(best, len(rem & r[f][1]) / len(rem))
    return best

def main(files=("episodes.csv", "episodes_new.csv"), out="revert_links_v2.csv"):
    rows = []
    for f in files: rows += [dict(r, _src=f) for r in csv.DictReader(open(f))]
    by_repo = defaultdict(list)
    for r in rows: by_repo[r["repo"]].append(r)
    res = []
    for rv in rows:
        if rv["label2"] != "revert" or not STRICT.search(rv["title"]) or "archive" in rv["repo"].lower():
            continue
        earlier = sorted((c for c in by_repo[rv["repo"]] if c["date"] < rv["date"]), key=lambda c: c["date"], reverse=True)[:LOOKBACK]
        rfiles = set(diff_by_file(rv["repo"], rv["commit_id"]))
        best, bs = None, 0.0
        for c in earlier:
            sc = inversion(rv["repo"], c["commit_id"], rv["commit_id"])
            if sc > bs: best, bs = c, sc
            if sc >= 0.99: break
        ok = best is not None and bs >= THRESH
        dt = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        res.append(dict(repo=rv["repo"], sample=rv["_src"], revert_id=rv["commit_id"], revert_date=rv["date"], revert_title=rv["title"],
                        ship_id=best["commit_id"] if ok else "", ship_date=best["date"] if ok else "",
                        ship_title=best["title"] if ok else "", inversion_score=round(bs, 2),
                        linked=int(ok), days_ship_to_revert=round((dt(rv["date"]) - dt(best["date"])).total_seconds() / 86400, 1) if ok else ""))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
    print(len(res), "strict reverts;", sum(r["linked"] for r in res), "linked by inversion")
    for r in res: print(r["linked"], r["inversion_score"], "|", r["repo"][:38], "|", r["revert_title"][:42], "->", r["ship_title"][:38], "|", r["days_ship_to_revert"])

if __name__ == "__main__":
    main()
