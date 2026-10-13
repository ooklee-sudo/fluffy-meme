"""Collapse results/sens2_summary.json into table rows and a range figure (used by the manuscript)."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")


def stationary_mean_lambda(P, lam):
    P = np.array(P)
    w, v = np.linalg.eig(P.T)
    pi = np.real(v[:, np.argmin(abs(w - 1))]); pi /= pi.sum()
    return float(pi @ np.array(lam))


def load():
    d = json.load(open(os.path.join(R, "sens2_summary.json")))["scenarios"]
    rows = []
    for n, v in d.items():
        runs = [v[k]["models"]["bertrand"] for k in sorted(v)]
        b0 = v["0"]
        c, s = b0["models"]["cartel"], b0["models"]["share"]
        prm = b0["params"]
        key = lambda r: (round(r["mean_capacity"], 0), round(r["avg_price"], 2))
        row = dict(
            name=n, n_eq=len(set(key(r) for r in runs)), all_converged=all(r["converged"] for r in runs),
            n_unconverged=sum(not r["converged"] for r in runs),
            mean_lambda=stationary_mean_lambda(prm["P_lam"], prm["lam"]),
            cartel_cap=c["mean_capacity"], contest_cap=s["mean_capacity"],
            cartel_price=c["avg_price"], cartel_profit=c["profit_total"], contest_profit=s["profit_total"],
            checks=b0["checks"],
        )
        for k in ("avg_price", "profit_total", "consumer_surplus", "mean_capacity", "excess_capacity"):
            row[k] = (min(r[k] for r in runs), max(r[k] for r in runs))
        # welfare in the two extreme (by capacity) equilibria
        lo = min(runs, key=lambda r: r["mean_capacity"]); hi = max(runs, key=lambda r: r["mean_capacity"])
        row["welfare_lo"] = lo["profit_total"] + lo["consumer_surplus"]
        row["welfare_hi"] = hi["profit_total"] + hi["consumer_surplus"]
        row["lo"], row["hi"] = lo, hi
        rows.append(row)
    return rows


def figure(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = list(rows)
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for i, r in enumerate(rows[::-1]):
        lo, hi = r["mean_capacity"]
        ax.plot([lo, hi], [i, i], color="#3b6ea8", lw=3, alpha=.6)
        ax.plot([lo, hi], [i, i], "o", color="#3b6ea8", ms=7, mfc="#3b6ea8", mec="white", mew=.8,
                label="Bertrand MPE (equilibria found)" if i == 0 else None)
        ax.plot(r["cartel_cap"], i, "D", color="#c9733a", ms=5, label="Joint-profit cartel" if i == 0 else None)
        ax.plot(r["contest_cap"], i, "s", color="#6e6e6e", ms=5, label="Market-share contest" if i == 0 else None)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"].replace("rho=", "ρ=").replace("beta=", "β=").replace("fc ", "FC ").replace("mc=", "c=") for r in rows[::-1]], fontsize=8)
    ax.set_xlabel("Mean installed capacity, κ(m_A + m_B), requests per period")
    ax.axvline(45, color="#bbbbbb", lw=.8, ls=":")
    ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(R, "sensitivity_capacity.png"), dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    rows = load()
    figure(rows)
    json.dump(rows, open(os.path.join(R, "sens2_rows.json"), "w"), indent=1)
    for r in rows:
        print(f"{r['name']:28s} lam={r['mean_lambda']:.1f} eq={r['n_eq']} unconv={r['n_unconverged']} "
              f"cap={r['mean_capacity'][0]:.1f}-{r['mean_capacity'][1]:.1f} cart={r['cartel_cap']:.1f} cont={r['contest_cap']:.1f} "
              f"W_lo={r['welfare_lo']:.2f} W_hi={r['welfare_hi']:.2f} prof_ratio={r['profit_total'][0]/r['cartel_profit']:.2f}-{r['profit_total'][1]/r['cartel_profit']:.2f}")
