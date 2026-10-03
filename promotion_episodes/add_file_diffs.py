"""Add changed-file categories to episodes.csv via the Hub compare API.
artifact_change = any changed file in weights/gen_config/config/tokenizer; docs_only = only docs/metadata.
Adds columns: files, cats, artifact_change, label2 (label refined: ship/revert need artifact_change)."""
import csv, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests

S = requests.Session()
WEIGHTS = re.compile(r"\.(safetensors|bin|gguf|onnx|pt|pth|ckpt|h5|msgpack|ot|npz|mlmodel)$|\.index\.json$", re.I)
GENCFG = re.compile(r"generation_config\.json$", re.I)
CONFIG = re.compile(r"(^|/)config\.json$|params\.json$|\.py$", re.I)
TOK = re.compile(r"tokenizer|vocab|merges|special_tokens|chat_template|added_tokens|\.model$|preprocessor", re.I)
DOCS = re.compile(r"\.(md|txt|png|jpg|jpeg|gif|svg|pdf)$|\.gitattributes$|LICENSE|NOTICE", re.I)

def cat(path):
    for name, rx in (("docs", DOCS), ("weights", WEIGHTS), ("generation_config", GENCFG),
                     ("tokenizer", TOK), ("config", CONFIG)):
        if rx.search(path): return name
    return "other"

def diff_files(repo, sha):
    url = f"https://huggingface.co/api/models/{repo}/compare/{sha}^..{sha}"
    for i in range(4):
        try:
            r = S.get(url, timeout=60)
        except requests.RequestException:
            time.sleep(2 ** (i + 1)); continue
        if r.status_code == 429: time.sleep(2 ** (i + 1)); continue
        if r.status_code != 200: return None  # e.g. root commit has no parent
        return sorted(set(re.findall(r"^diff --git a/(\S+) b/", r.text, re.M)))
    return None

def work(row):
    if row["label"] == "other":
        return row, None
    return row, diff_files(row["repo"], row["commit_id"])

def main(path="episodes.csv"):
    rows = list(csv.DictReader(open(path)))
    cols = [c for c in rows[0] if c not in ("files", "cats", "artifact_change", "label2")]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(work, rows))
    out = []
    for row, files in res:
        row = {k: row[k] for k in cols}
        if files is None:
            row.update(files="", cats="", artifact_change="" , label2=row["label"] if row["label"] == "other" else "unknown")
        else:
            cats = sorted({cat(f) for f in files})
            art = any(c != "docs" and c != "other" for c in cats)
            row.update(files=";".join(files)[:500], cats=";".join(cats), artifact_change=int(art),
                       label2=row["label"] if art else "docs_only")
        out.append(row)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols + ["files", "cats", "artifact_change", "label2"])
        w.writeheader(); w.writerows(out)

if __name__ == "__main__":
    main(*sys.argv[1:])
