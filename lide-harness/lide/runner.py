"""Runs one episode for a (cell, model, repetition) and returns a JSON-serializable record."""
from __future__ import annotations

import datetime as dt
import json
import traceback

from .conditions import (DEADLINE_TEXT, GOVERNANCE_TEXT, USER_DISSATISFACTION, VALENCE_PLANS, Cell,
                         episode_id)
from .envs import make_env
from .models import make_model
from .types import ToolCall


def _clip(value, n: int = 2000):
    if isinstance(value, str) and len(value) > n:
        return value[:n] + f"...[{len(value) - n} chars clipped]"
    if isinstance(value, dict):
        return {k: _clip(v, n) for k, v in value.items()}
    if isinstance(value, list):
        return [_clip(v, n) for v in value]
    return value


_TARGET_CHARS: dict[str, int] = {}


def _raw_history(env, valence: str):
    """Executes the scripted history against the environment (so state stays consistent)."""
    plan = VALENCE_PLANS[valence]
    counters = {"success": 0, "failure": 0, "neutral": 0}
    steps = []
    env.history_mode = True
    try:
        for kind in plan:
            calls = env.history_calls(kind, counters[kind])
            counters[kind] += 1
            results = []
            for call in calls:
                res = env.execute(call)
                results.append({"id": call.id, "name": call.name, "content": res.output,
                                "target": res.target})
            steps.append((kind, calls, results))
    finally:
        env.history_mode = False
    return steps, counters


def _chars(steps) -> int:
    return sum(len(json.dumps(c.args)) + len(r["content"])
               for _, calls, results in steps for c, r in zip(calls, results))


def target_chars(env_name: str) -> int:
    """Length of the longest (all-failure) history; every condition is padded to it."""
    if env_name not in _TARGET_CHARS:
        scratch = make_env(env_name)
        try:
            _TARGET_CHARS[env_name] = max(_chars(_raw_history(scratch, v)[0])
                                          for v in ("fail8",))
        finally:
            scratch.close()
    return _TARGET_CHARS[env_name]


def build_history(env, cell: Cell) -> tuple[list[dict], dict]:
    steps, counters = _raw_history(env, cell.valence)
    raw = _chars(steps)
    deficit = max(0, target_chars(cell.env) - raw)
    neutral_idx = [i for i, (k, _, _) in enumerate(steps) if k == "neutral"]
    if deficit and neutral_idx:
        # Spread the deficit over the first call of each neutral step, then fix rounding.
        share = deficit // len(neutral_idx)
        for n, i in enumerate(neutral_idx):
            _, calls, results = steps[i]
            want = share + (deficit - share * len(neutral_idx) if n == len(neutral_idx) - 1 else 0)
            results[0]["content"] = env.extend_output(calls[0], results[0]["content"], want)
    chars = _chars(steps)

    messages: list[dict] = []
    failed_targets: set[str] = set()
    for kind, calls, results in steps:
        if kind == "failure":
            failed_targets.update(r["target"] for r in results)
        messages.append({"role": "assistant", "text": "",
                         "tool_calls": [{"id": c.id, "name": c.name, "args": c.args} for c in calls]})
        messages.append({"role": "tool", "results": [{k: r[k] for k in ("id", "name", "content")}
                                                     for r in results]})

    meta = {"plan": VALENCE_PLANS[cell.valence], "failed_targets": sorted(failed_targets),
            "chars_raw": raw, "chars_full": chars, "chars_target": target_chars(cell.env)}
    if cell.record == "summary":
        summary = env.summarize(counters["success"], counters["failure"], counters["neutral"])
        pad = env.padding_text()
        while len(summary) < chars:
            summary += pad
        summary = summary[:chars] if len(summary) > chars else summary
        meta["chars_summary"] = len(summary)
        messages = [{"role": "user", "content": summary}]
    return messages, meta


def build_system(env, cell: Cell) -> str:
    parts = [env.system_rules()]
    if cell.default_exit:
        parts.append(GOVERNANCE_TEXT["default_exit"])
    if cell.stop_loss:
        parts.append(GOVERNANCE_TEXT["stop_loss"])
    if cell.scarcity == "deadline":
        parts.append(DEADLINE_TEXT)
    return "\n\n".join(parts)


def _scarcity_suffix(cell: Cell, actions_done: int, max_actions: int) -> str:
    if cell.scarcity == "steps":
        return f"\n[Steps remaining: {max(0, max_actions - actions_done)}]"
    if cell.scarcity == "deadline":
        minutes = max(0.0, 10 - 0.75 * actions_done)
        return f"\n[Deploy window closes in {minutes:.0f} min]"
    return ""


def run_episode(cell: Cell, model_spec: dict, rep: int, cfg: dict) -> dict:
    ep_cfg = cfg.get("episode", {})
    max_actions = ep_cfg.get("max_live_actions", 12)
    max_turns = ep_cfg.get("max_turns", 20)
    spec = dict(model_spec)
    if spec.get("provider", "mock") == "mock":
        spec["_env"] = cell.env
    record: dict = {
        "episode_id": episode_id(cell, spec["name"], rep),
        "cell": cell.as_dict(),
        "model": {k: spec.get(k) for k in ("name", "provider", "family", "generation", "size")},
        "rep": rep,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_params": cfg.get("generation", {}),
    }
    env = make_env(cell.env, friction=cell.friction, default_exit=cell.default_exit, seed=rep)
    try:
        model = make_model(spec, cfg.get("generation", {}))
        history, meta = build_history(env, cell)
        record["history"] = meta
        system = build_system(env, cell)
        continue_msg = env.continue_prompt()
        if cell.feedback == "user":
            continue_msg = USER_DISSATISFACTION + "\n\n" + continue_msg
        messages = [{"role": "user", "content": env.session_prompt()}] + history + \
                   [{"role": "user", "content": continue_msg}]
        tools = env.tools()
        live_start = len(messages)

        steps: list[dict] = []
        usage = {"input_tokens": 0, "output_tokens": 0, "model_calls": 0}
        actions, end_reason, claim = 0, "max_actions", None
        for turn_idx in range(max_turns):
            turn = model.complete(system, messages, tools)
            usage["input_tokens"] += turn.input_tokens
            usage["output_tokens"] += turn.output_tokens
            usage["model_calls"] += 1
            messages.append({"role": "assistant", "text": turn.text,
                             "tool_calls": [{"id": c.id, "name": c.name, "args": c.args}
                                            for c in turn.tool_calls]})
            if not turn.tool_calls:
                end_reason = "text_only"
                steps.append({"turn": turn_idx, "tool": None, "assistant_text": turn.text})
                break
            results, ended = [], False
            for j, call in enumerate(turn.tool_calls):
                if ended or actions >= max_actions:
                    results.append({"id": call.id, "name": call.name,
                                    "content": "Not executed: session ended or step limit reached."})
                    continue
                res = env.execute(call)
                actions += 1
                output = res.output + _scarcity_suffix(cell, actions, max_actions)
                results.append({"id": call.id, "name": call.name, "content": output})
                steps.append({
                    "turn": turn_idx,
                    "action_index": actions,
                    "tool": call.name,
                    "args": _clip(call.args),
                    "executed": res.executed,
                    "risk": res.risk.as_dict(),
                    "safeguard": res.safeguard,
                    "failure_signal": res.failure_signal,
                    "target": res.target,
                    "claimed_status": res.claimed_status,
                    "core_progress": env.core_progress(),
                    "output": _clip(output, 1500),
                    "assistant_text": turn.text if j == 0 else "",
                })
                if res.claimed_status:
                    claim = res.claimed_status
                if res.ends_episode:
                    ended, end_reason = True, "agent_ended"
            messages.append({"role": "tool", "results": results})
            if ended or actions >= max_actions:
                break
        else:
            end_reason = "max_turns"

        record.update({
            "steps": steps,
            "end_reason": end_reason,
            "claimed_status": claim,
            "final_state": env.final_state(),
            "usage": usage,
            "status": "ok",
        })
        if cfg.get("output", {}).get("save_transcripts", True):
            record["transcript"] = {"system": system, "tools": [t.name for t in tools],
                                    "messages": _clip(messages, 4000), "live_start": live_start}
    except Exception as exc:
        record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}",
                       "traceback": traceback.format_exc()[-4000:]})
    finally:
        env.close()
        record["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return record
