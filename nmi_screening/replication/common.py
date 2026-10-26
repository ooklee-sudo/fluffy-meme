import json, os, re, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data"); os.makedirs(DATA, exist_ok=True)
UA = {"User-Agent": "screening-replication/0.1 (research; contact: see repository README)"}

def http(url, data=None, headers=None, timeout=60, tries=3, binary=False):
    h = dict(UA); h.update(headers or {})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read(); return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410): return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return None

def words(t): return len(t.split())

import threading, fcntl
_lock = threading.Lock()
LEDGER = os.path.join(DATA, "spend.json")
def _read():
    try: return json.load(open(LEDGER))
    except Exception: return {"total": 0.0, "by": {}}
def add_spend(x, tag):
    """Several processes share the ledger: serialize with a file lock and replace the file atomically."""
    with _lock, open(LEDGER + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        d = _read(); d["total"] += x; d["by"][tag] = d["by"].get(tag, 0.0) + x
        tmp = LEDGER + f".{os.getpid()}.tmp"; json.dump(d, open(tmp, "w"), indent=1); os.replace(tmp, LEDGER)
def spend(): return _read()["total"]

def chat(model, messages, max_tokens=4000, temperature=0.7, cap=100.0, reasoning_low=False, timeout=600):
    """OpenRouter chat call. Authentication is injected by the sandbox proxy, or set OPENROUTER_API_KEY. Returns (text, cost)."""
    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    if reasoning_low: body["reasoning"] = {"effort": "low"}
    if os.environ.get("OR_SORT"): body["provider"] = {"sort": os.environ["OR_SORT"]}
    hdr = {"Content-Type": "application/json"}
    if os.environ.get("OPENROUTER_API_KEY"): hdr["Authorization"] = "Bearer " + os.environ["OPENROUTER_API_KEY"]
    for i in range(4):
        if spend() >= cap: raise SystemExit(f"spend cap reached: ${spend():.2f}")
        try:
            j = json.loads(http("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), headers=hdr, timeout=timeout, tries=1) or "null")
        except Exception: j = None
        if not j or "choices" not in j: time.sleep(5 * (i + 1)); continue
        cost = (j.get("usage") or {}).get("cost") or 0.0; add_spend(cost, model)
        t = j["choices"][0]["message"].get("content")
        if t: return t, cost
    return "", 0.0
