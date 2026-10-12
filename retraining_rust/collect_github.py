"""Collect weekly bug-issue counts and release dates for open-weight model repos
from the GitHub REST API. Needs GITHUB_TOKEN (public_repo read scope is enough).

  python collect_github.py QwenLM/Qwen2.5 deepseek-ai/DeepSeek-V3 --out data/
Writes data/<owner>__<repo>.csv with columns: week, bugs, all_issues, release
"""
import argparse, csv, os, re, sys, time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import requests

API = "https://api.github.com"
BUG_RE = re.compile(r"\b(bug|error|crash|fail|wrong|incorrect|regression|broken|exception)\b", re.I)


def get_all(url, headers, params=None):
    params = dict(params or {}, per_page=100)
    while url:
        r = requests.get(url, headers=headers, params=params, timeout=60)
        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            time.sleep(max(1, int(r.headers["X-RateLimit-Reset"]) - time.time()) + 2)
            continue
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")
        params = None


def week_of(ts):
    d = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def is_bug(issue):
    labels = " ".join(l["name"] for l in issue.get("labels", []))
    return bool(re.search(r"bug", labels, re.I)) or bool(BUG_RE.search(issue["title"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--out", default="data")
    ap.add_argument("--since", default="2023-01-01T00:00:00Z")
    a = ap.parse_args()
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        sys.exit("set GITHUB_TOKEN")
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    os.makedirs(a.out, exist_ok=True)
    for repo in a.repos:
        outf = os.path.join(a.out, repo.replace("/", "__") + ".csv")
        if os.path.exists(outf):
            print(repo, "already collected, skipping"); continue
        try:
            collect_one(repo, h, a, outf)
        except Exception as e:
            print(repo, "FAILED:", e)


def collect_one(repo, h, a, outf):
    if True:
        bugs, allc, rel = Counter(), Counter(), set()
        for it in get_all(f"{API}/repos/{repo}/issues", h, dict(state="all", since=a.since)):
            if "pull_request" in it or it["created_at"] < a.since:
                continue
            w = week_of(it["created_at"])
            allc[w] += 1
            bugs[w] += is_bug(it)
        for r in get_all(f"{API}/repos/{repo}/releases", h):
            if not r.get("draft") and not r.get("prerelease") and r.get("published_at"):
                rel.add(week_of(r["published_at"]))
        weeks = sorted(set(allc) | rel)
        if not weeks:
            return
        # fill gaps with zero weeks
        def nxt(wk):
            y, w = map(int, wk.split("-W"))
            y2, w2, _ = (date.fromisocalendar(y, w, 1) + timedelta(days=7)).isocalendar()
            return f"{y2}-W{w2:02d}"
        full, cur = [], weeks[0]
        while cur <= weeks[-1]:
            full.append(cur); cur = nxt(cur)
        with open(outf, "w", newline="") as f:
            wr = csv.writer(f); wr.writerow(["week", "bugs", "all_issues", "release"])
            for w in full:
                wr.writerow([w, bugs[w], allc[w], int(w in rel)])
        print(repo, len(full), "weeks,", len(rel), "releases")


if __name__ == "__main__":
    main()
