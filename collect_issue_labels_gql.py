"""Issue-label collector using the GitHub GraphQL API (issues only, no pull requests => no REST page-cap problem).

For each repo: all issues created in [adopt-12 months, adopt+12 months], counted as before/after the adoption month,
with 'labeled' (any label) and 'bug-like' (label name matches the regex). Same output columns as collect_issue_labels.py.
Needs $GITHUB_TOKEN. Resumable (repos already in the output CSV are skipped).

Usage: python collect_issue_labels_gql.py repos.csv out.csv [max_repos]      (repos.csv has columns repo_name, adopt)
NOTE: tested only against the query syntax on one repository; not run on the 50 target repos from this environment.
"""
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN")
URL = "https://api.github.com/graphql"
BUG = re.compile(r"\b(bug|defect|crash|regression|error|fail|broken|fault)", re.I)
QUERY = """
query($owner:String!, $name:String!, $after:String) {
  rateLimit { remaining resetAt }
  repository(owner:$owner, name:$name) {
    issues(first:100, after:$after, orderBy:{field:CREATED_AT, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes { createdAt labels(first:30) { nodes { name } } }
    }
  }
}"""


def gql(variables):
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    for attempt in range(6):
        req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "isr-pilot",
                                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.load(r)
            rl = (out.get("data") or {}).get("rateLimit")
            if rl and rl["remaining"] < 25:
                time.sleep(120)
            return out
        except urllib.error.HTTPError as e:
            if e.code in (401, 404):
                return {"errors": [{"message": f"HTTP {e.code}"}], "http": e.code}
            time.sleep(2 ** attempt)
        except urllib.error.URLError:
            time.sleep(2 ** attempt)
    return {"errors": [{"message": "failed"}]}


def month_index(ts):
    return int(ts[:4]) * 12 + int(ts[5:7]) - 1


def collect(repo, adopt):
    a = month_index(adopt)
    row = dict(repo_name=repo, adopt=adopt, status="ok", n_issues=0, n_labeled=0, n_bug=0, pre_issues=0, post_issues=0,
               pre_bug=0, post_bug=0, n_label_defs=0, truncated=0)
    owner, name = repo.split("/")
    after = None
    while True:
        out = gql({"owner": owner, "name": name, "after": after})
        if out.get("http") == 401:
            sys.exit("HTTP 401: the token is invalid or missing. Set GITHUB_TOKEN and try again.")
        if "data" not in out or not (out["data"] or {}).get("repository"):
            msg = json.dumps(out.get("errors"))[:300]
            row["status"] = "unavailable"
            if "NOT_FOUND" not in msg and "Could not resolve" not in msg:      # a real error, not just a deleted repo
                print(f"   GraphQL error for {repo}: {msg}", flush=True)
            return row
        conn = out["data"]["repository"]["issues"]
        stop = False
        for it in conn["nodes"]:
            m = month_index(it["createdAt"])
            if m < a - 12:
                stop = True; break
            if m <= a + 12:
                names = [l["name"] for l in it["labels"]["nodes"]]
                bug = any(BUG.search(n) for n in names)
                row["n_issues"] += 1; row["n_labeled"] += bool(names); row["n_bug"] += bug
                side = "post" if m >= a else "pre"
                row[f"{side}_issues"] += 1; row[f"{side}_bug"] += bug
        if stop or not conn["pageInfo"]["hasNextPage"]:
            return row
        after = conn["pageInfo"]["endCursor"]


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is not set in this window. In cmd: set GITHUB_TOKEN=<token>")
    src, dst = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    done = set(r["repo_name"] for r in csv.DictReader(open(dst))) if os.path.exists(dst) else set()
    todo = [r for r in csv.DictReader(open(src)) if r["repo_name"] not in done][:limit]
    new = not os.path.exists(dst)
    with open(dst, "a", newline="") as f:
        w = None
        for i, r in enumerate(todo, 1):
            row = collect(r["repo_name"], r["adopt"])
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(row)); new and w.writeheader()
            w.writerow(row); f.flush()
            print(f"[{i}/{len(todo)}] {row['repo_name']}: {row['status']} issues={row['n_issues']} pre={row['pre_issues']} "
                  f"post={row['post_issues']} bug={row['n_bug']}", flush=True)
