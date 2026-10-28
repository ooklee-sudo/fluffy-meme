"""Shared helpers: OpenRouter chat calls (key is injected by the proxy) and JSONL IO."""
import json
import os
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(model, prompt, max_tokens=1500, temperature=0.7, system=None, retries=5):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}
    for k in range(retries):
        try:
            r = requests.post(URL, json=body, headers={"Authorization": "Bearer dummy"}, timeout=120)
            if r.status_code == 200:
                c = r.json()["choices"][0]
                return c["message"]["content"] or ""
            err = r.text[:200]
        except requests.RequestException as e:
            err = str(e)
        time.sleep(2 ** k)
    raise RuntimeError(f"chat failed for {model}: {err}")


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
