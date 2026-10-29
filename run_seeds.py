"""Repeat the Section 3.3 / Appendix B model-pair experiment over several seeds.

Each seed resamples the training and calibration rows and the training order (eval rows are fixed),
so the spread of (R_C, R_A, C_A/C_N) across seeds is the sampling noise of the measurement.
Runs sequentially on purpose: C_A/C_N is a wall-clock ratio and parallel jobs would distort it.

  python run_seeds.py --seeds 1 2 3 4        # seed 0 is the original single-seed run
  python run_seeds.py --only pythia --seeds 1
"""
import argparse
import os
import subprocess
import sys
import time

from run_pairs import PAIRS, slug

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--only", default="")
    ap.add_argument("--fp32", action="store_true", help="pass --fp32 to act_llama.py (GPU runs at CPU precision)")
    ap.add_argument("--outdir", default=os.path.join(HERE, "results", "seeds"))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for seed in a.seeds:
        for name, src, srev, tgt, trev in PAIRS:
            if a.only and a.only not in name:
                continue
            out = os.path.join(a.outdir, f"{slug(name)}_s{seed}.json")
            if os.path.exists(out):
                print(f"[skip] {name} seed {seed}")
                continue
            cmd = [sys.executable, os.path.join(HERE, "act_llama.py"), "--preset", "cpu", "--source", src,
                   "--target", tgt, "--pair-name", name, "--seed", str(seed), "--out", out]
            cmd += ["--fp32"] if a.fp32 else []
            cmd += ["--source-revision", srev] if srev else []
            cmd += ["--target-revision", trev] if trev else []
            t0 = time.time()
            r = subprocess.run(cmd)
            print(f"[{'done' if r.returncode == 0 else 'fail'}] {name} seed {seed} in {(time.time() - t0) / 60:.1f} min",
                  flush=True)


if __name__ == "__main__":
    main()
