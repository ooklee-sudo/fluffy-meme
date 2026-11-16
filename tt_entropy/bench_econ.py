"""Economics study, experiment E2: measured serving cost per request for each personalization method.

A request = a customer prompt (~30 tokens) plus generation of a reply (--new-tokens, greedy). Methods:
  base        no personalization
  context-N   N extra context tokens in front of the prompt (RAG-8 / few-shot-8 add about 450-480)
  lora:1      LoRA rank 1 on q and v, unmerged (the multi-tenant serving case)
  vera:256    VeRA r=256 on q and v, unmerged
Timed per batch with CUDA synchronization; reports milliseconds per request and requests per GPU-hour.
Also times training of one LoRA r=1 adapter per tenant from the Phase 2 results if --phase2 is given.

Usage: python bench_econ.py [--bs 8,32] [--context 0,450] [--new-tokens 32] [--iters 5]
"""
import argparse
import glob
import json
import os
import time

import numpy as np
import torch

from adapters import add_slots, parse_config, set_method


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--bs", default="8,32")
    a.add_argument("--prompt-tokens", type=int, default=30)
    a.add_argument("--context", default="0,450")
    a.add_argument("--adapters", default="lora:1,vera:256")
    a.add_argument("--new-tokens", type=int, default=32)
    a.add_argument("--iters", type=int, default=5)
    a.add_argument("--phase2", default="results/phase2_s0")
    a.add_argument("--out", default="results/econ_e2.json")
    a.add_argument("--tiny", action="store_true")
    args = a.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModelForCausalLM, LlamaConfig, LlamaForCausalLM

    if args.tiny:
        torch.manual_seed(0)
        model = LlamaForCausalLM(LlamaConfig(vocab_size=1000, hidden_size=64, intermediate_size=128,
                                             num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                                             max_position_embeddings=2048)).to(device)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(device)
    model.eval()
    model.config.use_cache = True
    slots = add_slots(model, targets=("q_proj", "v_proj"))
    vocab = model.config.vocab_size
    sync = torch.cuda.synchronize if device == "cuda" else (lambda: None)

    def timed(bs, ctx):
        ids = torch.randint(100, vocab - 100, (bs, ctx + args.prompt_tokens), device=device)
        att = torch.ones_like(ids)
        kw = dict(max_new_tokens=args.new_tokens, min_new_tokens=args.new_tokens, do_sample=False,
                  pad_token_id=0, attention_mask=att)
        with torch.no_grad():
            model.generate(ids, **kw)  # warm-up
            sync()
            t = time.perf_counter()
            for _ in range(args.iters):
                model.generate(ids, **kw)
            sync()
        return (time.perf_counter() - t) / args.iters / bs * 1000  # ms per request

    rows = []
    conds = [("base", "none:0", c) for c in map(int, args.context.split(","))]
    conds += [(c, c, 0) for c in args.adapters.split(",")]
    print(f"device={device}  prompt {args.prompt_tokens} tok, reply {args.new_tokens} tok, mean of {args.iters}")
    print(f"{'method':<14}{'context':>8}" + "".join(f"{'ms/req bs ' + b:>16}" for b in args.bs.split(","))
          + f"{'req per GPU-hour (largest bs)':>32}")
    for label, cfg, ctx in conds:
        m, r = parse_config(cfg)
        set_method(slots, m, r)
        for p in (p for s in slots.values() if s.delta is not None for p in s.delta.parameters()):
            torch.nn.init.normal_(p, std=0.01)
        ms = [timed(int(b), ctx) for b in args.bs.split(",")]
        name = f"context-{ctx}" if label == "base" and ctx else label
        rows.append(dict(method=name, context=ctx, ms_per_request={b: v for b, v in zip(args.bs.split(","), ms)},
                         requests_per_gpu_hour=3.6e6 / ms[-1]))
        print(f"{name:<14}{ctx:>8}" + "".join(f"{v:>16.2f}" for v in ms) + f"{3.6e6 / ms[-1]:>32,.0f}")
    set_method(slots, "none", 0)

    train_s = None
    files = glob.glob(os.path.join(args.phase2, "*.json"))
    if files:
        secs = [x["seconds"] for f in files for x in json.load(open(f))["runs"] if x["config"] == "lora:1"]
        train_s = float(np.median(secs))
        print(f"\ntraining one LoRA r=1 adapter (Phase 2 median, {len(secs)} runs, incl. dev checks): {train_s:.0f} s")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(dict(device=torch.cuda.get_device_name(0) if device == "cuda" else "cpu", rows=rows,
                       lora1_train_seconds=train_s, config=vars(args)), f, indent=1)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
