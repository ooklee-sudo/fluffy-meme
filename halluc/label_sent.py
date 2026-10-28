"""Like label.py, but the biography is split into numbered sentences and every claim carries the number of the
sentence it came from ("sent"). This lets analyze_sent.py (a) merge claims of one sentence into one unit, removing the
mechanical correlation of split claims, and (b) drop claims the reference is silent on (N) to control verifiability.
"""
import argparse
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from common import DATA, chat, read_jsonl

PROMPT = """You are a careful fact-checker.

REFERENCE (Wikipedia article on {title}):
\"\"\"
{ref}
\"\"\"

BIOGRAPHY TO CHECK, split into numbered sentences:
{sents}

Step 1: for each sentence, list every atomic, independently verifiable factual claim it makes (a date, place, name, number, role, event). One fact per claim. Skip opinions, vague praise and filler. Sentences with no checkable fact get no claims.
Step 2: label each claim against the REFERENCE only:
  S = the reference supports it, C = the reference contradicts it, N = the reference neither supports nor contradicts it.

Return ONLY a JSON array in sentence order like [{{"sent": 1, "claim": "...", "label": "S"}}, ...]."""


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 3]


def parse(s, n_sent):
    arr = json.loads(re.search(r"\[.*\]", s, re.S).group(0))
    out = []
    for x in arr:
        lab = str(x.get("label", "")).strip().upper()[:1]
        sent = int(x.get("sent", 0))
        if lab in ("S", "C", "N") and 1 <= sent <= n_sent:
            out.append({"sent": sent, "claim": x["claim"], "label": lab})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True)
    ap.add_argument("--judge", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--entities", default=os.path.join(DATA, "entities.jsonl"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = a.out or a.gen.replace("gen_", "labs_")
    ents = {e["title"]: e for e in read_jsonl(a.entities)}
    done = {r["title"] for r in read_jsonl(out)}
    todo = [g for g in read_jsonl(a.gen) if g["title"] not in done and g["title"] in ents]

    lock = threading.Lock()

    def run(g):
        e = ents[g["title"]]
        sents = g.get("sents") or split_sentences(g["text"])  # "sents": caller-supplied segmentation (human-annotated data)
        numbered = "\n".join(f"[{i}] {s}" for i, s in enumerate(sents, 1))
        p = PROMPT.format(title=g["title"], ref=e["reference"], sents=numbered)
        for _ in range(3):
            try:
                cl = parse(chat(a.judge, p, 8000, 0.0), len(sents))
                if cl:
                    rec = {"title": g["title"], "sitelinks": e["sitelinks"], "gen_model": g["model"],
                           "judge": a.judge, "n_sent": len(sents), "claims": cl}
                    with lock:  # append per item so an interruption or rate limit loses nothing
                        with open(out, "a") as f:
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    return rec
            except Exception:
                pass
        return None

    with ThreadPoolExecutor(a.workers) as ex:
        new = [r for r in ex.map(run, todo) if r]
    print(f"{len(new)}/{len(todo)} labelled -> {out}")


if __name__ == "__main__":
    main()
