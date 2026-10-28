"""Split each biography into ordered atomic claims and judge each against the Wikipedia reference (FActScore-style).

Labels: S = supported, C = contradicted by the reference, N = not found in the reference.
Hallucination event (main) = not S; strict = C.
"""
import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from common import DATA, chat, read_jsonl, write_jsonl

PROMPT = """You are a careful fact-checker.

REFERENCE (Wikipedia article on {title}):
\"\"\"
{ref}
\"\"\"

BIOGRAPHY TO CHECK:
\"\"\"
{text}
\"\"\"

Step 1: list every atomic, independently verifiable factual claim in the biography, in the order it appears. One fact per claim (a date, place, name, number, role, event). Skip opinions, vague praise and filler.
Step 2: label each claim against the REFERENCE only:
  S = the reference supports it, C = the reference contradicts it, N = the reference neither supports nor contradicts it.

Return ONLY a JSON array like [{{"claim": "...", "label": "S"}}, ...]."""


def parse(s):
    m = re.search(r"\[.*\]", s, re.S)
    arr = json.loads(m.group(0))
    return [{"claim": x["claim"], "label": x["label"].strip().upper()[:1]} for x in arr if x.get("label", "").strip().upper()[:1] in "SCN"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True)
    ap.add_argument("--judge", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--entities", default=os.path.join(DATA, "entities.jsonl"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or a.gen.replace("gen_", "lab_")
    ents = {e["title"]: e for e in read_jsonl(a.entities)}
    done = {r["title"] for r in read_jsonl(out)}
    todo = [g for g in read_jsonl(a.gen) if g["title"] not in done and g["title"] in ents]

    def run(g):
        e = ents[g["title"]]
        p = PROMPT.format(title=g["title"], ref=e["reference"], text=g["text"])
        for _ in range(3):
            try:
                cl = parse(chat(a.judge, p, 6000, 0.0))
                if cl:
                    return {"title": g["title"], "sitelinks": e["sitelinks"], "gen_model": g["model"], "judge": a.judge, "claims": cl}
            except Exception:
                pass
        return None

    with ThreadPoolExecutor(8) as ex:
        new = [r for r in ex.map(run, todo) if r]
    write_jsonl(out, read_jsonl(out) + new)
    print(f"{len(new)}/{len(todo)} labelled -> {out}")


if __name__ == "__main__":
    main()
