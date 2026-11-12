"""H1 analysis of Phase 1 results: rank correlation of probe entropy and tenant traits with capacity need.

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

from scipy.stats import spearmanr

PROBE = ["mean_norm_entropy", "mean_entropy", "max_entropy", "mean_rank_at_energy"]
TRAITS = ["n_examples", "mean_response_tokens", "response_type_token_ratio", "distinct_response_share"]


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/phase1"
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    ok = [r for r in rows if r["capacity_need"] is not None]
    print(f"{len(rows)} tenants, {len(ok)} with a positive gain (others are left out)")
    if len(ok) < 4:
        print("need at least 4 tenants with a positive gain for a rank correlation")
        return
    need = [math.log2(r["capacity_need"]) for r in ok]
    best = [max(s["gain"] for s in r["sweep"]) for r in ok]

    table = []
    for k in PROBE:
        x = [r["probe"]["summary"][k] for r in ok]
        table.append(("probe", k, *spearmanr(x, need), *spearmanr(x, best)))
    for k in TRAITS:
        x = [r["features"][k] for r in ok]
        table.append(("trait", k, *spearmanr(x, need), *spearmanr(x, best)))

    print(f"\n{'signal':<32}{'rho(need)':>10}{'p':>8}{'rho(best gain)':>16}{'p':>8}")
    for kind, k, rn, pn, rb, pb in table:
        print(f"{kind + ':' + k:<32}{rn:>10.3f}{pn:>8.3f}{rb:>16.3f}{pb:>8.3f}")
    print("\nneed = log2 of the smallest bond dimension reaching the target share of the best gain."
          "\nWith few tenants and few rank levels, treat p-values as a first signal only.")

    out = d.rstrip("/")
    summary = dict(n_tenants=len(rows), n_used=len(ok), correlations=[
        dict(kind=t[0], signal=t[1], rho_need=t[2], p_need=t[3], rho_best_gain=t[4], p_best_gain=t[5])
        for t in table], tenants=[dict(tenant=r["tenant"], capacity_need=r["capacity_need"],
                                       best_gain=b, **r["probe"]["summary"]) for r, b in zip(ok, best)])
    with open(out + "_summary.json", "w") as f:
        json.dump(summary, f, indent=1)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = [r["probe"]["summary"]["mean_norm_entropy"] for r in ok]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.scatter(x, [r["capacity_need"] for r in ok])
        for xi, r in zip(x, ok):
            ax.annotate(r["tenant"], (xi, r["capacity_need"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax.set_yscale("log", base=2)
        ax.set_xlabel("probe entanglement entropy (normalized, mean over bonds)")
        ax.set_ylabel("capacity need (bond dimension)")
        ax.set_title(f"H1: rho = {table[0][2]:.2f} (n = {len(ok)})")
        fig.tight_layout()
        fig.savefig(out + "_h1.png", dpi=150)
        print(f"saved {out}_summary.json and {out}_h1.png")
    except ImportError:
        print(f"saved {out}_summary.json (install matplotlib for the plot)")


if __name__ == "__main__":
    main()
