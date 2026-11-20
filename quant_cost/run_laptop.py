"""One entry point for the laptop measurement. Stages run in order of effort; each is resumable.

  python -m quant_cost.run_laptop --stage check            # environment check only (1 min)
  python -m quant_cost.run_laptop --stage smoke            # tiny end-to-end test with a 0.5B model (~10 min)
  python -m quant_cost.run_laptop --stage main             # full ladders (hours; finished models are skipped)
  python -m quant_cost.run_laptop --stage report           # analysis + survey numbers
  python -m quant_cost.run_laptop --stage all              # main + report

Options: --route auto|llamacpp|torch, --n 100, --cpu (no GPU, for tests), --dry-run (print commands only),
--with-14b (llama.cpp route, adds 14B q2_k),
--api-model qwen/qwen-2.5-72b-instruct (needs OPENROUTER_API_KEY).
"""
import argparse
import os
import subprocess
import sys
import time

from .doctor import diagnose

LADDERS = {
    "llamacpp": [("Qwen/Qwen2.5-3B-Instruct-GGUF", "qwen2.5-3b-instruct", "q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k,q8_0", 3),
                 ("Qwen/Qwen2.5-7B-Instruct-GGUF", "qwen2.5-7b-instruct", "q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k", 7)],
    "torch": [("Qwen/Qwen2.5-3B-Instruct", None, "fp16,int8,nf4,fp4", 3),
              ("Qwen/Qwen2.5-7B-Instruct", None, "nf4,fp4", 7)],
}
SMALL = {
    "llamacpp": [("Qwen/Qwen2.5-0.5B-Instruct-GGUF", "qwen2.5-0.5b-instruct", "q4_k_m,q8_0", 0.5)],
    "torch": [("Qwen/Qwen2.5-0.5B-Instruct", None, "fp16,nf4", 0.5)],
}
EXTRA_14B = ("Qwen/Qwen2.5-14B-Instruct-GGUF", "qwen2.5-14b-instruct", "q2_k", 14)


def run(cmd, log, dry):
    line = " ".join(cmd)
    print("\n$", line, flush=True)
    if dry:
        return 0
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    # unbuffered child output, so progress shows up in run.out while a model is still being measured
    return subprocess.run(cmd, env=dict(os.environ, PYTHONUNBUFFERED="1")).returncode


def sweep_cmds(route, ladders, n, out_dir, a):
    py = [sys.executable, "-m"]
    cmds = []
    for repo, prefix, quants, pb in ladders:
        if route == "llamacpp":
            extra = ["--", "--n-gpu-layers", "0"] if a.cpu else []
            cmds.append(py + ["quant_cost.sweep", "--repo", repo, "--prefix", prefix, "--quants", quants,
                              "--params-b", str(pb), "--n", str(n), "--out-dir", out_dir] + extra)
        else:
            quants_ = "bf16" if a.cpu else quants
            extra = []
            if a.cpu:
                extra += ["--device", "cpu"]
            cmds.append(py + ["quant_cost.sweep_hf", "--model", repo, "--quants", quants_, "--params-b", str(pb),
                              "--n", str(n), "--out-dir", out_dir] + (["--"] + extra if extra else []))
    return cmds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="check", choices=["check", "smoke", "main", "report", "all"])
    ap.add_argument("--route", default="auto", choices=["auto", "llamacpp", "torch"])
    ap.add_argument("--n", type=int, default=100, help="items per task in the main stage")
    ap.add_argument("--results-dir", default="results/quant_cost")
    ap.add_argument("--cpu", action="store_true", help="run on CPU (tests only)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-14b", action="store_true")
    ap.add_argument("--api-model", default="qwen/qwen-2.5-72b-instruct")
    ap.add_argument("--local-label", help="local model for the survey numbers (default: best accuracy <= 6.5 GiB)")
    a = ap.parse_args()

    d = diagnose()
    route = a.route
    if route == "auto":
        if d["routes"]:
            route = d["routes"][0]
        elif a.cpu:
            route = "torch" if d["torch"]["ok"] else "llamacpp"
        elif a.stage in ("check", "report"):
            route = "llamacpp"
        else:
            raise SystemExit("\nNo GPU route works. Fix the problems listed above (see measurement_plan_rtx4060.md), "
                             "or add --cpu for a CPU-only test.")
    if a.stage == "check":
        print(f"\nChosen route if you continue: {route}")
        return
    os.makedirs(a.results_dir, exist_ok=True)
    log = os.path.join(a.results_dir, "run_log.txt")

    if a.stage == "smoke":
        out = a.results_dir + "_check"
        for c in sweep_cmds(route, SMALL[route], 10, out, a):
            if run(c, log, a.dry_run) != 0:
                raise SystemExit("\nSmoke test failed: fix this before the main run (see the error above).")
        print(f"\nSmoke test done. Look at {out}/*.json: energy_method, gpu_peak_mem_mib, gen_tokens_per_s.")
        print("If energy_method says no_gpu_meter, this laptop does not report GPU power. Wall-plug energy needs one")
        print("run per model with its own measured watts (bench.py --wall-watts W --wall-idle-watts W0); do not use one value for all.")
        return

    if a.stage in ("main", "all"):
        ladders = list(LADDERS[route]) + ([EXTRA_14B] if a.with_14b and route == "llamacpp" else [])
        for c in sweep_cmds(route, ladders, a.n, a.results_dir, a):
            run(c, log, a.dry_run)
        if os.environ.get("OPENROUTER_API_KEY") or a.dry_run:
            run([sys.executable, "-m", "quant_cost.api_baseline", "--model", a.api_model, "--n", str(a.n),
                 "--out-dir", a.results_dir], log, a.dry_run)
        else:
            print("\n[skip] API baseline: set OPENROUTER_API_KEY and rerun with --stage report after running "
                  "python -m quant_cost.api_baseline --model", a.api_model)

    if a.stage in ("report", "all"):
        run([sys.executable, "-m", "quant_cost.analyze", "--dir", a.results_dir, "--out", a.results_dir,
             "--pii-loss-usd", "0.01"], log, a.dry_run)
        sc = [sys.executable, "-m", "quant_cost.scenario_numbers", "--dir", a.results_dir]
        if a.local_label:
            sc += ["--local-label", a.local_label]
        run(sc, log, a.dry_run)


if __name__ == "__main__":
    main()
