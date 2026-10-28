"""Fault-injection experiment with a coding agent on real Python bugs (BugsInPy).

The agent gets a failing developer test and its output and must fix the source with tools
(list_dir, view_file, search, edit_file, run_tests, submit). An agent error is a tool call the environment rejects:
unknown tool or malformed arguments, missing path, edit text not found or ambiguous, an edit that breaks Python syntax,
an attempt to edit a test file, or a test run that times out. Arms as in the tau2-bench experiment:
  control - no injection (virtual injection index j recorded)
  single  - the j-th tool call (j in 1..3) is not executed and returns a transient 503 error
  blame   - as single, but the error reads like the agent's own mistake ("<argument> '<value>' not found")
  multi   - from the second call, each call is replaced by the 503 error with probability 0.25 (at most 3)
Success: every fail-to-pass developer test passes and every test that passed before still passes.
Each bug runs in its own worktree, one run at a time per bug, reverted afterwards.
Usage: python code_inject.py MODEL [--reps 2] [--bugs N] [--workers 16] [--cap USD]
"""
import argparse, ast, json, os, random, re, subprocess, sys, threading, time, traceback, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/fluffy-meme/reach_pilot/bugsinpy")
import bip_lib as B

MODELS = {"llama8b": "meta-llama/llama-3.1-8b-instruct", "llama70b": "meta-llama/llama-3.1-70b-instruct",
          "deepseek": "deepseek/deepseek-chat-v3.1"}
IGNORE = {"llama8b": ["Cerebras", "Groq"], "llama70b": ["Cerebras", "Groq"], "deepseek": ["CoreWeave", "SiliconFlow"]}
INJECT_MSG = "Error: service temporarily unavailable (503). The request was not processed."
P_MULTI, MAX_MULTI, MAX_TURNS, TEMP = 0.25, 3, 30, 0.5
META = json.load(open(HERE / "bug_meta.json"))
LOCKS = {k: threading.Lock() for k in META}

TOOLS = [
    {"name": "list_dir", "description": "List files and directories at a path relative to the repository root.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "view_file", "description": "Show lines of a file with line numbers (at most 150 lines per call).",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"},
                                                     "end_line": {"type": "integer"}}, "required": ["path"]}},
    {"name": "search", "description": "Search for a regular expression in files under a path; returns matching lines.",
     "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}},
    {"name": "edit_file", "description": "Replace exactly one occurrence of old_str with new_str in a source file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_str": {"type": "string"},
                                                     "new_str": {"type": "string"}}, "required": ["path", "old_str", "new_str"]}},
    {"name": "run_tests", "description": "Run the failing test(s) and show the output.", "parameters": {"type": "object", "properties": {}}},
    {"name": "submit", "description": "Finish when the bug is fixed.", "parameters": {"type": "object", "properties": {}}},
]
TOOLS = [{"type": "function", "function": t} for t in TOOLS]


class ToolError(Exception):
    pass


class Env:
    def __init__(self, key):
        self.key = key; proj, bug = key.split("/"); self.meta = META[key]
        self.wt = f"{B.W}/{proj}/wt{bug}"; self.py = f"{B.W}/{proj}/venv{bug}/bin/python"
        self.tests = set(self.meta["tests"])

    def reset(self):
        B.revert(self.wt)
        for f, txt in self.meta["tests"].items(): open(f"{self.wt}/{f}", "w").write(txt)

    def _path(self, p, must_exist=True):
        if not isinstance(p, str) or not p: raise ToolError("Error: path is required")
        full = os.path.normpath(os.path.join(self.wt, p.lstrip("/") if not p.startswith(self.wt) else os.path.relpath(p, self.wt)))
        if not full.startswith(self.wt): raise ToolError(f"Error: path '{p}' is outside the repository")
        if must_exist and not os.path.exists(full): raise ToolError(f"Error: path '{p}' does not exist")
        return full

    def call(self, name, a):
        if name == "list_dir":
            full = self._path(a.get("path", "."))
            if not os.path.isdir(full): raise ToolError(f"Error: '{a.get('path')}' is not a directory")
            items = sorted(x + ("/" if os.path.isdir(os.path.join(full, x)) else "") for x in os.listdir(full) if not x.startswith("."))
            return "\n".join(items[:200])
        if name == "view_file":
            full = self._path(a.get("path"))
            if os.path.isdir(full): raise ToolError(f"Error: '{a.get('path')}' is a directory")
            lines = open(full, errors="replace").read().splitlines()
            try: s = int(a.get("start_line") or 1); e = int(a.get("end_line") or s + 149)
            except (TypeError, ValueError): raise ToolError("Error: start_line and end_line must be integers")
            if s < 1 or s > max(len(lines), 1) or e < s: raise ToolError(f"Error: invalid line range {s}-{e} (file has {len(lines)} lines)")
            e = min(e, s + 149, len(lines))
            return "\n".join(f"{i}: {lines[i-1]}" for i in range(s, e + 1))
        if name == "search":
            pat = a.get("pattern")
            if not isinstance(pat, str) or not pat: raise ToolError("Error: pattern is required")
            try: re.compile(pat)
            except re.error as ex: raise ToolError(f"Error: invalid regular expression: {ex}")
            full = self._path(a.get("path") or ".")
            r = subprocess.run(["grep", "-rnE", "--include=*.py", pat, full], capture_output=True, text=True, timeout=60)
            out = r.stdout.replace(self.wt + "/", "").splitlines()
            return "\n".join(out[:60]) + (f"\n... {len(out) - 60} more" if len(out) > 60 else "") if out else "No matches."
        if name == "edit_file":
            p = a.get("path"); full = self._path(p)
            rel = os.path.relpath(full, self.wt)
            if rel in self.tests or "/test" in "/" + rel and os.path.basename(rel).startswith("test"):
                raise ToolError("Error: test files cannot be modified")
            old, new = a.get("old_str"), a.get("new_str")
            if not isinstance(old, str) or not isinstance(new, str) or not old: raise ToolError("Error: old_str and new_str are required strings")
            txt = open(full, errors="replace").read(); n = txt.count(old)
            if n == 0: raise ToolError(f"Error: old_str not found in {p}")
            if n > 1: raise ToolError(f"Error: old_str occurs {n} times in {p}; make it unique")
            new_txt = txt.replace(old, new, 1)
            if full.endswith(".py"):
                try: ast.parse(new_txt)
                except SyntaxError as ex: raise ToolError(f"Error: edit rejected, it would cause a syntax error: {ex.msg} (line {ex.lineno})")
            open(full, "w").write(new_txt); return f"Edited {p}."
        if name == "run_tests":
            try:
                r = subprocess.run(f"{self.py} -m pytest -x -q -p no:cacheprovider {self.meta['target']} 2>&1 | tail -40", shell=True,
                                   cwd=self.wt, capture_output=True, text=True, timeout=300, env=dict(os.environ, PYTHONPATH=self.wt))
            except subprocess.TimeoutExpired: raise ToolError("Error: test run timed out")
            return r.stdout[-3000:]
        if name == "submit": return "Submitted."
        raise ToolError(f"Error: unknown tool '{name}'")

    def evaluate(self):
        res, _ = B.run_pytest_xml(self.wt, self.py, self.meta["target"])
        ok = lambda t: res.get(t, ("", ""))[0] == "passed"
        f2p = all(ok(t) for t in self.meta["f2p"]); p2p = all(ok(t) for t in self.meta["p2p"])
        return dict(f2p_pass=f2p, p2p_pass=p2p, reward=float(f2p and p2p))


def chat(model, messages, ignore):
    body = dict(model=model, messages=messages, tools=TOOLS, temperature=TEMP, max_tokens=2000,
                provider={"ignore": ignore}, usage={"include": True})
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=180) as r: j = json.load(r)
            if "choices" in j: return j
            last = str(j)[:300]
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: " + e.read().decode(errors="replace")[:400]
            if e.code == 400 and "rate" not in last.lower(): break
        except Exception as e:
            last = str(e)[:300]
        time.sleep(2 * 2 ** attempt)
    raise RuntimeError("API failure: " + (last or ""))


def inject_msg(arm, args):
    if arm != "blame": return INJECT_MSG
    for k, v in (args or {}).items():
        if isinstance(v, (str, int)) and str(v): return f"Error: {k.replace('_', ' ')} '{str(v)[:80]}' not found"
    return "Error: invalid request arguments"


def run_one(job):
    key, arm, model = job["bug"], job["arm"], job["model"]; rng = random.Random(job["seed"]); j = rng.choice([1, 2, 3])
    env = Env(key); calls, cost, n_inj, n, malformed = [], 0.0, 0, 0, 0
    meta = env.meta
    prompt = (f"You are fixing a bug in a Python repository (the repository root is the working directory). The following "
              f"test currently fails:\n{chr(10).join(meta['f2p'][:5])}\n\nTest output:\n{meta['fail_output'][-2500:]}\n\n"
              f"Find and fix the bug in the source code so that this test passes without breaking other tests. Do not modify "
              f"test files. Use the tools; call submit when you are done.")
    msgs = [{"role": "system", "content": "You are a careful software engineer. Work only through the provided tools."},
            {"role": "user", "content": prompt}]
    t0 = time.time(); end = "max_turns"; idle = 0
    with LOCKS[key]:
        env.reset()
        try:
            for turn in range(MAX_TURNS):
                r = chat(MODELS[model], msgs, IGNORE[model]); cost += float((r.get("usage") or {}).get("cost") or 0)
                m = r["choices"][0]["message"]; tcs = m.get("tool_calls") or []
                parsed = []
                for tc in tcs:  # keep the history valid for the provider: malformed arguments are stored as {}
                    raw = (tc.get("function") or {}).get("arguments") or "{}"
                    try:
                        args = json.loads(raw) if isinstance(raw, str) else raw
                        if not isinstance(args, dict): raise ValueError
                        parsed.append((args, False))
                    except Exception:  # as in the tau2-bench experiment: keep the first JSON object and record the event
                        try: args = json.JSONDecoder().raw_decode(raw.strip())[0]
                        except Exception: args = None
                        malformed += 1
                        parsed.append((args, False) if isinstance(args, dict) else ({}, True))
                    tc.setdefault("function", {})["arguments"] = json.dumps(parsed[-1][0]); tc.setdefault("type", "function")
                msgs.append({"role": "assistant", "content": m.get("content") or "", **({"tool_calls": tcs} if tcs else {})})
                if not tcs:
                    idle += 1
                    if idle >= 2: end = "no_tool_calls"; break
                    msgs.append({"role": "user", "content": "Please continue using the tools, or call submit when the bug is fixed."}); continue
                idle = 0; done = False
                for tc, (args, bad_json) in zip(tcs, parsed):
                    n += 1; name = tc.get("function", {}).get("name")
                    inj = (arm in ("single", "blame") and n == j) or (arm == "multi" and n >= 2 and n_inj < MAX_MULTI and rng.random() < P_MULTI)
                    if inj and name != "submit":
                        n_inj += 1; out = inject_msg(arm, args); calls.append(dict(i=n, name=name, injected=1, error=1))
                    else:
                        try:
                            if bad_json: raise ToolError("Error: tool arguments are not valid JSON")
                            out = env.call(name, args); err = 0
                        except ToolError as ex: out, err = str(ex), 1
                        except Exception as ex: out, err = f"Error: {type(ex).__name__}: {ex}"[:300], 1
                        calls.append(dict(i=n, name=name, injected=0, error=err, msg=out[:120] if err else ""))
                        if name == "submit" and not err: done = True
                    msgs.append({"role": "tool", "tool_call_id": tc.get("id") or f"call_{n}", "content": out[:4000]})
                if done: end = "submit"; break
            ev = env.evaluate(); ok = 1; e = ""
        except Exception as ex:
            ev, ok, e = {}, 0 if "API failure" in str(ex) else 1, f"{type(ex).__name__}: {ex}"[:300]
            if ok: ev = dict(reward=0.0, f2p_pass=False, p2p_pass=False)
        finally:
            B.revert(env.wt)
    return dict(key=job["key"], ok=ok, err=e, model=model, bug=key, arm=arm, rep=job["rep"], seed=job["seed"], j=j, n_inj=n_inj, malformed=malformed,
                calls=calls, end=end, cost=round(cost, 5), secs=round(time.time() - t0, 1), **ev)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--bugs", type=int, default=0); ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--arms", default="control,single,blame,multi"); ap.add_argument("--cap", type=float, default=100.0)
    a = ap.parse_args()
    bugs = sorted(META)[: a.bugs] if a.bugs else sorted(META)
    jobs = [dict(model=a.model, bug=b, arm=arm, rep=r, seed=(1000003 * r + sum(map(ord, b))) % 2 ** 31, key=f"{a.model}|{b}|{arm}|{r}")
            for r in range(a.reps) for arm in a.arms.split(",") for b in bugs]
    random.Random(7).shuffle(jobs)
    out = HERE / "results" / f"{a.model}.jsonl"; out.parent.mkdir(exist_ok=True)
    done = {json.loads(l)["key"] for l in open(out) if json.loads(l).get("ok")} if out.exists() else set()
    todo = [x for x in jobs if x["key"] not in done]; spent = 0.0
    if out.exists(): spent = sum(json.loads(l).get("cost", 0) for l in open(out))
    print(f"{len(jobs)} jobs, {len(done)} done, {len(todo)} to run; spent so far ${spent:.2f}", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        futs = {}; it = iter(todo); stop = False
        def submit():
            x = next(it, None)
            if x is not None: futs[ex.submit(run_one, x)] = x
        for _ in range(a.workers * 2): submit()
        k = 0
        while futs:
            for fu in as_completed(list(futs)):
                futs.pop(fu)
                try: r = fu.result()
                except Exception as e: r = dict(ok=0, key=None, err=traceback.format_exc()[-300:], cost=0)
                f.write(json.dumps(r) + "\n"); f.flush(); spent += r.get("cost", 0) or 0; k += 1
                if k % 20 == 0: print(f"{k} finished; spent ${spent:.2f}", flush=True)
                if spent > a.cap and not stop: stop = True; print("spend cap reached", flush=True)
                if not stop: submit()
                break
    print(f"done; spent ${spent:.2f}", flush=True)


if __name__ == "__main__":
    main()
