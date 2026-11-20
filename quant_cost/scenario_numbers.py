"""Turn measurements into the performance numbers that go into the survey scenarios.

For each survey case (A-D) it reports accuracy of the chosen LOCAL model and the cloud API, and the cost per correct
answer (local: energy + hardware time; API: tokens x price), using the same cost model as analyze.py.

  python -m quant_cost.scenario_numbers --local-label qwen2.5-3b-instruct-q4_k_m --api-label api_qwen_qwen-2.5-72b-instruct

The synthetic tasks are only PROXIES for the four business cases (default mapping below). For the paper use
real task data (--task-file in bench) and map each case to its own task with --map.
Only the performance table of the survey changes; the cost figures B, E, L and lambda are fixed design values.
"""
import argparse
import json
import math
import os

from .analyze import load, local_cost

DEFAULT_MAP = "A=ticket,B=extract,C=arith,D=*"   # "*" = average over all tasks
CASE_NAMES = {"A": "customer inquiry classification", "B": "HR records", "C": "contract documents",
              "D": "insurance claims"}


def parse_map(s):
    return dict(kv.split("=") for kv in s.split(","))


def usd(x):
    """3 significant digits, never scientific notation or a misleading 0.0000."""
    return f"{x:.{max(2, 2 - int(math.floor(math.log10(x))))}f}"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def pick_local(local_runs, max_gib):
    cands = [r for r in local_runs if (r["meta"].get("file_gib") or 0) <= max_gib]
    if not cands:
        raise SystemExit(f"no local result with weights <= {max_gib} GiB")
    best = max(cands, key=lambda r: mean(t["acc"] for t in r["tasks"].values()))
    print(f"[auto] local model = {best['meta']['label']} (best mean accuracy among results <= {max_gib} GiB)")
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/quant_cost")
    ap.add_argument("--local-label")
    ap.add_argument("--api-label")
    ap.add_argument("--max-gib", type=float, default=6.5, help="auto-pick limit for the local model's weight size")
    ap.add_argument("--map", default=DEFAULT_MAP)
    ap.add_argument("--elec-usd-kwh", type=float, default=0.12)
    ap.add_argument("--hw-usd", type=float, default=1500.0)
    ap.add_argument("--life-years", type=float, default=3.0)
    ap.add_argument("--utilization", type=float, default=0.25)
    ap.add_argument("--marginal-energy", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    runs = load(a.dir)
    local = [r for r in runs if r["meta"]["kind"] == "local"]
    apis = [r for r in runs if r["meta"]["kind"] == "api"]
    if not local or not apis:
        raise SystemExit("need at least one local and one API result in " + a.dir)
    lr = next((r for r in local if r["meta"]["label"] == a.local_label), None) if a.local_label else pick_local(local, a.max_gib)
    ar = next((r for r in apis if r["meta"]["label"] == a.api_label), apis[0]) if a.api_label else apis[0]
    if lr is None:
        raise SystemExit(f"local label {a.local_label!r} not found; have: {[r['meta']['label'] for r in local]}")
    tasks_both = [t for t in lr["tasks"] if t in ar["tasks"]]
    cmap = parse_map(a.map)

    rows = {}
    for case, tk in cmap.items():
        ts = tasks_both if tk == "*" else [tk]
        ts = [t for t in ts if t in tasks_both]
        if not ts:
            print(f"[skip] case {case}: task {tk!r} not measured for both models")
            continue
        q_l = mean(lr["tasks"][t]["acc"] for t in ts)
        q_a = mean(ar["tasks"][t]["acc"] for t in ts)
        c_l = mean(local_cost(lr["tasks"][t], a)[0] for t in ts)
        c_a = mean(ar["tasks"][t]["cost_usd_per_req"] for t in ts)
        rows[case] = {"task": tk, "acc_local": q_l, "acc_api": q_a, "cost_req_local": c_l, "cost_req_api": c_a,
                      "cost_per_correct_local": c_l / q_l if q_l else None,
                      "cost_per_correct_api": c_a / q_a if q_a else None}

    print(f"\nlocal = {lr['meta']['label']}   api = {ar['meta']['label']}\n")
    print("| case | task | accuracy local / API | cost per correct answer local / API |")
    print("| --- | --- | --- | --- |")
    for case, r in rows.items():
        cl = r["cost_per_correct_local"]
        ca = r["cost_per_correct_api"]
        print(f"| {case} ({CASE_NAMES.get(case, '')}) | {r['task']} | {r['acc_local']*100:.0f}% / {r['acc_api']*100:.0f}% "
              f"| ${usd(cl)} / ${usd(ca)} |" if cl and ca else f"| {case} | {r['task']} | n/a | n/a |")
    print("\nSurvey rows (study2_survey_instrument.md section 4-2, second table):")
    for case, r in rows.items():
        if r["cost_per_correct_local"] and r["cost_per_correct_api"]:
            print(f"| {case} | [{r['acc_local']*100:.0f}]% / [{r['acc_api']*100:.0f}]% | "
                  f"$[{usd(r['cost_per_correct_local'])}] / $[{usd(r['cost_per_correct_api'])}] |")
    print("\nCaveat: the synthetic tasks are proxies for the business cases; local cost depends on --hw-usd, "
          "--utilization, electricity price and the energy method recorded in each result.")

    out = a.out or os.path.join(a.dir, "scenario_numbers.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"local": lr["meta"]["label"], "api": ar["meta"]["label"], "map": cmap,
                   "cost_model": {k: getattr(a, k) for k in ("elec_usd_kwh", "hw_usd", "life_years", "utilization",
                                                             "marginal_energy")},
                   "cases": rows}, f, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
