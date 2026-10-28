"""Have a (small) model write a long biography per entity."""
import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from common import DATA, chat, read_jsonl

PROMPT = ("Write a detailed, factual biography of {t} in about 600 words. Cover early life, career, "
          "achievements and later life, with specific dates, places, names and numbers. Plain prose, no headings.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemma-3-4b-it")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--entities", default=os.path.join(DATA, "entities.jsonl"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    out = a.out or os.path.join(DATA, "gen_" + a.model.split("/")[-1] + ".jsonl")
    ents = read_jsonl(a.entities)[: a.limit or None]
    done = {r["title"] for r in read_jsonl(out)}
    todo = [e for e in ents if e["title"] not in done]
    lock = threading.Lock()

    def run(e):
        try:
            r = {"title": e["title"], "model": a.model, "text": chat(a.model, PROMPT.format(t=e["title"]), 1400, a.temperature)}
        except RuntimeError as err:
            print("  skip", e["title"], str(err)[:80], flush=True)
            return None
        with lock:  # append per item so an interruption loses nothing
            with open(out, "a") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return r

    with ThreadPoolExecutor(a.workers) as ex:
        new = [r for r in ex.map(run, todo) if r]
    print(f"{len(new)} new generations -> {out}")


if __name__ == "__main__":
    main()
