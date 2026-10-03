"""Collect ship/revert promotion-episode proxies from Hugging Face Hub commit history.

Unit = one commit on the default branch of a text-generation model repo.
  revert : title matches revert/rollback/restore/undo patterns
  ship   : title suggests a change to the live artifact (weights, config,
           generation config, tokenizer, chat template)
  other  : docs/metadata-only or unclassifiable (kept, labelled, not an episode)
Title-based labels are a proxy; validate on a hand-coded sample before use.
"""
import argparse, csv, re, sys, time
import requests

API = "https://huggingface.co/api"
REVERT = re.compile(r"\b(revert|rollback|roll back|roll-back|restore|restoring|undo|back ?out)\b", re.I)
# ship = change to the served artifact; docs/license/metadata-only commits are excluded
SHIP = re.compile(r"(weights?|safetensors|\.bin\b|\.gguf|\.onnx|\.pt\b|checkpoint|config\.json|generation_config|tokenizer|chat[_ ]template|ForCausalLM|\bmodel\b|release|\bv\d|folder)", re.I)
DOCS = re.compile(r"(readme|model card|\.gitattributes|license|metadata|initial commit)", re.I)

S = requests.Session()

def get(url, **kw):
    for i in range(4):
        r = S.get(url, timeout=30, **kw)
        if r.status_code == 429:
            time.sleep(2 ** (i + 1)); continue
        if r.status_code in (401, 403, 404):
            return None
        r.raise_for_status()
        return r
    return None

def list_models(n, pipeline):
    r = get(f"{API}/models", params=dict(sort="downloads", direction=-1, limit=n, filter=pipeline))
    return [m["id"] for m in r.json()] if r else []

def commits(repo, max_pages=20):
    out, url = [], f"{API}/models/{repo}/commits/main"
    for _ in range(max_pages):
        r = get(url)
        if not r: break
        out += r.json()
        nxt = r.links.get("next", {}).get("url")
        if not nxt: break
        url = nxt
    return out

def classify(title):
    if REVERT.search(title): return "revert"
    if DOCS.search(title) and not SHIP.search(title): return "other"
    if SHIP.search(title): return "ship"
    return "other"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--pipeline", default="text-generation")
    ap.add_argument("--out", default="episodes.csv")
    a = ap.parse_args()
    repos = list_models(a.n, a.pipeline)
    print(f"{len(repos)} repos", file=sys.stderr)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "commit_id", "date", "title", "authors", "label"])
        for i, repo in enumerate(repos, 1):
            cs = commits(repo)
            for c in cs:
                t = c.get("title", "")
                w.writerow([repo, c["id"], c["date"], t,
                            ";".join(x.get("user", "") for x in c.get("authors", [])),
                            classify(t)])
            print(f"[{i}/{len(repos)}] {repo}: {len(cs)} commits", file=sys.stderr)

if __name__ == "__main__":
    main()
