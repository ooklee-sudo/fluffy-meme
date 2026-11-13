"""Forward-pass latency of each adapter, unmerged (the multi-tenant serving case), on random tokens.

The TT adapter here rebuilds dW from its cores on every forward, which is simple but not the fastest
possible contraction; LoRA and VeRA apply their low-rank factors directly. Merged into the base weights
(a dedicated deployment), all methods cost the same as the base model.

Usage: python bench.py [--configs ...] [--bs 1,8] [--len 256] [--iters 20]
"""
import argparse
import time

import torch

from adapters import add_slots, n_trainable, parse_config, set_method
from phase1 import load_model
from phase2 import MAIN_CONFIGS


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--configs", default="none:0," + MAIN_CONFIGS)
    a.add_argument("--bs", default="1,8")
    a.add_argument("--len", type=int, default=256)
    a.add_argument("--iters", type=int, default=20)
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--dtype", default="bf16")
    a.add_argument("--no-ckpt", action="store_true", default=True)
    args = a.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, _ = load_model(args, device)
    model.eval()
    slots = add_slots(model)
    vocab = model.config.vocab_size
    sync = torch.cuda.synchronize if device == "cuda" else (lambda: None)
    print(f"device={device}  seq len {args.len}  (ms per forward, mean of {args.iters})")
    print(f"{'config':<11}{'params':>11}" + "".join(f"{'bs ' + b:>10}" for b in args.bs.split(",")))
    for c in args.configs.split(","):
        m, r = parse_config(c)
        set_method(slots, m, r)
        for p in (p for s in slots.values() if s.delta is not None for p in s.delta.parameters()):
            torch.nn.init.normal_(p, std=0.01)  # non-zero update so nothing is skipped
        cells = []
        for b in (int(x) for x in args.bs.split(",")):
            ids = torch.randint(0, vocab, (b, args.len), device=device)
            with torch.no_grad():
                for _ in range(3):
                    model(input_ids=ids)
                sync()
                t = time.perf_counter()
                for _ in range(args.iters):
                    model(input_ids=ids)
                sync()
            cells.append((time.perf_counter() - t) / args.iters * 1000)
        print(f"{c:<11}{n_trainable(slots):>11,}" + "".join(f"{x:>10.1f}" for x in cells))


if __name__ == "__main__":
    main()
