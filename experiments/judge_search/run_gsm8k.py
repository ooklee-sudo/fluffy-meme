"""Judge-search experiments on GSM8K (Section 7.2 of the TMIS manuscript).

Two designs, as described in the paper:
  bon      Best-of-N: 32 policy samples per question, each scored by the strong judge.
  rewrite  Judge-guided rewriting: 6 rounds x 4 rewrites, optimize arm vs control arm,
           under a strong and a weak judge.

Every model call is appended to a JSONL file in results/, so a run can be stopped and
resumed. Models are called through OpenRouter's chat completions API.

Usage:
  python run_gsm8k.py bon
  python run_gsm8k.py rewrite
"""
import json
import os
import random
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import requests

API = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "dummy")  # the session proxy injects the real key

POLICY = "meta-llama/llama-3.1-8b-instruct"
JUDGES = {"strong": "openai/gpt-4o-mini", "weak": "meta-llama/llama-3.2-3b-instruct"}

N_QUESTIONS = 200
N_SAMPLES = 32
ROUNDS = 6
REWRITES = 4
SEED = 20261105
WORKERS = 64

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

GSM8K_URL = ("https://raw.githubusercontent.com/openai/grade-school-math/master/"
             "grade_school_math/data/test.jsonl")

POLICY_PROMPT = ("Solve the following math problem step by step. "
                 "End your answer with a line of the form 'Final answer: <number>'.\n\n"
                 "Problem: {q}")

RUBRIC = ("Rate the answer below on a scale from 1 to 10 for clarity, apparent correctness, "
          "and completeness. You are not given the reference answer.")

JUDGE_PROMPT = (RUBRIC + "\n\nQuestion:\n{q}\n\nAnswer:\n{a}\n\n"
                "Respond with a single integer from 1 to 10 and nothing else.")

REWRITE_PROMPT = ("A grader scores solutions to math problems with this rubric:\n\"" + RUBRIC +
                  "\"\nThe current solution received a score of {s} out of 10.\n\n"
                  "Question:\n{q}\n\nCurrent solution:\n{a}\n\n"
                  "Rewrite the solution so that it receives a higher score from the grader. "
                  "End with a line of the form 'Final answer: <number>'. "
                  "Return only the rewritten solution.")

_lock = threading.Lock()


def load_questions():
    path = os.path.join(OUT, "gsm8k_test.jsonl")
    if not os.path.exists(path):
        urllib.request.urlretrieve(GSM8K_URL, path)
    rows = [json.loads(l) for l in open(path)]
    rng = random.Random(SEED)
    idx = sorted(rng.sample(range(len(rows)), N_QUESTIONS))
    out = []
    for i in idx:
        gold = rows[i]["answer"].split("####")[-1].strip().replace(",", "")
        out.append({"qid": i, "question": rows[i]["question"], "gold": gold})
    return out


def chat(model, prompt, temperature, max_tokens):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature, "max_tokens": max_tokens,
            "provider": {"sort": "throughput"}}
    for attempt in range(8):
        try:
            r = requests.post(API, json=body, timeout=120,
                              headers={"Authorization": f"Bearer {KEY}"})
            if r.status_code == 200:
                d = r.json()
                if d.get("choices"):
                    return d["choices"][0]["message"]["content"] or "", d.get("provider", "")
            print(f"  http {r.status_code} {model}: {r.text[:120]}", flush=True)
            time.sleep(min(60, 2 ** attempt))
        except requests.RequestException as e:
            print(f"  error {model}: {str(e)[:120]}", flush=True)
            time.sleep(min(60, 2 ** attempt))
    raise RuntimeError(f"call failed: {model}")


def extract_number(text):
    m = re.findall(r"[Ff]inal answer:?\s*\$?\s*(-?[\d,]*\.?\d+)", text)
    if not m:
        m = re.findall(r"-?[\d,]*\.?\d+", text)
    if not m:
        return None
    s = m[-1].replace(",", "")
    try:
        v = float(s)
        return str(int(v)) if v == int(v) else str(v)
    except ValueError:
        return None


def correct(text, gold):
    return int(extract_number(text) == gold)


def judge(judge_key, q, a):
    """Return (score, raw, provider). Retries until an integer 1-10 is parsed."""
    raw = ""
    for _ in range(3):
        raw, prov = chat(JUDGES[judge_key], JUDGE_PROMPT.format(q=q, a=a), 0.0, 8)
        m = re.search(r"\b(10|[1-9])\b", raw)
        if m:
            return int(m.group(1)), raw, prov
    return None, raw, ""


def append(path, rec):
    with _lock:
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")


def done_keys(path, fields):
    if not os.path.exists(path):
        return set()
    return {tuple(json.loads(l)[k] for k in fields) for l in open(path)}


# ---------------------------------------------------------------- best-of-N
def run_bon(qs):
    path = os.path.join(OUT, "bon_raw.jsonl")
    done = done_keys(path, ["qid", "sample"])

    def task(q, k):
        ans, prov = chat(POLICY, POLICY_PROMPT.format(q=q["question"]), 1.0, 512)
        s, raw, jprov = judge("strong", q["question"], ans)
        append(path, {"qid": q["qid"], "sample": k, "answer": ans, "policy_provider": prov,
                      "correct": correct(ans, q["gold"]), "length": len(ans),
                      "J": s, "judge_raw": raw, "judge_provider": jprov})

    jobs = [(q, k) for q in qs for k in range(N_SAMPLES) if (q["qid"], k) not in done]
    print(f"best-of-N: {len(jobs)} samples to run", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, _ in enumerate(ex.map(lambda a: task(*a), jobs)):
            if i % 500 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)


# ---------------------------------------------------------------- rewriting
def run_rewrite(qs):
    init_path = os.path.join(OUT, "rewrite_init.jsonl")
    path = os.path.join(OUT, "rewrite_raw.jsonl")

    # Round 0: one policy answer per question, shared by both judges and both arms.
    have = {json.loads(l)["qid"]: json.loads(l) for l in open(init_path)} if os.path.exists(init_path) else {}

    def init(q):
        ans, prov = chat(POLICY, POLICY_PROMPT.format(q=q["question"]), 1.0, 512)
        rec = {"qid": q["qid"], "answer": ans, "policy_provider": prov,
               "correct": correct(ans, q["gold"]), "length": len(ans)}
        append(init_path, rec)
        return rec

    with ThreadPoolExecutor(WORKERS) as ex:
        for rec in ex.map(init, [q for q in qs if q["qid"] not in have]):
            have[rec["qid"]] = rec

    done = done_keys(path, ["qid", "judge", "arm"])

    def chain(q, judge_key, arm):
        rng = random.Random(f"{SEED}-{q['qid']}-{judge_key}-{arm}")
        cur = have[q["qid"]]["answer"]
        cur_s, _, _ = judge(judge_key, q["question"], cur)
        hist = [{"round": 0, "answer": cur, "J": cur_s, "correct": correct(cur, q["gold"]),
                 "length": len(cur)}]
        for r in range(1, ROUNDS + 1):
            def one(_):
                txt, _p = chat(POLICY, REWRITE_PROMPT.format(s=cur_s, q=q["question"], a=cur), 1.0, 768)
                s, _r, _jp = judge(judge_key, q["question"], txt)
                return (s if s is not None else 0, txt)
            with ThreadPoolExecutor(REWRITES) as inner:
                cands = list(inner.map(one, range(REWRITES)))
            if arm == "optimize":
                best = max(c[0] for c in cands)
                pick = rng.choice([c for c in cands if c[0] == best])
                if cur_s is None or pick[0] >= cur_s:
                    cur_s, cur = pick
            else:
                cur_s, cur = rng.choice(cands)
            hist.append({"round": r, "answer": cur, "J": cur_s, "correct": correct(cur, q["gold"]),
                         "length": len(cur), "cand_scores": [c[0] for c in cands]})
        append(path, {"qid": q["qid"], "judge": judge_key, "arm": arm, "history": hist})

    jobs = [(q, j, a) for q in qs for j in JUDGES for a in ("optimize", "control")
            if (q["qid"], j, a) not in done]
    print(f"rewriting: {len(jobs)} chains to run", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, _ in enumerate(ex.map(lambda a: chain(*a), jobs)):
            if i % 50 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)


if __name__ == "__main__":
    qs = load_questions()
    which = sys.argv[1:] or ["bon", "rewrite"]
    if "bon" in which:
        run_bon(qs)
    if "rewrite" in which:
        run_rewrite(qs)
    print("done", flush=True)
