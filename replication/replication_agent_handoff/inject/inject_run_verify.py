"""Verification-arm extension of inject_run.py (pilot version; V3 not implemented yet).

Reuses the injection machinery of inject_run.py unchanged (same arms, same seeds, hence the same injection
indices j as the original runs) and adds a verification LEVEL, applied as a change of the agent's system prompt:
  V0 - no change (re-run of the original design; used as a drift check)
  V1 - generic self-check: doubt tool results that say something does not exist
  V2 - cross-check rule: before concluding that something does not exist, check a different read-only tool
Extra logging: tool arguments per call, and whether the agent's messages to the user claim that something
does not exist / cannot be found.

Usage (one process per level, so the prompt patch is process-wide):
  python inject_run_verify.py MODEL --verif V2 [--arms control,blame] [--reps 2] [--sample-air 8 --sample-ret 12]
                              [--workers 8] [--cap USD] [--tag pilot]
Results: results/verif_<tag>_<model>_<verif>.jsonl (append-only, reruns skip finished keys).
"""
import argparse, json, os, random, re, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import inject_run as base

V_TEXT = {
    "V0": "",
    "V1": ("\n\nBefore you rely on a tool result that says something does not exist or cannot be found, "
           "pause and consider whether that result could be wrong."),
    "V2": ("\n\nVerification rule: if a lookup fails with a 'not found' style error, or a tool says that something "
           "does not exist, do not tell the user that and do not act on it yet. First cross-check with a different "
           "read-only tool (for example get_user_details to list the user's reservations or orders, or a search tool). "
           "Conclude that something does not exist only if the cross-check agrees. If the cross-check contradicts "
           "the error, use the cross-check result."),
}
CLAIM_RE = re.compile(r"(not found|does not exist|doesn't exist|do not see|don't see|couldn't find|could not find|"
                      r"cannot find|can't find|unable to (?:find|locate)|no (?:such )?(?:reservation|order|user|record))", re.I)
READ_PREFIX = ("get_", "find_", "search_", "list_")
_SC = threading.local()  # side channel: per-thread extra fields for the current run


def ensure_patched(verif):
    import tau2.agent.llm_agent as la
    from tau2.environment.environment import Environment
    import tau2.runner.simulation as rs
    with base._PATCH_LOCK:
        if getattr(base.run_one, "patched", False):
            return
        base._patch(); base.run_one.patched = True
        la.AGENT_INSTRUCTION = la.AGENT_INSTRUCTION + V_TEXT[verif]
        prev = Environment.get_response

        def get_response(self, message):
            r = prev(self, message)
            s = base.STATE
            if s and message.requestor == "assistant" and s.get("phase") == "run" and s["calls"]:
                s["calls"][-1]["args"] = json.dumps(message.arguments, sort_keys=True, default=str)[:160]
            return r
        Environment.get_response = get_response
        prev_eval = rs.evaluate_simulation

        def evaluate_simulation(*a, **kw):
            sim = a[0] if a else kw.get("simulation")
            try:
                claims = n_msgs = 0
                for m in (sim.messages or []):
                    if m.__class__.__name__ == "AssistantMessage" and (m.content or "") and not getattr(m, "tool_calls", None):
                        n_msgs += 1; claims += bool(CLAIM_RE.search(m.content))
                _SC.claims, _SC.n_msgs = claims, n_msgs
            except Exception:
                _SC.claims = _SC.n_msgs = None
            return prev_eval(*a, **kw)
        rs.evaluate_simulation = evaluate_simulation


def run_one(job):
    _SC.claims = _SC.n_msgs = None
    out = base.run_one(job)
    out.update(verif=job["verif"], claims=getattr(_SC, "claims", None), n_agent_msgs=getattr(_SC, "n_msgs", None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model"); ap.add_argument("--verif", required=True, choices=sorted(V_TEXT))
    ap.add_argument("--arms", default="control,blame"); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--cap", type=float, default=8.0)
    ap.add_argument("--sample-air", type=int, default=0); ap.add_argument("--sample-ret", type=int, default=0)
    ap.add_argument("--sample-seed", type=int, default=7); ap.add_argument("--tag", default="pilot")
    a = ap.parse_args()
    import logging
    from loguru import logger
    logger.remove(); logger.add(sys.stderr, level="ERROR", filter=lambda r: "isn't mapped" not in r["message"])
    logging.getLogger("LiteLLM").setLevel(logging.ERROR)
    from tau2.runner.helpers import get_tasks
    ensure_patched(a.verif)
    rng = random.Random(a.sample_seed)
    jobs = []
    for dom, k in (("airline", a.sample_air), ("retail", a.sample_ret)):
        if not k: continue
        ids = [t.id for t in get_tasks(dom)]
        ids = sorted(rng.sample(ids, k), key=lambda x: int(x) if str(x).isdigit() else str(x))
        for tid in ids:
            for rep in range(a.reps):
                for arm in a.arms.split(","):
                    seed = (1000003 * rep + sum(map(ord, dom + tid))) % (2 ** 31)  # same formula as inject_run.py
                    jobs.append(dict(model=a.model, domain=dom, task=tid, arm=arm, rep=rep, seed=seed, verif=a.verif,
                                     key=f"{a.model}|{dom}|{tid}|{arm}|{rep}|{a.verif}"))
    out = HERE / "results" / f"verif_{a.tag}_{a.model}_{a.verif}.jsonl"; out.parent.mkdir(exist_ok=True)
    done = set()
    if out.exists():
        for l in out.open():
            try:
                r = json.loads(l)
                if r.get("ok"): done.add(r["key"])
            except Exception: pass
    todo = [j for j in jobs if j["key"] not in done]
    u0, tot = base.credits_used()
    if u0 is not None and tot is not None and tot - u0 < a.cap:
        print(f"refusing to start: remaining credits {tot-u0:.2f} < cap {a.cap}", flush=True); return
    print(f"{a.verif}: {len(jobs)} jobs, {len(done)} done, {len(todo)} to run; credits used {u0} of {tot}", flush=True)
    stop = False; n = 0
    with ThreadPoolExecutor(a.workers) as ex, out.open("a") as f:
        futs = {}; it = iter(todo)

        def submit():
            j = next(it, None)
            if j is not None: futs[ex.submit(run_one, j)] = j
        for _ in range(a.workers): submit()
        while futs:
            for fu in as_completed(list(futs)):
                futs.pop(fu)
                try: r = fu.result()
                except Exception as e: r = dict(ok=0, key=None, err=str(e)[:300])
                f.write(json.dumps(r) + "\n"); f.flush(); n += 1
                if n % 10 == 0:
                    u, _ = base.credits_used()
                    spent = (u - u0) if (u is not None and u0 is not None) else None
                    print(f"{n} finished; spent ${spent if spent is None else round(spent, 2)}", flush=True)
                    if spent is not None and spent > a.cap: stop = True; print("spend cap reached; stopping", flush=True)
                if not stop: submit()
                break
    u, _ = base.credits_used()
    print(f"done; spent ${None if u is None or u0 is None else round(u - u0, 2)}", flush=True)


if __name__ == "__main__":
    main()
