#!/usr/bin/env python3
"""Collect issue / release histories for the 19 repositories in Table 1.

Run on your own machine (needs network + a read-only GitHub token):
    pip install requests
    export GITHUB_TOKEN=ghp_xxx        # public_repo / no scopes is enough
    python collect_github.py --out data

Outputs (in --out):
    issues.csv        one row per issue (PRs excluded): repo, number, created_at, title, labels, is_bug
    releases.csv      one row per non-draft, non-prerelease release: repo, tag, published_at
    weekly.csv        repo x ISO-week panel: issues, bugs, release flag, weeks_since_release
    bug_sample.csv    300 random issues for manual labeling (fill column `human_is_bug` with 0/1)
    docs/<repo>/*.md  CONTRIBUTING / RELEASING / release-policy files, for the policy comparison
"""
import argparse, csv, datetime as dt, os, random, re, sys, time
import requests

REPOS = """anthropics/anthropic-sdk-python Dao-AILab/flash-attention EleutherAI/lm-evaluation-harness
ggml-org/whisper.cpp huggingface/transformers huggingface/accelerate huggingface/diffusers huggingface/peft
huggingface/text-generation-inference huggingface/trl lm-sys/FastChat microsoft/autogen
microsoft/semantic-kernel NVIDIA/TensorRT-LLM ollama/ollama openai/openai-python
run-llama/llama_index sgl-project/sglang vllm-project/vllm""".split()

SINCE = dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)
KEYWORDS = re.compile(r"bug|error|crash|fail|wrong|incorrect|regression|broken|exception", re.I)
DOC_NAMES = ["CONTRIBUTING.md", "RELEASING.md", "RELEASE.md", "docs/RELEASING.md", "docs/release.md",
             "docs/releasing.md", ".github/CONTRIBUTING.md", "docs/contributing.md", "MAINTAINERS.md", "README.md"]
S = requests.Session()
S.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "iep-paper-collector"})
if os.environ.get("GITHUB_TOKEN"):
    S.headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
else:
    sys.exit("Set GITHUB_TOKEN (unauthenticated limit is 60 requests/hour).")


def get(url, **params):
    while True:
        r = S.get(url, params=params, timeout=60)
        if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
            wait = max(int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time(), 5) + 2
            print(f"  rate limited, sleeping {wait:.0f}s", flush=True); time.sleep(wait); continue
        if r.status_code >= 500:
            time.sleep(5); continue
        return r


def paginate(url, **params):
    params = dict(params, per_page=100)
    while url:
        r = get(url, **params)
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")
        params = {}


def parse(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def week_start(d):
    d = d.astimezone(dt.timezone.utc).date()
    return d - dt.timedelta(days=d.weekday())  # Monday of ISO week


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="data"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    issues, releases = [], []
    for repo in REPOS:
        print(repo, flush=True)
        n = 0
        for it in paginate(f"https://api.github.com/repos/{repo}/issues", state="all", sort="created",
                           direction="asc", since=SINCE.strftime("%Y-%m-%dT%H:%M:%SZ")):
            if "pull_request" in it: continue
            c = parse(it["created_at"])
            if c < SINCE: continue
            labels = [l["name"] for l in it["labels"]]
            bug = any("bug" in l.lower() for l in labels) or bool(KEYWORDS.search(it["title"]))
            issues.append(dict(repo=repo, number=it["number"], created_at=it["created_at"],
                               title=it["title"].replace("\n", " "), labels="|".join(labels), is_bug=int(bug)))
            n += 1
        m = 0
        for rel in paginate(f"https://api.github.com/repos/{repo}/releases"):
            if rel["draft"] or rel["prerelease"] or not rel.get("published_at"): continue
            releases.append(dict(repo=repo, tag=rel["tag_name"], published_at=rel["published_at"])); m += 1
        print(f"  {n} issues, {m} releases", flush=True)
        for path in DOC_NAMES:  # release-policy documents for Section 4.3 (iv)
            r = get(f"https://api.github.com/repos/{repo}/contents/{path}")
            if r.status_code == 200 and r.json().get("download_url"):
                txt = requests.get(r.json()["download_url"], timeout=60).text
                d = os.path.join(a.out, "docs", repo.replace("/", "__")); os.makedirs(d, exist_ok=True)
                open(os.path.join(d, path.replace("/", "_")), "w", encoding="utf8").write(txt)

    def dump(name, rows):
        with open(os.path.join(a.out, name), "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    dump("issues.csv", issues); dump("releases.csv", releases)

    # weekly panel: from first release in/after SINCE to the last week of data
    end = week_start(dt.datetime.now(dt.timezone.utc)) - dt.timedelta(days=7)  # drop incomplete week
    panel = []
    for repo in REPOS:
        iss, rel = {}, set()
        for i in issues:
            if i["repo"] == repo:
                w = week_start(parse(i["created_at"])); t = iss.setdefault(w, [0, 0]); t[0] += 1; t[1] += i["is_bug"]
        for r in releases:
            if r["repo"] == repo: rel.add(week_start(parse(r["published_at"])))
        in_window = sorted(w for w in rel if w >= SINCE.date())
        if not in_window: continue
        w, last = in_window[0], None
        while w <= end:
            if w in rel: last = w
            panel.append(dict(repo=repo, week=w.isoformat(), issues=iss.get(w, [0, 0])[0],
                              bugs=iss.get(w, [0, 0])[1], release=int(w in rel),
                              age=(w - last).days // 7 if last else ""))
            w += dt.timedelta(days=7)
    dump("weekly.csv", panel)

    random.seed(1); samp = random.sample(issues, min(300, len(issues)))
    dump("bug_sample.csv", [dict(s, human_is_bug="") for s in samp])
    print("done ->", a.out)


if __name__ == "__main__":
    main()
