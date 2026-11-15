"""Run HumanEval+ solutions against every test input and record failure signatures.

Specification (manuscript Section EC.4):
  * each solution runs in its own forked process (4 GB address space, 80 s CPU,
    120 s wall clock); stdin/stdout/stderr go to /dev/null;
  * the task stub (prompt) is executed first, then the candidate code;
  * inputs run one at a time on deep copies, each with a 1 s limit; after five
    timeouts the run stops and the remaining inputs count as TIMEOUT;
  * a result is correct if it equals the expected value after converting tuples to
    lists recursively; floats are compared as in EvalPlus (atol 1e-6 when the task
    gives none, rtol 1e-7);
  * a failing input gets a signature: EXC:<class>, TIMEOUT, LOAD:<class> (the code
    does not define the function; every input fails), or
    WA:<returned type>:<expected type>:<relation>.

usage: python3 -I harness.py TASKS_JSON OUT_JSONL.gz SAMPLES_JSONL [SAMPLES_JSONL ...]
       python3 -I harness.py TASKS_JSON OUT_JSONL.gz --reference
"""
import copy
import gzip
import json
import math
import os
import pickle
import resource
import signal
import sys
import time

import numpy as np

PER_INPUT_S, MAX_TIMEOUTS, CPU_S, WALL_S, MEM = 1.0, 5, 80, 120, 4 * 1024 ** 3
PARALLEL = int(os.environ.get("HARNESS_PROCS", os.cpu_count() or 4))


class _Timeout(BaseException):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def norm(x):
    if isinstance(x, tuple):
        x = list(x)
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    return x


def is_floats(x):
    if isinstance(x, float):
        return True
    if isinstance(x, (list, tuple)):
        return len(x) > 0 and all(isinstance(i, float) for i in x)
    return False


def equal(out, exp, atol):
    out, exp = norm(out), norm(exp)
    try:
        if out == exp:
            return True
    except Exception:
        pass
    if atol == 0 and is_floats(exp):
        atol = 1e-6
    if atol != 0:
        try:
            return bool(np.allclose(out, exp, rtol=1e-07, atol=atol))
        except Exception:
            return False
    return False


def wa_signature(out, exp):
    to, te = type(out).__name__, type(exp).__name__
    if isinstance(exp, bool):
        rel = "flip" if isinstance(out, bool) else "neq"
    elif isinstance(exp, (int, float)) and isinstance(out, (int, float)) and not isinstance(out, bool):
        try:
            rel = "lo" if out < exp else "hi"
        except Exception:
            rel = "neq"
    elif isinstance(exp, (list, tuple, str)) and isinstance(out, (list, tuple, str)):
        rel = "short" if len(out) < len(exp) else "long" if len(out) > len(exp) else "samelen"
    else:
        rel = "neq"
    return f"WA:{to}:{te}:{rel}"


def run_in_child(task, code):
    """Executed inside the forked child. Returns {signature: [failing input indices]}."""
    M = len(task["inputs"])
    fails = {}
    env = {"__name__": "__candidate__"}
    try:
        exec(compile(task["prompt"], "<stub>", "exec"), env)
    except BaseException:
        pass
    try:
        signal.setitimer(signal.ITIMER_REAL, 10.0)
        exec(compile(code, "<candidate>", "exec"), env)
        signal.setitimer(signal.ITIMER_REAL, 0)
        fn = env[task["entry_point"]]
        if not callable(fn):
            raise NameError("entry point not callable")
    except BaseException as e:
        signal.setitimer(signal.ITIMER_REAL, 0)
        return {f"LOAD:{type(e).__name__}": list(range(M))}, "load"
    n_to = 0
    for i, (inp, exp) in enumerate(zip(task["inputs"], task["results"])):
        if n_to >= MAX_TIMEOUTS:
            fails.setdefault("TIMEOUT", []).extend(range(i, M))
            return fails, "timeout_stop"
        args = copy.deepcopy(inp)
        try:
            signal.setitimer(signal.ITIMER_REAL, PER_INPUT_S)
            out = fn(*args)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except _Timeout:
            n_to += 1
            fails.setdefault("TIMEOUT", []).append(i)
            continue
        except BaseException as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            fails.setdefault(f"EXC:{type(e).__name__}", []).append(i)
            continue
        try:
            signal.setitimer(signal.ITIMER_REAL, PER_INPUT_S)
            ok = equal(out, exp, task["atol"])
            sig = None if ok else wa_signature(out, exp)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except BaseException:
            signal.setitimer(signal.ITIMER_REAL, 0)
            ok, sig = False, "WA:uncomparable"
        if not ok:
            fails.setdefault(sig, []).append(i)
    return fails, "ok"


def child(task, code, wfd):
    os.setsid()
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_S, CPU_S + 5))
    signal.signal(signal.SIGALRM, _alarm)
    sys.setrecursionlimit(10000)
    try:
        res = run_in_child(task, code)
    except BaseException as e:
        res = ({f"CRASH:{type(e).__name__}": list(range(len(task["inputs"])))}, "crash")
    data = pickle.dumps(res)
    with os.fdopen(wfd, "wb") as w:
        w.write(data)
    os._exit(0)


def main():
    tasks = {t["task_id"]: t for t in json.load(open(sys.argv[1]))}
    out_path = sys.argv[2]
    if sys.argv[3] == "--reference":
        jobs = [dict(model="reference", task_id=t, sample=0,
                     code=v["prompt"] + v["canonical_solution"]) for t, v in tasks.items()]
    else:
        jobs = []
        for p in sys.argv[3:]:
            for line in open(p):
                jobs.append(json.loads(line))
    done = set()
    if os.path.exists(out_path):
        with gzip.open(out_path, "rt") as f:
            for line in f:
                r = json.loads(line)
                done.add((r["model"], r["task_id"], r["sample"]))
    jobs = [j for j in jobs if (j["model"], j["task_id"], j["sample"]) not in done and j["task_id"] in tasks]
    print(f"{len(jobs)} solutions to run ({len(done)} already done)", flush=True)

    import select
    running = {}          # rfd -> [pid, job, start, bytearray]
    out = gzip.open(out_path, "at")
    t0, n = time.time(), 0

    def finish(rfd, killed=False):
        nonlocal n
        pid, job, start, buf = running.pop(rfd)
        os.close(rfd)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        task = tasks[job["task_id"]]
        M = len(task["inputs"])
        if buf and not killed:
            try:
                fails, status = pickle.loads(bytes(buf))
            except Exception:
                fails, status = {"KILLED": list(range(M))}, "killed"
        else:
            fails, status = {"KILLED": list(range(M))}, "killed"
        out.write(json.dumps(dict(model=job["model"], task_id=job["task_id"], sample=job["sample"],
                                  M=M, status=status, fails=fails)) + "\n")
        n += 1
        if n % 500 == 0:
            out.flush()
            print(f"{n}/{len(jobs)} done, {time.time() - t0:.0f}s", flush=True)

    it = iter(jobs)
    exhausted = False
    while running or not exhausted:
        while not exhausted and len(running) < PARALLEL:
            try:
                job = next(it)
            except StopIteration:
                exhausted = True
                break
            rfd, wfd = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(rfd)
                for other in list(running):
                    try:
                        os.close(other)
                    except OSError:
                        pass
                child(tasks[job["task_id"]], job["code"], wfd)
            os.close(wfd)
            running[rfd] = [pid, job, time.time(), bytearray()]
        if not running:
            break
        ready, _, _ = select.select(list(running), [], [], 0.05)
        for rfd in ready:
            chunk = os.read(rfd, 1 << 20)
            if chunk:
                running[rfd][3].extend(chunk)
            else:
                finish(rfd)
        now = time.time()
        for rfd, (pid, job, start, buf) in list(running.items()):
            if now - start > WALL_S:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except Exception:
                    pass
                finish(rfd, killed=True)
    out.close()
    print(f"finished {n} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
