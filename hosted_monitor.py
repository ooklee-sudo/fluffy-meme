"""Weekly (or daily) monitor of hosted LLM APIs with a FIXED question set.

Purpose: build the panel the repository study lacks, i.e. a measured performance series for hosted models
that can later be merged with vendor refresh dates (events_hosted.csv) in hosted_analyze.py.

Design choices that matter for the analysis:
  * the question set is generated once from a seed and never changes, so score changes are not question changes;
  * temperature 0, one call per question per run;
  * the model string RETURNED by the API is stored with every answer, so silent alias switches are visible;
  * every answer is stored raw, so scoring can be redone later.

Keys are read from the environment: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY.
Edit MODELS below. Use ALIASES where you want to track what the vendor serves under a moving name
(e.g. "gpt-4o"), because refresh decisions show up there; pinned snapshots should not change.

Usage:
    python hosted_monitor.py                 # one run over all configured models, appends to results/hosted_runs.csv
    python hosted_monitor.py --mock          # no network; fake model with built-in drift, for testing the pipeline
Schedule it (Windows Task Scheduler or cron) once a day. Roughly 90 short calls per model per run.
"""
import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import time

import requests

# provider, model name as sent to the API. Replace with the models you want to follow.
MODELS = [
    ("openai", "gpt-4o"),
    ("anthropic", "claude-sonnet-4-20250514"),
    ("google", "gemini-2.5-flash"),
]
OUT = "results/hosted_runs.csv"
FIELDS = ["ts", "provider", "model_requested", "model_returned", "task", "qid", "gold", "response", "correct", "latency_s", "error"]


# ----------------------------------------------------------------- fixed question set
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def build_questions(seed=7):
    """30 primality, 30 arithmetic, 30 strict-format questions. Same on every run and every machine."""
    r = random.Random(seed)
    qs = []
    for i in range(30):
        n = r.randrange(10007, 99991)
        if i % 2 == 0:  # half the numbers are prime
            while not is_prime(n):
                n += 1
        else:
            while is_prime(n):
                n += 1
        qs.append(("prime", i, f"Is {n} a prime number? Answer with exactly one word: Yes or No.", "yes" if is_prime(n) else "no"))
    for i in range(30):
        a, b, c = r.randrange(100, 999), r.randrange(100, 999), r.randrange(11, 99)
        qs.append(("arith", i, f"Compute {a} * {b} + {c}. Reply with the number only.", str(a * b + c)))
    for i in range(30):
        w = [r.choice(["alpha", "river", "stone", "ember", "violet", "harbor", "quartz", "meadow"]) for _ in range(3)]
        k = r.randrange(2, 9)
        qs.append(("format", i, f'Return a JSON object with keys "words" (the list {json.dumps(w)} in reverse order) and "n" (the integer {k}). '
                               f"Output only the JSON, no other text.", json.dumps({"words": w[::-1], "n": k}, sort_keys=True)))
    return qs


def score(task, gold, text):
    t = (text or "").strip().lower()
    if task == "prime":
        m = re.search(r"\b(yes|no)\b", t)
        return int(bool(m) and m.group(1) == gold)
    if task == "arith":
        m = re.findall(r"-?\d[\d,]*", t)
        return int(bool(m) and m[-1].replace(",", "") == gold)
    try:
        s = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
        return int(json.dumps(json.loads(s), sort_keys=True) == gold)
    except Exception:
        return 0


# ----------------------------------------------------------------- providers (plain HTTP, no SDKs)
def call(provider, model, prompt):
    if provider == "openai":
        r = requests.post("https://api.openai.com/v1/chat/completions", timeout=90,
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                          json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "seed": 7, "max_tokens": 200})
        r.raise_for_status(); j = r.json()
        return j["choices"][0]["message"]["content"], j.get("model", "")
    if provider == "anthropic":
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=90,
                          headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                          json={"model": model, "max_tokens": 200, "temperature": 0, "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status(); j = r.json()
        return "".join(b.get("text", "") for b in j["content"]), j.get("model", "")
    if provider == "google":
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", timeout=90,
                          headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                          json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "maxOutputTokens": 200}})
        r.raise_for_status(); j = r.json()
        return j["candidates"][0]["content"]["parts"][0].get("text", ""), j.get("modelVersion", "")
    raise ValueError(provider)


def mock_call(model, gold, task, day_index):
    """Fake model whose accuracy drifts down after day 20 and resets at day 40 (a 'refresh')."""
    drift = max(0, day_index - 20) if day_index < 40 else max(0, day_index - 60)
    p_ok = max(0.3, 0.95 - 0.015 * drift)
    ok = random.random() < p_ok
    if task == "prime":
        a = gold if ok else ("no" if gold == "yes" else "yes")
    elif task == "arith":
        a = gold if ok else str(int(gold) + 10)
    else:
        a = gold if ok else "not json"
    return a, f"{model}-mock"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-days", type=int, default=70, help="with --mock, simulate this many daily runs")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    new = not os.path.exists(a.out)
    qs = build_questions()
    runs = range(a.mock_days) if a.mock else [0]
    random.seed(1)
    with open(a.out, "a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for day in runs:
            ts = (dt.datetime(2026, 1, 1) + dt.timedelta(days=day)) if a.mock else dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            for provider, model in (MODELS if not a.mock else [("mock", "mock-model")]):
                for task, qid, prompt, gold in qs:
                    t0, err, resp, ret = time.time(), "", "", ""
                    try:
                        resp, ret = mock_call(model, gold, task, day) if a.mock else call(provider, model, prompt)
                    except Exception as e:  # keep going; errors are data too
                        err = str(e)[:200]
                    w.writerow(dict(ts=ts.isoformat(timespec="seconds"), provider=provider, model_requested=model, model_returned=ret,
                                    task=task, qid=qid, gold=gold, response=(resp or "")[:500], correct=score(task, gold, resp) if not err else "",
                                    latency_s=round(time.time() - t0, 2), error=err))
            f.flush()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
