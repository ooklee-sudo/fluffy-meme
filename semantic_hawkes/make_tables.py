"""Turn runs/results.jsonl and results.json into LaTeX tables for paper/main.tex (best value in bold)."""
import json
import os
from collections import defaultdict

import numpy as np

DATA = [("us-earthquake", "US Earthquake"), ("nyc-taxi", "NYC Taxi"), ("amazon-review", "Amazon Review"),
        ("chicago-crime", "Chicago Crime"), ("stack-overflow", "Stack Overflow")]
MODELS = [("NHP", "NHP"), ("THP", "THP"), ("FreeHawkesTPP", "Free Hawkes"), ("SemHawkesTPP", "Text-Hawkes (ours)")]
OUT = "paper/tables"


def cell(vals, best, fmt):
    if not vals:
        return "--"
    m = np.mean(vals)
    s = (fmt % m).replace("-", "$-$")
    if len(vals) > 1:
        s += r"{\scriptsize$\,\pm\,$" + fmt % np.std(vals, ddof=1) + "}"
    return r"\textbf{" + s + "}" if np.isclose(m, best) else s


def results_table(rows, n_train, caption, label):
    by = defaultdict(list)
    for r in rows:
        if (r["n_train"] or 0) == n_train and r["tag"] in ("", "qwen"):  # main tables: Qwen embeddings only
            by[(r["data"], r["model"])].append(r)
    lines = [r"\begin{table}[t]", r"\centering", r"\caption{" + caption + "}", r"\label{" + label + "}",
             r"\small", r"\begin{tabular}{llrrr}", r"\toprule",
             r"Dataset & Model & Test LL $\uparrow$ & Type acc.\ $\uparrow$ & Time RMSE $\downarrow$ \\", r"\midrule"]
    for d, dn in DATA:
        stats = {}
        for m, _ in MODELS:
            rs = by.get((d, m), [])
            stats[m] = dict(ll=[r["test_ll"] for r in rs], acc=[r["acc"] for r in rs], rmse=[r["rmse"] for r in rs])
        best = {k: (max if k != "rmse" else min)([np.mean(v[k]) for v in stats.values() if v[k]] or [np.nan])
                for k in ("ll", "acc", "rmse")}
        for i, (m, mn) in enumerate(MODELS):
            s = stats[m]
            lines.append(f"{dn if i == 0 else ''} & {mn} & {cell(s['ll'], best['ll'], '%.3f')} & "
                         f"{cell(s['acc'], best['acc'], '%.3f')} & {cell(s['rmse'], best['rmse'], '%.3f')} \\\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines += [r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def synthetic_table():
    res = json.load(open("semantic_hawkes/results.json"))
    by = defaultdict(list)
    for r in res["rows"]:
        by[(r["n_train"], r["model"])].append(r)
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Synthetic experiment ($K=12$ event types, three random seeds; mean $\pm$ s.d.). "
             r"``Oracle'' evaluates the data-generating parameters.}", r"\label{tab:synthetic}", r"\small",
             r"\begin{tabular}{rlrrr}", r"\toprule",
             r"$n_{\mathrm{train}}$ & Model & Test LL $\uparrow$ & Type acc.\ $\uparrow$ & $\mathrm{corr}(\hat A,A)$ $\uparrow$ \\",
             r"\midrule"]
    for n in sorted({k[0] for k in by}):
        best_ll = max(np.mean([r["test_ll"] for r in by[(n, m)]]) for m in ("free", "semantic"))
        for i, (m, mn) in enumerate((("free", "Free Hawkes"), ("semantic", "Text-Hawkes"))):
            rs = by[(n, m)]
            lines.append(f"{n if i == 0 else ''} & {mn} & {cell([r['test_ll'] for r in rs], best_ll, '%.3f')} & "
                         f"{cell([r['acc'] for r in rs], 9, '%.3f')} & {cell([r['A_corr'] for r in rs], 9, '%.3f')} \\\\")
        lines.append(r"\midrule")
    o = res["oracle"]
    lines += [f"-- & Oracle & {o['ll']:.3f} & {o['acc']:.3f} & 1.000 \\\\", r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open("semantic_hawkes/runs/results.jsonl")] \
        if os.path.exists("semantic_hawkes/runs/results.jsonl") else []
    open(f"{OUT}/results_full.tex", "w").write(results_table(
        rows, 0, r"Results with the full training split. Test log-likelihood (LL) per event, next-event type accuracy and "
                 r"time RMSE at the epoch with the best validation LL. Best value per dataset in bold.", "tab:full"))
    open(f"{OUT}/results_small.tex", "w").write(results_table(
        rows, 200, r"Results when only 200 randomly selected training sequences are used (same metrics as Table~\ref{tab:full}).",
        "tab:small"))
    open(f"{OUT}/synthetic.tex", "w").write(synthetic_table())
    print("wrote tables from", len(rows), "result rows")
