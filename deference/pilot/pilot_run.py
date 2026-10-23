"""Stance-free pilot: ask each model every pilot item REPS times, one letter back, via OpenRouter.

Credentials are injected by the environment's proxy; no key is read or sent here.
Usage: python pilot_run.py items.json out.jsonl [--limit N] [--models id,id] [--reps 2]
Output: one JSON line per call: model, served_by, returned_model, item_id, rep, role, raw, error.
"""
import argparse
import concurrent.futures as cf
import json
import re
import time
import urllib.request

MODELS = {  # label: (openrouter id, family, size_rank)
    "Qwen2.5-7B": ("qwen/qwen-2.5-7b-instruct", "Qwen", 1), "Qwen2.5-72B": ("qwen/qwen-2.5-72b-instruct", "Qwen", 2),
    "Llama3.1-8B": ("meta-llama/llama-3.1-8b-instruct", "Llama", 1), "Llama3.1-70B": ("meta-llama/llama-3.1-70b-instruct", "Llama", 2),
    "Gemma3-4B": ("google/gemma-3-4b-it", "Gemma", 1), "Gemma3-12B": ("google/gemma-3-12b-it", "Gemma", 2),
    "Gemma3-27B": ("google/gemma-3-27b-it", "Gemma", 3),
    "Ministral-3B": ("mistralai/ministral-3b-2512", "Ministral", 1), "Ministral-8B": ("mistralai/ministral-8b-2512", "Ministral", 2),
    "Ministral-14B": ("mistralai/ministral-14b-2512", "Ministral", 3),
    "Haiku4.5": ("anthropic/claude-haiku-4.5", "Claude", 1), "Sonnet5.5": ("anthropic/claude-sonnet-5.5", "Claude", 2),
    "Opus5.5": ("anthropic/claude-opus-5.5", "Claude", 3), "Fable5.1": ("anthropic/claude-fable-5.1", "Claude", 4),
}
LONG_FORM = {"Haiku4.5", "Sonnet5.5", "Fable5.1"}  # answer after reasoning: 2,048-token cap, final-answer parser
LONG_CAP = 2048
SYSTEM = "Answer with a single letter (A, B, or C) and nothing else."
URL = "https://openrouter.ai/api/v1/chat/completions"


def call(mid, text, temperature=1.0, max_tokens=512):
    body = {"model": mid, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
            "max_tokens": max_tokens, "temperature": temperature}
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.load(r)
            msg = (j.get("choices") or [{}])[0].get("message", {}) or {}
            return dict(raw=msg.get("content") or "", served_by=j.get("provider"), returned_model=j.get("model"), error=None)
        except Exception as e:  # noqa: BLE001
            last = str(e)[:200]
            if "temperature" in last.lower() and "temperature" in body:
                body.pop("temperature")  # some tiers reject it; recorded below
                body_note = True
            time.sleep(2 ** (attempt + 1))
    return dict(raw="", served_by=None, returned_model=None, error=last)


def parse(raw, final=False):
    if final:  # long-form tiers: the last stated answer, else a response ending in the letter
        m = re.findall(r"(?:answer|choice)\D{0,15}?\b([ABC])\b", raw, flags=re.I)
        if m:
            return m[-1].upper()
        m = re.search(r"\**\(?([ABC])\b[^A-Za-z]*$", raw.strip())
        if m:
            return m.group(1)
        m = re.findall(r"\*\*\(?([ABC])[.)]", raw)  # a bolded "**C. ..." line
        if m:
            return m[-1]
    m = re.match(r"\s*\**\(?([ABC])\)?[\s.\)*:]*$", raw.strip()) or re.match(r"\s*\**([ABC])\b", raw.strip())
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items"); ap.add_argument("out")
    ap.add_argument("--limit", type=int); ap.add_argument("--models"); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--max-tokens", type=int, default=512, help="cap for all other models")
    a = ap.parse_args()
    items = json.load(open(a.items))[: a.limit]
    labels = a.models.split(",") if a.models else list(MODELS)
    jobs = [(lab, it, r) for lab in labels for it in items for r in range(a.reps)]

    def work(job):
        lab, it, r = job
        long = lab in LONG_FORM
        res = call(MODELS[lab][0], it["text"], max_tokens=LONG_CAP if long else a.max_tokens)
        L = parse(res["raw"], final=long)
        return dict(model=lab, family=MODELS[lab][1], size_rank=MODELS[lab][2], item_id=it["item_id"], domain=it["domain"], rep=r,
                    role=it["roles"][L] if L else "missing", **res)

    with open(a.out, "w") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for k, row in enumerate(ex.map(work, jobs), 1):
            f.write(json.dumps(row) + "\n")
            if k % 100 == 0:
                print(k, "/", len(jobs), flush=True)


if __name__ == "__main__":
    main()
