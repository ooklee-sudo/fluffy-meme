"""Phase 3 (H3): does the TT-vs-LoRA gap at a matched budget change with how much capacity a task demands?

One task instance per run: synthetic fact injection with N facts (--task facts --n-facts N --task-seed S) or
math (--task math). Adapters go on q, v, up and down projections. For each adapter config, train with early
stopping on dev, then score eval: response NLL, relative gain, and for facts exact-match accuracy (every
answer token is the model's top prediction). One JSON per task instance goes to --out.

Pilot (exploratory) usage:
  python phase3.py --task facts --n-facts 500 --task-seed 0
  python phase3.py --task facts --n-facts 2000 --task-seed 0
  python phase3.py --task facts --n-facts 8000 --task-seed 0
  python phase3.py --task math --n-math 5000
  python phase3.py --tiny                                   # CPU smoke test (random tiny model)
"""
import argparse
import json
import math
import os
import time

import torch
import torch.nn.functional as F

from adapters import add_slots, n_trainable, parse_config, set_method
from data_tasks import encode, facts_task, math_task
from phase1 import collate, evaluate
from phase2 import train

PILOT_CONFIGS = "lora:1,lora:16,tt:7,tt:31"


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--task", default="facts", choices=["facts", "math"])
    a.add_argument("--n-facts", type=int, default=1000)
    a.add_argument("--n-math", type=int, default=5000)
    a.add_argument("--task-seed", type=int, default=0)
    a.add_argument("--configs", default=PILOT_CONFIGS)
    a.add_argument("--lrs", default="tt=1e-3,lora=3e-3,vera=3e-2", help="Phase 2 choices until Phase 3 tuning")
    a.add_argument("--epochs", type=float, default=None, help="default: 8 for facts, 1 for math")
    a.add_argument("--steps", type=int, default=None, help="overrides --epochs")
    a.add_argument("--max-steps", type=int, default=6000)
    a.add_argument("--bs", type=int, default=None, help="default: 32 for facts, 4 for math")
    a.add_argument("--max-len", type=int, default=None, help="default: 64 for facts, 512 for math")
    a.add_argument("--targets", default="q_proj,v_proj,up_proj,down_proj")
    a.add_argument("--seed", type=int, default=0, help="training seed")
    a.add_argument("--d", type=int, default=4)
    a.add_argument("--dtype", default="bf16", choices=["bf16", "fp32"])
    a.add_argument("--no-ckpt", action="store_true")
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--out", default=None)
    args = a.parse_args()
    facts = args.task == "facts"
    args.epochs = args.epochs if args.epochs is not None else (8 if facts else 1)
    args.bs = args.bs or (32 if facts else 4)
    args.max_len = args.max_len or (64 if facts else 512)
    if args.tiny:
        args.n_facts, args.dtype, args.max_steps = min(args.n_facts, 100), "fp32", 60
        if args.configs == PILOT_CONFIGS:
            args.configs = "lora:1,lora:4,tt:2,tt:4"
        args.lrs = "tt=1e-2,lora=1e-2,vera=3e-2"
    args.out = args.out or ("results/phase3_tiny" if args.tiny else "results/phase3_pilot")
    return args


def load(args, device):
    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig, LlamaForCausalLM

    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B" if args.tiny else args.model)
    if args.tiny:
        torch.manual_seed(0)
        cfg = LlamaConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                          num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=512)
        model = LlamaForCausalLM(cfg).to(device)
    else:
        dtype = torch.bfloat16 if args.dtype == "bf16" else torch.float32
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device)
        if not args.no_ckpt:
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    return model, tok, pad


@torch.no_grad()
def exact_match(model, data, args, pad, device):
    """Share of examples whose every response token is the model's argmax prediction (teacher forcing)."""
    model.eval()
    hit = 0
    for i in range(0, len(data), args.bs):
        ids, att, lab = collate(data[i: i + args.bs], pad, args.max_len, device)
        pred = model(input_ids=ids, attention_mask=att).logits[:, :-1].argmax(-1)
        tgt = lab[:, 1:]
        m = tgt != -100
        ok = ((pred == tgt) | ~m).all(1) & m.any(1)
        hit += int(ok.sum())
    return hit / max(len(data), 1)


def main():
    args = get_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    name = f"facts_n{args.n_facts}_s{args.task_seed}" if args.task == "facts" else f"math_n{args.n_math}_s{args.task_seed}"
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"{name}_seed{args.seed}.json")
    if os.path.exists(path):
        raise SystemExit(f"{path} exists; delete it to rerun")

    if args.task == "facts":
        tr_t, dv_t, ev_t = facts_task(args.n_facts, args.task_seed)
    else:
        tr_t, dv_t, ev_t = math_task(args.n_math, args.task_seed)
    model, tok, pad = load(args, device)
    tr, dv, ev = (encode(x, tok, args.max_len) for x in (tr_t, dv_t, ev_t))
    steps = args.steps or min(args.max_steps, math.ceil(args.epochs * len(tr) / args.bs))
    args.steps, args.eval_every = steps, max(25, steps // 10)
    slots = add_slots(model, targets=tuple(args.targets.split(",")), d=args.d)
    configs = [parse_config(c) for c in args.configs.split(",")]
    lrs = {m: float(v) for m, v in (x.split("=") for x in args.lrs.split(","))}
    print(f"{name}: train {len(tr)}, dev {len(dv)}, eval {len(ev)}; {steps} steps, bs {args.bs}, max len {args.max_len}")
    print(f"device={device}  adapted modules={len(slots)}  configs {args.configs}  lrs {lrs}")

    set_method(slots, "none", 0)
    nll_none = evaluate(model, ev, args, pad, device)
    acc_none = exact_match(model, ev, args, pad, device) if args.task == "facts" else None
    print(f"  no adapter: nll={nll_none:.4f}" + (f" acc={acc_none:.3f}" if acc_none is not None else ""))
    runs = []
    for method, r in configs:
        params = set_method(slots, method, r, seed=args.seed)
        ts = time.time()
        dev_best, best_step = train(model, slots, params, tr, dv, lrs[method], args, pad, device, args.seed)
        nll = evaluate(model, ev, args, pad, device)
        acc = exact_match(model, ev, args, pad, device) if args.task == "facts" else None
        n = n_trainable(slots)
        runs.append(dict(config=f"{method}:{r}", method=method, r=r, lr=lrs[method], params=n, nll=nll,
                         gain=nll_none - nll, rel_gain=(nll_none - nll) / nll_none, acc=acc, dev_best=dev_best,
                         best_step=best_step, seconds=time.time() - ts))
        print(f"    {method}:{r:<4} params={n:>11,} nll={nll:.4f} rel gain={runs[-1]['rel_gain']:+.4f}"
              + (f" acc={acc:.3f}" if acc is not None else "") + f"  best step {best_step}/{steps}"
              f"  ({runs[-1]['seconds'] / 60:.1f} min)")
    set_method(slots, "none", 0)
    with open(path, "w") as f:
        json.dump(dict(task=args.task, name=name, n_facts=args.n_facts if args.task == "facts" else None,
                       n_train=len(tr), steps=steps, nll_none=nll_none, acc_none=acc_none, runs=runs,
                       config=vars(args)), f, indent=1)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
