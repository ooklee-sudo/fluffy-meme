"""Combine bench/API results into the quantities of the sourcing model.

Per task t and option j (local quant b, or cloud API):
  q_j      accuracy (fraction of fully correct items)
  c_j      cost per request, USD
             local = energy_kWh * electricity_price + latency * capex_per_busy_second
             API   = tokens * price
  c_j/q_j  cost per correct answer
  F        fixed set-up cost of going local (engineering hours, hardware not yet owned, ...)
  n*       break-even request volume:  F / (c_api - c_local)   (cost only)
           and with value v per correct answer:  F / [(v q_l - c_l) - (v q_a - c_a)]  (net benefit)
  PII/req  personal-data entities leaving the firm per request under the API option;
           with --pii-loss-usd (= lambda*L per entity) the API cost becomes c_a + lambda*L*PII/req

  python -m quant_cost.analyze --api api_qwen_qwen-2.5-72b-instruct
"""
import argparse
import csv
import glob
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

S_PER_YEAR = 365 * 24 * 3600


def load(dir_):
    out = []
    for p in sorted(glob.glob(os.path.join(dir_, "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def local_cost(t, a):
    """USD per request for a local run summary `t` (one task)."""
    j = t["energy_marginal_j_per_req"] if a.marginal_energy else t["energy_total_j_per_req"]
    energy = j / 3.6e6 * a.elec_usd_kwh
    capex = t["latency_mean_s"] * a.hw_usd / (a.life_years * S_PER_YEAR * a.utilization)
    return energy + capex, energy, capex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/quant_cost")
    ap.add_argument("--api", help="label of the cloud baseline result (default: first API result found)")
    ap.add_argument("--elec-usd-kwh", type=float, default=0.12)
    ap.add_argument("--hw-usd", type=float, default=1500.0, help="laptop price")
    ap.add_argument("--life-years", type=float, default=3.0)
    ap.add_argument("--utilization", type=float, default=0.25,
                    help="share of the laptop's lifetime available for this workload")
    ap.add_argument("--setup-usd", type=float, default=2000.0, help="fixed cost F of building the local pipeline")
    ap.add_argument("--value-usd", type=float, default=0.05, help="value v of one correct answer, USD")
    ap.add_argument("--pii-loss-usd", type=float, default=0.0,
                    help="expected privacy loss (lambda*L) per PII entity sent to the API, USD; 0 = ignore privacy")
    ap.add_argument("--marginal-energy", action="store_true", help="use energy above idle instead of total")
    ap.add_argument("--out", default="results/quant_cost")
    a = ap.parse_args()

    runs = load(a.dir)
    local = [r for r in runs if r["meta"]["kind"] == "local"]
    apis = [r for r in runs if r["meta"]["kind"] == "api"]
    if not local or not apis:
        raise SystemExit("need at least one local and one API result in " + a.dir)
    api = next((r for r in apis if r["meta"]["label"] == a.api), apis[0]) if a.api else apis[0]
    local.sort(key=lambda r: r["meta"].get("nominal_bits") or 99)

    rows = []
    for t in api["tasks"]:
        at = api["tasks"][t]
        c_a, q_a, pii = at["cost_usd_per_req"], at["acc"], at["pii_entities_sent_per_req"]
        rows.append({"task": t, "option": api["meta"]["label"], "bits": "", "acc": q_a, "acc_lo": at["acc_ci95"][0],
                     "acc_hi": at["acc_ci95"][1], "lat_s": at["latency_mean_s"], "cost_per_req": c_a,
                     "cost_per_correct": c_a / q_a if q_a else float("inf"), "pii_per_req": pii,
                     "n_star_cost": "", "n_star_value": ""})
        for r in local:
            if t not in r["tasks"]:
                continue
            lt = r["tasks"][t]
            c_l, e, cap = local_cost(lt, a)
            q_l = lt["acc"]
            c_a_eff = c_a + a.pii_loss_usd * pii  # API cost incl. expected privacy loss
            d_cost = c_a_eff - c_l
            d_val = (a.value_usd * q_l - c_l) - (a.value_usd * q_a - c_a_eff)
            rows.append({
                "task": t, "option": r["meta"]["label"], "bits": r["meta"].get("nominal_bits") or "", "backend": r["meta"].get("backend", "llama.cpp"),
                "acc": q_l, "acc_lo": lt["acc_ci95"][0], "acc_hi": lt["acc_ci95"][1],
                "lat_s": lt["latency_mean_s"], "cost_per_req": c_l, "energy_usd": e, "capex_usd": cap,
                "cost_per_correct": c_l / q_l if q_l else float("inf"), "pii_per_req": 0.0,
                "n_star_cost": a.setup_usd / d_cost if d_cost > 0 else "never",
                "n_star_value": a.setup_usd / d_val if d_val > 0 else "never"})

    os.makedirs(a.out, exist_ok=True)
    cols = ["task", "option", "backend", "bits", "acc", "acc_lo", "acc_hi", "lat_s", "cost_per_req", "energy_usd",
            "capex_usd", "cost_per_correct", "pii_per_req", "n_star_cost", "n_star_value"]
    with open(os.path.join(a.out, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"{'task':8s} {'option':38s} {'bits':>5s} {'acc':>6s} {'$/1k req':>9s} {'$/1k correct':>12s} "
          f"{'n*(cost)':>10s} {'n*(value)':>10s}")
    for r in rows:
        f_ = lambda x: f"{x:10.0f}" if isinstance(x, float) else f"{x:>10s}"  # noqa: E731
        print(f"{r['task']:8s} {r['option'][:38]:38s} {str(r['bits']):>5s} {r['acc']:6.3f} "
              f"{1000*r['cost_per_req']:9.4f} {1000*r['cost_per_correct']:12.4f} "
              f"{f_(r['n_star_cost'])} {f_(r['n_star_value'])}")

    # ---- figures: accuracy vs bits (q_l(b)), cost per correct answer vs bits
    tasks = list(api["tasks"])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for t in tasks:
        pts = [(r["bits"], r["acc"], r["acc_lo"], r["acc_hi"], r["cost_per_correct"]) for r in rows
               if r["task"] == t and r["bits"] != ""]
        pts.sort()
        if not pts:
            continue
        b = [p[0] for p in pts]
        line, = ax[0].plot(b, [p[1] for p in pts], "o-", label=t)
        ax[0].fill_between(b, [p[2] for p in pts], [p[3] for p in pts], alpha=0.15, color=line.get_color())
        ax[0].axhline(api["tasks"][t]["acc"], ls=":", color=line.get_color())
        ax[1].plot(b, [1000 * p[4] for p in pts], "o-", color=line.get_color(), label=t)
        ax[1].axhline(1000 * api["tasks"][t]["cost_usd_per_req"] / max(api["tasks"][t]["acc"], 1e-9),
                      ls=":", color=line.get_color())
    ax[0].set(xlabel="nominal bits per weight", ylabel="accuracy",
              title="q_l(b)   (dotted = cloud API)")
    ax[1].set(xlabel="nominal bits per weight", ylabel="USD per 1000 correct answers", yscale="log",
              title="Cost per correct answer   (dotted = cloud API)")
    ax[0].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "quant_curves.png"), dpi=150)

    # ---- figure: accuracy vs memory footprint (which model size/quant uses a fixed VRAM budget best?)
    fig2, ax2 = plt.subplots(1, len(tasks), figsize=(4.2 * len(tasks), 3.8), squeeze=False)
    for k, t in enumerate(tasks):
        by_size = {}
        for r in local:
            if t in r["tasks"]:
                by_size.setdefault(r["meta"].get("params_b") or 0, []).append(
                    (r["meta"]["file_gib"], r["tasks"][t]["acc"]))
        for size, pts in sorted(by_size.items()):
            pts.sort()
            ax2[0][k].plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"{size:g}B")
        ax2[0][k].axhline(api["tasks"][t]["acc"], ls=":", color="gray")
        ax2[0][k].set(title=t, xlabel="model file size (GiB)", ylabel="accuracy")
    ax2[0][0].legend()
    fig2.tight_layout()
    fig2.savefig(os.path.join(a.out, "memory_frontier.png"), dpi=150)
    print("wrote", os.path.join(a.out, "summary.csv"), "quant_curves.png and memory_frontier.png")


if __name__ == "__main__":
    main()
