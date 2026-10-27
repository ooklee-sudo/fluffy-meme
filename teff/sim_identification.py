"""Simulation checks for the theory added in the revision.

S1  scale confound: if the context multiplies the logits by a, T_eff -> T/a.
S2  interval coverage / width of T_eff with 6, 36 and 240 choices.
S3  behaviour near saturation; an interval-based identification rule versus the
    fixed 0.999 threshold.
S4  stylised escape model: an interior accuracy peak exists iff
    Delta < (K-2) g.
Writes results/sim_identification.json.
"""
import json
import os

import numpy as np

from teff_core import GRID, loglik_grid, softmax, teff_from_ll

rng = np.random.default_rng(20260101)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
res = {}


def ref_logits(n, K, spread, top_gap=0.0):
    """Random reference logits; top_gap raises candidate 0 (saturation)."""
    v = rng.normal(0, spread, size=(n, K))
    v[:, 0] += top_gap
    return v


def draw(Z, T):
    P = softmax(Z, T)
    return np.array([rng.choice(P.shape[1], p=p) for p in P])


# S1 ---------------------------------------------------------------------
rows = []
K, n = 12, 600
for a in (0.5, 1.0, 2.0):
    for T in (0.8, 2.0):
        V = ref_logits(n, K, 2.0)
        Z = a * V                       # context only rescales preferences
        y = draw(Z, T)
        e = teff_from_ll(loglik_grid(V, y))
        # ordering change of the same size: shuffle half of the candidates
        Zo = V.copy()
        perm = rng.permutation(K)
        Zo[:, :] = V[:, perm]
        yo = draw(Zo, T)
        eo = teff_from_ll(loglik_grid(V, yo))
        rows.append(dict(a=a, T=T, T_over_a=T / a, teff_scale_only=e["teff"],
                         teff_ordering_only=eo["teff"],
                         ll_scale=float(loglik_grid(V, y).max() / n),
                         ll_order=float(loglik_grid(V, yo).max() / n)))
res["S1_scale_confound"] = rows

# S2 ---------------------------------------------------------------------
S2 = []
K, spread = 12, 2.0
for tau in (0.5, 1.0, 2.0, 4.0):
    for n_ch in (6, 36, 240):
        cover, widths, ratios, bias = 0, [], [], []
        R = 400
        for _ in range(R):
            V = ref_logits(n_ch, K, spread)
            y = draw(V, tau)
            e = teff_from_ll(loglik_grid(V, y))
            cover += e["lo"] <= tau <= e["hi"]
            widths.append(e["hi"] / e["lo"])
            ratios.append(e["teff"] / tau)
            bias.append(np.log(e["teff"] / tau))
        S2.append(dict(tau=tau, n_choices=n_ch, coverage=cover / R,
                       median_hi_over_lo=float(np.median(widths)),
                       median_ratio=float(np.median(ratios)),
                       iqr_log_ratio=float(np.subtract(*np.percentile(bias, [75, 25])))))
res["S2_interval_properties"] = S2

# S3 ---------------------------------------------------------------------
S3 = []
K, n_ch, tau = 12, 36, 1.0
for top_gap in (0.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0):
    mrp, ratio, covered, ident_thr, ident_int = [], [], [], [], []
    for _ in range(300):
        V = ref_logits(n_ch, K, 1.0, top_gap)
        y = draw(V, tau)
        ll = loglik_grid(V, y)
        e = teff_from_ll(ll)
        pref = softmax(V, 0.8)[np.arange(n_ch), y].mean()   # nominal T = 0.8
        mrp.append(pref)
        covered.append(e["lo"] <= tau <= e["hi"])
        ident_thr.append(pref <= 0.999)
        # interval rule: bounded interval, not at a grid boundary, hi/lo <= 4
        ident_int.append((not e["at_boundary"]) and (not e["open_hi"])
                         and (not e["open_lo"]) and e["hi"] / e["lo"] <= 4.0)
        ratio.append(e["hi"] / e["lo"])
    S3.append(dict(top_gap=top_gap, mean_ref_prob=float(np.mean(mrp)),
                   coverage=float(np.mean(covered)),
                   median_hi_over_lo=float(np.median(ratio)),
                   frac_identified_thr0999=float(np.mean(ident_thr)),
                   frac_identified_interval_rule=float(np.mean(ident_int))))
res["S3_saturation"] = S3

# S4 ---------------------------------------------------------------------
def acc_curve(K, delta, g, Ts):
    D = np.exp(delta / Ts) + 1 + (K - 2) * np.exp(-g / Ts)
    return 1.0 / D


S4 = []
Ts = np.geomspace(0.05, 50, 2000)
for K in (8, 26):
    for g in (0.5, 1.0, 2.0):
        for delta in (1.0, 3.0, 6.0, 12.0, 24.0, 48.0):
            p = acc_curve(K, delta, g, Ts)
            j = int(np.argmax(p))
            interior = 0 < j < len(Ts) - 1
            pred = delta < (K - 2) * g
            S4.append(dict(K=K, g=g, delta=delta, interior_peak=bool(interior),
                           predicted=bool(pred), T_star=float(Ts[j]),
                           p_star=float(p[j]), p_at_Tmax=float(p[-1])))
res["S4_peak_condition"] = S4
agree = np.mean([r["interior_peak"] == r["predicted"] for r in S4])
res["S4_agreement"] = float(agree)

json.dump(res, open(os.path.join(OUT, "sim_identification.json"), "w"), indent=1)
print("S1"); [print(r) for r in rows]
print("S2"); [print(r) for r in S2]
print("S3"); [print(r) for r in S3]
print("S4 agreement", agree)
[print(r) for r in S4 if r["K"] == 26 and r["g"] == 1.0]
