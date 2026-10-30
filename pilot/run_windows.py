"""Recency-gap pilot: each model answers questions from an old block and a recent block (last half-year before its
cutoff); same prompt (user message only), T=0, up to 2000 tokens, judged vs accepted answer by gpt-4.1-mini."""
import json, re, html, os, time, urllib.request, concurrent.futures as cf, threading
MODELS = {  # label: (OpenRouter id, old block, recent block)
    "gpt-3.5": ("openai/gpt-3.5-turbo-0613", "2019H1", "2021H1"),
    "llama-3.1-8b": ("meta-llama/llama-3.1-8b-instruct", "2021H2", "2023H2"),
    "gpt-4.1": ("openai/gpt-4.1", "2022H1", "2024H1"),
    "gemma-3-27b": ("google/gemma-3-27b-it", "2022H1", "2024H1"),
    "llama-4-scout": ("meta-llama/llama-4-scout", "2022H1", "2024H1"),
}
JUDGE = "openai/gpt-4.1-mini"; OUT = "results_windows.jsonl"; lock = threading.Lock()
PRE = "You are an expert programmer answering a Stack Overflow question. Give a correct answer.\n\n"
def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()
def extract(ans):
    m = re.search(r"```[^\n]*\n(.*?)```", ans, re.S)
    if m: return "First code block:\n" + m.group(1).strip()[:2500]
    paras = [p for p in re.split(r"\n\s*\n", ans.strip()) if p.strip()]
    return "Conclusion:\n" + (paras[-1] if paras else "")[:1500]
def chat(model, content, max_tokens, tries=4):
    body = json.dumps(dict(model=model, messages=[{"role": "user", "content": content}], temperature=0, max_tokens=max_tokens)).encode()
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=180)); c = d["choices"][0]
            return c["message"]["content"] or "", d["usage"].get("cost", 0), c.get("finish_reason")
        except Exception as e: err = e; time.sleep(2 ** i)
    return f"ERROR {err}", 0, "error"
def one(job):
    q, label, kind = job
    prompt = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    ans, c1, fin = chat(MODELS[label][0], PRE + prompt, 2000)
    ok = None
    if not ans.startswith("ERROR"):
        jp = (f"Question:\n{prompt}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\nCandidate answer (key part only):\n{extract(ans)}\n\n"
              "Does the candidate's key part solve the question correctly, consistent with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT.")
        v, c2, _ = chat(JUDGE, jp, 5); c1 += c2; ok = int(v.strip().upper().startswith("CORRECT"))
    r = dict(model=label, kind=kind, block=q["block"], tag=q["tag"], qid=q["qid"], correct=ok, truncated=(fin == "length"), err=ans.startswith("ERROR"), cost=c1)
    with lock: open(OUT, "a").write(json.dumps(r) + "\n")
qs = json.load(open("questions_windows.json"))
done = set()
if os.path.exists(OUT):
    for l in open(OUT): x = json.loads(l); done.add((x["qid"], x["block"], x["model"]))
jobs = [(q, l, "old" if q["block"] == o else "recent") for l, (_, o, r) in MODELS.items() for q in qs if q["block"] in (o, r) and (q["qid"], q["block"], l) not in done]
print("jobs", len(jobs), flush=True)
with cf.ThreadPoolExecutor(40) as ex: list(ex.map(one, jobs))
print("finished", flush=True)
