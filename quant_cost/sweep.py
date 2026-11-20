"""Download a GGUF quantization ladder from Hugging Face and benchmark each rung.

  python -m quant_cost.sweep --repo Qwen/Qwen2.5-3B-Instruct-GGUF --prefix qwen2.5-3b-instruct \
      --quants q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k,q8_0 --params-b 3 --n 100

Finished rungs are skipped on rerun. Anything after `--` goes to quant_cost.bench.
"""
import argparse
import os
import subprocess
import sys


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="HF repo with GGUF files, e.g. Qwen/Qwen2.5-3B-Instruct-GGUF")
    ap.add_argument("--prefix", required=True, help="file prefix, e.g. qwen2.5-3b-instruct")
    ap.add_argument("--quants", default="q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k,q8_0")
    ap.add_argument("--params-b", type=float)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--out-dir", default="results/quant_cost")
    ap.add_argument("--keep", action="store_true", help="keep downloaded files (default: delete after each rung)")
    a = ap.parse_args(argv)

    from huggingface_hub import hf_hub_download

    os.makedirs(a.models_dir, exist_ok=True)
    for q in a.quants.split(","):
        fname = f"{a.prefix}-{q}.gguf"
        label = f"{a.prefix}-{q}"
        if os.path.exists(os.path.join(a.out_dir, label + ".json")):
            print(f"skip {label} (done)")
            continue
        print(f"=== {label}")
        path = hf_hub_download(a.repo, fname, local_dir=a.models_dir)
        cmd = [sys.executable, "-m", "quant_cost.bench", "--model", path, "--label", label, "--n", str(a.n),
               "--out-dir", a.out_dir] + (["--params-b", str(a.params_b)] if a.params_b else []) + extra
        subprocess.run(cmd, check=True)
        if not a.keep:
            os.remove(path)


if __name__ == "__main__":
    main()
