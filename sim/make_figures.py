"""Figures for the M&SOM draft. Run with a Python that has numpy and matplotlib:
    python sim/make_figures.py            (writes figures/fig1..fig4 as PNG and PDF)

Fig 1  optimal hand-off count vs theta_w (Proposition 1) with the estimated theta_w of each agent
Fig 2  control portfolio as hand-off cost H and the fixed cost of verification vary (Proposition 3)
Fig 3  escalation rate and cost of an average-wait rule vs the system optimum (Proposition 4)
Fig 4  what a misleading message does: transfer rate, and the two channels (Section 5)

Palette: reference palette of the dataviz skill, validated with its script (categorical slots 1-2 pass; slots 1-3 pass all-pairs;
the ordinal blue ramp passes). Illustrative costs are stated in each caption.
"""
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import table4_two_component as t4
import sim_capacity3 as sc

OUT = ROOT / "figures"; OUT.mkdir(exist_ok=True)
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#5598e7", "#256abf", "#104281"]   # ordinal blue, validated
NAME = {"deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Claude Sonnet 5.5"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.facecolor": SURF,
                     "figure.facecolor": SURF, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "hatch.linewidth": 0.8})


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, facecolor=SURF, bbox_inches="tight")
    fig.savefig(OUT / f"{name}.pdf", facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 1
def fig1():
    T = json.load(open(ROOT / "sim/table4_two_component.json"))
    tw = np.round(np.arange(0.01, 0.501, 0.005), 4)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for F, col in ((60.0, BLUE), (100.0, ORANGE)):
        y = np.array([min(t4.n_star_new(float(x), 0.0, F), 12) for x in tw], dtype=float)
        ax.step(tw, y, where="post", color=col, lw=2, solid_capstyle="round")
    ax.text(0.205, 2.35, "F = 60", color=INK2, fontsize=8.5, ha="left", va="bottom")
    ax.text(0.19, 0.95, "F = 100", color=INK2, fontsize=8.5, ha="left", va="top")
    ax.text(0.565, 0.35, "N* is capped at 12 in the plot", color=INK2, fontsize=7.5, ha="right", va="bottom")
    # estimated theta_w of each agent (misleading message): interval from the two splits
    bands = []
    for m in ("sonnet55", "deepseek", "gpt61terra"):
        d = T[m]["misleading"]
        lo, hi = sorted([d["theta_w"], d["thm_w"]]); lo, hi = max(lo, 0.0), max(hi, 0.0)
        bands.append((m, lo, hi))
    ymax = 12.6
    for i, (m, lo, hi) in enumerate(bands):
        ycen = ymax - 0.7 - 1.15 * i
        ax.plot([lo, hi], [ycen, ycen], color=INK2, lw=2.2, solid_capstyle="round")
        ax.plot([lo], [ycen], "o", color=INK2, ms=4.5, mec=SURF, mew=1.2)
        ax.plot([hi], [ycen], "o", color=INK2, ms=4.5, mec=SURF, mew=1.2)
        lab = f"{NAME[m]}: θ$_w$ {lo:.2f}–{hi:.2f}" if hi - lo > 0.015 else f"{NAME[m]}: θ$_w$ ≈ {0.5 * (lo + hi):.2f}"
        if m == "gpt61terra": lab = f"{NAME[m]}: θ$_w$ ≈ 0 (no rule)"
        ax.text(hi + 0.012, ycen, lab, va="center", fontsize=8, color=INK2)
    ax.set_xlim(-0.012, 0.57); ax.set_ylim(0, ymax)
    ax.set_xlabel("Probability that an error leads to a wrong output (θ$_w$)")
    ax.set_ylabel("Hand off at the N-th error (N*)")
    ax.set_yticks(range(0, 13, 2))
    ax.set_title("The firm's count threshold falls as errors become more harmful", loc="left", fontsize=10, color=INK, pad=10)
    save(fig, "fig1_threshold")


# ---------------------------------------------------------------- Figure 2
def portfolio_grid(tw, th, Ks, Hs, Fu=100.0, Fd=30.0, dbar=0.8):
    import chain_selftransfer as ch
    Pn, an, zn, ns = ch.table(tw, th)
    Fv = dbar * Fd + (1 - dbar) * Fu
    grid = []
    for Kfix in Ks:
        row = []
        for Hc in Hs:
            best = None
            for tag, F_, add in (("", Fu, 0.0), ("V", Fv, Kfix)):
                cs = [an[i] + F_ * zn[i] + Pn[i] * Hc + add for i in range(len(ns))]
                i = int(np.argmin(cs)); n = ns[i]
                typ = "E" if n == 0 else ("N" if n == ch.NINF else "C")
                if best is None or cs[i] < best[0]: best = (cs[i], typ, tag == "V")
            row.append(best[1:])
        grid.append(row)
    return grid


def fig2():
    tw = 0.12
    Ks = [0.5, 1, 2, 4, 6, 10]
    Hs = [10, 20, 30, 40, 60, 80, 100, 150, 300]
    COL = {"E": BLUE, "C": ORANGE, "N": AQUA}
    fig, axs = plt.subplots(1, 2, figsize=(11.2, 3.7), gridspec_kw={"wspace": 0.12}, sharey=True)
    grids = {}
    for ax, th, ttl in zip(axs, (0.0, 0.5), ("(a) no self-transfer ($\\theta_h = 0$)", "(b) frequent self-transfer ($\\theta_h = 0.5$)")):
        grid = portfolio_grid(tw, th, Ks, Hs); grids[th] = grid
        for iK, row in enumerate(grid):
            for iH, (typ, v) in enumerate(row):
                ax.add_patch(Rectangle((iH + 0.03, iK + 0.03), 0.94, 0.94, facecolor=COL[typ], edgecolor=SURF, lw=0))
                if v: ax.add_patch(Rectangle((iH + 0.03, iK + 0.03), 0.94, 0.94, facecolor="none", edgecolor=SURF, lw=0, hatch="////"))
                lab = typ + ("+V" if v else "")
                ax.text(iH + 0.5, iK + 0.5, lab, ha="center", va="center", fontsize=8, color="#ffffff" if typ != "N" else "#0b0b0b",
                        fontweight="bold", bbox=dict(boxstyle="round,pad=0.12", fc=COL[typ], ec="none"))
        ax.set_xlim(0, len(Hs)); ax.set_ylim(0, len(Ks)); ax.invert_yaxis()
        ax.set_xticks([i + 0.5 for i in range(len(Hs))]); ax.set_xticklabels([str(h) for h in Hs])
        ax.set_yticks([i + 0.5 for i in range(len(Ks))]); ax.set_yticklabels([f"{k:g}" for k in Ks])
        ax.grid(False)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(length=0)
        ax.set_xlabel("Cost of handing the task to a person (H)")
        ax.set_title(ttl, loc="left", fontsize=9.5, pad=8)
    axs[0].set_ylabel("Fixed cost of output\nverification (K)")
    from matplotlib.patches import Patch
    hs = [Patch(fc=BLUE, label="E  always hand off"), Patch(fc=ORANGE, label="C  count rule"), Patch(fc=AQUA, label="N  never hand off"),
          Patch(fc=SURF, ec=INK2, hatch="////", label="+V  verify outputs")]
    fig.legend(handles=hs, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.07), fontsize=8, handlelength=1.4, columnspacing=1.4)
    same = all(grids[0.0][i][j] == grids[0.5][i][j] for i in range(len(Ks)) for j in range(len(Hs)))
    ndiff = sum(grids[0.0][i][j] != grids[0.5][i][j] for i in range(len(Ks)) for j in range(len(Hs)))
    save(fig, "fig2_portfolio")
    import chain_selftransfer as ch
    nv = {str(th): int(sum(v for row in g for (_, v) in row)) for th, g in grids.items()}
    zinf = {str(th): float(ch.quantities(ch.NINF, tw, th)[1]) for th in (0.0, 0.5)}
    return dict(identical=bool(same), n_cells=len(Ks) * len(Hs), n_different=int(ndiff), n_with_verification=nv, z_inf=zinf)


# ---------------------------------------------------------------- Figure 3
def fig3():
    import chain_selftransfer as ch
    tw, th, F, h, om = 0.12, 0.05, 100.0, 20.0, 10.0
    Lams = np.arange(0.5, 6.01, 0.25)

    def losses(Fv, c_, grid=2501):
        Pn, an, zn, ns = ch.table(tw, th)
        Hh = sc.Hull(Pn, an + Fv * zn)
        out = []
        for L in Lams:
            r = sc.solve(Hh, sc.Queue(c_, 1.0 / c_, 1, 1, L, include_service=(c_ == 1 and False)), h, om, grid=grid)
            out.append((r, 100 * (r["cost_dec"] - r["cost_sys"]) / r["cost_sys"]))
        return out
    Pn, an, zn, ns = ch.table(tw, th)
    Hh = sc.Hull(Pn, an + F * zn)
    P_sys, P_dec = [], []
    for L in Lams:
        r = sc.solve(Hh, sc.Queue(1, 1.0, 1, 1, L, include_service=False), h, om, grid=4001)
        P_sys.append(r["P_sys"]); P_dec.append(r["P_dec"])
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.5), gridspec_kw={"wspace": 0.28})
    ax = axs[0]
    ax.plot(Lams, P_dec, color=ORANGE, lw=2); ax.plot(Lams, P_sys, color=BLUE, lw=2)
    ax.text(Lams[-1] + 0.06, P_dec[-1] + 0.012, "average-wait\nrule", color=INK2, fontsize=8, va="center")
    ax.text(Lams[-1] + 0.06, P_sys[-1] - 0.025, "system\noptimum", color=INK2, fontsize=8, va="center")
    ax.set_xlim(0.5, 7.6); ax.set_ylim(0, max(P_dec) * 1.15)
    ax.set_xlabel("Task arrival rate (one reviewer, service rate 1)"); ax.set_ylabel("Share of tasks handed to a person")
    ax.set_title("(a) Average-wait rules hand off too many tasks", loc="left", fontsize=9.5, pad=8)
    ax = axs[1]
    res = {}
    for c_, col in zip((1, 2, 5, 10), RAMP):
        ls = np.array([x[1] for x in losses(F, c_, 2001)]); res[c_] = ls
        ax.plot(Lams, ls, color=col, lw=2)
        ax.text(Lams[-1] + 0.06, ls[-1], f"{c_} reviewer" + ("s" if c_ > 1 else ""), color=INK2, fontsize=8, va="center")
    ax.set_xlim(0.5, 7.6); ax.set_ylim(0, None)
    ax.set_xlabel("Task arrival rate (total reviewer capacity 1)"); ax.set_ylabel("Extra cost of the average-wait rule (%)")
    ax.set_title("(b) Pooling reviewers tends to enlarge the loss", loc="left", fontsize=9.5, pad=8)
    save(fig, "fig3_average_wait")
    hi = Lams >= 2
    res200 = {c_: np.array([x[1] for x in losses(200.0, c_, 2001)]) for c_ in (1, 2, 5, 10)}
    return dict(params=dict(theta_w=tw, theta_h=th, F=F, h=h, omega=om),
                mean_loss_lam_ge_2={str(c_): float(v[hi].mean()) for c_, v in res.items()},
                max_loss={str(c_): float(v.max()) for c_, v in res.items()},
                share_exceeding_one_reviewer={str(c_): float((res[c_][hi] > res[1][hi]).mean()) for c_ in (2, 5, 10)},
                max_loss_F200={str(c_): float(v.max()) for c_, v in res200.items()})


# ---------------------------------------------------------------- Figure 4
def fig4():
    T = json.load(open(ROOT / "sim/table4_two_component.json"))
    agents = ["deepseek", "gpt61terra", "sonnet55"]
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.6), gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.5})
    ax = axs[0]
    y = np.arange(len(agents)); bh = 0.34
    for j, (key, col, lab) in enumerate((("c", BLUE, "no injected error"), ("m", ORANGE, "misleading message"))):
        vals = []
        for m in agents:
            r = T[m]; pc = r["ptr_ctrl"]; pm_ = pc + r["misleading"]["d_transfer"]
            vals.append(pc if key == "c" else pm_)
        yy = y + (j - 0.5) * (bh + 0.04)
        ax.barh(yy, vals, height=bh, color=col, edgecolor=SURF, linewidth=1.2)
        for yv, v in zip(yy, vals): ax.text(v + 0.012, yv, f"{v:.2f}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([NAME[m] for m in agents]); ax.invert_yaxis()
    ax.set_xlim(0, 1.0); ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch as _P
    ax.legend(handles=[_P(fc=BLUE, label="no injected error"), _P(fc=ORANGE, label="misleading message")], loc="upper center",
              bbox_to_anchor=(0.45, -0.17), ncol=2, fontsize=8, handlelength=1.2, columnspacing=1.2)
    ax.set_xlabel("Share of runs in which the agent transfers the task to a person")
    ax.set_title("(a) A misleading message sends work to people", loc="left", fontsize=9.5, pad=8)
    ax = axs[1]
    rows = []
    for m in agents:
        d = T[m]["misleading"]
        rows.append((m, "h", d["thm_h"], d["thm_h_ci"], d["theta_h"]))
        rows.append((m, "w", d["thm_w"], d["thm_w_ci"], d["theta_w"]))
    ypos = []
    yy = 0
    for i, (m, ch, est, ci, add) in enumerate(rows):
        if ch == "h" and i > 0: yy += 0.55
        ypos.append(yy); yy += 1.0
    for (m, ch, est, ci, add), yv in zip(rows, ypos):
        col = BLUE if ch == "h" else ORANGE
        ax.plot([ci[0], ci[1]], [yv, yv], color=col, lw=2.2, solid_capstyle="round")
        ax.plot([est], [yv], "o", color=col, ms=6.5, mec=SURF, mew=1.4)
        ax.plot([add], [yv], "D", mfc=SURF, mec=col, ms=5.2, mew=1.4)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks([(ypos[2 * i] + ypos[2 * i + 1]) / 2 for i in range(len(agents))])
    ax.set_yticklabels([NAME[m] for m in agents]); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
    ax.set_xlim(-0.2, 0.75)
    ax.set_xlabel("Probability that a misleading message leads to … (θ)")
    ax.set_title("(b) Self-transfer, not wrong output, for two of three agents", loc="left", fontsize=9.5, pad=8)
    # legend
    from matplotlib.lines import Line2D
    lh = [Line2D([0], [0], color=BLUE, lw=2.2, label="agent transfers the task (θ$_h$)"),
          Line2D([0], [0], color=ORANGE, lw=2.2, label="task ends with a wrong output (θ$_w$)"),
          Line2D([0], [0], marker="o", ls="", color=INK2, ms=6, label="model-consistent split, 95% interval"),
          Line2D([0], [0], marker="D", ls="", mfc=SURF, mec=INK2, ms=5, label="additive split")]
    ax.legend(handles=lh, loc="upper center", bbox_to_anchor=(0.42, -0.2), ncol=2, fontsize=7.8, handlelength=1.6, columnspacing=1.0)
    save(fig, "fig4_two_channels")


if __name__ == "__main__":
    fig1()
    n2 = fig2()
    n3 = fig3()
    fig4()
    (OUT / "figure_numbers.json").write_text(json.dumps(dict(fig2=n2, fig3=n3), indent=1))
    print("figures written to", OUT)
    print("fig2:", n2)
    print("fig3 mean loss (arrival rate >= 2):", {k: round(v, 1) for k, v in n3["mean_loss_lam_ge_2"].items()}, "| max:", {k: round(v, 1) for k, v in n3["max_loss"].items()},
          "| share above 1 reviewer:", {k: round(v, 2) for k, v in n3["share_exceeding_one_reviewer"].items()}, "| max at F=200:", {k: round(v, 1) for k, v in n3["max_loss_F200"].items()})
