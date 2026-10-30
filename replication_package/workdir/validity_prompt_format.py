"""Table 3 (Section 4.1): re-ask the 80 validity-check questions with the F1 prompt (system message) and compare with the
F2 run stored in validity_check.json and with the earlier large run in results_v2.jsonl. Needs OPENROUTER_API_KEY outside the original environment.
NOTE: the raw outputs of the run reported in the manuscript were not stored; re-running gives slightly different values (item-level agreement 84-89%)."""
import json, re, html, time, urllib.request, statistics as st, concurrent.futures as cf, os as _os
_HDR = {"Content-Type": "application/json"}
if _os.environ.get("OPENROUTER_API_KEY"): _HDR["Authorization"] = "Bearer " + _os.environ["OPENROUTER_API_KEY"]
MOD = {"gpt-3.5": "openai/gpt-3.5-turbo-0613", "gpt-4o": "openai/gpt-4o-2024-05-13"}
SYS = "You are an expert programmer answering a Stack Overflow question. Give a correct answer."
def txt(s): return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()
def extract(a):
    m = re.search(r"```[^\n]*\n(.*?)```", a, re.S)
    if m: return "First code block:\n" + m.group(1).strip()[:2500]
    ps = [p for p in re.split(r"\n\s*\n", a.strip()) if p.strip()]; return "Conclusion:\n" + (ps[-1] if ps else "")[:1500]
def call(model, messages, mt):
    body = json.dumps(dict(model=model, messages=messages, temperature=0, max_tokens=mt)).encode()
    for i in range(4):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, _HDR), timeout=180))
            return d["choices"][0]["message"]["content"] or "", d["usage"].get("cost", 0)
        except Exception: time.sleep(2 ** i)
    return "ERROR", 0
qs = {q["qid"]: q for q in json.load(open("questions_v2.json"))}
val = json.load(open("validity_check.json")); qids = sorted({r["qid"] for r in val})
prev = {}
for l in open("results_v2.jsonl"):
    x = json.loads(l); prev.setdefault((x["qid"], x["model"]), x["correct"])
def one(job):
    qid, m = job; q = qs[qid]; p = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    a, c = call(MOD[m], [{"role": "system", "content": SYS}, {"role": "user", "content": p}], 2000)
    if a == "ERROR": return None
    v, c2 = call("openai/gpt-4.1-mini", [{"role": "user", "content": f"Question:\n{p}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\nCandidate answer (key part only):\n{extract(a)}\n\nDoes the candidate's key part solve the question correctly, consistent with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT."}], 5)
    return dict(qid=qid, model=m, r1=int(v.strip().upper().startswith("CORRECT")), cost=c + c2)
with cf.ThreadPoolExecutor(24) as ex: res = [r for r in ex.map(one, [(q, m) for q in qids for m in MOD]) if r]
json.dump(res, open("results_validity_systemrole.json", "w"))
f2 = {(r["qid"], r["model"]): r["r1"] for r in val}
print("cost $%.2f" % sum(r["cost"] for r in res)); print("%-9s %12s %12s %16s" % ("model", "F2 (stored)", "F1 (rerun)", "earlier large run"))
for m in MOD:
    a = [f2[(q, m)] for q in qids if (q, m) in f2]; b = [r["r1"] for r in res if r["model"] == m]; c = [prev[(q, m)] for q in qids if prev.get((q, m)) is not None]
    ag = [prev[(r["qid"], m)] == r["r1"] for r in res if r["model"] == m and prev.get((r["qid"], m)) is not None]
    print("%-9s %11.1f%% %11.1f%% %15.1f%%   item-level agreement F1 rerun vs earlier run: %.0f%%" % (m, 100 * st.mean(a), 100 * st.mean(b), 100 * st.mean(c), 100 * st.mean(ag)))
