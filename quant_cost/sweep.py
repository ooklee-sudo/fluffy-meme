"""Download a GGUF quantization ladder from Hugging Face and benchmark each rung.

  python -m quant_cost.sweep --repo Qwen/Qwen2.5-3B-Instruct-GGUF --prefix qwen2.5-3b-instruct \
      --quants q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k,q8_0 --params-b 3 --n 100

Finished rungs are skipped on rerun. Anything after `--` goes to quant_cost.bench.
"""
import argparse
import os
import re
import subprocess
import sys


def pick_files(repo_files, prefix, q):
    """Single file `<prefix>-<q>.gguf` or all shards `<prefix>-<q>-0000i-of-0000n.gguf` (sorted)."""
    single = f"{prefix}-{q}.gguf"
    if single in repo_files:
        return [single]
    pat = re.compile(rf"^{re.escape(prefix)}-{re.escape(q)}-(\d+)-of-(\d+)\.gguf$")
    shards = sorted(f for f in repo_files if pat.match(f))
    if shards and len(shards) == int(pat.match(shards[0]).group(2)):
        return shards
    return []


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

    from huggingface_hub import hf_hub_download, list_repo_files

    repo_files = set(list_repo_files(a.repo))
    os.makedirs(a.models_dir, exist_ok=True)
    for q in a.quants.split(","):
        label = f"{a.prefix}-{q}"
        if os.path.exists(os.path.join(a.out_dir, label + ".json")):
            print(f"skip {label} (done)")
            continue
        files = pick_files(repo_files, a.prefix, q)
        if not files:
            print(f"skip {label}: no such file in {a.repo}")
            continue
        print(f"=== {label} ({len(files)} file(s))")
        paths = [hf_hub_download(a.repo, f, local_dir=a.models_dir) for f in files]
        path = paths[0]  # llama.cpp loads the remaining shards from the same directory
        cmd = [sys.executable, "-m", "quant_cost.bench", "--model", path, "--label", label, "--n", str(a.n),
               "--out-dir", a.out_dir] + (["--params-b", str(a.params_b)] if a.params_b else []) + extra
        subprocess.run(cmd, check=True)
        if not a.keep:
            for p_ in paths:
                os.remove(p_)


if __name__ == "__main__":
    main()
