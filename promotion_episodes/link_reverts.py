"""Link each artifact revert (label2=='revert') to the ship commit it reverses -> revert_links.csv.
Methods, in order: (1) commit-hash in title, (2) PR number in title matching '(#N)' of an earlier commit,
(3) fallback: latest earlier commit in the same repo whose changed files overlap the revert's files
(file lists for earlier commits are fetched on demand). 'method' column records which was used."""
import csv, re, sys
from collections import defaultdict
from add_file_diffs import diff_files

def main(path="episodes.csv", out="revert_links.csv", lookback=30):
    rows = list(csv.DictReader(open(path)))
    by_repo = defaultdict(list)
    for r in rows: by_repo[r["repo"]].append(r)
    res = []
    for rv in [r for r in rows if r["label2"] == "revert"]:
        earlier = sorted((c for c in by_repo[rv["repo"]] if c["date"] < rv["date"]),
                         key=lambda c: c["date"], reverse=True)
        t = rv["title"]; target = method = None
        for h in re.findall(r"\b[0-9a-f]{7,40}\b", t):
            m = [c for c in earlier if c["commit_id"].startswith(h)]
            if m: target, method = m[0], "hash"; break
        if not target:
            own = re.findall(r"\(#(\d+)\)\s*$", t)  # this commit's own PR number
            for n in re.findall(r"(?:PR|pull request|#)\s*#?(\d+)", t, re.I):
                if n in own: continue
                m = [c for c in earlier if re.search(rf"\(#{n}\)\s*$", c["title"])]
                if m: target, method = m[0], "pr_number"; break
        rfiles = set(rv["files"].split(";")) if rv["files"] else set()
        if not target and rfiles:
            for c in earlier[:lookback]:
                files = set(c["files"].split(";")) if c["files"] else set(diff_files(c["repo"], c["commit_id"]) or [])
                if files & rfiles: target, method = c, "file_overlap"; break
        if not target: method = "unlinked"
        days = (int(__import__("datetime").datetime.fromisoformat(rv["date"].replace("Z", "+00:00")).timestamp())
                - int(__import__("datetime").datetime.fromisoformat(target["date"].replace("Z", "+00:00")).timestamp())) / 86400 if target else ""
        res.append(dict(repo=rv["repo"], revert_id=rv["commit_id"], revert_date=rv["date"], revert_title=t,
                        ship_id=target["commit_id"] if target else "", ship_date=target["date"] if target else "",
                        ship_title=target["title"] if target else "", method=method,
                        days_ship_to_revert=round(days, 1) if target else ""))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
    for r in res: print(r["method"], "|", r["repo"], "|", r["revert_title"][:40], "->", r["ship_title"][:45], "|", r["days_ship_to_revert"])

if __name__ == "__main__":
    main(*sys.argv[1:])
