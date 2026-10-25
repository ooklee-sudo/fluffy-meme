"""Measure issue-label usage for the repos that pass the pilot filter.

For each repo: count issues (excluding pull requests) opened in a window around AI-config adoption,
the share carrying any label, and the share carrying a bug-like label.

Needs a GitHub token in $GITHUB_TOKEN (read-only public access is enough).
Usage: python3 collect_issue_labels.py pilot_pass_repos.csv issue_labels.csv [max_repos]
Resumable: repos already present in the output CSV are skipped.
"""
import csv
import os
import re
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

API = "https://api.github.com"
BUG = re.compile(r"\b(bug|defect|crash|regression|error|fail|broken|fault)", re.I)
TOKEN = os.environ.get("GITHUB_TOKEN")
LAST_ERROR = {"code": None}
MAX_PAGES = 15                    # 1,500 issues per repo is enough for rate estimation


def get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "isr-pilot",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                remaining = int(r.headers.get("X-RateLimit-Remaining", "1"))
                if remaining < 20:
                    reset = int(r.headers.get("X-RateLimit-Reset", "0"))
                    time.sleep(max(0, reset - time.time()) + 5)
                return json.load(r), r.headers.get("Link", "")
        except urllib.error.HTTPError as e:
            LAST_ERROR["code"] = e.code
            if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(e.headers.get("X-RateLimit-Reset", "0"))
                time.sleep(min(max(0, reset - time.time()) + 5, 3600))
            elif e.code == 403:                      # access denied, not a rate limit: do not retry
                return None, ""
            elif e.code in (401, 404, 451, 410):
                return None, ""
            else:
                time.sleep(2 ** attempt)
        except urllib.error.URLError:
            time.sleep(2 ** attempt)
    return None, ""


def month_index(ts):
    d = datetime.strptime(ts[:7], "%Y-%m")
    return d.year * 12 + d.month - 1


def collect(repo, adopt):
    a = month_index(adopt)
    row = dict(repo_name=repo, adopt=adopt, status="ok", n_issues=0, n_labeled=0, n_bug=0,
               pre_issues=0, post_issues=0, pre_bug=0, post_bug=0, n_label_defs=0, truncated=0)
    defs, _ = get(f"{API}/repos/{repo}/labels?per_page=100")
    if defs is None:
        row["status"] = f"unavailable_http{LAST_ERROR['code']}"; return row
    row["n_label_defs"] = len(defs)
    since = f"{(a - 12) // 12}-{(a - 12) % 12 + 1:02d}-01T00:00:00Z"        # 12 months before adoption
    for page in range(1, MAX_PAGES + 1):
        items, _ = get(f"{API}/repos/{repo}/issues?state=all&per_page=100&page={page}"
                       f"&since={since}&sort=created&direction=asc")
        if not items:
            break
        for it in items:
            if "pull_request" in it:
                continue
            m = month_index(it["created_at"])
            if not (a - 12 <= m <= a + 12):
                continue
            names = [l["name"] for l in it.get("labels", [])]
            bug = any(BUG.search(n) for n in names)
            row["n_issues"] += 1; row["n_labeled"] += bool(names); row["n_bug"] += bug
            side = "post" if m >= a else "pre"
            row[f"{side}_issues"] += 1; row[f"{side}_bug"] += bug
        if len(items) < 100:
            break
    else:
        row["truncated"] = 1
    return row


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    done = set()
    if os.path.exists(dst):
        done = {r["repo_name"] for r in csv.DictReader(open(dst))}
    todo = [r for r in csv.DictReader(open(src)) if r["repo_name"] not in done][:limit]
    new = not os.path.exists(dst)
    with open(dst, "a", newline="") as f:
        w = None
        if not TOKEN:
            sys.exit("GITHUB_TOKEN is not set in this window. In cmd: set GITHUB_TOKEN=<token>")
        for i, r in enumerate(todo, 1):
            row = collect(r["repo_name"], r["adopt"])
            if row["status"] == "unavailable_http401":
                sys.exit("HTTP 401: the token is invalid or has a typo. Create a new token and set it again.")
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(row)); new and w.writeheader()
            w.writerow(row); f.flush()
            print(f"[{i}/{len(todo)}] {row['repo_name']}: {row['status']} issues={row['n_issues']} "
                  f"labeled={row['n_labeled']} bug={row['n_bug']}", flush=True)
