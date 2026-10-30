"""Execution-based grading: model sees question + setup code, returns a python block storing `result`; we run it."""
import json, re, html, sys, os, subprocess, tempfile, time, urllib.request, concurrent.futures as cf

MODELS = {"gpt-3.5": "openai/gpt-3.5-turbo-0613", "gpt-4": "openai/gpt-4",
          "gpt-4o": "openai/gpt-4o-2024-05-13", "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct"}
def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()

def chat(model, prompt):
    body = json.dumps(dict(model=model, temperature=0, max_tokens=2000,
                           messages=[{"role": "system", "content": "You are an expert Python programmer."},
                                     {"role": "user", "content": prompt}])).encode()
    for i in range(4):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=180))
            return d["choices"][0]["message"]["content"] or "", d["usage"].get("cost", 0)
        except Exception: time.sleep(2 ** i)
    return "", 0

def run(code, timeout=20):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py"); open(p, "w").write(code)
        try: return subprocess.run([sys.executable, "-I", p], capture_output=True, timeout=timeout, cwd=d).returncode == 0
        except subprocess.TimeoutExpired: return False

qs = {q["qid"]: q for q in json.load(open("questions_v2.json"))}
tests = json.load(open("tests_v2.json"))

def one(job):
    t, label = job; q = qs[t["qid"]]
    prompt = (f"{q['title']}\n\n{txt(q['question'])[:3000]}\n\nAssume this setup code has already been run:\n{t['setup']}\n\n"
              "Write Python code that stores the final answer in a variable named `result`. Reply with one ```python block.")
    ans, c = chat(MODELS[label], prompt)
    m = re.search(r"```(?:python)?\n(.*?)```", ans, re.S)
    ok = bool(m) and run(f"{t['setup']}\n{m.group(1)}\n{t['assertions']}")
    return dict(qid=t["qid"], tag=t["tag"], model=label, exec_correct=int(ok), cost=c)

with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, [(t, l) for t in tests for l in MODELS]))
json.dump(res, open("results_tests_v2.json", "w"))
for l in MODELS:
    r = [x for x in res if x["model"] == l]; print(l, "%d/%d = %.2f" % (sum(x["exec_correct"] for x in r), len(r), sum(x["exec_correct"] for x in r) / len(r)))
print("cost $%.2f" % sum(x["cost"] for x in res))
