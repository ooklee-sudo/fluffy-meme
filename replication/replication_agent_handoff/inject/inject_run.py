"""Fault-injection experiment on tau2-bench (airline, retail).

Each run is (model, domain, task, arm, rep). Arms:
  control - no injection; a virtual injection index j is still drawn and recorded
  single  - the agent's j-th tool call (j in 1..3) is not executed; it returns a transient error
  blame   - as single, but the error reads like the agent's own mistake ("<argument> '<value>' not found")
  multi   - after the first call, each agent tool call is replaced by the error with probability P_MULTI (at most 3)
Injected calls do not change the database. Agent errors are the tool calls the real environment rejects.
Success is the environment (database) check. Results are appended to results/<model>.jsonl; reruns skip done keys.
Usage: python inject_run.py MODEL [--tasks N] [--reps R] [--arms a,b] [--workers W] [--cap USD]
"""
import argparse, json, os, random, sys, time, traceback, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("OPENROUTER_API_KEY", "proxy-injected")  # the sandbox proxy adds the real credential
os.environ.setdefault("TAU2_DATA_DIR", str(HERE / "tau2-bench" / "data"))
MODELS = {"gpt61terra": "openrouter/openai/gpt-6.1-terra", "sonnet55": "openrouter/anthropic/claude-sonnet-5.5",
          "llama8b": "openrouter/meta-llama/llama-3.1-8b-instruct",
          "llama70b": "openrouter/meta-llama/llama-3.1-70b-instruct",
          "deepseek": "openrouter/deepseek/deepseek-chat-v3.1"}
USER_LLM = "openrouter/openai/gpt-4.1-mini"
P_MULTI, MAX_MULTI = 0.25, 3
INJECT_MSG = "Error: service temporarily unavailable (503). The request was not processed."
TEMP = 0.5

import threading
_TLS = threading.local()
_PATCH_LOCK = threading.Lock()
IGNORE = {"llama8b": ["Cerebras", "Groq"], "llama70b": ["Cerebras", "Groq"], "deepseek": ["CoreWeave"], "gpt61terra": [], "sonnet55": []}
# commercial models: low reasoning effort so that they are comparable with the non-reasoning open models
EXTRA = {"gpt61terra": {"reasoning": {"effort": "low"}}, "sonnet55": {"reasoning": {"effort": "low"}, "cache_control": {"type": "ephemeral"}}}


class _State:  # injection state of the run executing in the current thread
    def _d(self):
        if not hasattr(_TLS, "d"): _TLS.d = {}
        return _TLS.d
    def __getitem__(self, k): return self._d()[k]
    def __setitem__(self, k, v): self._d()[k] = v
    def get(self, k, default=None): return self._d().get(k, default)
    def __bool__(self): return bool(self._d())
    def clear(self): self._d().clear()
    def update(self, **kw): self._d().update(kw)


STATE = _State()


def inject_msg(arm, message):
    if arm != "blame": return INJECT_MSG
    for k, v in (message.arguments or {}).items():
        if isinstance(v, (str, int)) and str(v):
            return f"Error: {k.replace('_', ' ')} '{v}' not found"
    return "Error: invalid request arguments"


def _patch():
    from tau2.environment.environment import Environment
    from tau2.data_model.message import ToolMessage
    orig = Environment.get_response

    def get_response(self, message):
        s = STATE
        if not s or message.requestor != "assistant":
            return orig(self, message)
        key = (message.id, message.name, json.dumps(message.arguments, sort_keys=True, default=str))
        occ = s["seen"].get((s.get("phase"), key), 0); s["seen"][(s.get("phase"), key)] = occ + 1
        if s.get("phase") == "eval":  # evaluation replays the trajectory: injected calls stay unexecuted
            if (key, occ) in s["inj_ids"]:
                return ToolMessage(id=message.id, content=inject_msg(s["arm"], message), requestor=message.requestor, role="tool", error=True)
            return orig(self, message)
        s["n"] += 1; i = s["n"]
        inj = False
        if s["arm"] in ("single", "blame") and i == s["j"]: inj = True
        elif s["arm"] == "multi" and i >= 2 and s["n_inj"] < MAX_MULTI and s["rng"].random() < P_MULTI: inj = True
        if inj:
            s["n_inj"] += 1; s["inj_ids"].add((key, occ)); s["inj_msg"] = msg = inject_msg(s["arm"], message)
            s["calls"].append(dict(i=i, name=message.name, injected=1, error=1))
            return ToolMessage(id=message.id, content=msg, requestor=message.requestor, role="tool", error=True)
        r = orig(self, message)
        s["calls"].append(dict(i=i, name=message.name, injected=0, error=int(bool(r.error)), msg=(r.content[:160] if r.error else "")))
        return r
    Environment.get_response = get_response
    import tau2.utils.llm_utils as lu
    _orig_cost = lu.get_response_cost

    def get_response_cost(response):  # OpenRouter reports the billed cost in usage.cost
        try:
            c = getattr(response.usage, "cost", None)
            if c is None and isinstance(response.usage, dict): c = response.usage.get("cost")
            if c is not None: return float(c)
        except Exception: pass
        return _orig_cost(response)
    lu.get_response_cost = get_response_cost
    import json as _json

    class _LenientJSON:  # tool-call arguments: keep the first JSON object if the model appends extra text
        def __getattr__(self, k): return getattr(_json, k)
        def loads(self, x, *a, **kw):  # only used for tool-call arguments in llm_utils
            try: v = _json.loads(x, *a, **kw)
            except (_json.JSONDecodeError, TypeError):
                try: v = _json.JSONDecoder().raw_decode((x or "").strip())[0]
                except Exception: v = None
                v = ("bad", v)
            bad = isinstance(v, tuple)
            if bad: v = v[1]
            if not isinstance(v, dict):
                bad = True; v = v[0] if isinstance(v, list) and v and isinstance(v[0], dict) else {}
            if bad and STATE: STATE["malformed"] = STATE.get("malformed", 0) + 1
            return v
    lu.json = _LenientJSON()
    import tau2.runner.simulation as rs
    orig_eval = rs.evaluate_simulation

    def evaluate_simulation(*args, **kw):
        STATE["phase"] = "eval"
        return orig_eval(*args, **kw)
    rs.evaluate_simulation = evaluate_simulation


def run_one(job):
    with _PATCH_LOCK:
        if not getattr(run_one, "patched", False): _patch(); run_one.patched = True
    from tau2.runner.batch import run_single_task
    from tau2.runner.helpers import get_tasks
    from tau2.data_model.simulation import TextRunConfig
    from tau2.evaluator.evaluator import EvaluationType
    m, dom, tid, arm, rep, seed = job["model"], job["domain"], job["task"], job["arm"], job["rep"], job["seed"]
    rng = random.Random(seed)
    STATE.clear(); STATE.update(arm=arm, j=rng.choice([1, 2, 3]), n=0, n_inj=0, calls=[], rng=rng, inj_ids=set(), seen={}, phase="run")
    task = get_tasks(dom, task_ids=[tid])[0]
    cfg = TextRunConfig(domain=dom, agent="llm_agent", user="user_simulator", llm_agent=MODELS[m],
                        llm_args_agent={"temperature": TEMP, "extra_body": {"provider": {"ignore": IGNORE[m]}, **EXTRA.get(m, {})}}, llm_user=USER_LLM, llm_args_user={"temperature": TEMP},
                        max_steps=100, max_errors=10, seed=seed)
    t0 = time.time()
    try:
        sim = run_single_task(cfg, task, seed=seed, evaluation_type=EvaluationType.ENV)
        rew = sim.reward_info.reward if sim.reward_info else None
        from tau2.data_model.message import AssistantMessage, UserMessage
        ac = sum(m_.cost or 0 for m_ in (sim.messages or []) if isinstance(m_, AssistantMessage))
        uc = sum(m_.cost or 0 for m_ in (sim.messages or []) if isinstance(m_, UserMessage))
        out = dict(ok=1, reward=rew, termination=str(sim.termination_reason), agent_cost=ac, user_cost=uc,
                   n_messages=len(sim.messages or []))
    except Exception as e:
        mod = type(e).__module__ or ""
        transient = mod.startswith(("litellm", "openai", "httpx")) or "Openrouter" in str(e)[:300] or "BrokenProcessPool" in type(e).__name__
        # malformed agent output (bad JSON tool arguments etc.) ends the run as a failure; API problems are retried later
        out = dict(ok=0 if transient else 1, crashed=1, reward=None if transient else 0.0, err=f"{type(e).__name__}: {e}"[:400], tb=traceback.format_exc()[-800:])
    out.update(key=job["key"], model=m, domain=dom, task=tid, arm=arm, rep=rep, seed=seed, j=STATE["j"], n_inj=STATE["n_inj"], malformed=STATE.get("malformed", 0),
               calls=STATE["calls"], secs=round(time.time() - t0, 1))
    STATE.clear()
    return out


def credits_used():
    try:
        with urllib.request.urlopen("https://openrouter.ai/api/v1/credits", timeout=30) as r:
            d = json.load(r)["data"]; return d["total_usage"], d["total_credits"]
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model"); ap.add_argument("--tasks", type=int, default=0); ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--arms", default="control,single,blame,multi"); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cap", type=float, default=150.0, help="stop when this run has spent more than this many USD")
    ap.add_argument("--domains", default="airline,retail")
    a = ap.parse_args()
    import logging
    from loguru import logger
    logger.remove(); logger.add(sys.stderr, level="ERROR", filter=lambda r: "isn't mapped" not in r["message"])
    logging.getLogger("LiteLLM").setLevel(logging.ERROR)
    from tau2.runner.helpers import get_tasks
    jobs = []
    for dom in a.domains.split(","):
        ids = [t.id for t in get_tasks(dom)]
        if a.tasks: ids = ids[:a.tasks]
        for tid in ids:
            for rep in range(a.reps):
                for arm in a.arms.split(","):
                    seed = (1000003 * rep + sum(map(ord, dom + tid))) % (2 ** 31)
                    jobs.append(dict(model=a.model, domain=dom, task=tid, arm=arm, rep=rep, seed=seed, key=f"{a.model}|{dom}|{tid}|{arm}|{rep}"))
    out = HERE / "results" / f"{a.model}.jsonl"; out.parent.mkdir(exist_ok=True)
    done = set()
    if out.exists():
        for l in out.open():
            try:
                r = json.loads(l)
                if r.get("ok"): done.add(r["key"])
            except Exception: pass
    todo = [j for j in jobs if j["key"] not in done]
    u0, tot = credits_used()
    print(f"{len(jobs)} jobs, {len(done)} done, {len(todo)} to run; credits used {u0} of {tot}", flush=True)
    stop = False; n = 0
    with ThreadPoolExecutor(a.workers) as ex, out.open("a") as f:
        futs = {}
        it = iter(todo)
        def submit():
            j = next(it, None)
            if j is not None: futs[ex.submit(run_one, j)] = j
        for _ in range(a.workers * 2): submit()
        while futs:
            for fu in as_completed(list(futs)):
                futs.pop(fu)
                try: r = fu.result()
                except Exception as e: r = dict(ok=0, key=None, err=str(e)[:300])
                f.write(json.dumps(r) + "\n"); f.flush(); n += 1
                if n % 20 == 0:
                    u, _ = credits_used()
                    spent = (u - u0) if (u is not None and u0 is not None) else None
                    print(f"{n} finished; spent this run ${spent if spent is None else round(spent, 2)}", flush=True)
                    if spent is not None and spent > a.cap: stop = True; print("spend cap reached; stopping", flush=True)
                if not stop: submit()
                break
    u, _ = credits_used()
    print(f"done; spent this run ${None if u is None or u0 is None else round(u - u0, 2)}", flush=True)


if __name__ == "__main__":
    main()
