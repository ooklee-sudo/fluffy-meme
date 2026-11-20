"""Measure ONE model with PyTorch + Hugging Face transformers (+ bitsandbytes quantization).

Windows-friendly alternative to bench.py (llama.cpp): everything installs with pip.
Writes the SAME result schema as bench.py, so analyze.py works on both. Results carry `backend`; do not mix
backends in one latency/energy comparison (bitsandbytes and llama.cpp have different kernels and speeds).

  python -m quant_cost.bench_hf --model Qwen/Qwen2.5-3B-Instruct --quant nf4 --params-b 3 --n 100

--quant: fp16 | bf16 | fp32 (no quantization), int8 (LLM.int8), nf4, fp4 (4-bit, bitsandbytes; needs a CUDA GPU).
A pre-quantized repo (GPTQ/AWQ) also works if its backend is installed; pass --quant-label to name it.
"""
import argparse
import json
import os
import re
import statistics
import time

from .bench import run_task
from .power import gpu_info, measure_idle
from .tasks import build_tasks

SYSTEM = "You are a precise assistant. Follow the output format exactly."
DTYPES = {"fp16": "float16", "bf16": "bfloat16", "fp32": "float32"}


def _dtype_key():
    """transformers >= 4.56 renamed `torch_dtype` to `dtype`; support both."""
    import transformers
    v = tuple(int(x) for x in re.findall(r"\d+", transformers.__version__)[:2])
    return "dtype" if v >= (4, 56) else "torch_dtype"


DTYPE_KEY = None


def nominal_bits(quant, double_quant):
    if quant in ("fp16", "bf16"):
        return 16.0
    if quant == "fp32":
        return 32.0
    if quant == "int8":
        return 8.0
    if quant in ("nf4", "fp4"):  # 4 bit + per-block (64) scale: 0.5 bit, or ~0.13 bit with double quantization
        return 4.13 if double_quant else 4.5
    return None


def load(args):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA is not available to PyTorch. Install a CUDA build of torch, or use --device cpu.")
    global DTYPE_KEY
    DTYPE_KEY = _dtype_key()
    tok = AutoTokenizer.from_pretrained(args.model)
    kw = {"low_cpu_mem_usage": True}
    q = args.quant
    if q in ("int8", "nf4", "fp4"):
        if args.device != "cuda":
            raise SystemExit(f"--quant {q} needs a CUDA GPU (bitsandbytes).")
        if q == "int8":
            kw["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        else:
            kw["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type=q, bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=args.double_quant)
        kw[DTYPE_KEY] = torch.float16
    elif q in DTYPES:
        kw[DTYPE_KEY] = getattr(torch, DTYPES[q])
    else:
        raise SystemExit(f"unknown --quant {q!r}")
    kw["device_map"] = {"": 0} if args.device == "cuda" else {"": "cpu"}
    model = AutoModelForCausalLM.from_pretrained(args.model, **kw).eval()
    return torch, tok, model


def make_chat_fn(torch, tok, model, device):
    dev = next(model.parameters()).device

    def chat_fn(prompt, max_tokens):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
        enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
        enc = {k: v.to(dev) for k, v in enc.items()}
        n_in = enc["input_ids"].shape[1]
        if device == "cuda":
            torch.cuda.synchronize()
        t = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(**enc, max_new_tokens=max_tokens, do_sample=False, temperature=None, top_p=None,
                                 top_k=None, pad_token_id=tok.pad_token_id or tok.eos_token_id)
        if device == "cuda":
            torch.cuda.synchronize()
        dt = time.perf_counter() - t
        gen = out[0, n_in:]
        return tok.decode(gen, skip_special_tokens=True), n_in, int(gen.shape[0]), dt

    return chat_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="HF repo id or local folder, e.g. Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--quant", default="nf4", help="fp16|bf16|fp32|int8|nf4|fp4")
    ap.add_argument("--quant-label", help="name for a pre-quantized repo (GPTQ/AWQ); overrides --quant in labels")
    ap.add_argument("--double-quant", action="store_true", help="bitsandbytes nested quantization for nf4/fp4")
    ap.add_argument("--label")
    ap.add_argument("--params-b", type=float)
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    ap.add_argument("--tasks", default="ticket,extract,arith")
    ap.add_argument("--task-file", action="append", default=[])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gpu-index", type=int, default=0)
    ap.add_argument("--assumed-cpu-watts", type=float, default=15.0)
    ap.add_argument("--wall-watts", type=float)
    ap.add_argument("--wall-idle-watts", type=float)
    ap.add_argument("--idle-s", type=float, default=5.0)
    ap.add_argument("--out-dir", default="results/quant_cost")
    args = ap.parse_args()

    qlabel = args.quant_label or args.quant
    label = args.label or re.sub(r"[^A-Za-z0-9._-]+", "-", args.model.split("/")[-1]).lower() + "-" + qlabel
    idle = measure_idle(args.idle_s, gpu_index=args.gpu_index)
    t0 = time.perf_counter()
    torch, tok, model = load(args)
    load_s = time.perf_counter() - t0
    footprint_gib = model.get_memory_footprint() / 2**30
    print(f"[{label}] loaded in {load_s:.1f}s, weights {footprint_gib:.2f} GiB, idle={idle}")

    chat_fn = make_chat_fn(torch, tok, model, args.device)
    chat_fn("Say OK.", 4)  # warm-up

    tasks = build_tasks([t for t in args.tasks.split(",") if t], args.n, args.seed, args.task_file)
    res = {"meta": {"label": label, "kind": "local", "backend": "transformers", "model": args.model,
                    "quant": qlabel, "nominal_bits": nominal_bits(args.quant, args.double_quant),
                    "params_b": args.params_b, "file_gib": footprint_gib, "load_s": load_s,
                    "device": args.device, "idle": idle, "gpu": gpu_info(args.gpu_index),
                    "torch": torch.__version__, "date": time.strftime("%Y-%m-%d %H:%M:%S")},
           "tasks": {}, "records": {}}
    for task in tasks:
        if args.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        summ, recs = run_task(chat_fn, task, args, idle, label)
        if args.device == "cuda":
            summ["torch_peak_alloc_mib"] = torch.cuda.max_memory_allocated() / 2**20
            summ["torch_peak_reserved_mib"] = torch.cuda.max_memory_reserved() / 2**20
        res["tasks"][task["name"]], res["records"][task["name"]] = summ, recs

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
