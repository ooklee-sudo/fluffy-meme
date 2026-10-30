"""Pilot steps 2-3: ask each model generation the same questions (T=0, fixed prompt), grade vs accepted answer."""
import json, re, html, sys, time, urllib.request, concurrent.futures as cf

MODELS = {  # generation label -> OpenRouter id
    "gpt-3.5 (2022-11 proxy)": "openai/gpt-3.5-turbo-0613",
    "gpt-4 (2023-03)": "openai/gpt-4",
    "gpt-4o (2024-05)": "openai/gpt-4o-2024-05-13",
    "llama-3.1-8b (open proxy)": "meta-llama/llama-3.1-8b-instruct",
}
JUDGE = "openai/gpt-4.1-mini"
SYS = "You are an expert programmer answering a Stack Overflow question. Give a concise, correct answer."

def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()

def chat(model, messages, max_tokens, tries=4):
    body = json.dumps(dict(model=model, messages=messages, temperature=0, max_tokens=max_tokens)).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
                                         {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=120))
            return d["choices"][0]["message"]["content"] or "", d["usage"].get("cost", 0)
        except Exception as e:
            err = e; time.sleep(2 ** i)
    return f"ERROR {err}", 0

def one(job):
    q, label, mid = job
    prompt = f"{q['title']}\n\n{txt(q['question'])[:2500]}"
    ans, c1 = chat(mid, [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}], 500)
    jp = (f"Question:\n{prompt}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\n"
          f"Candidate answer:\n{ans[:2500]}\n\nDoes the candidate answer solve the question correctly and "
          "consistently with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT.")
    v, c2 = chat(JUDGE, [{"role": "user", "content": jp}], 5)
    return dict(tag=q["tag"], qid=q["qid"], model=label, correct=int(v.strip().upper().startswith("CORRECT")),
                err=ans.startswith("ERROR"), cost=c1 + c2)

qs = json.load(open("questions.json"))
jobs = [(q, l, m) for q in qs for l, m in MODELS.items()]
with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(one, jobs))
json.dump(res, open("results.json", "w"))
print("calls", len(res), "errors", sum(r["err"] for r in res), "cost $%.2f" % sum(r["cost"] for r in res))
