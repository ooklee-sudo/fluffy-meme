import json, statistics as st, collections
E_ = [r for f in ("results/editors_qwen7b_seed1_ike.json", "results/editors_qwen7b_seed1_edit.json", "results/editors_qwen7b_s23.json") for r in json.load(open(f)) if "error" not in r]
L = json.load(open("results/reallaw_qwen7b.json")) + json.load(open("results/reallaw_sweep_qwen7b.json"))
keys = ("listed", "unlisted_AB", "ripple_dep", "keep_control", "currency_all")
rows = collections.defaultdict(list)
for r in E_: rows[r["editor"]].append(r)
for r in L:
    if r["kA"] == 0.5 and r["kdep"] == 0 and (r["method"], r["lam"]) in (("none", 0.0), ("dep", 10.0), ("ss", 10.0)):
        rows[{"none": "fine-tune on amendments (LoRA)", "dep": "fine-tune + dependency-scoped KL", "ss": "fine-tune + stream-scoped KL"}[r["method"]]].append(r)
order = ["launch", "ike_own", "ike_all", "memit", "rome", "fine-tune on amendments (LoRA)", "fine-tune + dependency-scoped KL", "fine-tune + stream-scoped KL"]
print("Same listed amendments (kA=0.5, kdep=0), Qwen2.5-7B, seeds 1-3: mean [min-max]")
print(f"{'method':34s} n  " + "  ".join(f"{k:>22s}" for k in keys))
for m in order:
    v = rows.get(m); 
    if not v: continue
    cells = []
    for k in keys:
        xs = [x[k] for x in v if x[k] == x[k]]; cells.append(f"{st.mean(xs):.2f} [{min(xs):.2f}-{max(xs):.2f}]")
    print(f"{m:34s} {len(v)}  " + "  ".join(f"{c:>22s}" for c in cells))
