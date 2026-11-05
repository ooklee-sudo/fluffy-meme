"""Make a "model update" by LoRA fine-tuning (QLoRA on a GPU).

The adapter is trained on a different task than the QA questions used for probing
(default: GSM8K math), which mimics a routine domain fine-tune. Afterwards compare the
model with and without the adapter:

  python finetune_lora.py --model Qwen/Qwen3-4B --out adapters/qwen3-4b_gsm8k
  python generate.py --model Qwen/Qwen3-4B --prompt fewshot --n 2000 --out runs/qwen3-4b_fs
  python generate.py --model Qwen/Qwen3-4B --adapter adapters/qwen3-4b_gsm8k --prompt fewshot \
      --n 2000 --out runs/qwen3-4b_gsm8k_fs
  python transfer.py runs/qwen3-4b_fs runs/qwen3-4b_gsm8k_fs --out results/lora_gsm8k

Memory: Qwen3-4B in 4-bit with rank-16 LoRA, batch 4 x 384 tokens fits in 8 GB.
"""

import argparse
import math
import os
import random
import time

import torch

from common import load_model


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="Qwen/Qwen3-4B")
    p.add_argument("--quant", default="4bit", choices=["4bit", "8bit", "none"])
    p.add_argument("--out", required=True)
    p.add_argument("--n-train", type=int, default=2000)
    p.add_argument("--steps", type=int, default=500)
    p.add_argument("--bs", type=int, default=4)
    p.add_argument("--grad-accum", type=int, default=2)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--max-len", type=int, default=384)
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def load_gsm8k(tok, n, max_len, seed):
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split="train").shuffle(seed=seed).select(range(n))
    examples = []
    for r in ds:
        prompt = f"Question: {r['question']}\nAnswer:"
        response = " " + r["answer"].replace("####", "The answer is") + tok.eos_token
        p_ids = tok(prompt, add_special_tokens=False).input_ids
        r_ids = tok(response, add_special_tokens=False).input_ids
        ids = (p_ids + r_ids)[:max_len]
        labels = ([-100] * len(p_ids) + r_ids)[:max_len]  # loss on the answer only
        examples.append((ids, labels))
    return examples


def batches(examples, bs, pad_id, rng):
    while True:
        rng.shuffle(examples)
        for i in range(0, len(examples) - bs + 1, bs):
            chunk = examples[i:i + bs]
            L = max(len(ids) for ids, _ in chunk)
            ids = torch.full((bs, L), pad_id)
            labels = torch.full((bs, L), -100)
            mask = torch.zeros((bs, L), dtype=torch.long)
            for j, (x, y) in enumerate(chunk):
                ids[j, :len(x)], labels[j, :len(y)], mask[j, :len(x)] = torch.tensor(x), torch.tensor(y), 1
            yield ids, labels, mask


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    model, tok = load_model(args.model, args.quant)
    if torch.cuda.is_available() and args.quant != "none":
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()

    examples = load_gsm8k(tok, args.n_train, args.max_len, args.seed)
    it = batches(examples, args.bs, tok.pad_token_id, random.Random(args.seed))
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / 20) * 0.5 * (1 + math.cos(math.pi * s / args.steps)))

    model.train()
    t0, running = time.time(), 0.0
    for step in range(args.steps):
        for _ in range(args.grad_accum):
            ids, labels, mask = (x.to(model.device) for x in next(it))
            loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss / args.grad_accum
            loss.backward()
            running += loss.item()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        if (step + 1) % 20 == 0 or step == args.steps - 1:
            mem = torch.cuda.max_memory_allocated() / 2**30 if torch.cuda.is_available() else 0
            print(f"step {step + 1}/{args.steps} | loss {running / 20:.3f} | "
                  f"{(time.time() - t0) / (step + 1):.2f}s/step | peak GPU mem {mem:.1f} GB")
            running = 0.0

    os.makedirs(args.out, exist_ok=True)
    model.save_pretrained(args.out)
    print(f"adapter saved to {args.out}")


if __name__ == "__main__":
    main()
