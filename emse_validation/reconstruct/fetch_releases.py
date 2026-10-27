"""Rebuild releases.csv from git tags (GitHub's Releases API is not available in this session).

Usage: python fetch_releases.py OUT.csv [WORKDIR]

For each of the 19 study repositories, fetch all tags (no blobs, no trees) and take the tag date:
annotated tag -> tagger date; lightweight tag -> committer date of the tagged commit.
Output columns: repo,tag,published_at (UTC, ISO),tag_type,is_prerelease,is_hotfix

Approximation caveats (also printed in README.md): a git tag is not a GitHub release. Lightweight-tag dates are the
commit date and can precede publication; draft/prerelease flags are inferred from the tag name; tags without a
parseable x.y.z version are kept as regular releases and cannot be hot-fixes.
"""
import csv, datetime as dt, os, re, subprocess, sys

REPOS = ["anthropics/anthropic-sdk-python", "Dao-AILab/flash-attention", "EleutherAI/lm-evaluation-harness",
         "ggml-org/whisper.cpp", "huggingface/transformers", "huggingface/accelerate", "huggingface/diffusers",
         "huggingface/peft", "huggingface/text-generation-inference", "huggingface/trl", "lm-sys/FastChat",
         "microsoft/autogen", "microsoft/semantic-kernel", "NVIDIA/TensorRT-LLM", "ollama/ollama",
         "openai/openai-python", "run-llama/llama_index", "sgl-project/sglang", "vllm-project/vllm"]
START = dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)
PRE = re.compile(r"(?i)(?:^|[._\-+])(a|b|rc|alpha|beta|dev|pre|preview|snapshot|nightly|test)\d*(?:$|[._\-+])|\d(a|b|rc)\d+")
VER = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, check=True, capture_output=True, text=True).stdout


def tags(repo, work):
    d = os.path.join(work, repo.replace("/", "__"))
    if not os.path.isdir(d):
        sh("git", "init", "-q", "--bare", d)
        sh("git", "remote", "add", "origin", f"https://github.com/{repo}", cwd=d)
    sh("git", "fetch", "-q", "--depth=1", "--filter=tree:0", "origin", "+refs/tags/*:refs/tags/*", cwd=d)
    out = sh("git", "for-each-ref", "--format=%(refname:short)\t%(objecttype)\t%(creatordate:unix)", "refs/tags", cwd=d)
    rows = []
    for line in out.splitlines():
        name, otype, ts = line.split("\t")
        if not ts:
            continue
        rows.append((name, "annotated" if otype == "tag" else "lightweight",
                     dt.datetime.fromtimestamp(int(ts), dt.timezone.utc)))
    return sorted(rows, key=lambda r: r[2])


def main():
    out = sys.argv[1]
    work = sys.argv[2] if len(sys.argv) > 2 else "/tmp/rc"
    os.makedirs(work, exist_ok=True)
    allrows = []
    for repo in REPOS:
        prev = None
        n = 0
        for name, typ, when in tags(repo, work):
            if when < START:
                continue
            pre = int(bool(PRE.search(name)))
            m = VER.search(name)
            ver = (name[:m.start()], int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
            hot = 0
            if not pre:
                if prev and ver and prev[0] and prev[1] and ver[0] == prev[1][0] and ver[1:3] == prev[1][1:3] \
                        and ver[3] != prev[1][3] and (when - prev[0]).days <= 7:
                    hot = 1
                prev = (when, ver) if True else prev
            allrows.append((repo, name, when.strftime("%Y-%m-%dT%H:%M:%SZ"), typ, pre, hot))
            n += 1
        print(f"{repo}: {n} tags since 2023-01-01")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "tag", "published_at", "tag_type", "is_prerelease", "is_hotfix"])
        w.writerows(allrows)


if __name__ == "__main__":
    main()
