"""Retrieval and in-context baselines on the real-law fact bank, with a diagnosis of the weak in-context result.

Question 1 (diagnosis). Is the weak effect of placing an amended statement in the prompt caused by the launch fine-tuning,
which may have taught the model to ignore context? We compare the same prompt formats on
  base      : the pretrained model, which was never fine-tuned on the old values
  launch3   : launch model after 3 epochs of fine-tuning on the old values
  launch10  : after 10 epochs
  launch    : the launch model used elsewhere (trained until token accuracy 0.995)
Question 2 (retrieval). What does a retrieval-augmented setup do on the same amendments?
  rag_incremental : the document store holds one statement per provision; only provisions that are listed in the update have their
                    statement replaced by the new text, the others keep the old text (stale), as in an index refreshed only for known changes
  rag_full        : the store holds the current statement of every provision (an up-to-date consolidated text; an upper bound)
Retrieval is TF-IDF over the provision reference and the last words of the statement; top-k statements are placed before the question.

Prompt formats: plain | ike_own | ike_all | instr_all | rag_incremental | rag_full
Run: python lm_rag_gpu.py --model Qwen/Qwen2.5-7B --seeds 1 2 3 --out rag_qwen7b.json
"""
import argparse, json, os, random, time, gc
import torch
from transformers import AutoModelForCausalLM
from sklearn.feature_extraction.text import TfidfVectorizer
import lm_reallaw_gpu as RL
import lm_editors_gpu as ED

def statement(f, value): return RL.prefix(f) + value + "."

def store(bank, listed, mode):
    docs = []
    for i, f in enumerate(bank):
        val = f["old"] if f["kind"] == "control" else (f["new"] if (mode == "full" or i in listed) else f["old"])
        docs.append(statement(f, val))
    return docs

def index_text(f): return f"{f['act_name']} section {f['section']} {f['title']} " + " ".join(f["ctx"].split()[-8:])

def retrieve(bank, docs, k):
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit([index_text(f) for f in bank])
    D = vec.transform([index_text(f) for f in bank]); out = []; hit = 0
    for i, f in enumerate(bank):
        sims = (D @ vec.transform([index_text(f)]).T).toarray().ravel()
        top = sims.argsort()[::-1][:k]; hit += int(i in top)
        out.append("\n".join(docs[j] for j in top))
    return out, hit / len(bank)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B"); ap.add_argument("--bank", default="real_fact_bank.json")
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=100); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1]); ap.add_argument("--kA", type=float, default=0.5); ap.add_argument("--kdep", type=float, default=0.0)
    ap.add_argument("--k", type=int, default=3); ap.add_argument("--variants", nargs="+", default=["base", "launch3", "launch10", "launch"])
    ap.add_argument("--out", default="rag.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); bank = json.load(open(args.bank)); n = len(bank)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []; done = {(r["seed"], r["variant"], r["format"]) for r in rows}
    ctl = [i for i, f in enumerate(bank) if f["kind"] == "control"]
    for seed in args.seeds:
        listed = ED.choose_listed(bank, seed, args.kA, args.kdep); drng = random.Random(seed * 5); dist = {i: RL.distractor(bank[i], drng) for i in ctl}
        auth = [bank[i]["new"] if bank[i]["kind"] == "changed" else bank[i]["old"] for i in range(n)]
        alt = [bank[i]["old"] if bank[i]["kind"] == "changed" else dist[i] for i in range(n)]
        pr = [RL.prefix(f) for f in bank]
        inc_docs, full_docs = store(bank, listed, "incremental"), store(bank, listed, "full")
        inc_ctx, inc_hit = retrieve(bank, inc_docs, args.k); full_ctx, full_hit = retrieve(bank, full_docs, args.k)
        own = {i: statement(bank[i], bank[i]["new"]) for i in listed}; allst = "\n".join(own[i] for i in sorted(listed))
        formats = {
            "plain": pr,
            "ike_own": [own[i] + "\n" + pr[i] if i in listed else pr[i] for i in range(n)],
            "ike_all": [allst + "\n" + p for p in pr],
            "instr_all": ["The following statements give the current text of provisions of the law. Complete the final sentence exactly as the current text does.\n" + allst + "\n\n" + p for p in pr],
            "rag_incremental": [inc_ctx[i] + "\n\n" + pr[i] for i in range(n)],
            "rag_full": [full_ctx[i] + "\n\n" + pr[i] for i in range(n)]}
        for variant in args.variants:
            todo = [fm for fm in formats if (seed, variant, fm) not in done]
            if not todo: continue
            if variant == "base":
                tok = RL.AutoTokenizer.from_pretrained(args.model)
                if tok.pad_token is None: tok.pad_token = tok.eos_token
                model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16 if dev.type == "cuda" else torch.float32).to(dev); c = None
            else:
                a = argparse.Namespace(**vars(args)); a.launch_epochs = {"launch3": 3, "launch10": 10, "launch": args.launch_epochs}[variant]
                cache = {}; c = RL.launch(a, seed, bank, cache, dev); tok, model = c["tok"], c["model"]
            for fm in todo:
                ok = ED.pref_prompts(model, tok, formats[fm], auth, alt, dev, bs=6)
                r = dict(seed=seed, variant=variant, format=fm, n_listed=len(listed), retrieval_at_k=(inc_hit if fm == "rag_incremental" else full_hit if fm == "rag_full" else None),
                         launch_acc=(c["acc"] if c else None), **ED.metrics(ok, bank, listed))
                rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
                print(f"seed={seed} {variant:9s} {fm:16s} " + " ".join(f"{k}={r[k]:.2f}" for k in ("listed", "unlisted_AB", "ripple_dep", "keep_control", "currency_all")), flush=True)
            del model, c; gc.collect(); torch.cuda.empty_cache()

if __name__ == "__main__":
    main()
