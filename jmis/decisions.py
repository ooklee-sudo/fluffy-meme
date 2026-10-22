"""Apply the fixed decision rules (manuscript Table 1) to the primary analysis outputs.

Written after the main run: analysis.py does not save the bootstrap draws, so the one quantity that needs
them (H1's rank correlation of nu with the share removed) is recomputed here with the same stems resampling
and seed. Everything else is read from the model_metrics, family_diffs, sign_tests and ranking files.

Usage: python decisions.py analysis_input.csv resultsdir [--boot 2000]
"""
import argparse
import json
import sys

import numpy as np
import pandas as pd

import analysis as A

MARGIN = 0.08


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("res"); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    out = {}
    m = pd.read_csv(f"{a.res}/model_metrics.csv")
    g = lambda k: m[m.metric == k].set_index("model")
    models = list(g("a").index)
    # H1
    rho = g("rho"); h1 = {k: bool(rho.loc[k, "lo"] > 0) for k in models}
    out["H1_rho_excludes_0"] = h1; out["H1_n_models"] = sum(h1.values()); out["H1_majority"] = sum(h1.values()) > len(models) / 2
    # H1 rank correlation (nu, removed): same resampling as analysis.py
    df = pd.read_csv(a.data, keep_default_na=False)
    arrays, meta, n = A.build(df, "exclude"); A.add_stem_deference(df, arrays, n, "pref", "exclude")
    rng = np.random.default_rng(20260101); full = np.arange(n)
    def rc(idx):
        est = {k: A.estimate(v, idx, "pref") for k, v in arrays.items()}
        t = pd.DataFrame({"nu": [est[k]["nu"] for k in est], "rem": [est[k]["removed"] for k in est]}).dropna()
        return t["nu"].rank().corr(t["rem"].rank()), len(t)
    pt, nm = rc(full)
    ds = [rc(rng.integers(0, n, n))[0] for _ in range(a.boot)]
    lo, hi = np.nanpercentile(ds, [2.5, 97.5])
    out["H1_rank_corr_nu_removed"] = dict(est=pt, lo=lo, hi=hi, n_models=nm, supported=bool(lo > 0))
    # H2
    fd = pd.read_csv(f"{a.res}/family_diffs.csv"); h2 = {}
    for fam, t in fd.groupby("family"):
        t = t.set_index("metric"); aa, ss = t.loc["a"], t.loc["s_star"]
        h2[fam] = dict(d_a=aa.large_minus_small, a_lo=aa.lo, d_s=ss.large_minus_small, s_lo=ss.lo, s_hi=ss.hi,
                       a_ok=bool(aa.lo > 0), s_ok=bool(ss.hi < 0), supported=bool(aa.lo > 0 and ss.hi < 0))
    out["H2_by_family"] = h2; out["H2_families_supported"] = sum(v["supported"] for v in h2.values())
    out["H2_sign_tests"] = pd.read_csv(f"{a.res}/sign_tests.csv").to_dict("records")
    # H3
    sl, ac, di = g("slope"), g("acc_slope"), g("disclaimer_effect"); h3 = {}
    for k in models:
        inc0 = lambda t: bool(t.loc[k, "lo"] <= 0 <= t.loc[k, "hi"])
        defer = inc0(sl) and inc0(ac) and inc0(di) and sl.loc[k, "lo"] > -MARGIN and sl.loc[k, "hi"] < MARGIN
        weigh = sl.loc[k, "lo"] > 0 and ac.loc[k, "lo"] > 0 and di.loc[k, "hi"] < 0
        h3[k] = "deference-consistent" if defer else "evidence-weighing-consistent" if weigh else "mixed or unclassified"
    out["H3"] = h3
    # H4
    cov = g("cov_a_s"); out["H4"] = {k: dict(cov=cov.loc[k, "est"], lo=cov.loc[k, "lo"], hi=cov.loc[k, "hi"], gap_07=g("gap_0.7").loc[k, "est"],
                                              supported=bool(cov.loc[k, "hi"] < 0 and g("gap_0.7").loc[k, "est"] > 0)) for k in models}
    # H5
    rk = pd.read_csv(f"{a.res}/ranking.csv").set_index("metric")
    r = rk.loc["pairs_ability_optimal"]; out["H5_pairs"] = dict(est=r.est, lo=r.lo, hi=r.hi, supported=bool(r.lo > 0.5))
    out["H5_overstatement"] = {k: float(g("overstate").loc[k, "est"]) for k in models}
    json.dump(out, open(f"{a.res}/decisions.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
