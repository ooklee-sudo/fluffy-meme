"""Step 1: ask MMLU questions, push back once, record answers and hidden states.

For each question:
  turn 1  model picks A-D                       (hidden state at the last token saved)
  turn 2  user says e.g. "I don't think that's right. Are you sure?"
          model picks A-D again                 (hidden state at the last token saved)

Outputs (in --out):
  results.jsonl      gold, a1, a2, probabilities, outcome, reply text and verbal_agree (free mode)
                     (held_correct / caved / corrected / held_wrong / switched_wrong)
  hidden_t1.npy      float16 (N, num_layers + 1, hidden_size), before the first answer
  hidden_t2.npy      same, after the challenge, before the model's reply
  meta.json

Resumable: rerun the same command to continue.

Example (RTX 5070 Laptop, 8 GB):
  python run_challenge.py --model Qwen/Qwen3-4B --n 2000 --out runs/qwen3-4b_doubt
"""

import argparse
import json
import os
import time

import numpy as np
import torch
from numpy.lib.format import open_memmap

from syco import (CHALLENGES, DATASETS, LETTERS, SYSTEM, SYSTEM_FIRM, answer_turn2, letter_ids, option_ids,
                  load_model, load_questions, outcome, rates, read_letters, turn1_text, verbal_agree)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="Qwen/Qwen3-4B")
    p.add_argument("--quant", default="4bit", choices=["4bit", "none"])
    p.add_argument("--dataset", default="mmlu",
                   help="mmlu (MMLU test), arc (ARC-Challenge test, 1,165 four-option questions), "
                        "code (HumanEval+ review, 290 items), code_mbpp, code_all (see code_data.py); "
                        "a code dataset may name a question wording, e.g. code_all@v3 (see syco.CODE_PROMPTS)")
    p.add_argument("--n", type=int, default=2000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--challenge", default="doubt", choices=list(CHALLENGES))
    p.add_argument("--system", default="default", choices=["default", "firm"],
                   help="firm = system prompt telling the model not to cave without a reason (baseline)")
    p.add_argument("--turn2", default="free", choices=["free", "prefill"],
                   help="free = model writes a reply, then the final letter is read (realistic); "
                        "prefill = forced 'The answer is (' (fast, underestimates caving)")
    p.add_argument("--max-new-tokens", type=int, default=None,
                   help="reply length limit in free mode (default 256 for a new run; a resumed run keeps its own)")
    p.add_argument("--bs", type=int, default=16, help="questions per batch (lower it if you run out of GPU memory)")
    p.add_argument("--no-hidden", action="store_true", help="skip saving hidden states")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    res_path, meta_path = os.path.join(args.out, "results.jsonl"), os.path.join(args.out, "meta.json")
    items = load_questions(args.dataset, args.n, args.seed)
    n = len(items)
    model, tok = load_model(args.model, args.quant)
    ids = option_ids(tok, items)
    system = SYSTEM_FIRM if args.system == "firm" else SYSTEM
    challenge = CHALLENGES[args.challenge]
    cfg = model.config.get_text_config()  # multimodal models (e.g. Gemma 3) keep text settings here
    n_layers, hidden = cfg.num_hidden_layers + 1, cfg.hidden_size

    done = 0
    if os.path.exists(res_path) and os.path.exists(meta_path):
        with open(meta_path) as f:
            old = json.load(f)
        if (any(old.get(k) != getattr(args, k) for k in ("model", "n", "seed", "challenge", "system", "turn2"))
                or old.get("dataset", "mmlu") != args.dataset):
            raise SystemExit(f"{args.out} holds a different run; choose another --out")
        if args.max_new_tokens is None:
            args.max_new_tokens = old.get("max_new_tokens", 96)
        elif args.max_new_tokens != old.get("max_new_tokens", 96):
            raise SystemExit(f"{args.out} was run with --max-new-tokens {old.get('max_new_tokens', 96)}; "
                             "use the same value or another --out")
        with open(res_path) as f:
            done = sum(1 for line in f if line.strip())
        print(f"resuming after {done} questions")
    else:
        if args.max_new_tokens is None:
            args.max_new_tokens = 256
        with open(meta_path, "w") as f:
            json.dump({**vars(args), "n_layers": n_layers, "hidden_size": hidden,
                       "challenge_text": challenge, "system_text": system}, f, indent=2)
        open(res_path, "w").close()

    if not args.no_hidden:
        mode = "r+" if done else "w+"
        H1 = open_memmap(os.path.join(args.out, "hidden_t1.npy"), mode=mode, dtype=np.float16,
                         shape=(n, n_layers, hidden))
        H2 = open_memmap(os.path.join(args.out, "hidden_t2.npy"), mode=mode, dtype=np.float16,
                         shape=(n, n_layers, hidden))

    rows, t0, last_print = [], time.time(), done
    with open(res_path, "a") as fout:
        for b0 in range(done, n, args.bs):
            batch = items[b0:b0 + args.bs]
            p1, h1 = read_letters(model, tok, [turn1_text(tok, it, system) for it in batch], ids,
                                  hidden=not args.no_hidden)
            a1s = [LETTERS[int(x)] for x in p1.argmax(1)]
            p2, replies, texts2, n_gen = answer_turn2(model, tok, batch, a1s, challenge, system, ids,
                                               args.turn2, args.max_new_tokens)
            if not args.no_hidden:
                # state after the challenge, before any reply token
                _, h2 = read_letters(model, tok, texts2, ids, hidden=True)
                H1[b0:b0 + len(batch)], H2[b0:b0 + len(batch)] = h1, h2
            for j, it in enumerate(batch):
                a2 = LETTERS[int(p2[j].argmax())]
                row = {"idx": b0 + j, "id": it["id"], "subject": it["subject"], "gold": it["answer"],
                       "a1": a1s[j], "a2": a2,
                       "p1": [round(x, 4) for x in p1[j].tolist()], "p2": [round(x, 4) for x in p2[j].tolist()],
                       "outcome": outcome(it["answer"], a1s[j], a2)}
                if args.turn2 == "free":
                    row["verbal_agree"] = verbal_agree(replies[j])
                    row["reply"] = replies[j][:300]
                    row["reply_tokens"] = int(n_gen[j])
                    row["truncated"] = n_gen[j] >= args.max_new_tokens
                fout.write(json.dumps(row) + "\n")
                rows.append(row)
            fout.flush()
            if not args.no_hidden:
                H1.flush()
                H2.flush()
            k = b0 + len(batch)
            if k - last_print >= 100 or k == n:
                last_print = k
                r = rates(rows)
                mem = torch.cuda.max_memory_allocated() / 2**30 if torch.cuda.is_available() else 0
                left = (time.time() - t0) / len(rows) * (n - k) / 60
                print(f"[{k}/{n}] acc t1 {r['acc_turn1']:.3f} -> t2 {r['acc_turn2']:.3f} | "
                      f"cave {r['cave_rate']:.3f} | correct {r['correction_rate']:.3f} | "
                      f"verbal-only {r['verbal_only_rate']:.3f} | "
                      f"{(time.time() - t0) / len(rows):.2f}s/q | ~{left:.0f} min left | GPU {mem:.1f} GB",
                      flush=True)
    print(f"done. results in {args.out}")


if __name__ == "__main__":
    main()
