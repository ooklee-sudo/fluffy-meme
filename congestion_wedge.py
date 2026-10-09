"""Congestion wedge and a 'productivity paradox' experiment (quasi-static model of theory_check.py).

Per unit time, with phase probabilities pi_k:
  Q  = sum pi_k lam_k                     measured throughput (requests served; what usage statistics show)
  V  = sum pi_k P(lam_k - lam_k^2/(2 Lam_k))   gross value users obtain
  Dc = sum pi_k lam_k d(lam_k)            time users lose waiting -- not in revenue, output or input statistics
  W  = V - Dc                             welfare
  wedge share = Dc / V                    the part of created value dissipated in queues
Adoption a = mean demand potential / capacity.  Policies: no price (consumer-plan style), best flat price,
phase-dependent first-best (Pigouvian) prices.  Poisson = same mean potential, no phase variation.
Usage: python congestion_wedge.py DATA_DIR [OUT.md]"""
import sys

import numpy as np

import theory_check as th

P = th.P


def metrics(prices, Lams, pis, c):
    Q = V = Dc = 0.0
    for k in range(len(Lams)):
        l = th.eq_rate(prices[k], Lams[k], c)
        Q += pis[k] * l
        V += pis[k] * P * (l - l * l / (2 * Lams[k]))
        Dc += pis[k] * l * th.sojourn(l, c)
    return Q, V, Dc


def best_flat(Lams, pis, c):
    return max((sum(pis[k] * th.w_phase(th.eq_rate(p, Lams[k], c), Lams[k], c) for k in range(len(Lams))), p)
               for p in np.linspace(0, P, 201))[1]


def first_best_prices(Lams, c):
    from theory_props import toll_at
    return [toll_at(th.first_best(L, c), c) for L in Lams]


def row(label, prices, Lams, pis, c):
    Q, V, Dc = metrics(prices, Lams, pis, c)
    return [label, f"{Q / c:.2f}", f"{V / c:.2f}", f"{Dc / c:.2f}", f"{(V - Dc) / c:.2f}", f"{100 * Dc / V:.0f}%"]


def run(name, lam_s, G, c, md):
    from trace_calibration import table
    pi = th_pi = None
    import trace_pricing as tp
    pi = tp.stationary(G)
    rel_trace = lam_s / (pi @ lam_s)
    md.append(f"## {name} (c={c})\n")
    # --- adoption sweep
    rows = []
    for a in (0.5, 0.8, 1.0, 1.2, 1.4, 1.8, 2.4):
        for lab, rel, pis in (("bursty", rel_trace, pi), ("Poisson", np.array([1.0]), np.array([1.0]))):
            Lams = a * c * rel
            none = row(f"{lab}, no price", [0.0] * len(Lams), Lams, pis, c)
            bf = best_flat(Lams, pis, c)
            flat = row(f"{lab}, best flat (p={bf:.1f})", [bf] * len(Lams), Lams, pis, c)
            fb = row(f"{lab}, phase-optimal", first_best_prices(Lams, c), Lams, pis, c)
            rows += [[a] + none, [""] + flat, [""] + fb]
    md.append("### Adoption sweep (per unit of capacity; a = mean demand potential / capacity)\n")
    md.append(table(rows, ["a", "scenario", "throughput Q/c", "gross value V/c", "waiting cost Dc/c", "welfare W/c", "Dc/V"]))
    # --- dispersion sweep at a = 1.4, no price and best flat
    rows = []
    for spread in (0.0, 0.25, 0.5, 0.75, 1.0):
        rel = 1 + spread * (rel_trace - 1)
        Lams = 1.4 * c * np.maximum(rel, 0.02)
        Q, V, Dc = metrics([0.0] * len(Lams), Lams, pi, c)
        bf = best_flat(Lams, pi, c)
        Q2, V2, Dc2 = metrics([bf] * len(Lams), Lams, pi, c)
        rows.append([spread, f"{100 * Dc / V:.1f}%", f"{(V - Dc) / c:.2f}", f"{100 * Dc2 / V2:.1f}%", f"{(V2 - Dc2) / c:.2f}"])
    md.append("\n### Dispersion sweep at a = 1.4 (0 = Poisson, 1 = fitted trace)\n")
    md.append(table(rows, ["spread", "Dc/V no price", "W/c no price", "Dc/V best flat", "W/c best flat"]))
    md.append("")
    print("\n".join(md[-12:]), flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = args[0]
    out = args[1] if len(args) > 1 else "results/congestion_wedge.md"
    md = ["# Congestion wedge: measured throughput vs. welfare\n"]
    for name, sc in (("Code trace", th.scenario_code), ("Conversation trace", th.scenario_conv)):
        lam_s, G, c = sc(data)
        run(name, lam_s, G, c, md)
        open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
