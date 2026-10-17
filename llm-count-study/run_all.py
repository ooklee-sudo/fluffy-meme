"""Run the pilot grid: models x temperatures x anchor x seeds. Resumable.

Each configuration writes <runs>/<model>_t<temp>_<anchor|plain>[_s<seed>]/summary.csv; a finished configuration is
skipped on re-run. Seed 0 keeps the folder names of earlier runs (no suffix).

  set OPENROUTER_API_KEY=...
  python run_all.py --n 200 --workers 12 --scenario grocery --temps 0.7 --seeds 1,2 --runs runs_grocery
  python run_all.py --mock --n 100 --runs runs_mock          # dry run, no key
"""
import itertools, os
import pandas as pd
import run_pilot as rp

MODELS = ["openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "anthropic/claude-haiku-5.5"]
TEMPS = [0.3, 0.7, 1.0]


def main():
    ap = rp.build_parser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--temps", default=",".join(map(str, TEMPS)))
    ap.add_argument("--seeds", default="0", help="comma-separated seeds, e.g. 0,1,2")
    a = ap.parse_args()
    temps = [float(t) for t in a.temps.split(",")]
    seeds = [int(x) for x in a.seeds.split(",")]
    grid = []
    for seed in seeds:
        for model in a.models.split(","):
            if not a.mock and not rp.model_info(model)["temperature"]:
                print(f"note: {model} does not accept temperature; running a single temperature setting", flush=True)
                mt = temps[:1]
            else:
                mt = temps
            grid += [(model, t, an, seed) for t in mt for an in (False, True)]
    parts = []
    for i, (model, temp, anchor, seed) in enumerate(grid, 1):
        a.wording = a.wording  # prompt wording is set per run directory (use a separate --runs folder per wording)
        tag = f"{model.replace('/', '_')}_t{temp}_{'anchor' if anchor else 'plain'}" + (f"_s{seed}" if seed else "")
        out = os.path.join(a.runs, tag)
        a.model, a.temp, a.anchor, a.out, a.seed = model, temp, anchor, out, seed
        if not os.path.exists(os.path.join(out, "summary.csv")):
            print(f"[{i}/{len(grid)}] {tag}", flush=True)
            rp.run(a)
        else:
            print(f"[{i}/{len(grid)}] {tag} (already done, skipped)", flush=True)
        s = pd.read_csv(os.path.join(out, "summary.csv"))
        s.insert(0, "seed", seed); s.insert(0, "anchor", anchor); s.insert(0, "temp", temp); s.insert(0, "model", model)
        parts.append(s)
    allp = pd.concat(parts)
    allp.to_csv(os.path.join(a.runs, "all_summary.csv"), index=False)
    print("\nfinished; summarize with: python analyze_ci.py --runs " + a.runs)


if __name__ == "__main__":
    main()
