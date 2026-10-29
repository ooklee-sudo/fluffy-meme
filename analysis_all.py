"""Combine all multi-seed result sets into one table of (pair, task) cells with Gamma and the copy/tool verdict.

  python analysis_all.py        # writes results/all_tasks_summary.json and prints the markdown table

Cost reference: the CPU compute-only ratio C_A/C_N of the pair (Table C.1) for the 160M-0.5B pairs; 0.36 (the
Pythia-160M +70k value) for the 1.4B-3B pairs, whose CPU cost was not measured. The same ratio is used for every task.
"""
import json
import re

from real_options import Params, gamma

SETS = [("results/seeds_gpu", "GSM8K"), ("results/seeds_large_gpu", "GSM8K"),
        ("results/tasks_small_gpu", None), ("results/tasks_large_gpu", None)]
CPU_RATIO = {"pythia-160m +10k": 0.377, "pythia-160m +30k": 0.348, "pythia-160m +70k": 0.359,
             "smollm2-360m instr": 0.612, "qwen2.5-0.5b instr": 0.433}
REF = 0.36
p = Params()
clip = lambda r: min(max(r, 0.0), 0.999)
rows = []
for d, task in SETS:
    for pair, v in json.load(open(f"{d}/summary.json")).items():
        if pair.startswith("_"):
            continue
        m = re.match(r"(.*?) \[(\w+)\]$", pair)
        name, tk = (m.group(1), m.group(2)) if m else (pair, task)
        RC, RA = clip(v["R_C"]["mean"]), clip(v["R_A"]["mean"])
        G = gamma(RA, RC, p) if RA > RC + 1e-9 and RC < 0.95 else 0.0
        cost = CPU_RATIO.get(name, REF)
        rows.append(dict(pair=name, task={"gsm8k": "GSM8K", "dialogsum": "DialogSum", "sql": "SQL"}.get(tk.lower(), tk), n=v["n"],
                         R_C=v["R_C"]["mean"], R_C_lo=v["R_C"]["lo"], R_C_hi=v["R_C"]["hi"],
                         R_A=v["R_A"]["mean"], R_A_lo=v["R_A"]["lo"], R_A_hi=v["R_A"]["hi"],
                         Gamma=G, cost=cost, tool_pays=bool(G > cost)))
json.dump(rows, open("results/all_tasks_summary.json", "w"), indent=1)
order = ["pythia-160m +10k", "pythia-160m +30k", "pythia-160m +70k", "smollm2-360m instr", "qwen2.5-0.5b instr",
         "pythia-1.4b +10k", "pythia-1.4b +70k", "qwen2.5-1.5b instr", "smollm2-1.7b instr", "qwen2.5-3b instr"]
rows.sort(key=lambda r: (order.index(r["pair"]), r["task"]))
print("| Pair | Task | Seeds | $R_C$ [95% CI] | $R_A$ [95% CI] | $\\Gamma$ | Tool pays |\n|:---|:---|---:|:---:|:---:|---:|:---:|")
for r in rows:
    print(f"| {r['pair']} | {r['task']} | {r['n']} | {r['R_C']:.2f} [{r['R_C_lo']:.2f}, {r['R_C_hi']:.2f}] | {r['R_A']:.2f} [{r['R_A_lo']:.2f}, {r['R_A_hi']:.2f}] | {r['Gamma']:.2f} | {'yes' if r['tool_pays'] else 'no'} |")
print(f"\ncells {len(rows)}, tool pays in {sum(r['tool_pays'] for r in rows)}")
sm = [r for r in rows if r['pair'].startswith('pythia-160m')]
for t in ("GSM8K","DialogSum","SQL"):
    for pr in ("pythia-160m +10k","pythia-160m +30k","pythia-160m +70k"):
        x=[r for r in rows if r['pair']==pr and r['task']==t][0]; print(t,pr,round(x['R_C'],3),round(x['R_A'],3))
