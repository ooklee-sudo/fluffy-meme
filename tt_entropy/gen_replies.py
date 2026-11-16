"""H5 / H10 data (PREREGISTRATION_H5_H7.md): generate replies with each personalization method, plus the NLL
quality measures, for the judge to compare.

For each brand (same split as all earlier studies: data seed 0, 320 train, 40 dev, 80 eval):
  - NLL relative gain of LoRA r=1 (lr 3e-3), VeRA r=256 (lr 3e-2) and RAG-8 over no personalization
  - greedy replies (up to --new-tokens) to the first --n-gen evaluation messages from: no personalization,
    RAG-8, LoRA r=1, VeRA r=256
  - five training replies of the brand, chosen with a fixed seed, as style examples for the judge
One JSON per brand goes to --out; reruns skip finished brands. The judge runs separately (judge.py).

Usage:
  python gen_replies.py --tenants-file h5_brands.txt --out results/h5_gen
  python gen_replies.py --tiny                                   # CPU smoke test
"""
import argparse
import json
import os
import random
import re
import time

import torch

from adapters import add_slots, set_method
from data import PROMPT_TEMPLATE, encode_tenant, features, load_jsonl
from drift import rag_data
from phase1 import evaluate
from phase2 import train

METHODS = [("zero", None, None), ("rag-8", None, None), ("lora:1", "lora", 1), ("vera:256", "vera", 256)]
LRS = {"lora": 3e-3, "vera": 3e-2}


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--data", default="data/twcs_pairs.jsonl")
    a.add_argument("--tenants-file", default="h5_brands.txt")
    a.add_argument("--tenants", default="")
    a.add_argument("--n-train", type=int, default=320)
    a.add_argument("--n-dev", type=int, default=40)
    a.add_argument("--n-eval", type=int, default=80)
    a.add_argument("--n-gen", type=int, default=40)
    a.add_argument("--new-tokens", type=int, default=64)
    a.add_argument("--gen-bs", type=int, default=8)
    a.add_argument("--k", type=int, default=8)
    a.add_argument("--steps", type=int, default=300)
    a.add_argument("--eval-every", type=int, default=50)
    a.add_argument("--bs", type=int, default=4)
    a.add_argument("--max-len", type=int, default=256)
    a.add_argument("--demo-len", type=int, default=96)
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--out", default="results/h5_gen")
    args = a.parse_args()
    if args.tiny:
        args.steps, args.eval_every, args.n_gen, args.new_tokens = 6, 3, 4, 8
    return args


@torch.no_grad()
def generate(model, tok, prompts, args, device):
    """Greedy continuation of each token-id prompt, left-padded in batches; returns decoded replies."""
    model.eval()
    model.config.use_cache = True
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    out = []
    for i in range(0, len(prompts), args.gen_bs):
        batch = prompts[i: i + args.gen_bs]
        n = max(len(p) for p in batch)
        ids = torch.tensor([[pad] * (n - len(p)) + p for p in batch], device=device)
        att = torch.tensor([[0] * (n - len(p)) + [1] * len(p) for p in batch], device=device)
        gen = model.generate(input_ids=ids, attention_mask=att, max_new_tokens=args.new_tokens, do_sample=False,
                             pad_token_id=pad, eos_token_id=tok.eos_token_id)
        for row in gen[:, n:]:
            text = tok.decode(row, skip_special_tokens=True)
            out.append(text.split("\nCustomer:")[0].strip())
    model.config.use_cache = False
    return out


def main():
    args = get_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig, LlamaForCausalLM

    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B" if args.tiny else args.model)
    if args.tiny:
        torch.manual_seed(0)
        model = LlamaForCausalLM(LlamaConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128,
                                             num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                                             max_position_embeddings=2048)).to(device)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(device)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    slots = add_slots(model, targets=("q_proj", "v_proj"))
    ctx_args = argparse.Namespace(bs=args.bs, max_len=args.demo_len * args.k + args.max_len)

    raw = load_jsonl(args.data)
    if args.tenants:
        names = args.tenants.split(",")
    else:
        names = [l.strip() for l in open(args.tenants_file) if l.strip() and not l.startswith("#")]
    missing = [n for n in names if n not in raw]
    if missing:
        raise SystemExit(f"brands not in {args.data}: {missing}")
    os.makedirs(args.out, exist_ok=True)
    print(f"{len(names)} brands, device {device}, {args.n_gen} replies per method")

    for bi, name in enumerate(names):
        path = os.path.join(args.out, re.sub(r"[^\w.-]", "_", name) + ".json")
        if os.path.exists(path):
            print(f"[{bi + 1}/{len(names)}] {name}: done, skipping")
            continue
        t0 = time.time()
        pairs = list(raw[name])
        random.Random(0).shuffle(pairs)  # data seed 0: the same split as every earlier study
        tr, dv = pairs[: args.n_train], pairs[args.n_train: args.n_train + args.n_dev]
        ev = pairs[args.n_train + args.n_dev: args.n_train + args.n_dev + args.n_eval]
        tr_e, dv_e, ev_e = (encode_tenant(x, tok, args.max_len) for x in (tr, dv, ev))
        gen_items = ev[: args.n_gen]
        plain = [tok(PROMPT_TEMPLATE.format(prompt=p), add_special_tokens=True)["input_ids"][: args.max_len // 2]
                 for p, _ in gen_items]
        rag_prompts = [x for x, _ in rag_data(gen_items, tr, tok, args)]

        res = dict(brand=name, features=features(tr_e), nll={}, rel_gain={}, items=[])
        set_method(slots, "none", 0)
        res["nll"]["zero"] = evaluate(model, ev_e, args, pad, device)
        res["nll"]["rag-8"] = evaluate(model, rag_data(ev, tr, tok, args), ctx_args, pad, device)
        gens = {"zero": generate(model, tok, plain, args, device),
                "rag-8": generate(model, tok, rag_prompts, args, device)}
        for label, method, r in METHODS[2:]:
            params = set_method(slots, method, r, seed=args.seed)
            train(model, slots, params, tr_e, dv_e, LRS[method], args, pad, device, args.seed)
            res["nll"][label] = evaluate(model, ev_e, args, pad, device)
            gens[label] = generate(model, tok, plain, args, device)
        set_method(slots, "none", 0)
        z = res["nll"]["zero"]
        res["rel_gain"] = {m: (z - v) / z for m, v in res["nll"].items()}
        res["style_examples"] = [r for _, r in random.Random(1).sample(tr, 5)]
        for j, (p, r) in enumerate(gen_items):
            res["items"].append(dict(customer=p, gold=r, replies={m: gens[m][j] for m in gens}))
        res["seconds"] = time.time() - t0
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        g = res["rel_gain"]
        print(f"[{bi + 1}/{len(names)}] {name}: rel gain rag-8 {g['rag-8']:+.3f}, lora {g['lora:1']:+.3f}, "
              f"vera {g['vera:256']:+.3f}  ({res['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
