"""Held-out replication pipeline (configuration frozen in PREREG.md).

Stages (each resumable, one JSONL line per item):
  gen    : sample questions, generate answers, run L1 and L2
  judge  : run the LLM judge L3 on every non-abstained answer
Usage:
  python run_heldout.py gen   --gen qwen0.5b --n 1000
  python run_heldout.py judge --gen qwen0.5b --judge qwen1.5b
"""
import argparse, json, os, random, re, string, time
from collections import Counter

import torch

torch.set_num_threads(4)
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)
SQUAD = os.environ.get("SQUAD_DEV", "/tmp/dev-v2.0.json")
SEED = 20261030

GENS = {
    "qwen0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "smollm360m": "HuggingFaceTB/SmolLM2-360M-Instruct",
    "qwen1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
}
JUDGES = {
    "qwen1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "smollm1.7b": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
}
L2_MODEL = "deepset/roberta-base-squad2"
GEN_SYS = ("Answer the question using only the passage. Reply with a short answer (a few words) copied "
           "from the passage, or reply exactly UNANSWERABLE if the passage does not contain the answer.")
JUDGE_SYS = "You are a strict fact checker."


# ---------------------------------------------------------------- text utils
def norm(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def f1(a, b):
    ta, tb = norm(a).split(), norm(b).split()
    if not ta or not tb:
        return float(ta == tb)
    common = Counter(ta) & Counter(tb)
    n = sum(common.values())
    if n == 0:
        return 0.0
    p, r = n / len(ta), n / len(tb)
    return 2 * p * r / (p + r)


def is_hallucination(answer, gold, unanswerable):
    if unanswerable:
        return True
    na = norm(answer)
    for g in gold:
        ng = norm(g)
        if na and ng and (na in ng or ng in na):
            return False
        if f1(answer, g) >= 0.6:
            return False
    return True


# ---------------------------------------------------------------- L1 rules
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
PHONE = re.compile(r"(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]\d{3}[ -]\d{4}\b")
TEMPLATE = re.compile(r"<\|.*?\|>|\[/?INST\]|\{\{.*?\}\}|<unk>|</s>")
NUM = re.compile(r"\d+(?:\.\d+)?")


def l1_block(answer, passage):
    if EMAIL.search(answer) or SSN.search(answer) or CARD.search(answer) or PHONE.search(answer):
        return True
    if TEMPLATE.search(answer):
        return True
    toks = answer.lower().split()
    if len(toks) >= 4 and any(toks[i] == toks[i + 1] == toks[i + 2] == toks[i + 3] for i in range(len(toks) - 3)):
        return True
    tri = Counter(zip(toks, toks[1:], toks[2:]))
    if tri and max(tri.values()) >= 3:
        return True
    pnums = set(NUM.findall(passage.replace(",", "")))
    for n in NUM.findall(answer.replace(",", "")):
        if n not in pnums:
            return True
    return False


# ---------------------------------------------------------------- data
def load_sample(n):
    data = json.load(open(SQUAD))["data"]
    qs = []
    for art in data:
        for par in art["paragraphs"]:
            for qa in par["qas"]:
                qs.append({"id": qa["id"], "passage": par["context"], "question": qa["question"],
                           "unanswerable": bool(qa["is_impossible"]),
                           "gold": [a["text"] for a in qa["answers"]]})
    assert len(qs) == 11873, len(qs)
    return random.Random(SEED).sample(qs, n)


def chat(tok, system, user):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def read_done(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


@torch.no_grad()
def generate(model, tok, prompt, max_new):
    ids = tok(prompt, return_tensors="pt")
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


# ---------------------------------------------------------------- L2 (extractive QA verifier)
def load_l2():
    import numpy as np
    from transformers import AutoModelForQuestionAnswering, AutoTokenizer
    tk = AutoTokenizer.from_pretrained(L2_MODEL)
    m = AutoModelForQuestionAnswering.from_pretrained(L2_MODEL).eval()

    @torch.no_grad()
    def run(question, context):
        enc = tk(question, context, truncation="only_second", max_length=384, stride=128,
                 return_overflowing_tokens=True, return_offsets_mapping=True, padding=True, return_tensors="pt")
        offs = enc.pop("offset_mapping"); enc.pop("overflow_to_sample_mapping")
        out = m(**enc)
        best, best_txt, null_min = -1e9, "", 1e9
        for k in range(enc["input_ids"].shape[0]):
            sl, el = out.start_logits[k].numpy(), out.end_logits[k].numpy()
            null_min = min(null_min, sl[0] + el[0])
            seq = enc.sequence_ids(k)
            ctx = [i for i, sid in enumerate(seq) if sid == 1]
            for i in np.argsort(sl)[::-1][:20]:
                if i not in ctx:
                    continue
                for j in np.argsort(el)[::-1][:20]:
                    if j not in ctx or j < i or j - i + 1 > 30:
                        continue
                    sc = sl[i] + el[j]
                    if sc > best:
                        best, best_txt = sc, context[offs[k][i][0]:offs[k][j][1]]
        return {"answer": best_txt if best >= null_min else ""}
    return run


# ---------------------------------------------------------------- stages
def stage_gen(a):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    path = os.path.join(RES, f"gen_{a.gen}.jsonl")
    done = read_done(path)
    qs = load_sample(a.n)
    todo = qs[len(done):]
    if a.limit:
        todo = todo[: a.limit]
    if not todo:
        print("nothing to do"); return
    tok = AutoTokenizer.from_pretrained(GENS[a.gen])
    model = AutoModelForCausalLM.from_pretrained(GENS[a.gen], torch_dtype=torch.float32).eval()
    qa = load_l2()
    with open(path, "a") as fh:
        for i, q in enumerate(todo):
            t0 = time.time()
            ans = generate(model, tok, chat(tok, GEN_SYS, f"Passage: {q['passage']}\n\nQuestion: {q['question']}"), 24)
            gen_s = time.time() - t0
            rec = dict(q, answer=ans, gen_s=gen_s)
            rec["abstain"] = "UNANSWERABLE" in ans.upper()
            if not rec["abstain"]:
                rec["halluc"] = is_hallucination(ans, q["gold"], q["unanswerable"])
                rec["l1_block"] = l1_block(ans, q["passage"])
                t1 = time.time()
                pred = qa(q["question"], q["passage"])
                rec["l2_ms"] = (time.time() - t1) * 1000
                span = pred["answer"]
                rec["l2_span"] = span
                rec["l2_score"] = f1(span, ans) if span.strip() else 0.0
                rec["l2_block"] = rec["l2_score"] < 0.5
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            if (i + 1) % 25 == 0:
                print(f"[{a.gen}] {len(done)+i+1}/{a.n}", flush=True)


def stage_judge(a):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    gpath = os.path.join(RES, f"gen_{a.gen}.jsonl")
    jpath = os.path.join(RES, f"judge_{a.judge}_{a.gen}.jsonl")
    items = [r for r in read_done(gpath)]
    done = read_done(jpath)
    seen = {d["id"] for d in done}
    todo = [r for r in items if not r["abstain"] and r["id"] not in seen]
    if a.limit:
        todo = todo[: a.limit]
    if not todo:
        print("nothing to do"); return
    tok = AutoTokenizer.from_pretrained(JUDGES[a.judge])
    model = AutoModelForCausalLM.from_pretrained(JUDGES[a.judge], torch_dtype=torch.float32).eval()
    with open(jpath, "a") as fh:
        for i, r in enumerate(todo):
            user = (f"Passage: {r['passage']}\n\nQuestion: {r['question']}\n\nAnswer: {r['answer']}\n\n"
                    "Is the answer fully supported by the passage? Reply with exactly one word: SUPPORTED or UNSUPPORTED.")
            t0 = time.time()
            out = generate(model, tok, chat(tok, JUDGE_SYS, user), 4)
            lat = time.time() - t0
            fh.write(json.dumps({"id": r["id"], "raw": out, "unsupported": "UNSUPPORTED" in out.upper(),
                                 "latency_s": lat, "failure": lat > 2.0}) + "\n"); fh.flush()
            if (i + 1) % 25 == 0:
                print(f"[judge {a.judge}/{a.gen}] {len(done)+i+1}/{len(items)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["gen", "judge"])
    ap.add_argument("--gen", required=True, choices=list(GENS))
    ap.add_argument("--judge", default="qwen1.5b", choices=list(JUDGES))
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    (stage_gen if a.stage == "gen" else stage_judge)(a)
