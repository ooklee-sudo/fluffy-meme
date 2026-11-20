"""Measure accuracy, latency, throughput, memory and energy of ONE local GGUF model (llama.cpp).

  python -m quant_cost.bench --model models/qwen2.5-3b-instruct-q4_k_m.gguf --n 100

Output: results/quant_cost/<label>.json  (summary per task + every per-item record).
Install a CUDA build for GPU offload:  CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
"""
import argparse
import json
import math
import os
import re
import statistics
import time

from .power import PowerMeter, gpu_info, measure_idle
from .tasks import build_tasks

SYSTEM = "You are a precise assistant. Follow the output format exactly."


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def model_bytes(path):
    """File size; for sharded GGUF (`...-00001-of-0000N.gguf`) the sum of all shards."""
    m = re.match(r"^(.*)-\d+-of-(\d+)\.gguf$", path)
    if m:
        import glob
        return sum(os.path.getsize(f) for f in glob.glob(f"{m.group(1)}-*-of-{m.group(2)}.gguf"))
    return os.path.getsize(path)


def quant_label(path):
    m = re.search(r"(q\d(?:_[0-9a-z]+)*|f16|fp16|bf16)", os.path.basename(path).lower())
    return m.group(1) if m else "unknown"


def approx_bits(q):
    """Nominal bits/weight of common llama.cpp quants (for plotting only)."""
    table = {"q2_k": 2.6, "q3_k_m": 3.9, "q4_0": 4.5, "q4_k_m": 4.9, "q5_0": 5.5, "q5_k_m": 5.7,
             "q6_k": 6.6, "q8_0": 8.5, "f16": 16.0, "fp16": 16.0, "bf16": 16.0}
    return table.get(q)


def chat(llm, prompt, max_tokens):
    t = time.perf_counter()
    r = llm.create_chat_completion(
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=0.0, seed=0)
    dt = time.perf_counter() - t
    u = r["usage"]
    return r["choices"][0]["message"]["content"], u["prompt_tokens"], u["completion_tokens"], dt


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def run_task(llm, task, args, idle, hw_label):
    items = task["items"]
    meter = PowerMeter(gpu_index=args.gpu_index).start()
    recs = []
    for it in items:
        out, pt, ct, dt = chat(llm, it["prompt"], task["max_tokens"])
        s = task["score"](out, it)
        recs.append({"score": s, "correct": s == 1.0, "prompt_tokens": pt, "completion_tokens": ct,
                     "latency_s": dt, "output": out[:300]})
    pw = meter.stop()

    # time-to-first-token: re-run a few prompts with max_tokens=1 (prefill cost)
    ttft = [chat(llm, it["prompt"], 1)[3] for it in items[:min(5, len(items))]]

    dur = pw["duration_s"]
    n = len(items)
    # energy: GPU board + CPU package (RAPL) if measured; else assumed wattage; or wall-plug override
    gpu_idle = idle.get("gpu_idle_w") or 0.0
    cpu_idle = idle.get("cpu_idle_w") or 0.0
    if args.wall_watts:
        total_j, how = args.wall_watts * dur, "wall_watts_override"
        marginal_j = max(0.0, args.wall_watts - (args.wall_idle_watts or 0.0)) * dur
    else:
        g = pw["gpu_energy_j"]
        c = pw["cpu_energy_j"] if pw["cpu_energy_j"] is not None else args.assumed_cpu_watts * dur
        total_j = (g or 0.0) + c
        marginal_j = max(0.0, (g or 0.0) - gpu_idle * dur) + max(0.0, c - cpu_idle * dur)
        how = ("gpu_smi" if g is not None else "no_gpu_meter") + ("+rapl" if pw["cpu_energy_j"] is not None
                                                                   else f"+assumed_cpu_{args.assumed_cpu_watts}W")
    ok = sum(r["correct"] for r in recs)
    lo, hi = wilson(ok, n)
    gen = sum(r["completion_tokens"] for r in recs)
    summ = {
        "n": n, "sensitivity": task["sensitivity"],
        "acc": ok / n, "acc_ci95": [lo, hi], "mean_score": statistics.mean(r["score"] for r in recs),
        "mean_prompt_tokens": statistics.mean(r["prompt_tokens"] for r in recs),
        "mean_completion_tokens": gen / n,
        "latency_mean_s": statistics.mean(r["latency_s"] for r in recs),
        "latency_p95_s": pct([r["latency_s"] for r in recs], 0.95),
        "ttft_mean_s": statistics.mean(ttft) if ttft else None,
        "gen_tokens_per_s": gen / sum(r["latency_s"] for r in recs),
        "wall_s": dur, "energy_total_j_per_req": total_j / n, "energy_marginal_j_per_req": marginal_j / n,
        "energy_method": how, "gpu_avg_w": pw["gpu_avg_w"], "gpu_peak_mem_mib": pw["gpu_peak_mem_mib"],
    }
    print(f"  {task['name']:8s} acc={summ['acc']:.3f} [{lo:.2f},{hi:.2f}]  lat={summ['latency_mean_s']:.2f}s "
          f"tok/s={summ['gen_tokens_per_s']:.1f}  J/req={summ['energy_total_j_per_req']:.1f} ({how})")
    return summ, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="path to a .gguf file")
    ap.add_argument("--label", help="result name (default: file stem)")
    ap.add_argument("--params-b", type=float, help="model size in billions of params (metadata)")
    ap.add_argument("--tasks", default="ticket,extract,arith")
    ap.add_argument("--task-file", action="append", default=[], help="custom JSONL task (prompt/answer/pii)")
    ap.add_argument("--n", type=int, default=100, help="items per task")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-gpu-layers", type=int, default=-1, help="-1 = all layers on GPU, 0 = CPU only")
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--gpu-index", type=int, default=0)
    ap.add_argument("--assumed-cpu-watts", type=float, default=15.0,
                    help="CPU+rest power if RAPL is unavailable (e.g. Windows)")
    ap.add_argument("--wall-watts", type=float, help="average wall-plug power while running (overrides meters)")
    ap.add_argument("--wall-idle-watts", type=float, help="wall-plug idle power, to compute marginal energy")
    ap.add_argument("--idle-s", type=float, default=5.0)
    ap.add_argument("--out-dir", default="results/quant_cost")
    args = ap.parse_args()

    from llama_cpp import Llama

    label = args.label or os.path.splitext(os.path.basename(args.model))[0]
    q = quant_label(args.model)
    idle = measure_idle(args.idle_s, gpu_index=args.gpu_index)
    t0 = time.perf_counter()
    llm = Llama(model_path=args.model, n_gpu_layers=args.n_gpu_layers, n_ctx=args.n_ctx,
                n_threads=args.threads, verbose=False)
    load_s = time.perf_counter() - t0
    print(f"[{label}] quant={q} loaded in {load_s:.1f}s, file={model_bytes(args.model)/2**30:.2f} GiB, "
          f"idle={idle}")

    chat(llm, "Say OK.", 4)  # warm-up (kernel compile / cache)

    tasks = build_tasks([t for t in args.tasks.split(",") if t], args.n, args.seed, args.task_file)
    res = {"meta": {"label": label, "kind": "local", "model_file": os.path.basename(args.model), "quant": q,
                    "nominal_bits": approx_bits(q), "params_b": args.params_b,
                    "file_gib": model_bytes(args.model) / 2**30, "load_s": load_s,
                    "n_gpu_layers": args.n_gpu_layers, "n_ctx": args.n_ctx, "idle": idle, "gpu": gpu_info(args.gpu_index),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")},
           "tasks": {}, "records": {}}
    for task in tasks:
        res["tasks"][task["name"]], res["records"][task["name"]] = run_task(llm, task, args, idle, label)

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
