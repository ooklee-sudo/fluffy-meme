"""v2 main measurement. Uncapped-ish output (2000 tok, truncation logged); judge sees first code block or conclusion only.
gpt-4 runs on rank<=10 and gpt-4o on rank<=20 per tag (nested subsets) to stay within budget. Resumable via results_v2.jsonl."""
import json, re, html, os, time, urllib.request, concurrent.futures as cf, threading

MODELS = {
    "gpt-3.5": ("openai/gpt-3.5-turbo-0613", 99),
    "gpt-4": ("openai/gpt-4", 10),
    "gpt-4o": ("openai/gpt-4o-2024-05-13", 20),
    "llama-3.1-8b": ("meta-llama/llama-3.1-8b-instruct", 99),
}
JUDGE = "openai/gpt-4.1-mini"
SYS = "You are an expert programmer answering a Stack Overflow question. Give a correct answer."
OUT = "results_v2.jsonl"; lock = threading.Lock()

def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()

def extract(ans):
    m = re.search(r"```[^\n]*\n(.*?)```", ans, re.S)
    if m: return "First code block:\n" + m.group(1).strip()[:2500]
    paras = [p for p in re.split(r"\n\s*\n", ans.strip()) if p.strip()]
    return "Conclusion:\n" + (paras[-1] if paras else "")[:1500]

def chat(model, messages, max_tokens, tries=4):
    body = json.dumps(dict(model=model, messages=messages, temperature=0, max_tokens=max_tokens)).encode()
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=180))
            c = d["choices"][0]
            return c["message"]["content"] or "", d["usage"].get("cost", 0), c.get("finish_reason")
        except Exception as e:
            err = e; time.sleep(2 ** i)
    return f"ERROR {err}", 0, "error"

def one(job):
    q, label = job
    prompt = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    ans, c1, fin = chat(MODELS[label][0], [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}], 2000)
    jp = (f"Question:\n{prompt}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\n"
          f"Candidate answer (key part only):\n{extract(ans)}\n\nDoes the candidate's key part solve the question "
          "correctly, consistent with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT.")
    v, c2, _ = chat(JUDGE, [{"role": "user", "content": jp}], 5)
    r = dict(tag=q["tag"], qid=q["qid"], rank=q["rank"], model=label, correct=int(v.strip().upper().startswith("CORRECT")),
             err=ans.startswith("ERROR"), truncated=(fin == "length"), cost=c1 + c2)
    with lock: open(OUT, "a").write(json.dumps(r) + "\n")

qs = json.load(open("questions_v2.json"))
done = set()
if os.path.exists(OUT):
    for l in open(OUT): x = json.loads(l); done.add((x["qid"], x["model"]))
jobs = [(q, l) for q in qs for l, (_, maxrank) in MODELS.items() if q["rank"] <= maxrank and (q["qid"], l) not in done]
print("jobs", len(jobs), flush=True)
with cf.ThreadPoolExecutor(16) as ex: list(ex.map(one, jobs))
print("finished")
