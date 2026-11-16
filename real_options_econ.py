"""Link the measured personalization economics (tt_entropy/ECON_RESULTS.md) to the real-options model of
adapter maintenance (real_options.py): when should a brand's adapter be retrained as its traffic drifts?

Mapping (assumptions, stated in the output):
  - Event = a drift epoch. Measured: a stale LoRA r=1 adapter keeps R = 0.887 of a fresh adapter's gain
    after about 7 weeks (E4). Drift is modeled as Poisson events with mean spacing 7 weeks
    (mu = 52/7 per year), each leaving the adapter at recovery R until it is retrained.
  - C_N = one retraining = 45 GPU-seconds (Phase 2 median). Costs and values are in GPU-seconds.
  - Annual adapter value v = V * lambda * q: V requests per year, q = 0.441 relative gain of a fresh
    adapter (E4 in-period), lambda = GPU-seconds a firm would pay per unit of relative gain per request.
    Lower bound for lambda: a firm that pays RAG-8's extra 39.85 ms per request for its 0.284 gain values a
    unit of gain at >= 0.140 s. Scenarios: 1x, 10x and 100x that bound.
  - rho, g, sigma: the real-options paper's defaults (0.10, 0.20, 0.40).

Outputs, per lambda scenario: the retraining threshold v* (Proposition 2) as a request volume per year, the
share of TWCS brands above it (annual volume = TWCS volume x 6), and the expected yearly maintenance cost
of the optimal threshold policy vs "retrain at every drift epoch" and "never retrain for drift".

Usage: python real_options_econ.py [--pairs tt_entropy/data/twcs_pairs.jsonl] [--mc]
"""
import argparse
import collections
import json
import math
import os

import numpy as np

from real_options import Params, W, beta, k, mc_check, v_star

R_DRIFT, WEEKS, C_N = 0.887, 7.0, 45.0
Q_FRESH = 0.441
LAMBDA_MIN = 0.03985 / 0.284  # GPU-seconds per unit of relative gain per request


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pairs", default="tt_entropy/data/twcs_pairs.jsonl")
    ap.add_argument("--year-factor", type=float, default=6.0, help="TWCS window (about 9 weeks) to one year")
    ap.add_argument("--mc", action="store_true", help="Monte Carlo check of the threshold policy cost")
    ap.add_argument("--out", default="results/real_options_econ.json")
    a = ap.parse_args()

    p = Params(rho=0.10, mu=52 / WEEKS, g=0.20, sigma=0.40, C_N=C_N, C_A=0.0)
    b, kk, vs = beta(p), k(R_DRIFT, p), v_star(R_DRIFT, p)
    print(f"drift events per year mu = {p.mu:.2f}; R = {R_DRIFT}; C_N = {C_N:.0f} GPU-s")
    print(f"beta = {b:.3f}, beta/(beta-1) = {b / (b - 1):.3f}, k(R) = {kk:.5f} years")
    print(f"retraining threshold v* = {vs:,.0f} GPU-s of adapter value per year "
          f"(= {vs / C_N:,.0f} x C_N)\n")

    vols = None
    if os.path.exists(a.pairs):
        c = collections.Counter(json.loads(l)["tenant"] for l in open(a.pairs))
        vols = np.array(list(c.values()), float) * a.year_factor
    rows = []
    print(f"{'lambda (s per unit gain)':<26}{'value/request (ms)':>19}{'threshold V* (req/yr)':>23}"
          f"{'brands above':>14}{'cost: optimal':>15}{'retrain always':>16}{'never':>10}")
    for mult in (1, 10, 100):
        lam = LAMBDA_MIN * mult
        per_req = lam * Q_FRESH
        V_star = vs / per_req
        row = dict(lambda_s=lam, value_per_request_s=per_req, threshold_requests_per_year=V_star)
        cells = ["", "", "", ""]
        if vols is not None:
            v = vols * per_req
            # expected discounted cost per drift epoch x epochs per year (approximate yearly cost)
            opt = float(np.sum(np.minimum(W(v, R_DRIFT, 0.0, p), C_N)) * p.mu)
            always = float(len(v) * C_N * p.mu)
            never = float(np.sum(kk * v) * p.mu)
            row.update(brands_above=int((vols > V_star).sum()), n_brands=len(vols),
                       yearly_cost_optimal_gpu_h=opt / 3600, yearly_cost_always_gpu_h=always / 3600,
                       yearly_cost_never_gpu_h=never / 3600)
            cells = [f"{row['brands_above']}/{len(vols)}", f"{opt / 3600:.2f} h", f"{always / 3600:.2f} h",
                     f"{never / 3600:.2f} h"]
        rows.append(row)
        print(f"{f'{lam:.3f} ({mult}x bound)':<26}{per_req * 1000:>19.1f}{V_star:>23,.0f}{cells[0]:>14}"
              f"{cells[1]:>15}{cells[2]:>16}{cells[3]:>10}")
    print("\nCosts are GPU-hours per year for all brands combined, counting retraining and the value lost to a"
          "\nstale adapter (in GPU-second equivalents). Optimal = the threshold policy of Proposition 2.")
    if a.mc:
        v0 = 0.5 * vs
        est, se = mc_check(R_DRIFT, p, v0, n=50_000)
        print(f"\nMonte Carlo check at v = v*/2: {est:.3f} +/- {se:.3f} GPU-s vs model "
              f"{float(W(v0, R_DRIFT, 0.0, p)):.3f}")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(dict(params=p.__dict__, R=R_DRIFT, weeks=WEEKS, q_fresh=Q_FRESH, beta=b, k=kk, v_star=vs,
                       scenarios=rows), f, indent=1)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
