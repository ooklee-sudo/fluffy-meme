"""Build executable tests for python/pandas questions. A test is kept only if the reference solution passes it
and an empty candidate fails it."""
import json, re, html, subprocess, sys, tempfile, os, urllib.request, concurrent.futures as cf
import os as _os
_HDR = {"Content-Type": "application/json"}
if _os.environ.get("OPENROUTER_API_KEY"): _HDR["Authorization"] = "Bearer " + _os.environ["OPENROUTER_API_KEY"]

def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()

def chat(prompt):
    body = json.dumps(dict(model="openai/gpt-4.1", temperature=0, max_tokens=1800,
                           response_format={"type": "json_object"},
                           messages=[{"role": "user", "content": prompt}])).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, _HDR)
    return json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]

def run(code, timeout=20):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py"); open(p, "w").write(code)
        try:
            r = subprocess.run([sys.executable, "-I", p], capture_output=True, timeout=timeout, cwd=d)
            return r.returncode == 0
        except subprocess.TimeoutExpired:
            return False

PROMPT = """Turn this Stack Overflow question into a deterministic, self-contained Python test.
Return JSON with keys: "eligible" (bool; false if the problem cannot be checked by running pure-Python/pandas/numpy code without files, network, randomness or external services),
"setup" (code defining the small input variables the question talks about, using literal data),
"reference" (code that runs after setup and stores the correct answer in variable `result`, based on the accepted answer),
"assertions" (code that runs after `result` is set and asserts it is correct; compare values, not identity; use pandas.testing or numpy.testing where relevant).
Question:
{q}

Accepted answer:
{a}"""

def build(q):
    try:
        j = json.loads(chat(PROMPT.format(q=f"{q['title']}\n{txt(q['question'])[:2500]}", a=txt(q['accepted'])[:2000])))
        if not j.get("eligible"): return None
        s, r, a = j["setup"], j["reference"], j["assertions"]
        if run(f"{s}\n{r}\n{a}") and not run(f"{s}\n{a}"):
            return dict(qid=q["qid"], tag=q["tag"], rank=q["rank"], title=q["title"], setup=s, reference=r, assertions=a)
    except Exception:
        return None

qs = [q for q in json.load(open("questions_v2.json")) if q["tag"] in ("python", "pandas")]
with cf.ThreadPoolExecutor(8) as ex: res = [x for x in ex.map(build, qs) if x]
json.dump(res, open("tests_v2.json", "w"))
print("candidates", len(qs), "validated tests", len(res), {t: sum(x["tag"] == t for x in res) for t in ("python", "pandas")})
