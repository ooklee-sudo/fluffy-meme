"""Prompt-format robustness of tag-level accuracy. Formats: F1 system-role (existing, results_v2.jsonl), F2 user-message with instruction, F3 bare question.
30 tags x 40 q; GPT-3.5 and Llama 3.1 8B on F2, F3; GPT-4o on F2 for the 400 questions it already has under F1. Judge: same R1 rubric, gpt-4.1-mini."""
import json, re, html, os, time, urllib.request, concurrent.futures as cf, threading
OUT = "results_formats.jsonl"; lock = threading.Lock()
MOD = {"gpt-3.5": "openai/gpt-3.5-turbo-0613", "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct", "gpt-4o": "openai/gpt-4o-2024-05-13"}
PRE = "You are an expert programmer answering a Stack Overflow question. Give a correct answer.\n\n"
def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()
def extract(a):
    m = re.search(r"```[^\n]*\n(.*?)```", a, re.S)
    if m: return "First code block:\n" + m.group(1).strip()[:2500]
    ps = [p for p in re.split(r"\n\s*\n", a.strip()) if p.strip()]; return "Conclusion:\n" + (ps[-1] if ps else "")[:1500]
def chat(model, content, mt, tries=4):
    body = json.dumps(dict(model=model, messages=[{"role": "user", "content": content}], temperature=0, max_tokens=mt)).encode()
    for i in range(tries):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json"}), timeout=180))
            return d["choices"][0]["message"]["content"] or "", d["usage"].get("cost", 0)
        except Exception as e: err = e; time.sleep(2 ** i)
    return "ERROR " + str(err), 0
def one(job):
    q, model, fmt = job
    p = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    a, c = chat(MOD[model], (PRE + p) if fmt == "F2" else p, 2000)
    if a.startswith("ERROR"): return
    v, c2 = chat("openai/gpt-4.1-mini", f"Question:\n{p}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\nCandidate answer (key part only):\n{extract(a)}\n\nDoes the candidate's key part solve the question correctly, consistent with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT.", 5)
    r = dict(model=model, fmt=fmt, qid=q["qid"], tag=q["tag"], correct=int(v.strip().upper().startswith("CORRECT")), cost=c + c2)
    with lock: open(OUT, "a").write(json.dumps(r) + "\n")
qs = json.load(open("questions_v2.json")); tags = list(dict.fromkeys(q["tag"] for q in qs))[:30]
qs = [q for q in qs if q["tag"] in tags]
have4o = {json.loads(l)["qid"] for l in open("results_v2.jsonl") if json.loads(l)["model"] == "gpt-4o"}
done = set()
if os.path.exists(OUT):
    for l in open(OUT): x = json.loads(l); done.add((x["qid"], x["model"], x["fmt"]))
jobs = [(q, m, f) for q in qs for m in ("gpt-3.5", "llama-3.1-8b") for f in ("F2", "F3")] + [(q, "gpt-4o", "F2") for q in qs if q["qid"] in have4o]
jobs = [j for j in jobs if (j[0]["qid"], j[1], j[2]) not in done]
print("jobs", len(jobs), flush=True)
with cf.ThreadPoolExecutor(64) as ex: list(ex.map(one, jobs))
print("finished", flush=True)
