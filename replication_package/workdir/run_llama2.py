"""Run Llama 2 chat (7B, 13B; pretraining cutoff Sep 2022) on the v2 questions via a vLLM server on RunPod,
grade with the same OpenRouter judge as run_v2.py. Usage: run_llama2.py <pod_id> <api_key_file> [llama2-13b,llama2-7b]"""
import json, re, html, os, sys, time, urllib.request, concurrent.futures as cf, threading
import os as _os
_HDR = {"Content-Type": "application/json"}
if _os.environ.get("OPENROUTER_API_KEY"): _HDR["Authorization"] = "Bearer " + _os.environ["OPENROUTER_API_KEY"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
POD, KEY = sys.argv[1], open(sys.argv[2]).read().strip()
PORTS = {"llama2-13b": 8000, "llama2-7b": 8001}
OUT = "results_llama2.jsonl"; lock = threading.Lock()
SYS = "You are an expert programmer answering a Stack Overflow question. Give a correct answer."
JUDGE = "openai/gpt-4.1-mini"

def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()
def extract(ans):
    m = re.search(r"```[^\n]*\n(.*?)```", ans, re.S)
    if m: return "First code block:\n" + m.group(1).strip()[:2500]
    paras = [p for p in re.split(r"\n\s*\n", ans.strip()) if p.strip()]
    return "Conclusion:\n" + (paras[-1] if paras else "")[:1500]

def post(url, body, headers, tries=4):
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception as e: err = e; time.sleep(2 ** i)
    return {"error": str(err)}

def gen(model, prompt):
    p = f"<s>[INST] <<SYS>>\n{SYS}\n<</SYS>>\n\n{prompt} [/INST]"
    d = post(f"https://{POD}-{PORTS[model]}.proxy.runpod.net/v1/completions",
             dict(model=model, prompt=p, temperature=0, max_tokens=1024),
             {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}", "User-Agent": "research-pilot/1.0"})
    if "choices" not in d: return "ERROR", None
    c = d["choices"][0]; return c["text"], c.get("finish_reason")

def judge(prompt, ref, ans):
    jp = (f"Question:\n{prompt}\n\nReference (accepted) answer:\n{ref}\n\nCandidate answer (key part only):\n{extract(ans)}\n\n"
          "Does the candidate's key part solve the question correctly, consistent with the reference answer's core solution? "
          "Reply with exactly CORRECT or INCORRECT.")
    d = post("https://openrouter.ai/api/v1/chat/completions", dict(model=JUDGE, temperature=0, max_tokens=5,
             messages=[{"role": "user", "content": jp}]), _HDR)
    try: return int(d["choices"][0]["message"]["content"].strip().upper().startswith("CORRECT"))
    except Exception: return None

def one(job):
    q, model = job
    prompt = f"{q['title']}\n\n{txt(q['question'])[:2500]}"
    ans, fin = gen(model, prompt)
    ok = None if ans == "ERROR" else judge(prompt, txt(q["accepted"])[:2000], ans)
    r = dict(tag=q["tag"], qid=q["qid"], rank=q["rank"], model=model, correct=ok, truncated=(fin == "length"), err=(ans == "ERROR"))
    with lock: open(OUT, "a").write(json.dumps(r) + "\n")

qs = json.load(open("questions_v2.json"))
done = set()
if os.path.exists(OUT):
    for l in open(OUT): x = json.loads(l); done.add((x["qid"], x["model"]))
only = sys.argv[3].split(",") if len(sys.argv) > 3 else list(PORTS)
jobs = [(q, m) for q in qs for m in only if (q["qid"], m) not in done]
print("jobs", len(jobs), flush=True)
with cf.ThreadPoolExecutor(24) as ex: list(ex.map(one, jobs))
print("finished")
