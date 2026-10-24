"""Child process: run one candidate on one task's test inputs, report failing indices per failure signature.

stdin: JSON {prompt, code, entry_point, test_src, inputs, results, atol}
stdout: JSON {"n": total tests, "fails": {signature: [indices]}}
"""
import copy
import io
import json
import resource
import signal
import sys

payload = json.loads(sys.stdin.read())
resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
resource.setrlimit(resource.RLIMIT_CPU, (80, 80))
real_stdout = sys.stdout
sys.stdout = io.StringIO()
sys.stdin = io.StringIO()


class Timeout(Exception):
    pass


def _alarm(*_):
    raise Timeout()


signal.signal(signal.SIGALRM, _alarm)


def relation(out, exp):
    try:
        if isinstance(exp, bool) or isinstance(out, bool):
            return "flip"
        if isinstance(exp, (int, float)) and isinstance(out, (int, float)):
            return "lo" if out < exp else "hi"
        if hasattr(exp, "__len__") and hasattr(out, "__len__"):
            return "short" if len(out) < len(exp) else ("long" if len(out) > len(exp) else "samelen")
    except Exception:
        pass
    return "neq"


def norm(x):
    """tuple -> list recursively: expected values are stored as lists, solutions may return tuples."""
    if isinstance(x, (tuple, list)):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    return x


def finish(fails, n):
    real_stdout.write(json.dumps({"n": n, "fails": fails}))
    sys.exit(0)


inputs, results, atol = payload["inputs"], payload["results"], payload["atol"]
n = len(inputs)
ns = {}
try:
    exec(payload["test_src"], ns)
    assertion = ns["assertion"]
    g = {"__name__": "candidate"}
    exec(payload["prompt"], g)
    exec(payload["code"], g)
    fn = g[payload["entry_point"]]
except BaseException as e:  # candidate does not load: one defect, every test fails
    finish({"LOAD:" + type(e).__name__: list(range(n))}, n)

fails, n_timeouts = {}, 0
for i in range(n):
    sig = None
    try:
        signal.alarm(2)
        out = fn(*copy.deepcopy(inputs[i]))
        signal.alarm(0)
        try:
            assertion(norm(out), norm(results[i]), atol)
        except BaseException:
            sig = "WA:%s>%s:%s" % (type(out).__name__, type(results[i]).__name__, relation(out, results[i]))
    except Timeout:
        sig = "TIMEOUT"
        n_timeouts += 1
    except BaseException as e:
        signal.alarm(0)
        sig = "EXC:" + type(e).__name__
    finally:
        signal.alarm(0)
    if sig:
        fails.setdefault(sig, []).append(i)
    if n_timeouts >= 15:
        fails.setdefault("TIMEOUT", []).extend(range(i + 1, n))
        break
finish(fails, n)
