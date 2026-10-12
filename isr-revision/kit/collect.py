"""Collect releases, issues, merged pull requests and commits for the 19 repositories.

Usage:
    export GITHUB_TOKEN=ghp_...        (a classic token with public_repo read access is enough)
    python collect.py                  (all repositories)
    python collect.py vllm-project/vllm   (one repository)

Output: data/<owner>__<name>/{meta,releases,issues,prs,commits}.json
Re-running skips files that already exist, so an interrupted run can be resumed.
"""
import json, os, sys, time
import requests

SINCE = "2023-01-01T00:00:00Z"
REPOS = [l.split(",")[0] for l in open("repo_relevance.csv").read().splitlines()[1:] if l.strip()]
TOKEN = os.environ.get("GITHUB_TOKEN")
S = requests.Session()
S.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
if TOKEN:
    S.headers["Authorization"] = f"Bearer {TOKEN}"


def get(url, params=None):
    for attempt in range(8):
        r = S.get(url, params=params, timeout=60)
        if r.status_code == 200:
            if int(r.headers.get("X-RateLimit-Remaining", "1")) < 5:
                wait = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time() + 5
                print(f"  rate limit: sleeping {wait:.0f}s"); time.sleep(max(wait, 5))
            return r
        if r.status_code in (403, 429) and "rate limit" in r.text.lower():
            wait = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time() + 5
            print(f"  rate limit: sleeping {wait:.0f}s"); time.sleep(max(wait, 5)); continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt); continue
        r.raise_for_status()
    raise RuntimeError(f"failed: {url}")


def pages(url, params, stop=None):
    params = dict(params, per_page=100)
    while url:
        r = get(url, params)
        items = r.json()
        for it in items:
            if stop and stop(it):
                return
            yield it
        url = r.links.get("next", {}).get("url")
        params = None  # the next link already carries the parameters


def save(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


def collect(repo):
    d = os.path.join("data", repo.replace("/", "__"))
    os.makedirs(d, exist_ok=True)
    base = f"https://api.github.com/repos/{repo}"
    print(repo)
    meta_p = os.path.join(d, "meta.json")
    if not os.path.exists(meta_p):
        m = get(base).json()
        save(meta_p, {"default_branch": m["default_branch"], "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    default = json.load(open(meta_p))["default_branch"]

    p = os.path.join(d, "releases.json")
    if not os.path.exists(p):
        rel = [{"tag": x["tag_name"], "published_at": x["published_at"], "body": (x.get("body") or "")[:20000],
                "name": x.get("name") or ""}
               for x in pages(base + "/releases", {}) if not x["draft"] and not x["prerelease"] and x["published_at"]]
        save(p, rel); print(f"  releases {len(rel)}")

    p = os.path.join(d, "issues.json")
    if not os.path.exists(p):
        iss = [{"created_at": x["created_at"], "title": x["title"], "labels": [l["name"] for l in x["labels"]]}
               for x in pages(base + "/issues", {"state": "all", "since": SINCE})
               if "pull_request" not in x and x["created_at"] >= SINCE]
        save(p, iss); print(f"  issues {len(iss)}")

    p = os.path.join(d, "prs.json")
    if not os.path.exists(p):
        prs = [{"number": x["number"], "merged_at": x["merged_at"], "title": x["title"],
                "user": (x.get("user") or {}).get("login", ""), "user_type": (x.get("user") or {}).get("type", ""),
                "base": x["base"]["ref"]}
               for x in pages(base + "/pulls", {"state": "closed", "sort": "updated", "direction": "desc"},
                              stop=lambda x: x["updated_at"] < SINCE)
               if x["merged_at"] and x["merged_at"] >= SINCE]
        save(p, prs); print(f"  merged PRs {len(prs)}")

    p = os.path.join(d, "commits.json")
    if not os.path.exists(p):
        com = [{"date": x["commit"]["committer"]["date"], "author": (x.get("author") or {}).get("login", ""),
                "message": x["commit"]["message"][:200]}
               for x in pages(base + "/commits", {"sha": default, "since": SINCE})]
        save(p, com); print(f"  commits {len(com)}")


if __name__ == "__main__":
    if not TOKEN:
        print("Warning: GITHUB_TOKEN is not set; the unauthenticated limit (60 requests/hour) is far too low.")
    for repo in (sys.argv[1:] or REPOS):
        collect(repo)
    print("done")
