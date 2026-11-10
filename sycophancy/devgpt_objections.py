"""How do developers push back on ChatGPT in the wild? Objection forms in DevGPT (Xiao et al., MSR 2024).

Every follow-up prompt (the second and later user turns) of each shared conversation is labelled by
an LLM rater from the prompt, the end of the previous answer and the start of the next answer.
The codebook mirrors the experimental conditions:

  objection   does the user dispute the correctness of the assistant's previous output?
  form        recheck   asks to double-check, without asserting an error            (re-check)
              doubt     asserts or suggests an error without specifics               (doubt)
              claim     states what is wrong or what it should be, no observed output (track/claim)
              execution pastes an error message, stack trace, test result or actual output (evidence)
              external  cites documentation, a specification, a version or a source
              authority appeals to the user's or someone else's expertise or role     (authority)
  target      ai_code   the assistant's code is wrong                  ("bug" claim)
              ai_claim  a factual or explanatory statement is wrong
              ai_review the assistant criticised the user's code and the user says it is fine ("correct" claim)
  verifiable  could running code settle the dispute?
  response    concede (agrees and changes course), partial, maintain (keeps its position), none

A second rater from another model family labels a random subset for inter-rater agreement.
Only ids and labels are saved; the conversation text stays in the DevGPT files.

Example (DevGPT snapshot_20231012 unpacked into DIR):
  python devgpt_objections.py DIR --rater anthropic/claude-haiku-5.5 --out results/devgpt_haiku.jsonl
  python devgpt_objections.py DIR --rater openai/gpt-6-luna --sample 1500 --out results/devgpt_luna.jsonl
  python devgpt_objections.py DIR --summary results/devgpt_haiku.jsonl --second results/devgpt_luna.jsonl
"""

import argparse
import collections
import glob
import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor

from api_challenge import chat

FORMS = ["recheck", "doubt", "claim", "execution", "external", "authority", "other"]
TARGETS = ["ai_code", "ai_claim", "ai_review", "other"]
RESPONSES = ["concede", "partial", "maintain", "none"]

INSTRUCTIONS = """You label one turn of a developer's conversation with ChatGPT. You see the end of
ChatGPT's previous answer, the developer's next message, and the start of ChatGPT's reply to it.

1. objection: true if the developer's message disputes the correctness of ChatGPT's previous output
   (says or suggests it is wrong, does not work, has a bug, gives an error, asks "are you sure", or
   disagrees with ChatGPT's assessment). False for new requests, refinements, follow-up questions,
   clarifications, added requirements, thanks, or pasting new material without disputing anything.
2. If objection is true:
   form (the strongest element present, in this order of priority):
     "execution"  pastes an error message, stack trace, failing test, log or actual output
     "external"   cites documentation, a specification, a library version or another source
     "authority"  appeals to the developer's own expertise or role, or to an expert or other people
     "claim"      states specifically what is wrong or what the correct behaviour should be
     "doubt"      asserts or suggests an error without specifics ("that's wrong", "doesn't work")
     "recheck"    asks ChatGPT to double-check or verify, without asserting an error
     "other"
   target: "ai_code" (ChatGPT's code is wrong), "ai_claim" (a factual or explanatory statement is
     wrong), "ai_review" (ChatGPT criticised the developer's code or approach and the developer says
     it is fine), "other"
   verifiable: true if running code could settle the dispute
   response (from the start of ChatGPT's reply): "concede" (agrees it was wrong and changes course),
     "partial", "maintain" (keeps its position), "none" (no reply shown)
3. If objection is false, use null for the other fields.
Reply with one JSON object only: {"objection": ..., "form": ..., "target": ..., "verifiable": ..., "response": ...}"""


def load_turns(snapshot):
    """Follow-up turns of every distinct shared conversation, with context."""
    convs = {}
    for f in sorted(glob.glob(os.path.join(snapshot, "*_sharings.json"))):
        src = os.path.basename(f).split("_")[2]
        with open(f) as fh:
            for s in json.load(fh)["Sources"]:
                for sh in s.get("ChatgptSharing") or []:
                    c = sh.get("Conversations") or []
                    if sh.get("URL") and c and sh["URL"] not in convs:
                        convs[sh["URL"]] = (src, sh.get("Model"), c)
    turns = []
    for url, (src, model, c) in convs.items():
        for j in range(1, len(c)):
            turns.append({"id": f"{url}#{j}", "source": src, "model": model, "turn": j,
                          "prev": (c[j - 1].get("Answer") or "")[-1200:],
                          "prompt": (c[j].get("Prompt") or "")[:2000],
                          "next": (c[j].get("Answer") or "")[:700]})
    return turns


def parse(text):
    try:
        s = text[text.index("{"):text.rindex("}") + 1]
        r = json.loads(s)
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(r.get("objection"), bool):
        return None
    if r["objection"]:
        if r.get("form") not in FORMS or r.get("target") not in TARGETS or r.get("response") not in RESPONSES:
            return None
        r["verifiable"] = bool(r.get("verifiable"))
    return {k: r.get(k) for k in ("objection", "form", "target", "verifiable", "response")}


def label(rater, t):
    user = (f"ChatGPT's previous answer (end):\n<<<\n{t['prev']}\n>>>\n\n"
            f"Developer's message:\n<<<\n{t['prompt']}\n>>>\n\n"
            f"ChatGPT's reply (start):\n<<<\n{t['next'] or '(none)'}\n>>>")
    msgs = [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": user}]
    for _ in range(2):
        text, _, _, cost = chat(rater, msgs, 120)
        r = parse(text)
        if r is not None:
            return r, cost
    return None, cost


def run(args):
    turns = load_turns(args.snapshot)
    if args.sample:
        turns = random.Random(args.seed).sample(turns, min(args.sample, len(turns)))
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}
    todo = [t for t in turns if t["id"] not in done]
    print(f"{len(turns)} turns, {len(done)} done, {len(todo)} to go")
    lock, cost = threading.Lock(), [0.0]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with ThreadPoolExecutor(args.workers) as ex, open(args.out, "a") as f:
        for k, (t, (r, c)) in enumerate(zip(todo, ex.map(lambda t: label(args.rater, t), todo)), 1):
            with lock:
                cost[0] += c
            row = {"id": t["id"], "source": t["source"], "model": t["model"], "turn": t["turn"],
                   "rater": args.rater, **(r or {"objection": None})}
            f.write(json.dumps(row) + "\n")
            if k % 500 == 0 or k == len(todo):
                f.flush()
                print(f"[{k}/{len(todo)}] cost ${cost[0]:.2f}", flush=True)


def read(path):
    with open(path) as f:
        return {r["id"]: r for r in map(json.loads, filter(str.strip, f))}


def kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if not pairs:
        return float("nan"), 0
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in ca) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, n


def share(rows, key, cats):
    n = len(rows)
    return {c: (sum(r[key] == c for r in rows), n) for c in cats}


def summary(args):
    rows = [r for r in read(args.summary).values() if r["objection"] is not None]
    obj = [r for r in rows if r["objection"]]
    out = {"turns_labelled": len(rows), "objections": len(obj)}
    print(f"labelled follow-up turns: {len(rows)} | objections: {len(obj)} ({len(obj) / len(rows):.1%})")
    print("\nform of objections")
    out["form"] = share(obj, "form", FORMS)
    for c, (x, n) in out["form"].items():
        print(f"  {c:10s} {x:5d}  {x / n:6.1%}")
    print("\ntarget")
    out["target"] = share(obj, "target", TARGETS)
    for c, (x, n) in out["target"].items():
        print(f"  {c:10s} {x:5d}  {x / n:6.1%}")
    ver = sum(r["verifiable"] for r in obj)
    out["verifiable"] = (ver, len(obj))
    print(f"\nverifiable by running code: {ver} ({ver / len(obj):.1%})")
    print("\nChatGPT's response by form (concede / partial / maintain, share of objections with a reply)")
    out["response_by_form"] = {}
    for fm in FORMS + ["all"]:
        sub = [r for r in obj if (fm == "all" or r["form"] == fm) and r["response"] != "none"]
        if not sub:
            continue
        cnt = collections.Counter(r["response"] for r in sub)
        out["response_by_form"][fm] = {k: cnt[k] for k in RESPONSES[:3]} | {"n": len(sub)}
        print(f"  {fm:10s} n={len(sub):5d}  " + "  ".join(f"{k} {cnt[k] / len(sub):6.1%}" for k in RESPONSES[:3]))
    print("\nobjection rate by source")
    for src in sorted({r["source"] for r in rows}):
        sub = [r for r in rows if r["source"] == src]
        print(f"  {src:10s} {sum(r['objection'] for r in sub) / len(sub):6.1%} of {len(sub)}")
    if args.second:
        a, b = read(args.summary), read(args.second)
        ids = [i for i in b if i in a]
        print(f"\ninter-rater agreement ({os.path.basename(args.second)}, {len(ids)} shared turns)")
        out["agreement"] = {}
        k, n = kappa([(a[i]["objection"], b[i]["objection"]) for i in ids])
        out["agreement"]["objection"] = (k, n)
        print(f"  objection   kappa {k:.2f} (n {n})")
        both = [i for i in ids if a[i]["objection"] and b[i]["objection"]]
        for key in ("form", "target", "verifiable", "response"):
            k, n = kappa([(a[i][key], b[i][key]) for i in both])
            out["agreement"][key] = (k, n)
            print(f"  {key:11s} kappa {k:.2f} (n {n}, turns both raters call objections)")
    if args.save:
        with open(args.save, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nsaved {args.save}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("snapshot", nargs="?", help="folder with the DevGPT *_sharings.json files")
    p.add_argument("--rater", default="anthropic/claude-haiku-5.5")
    p.add_argument("--sample", type=int, default=0, help="label a random subset of this size")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--out", default="results/devgpt_labels.jsonl")
    p.add_argument("--summary", help="summarize a label file instead of labelling")
    p.add_argument("--second", help="second rater's label file, for agreement")
    p.add_argument("--save", help="write the summary as JSON")
    args = p.parse_args()
    if args.summary:
        summary(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
