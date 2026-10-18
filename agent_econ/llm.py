"""OpenRouter client with a persistent, thread-safe spend ledger and a hard budget cap."""
import json, os, threading, time
import requests

URL = "https://openrouter.ai/api/v1/chat/completions"
LEDGER = os.environ.get("AE_LEDGER", os.path.join(os.path.dirname(__file__), "results", "spend.json"))
CAP_USD = float(os.environ.get("AE_BUDGET_USD", "45"))  # 5 USD margin under the 50 USD limit

_lock = threading.Lock()


class BudgetExceeded(RuntimeError):
    pass


def _read():
    try:
        return json.load(open(LEDGER))
    except FileNotFoundError:
        return {"total_usd": 0.0, "calls": 0, "by_model": {}}


def spent():
    with _lock:
        return _read()["total_usd"]


def _add(model, cost, tin, tout):
    with _lock:
        d = _read()
        d["total_usd"] += cost
        d["calls"] += 1
        m = d["by_model"].setdefault(model, {"usd": 0.0, "calls": 0, "tin": 0, "tout": 0})
        m["usd"] += cost; m["calls"] += 1; m["tin"] += tin; m["tout"] += tout
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        json.dump(d, open(LEDGER, "w"), indent=1)


def chat(model, system, user, max_tokens=1500, temperature=1.0, retries=4):
    """Return (text, cost_usd, finish_reason, completion_tokens). Raises BudgetExceeded before a call if the cap is already reached."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    if spent() >= CAP_USD:
        raise BudgetExceeded(f"spend {spent():.2f} USD >= cap {CAP_USD:.2f} USD")
    body = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
            "usage": {"include": True},
            "reasoning": {"enabled": False},   # agents answer directly; hidden reasoning would eat max_tokens and cost
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    err = None
    for i in range(retries):
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=120)
            if r.status_code == 200:
                j = r.json()
                u = j.get("usage", {})
                cost = float(u.get("cost") or 0.0)
                _add(model, cost, u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
                ch = j["choices"][0]
                return (ch["message"].get("content") or ""), cost, ch.get("finish_reason"), u.get("completion_tokens", 0)
            err = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code == 400 and "reasoning" in body:   # model cannot disable reasoning: retry without
                del body["reasoning"]
                continue
            if r.status_code in (401, 402, 403):
                break
        except requests.RequestException as e:
            err = str(e)
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"OpenRouter call failed: {err}")
