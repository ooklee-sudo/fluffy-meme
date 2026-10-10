"""Where does ACT's compute time go, and why does it grow faster than retraining with model size?

Runs act_llama.act_transfer on untrained (zero-initialised) LoRA adapters for a Pythia source/target pair and
times the pieces:  forward passes that capture module inputs, the linear solves (torch.linalg.solve), and the
remainder (Gram-matrix accumulation, validation error, bookkeeping).  Timing does not depend on the adapter values.

Usage:  python profile_act.py EleutherAI/pythia-160m [--src-rev step73000 --tgt-rev step143000] [--out results/profile_act_160m.json]
"""
import argparse
import json
import time
from types import SimpleNamespace

import torch

import act_llama as al


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--src-rev", default="step73000")
    ap.add_argument("--tgt-rev", default="step143000")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.threads:
        torch.set_num_threads(a.threads)

    args = SimpleNamespace(
        source=a.model, target=a.model, source_revision=a.src_rev, target_revision=a.tgt_rev,
        dataset="openai/gsm8k", dataset_config="main", eval_split="test",
        prompt_template="Question: {question}\nAnswer:", response_field="answer",
        n_train=500, n_eval=200, n_cal=128, max_len=256, rank=8, lora_alpha=16, target_modules=["auto"],
        bs=4, seed=0, calib_with_response=False, tiny=False)
    device = torch.device("cpu")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model, revision=a.src_rev)
    tok.pad_token = tok.pad_token or tok.eos_token
    src = al.load_model(a.model, a.src_rev, device, torch.float32)
    tgt = al.load_model(a.model, a.tgt_rev, device, torch.float32)
    _, _, calib = al.load_examples(args, tok)
    src_pm, tgt_pm = al.add_lora(src, args), al.add_lora(tgt, args)

    cfg = src.config
    acc = {"capture": 0.0, "solve": 0.0, "n_solve": 0, "solve_by_d": {}}
    orig_capture, orig_solve = al.capture, torch.linalg.solve

    def timed_capture(*x, **k):
        t0 = time.time()
        out = orig_capture(*x, **k)
        acc["capture"] += time.time() - t0
        return out

    def timed_solve(A, B, *x, **k):
        t0 = time.time()
        out = orig_solve(A, B, *x, **k)
        dt = time.time() - t0
        d = int(A.shape[-1])
        acc["solve"] += dt
        acc["n_solve"] += 1
        e = acc["solve_by_d"].setdefault(d, [0, 0.0])
        e[0] += 1
        e[1] += dt
        return out

    al.capture, torch.linalg.solve = timed_capture, timed_solve
    t0 = time.time()
    al.act_transfer(src_pm, tgt_pm, calib, args, device, tok.pad_token_id)
    total = time.time() - t0
    al.capture, torch.linalg.solve = orig_capture, orig_solve

    res = dict(model=a.model, n_layers=cfg.num_hidden_layers, hidden=cfg.hidden_size,
               d_ff=getattr(cfg, "intermediate_size", None), total_s=total,
               capture_s=acc["capture"], solve_s=acc["solve"], n_solve=acc["n_solve"],
               other_s=total - acc["capture"] - acc["solve"],
               solve_by_d={str(k): {"n": v[0], "seconds": v[1]} for k, v in acc["solve_by_d"].items()},
               threads=torch.get_num_threads())
    print(json.dumps(res, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)


if __name__ == "__main__":
    main()
