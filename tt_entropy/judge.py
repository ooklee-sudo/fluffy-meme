"""H5 / H6 judging (PREREGISTRATION_H5_H7.md): pairwise LLM judgments of generated customer-service replies.

For each brand file from gen_replies.py, each evaluation message and each pair of methods, a judge model sees
five real replies of the brand (its usual voice), the customer's message and two replies in random order
(the brand's actual reply is not shown), and returns JSON: which reply better matches the brand's voice,
which is more helpful, whether each makes unsupported claims, whether each could be sent as is, and which it
would rather send. Results are appended to a JSONL cache, so reruns resume and never pay twice.

Pairs: lora:1 vs rag-8 (primary), vera:256 vs rag-8, lora:1 vs zero. A second judge sees a fixed 20% sample
of the primary pairs.

Usage:
  python judge.py results/h5_gen --out results/h5_judge.jsonl --max-cost 10
Needs OpenRouter access (in this project's cloud session the key is injected by the network proxy).
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import random
import threading
import time
import urllib.request

PRIMARY_JUDGE = "anthropic/claude-haiku-5.5"
SECOND_JUDGE = "openai/gpt-5-mini"
PAIRS = [("lora:1", "rag-8"), ("vera:256", "rag-8"), ("lora:1", "zero")]
URL = "https://openrouter.ai/api/v1/chat/completions"

PROMPT = """You are reviewing customer-service replies written for the Twitter support account of a company ({brand}).

Five real replies written by this company's support team, showing its usual voice:
{examples}

Customer message:
\"\"\"{customer}\"\"\"

Reply A:
\"\"\"{a}\"\"\"

Reply B:
\"\"\"{b}\"\"\"

Evaluate both replies as the company's support manager would. Return only a JSON object with these keys:
"voice": which reply better matches the company's usual voice and style: "A", "B" or "tie"
"helpfulness": which reply better addresses the customer's message: "A", "B" or "tie"
"unsupported_A": true if reply A states specific facts, promises, names or details that are not supported by the customer's message or that the company could not know, else false
"unsupported_B": the same for reply B
"send_as_is_A": true if you would let reply A be sent without editing, else false
"send_as_is_B": the same for reply B
"overall": which reply you would rather send: "A", "B" or "tie\""""

lock = threading.Lock()
spent = [0.0]


def call(model, prompt, tries=4):
    """One judgment. Reasoning models get a low reasoning effort and room to answer after reasoning. Every
    billed attempt, failed or not, is added to the running cost."""
    body = json.dumps(dict(model=model, temperature=0, max_tokens=3000, reasoning={"effort": "low"},
                           response_format={"type": "json_object"},
                           messages=[{"role": "user", "content": prompt}])).encode()
    err = None
    for t in range(tries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json",
                                                                  "Authorization": "Bearer proxy-injected"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            cost = float(d.get("usage", {}).get("cost") or 0.0)
            with lock:
                spent[0] += cost
            text = d["choices"][0]["message"].get("content") or ""
            out = json.loads(text[text.find("{"): text.rfind("}") + 1])
            return out, cost
        except Exception as e:  # network, rate limit, empty or malformed answer: back off and retry
            err = e
            time.sleep(2 * (t + 1))
    raise RuntimeError(f"{model}: {err}")


def tasks(gen_dir, second_share, seed):
    out = []
    for path in sorted(glob.glob(os.path.join(gen_dir, "*.json"))):
        g = json.load(open(path))
        ex = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(g["style_examples"]))
        for j, it in enumerate(g["items"]):
            for a, b in PAIRS:
                key = f"{g['brand']}|{j}|{a}|{b}"
                rng = random.Random(f"{seed}|{key}")
                flip = rng.random() < 0.5
                ra, rb = (it["replies"][b], it["replies"][a]) if flip else (it["replies"][a], it["replies"][b])
                prompt = PROMPT.format(brand=g["brand"], examples=ex, customer=it["customer"], a=ra, b=rb)
                base = dict(brand=g["brand"], item=j, first=a, second=b, flip=flip)
                out.append((PRIMARY_JUDGE, key, prompt, base))
                if (a, b) == PAIRS[0] and random.Random(f"second|{seed}|{key}").random() < second_share:
                    out.append((SECOND_JUDGE, key, prompt, base))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gen_dir")
    ap.add_argument("--out", default="results/h5_judge.jsonl")
    ap.add_argument("--max-cost", type=float, default=10.0, help="stop when this many US dollars are spent")
    ap.add_argument("--second-share", type=float, default=0.2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="judge only this many new tasks (0 = all)")
    a = ap.parse_args()
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            r = json.loads(line)
            done.add((r["judge"], r["key"]))
            spent[0] += r.get("cost", 0.0)
    todo = [t for t in tasks(a.gen_dir, a.second_share, a.seed) if (t[0], t[1]) not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(done)} judgments cached (${spent[0]:.3f}); {len(todo)} to do; cap ${a.max_cost:.2f}")

    def work(t):
        model, key, prompt, base = t
        if spent[0] >= a.max_cost:
            return None
        out, cost = call(model, prompt)
        rec = dict(base, judge=model, key=key, verdict=out, cost=cost)
        with lock:
            with open(a.out, "a") as f:
                f.write(json.dumps(rec) + "\n")
        return rec

    n = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for rec in ex.map(lambda t: _safe(work, t), todo):
            n += rec is not None
            if n and n % 200 == 0:
                print(f"  {n}/{len(todo)} done, ${spent[0]:.3f} spent")
    print(f"finished {n} new judgments; total spent ${spent[0]:.3f}"
          + ("  (stopped at the cost cap)" if spent[0] >= a.max_cost else ""))


def _safe(fn, t):
    try:
        return fn(t)
    except Exception as e:
        print(f"  failed {t[1]} ({t[0]}): {e}")
        return None


if __name__ == "__main__":
    main()
