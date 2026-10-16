"""Run the full pilot grid: models x temperatures x anchor. Resumable.

Each configuration writes runs/<model>_t<temp>_<anchor|plain>/summary.csv; a finished
configuration is skipped on re-run, so an interrupted grid continues where it stopped.

  set OPENROUTER_API_KEY=...
  python run_all.py --n 1000 --workers 8
  python run_all.py --mock --n 100 --runs runs_mock      # dry run, no key
"""
import itertools, os, sys
import pandas as pd
import run_pilot as rp

MODELS = ["openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "anthropic/claude-haiku-5.5"]
TEMPS = [0.3, 0.7, 1.0]


def main():
    ap = rp.build_parser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--temps", default=",".join(map(str, TEMPS)))
    a = ap.parse_args()
    parts = []
    grid = list(itertools.product(a.models.split(","), [float(t) for t in a.temps.split(",")], [False, True]))
    for i, (model, temp, anchor) in enumerate(grid, 1):
        tag = f"{model.replace('/', '_')}_t{temp}_{'anchor' if anchor else 'plain'}"
        out = os.path.join(a.runs, tag)
        a.model, a.temp, a.anchor, a.out = model, temp, anchor, out
        if not os.path.exists(os.path.join(out, "summary.csv")):
            print(f"[{i}/{len(grid)}] {tag}", flush=True)
            rp.run(a)
        else:
            print(f"[{i}/{len(grid)}] {tag} (already done, skipped)", flush=True)
        s = pd.read_csv(os.path.join(out, "summary.csv"))
        s.insert(0, "anchor", anchor); s.insert(0, "temp", temp); s.insert(0, "model", model)
        parts.append(s)
    allp = pd.concat(parts)
    allp.to_csv(os.path.join(a.runs, "all_summary.csv"), index=False)
    cols = ["model", "temp", "anchor", "cond", "mean", "var_mean", "zero", "zero_expected_at_mean", "alpha", "js", "parse_fail"]
    print(allp[allp.cond != "real(ref)"][cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
