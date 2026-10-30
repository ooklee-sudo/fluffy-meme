"""Is the tag-accuracy metric valid? Regenerate answers for 80 questions with GPT-3.5, GPT-4o (all 80) and GPT-4 (first 30),
grade with (R1) the original 'same core solution as accepted answer, key part only' rubric and (R2) a relaxed rubric
('accepted answer is one valid solution; would the candidate solve the asker's problem?', full answer, stronger judge)."""
import json, re, html, random, time, urllib.request, collections, statistics as st, concurrent.futures as cf
MOD = {"gpt-3.5": "openai/gpt-3.5-turbo-0613", "gpt-4o": "openai/gpt-4o-2024-05-13", "gpt-4": "openai/gpt-4"}
J1, J2 = "openai/gpt-4.1-mini", "openai/gpt-4.1"
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
qs = {q["qid"]: q for q in json.load(open("questions_v2.json"))}
have = sorted({json.loads(l)["qid"] for l in open("results_v2.jsonl") if json.loads(l)["model"] == "gpt-4o"})
random.seed(5); sample = random.sample(have, 80)
def R1(q, ans):
    p = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    v, c = chat(J1, f"Question:\n{p}\n\nReference (accepted) answer:\n{txt(q['accepted'])[:2000]}\n\nCandidate answer (key part only):\n{extract(ans)}\n\nDoes the candidate's key part solve the question correctly, consistent with the reference answer's core solution? Reply with exactly CORRECT or INCORRECT.", 5)
    return int(v.strip().upper().startswith("CORRECT")), c
def R2(q, ans):
    p = f"{q['title']}\n\n{txt(q['question'])[:3000]}"
    v, c = chat(J2, f"Question:\n{p}\n\nThe accepted answer below is ONE valid solution; other valid approaches also count.\nAccepted answer:\n{txt(q['accepted'])[:2000]}\n\nCandidate answer:\n{ans[:4000]}\n\nWould the candidate answer correctly solve the asker's problem (working code or a correct explanation, no major errors)? Ignore style and length. Reply with exactly CORRECT or INCORRECT.", 5)
    return int(v.strip().upper().startswith("CORRECT")), c
def one(job):
    qid, m = job; q = qs[qid]
    ans, c = chat(MOD[m], PRE + f"{q['title']}\n\n{txt(q['question'])[:3000]}", 2000)
    if ans.startswith("ERROR"): return None
    r1, c1 = R1(q, ans); r2, c2 = R2(q, ans)
    return dict(qid=qid, tag=q["tag"], model=m, r1=r1, r2=r2, len=len(ans), cost=c + c1 + c2, answer=re.sub(r"(?:[ps]k\.)?eyJ[A-Za-z0-9_\-]{8,}(?:\.[A-Za-z0-9_\-]+)*", "[REDACTED]", ans))
jobs = [(q, m) for q in sample for m in ("gpt-3.5", "gpt-4o")] + [(q, "gpt-4") for q in sample[:30]]
with cf.ThreadPoolExecutor(24) as ex: res = [r for r in ex.map(one, jobs) if r]
json.dump(res, open("validity_check.json", "w"), ensure_ascii=False)
print("cost $%.2f, rows %d" % (sum(r["cost"] for r in res), len(res)))
print("\n%-9s %4s %9s %9s %8s" % ("model", "n", "R1 orig", "R2 relax", "avg len"))
for m in ("gpt-3.5", "gpt-4o", "gpt-4"):
    s = [r for r in res if r["model"] == m]
    print("%-9s %4d %8.1f%% %8.1f%% %8.0f" % (m, len(s), 100 * st.mean(r["r1"] for r in s), 100 * st.mean(r["r2"] for r in s), st.mean(r["len"] for r in s)))
first30 = set(sample[:30])
print("\nSame 30 questions for all three models:")
for m in ("gpt-3.5", "gpt-4o", "gpt-4"):
    s = [r for r in res if r["model"] == m and r["qid"] in first30]
    print("%-9s %4d %8.1f%% %8.1f%%" % (m, len(s), 100 * st.mean(r["r1"] for r in s), 100 * st.mean(r["r2"] for r in s)))
