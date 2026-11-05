"""Week 1: answer questions with a (4-bit) LLM and save per-layer hidden states.

For each question this script
  1. generates a short greedy answer,
  2. records token-level confidence scores (mean/min log-prob, mean entropy),
  3. grades the answer against the gold aliases (correct = 1 / hallucination = 0),
  4. saves the hidden state of every layer at two positions:
       - "prompt": the last prompt token, i.e. before the model answers
       - "answer": the last token of the generated answer

Outputs (in --out):
  generations.jsonl   one line per question (answer, label, confidence scores)
  hidden_prompt.npy   float16, shape (N, num_layers + 1, hidden_size)
  hidden_answer.npy   same shape
  meta.json           run settings

The run can be stopped and restarted: it continues from the last saved question.

Example (RTX 5070 Laptop, 8 GB):
  python generate.py --model Qwen/Qwen3-8B --dataset triviaqa --n 1000 --out runs/qwen3-8b_triviaqa
"""

import argparse
import json
import os
import time

import numpy as np
import torch
from numpy.lib.format import open_memmap

from common import build_prompt, grade, load_model, load_questions


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="Qwen/Qwen3-8B")
    p.add_argument("--quant", default="4bit", choices=["4bit", "8bit", "none"])
    p.add_argument("--dataset", default="triviaqa", choices=["triviaqa", "nq", "jsonl"])
    p.add_argument("--data-path", help="jsonl file when --dataset jsonl")
    p.add_argument("--n", type=int, default=1000, help="number of questions")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=32)
    p.add_argument("--out", required=True)
    return p.parse_args()


@torch.no_grad()
def answer_one(model, tok, question, max_new_tokens):
    prompt = build_prompt(tok, question)
    enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    prompt_len = enc.input_ids.shape[1]

    out = model.generate(
        **enc,
        do_sample=False, temperature=None, top_p=None, top_k=None,
        max_new_tokens=max_new_tokens,
        return_dict_in_generate=True, output_logits=True,
        pad_token_id=tok.pad_token_id,
    )
    gen_ids = out.sequences[0, prompt_len:]

    # Drop end-of-turn / padding tokens at the end of the answer.
    stop_ids = {tok.eos_token_id, tok.pad_token_id}
    if isinstance(model.generation_config.eos_token_id, list):
        stop_ids |= set(model.generation_config.eos_token_id)
    n_ans = len(gen_ids)
    while n_ans > 0 and gen_ids[n_ans - 1].item() in stop_ids:
        n_ans -= 1
    ans_ids = gen_ids[:n_ans]
    answer = tok.decode(ans_ids, skip_special_tokens=True).strip()

    # Token-level confidence from the raw logits of the answer tokens.
    if n_ans > 0:
        logits = torch.stack(out.logits[:n_ans], dim=0)[:, 0].float()  # (n_ans, vocab)
        logp = torch.log_softmax(logits, dim=-1)
        tok_logp = logp.gather(1, ans_ids.view(-1, 1)).squeeze(1)
        entropy = -(logp.exp() * logp).sum(-1)
        scores = {"mean_logprob": tok_logp.mean().item(), "min_logprob": tok_logp.min().item(),
                  "mean_entropy": entropy.mean().item(), "first_logprob": tok_logp[0].item()}
    else:
        scores = {"mean_logprob": float("nan"), "min_logprob": float("nan"),
                  "mean_entropy": float("nan"), "first_logprob": float("nan")}

    # One forward pass over prompt + answer to read the hidden states of every layer.
    full = out.sequences[:, : prompt_len + n_ans]
    hs = model(input_ids=full, output_hidden_states=True).hidden_states  # tuple of (1, T, d)
    hs = torch.stack(hs, dim=0)[:, 0]  # (layers + 1, T, d)
    h_prompt = hs[:, prompt_len - 1].float().cpu().numpy()
    h_answer = hs[:, prompt_len + n_ans - 1].float().cpu().numpy()
    return answer, n_ans, scores, h_prompt, h_answer


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    gen_path = os.path.join(args.out, "generations.jsonl")
    meta_path = os.path.join(args.out, "meta.json")

    questions = load_questions(args.dataset, args.n, seed=args.seed, path=args.data_path)
    n = len(questions)
    print(f"{n} questions loaded from {args.dataset}")

    model, tok = load_model(args.model, args.quant)
    n_layers = model.config.num_hidden_layers + 1  # + embedding output
    hidden = model.config.hidden_size
    print(f"model: {args.model} | layers (incl. embeddings): {n_layers} | hidden size: {hidden}")

    # Resume support: count finished lines and reopen the arrays.
    done = 0
    if os.path.exists(gen_path) and os.path.exists(meta_path):
        with open(meta_path) as f:
            old = json.load(f)
        if old["model"] != args.model or old["n"] != n or old["dataset"] != args.dataset:
            raise SystemExit(f"{args.out} holds a different run; choose another --out")
        with open(gen_path, encoding="utf-8") as f:
            done = sum(1 for line in f if line.strip())
        print(f"resuming after {done} finished questions")
    else:
        with open(meta_path, "w") as f:
            json.dump({**vars(args), "n": n, "n_layers": n_layers, "hidden_size": hidden}, f, indent=2)
        open(gen_path, "w").close()

    mode = "r+" if done > 0 else "w+"
    shape = (n, n_layers, hidden)
    hp = open_memmap(os.path.join(args.out, "hidden_prompt.npy"), mode=mode, dtype=np.float16, shape=shape)
    ha = open_memmap(os.path.join(args.out, "hidden_answer.npy"), mode=mode, dtype=np.float16, shape=shape)

    n_correct = 0
    t0 = time.time()
    with open(gen_path, "a", encoding="utf-8") as fout:
        for i in range(done, n):
            q = questions[i]
            answer, n_ans, scores, h_p, h_a = answer_one(model, tok, q["question"], args.max_new_tokens)
            em, contains = grade(answer, q["answers"])
            hp[i], ha[i] = h_p, h_a
            row = {"idx": i, "id": q["id"], "question": q["question"], "answers": q["answers"][:10],
                   "prediction": answer, "n_answer_tokens": n_ans,
                   "exact_match": em, "correct": contains, **scores}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_correct += contains

            if (i + 1) % 10 == 0 or i == n - 1:
                fout.flush()
                hp.flush()
                ha.flush()
                k = i + 1 - done
                mem = torch.cuda.max_memory_allocated() / 2**30 if torch.cuda.is_available() else 0
                print(f"[{i + 1}/{n}] acc so far {n_correct / k:.3f} | "
                      f"{(time.time() - t0) / k:.2f}s/question | peak GPU mem {mem:.1f} GB")
                print(f"    Q: {q['question'][:70]}\n    A: {answer[:70]}  ->  {'O' if contains else 'X'}")

    print(f"done. results in {args.out}")


if __name__ == "__main__":
    main()
