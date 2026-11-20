"""Run bench_hf for several quantization modes of one model, each in a fresh process (frees GPU memory).

  python -m quant_cost.sweep_hf --model Qwen/Qwen2.5-3B-Instruct --quants fp16,int8,nf4,fp4 --params-b 3 --n 100

Anything after `--` goes to quant_cost.bench_hf. Finished modes are skipped on rerun.
Rough weight sizes (GiB) for planning an 8 GB GPU: 3B fp16 ~6.2, int8 ~3.5, nf4 ~2.2; 7B nf4 ~5.0 (7B fp16
and int8 do not fit with KV cache and activations); 14B nf4 ~9 (does not fit).
"""
import argparse
import os
import re
import subprocess
import sys


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--quants", default="fp16,int8,nf4,fp4")
    ap.add_argument("--params-b", type=float)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out-dir", default="results/quant_cost")
    a = ap.parse_args(argv)
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", a.model.split("/")[-1]).lower()
    for q in a.quants.split(","):
        label = f"{base}-{q}"
        if os.path.exists(os.path.join(a.out_dir, label + ".json")):
            print(f"skip {label} (done)")
            continue
        cmd = [sys.executable, "-m", "quant_cost.bench_hf", "--model", a.model, "--quant", q, "--n", str(a.n),
               "--out-dir", a.out_dir] + (["--params-b", str(a.params_b)] if a.params_b else []) + extra
        print("===", label)
        r = subprocess.run(cmd)
        if r.returncode != 0:  # e.g. out of memory: keep going with the other modes
            print(f"!! {label} failed (exit {r.returncode}); continuing")


if __name__ == "__main__":
    main()
