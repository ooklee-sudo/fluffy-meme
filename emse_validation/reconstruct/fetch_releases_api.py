"""Exact releases.csv from the GitHub Releases API. Run this on your own machine (not testable in the cloud session).

Usage: GITHUB_TOKEN=ghp_xxx python fetch_releases_api.py releases_api.csv
A token with no scopes is enough for public repositories (5,000 requests/hour). Output columns match what
build_inputs.py/confirmatory_analysis.py need: repo,published_at,is_hotfix  (draft and prerelease already excluded).
is_hotfix follows the paper: patch component only differs from the previous regular release (same prefix, major, minor)
and published within 7 days of it.
"""
import csv, datetime as dt, json, os, re, sys, urllib.request

REPOS = ["anthropics/anthropic-sdk-python", "Dao-AILab/flash-attention", "EleutherAI/lm-evaluation-harness",
         "ggml-org/whisper.cpp", "huggingface/transformers", "huggingface/accelerate", "huggingface/diffusers",
         "huggingface/peft", "huggingface/text-generation-inference", "huggingface/trl", "lm-sys/FastChat",
         "microsoft/autogen", "microsoft/semantic-kernel", "NVIDIA/TensorRT-LLM", "ollama/ollama",
         "openai/openai-python", "run-llama/llama_index", "sgl-project/sglang", "vllm-project/vllm"]
VER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
END = "2026-10-11T23:59:59Z"


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                               "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req))


rows = []
for repo in REPOS:
    rel, page = [], 1
    while True:
        batch = get(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}")
        if not batch:
            break
        rel += batch
        page += 1
    rel = [r for r in rel if not r["draft"] and not r["prerelease"] and r["published_at"]
           and "2023-01-01" <= r["published_at"] <= END]
    rel.sort(key=lambda r: r["published_at"])
    prev = None
    for r in rel:
        when = dt.datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))
        m = VER.search(r["tag_name"])
        ver = (r["tag_name"][:m.start()], int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
        hot = int(bool(prev and ver and prev[1] and ver[0] == prev[1][0] and ver[1:3] == prev[1][1:3]
                       and ver[3] != prev[1][3] and (when - prev[0]).days <= 7))
        prev = (when, ver)
        rows.append((repo, r["published_at"], hot))
    print(repo, len(rel), file=sys.stderr)
with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f); w.writerow(["repo", "published_at", "is_hotfix"]); w.writerows(rows)
