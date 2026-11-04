"""Run a study and log one row per turn to JSONL.

    python run.py study4 --dry-run          # count calls, estimate cost
    python run.py study4 --limit 50         # small pilot
    python run.py study4                    # full run (resumes if interrupted)
    python run.py study7_screen --only L1_min_reasoning
    python run.py study7_followup:L1_min_reasoning

The runner stops on a client error or after five consecutive failed calls,
and resumes an interrupted run without duplicating episodes (Appendix C).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from backends import ClientError, make_backend, parse_action
from env import (ACTIONS, SKIP_ACTIONS, Condition, draws, ev_max_action, expected_value,
                 initial_state, step, system_prompt, user_prompt)
from studies import M, STUDIES, Run, study7_followup
from wordings import wordings_sha

HERE = Path(__file__).parent
RESULTS = HERE / "results"


def resolve(study: str) -> list[Run]:
    if study.startswith("study7_followup:"):
        return study7_followup(study.split(":", 1)[1])
    return STUDIES[study]


def run_id(study: str, r: Run) -> str:
    return f"{study.replace(':', '-')}__{r.model}" + (f"__{r.tag}" if r.tag else "")


def episode_key(cell: dict, ep: int) -> str:
    return f"{cell['frame']}|{cell['wording']}|{cell['turns_left']}|{cell['n_fails']}|{int(cell['hide_target'])}|{ep}"


def play_episode(backend, r: Run, cell: dict, ep: int, full: bool) -> list[dict]:
    spec = M[r.model]
    cond = Condition(frame=cell["frame"], wording=cell["wording"], hide_target=cell["hide_target"],
                     show_ev=r.show_ev, system_extra=r.system_extra, rotate=r.rotate,
                     episode=ep)
    seed = ep  # same world for every model and frame
    u = draws(seed)
    s = initial_state(cell["n_fails"], cell["turns_left"])
    sys_p = system_prompt(cond)
    rows, t = [], 0
    while s.remaining > 0:
        user, order = user_prompt(cond, s, t)
        reply = backend(sys_p, user)
        action, reason, pfail = parse_action(reply.text)
        best = ev_max_action(s.quality)
        s2, outcome = step(s, action, u[t], overrun=r.overrun)
        usage = reply.usage or {}
        rows.append({
            "seed": seed, "episode": ep, "model": spec.name, "model_id": spec.model_id,
            "model_version": reply.model_version, "provider": reply.provider,
            "frame": cell["frame"], "headline_id": cell["wording"], "n_fails": cell["n_fails"],
            "turns_left": cell["turns_left"], "hide_target": cell["hide_target"],
            "show_ev": r.show_ev, "system_extra": bool(r.system_extra), "overrun": r.overrun,
            "temperature": spec.temperature, "temperature_applied": reply.temperature_applied,
            "reasoning_cfg": spec.reasoning, "t": t, "turn": s.spent,
            "quality_before": s.quality, "fail_streak_before": s.fail_streak,
            "cum_loss_before": s.unrealized_loss, "action": action, "skip": action in SKIP_ACTIONS,
            "parse_fail": pfail, "risk": ACTIONS[action][4],
            "excess_risk": ACTIONS[action][4] - ACTIONS[best][4],
            "ev_gap": expected_value(action, s.quality) - expected_value(best, s.quality),
            "reason": reason, "raw": None if not pfail else reply.text[:300],
            "rotate": r.rotate, "action_order": ",".join(order), "first_listed": order[0], "outcome": outcome, "quality_after": s2.quality,
            "first_choice": t == 0, "wordings_sha": wordings_sha(),
            "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "reasoning_chars": len(reply.reasoning_text or ""),
            "cost": usage.get("cost"),
        })
        s, t = s2, t + 1
        if not full:
            break
    for row in rows:
        row["terminal_quality"] = s.quality if full else None
    return rows


def done_keys(path: Path) -> set[str]:
    keys = set()
    if path.exists():
        for line in path.open():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue  # partial last line from an interrupted run
            if d.get("t") == 0:
                keys.add(episode_key({"frame": d["frame"], "wording": d["headline_id"],
                                      "turns_left": d["turns_left"], "n_fails": d["n_fails"],
                                      "hide_target": d["hide_target"]}, d["episode"]))
    return keys


def execute(study: str, r: Run, args) -> bool:
    out = RESULTS / f"{run_id(study, r)}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = done_keys(out)
    jobs = [(c, ep) for c in r.cells() for ep in range(r.episodes) if episode_key(c, ep) not in done]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"[{run_id(study, r)}] {len(done)} episodes done, {len(jobs)} to run -> {out}", flush=True)
    if not jobs:
        return True
    backend = make_backend(M[r.model])
    lock, stop = threading.Lock(), threading.Event()
    consecutive_fail = [0]
    n_ok = [0]

    def work(job):
        if stop.is_set():
            return None
        cell, ep = job
        return play_episode(backend, r, cell, ep, args.full_episodes)

    t0 = time.time()
    with out.open("a") as f, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(work, j) for j in jobs]
        for fut in as_completed(futs):
            try:
                rows = fut.result()
            except ClientError as e:
                print(f"  client error, stopping: {e}", file=sys.stderr)
                stop.set()
                continue
            except (RuntimeError, requests.RequestException) as e:
                with lock:
                    consecutive_fail[0] += 1
                    if consecutive_fail[0] >= 5:
                        print(f"  five failed calls in a row, stopping: {e}", file=sys.stderr)
                        stop.set()
                continue
            if rows is None:
                continue
            with lock:
                consecutive_fail[0] = 0
                for row in rows:
                    f.write(json.dumps(row) + "\n")
                f.flush()
                n_ok[0] += 1
                if n_ok[0] % 100 == 0:
                    print(f"  {n_ok[0]}/{len(jobs)} ({time.time() - t0:.0f}s)", flush=True)
        if stop.is_set():
            for fu in futs:
                fu.cancel()
    print(f"  finished {n_ok[0]}/{len(jobs)} in {time.time() - t0:.0f}s", flush=True)
    return not stop.is_set()


# ---------------------------------------------------------------- cost estimate
def prices() -> dict:
    try:
        d = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
        return {m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])) for m in d}
    except Exception:
        return {}


def dry_run(study: str, runs: list[Run], args):
    p = prices()
    total = 0.0
    for r in runs:
        spec = M[r.model]
        n = r.n_calls() * (6 if args.full_episodes else 1)
        # Rough per-call tokens: ~420 prompt; ~40 answer, more when the model reasons.
        out_tok = 40 if spec.reasoning is None and spec.temperature is not None else 400
        pin, pout = p.get(spec.model_id, (0.0, 0.0))
        cost = n * (420 * pin + out_tok * pout)
        total += cost
        print(f"{run_id(study, r):55s} calls={n:6d}  ~${cost:8.2f}" + ("" if spec.model_id in p else "  (price unknown)"))
    print(f"{'TOTAL':55s} ~${total:.2f}  (rough; reasoning models can cost several times more)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study", help="name in studies.STUDIES, or study7_followup:<step tag>")
    ap.add_argument("--only", nargs="*", help="run only these models or tags")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="cap episodes per run (pilot)")
    ap.add_argument("--full-episodes", action="store_true",
                    help="play to the end of the budget (default: first free choice only)")
    ap.add_argument("--episodes", type=int, help="override episodes per cell (pilot)")
    ap.add_argument("--turns", type=int, nargs="*", help="override turns_left levels (pilot)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    runs = resolve(args.study)
    if args.only:
        runs = [r for r in runs if r.model in args.only or r.tag in args.only]
    from dataclasses import replace as _replace
    if args.episodes or args.turns:
        runs = [_replace(r, episodes=args.episodes or r.episodes, turns_left=args.turns or r.turns_left)
                for r in runs]
    if args.dry_run:
        return dry_run(args.study, runs, args)
    for r in runs:
        if not execute(args.study, r, args):
            sys.exit(1)


if __name__ == "__main__":
    main()
