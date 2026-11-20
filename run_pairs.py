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
  python run_pairs.py --suite gpu8 --tasks gsm8k --seeds 0   # 1-2B pairs on an 8 GB NVIDIA GPU (see README)
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
    ("pythia-70m +10k",   "EleutherAI/pythia-70m",        "step133000", "EleutherAI/pythia-70m",              "step143000"),
    ("pythia-70m +40k",   "EleutherAI/pythia-70m",        "step103000", "EleutherAI/pythia-70m",              "step143000"),
    ("pythia-70m +70k",   "EleutherAI/pythia-70m",        "step73000", "EleutherAI/pythia-70m",              "step143000"),
    ("pythia-410m +10k",   "EleutherAI/pythia-410m",        "step133000", "EleutherAI/pythia-410m",              "step143000"),
    ("pythia-410m +40k",   "EleutherAI/pythia-410m",        "step103000", "EleutherAI/pythia-410m",              "step143000"),
    ("pythia-410m +70k",   "EleutherAI/pythia-410m",        "step73000", "EleutherAI/pythia-410m",              "step143000"),
    ("smollm2-360m instr", "HuggingFaceTB/SmolLM2-360M",    None,         "HuggingFaceTB/SmolLM2-360M-Instruct", None),
    ("qwen2.5-0.5b instr", "Qwen/Qwen2.5-0.5B",             None,         "Qwen/Qwen2.5-0.5B-Instruct",          None),
]

# --suite gpu8: 1-2B models on an 8 GB NVIDIA GPU (act_llama.py --preset gpu8).  Ordered by priority: the first rows
# extend the paper's Pythia series in scale, then the base->instruct pairs that test the SmolLM2 exception, then a second
# model family with its own drift series.
P, O = "EleutherAI/pythia-", "allenai/OLMo-2-0425-1B"
OLMO_END = "stage1-step1907359-tokens4001B"
GPU8_PAIRS = [
    ("pythia-1b +70k",       P + "1b",   "step73000",  P + "1b",   "step143000"),
    ("pythia-1b +10k",       P + "1b",   "step133000", P + "1b",   "step143000"),
    ("pythia-1b +40k",       P + "1b",   "step103000", P + "1b",   "step143000"),
    ("pythia-1b +60k",       P + "1b",   "step83000",  P + "1b",   "step143000"),
    ("qwen2.5-1.5b instr",   "Qwen/Qwen2.5-1.5B",          None, "Qwen/Qwen2.5-1.5B-Instruct",          None),
    ("smollm2-1.7b instr",   "HuggingFaceTB/SmolLM2-1.7B", None, "HuggingFaceTB/SmolLM2-1.7B-Instruct", None),
    ("olmo2-1b instr",       O,                            None, O + "-Instruct",                       None),
    ("qwen2.5-0.5b instr",   "Qwen/Qwen2.5-0.5B",          None, "Qwen/Qwen2.5-0.5B-Instruct",          None),
    ("olmo2-1b +907k",       O, "stage1-step1000000-tokens2098B", O, OLMO_END),
    ("olmo2-1b +107k",       O, "stage1-step1800000-tokens3775B", O, OLMO_END),
    ("olmo2-1b +307k",       O, "stage1-step1600000-tokens3356B", O, OLMO_END),
    ("olmo2-1b +507k",       O, "stage1-step1400000-tokens2937B", O, OLMO_END),
    ("pythia-1.4b +70k",     P + "1.4b", "step73000",  P + "1.4b", "step143000"),
    ("pythia-1.4b +10k",     P + "1.4b", "step133000", P + "1.4b", "step143000"),
    ("pythia-1.4b +40k",     P + "1.4b", "step103000", P + "1.4b", "step143000"),
    ("pythia-1.4b +60k",     P + "1.4b", "step83000",  P + "1.4b", "step143000"),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def slug(name):
    s = "".join(c if c.isalnum() else "_" for c in name)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows consoles (cp949 etc.) cannot print every character
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    if "--suite" in sys.argv and sys.argv[sys.argv.index("--suite") + 1] == "gpu8":
        return main_gpu8()
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



# ---------------------------------------------------------------- gpu8 suite
def purge_revision(repo, rev):
    """Delete one downloaded revision from the Hugging Face cache (each Pythia/OLMo checkpoint is 2-6 GB)."""
    try:
        from huggingface_hub import scan_cache_dir
        info = scan_cache_dir()
        hashes = [r.commit_hash for repo_ in info.repos if repo_.repo_id == repo
                  for r in repo_.revisions if rev in r.refs]
        if hashes:
            strategy = info.delete_revisions(*hashes)
            print(f"[purge] {repo}@{rev}: frees {strategy.expected_freed_size_str}")
            strategy.execute()
    except Exception as e:  # never fail a run over cache cleanup
        print(f"[purge] {repo}@{rev} skipped: {e}")


def median_drift(r):
    d = sorted(v["drift"] for v in r["act_info"].values())
    return d[len(d) // 2]


def summarize_gpu8(outdir):
    """Mean and sd over seeds per (task, pair); policy quantities from the mean recoveries and cost ratio."""
    import glob
    from dataclasses import replace
    sys.path.insert(0, HERE)
    import real_options as ro
    groups = {}
    for path in sorted(glob.glob(os.path.join(outdir, "*", "*.json"))):
        if os.sep + "check" + os.sep in path:
            continue
        r = json.load(open(path))
        task = r["args"].get("task", "gsm8k")
        rec = r["recovery"][0]
        groups.setdefault((task, r["pair"]), []).append(
            {"seed": r["args"]["seed"], "R_C": rec["R_C"], "R_A": rec["R_A"], "C": r["C_A_over_C_N"],
             "drift": median_drift(r), "t_retrain": r["time_retrain_s"], "t_act": r["time_act_s"],
             "gpu": r.get("gpu"), "peak_gb": r.get("peak_gpu_mem_gb")})
    order = {name: i for i, (name, *_) in enumerate(GPU8_PAIRS)}
    rows = []
    for (task, pair), runs in sorted(groups.items(), key=lambda kv: (kv[0][0], order.get(kv[0][1], 99))):
        m = lambda k: statistics.mean(x[k] for x in runs)
        sd = lambda k: statistics.stdev(x[k] for x in runs) if len(runs) > 1 else float("nan")
        R_C, R_A, C = (min(m(k), 0.999) for k in ("R_C", "R_A", "C"))
        p = replace(ro.Params(), C_A=C)
        G = ro.gamma(R_A, R_C, p)
        reg = ro.act_region(R_C, R_A, p)
        rows.append({"task": task, "pair": pair, "n_seeds": len(runs), "drift": m("drift"),
                     "R_C": m("R_C"), "R_C_sd": sd("R_C"), "R_A": m("R_A"), "R_A_sd": sd("R_A"),
                     "gain": m("R_A") - m("R_C"), "C_A_over_C_N": m("C"), "C_sd": sd("C"), "Gamma": G,
                     "v_star_copy": ro.v_star(R_C, p), "act_optimal": list(reg) if reg else None,
                     "gpu": runs[0]["gpu"], "peak_gb": max((x["peak_gb"] or 0) for x in runs)})
    json.dump(rows, open(os.path.join(HERE, "results", "gpu8_summary.json"), "w", encoding="utf-8"), indent=2, default=float)
    f = lambda x: "-" if x != x else f"{x:.3f}"
    lines = ["| Task | Pair | Seeds | Drift | R_C (sd) | R_A (sd) | Gain | C_A/C_N | Γ | ACT optimal for |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        reg = f"[{r['act_optimal'][0]:.2f}, {r['act_optimal'][1]:.2f})" if r["act_optimal"] else "never"
        lines.append(f"| {r['task']} | {r['pair']} | {r['n_seeds']} | {r['drift']:.2f} | {f(r['R_C'])} ({f(r['R_C_sd'])}) "
                     f"| {f(r['R_A'])} ({f(r['R_A_sd'])}) | {r['gain']:+.3f} | {r['C_A_over_C_N']:.2f} | {r['Gamma']:.2f} | {reg} |")
    md = os.path.join(HERE, "results", "gpu8_table.md")
    open(md, "w", encoding="utf-8").write("Baseline parameters ρ=0.10, μ=2, g=0.20, σ=0.40; Γ and v in multiples of C_N; "
                        "C_A/C_N is compute time only (weight moves under --offload excluded).\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines) + f"\n\nsaved {md} and results/gpu8_summary.json")


def main_gpu8():
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[: argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(description="1-2B model pairs on an 8 GB NVIDIA GPU")
    ap.add_argument("--suite", choices=["gpu8"])
    ap.add_argument("--only", default="", help="run pairs whose name contains this text")
    ap.add_argument("--tasks", default="gsm8k,samsum,boolq")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--outdir", default=os.path.join(HERE, "results", "gpu8"))
    ap.add_argument("--force", action="store_true", help="rerun runs that already have results")
    ap.add_argument("--purge", action="store_true",
                    help="delete each source checkpoint from the Hugging Face cache once all its runs are done")
    ap.add_argument("--check-precision", action="store_true",
                    help="rerun pythia-1b +70k (gsm8k, seed 0) with float64 Gram matrices and compare with the default")
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args(argv)
    tasks, seeds = a.tasks.split(","), [int(x) for x in a.seeds.split(",")]

    def run(name, src, srev, tgt, trev, task, seed, out, more=()):
        cmd = [sys.executable, os.path.join(HERE, "act_llama.py"), "--preset", "gpu8", "--task", task,
               "--seed", str(seed), "--source", src, "--target", tgt, "--pair-name", name, "--out", out]
        cmd += ["--source-revision", srev] if srev else []
        cmd += ["--target-revision", trev] if trev else []
        cmd += list(more) + extra
        print(f"\n===== {name} | {task} | seed {seed} =====\n" + " ".join(cmd), flush=True)
        t0 = time.time()
        rc = subprocess.run(cmd).returncode
        print(f"[{'done' if rc == 0 else f'fail (exit {rc})'}] {name} {task} s{seed} in {(time.time() - t0) / 60:.1f} min",
              flush=True)
        return rc == 0

    if a.check_precision:
        name, src, srev, tgt, trev = GPU8_PAIRS[0]
        ref = os.path.join(a.outdir, "gsm8k", slug(name) + "_s0.json")
        chk = os.path.join(a.outdir, "check", slug(name) + "_s0_double.json")
        if not os.path.exists(ref):
            run(name, src, srev, tgt, trev, "gsm8k", 0, ref)
        run(name, src, srev, tgt, trev, "gsm8k", 0, chk, ["--gram-acc", "double"])
        r1, r2 = json.load(open(ref)), json.load(open(chk))
        same = sum(r1["act_info"][k]["alpha"] == r2["act_info"][k]["alpha"] for k in r1["act_info"])
        print(f"\nmixed vs double: same alpha in {same}/{len(r1['act_info'])} modules; "
              f"ACT NLL {r1['act']['nll']:.5f} vs {r2['act']['nll']:.5f}; "
              f"R_A {r1['recovery'][0]['R_A']:.4f} vs {r2['recovery'][0]['R_A']:.4f}; "
              f"ACT time {r1['time_act_s']:.0f}s vs {r2['time_act_s']:.0f}s")
        return

    if not a.summary_only:
        pairs = [p for p in GPU8_PAIRS if not a.only or a.only in p[0]]
        for i, (name, src, srev, tgt, trev) in enumerate(pairs):
            for task in tasks:
                for seed in seeds:
                    out = os.path.join(a.outdir, task, f"{slug(name)}_s{seed}.json")
                    if os.path.exists(out) and not a.force:
                        print(f"[skip] {name} {task} s{seed}: {out} exists")
                        continue
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    run(name, src, srev, tgt, trev, task, seed, out)
            later = {(p[1], p[2]) for p in pairs[i + 1:]} | {(p[3], p[4]) for p in pairs}
            if a.purge and srev and (src, srev) not in later:
                purge_revision(src, srev)
    summarize_gpu8(a.outdir)


if __name__ == "__main__":
    main()
