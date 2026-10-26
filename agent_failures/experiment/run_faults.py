"""Fault-injection experiment on tau-bench (tau2-bench, MIT license).

Conditions (same tasks, same agent model, same seeds):
  baseline : released harness, no injected faults
  raw      : a share p of agent WRITE tool calls fail at the connector; the agent receives an HTML 400 page as the
             tool output, not flagged as an error (the 'leaked page' pattern); the write is NOT applied
  typed    : same faults, same call indices, returned as a typed envelope
             {"ok": false, "code": "http_400", "retryable": true, "provenance": "connector:<tool>"}, flagged as an error
The harness keeps a ledger of write calls (attempted / faulted / applied) used by the claim-versus-state monitor.

Run with the tau2-bench virtual environment, e.g.
  /home/user/sierra-research/tau2-bench/.venv/bin/python run_faults.py --domain airline --n-tasks 10 --conditions baseline --out runs/pilot.jsonl
"""
import argparse, hashlib, json, os, random, sys, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault("OPENROUTER_API_KEY", "placeholder")  # the proxy injects the real key

from tau2.data_model.message import ToolMessage
from tau2.environment.environment import Environment
from tau2.environment.toolkit import ToolType
from tau2.evaluator.evaluator import EvaluationType
from tau2.runner.batch import run_single_task
from tau2.runner.helpers import load_tasks
from tau2.data_model.simulation import TextRunConfig

HTML_400 = ("<html><head><title>400 Bad Request</title></head><body><h1>Bad Request</h1>"
            "<p>Your browser sent a request that this server could not understand.</p><hr>"
            "<address>Apache/2.4.52 (Ubuntu) Server at api.internal Port 443</address></body></html>")

_ctx = threading.local()
_orig_get_response = Environment.get_response


def _patched_get_response(self, message):
    cfg = getattr(_ctx, "cfg", None)
    if cfg is None or message.requestor != "assistant":
        return _orig_get_response(self, message)
    try:
        is_write = self.tools.tool_type(message.name) == ToolType.WRITE
    except Exception:
        is_write = False
    if not is_write:
        return _orig_get_response(self, message)
    # decisions are keyed by the tool-call id, so the evaluator's replay of the trajectory sees the same faults
    h = hashlib.sha256(f"{cfg['seed']}|{cfg['task_id']}|{message.id}".encode()).digest()
    faulted = cfg["condition"] != "baseline" and (int.from_bytes(h[:4], "big") / 2**32) < cfg["p"]
    seen = cfg["seen"]
    if not faulted:
        resp = _orig_get_response(self, message)
        if message.id not in seen:
            seen[message.id] = True
            cfg["ledger"].append(dict(tool=message.name, faulted=False, applied=not resp.error))
        return resp
    if message.id not in seen:
        seen[message.id] = True
        cfg["ledger"].append(dict(tool=message.name, faulted=True, applied=False))
    if cfg["condition"] == "raw":
        return ToolMessage(id=message.id, content=HTML_400, requestor=message.requestor, role="tool", error=False)
    envelope = json.dumps({"ok": False, "code": "http_400", "retryable": True, "provenance": f"connector:{message.name}"})
    return ToolMessage(id=message.id, content=envelope, requestor=message.requestor, role="tool", error=True)


Environment.get_response = _patched_get_response

import litellm
COST = {"total": 0.0, "calls": 0, "tokens": 0}
_cost_lock = threading.Lock()


def _track_cost(kwargs, completion_response, start_time, end_time):
    c = kwargs.get("response_cost") or 0.0
    try:
        c = c or float(completion_response.usage.cost)
    except Exception:
        pass
    with _cost_lock:
        COST["total"] += c or 0.0; COST["calls"] += 1
        try: COST["tokens"] += completion_response.usage.total_tokens
        except Exception: pass


litellm.success_callback = [_track_cost]


def run_one(args, task, condition, seed):
    _ctx.cfg = dict(condition=condition, p=args.p, seed=seed, task_id=str(task.id), ledger=[], seen={})
    t0 = time.time()
    try:
        config = TextRunConfig(domain=args.domain, agent="llm_agent", user="user_simulator",
                               llm_agent=args.agent_model, llm_args_agent={"temperature": 0.0},
                               llm_user=args.user_model, llm_args_user={"temperature": 0.0},
                               max_steps=args.max_steps, max_errors=10, seed=seed)
        run = run_single_task(config, task, seed=seed, evaluation_type=EvaluationType.ENV)
        ri = run.reward_info
        msgs = []
        for m in run.messages:
            msgs.append(dict(role=m.role, content=(m.content if isinstance(m.content, str) else None),
                             tool_calls=[tc.name for tc in (getattr(m, "tool_calls", None) or [])]))
        return dict(ok=True, domain=args.domain, task_id=str(task.id), condition=condition, seed=seed, agent_model=args.agent_model,
                    reward=ri.reward if ri else None,
                    db_match=(ri.db_check.db_match if ri and ri.db_check else None),
                    termination=str(run.termination_reason), agent_cost=run.agent_cost, user_cost=run.user_cost,
                    n_faults=sum(e["faulted"] for e in _ctx.cfg["ledger"]), n_writes=len(_ctx.cfg["ledger"]),
                    ledger=_ctx.cfg["ledger"], messages=msgs, seconds=time.time() - t0)
    except Exception as e:
        return dict(ok=False, task_id=str(task.id), condition=condition, seed=seed, error=repr(e), trace=traceback.format_exc()[-1500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="airline")
    ap.add_argument("--n-tasks", type=int, default=10)
    ap.add_argument("--task-offset", type=int, default=0)
    ap.add_argument("--conditions", default="baseline,raw,typed")
    ap.add_argument("--p", type=float, default=0.3)
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--agent-model", default="openrouter/openai/gpt-4.1-mini")
    ap.add_argument("--user-model", default="openrouter/openai/gpt-4.1-mini")
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tasks = load_tasks(args.domain)
    tasks = tasks[args.task_offset: args.task_offset + args.n_tasks]
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            r = json.loads(l)
            if r.get("ok"): done.add((r["task_id"], r["condition"], r["seed"]))
    jobs = [(t, c, int(s)) for s in args.seeds.split(",") for c in args.conditions.split(",") for t in tasks if (str(t.id), c, int(s)) not in done]
    print(f"{len(tasks)} tasks, {len(jobs)} episodes to run", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    lock = threading.Lock()
    with ThreadPoolExecutor(args.workers) as ex, open(args.out, "a") as fh:
        futs = [ex.submit(run_one, args, t, c, s) for t, c, s in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            with lock:
                fh.write(json.dumps(r) + "\n"); fh.flush()
            print(i, len(jobs), r.get("task_id"), r.get("condition"), "ok" if r.get("ok") else r.get("error"), r.get("db_match"), f"cost_so_far=${COST['total']:.3f} calls={COST['calls']}", flush=True)
    print("TOTAL_COST_USD", round(COST["total"], 4), "CALLS", COST["calls"], "TOKENS", COST["tokens"], flush=True)


if __name__ == "__main__":
    main()
