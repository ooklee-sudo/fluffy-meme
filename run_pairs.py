"""Run the Section 7.1 model-pair experiment on several open (non-gated) model pairs, then feed the
measured recovery rates and costs into the economic model.

Every pair shares a tokenizer (Appendix A.1, scenario S1):
  - Pythia-160M checkpoints: step N -> step 143000 (upgrades of increasing size = a drift series)
  - SmolLM2-360M  Base -> Instruct
  - Qwen2.5-0.5B  Base -> Instruct

Usage (CPU, a few hours in total; finished pairs are skipped on rerun):
  python run_pairs.py                 # all pairs, CPU preset
  python run_pairs.py --only pythia   # just the Pythia drift series
  python run_pairs.py --preset gpu    # full-size run on a GPU
  python run_pairs.py -- --steps 200  # anything after -- is passed to act_llama.py
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import time

PAIRS = [
    # name,                source,                          source rev,   target,                                target rev
    ("pythia-160m +10k",   "EleutherAI/pythia-160m",        "step133000", "EleutherAI/pythia-160m",              "step143000"),
    ("pythia-160m +30k",   "EleutherAI/pythia-160m",        "step113000", "EleutherAI/pythia-160m",              "step143000"),
    ("pythia-160m +70k",   "EleutherAI/pythia-160m",        "step73000",  "EleutherAI/pythia-160m",              "step143000"),
    ("pythia-160m +40k",   "EleutherAI/pythia-160m",        "step103000", "EleutherAI/pythia-160m",              "step143000"),
    ("pythia-160m +60k",   "EleutherAI/pythia-160m",        "step83000",  "EleutherAI/pythia-160m",              "step143000"),
    ("smollm2-360m instr", "HuggingFaceTB/SmolLM2-360M",    None,         "HuggingFaceTB/SmolLM2-360M-Instruct", None),
    ("qwen2.5-0.5b instr", "Qwen/Qwen2.5-0.5B",             None,         "Qwen/Qwen2.5-0.5B-Instruct",          None),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def slug(name):
    s = "".join(c if c.isalnum() else "_" for c in name)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def main():
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[: argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="run pairs whose name contains this text")
    ap.add_argument("--preset", choices=["cpu", "gpu"], default="cpu")
    ap.add_argument("--outdir", default=os.path.join(HERE, "results", "pairs"))
    ap.add_argument("--force", action="store_true", help="rerun pairs that already have results")
    a = ap.parse_args(argv)
    os.makedirs(a.outdir, exist_ok=True)

    done = []
    for name, src, srev, tgt, trev in PAIRS:
        if a.only and a.only not in name:
            continue
        out = os.path.join(a.outdir, slug(name) + ".json")
        if os.path.exists(out) and not a.force:
            print(f"[skip] {name}: {out} exists")
            done.append(out)
            continue
        cmd = [sys.executable, os.path.join(HERE, "act_llama.py"), "--source", src, "--target", tgt,
               "--pair-name", name, "--out", out]
        cmd += ["--preset", a.preset] if a.preset == "cpu" else []
        cmd += ["--source-revision", srev] if srev else []
        cmd += ["--target-revision", trev] if trev else []
        cmd += extra
        print(f"\n===== {name} =====\n" + " ".join(cmd), flush=True)
        t0 = time.time()
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"[fail] {name} (exit {r.returncode}); continuing with the next pair")
            continue
        print(f"[done] {name} in {(time.time() - t0) / 60:.1f} min")
        done.append(out)

    rows = [json.load(open(p)) for p in done]
    if not rows:
        sys.exit("no finished pairs")
    print(f"\n{'pair':<22} {'R_C':>7} {'R_A':>7} {'ACT>copy':>9} {'C_A/C_N':>8}")
    for r in rows:
        rec = r["recovery"][0]
        print(f"{r['pair']:<22} {rec['R_C']:7.3f} {rec['R_A']:7.3f} {str(rec['R_A'] > rec['R_C']):>9} "
              f"{r['C_A_over_C_N']:8.3f}")
    summary = {"recovery": [r["recovery"][0] for r in rows],
               "C_A_over_C_N": statistics.median(r["C_A_over_C_N"] for r in rows),
               "pairs": {r["pair"]: {k: r[k] for k in ("none", "retrain", "copy", "act",
                                                       "time_retrain_s", "time_act_s", "C_A_over_C_N")}
                         for r in rows}}
    path = os.path.join(HERE, "results", "pairs_summary.json")
    json.dump(summary, open(path, "w"), indent=2, default=float)
    print(f"\nsaved {path}\n\n===== economic model with measured (R_C, R_A, C_A/C_N) =====", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, "real_options.py"), "--recovery", path,
                    "--out", os.path.join(HERE, "results", "real_options_pairs.json"),
                    "--plot", os.path.join(HERE, "results", "policy_costs_pairs.png")])


if __name__ == "__main__":
    main()
