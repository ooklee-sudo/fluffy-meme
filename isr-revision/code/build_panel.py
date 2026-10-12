"""Collect issues and releases from the GitHub REST API and build weekly_panel.csv and releases.csv.

    export GITHUB_TOKEN=...            # read-only token for public repos is enough
    python build_panel.py --repos sql/repo_map.csv --out data --end 2026-10-05

Outputs (schemas as in make_synthetic.py)
  releases.csv       repo, published_at, tag, is_hotfix, body
  weekly_panel.csv   repo, week (Monday), release, age, regular_release, regular_age, issues, bugs

Definitions follow Section 4.2 of the manuscript.
  - issues: created since 2023-01-01, pull requests excluded, aggregated by ISO week (Monday start)
  - bug: a label containing "bug" or a title matching BUG_RE
  - releases: non-draft, non-prerelease
  - hot-fix: version differs from the previous release only in the patch component and the release
    appears within 7 days of the previous release; regular release = not a hot-fix
  - panel: first week with a release on or after 2023-01-01 through the last complete week before --end
  - age: weeks since the last release, 1 = first week after a release, capped at 52 (same for regular_age)
Raw API responses are cached in --cache so a rerun does not refetch. Keep the cache with the data:
issues can be edited or deleted later (Section 6.3).
"""
import argparse
import json
import os
import re
import sys
import time
import http.client
import urllib.request
import urllib.error

import pandas as pd

BUG_RE = re.compile(r"\b(?:bug|error|crash|fail|wrong|incorrect|regression|broken|exception)", re.I)   # as in the first kit: no trailing word boundary
VER_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")
API = "https://api.github.com"
SINCE = "2023-01-01"


def get(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "Authorization": f"Bearer {token}",
                                               "X-GitHub-Api-Version": "2022-11-28"})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), r.headers.get("Link", "")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
                wait = max(int(e.headers.get("X-RateLimit-Reset", "0")) - time.time(), 0) + 5
                print(f"rate limit; sleeping {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
            elif e.code >= 500:
                time.sleep(2 ** attempt)
            else:
                raise
        except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError, OSError) as e:
            print(f"network error ({type(e).__name__}); retry {attempt + 1}/8", file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("giving up on " + url)


def pages(path, params, token, cache):
    if os.path.exists(cache):
        return json.load(open(cache))
    out, url = [], f"{API}{path}?per_page=100&{params}"
    while url:
        data, link = get(url, token)
        out += data
        m = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = m.group(1) if m else None
    json.dump(out, open(cache, "w"))
    return out


def is_bug(labels, title):
    return any("bug" in l["name"].lower() for l in labels) or bool(BUG_RE.search(title or ""))


def classify_hotfix(rel):
    """rel sorted by published_at with columns tag, published_at. Returns list of 0/1."""
    flags, prev_v, prev_ts = [], None, None
    for tag, ts in zip(rel.tag, rel.published_at):
        m = VER_RE.search(tag or "")
        v = tuple(int(g) if g else 0 for g in m.groups()) if m else None
        hot = int(prev_v is not None and v is not None and v[:2] == prev_v[:2]
                  and v[2] != prev_v[2] and (ts - prev_ts).days <= 7)
        flags.append(hot)
        prev_v, prev_ts = v, ts
    return flags


def build_repo(repo, token, cache_dir, end):
    key = repo.replace("/", "__")
    rels = pages(f"/repos/{repo}/releases", "", token, f"{cache_dir}/{key}_releases.json")
    rels = [r for r in rels if not r["draft"] and not r["prerelease"] and r.get("published_at")]
    R = pd.DataFrame({"repo": repo,
                      "published_at": [pd.Timestamp(r["published_at"]).tz_convert(None) for r in rels],
                      "tag": [r["tag_name"] for r in rels],
                      "body": [r.get("body") or "" for r in rels]}).sort_values("published_at").reset_index(drop=True)
    R["is_hotfix"] = classify_hotfix(R)
    iss = pages(f"/repos/{repo}/issues", f"state=all&since={SINCE}T00:00:00Z", token, f"{cache_dir}/{key}_issues.json")
    rows = [(pd.Timestamp(i["created_at"]).tz_convert(None), int(is_bug(i["labels"], i["title"])))
            for i in iss if "pull_request" not in i and i["created_at"] >= SINCE]
    I = pd.DataFrame(rows, columns=["t", "bug"])
    I["week"] = I.t.dt.to_period("W-SUN").dt.start_time
    wk = I.groupby("week").agg(issues=("bug", "size"), bugs=("bug", "sum"))

    R2 = R[R.published_at >= SINCE].copy()
    R2["week"] = R2.published_at.dt.to_period("W-SUN").dt.start_time
    if R2.empty:
        raise RuntimeError(f"{repo}: no releases since {SINCE}")
    any_w = set(R2.week)
    reg_w = set(R2.week[R2.is_hotfix == 0])
    weeks = pd.date_range(R2.week.min(), pd.Timestamp(end) - pd.Timedelta(days=7), freq="W-MON")
    out, age, rage = [], 1, 1
    for w in weeks:
        rel, reg = int(w in any_w), int(w in reg_w)
        n = wk.loc[w] if w in wk.index else None
        out.append((repo, w.date(), rel, min(age, 52), reg, min(rage, 52),
                    int(n.issues) if n is not None else 0, int(n.bugs) if n is not None else 0))
        age = 1 if rel else age + 1
        rage = 1 if reg else rage + 1
    P = pd.DataFrame(out, columns=["repo", "week", "release", "age", "regular_release", "regular_age", "issues", "bugs"])
    return P, R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", default="sql/repo_map.csv")
    ap.add_argument("--out", default="data")
    ap.add_argument("--end", required=True, help="Monday of the first week NOT in the panel, e.g. 2026-10-05")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--only", default=None, help="comma-separated repos (testing)")
    a = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("set GITHUB_TOKEN")
    cache = a.cache or os.path.join(a.out, "raw_cache")
    os.makedirs(cache, exist_ok=True)
    repos = a.only.split(",") if a.only else list(pd.read_csv(a.repos).repo)
    Ps, Rs = [], []
    for r in repos:
        print(r, file=sys.stderr)
        P, R = build_repo(r, token, cache, a.end)
        Ps.append(P)
        Rs.append(R)
    pd.concat(Ps).to_csv(os.path.join(a.out, "weekly_panel.csv"), index=False)
    pd.concat(Rs)[["repo", "published_at", "tag", "is_hotfix", "body"]].to_csv(os.path.join(a.out, "releases.csv"), index=False)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
