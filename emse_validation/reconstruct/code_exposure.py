"""Rule-based exposure coding from the repositories' own files (reconstruction only; not the two-coder protocol).

Usage: python code_exposure.py SRC_DIR OUT_exposure.csv OUT_counts.csv

A repository is exposed to a provider type when at least MIN_FILES tracked text files (excluding tests, changelogs,
release notes, lock files and vendored directories) contain a marker that the repository itself calls that provider's
API (open_weights: loads/serves/converts downloadable weights). Client SDKs of a single provider are set to 0 for
open_weights by rule. Coding is as of the checkout date, not as of each launch date.
"""
import csv, os, subprocess, sys

MARK = {
    # real provider endpoints or the provider's own model names; "import openai" alone is not used because it also
    # matches OpenAI-compatible servers (vLLM, SGLang, ...) that are tested with the OpenAI client
    "openai": r"api\.openai\.com|gpt-4o|gpt-4\.1|gpt-4-turbo|gpt-3\.5-turbo|gpt-5|o1-preview|o3-mini",
    "anthropic": r"api\.anthropic\.com|claude-3|claude-2|claude-sonnet|claude-opus|claude-haiku|claude-instant",
    "google": r"generativelanguage\.googleapis\.com|google\.generativeai|google-genai|from google import genai|gemini-1|gemini-2|gemini-pro|gemini-flash",
    "open_weights": r"from_pretrained|\.safetensors|\.gguf|huggingface\.co/",
}
MIN_FILES = {"openai": 3, "anthropic": 3, "google": 3, "open_weights": 5}
EXCLUDE = [":!*test*", ":!*Test*", ":!*CHANGELOG*", ":!*changelog*", ":!*RELEASE*", ":!*release_notes*", ":!*.lock",
           ":!*node_modules*", ":!*third_party*", ":!*vendor*", ":!*.json", ":!*.ipynb", ":!*.svg"]
SDK_ONLY = {"anthropics/anthropic-sdk-python", "openai/openai-python"}


def count(path, pattern):
    r = subprocess.run(["git", "grep", "-l", "-I", "-i", "-E", pattern, "--", "."] + EXCLUDE,
                       cwd=path, capture_output=True, text=True)
    return len([l for l in r.stdout.splitlines() if l])


def main():
    src, out, cnt = sys.argv[1:4]
    rows, counts = [], []
    for d in sorted(os.listdir(src)):
        repo = d.replace("__", "/", 1)
        for t, pat in MARK.items():
            n = count(os.path.join(src, d), pat)
            e = int(n >= MIN_FILES[t])
            if t == "open_weights" and repo in SDK_ONLY:
                e = 0
            rows.append((repo, t, e))
            counts.append((repo, t, n, e))
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["repo", "launch_type", "exposed"]); w.writerows(rows)
    with open(cnt, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["repo", "launch_type", "matching_files", "exposed"]); w.writerows(counts)


if __name__ == "__main__":
    main()
