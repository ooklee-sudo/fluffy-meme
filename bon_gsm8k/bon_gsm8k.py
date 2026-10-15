"""Best-of-N under an LLM judge, scored by deterministic gold (GSM8K exact match).

J = reference-free LLM judge score (1-10), the cheap quote the search can see.
G = exact match against the GSM8K answer, the inspection the search never sees.
For each N the selector picks the candidate with the highest J among N drawn from K
generated candidates; we then report G, J, and length of the selected answer.

Needs: Python 3.9+, numpy. No other packages. API key in env var OPENROUTER_API_KEY.
    python bon_gsm8k.py --n-questions 200 --k 32 --max-usd 3
    python bon_gsm8k.py --mock            # offline self-test, no API calls
Runs resume from the cache files in --out, so an interrupted run can simply be restarted.
"""
import argparse, io, json, os, random, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

API = "https://openrouter.ai/api/v1"
GSM = "https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet"

def http(url, data=None, headers=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def load_gsm8k(n, seed):
    try:
        import pandas as pd
        df = pd.read_parquet(io.BytesIO(http(GSM)))
        rows = list(zip(df.question, df.answer))
    except ImportError:
        sys.exit("Reading GSM8K needs pandas+pyarrow: pip install pandas pyarrow")
    random.Random(seed).shuffle(rows)
    return [(i, q, a.split("####")[-1].strip().replace(",", "")) for i, (q, a) in enumerate(rows[:n])]

def prices(models):
    data = json.loads(http(API + "/models"))["data"]
    p = {m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])) for m in data}
    for m in models:
        if m not in p: sys.exit(f"Model id not found on OpenRouter: {m}")
    return p

class Spend:
    def __init__(self, cap): self.usd, self.cap = 0.0, cap
    def add(self, model_price, usage):
        self.usd += usage.get("prompt_tokens", 0) * model_price[0] + usage.get("completion_tokens", 0) * model_price[1]
        if self.usd > self.cap: raise RuntimeError(f"Spend cap reached: ${self.usd:.2f} > ${self.cap:.2f}")

def chat(model, prompt, temp, max_tokens, key, price, spend, retries=5):
    body = json.dumps({"model": model, "temperature": temp, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    hdr = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    for a in range(retries):
        try:
            r = json.loads(http(API + "/chat/completions", body, hdr))
            spend.add(price, r.get("usage", {}))
            return r["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403): sys.exit(f"API refused the request ({e.code}). Check key/credit.")
            time.sleep(2 ** a)
        except (urllib.error.URLError, KeyError, TimeoutError, json.JSONDecodeError):
            time.sleep(2 ** a)
    return None

GEN = "Solve the problem step by step. End with a line of the form 'Final answer: <number>'.\n\nProblem: {q}"
JUDGE = ("You are grading an answer to a math word problem. Rate the overall quality of the response "
         "(clarity, apparent correctness, completeness) from 1 to 10. Reply with the integer only.\n\n"
         "Problem: {q}\n\nResponse:\n{a}")

def extract(text):
    m = re.findall(r"final answer\s*[:=]?\s*\$?\s*(-?[\d,]*\.?\d+)", text, flags=re.I)
    if not m: m = re.findall(r"-?[\d,]*\.?\d+", text)
    return m[-1].replace(",", "") if m else None

def same(a, b):
    try: return a is not None and abs(float(a) - float(b)) < 1e-6
    except ValueError: return False

def jsonl_load(path):
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line); out[(r["qid"], r["k"])] = r
    return out

def run_stage(tasks, fn, path, workers):
    done = jsonl_load(path); todo = [t for t in tasks if (t[0], t[1]) not in done]
    print(f"{path}: {len(done)} cached, {len(todo)} to run", flush=True)
    with open(path, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, *t): t for t in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            if r is not None:
                f.write(json.dumps(r) + "\n"); f.flush(); done[(r["qid"], r["k"])] = r
            if i % 200 == 0: print(f"  {i}/{len(todo)}", flush=True)
    return done

def analyse(qs, gens, judges, K, Ns, draws, seed):
    rng = np.random.default_rng(seed)
    J, G, L = [], [], []
    keep = [qid for qid, _, _ in qs if all((qid, k) in gens and (qid, k) in judges for k in range(K))]
    gold = {qid: g for qid, _, g in qs}
    for qid in keep:
        J.append([judges[(qid, k)]["score"] for k in range(K)])
        G.append([1.0 if same(extract(gens[(qid, k)]["text"]), gold[qid]) else 0.0 for k in range(K)])
        L.append([len(gens[(qid, k)]["text"]) for k in range(K)])
    J, G, L = np.array(J, float), np.array(G), np.array(L, float)
    Q = len(keep); res = {"questions": Q, "K": K, "rows": []}
    res["mean_G_single"] = float(G.mean()); res["mean_J_single"] = float(J.mean())
    res["corr_J_G_within_q"] = float(np.nanmean([np.corrcoef(J[i], G[i])[0, 1] for i in range(Q) if J[i].std() > 0 and G[i].std() > 0]))
    res["corr_J_len_within_q"] = float(np.nanmean([np.corrcoef(J[i], L[i])[0, 1] for i in range(Q) if J[i].std() > 0 and L[i].std() > 0]))
    for N in Ns:
        sg, sj, sl, orc = np.zeros(Q), np.zeros(Q), np.zeros(Q), np.zeros(Q)
        for i in range(Q):
            for _ in range(draws):
                idx = rng.choice(K, N, replace=False)
                top = idx[np.flatnonzero(J[i, idx] == J[i, idx].max())]
                s = rng.choice(top)
                sg[i] += G[i, s]; sj[i] += J[i, s]; sl[i] += L[i, s]; orc[i] += G[i, idx].max()
        sg, sj, sl, orc = sg / draws, sj / draws, sl / draws, orc / draws
        b = [rng.integers(0, Q, Q) for _ in range(1000)]
        ci = lambda x: [float(np.percentile([x[j].mean() for j in b], p)) for p in (2.5, 97.5)]
        res["rows"].append({"N": N, "G_selected": float(sg.mean()), "G_ci": ci(sg), "J_selected": float(sj.mean()),
                            "len_selected": float(sl.mean()), "G_oracle": float(orc.mean())})
    return res

def show(res):
    print(f"\nquestions={res['questions']}  K={res['K']}  single-sample accuracy={res['mean_G_single']:.3f}")
    print(f"within-question corr(J,G)={res['corr_J_G_within_q']:.3f}  corr(J,length)={res['corr_J_len_within_q']:.3f}")
    print("\n  N | G (accuracy of selected) [95% CI] | J selected | length | oracle G")
    for r in res["rows"]:
        print(f"{r['N']:3d} | {r['G_selected']:.3f} [{r['G_ci'][0]:.3f}, {r['G_ci'][1]:.3f}] | {r['J_selected']:.2f} | {r['len_selected']:6.0f} | {r['G_oracle']:.3f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="meta-llama/llama-3.1-8b-instruct")
    ap.add_argument("--judge", default="openai/gpt-4o-mini")
    ap.add_argument("--n-questions", type=int, default=200)
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max-usd", type=float, default=3.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="bon_out")
    ap.add_argument("--mock", action="store_true", help="offline self-test with synthetic generator/judge")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    Ns = [n for n in (1, 2, 4, 8, 16, 32, 64) if n <= a.k]
    if a.mock:
        rng = random.Random(1)
        qs = [(i, f"q{i}", "42") for i in range(a.n_questions)]
        gens, judges = {}, {}
        for qid, _, _ in qs:
            for k in range(a.k):
                ok = rng.random() < 0.7; n = rng.randint(300, 1500)
                gens[(qid, k)] = {"text": "x" * n + f"\nFinal answer: {'42' if ok else '41'}"}
                s = 4 + 3 * ok + n / 600 + rng.gauss(0, 1.2)       # judge rewards correctness weakly, length strongly
                judges[(qid, k)] = {"score": max(1, min(10, round(s)))}
        res = analyse(qs, gens, judges, a.k, Ns, a.draws, a.seed); show(res); return
    key = os.environ.get("OPENROUTER_API_KEY") or sys.exit("Set OPENROUTER_API_KEY first.")
    pr = prices([a.policy, a.judge]); spend = Spend(a.max_usd)
    qs = load_gsm8k(a.n_questions, a.seed); qd = {qid: q for qid, q, _ in qs}
    def gen(qid, k):
        t = chat(a.policy, GEN.format(q=qd[qid]), 1.0, 700, key, pr[a.policy], spend)
        return None if t is None else {"qid": qid, "k": k, "text": t}
    gens = run_stage([(qid, k) for qid, _, _ in qs for k in range(a.k)], gen, os.path.join(a.out, "gens.jsonl"), a.workers)
    def judge(qid, k):
        t = chat(a.judge, JUDGE.format(q=qd[qid], a=gens[(qid, k)]["text"]), 0.0, 8, key, pr[a.judge], spend)
        m = re.search(r"\d+", t or "")
        return None if not m else {"qid": qid, "k": k, "score": max(1, min(10, int(m.group())))}
    judges = run_stage([(qid, k) for qid, _, _ in qs for k in range(a.k) if (qid, k) in gens], judge,
                       os.path.join(a.out, "judges.jsonl"), a.workers)
    print(f"estimated spend this run: ${spend.usd:.2f}")
    res = analyse(qs, gens, judges, a.k, Ns, a.draws, a.seed)
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=2); show(res)

if __name__ == "__main__":
    main()
