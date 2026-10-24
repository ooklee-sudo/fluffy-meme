"""Builds Tables 2-6, the dominance checks, and Figures 1-2 from the per-run files written by run_experiments.py.

Usage: python analyze.py [--results ../results]
Writes results/tables_simulation.md, results/summary.json, results/figures/Figure_1.{pdf,png}, Figure_2.{pdf,png}.
"""
import argparse, gzip, json, os

import numpy as np

HOURS = [1, 2, 3, 6, 12, 48]
DELTAS = [0.0, 0.25, 0.5, 1.0, 2.0]
rng = np.random.default_rng(12345)


def load(results, name):
    with gzip.open(os.path.join(results, "runs", f"{name}.json.gz"), "rt") as fh:
        rows = json.load(fh)
    out = {}
    for r in rows:
        out.setdefault(r["tag"], {}).setdefault(r["plan"], {})[r["rep"]] = r
    return out


def N_at(a, h):
    return int(np.searchsorted(np.asarray(a), h, side="right"))


def V(a, delta):
    return float(np.exp(-delta * np.asarray(a)).sum()) if len(a) else 0.0


def t50(a):
    return float(a[(len(a) + 1) // 2 - 1]) if len(a) else float("nan")


def cvar(x, q=0.2):
    x = np.sort(np.asarray(x, float))
    k = max(1, int(np.ceil(q * len(x))))
    return float(x[:k].mean())


def boot_ci(d, n=4000):
    d = np.asarray(d, float)
    idx = rng.integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def stats(cell, key):
    """cell = {plan: {rep: row}}; returns paired arrays for reps present in both plans."""
    reps = sorted(set(cell["concentrated"]) & set(cell["distributed"]))
    C = [cell["concentrated"][r]["adopt"] for r in reps]
    D = [cell["distributed"][r]["adopt"] for r in reps]
    return reps, C, D


def fmt_ci(m, ci, d=0):
    return f"{m:.{d}f} [{ci[0]:.{d}f}, {ci[1]:.{d}f}]"


def paired(C, D, fn):
    x = np.array([fn(c) for c in C]); y = np.array([fn(d) for d in D])
    diff = x - y
    return x, y, diff


def dominance(C, D):
    """First-order stochastic dominance of C over D on final adopters (empirical quantiles), and pathwise-in-mean
    dominance E[N(t)] on an hourly grid."""
    fc = np.sort([len(c) for c in C]); fd = np.sort([len(d) for d in D])
    fsd = bool(np.all(fc >= fd))
    grid = np.arange(1, 49)
    mc = np.mean([[N_at(c, h) for h in grid] for c in C], axis=0)
    md = np.mean([[N_at(d, h) for h in grid] for d in D], axis=0)
    return fsd, bool(np.all(mc >= md)), int((mc >= md).sum())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--results", default="../results")
    a = ap.parse_args()
    R = a.results
    os.makedirs(os.path.join(R, "figures"), exist_ok=True)
    md, summary = [], {}

    # ------------------------------------------------------------------ Table 2 (base)
    base = load(R, "base")["base"]
    reps, C, D = stats(base, None)
    md.append(f"## Table 2. Base configuration (beta = 0, equal-link budget, {len(reps)} paired replications)\n")
    md.append("| | Concentrated | Distributed |\n|---|---|---|")
    seeds_d = np.mean([base["distributed"][r]["n_seeds"] for r in reps])
    for h in HOURS:
        md.append(f"| Mean cumulative adopters at {h} h | {np.mean([N_at(c,h) for c in C]):.0f} | {np.mean([N_at(d,h) for d in D]):.0f} |")
    fc = [len(c) for c in C]; fd = [len(d) for d in D]
    md.append(f"| SD of final adopters | {np.std(fc, ddof=1):.0f} | {np.std(fd, ddof=1):.0f} |")
    md.append(f"| Minimum of final adopters | {min(fc)} | {min(fd)} |")
    md.append(f"| CVaR_0.2 (mean of worst 20%) | {cvar(fc):.0f} | {cvar(fd):.0f} |")
    md.append(f"| Mean t50 (h) | {np.nanmean([t50(c) for c in C]):.2f} | {np.nanmean([t50(d) for d in D]):.2f} |")
    md.append(f"| Number of seeds (mean) | 3 | {seeds_d:.0f} |\n")
    x, y, dif = paired(C, D, len)
    ci = boot_ci(dif)
    md.append(f"Paired difference in final adopters: {fmt_ci(dif.mean(), ci)}; concentrated ahead in {int((dif>0).sum())} of {len(reps)} replications.")
    _, _, dt = paired(C, D, t50)
    md.append(f"Paired difference in t50 (concentrated minus distributed): {fmt_ci(np.nanmean(dt), boot_ci(dt[~np.isnan(dt)]), 2)} h.")
    for delta in DELTAS:
        _, _, dv = paired(C, D, lambda z: V(z, delta))
        md.append(f"- Discounted reach, delta = {delta}: C {np.mean([V(c,delta) for c in C]):.1f}, D {np.mean([V(d,delta) for d in D]):.1f}, paired diff {fmt_ci(dv.mean(), boot_ci(dv), 1)}")
    fsd, mean_dom, nh = dominance(C, D)
    md.append(f"- First-order stochastic dominance of concentrated on final adopters (all empirical quantiles): {fsd}")
    md.append(f"- Mean cumulative adopters higher for concentrated at {nh} of 48 hourly points (all hours: {mean_dom})")
    for h in (1, 2):
        ahead = np.mean([N_at(d, h) > N_at(c, h) for c, d in zip(C, D)])
        md.append(f"- Distributed strictly ahead after {h} h in {100*ahead:.0f}% of replications")
    summary["base"] = dict(C=float(np.mean(fc)), D=float(np.mean(fd)), diff=float(dif.mean()), ci=ci, fsd=fsd, mean_dominance=mean_dom,
                           t50_C=float(np.nanmean([t50(c) for c in C])), t50_D=float(np.nanmean([t50(d) for d in D])), seeds_D=float(seeds_d))
    md.append("")

    # ------------------------------------------------------------------ Table 3 (schedulers)
    sch = load(R, "schedulers")
    md.append("## Table 3. Concentrated minus distributed under alternative schedulers (beta = 0, 18:00 injection)\n")
    md.append("| Scheduler | Adopters (C / D) | Ratio C/D | Delta adopters [95% CI] | Delta t50, h [95% CI] | CVaR_0.2 (C / D) |\n|---|---|---|---|---|---|")
    rows = [("Event-driven IPP (proposed)", base)] + [(n, sch[f"sched_{k}"]) for n, k in
            (("Circadian-only IPP", "circadian"), ("Homogeneous Poisson", "hpp"), ("Fixed-period polling", "polling"))]
    sched_sum = {}
    for name, cell in rows:
        reps_, C_, D_ = stats(cell, None)
        fc_ = [len(c) for c in C_]; fd_ = [len(d) for d in D_]
        _, _, dd = paired(C_, D_, len); _, _, dtt = paired(C_, D_, t50)
        md.append(f"| {name} | {np.mean(fc_):.0f} / {np.mean(fd_):.0f} | {np.mean(fc_)/np.mean(fd_):.2f} | {fmt_ci(dd.mean(), boot_ci(dd))} | "
                  f"{fmt_ci(np.nanmean(dtt), boot_ci(dtt[~np.isnan(dtt)]), 2)} | {cvar(fc_):.0f} / {cvar(fd_):.0f} |")
        sched_sum[name] = dict(diff=float(dd.mean()), ratio=float(np.mean(fc_) / np.mean(fd_)), C=float(np.mean(fc_)))
    summary["schedulers"] = sched_sum
    try:
        md.append(f"\nVolume-matching multiplier from pilot runs without a campaign: {json.load(open(os.path.join(R,'volume_multiplier.json')))['multiplier']:.2f}\n")
    except FileNotFoundError:
        pass

    # ------------------------------------------------------------------ Table 4 (injection time)
    inj = load(R, "injection")
    md.append("## Table 4. Effect of injection time\n")
    md.append("| Injection | Scheduler | Adopters (C / D) | Delta adopters [95% CI] | t50, h (C / D) |\n|---|---|---|---|---|")
    for hour in (3, 9, 18):
        for s, label in (("event", "Event-driven IPP"), ("circadian", "Circadian-only")):
            if hour == 18:
                cell = base if s == "event" else sch["sched_circadian"]
                reps_ = sorted(set(cell["concentrated"]) & set(cell["distributed"]))[:20]
                C_ = [cell["concentrated"][r]["adopt"] for r in reps_]; D_ = [cell["distributed"][r]["adopt"] for r in reps_]
            else:
                reps_, C_, D_ = stats(inj[f"inj{hour:02d}_{s}"], None)
            _, _, dd = paired(C_, D_, len)
            md.append(f"| {hour:02d}:00 | {label} | {np.mean([len(c) for c in C_]):.0f} / {np.mean([len(d) for d in D_]):.0f} | {fmt_ci(dd.mean(), boot_ci(dd))} | "
                      f"{np.nanmean([t50(c) for c in C_]):.2f} / {np.nanmean([t50(d) for d in D_]):.2f} |")
    md.append("")

    # ------------------------------------------------------------------ Table 5 (pricing and hybrids)
    pr = load(R, "pricing")
    md.append("## Table 5. Hybrid portfolios (beta = 0)\n")
    md.append("| Pricing C(f) | k | Seeds | Mean adopters (SD) | CVaR_0.2 | V(delta=1/h) | t50 (h) |\n|---|---|---|---|---|---|---|")
    for pname, label in (("equal", "f (equal links)"), ("concave", "f^0.7 (concave)"), ("fixed", "10 + f (fixed fee)")):
        for k in range(4):
            tag = f"price_{pname}_k{k}" if not (k == 3 and pname != "equal") else "price_equal_k3"
            cell = pr[tag]["hybrid"]
            rr = [cell[r] for r in sorted(cell)]
            fin = [len(x["adopt"]) for x in rr]
            md.append(f"| {label if k==0 else ''} | {k} | {np.mean([x['n_seeds'] for x in rr]):.0f} | {np.mean(fin):.0f} ({np.std(fin, ddof=1):.0f}) | {cvar(fin):.0f} | "
                      f"{np.mean([V(x['adopt'],1.0) for x in rr]):.0f} | {np.nanmean([t50(x['adopt']) for x in rr]):.2f} |")
    md.append("")

    # ------------------------------------------------------------------ Table 6 and Figure 2 (beta sweep)
    bt = load(R, "beta")
    if os.path.exists(os.path.join(R, "runs", "beta_obs.json.gz")):
        bt.update(load(R, "beta_obs"))
    if os.path.exists(os.path.join(R, "runs", "beta_fine.json.gz")):
        bt.update(load(R, "beta_fine"))
    md.append("## Table 6. Concentrated vs. distributed seeding by engagement elasticity beta (equal-link budget)\n")
    md.append("| beta | Adopters (C / D) | Delta adopters [95% CI] | P(C > D) | Delta V(delta=1/h) [95% CI] | CVaR_0.2 (C / D) | Adopters at 1 h (C / D) |\n|---|---|---|---|---|---|---|")
    betas = sorted(float(k.split("_")[1]) for k in bt)
    fig = dict(beta=[], d=[], lo=[], hi=[], dv=[], vlo=[], vhi=[])
    beta_sum = {}
    for b in betas:
        reps_, C_, D_ = stats(bt[f"beta_{b:.2f}"], None)
        fc_ = [len(c) for c in C_]; fd_ = [len(d) for d in D_]
        _, _, dd = paired(C_, D_, len); _, _, dv = paired(C_, D_, lambda z: V(z, 1.0))
        cid, civ = boot_ci(dd), boot_ci(dv)
        md.append(f"| {b:.2f} | {np.mean(fc_):.0f} / {np.mean(fd_):.0f} | {fmt_ci(dd.mean(), cid)} | {np.mean(dd > 0):.2f} | {fmt_ci(dv.mean(), civ, 1)} | "
                  f"{cvar(fc_):.0f} / {cvar(fd_):.0f} | {np.mean([N_at(c,1) for c in C_]):.0f} / {np.mean([N_at(d,1) for d in D_]):.0f} |")
        for k_, v_ in zip(("beta", "d", "lo", "hi", "dv", "vlo", "vhi"), (b, dd.mean(), cid[0], cid[1], dv.mean(), civ[0], civ[1])):
            fig[k_].append(v_)
        beta_sum[f"{b:.2f}"] = dict(d=float(dd.mean()), lo=cid[0], hi=cid[1], dv=float(dv.mean()), vlo=civ[0], vhi=civ[1])
    summary["beta"] = beta_sum
    # first-generation approximation (Eq. 2)
    f_c = np.mean([np.mean(base["concentrated"][r]["seed_followers"]) for r in base["concentrated"]])
    R0 = np.mean(fc) / np.mean(fd)
    md.append(f"\nEq. (2) check: R0 = {R0:.2f}, mean followers per concentrated seed f_C = {f_c:.0f}, beta* ~ ln R0 / ln(f_C/10) = {np.log(R0)/np.log(f_c/10):.2f}\n")
    summary["eq2"] = dict(R0=float(R0), f_C=float(f_c), beta_star=float(np.log(R0) / np.log(f_c / 10)))

    open(os.path.join(R, "tables_simulation.md"), "w").write("\n".join(md))
    json.dump(summary, open(os.path.join(R, "summary.json"), "w"), indent=1)
    print("\n".join(md))

    # ------------------------------------------------------------------ figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    grid = np.arange(0, 49)
    fig1, axs = plt.subplots(1, 2, figsize=(8.5, 3.4), sharey=False)
    for ax, (cell, title) in zip(axs, ((base, "(a) No engagement decay ($\\beta=0$)"), (bt["beta_0.30"], "(b) Engagement decay $\\beta=0.3$"))):
        reps_, C_, D_ = stats(cell, None)
        reps_ = reps_[:15]; C_, D_ = C_[:15], D_[:15]
        ax.plot(grid, np.mean([[N_at(c, h) for h in grid] for c in C_], axis=0), "k-", label="Concentrated (3 influencers)")
        ax.plot(grid, np.mean([[N_at(d, h) for h in grid] for d in D_], axis=0), "k--", label="Distributed (ordinary users)")
        ax.set_title(title, fontsize=9); ax.set_xlabel("Hours after injection"); ax.set_ylabel("Mean cumulative adopters")
    axs[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig1.tight_layout()
    for ext, kw in (("pdf", {}), ("png", {"dpi": 400})):
        fig1.savefig(os.path.join(R, "figures", f"Figure_1.{ext}"), **kw)
    fig2, ax = plt.subplots(figsize=(5.5, 3.8))
    b_, d_ = np.array(fig["beta"]), np.array(fig["d"])
    ax.errorbar(b_, d_, yerr=[d_ - np.array(fig["lo"]), np.array(fig["hi"]) - d_], fmt="k-o", ms=4, capsize=3, label="Final adopters (48 h)")
    dv_ = np.array(fig["dv"])
    ax.errorbar(b_ + 0.006, dv_, yerr=[dv_ - np.array(fig["vlo"]), np.array(fig["vhi"]) - dv_], fmt="--s", color="0.45", ms=4, capsize=3,
                label=r"Discounted reach $V(\delta=1/\mathrm{h})$")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel(r"Engagement elasticity $\beta$"); ax.set_ylabel("Concentrated minus distributed"); ax.legend(frameon=False)
    fig2.tight_layout()
    for ext, kw in (("pdf", {}), ("png", {"dpi": 400})):
        fig2.savefig(os.path.join(R, "figures", f"Figure_2.{ext}"), **kw)


if __name__ == "__main__":
    main()
