"""H1 analysis of Phase 1 results: rank correlation of probe signals and tenant traits with capacity need.

Primary test (fixed in advance): gradient-probe normalized bond entropy vs. log2 capacity need.
Every other row is exploratory; Holm-adjusted p-values cover all probe rows.

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

from scipy.stats import spearmanr

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
    print(f"{len(rows)} tenants, {len(ok)} with a positive gain (others are left out)")
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
        mark = "  <- primary" if (g, k) == PRIMARY else ""
        print(f"{g + ':' + k:<34}{rn:>10.3f}{pn:>8.3f}{ph:>8.3f}{rb:>11.3f}{pb:>8.3f}{mark}")
    print("\nneed = log2 of the interpolated bond dimension where the gain reaches the target share of the best"
          " gain; best = best gain over the sweep.\nHolm adjusts over the probe rows only."
          " With few tenants, treat this as a first signal.")

    print(f"\n{'tenant':<18}{'need':>6}{'grid':>6}{'best':>7}{'grad H':>8}{'grad r90':>9}{'resp tok':>9}")
    for r, b in sorted(zip(ok, best), key=lambda z: z[0]["capacity_need"]):
        g = r["grad_probe"]["summary"]
        print(f"{r['tenant']:<18}{r['capacity_need']:>6.2f}{r.get('capacity_need_grid') or 0:>6}{b:>7.3f}"
              f"{g['mean_norm_entropy']:>8.3f}{g['mean_rank_at_90']:>9.1f}{r['features']['mean_response_tokens']:>9.1f}")

    out = d.rstrip("/")
    summary = dict(n_tenants=len(rows), n_used=len(ok), primary=":".join(PRIMARY), correlations=[
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
        ax.set_title(f"H1 primary: rho = {table[0][2]:.2f}, p = {table[0][3]:.3f} (n = {len(ok)})")
        fig.tight_layout()
        fig.savefig(out + "_h1.png", dpi=150)
        print(f"\nsaved {out}_summary.json and {out}_h1.png")
    except ImportError:
        print(f"\nsaved {out}_summary.json (install matplotlib for the plot)")


if __name__ == "__main__":
    main()
