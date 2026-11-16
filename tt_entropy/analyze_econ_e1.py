"""Economics study, E1 summary (exploratory): quality and per-request context of in-context personalization
(baselines.py) against the Phase 2 adapters, on the same tenants and evaluation tokens.

Usage: python analyze_econ_e1.py [results/econ_e1] [results/phase2_s0 results/phase2_s1]
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import wilcoxon

ADAPTERS = ["vera:256", "vera:1024", "lora:1", "lora:4"]


def main():
    e1 = sys.argv[1] if len(sys.argv) > 1 else "results/econ_e1"
    p2 = sys.argv[2:] or ["results/phase2_s0", "results/phase2_s1"]
    base = {json.load(open(f))["tenant"]: json.load(open(f)) for f in glob.glob(os.path.join(e1, "*.json"))}
    ad = defaultdict(lambda: defaultdict(list))
    params = {}
    for d in p2:
        for f in glob.glob(os.path.join(d, "*.json")):
            r = json.load(open(f))
            for x in r["runs"]:
                ad[r["tenant"]][x["config"]].append(x["rel_gain"])
                params[x["config"]] = x["params"]
    tenants = sorted(t for t in base if t in ad)
    if not tenants:
        raise SystemExit("no tenants with both baseline and adapter results")
    rows = {}
    for t in tenants:
        g = {m: v["rel_gain"] for m, v in base[t]["methods"].items()}
        g.update({c: float(np.mean(v)) for c, v in ad[t].items() if c in ADAPTERS})
        rows[t] = g
    ctx = {m: np.mean([base[t]["methods"][m]["context_tokens"] for t in tenants]) for m in base[tenants[0]]["methods"]}
    methods = list(base[tenants[0]]["methods"]) + [c for c in ADAPTERS if c in rows[tenants[0]]]
    zero_ctx = ctx.get("zero", 0)
    check = [abs(base[t]["methods"]["zero"]["nll"] - base[t]["phase2_nll_none"]) for t in tenants if "phase2_nll_none" in base[t]]
    print(f"{len(tenants)} tenants; zero-shot NLL matches Phase 2 nll_none within {max(check) if check else float('nan'):.2e}\n")
    print(f"{'method':<12}{'mean rel gain':>15}{'context tokens / request':>27}{'trainable params':>18}{'best for':>10}")
    best = defaultdict(int)
    for t in tenants:
        best[max(methods, key=lambda m: rows[t].get(m, -1))] += 1
    for m in methods:
        c = f"{ctx[m]:.0f}" if m in ctx else f"{zero_ctx:.0f}"
        print(f"{m:<12}{np.mean([rows[t][m] for t in tenants]):>15.4f}{c:>27}{params.get(m, 0):>18,}{best[m]:>10}")
    print("\nPaired comparisons (per tenant, Wilcoxon two-sided; exploratory):")
    for a, b in [("rag-8", "lora:1"), ("rag-8", "vera:256"), ("fewshot-8", "lora:1"), ("rag-8", "fewshot-8")]:
        if a in methods and b in methods:
            d = np.array([rows[t][a] - rows[t][b] for t in tenants])
            p = wilcoxon(d).pvalue if not np.allclose(d, 0) else float("nan")
            print(f"  {a + ' - ' + b:<22} median {np.median(d):+.4f}  {a} better in {(d > 0).sum()}/{len(d)}  p = {p:.4f}")
    print("\nIn-context methods add the listed context tokens to every request; adapters add none but need training"
          "\n(about 1 GPU-minute per tenant here) and storage. E2 turns these into costs per request volume.")


if __name__ == "__main__":
    main()
