"""H1 analysis of Phase 1 results: rank correlation of probe signals and tenant traits with capacity need.

Primary test (PREREGISTRATION.md): partial Spearman correlation of the gradient-probe normalized bond entropy
with log2 capacity need, controlling for mean response length; two-sided, alpha = 0.05. Tenants whose
gradient probe did not reach its token budget are left out. Every other row is exploratory; Holm-adjusted
p-values cover the probe rows of the zero-order table.

Usage:
  python analyze.py                      # reads results/phase1/*.json
  python analyze.py results/phase1_tiny
Writes <dir>_summary.json and <dir>_h1.png next to the results folder.
"""
import glob
import json
import math
import os
import sys
import warnings

import numpy as np
from scipy.stats import pearsonr, rankdata, spearmanr, t as tdist

PRIMARY = ("grad", "mean_norm_entropy")
SIGNALS = [  # (group, key, where in the result JSON)
    ("grad", "mean_norm_entropy", lambda r: r["grad_probe"]["summary"]),
    ("grad", "mean_rank_at_90", lambda r: r["grad_probe"]["summary"]),
    ("grad", "mean_rank_at_energy", lambda r: r["grad_probe"]["summary"]),
    ("grad-matrix", "mean_norm_entropy", lambda r: r["grad_probe"]["matrix_summary"]),
    ("grad-matrix", "mean_rank_at_90", lambda r: r["grad_probe"]["matrix_summary"]),
    ("tt-probe", "mean_norm_entropy", lambda r: r["probe"]["summary"]),
    ("tt-probe", "mean_rank_at_energy", lambda r: r["probe"]["summary"]),
]
TRAITS = ["mean_response_tokens", "response_type_token_ratio", "distinct_response_share", "mean_prompt_tokens"]


def partial_spearman(x, y, z):
    """Spearman correlation of x and y after removing a linear effect of z on the ranks; two-sided p, df n-3."""
    rx, ry, rz = (rankdata(v) for v in (x, y, z))
    res = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    r = float(pearsonr(res(rx), res(ry))[0])
    n = len(x)
    if n < 5 or abs(r) >= 1:
        return r, float("nan")
    tt = r * math.sqrt((n - 3) / (1 - r * r))
    return r, float(2 * tdist.sf(abs(tt), n - 3))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/phase1"
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    ok = [r for r in rows if r["capacity_need"] is not None]
    short = [r["tenant"] for r in ok if not r.get("grad_probe", {}).get("budget_met", True)]
    ok = [r for r in ok if r["tenant"] not in short]
    print(f"{len(rows)} tenants, {len(ok)} used (left out: {len(rows) - len(ok) - len(short)} without a positive gain,"
          f" {len(short)} below the probe token budget{': ' + ', '.join(short) if short else ''})")
    missing = [r["tenant"] for r in ok if "grad_probe" not in r]
    if missing:
        print(f"no gradient probe for {len(missing)} tenants; run: python phase1.py --reprobe ...")
        return
    if len(ok) < 4:
        print("need at least 4 tenants with a positive gain for a rank correlation")
        return
    need = [math.log2(r["capacity_need"]) for r in ok]
    best = [max(s["gain"] for s in r["sweep"]) for r in ok]

    warnings.filterwarnings("ignore", message=".*constant.*")
    table = []
    for group, key, get in SIGNALS:
        x = [get(r)[key] for r in ok]
        table.append([group, key, *spearmanr(x, need), *spearmanr(x, best)])
    adj = holm([t[3] if t[3] == t[3] else 1.0 for t in table])
    for t, a in zip(table, adj):
        t.append(a)
    for key in TRAITS:
        x = [r["features"][key] for r in ok]
        table.append(["trait", key, *spearmanr(x, need), *spearmanr(x, best), float("nan")])

    print(f"\n{'signal':<34}{'rho(need)':>10}{'p':>8}{'p Holm':>8}{'rho(best)':>11}{'p':>8}")
    for g, k, rn, pn, rb, pb, ph in table:
        mark = "  <- primary signal (zero-order; the test is PRIMARY below)" if (g, k) == PRIMARY else ""
        print(f"{g + ':' + k:<34}{rn:>10.3f}{pn:>8.3f}{ph:>8.3f}{rb:>11.3f}{pb:>8.3f}{mark}")
    print("\nneed = log2 of the interpolated bond dimension where the gain reaches the target share of the best"
          " gain; best = best gain over the sweep.\nHolm adjusts over the probe rows only."
          " With few tenants, treat this as a first signal.")

    # primary test
    x = [r["grad_probe"]["summary"]["mean_norm_entropy"] for r in ok]
    z = [r["features"]["mean_response_tokens"] for r in ok]
    pr, pp = partial_spearman(x, need, z)
    budget = ok[0]["grad_probe"].get("budget", "all")
    print(f"\nPRIMARY (two-sided): partial rho(grad entropy, log2 need | response length) = {pr:.3f}, p = {pp:.4f}, "
          f"n = {len(ok)}, probe budget = {budget} tokens -> {'significant' if pp < 0.05 else 'not significant'} at 0.05")
    lr, lp = partial_spearman(z, need, x)
    print(f"  for reference: partial rho(response length, log2 need | grad entropy) = {lr:.3f}, p = {lp:.4f}")
    seeds = [r.get("capacity_need_by_seed") for r in ok]
    if all(s and len(s) >= 2 for s in seeds):
        a, b = [math.log2(s[0]) for s in seeds], [math.log2(s[1]) for s in seeds]
        sr = spearmanr(a, b)[0]
        print(f"  seed reliability: Spearman of capacity need between seed 1 and seed 2 = {sr:.3f}")
    else:
        sr = None

    print(f"\n{'tenant':<18}{'need':>6}{'grid':>6}{'best':>7}{'grad H':>8}{'grad r90':>9}{'resp tok':>9}")
    for r, b in sorted(zip(ok, best), key=lambda z: z[0]["capacity_need"]):
        g = r["grad_probe"]["summary"]
        print(f"{r['tenant']:<18}{r['capacity_need']:>6.2f}{r.get('capacity_need_grid') or 0:>6}{b:>7.3f}"
              f"{g['mean_norm_entropy']:>8.3f}{g['mean_rank_at_90']:>9.1f}{r['features']['mean_response_tokens']:>9.1f}")

    out = d.rstrip("/")
    summary = dict(n_tenants=len(rows), n_used=len(ok), left_out_budget=short,
                   primary=dict(test="partial Spearman, grad mean_norm_entropy vs log2 need | mean_response_tokens",
                                rho=pr, p=pp, two_sided=True, alpha=0.05),
                   length_given_entropy=dict(rho=lr, p=lp), seed_reliability=sr, correlations=[
        dict(group=t[0], signal=t[1], rho_need=t[2], p_need=t[3], rho_best_gain=t[4], p_best_gain=t[5],
             p_need_holm=t[6]) for t in table],
        tenants=[dict(tenant=r["tenant"], capacity_need=r["capacity_need"], best_gain=b,
                      grad=r["grad_probe"]["summary"], grad_matrix=r["grad_probe"]["matrix_summary"],
                      tt_probe=r["probe"]["summary"], features=r["features"]) for r, b in zip(ok, best)])
    with open(out + "_summary.json", "w") as f:
        json.dump(summary, f, indent=1)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [r["grad_probe"]["summary"]["mean_norm_entropy"] for r in ok]
        fig, ax = plt.subplots(figsize=(5.5, 4))
        ax.scatter(x, [r["capacity_need"] for r in ok])
        for xi, r in zip(x, ok):
            ax.annotate(r["tenant"], (xi, r["capacity_need"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax.set_yscale("log", base=2)
        ax.set_xlabel("gradient-probe entanglement entropy (normalized, mean over bonds)")
        ax.set_ylabel("capacity need (bond dimension, interpolated)")
        ax.set_title(f"zero-order rho = {table[0][2]:.2f}; partial (| length) rho = {pr:.2f}, p = {pp:.3f} (n = {len(ok)})",
                     fontsize=9)
        fig.tight_layout()
        fig.savefig(out + "_h1.png", dpi=150)
        print(f"\nsaved {out}_summary.json and {out}_h1.png")
    except ImportError:
        print(f"\nsaved {out}_summary.json (install matplotlib for the plot)")


if __name__ == "__main__":
    main()
