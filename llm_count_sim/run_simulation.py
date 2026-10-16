"""(b) Offline simulation of H1-H4 with a MockLLM. Run: python run_simulation.py [--n 5000 --reps 20]"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import count_metrics as cm
from evaluate import evaluate_condition
from synthetic_customers import CONDITIONS, MockLLM, make_real

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def main(n, reps, overreact):
    rows, pmfs = [], {}
    for r in range(reps):
        rng = np.random.default_rng(1000 + r)
        real = make_real(n, rng)
        llm = MockLLM(rng, promo_overreact=overreact)
        pi = rng.choice(n, 200, replace=False)
        pilot = (real.y[pi], real.segment[pi])
        for name, fn in CONDITIONS.items():
            ysyn = fn(real, llm, rng, pilot) if name.startswith("D") else fn(real, llm, rng)
            row = evaluate_condition(real.y, real.treat, ysyn, real.treat)
            row.update(cond=name, rep=r)
            rows.append(row)
            if r == 0:
                pmfs[name] = cm.pmf(ysyn)
        if r == 0:
            pmfs["Real"] = cm.pmf(real.y)
            real0 = real.y
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/sim_rows.csv", index=False)

    agg = df.groupby("cond").agg(
        disp_ratio=("syn_disp_ratio", "mean"), zero_frac=("syn_zero_frac", "mean"),
        top10=("syn_top10_share", "mean"), wasserstein=("wasserstein", "mean"), js=("js", "mean"),
        irr_syn=("irr_syn", "mean"), irr_ratio=("irr_ratio", "mean"),
        overdisp_rejected=("ct_p", lambda p: (p < 0.05).mean()),
        best_model=("best_model", lambda s: s.value_counts().idxmax())).round(3)
    real_ref = df[["real_disp_ratio", "real_zero_frac", "real_top10_share", "irr_real"]].mean().round(3)
    agg.to_csv(f"{OUT}/sim_summary.csv")
    json.dump({"real_reference": real_ref.to_dict(), "n": n, "reps": reps, "promo_overreact": overreact},
              open(f"{OUT}/sim_meta.json", "w"), indent=2)
    print("Real reference:", real_ref.to_dict())
    print(agg.to_string())

    # Figures
    colors = {"Real": "#222222", "A direct": "#d95f02", "B daily-sim": "#7570b3",
              "C describe→sample": "#1b9e77", "D hybrid": "#e7298a"}
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    x = np.arange(21)
    for k, p in pmfs.items():
        ax[0].plot(x, p[:21], marker="o", ms=3, lw=2 if k == "Real" else 1.2, color=colors[k], label=k)
    ax[0].set(xlabel="orders in 4 weeks", ylabel="share of customers", title="Count distribution (rep 0)")
    ax[0].legend(frameon=False, fontsize=8)
    conds = list(CONDITIONS)
    g = df.groupby("cond")
    ax[1].bar(conds, [g.get_group(c)["syn_disp_ratio"].mean() for c in conds],
              yerr=[g.get_group(c)["syn_disp_ratio"].std() for c in conds],
              color=[colors[c] for c in conds])
    ax[1].axhline(real_ref["real_disp_ratio"], color="k", ls="--", label=f"real = {real_ref['real_disp_ratio']:.1f}")
    ax[1].axhline(1, color="gray", ls=":", label="Poisson = 1")
    ax[1].set(ylabel="variance / mean", title="Dispersion ratio (mean ± sd, reps)")
    ax[1].tick_params(axis="x", labelrotation=15)
    ax[1].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_distribution_dispersion.png", dpi=140)

    # Sensitivity: promo over-reaction exponent vs IRR bias (condition D)
    fig2, ax2 = plt.subplots(figsize=(5.5, 4))
    exps = [0.5, 1.0, 1.5, 2.0]
    for name in ["A direct", "D hybrid"]:
        irrs = []
        for e in exps:
            vals = []
            for r in range(5):
                rng = np.random.default_rng(5000 + r)
                real = make_real(n, rng)
                llm = MockLLM(rng, promo_overreact=e)
                ys = CONDITIONS[name](real, llm, rng, (real.y[(pi := rng.choice(n, 200, replace=False))], real.segment[pi])) \
                    if name.startswith("D") else CONDITIONS[name](real, llm, rng)
                vals.append(cm.irr(ys, real.treat)[0])
            irrs.append(np.mean(vals))
        ax2.plot(exps, irrs, marker="o", label=name, color=colors[name])
    ax2.axhline(1.25, color="k", ls="--", label="true IRR 1.25")
    ax2.set(xlabel="LLM promo over-reaction exponent", ylabel="estimated IRR", title="H4: promo effect bias")
    ax2.legend(frameon=False)
    fig2.tight_layout()
    fig2.savefig(f"{OUT}/fig_irr_sensitivity.png", dpi=140)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--overreact", type=float, default=1.5, help="MockLLM promo effect exponent (1 = unbiased)")
    a = ap.parse_args()
    main(a.n, a.reps, a.overreact)
