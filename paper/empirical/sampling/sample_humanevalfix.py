"""Sample n patches per HumanEvalFix(Python) bug from an OpenRouter model, run tests, log (success, tokens, cost).
Usage: python3 sample_humanevalfix.py MODEL N_SAMPLES [N_TASKS]"""
import sys, os, re, json, subprocess, tempfile, concurrent.futures as cf, urllib.request, time
import pandas as pd
MODEL, NS = sys.argv[1], int(sys.argv[2]); NT = int(sys.argv[3]) if len(sys.argv) > 3 else 164
OUT = f"raw_{MODEL.replace('/', '_')}.jsonl"
df = pd.read_parquet("hep_python.parquet").iloc[:NT]
done = set()
if os.path.exists(OUT):
    for l in open(OUT): r = json.loads(l); done.add((r["task"], r["i"]))

def prompt(r):
    return (f"Fix bugs in {r['entry_point']}.\n\n{r['declaration']}{r['buggy_solution']}\n\n"
            f"The function must satisfy its specification:\n{r['docstring']}\n\n"
            "Return the full corrected function in a single ```python code block, nothing else.")

def call(r):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt(r)}], "temperature": 1.0, "max_tokens": 1500, "usage": {"include": True}}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:
            time.sleep(2 ** attempt)
    return None

def extract(txt):
    m = re.findall(r"```(?:python)?\n(.*?)```", txt or "", re.S)
    return m[0] if m else (txt or "")

def run_tests(code, r):
    prog = f"{r['import']}\n{code}\n\n{r['test_setup']}\n{r['test']}\ncheck({r['entry_point']})\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py"); open(p, "w").write(prog)
        try:
            return subprocess.run([sys.executable, "-I", p], cwd=d, capture_output=True, timeout=10, stdin=subprocess.DEVNULL).returncode == 0
        except Exception: return False

def job(args):
    ti, i = args; r = df.iloc[ti]
    resp = call(r)
    if not resp or "choices" not in resp: return dict(task=r["task_id"], i=i, ok=False, error=True)
    txt = resp["choices"][0]["message"].get("content") or ""
    u = resp.get("usage", {})
    return dict(task=r["task_id"], i=i, ok=run_tests(extract(txt), r), pt=u.get("prompt_tokens"), ct=u.get("completion_tokens"), cost=u.get("cost"), error=False)

jobs = [(t, i) for t in range(len(df)) for i in range(NS) if (df.iloc[t]["task_id"], i) not in done]
print(len(jobs), "jobs", flush=True)
with cf.ThreadPoolExecutor(16) as ex, open(OUT, "a") as f:
    for n, res in enumerate(ex.map(job, jobs)):
        f.write(json.dumps(res) + "\n"); f.flush()
        if n % 500 == 0: print(n, flush=True)
