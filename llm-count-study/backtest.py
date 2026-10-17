"""Stage 3: backtest of the acceptance test (offline; uses the parsed result tables in report/, no API calls).

A. Email campaigns. The men's email is the 'past randomized test' and the women's email the 'new campaign' (and the
   reverse). Gate: the simulated absolute lift of the past campaign is within a factor of 2 of its measured lift.
   Decision: launch if lift > break-even lift t. t is swept over 0.1x..10x the measured lift of the new campaign; a
   decision is wrong when simulated and measured lift fall on different sides of t.
   Compared rules: trust always; face validity (right sign for both emails); acceptance gate; gate + ratio recalibration.
B. Transactions. Gate on history statistics (mean and zero share inside the model's interval around the reference);
   held-out decision statistic: share of purchases made by the top decile, computed from the simulated alpha with
   Proposition 3(b) (gamma form) and compared with the reference share (error above 0.10 = wrong).
"""
import numpy as np, pandas as pd
from scipy import stats

REAL = {("visit", "men"): 0.0766, ("visit", "women"): 0.0452, ("purchase", "men"): 0.0068, ("purchase", "women"): 0.0031}
U = np.linspace(-1, 1, 201)  # log10 of break-even threshold relative to measured lift


def wrong_share(sim, real):
    if sim <= 0:
        return 1.0
    return float(np.mean((sim > real * 10 ** U) != (real > real * 10 ** U)))


def email():
    d = pd.read_csv("report/hillstrom_rd_parsed.csv")
    d = d[d.method == "C_prob"]
    rows = []
    for _, r in d.iterrows():
        for past, new in (("men", "women"), ("women", "men")):
            sp, sn = r[f"RD_{past}"], r[f"RD_{new}"]
            rp, rn = REAL[(r.outcome, past)], REAL[(r.outcome, new)]
            ratio_p = sp / rp
            gate = 0.5 <= ratio_p <= 2
            face = (r.RD_men > 0) and (r.RD_women > 0)
            recal = sn / ratio_p if ratio_p > 0 else np.nan
            rows.append(dict(model=r.model, anchor=r.anchor, outcome=r.outcome, past=past, face=face, gate=gate,
                             err_raw=wrong_share(sn, rn), err_recal=wrong_share(recal, rn) if ratio_p > 0 else 1.0,
                             big_raw=not (0.5 <= sn / rn <= 2), big_recal=not (0.5 <= recal / rn <= 2) if ratio_p > 0 else True,
                             ratio_new=sn / rn, ratio_past=ratio_p))
    return pd.DataFrame(rows)


def share_gamma(alpha, q=0.1):
    if alpha <= 1e-6:
        return q
    k = 1 / alpha
    x = stats.gamma.ppf(1 - q, k)
    return 1 - stats.gamma.cdf(x, k + 1)


REF = {"retail": dict(mean=0.49, zero=0.74, alpha=3.05), "grocery": dict(mean=4.84, zero=0.19, alpha=1.42), "demo": dict(mean=7.83, zero=0.03, alpha=0.71)}


def trans():
    rows = []
    for s in REF:
        d = pd.read_csv(f"report/{s}_ci.csv"); R = REF[s]; rs = share_gamma(R["alpha"])
        for _, r in d.iterrows():
            if not (r["alpha"] > -1) or pd.isna(r["alpha"]):
                continue
            a = max(r["alpha"], 0.0)
            face = abs(r["mean"] / R["mean"] - 1) <= 0.5 and r["parse_fail"] < 0.05
            tol = 0.02
            gate = (r.mean_lo - tol * R["mean"] <= R["mean"] <= r.mean_hi + tol * R["mean"]) and (r.zero_lo - 0.02 <= R["zero"] <= r.zero_hi + 0.02)
            rows.append(dict(setting=s, model=r.model, anchor=r.anchor, design=r.cond, face=face, gate=gate,
                             share_err=abs(share_gamma(a) - rs), wrong=abs(share_gamma(a) - rs) > 0.10))
    return pd.DataFrame(rows)


def main():
    E = email()
    print("A. EMAIL: past campaign -> new campaign (C_prob design; 16 configs x 2 outcomes x 2 directions =", len(E), "cases)")
    print(f"  trust always       : cases {len(E)}, mean wrong-decision share across break-evens {E.err_raw.mean():.3f}, lift off by >2x in {E.big_raw.mean():.2f}")
    f = E[E.face]
    print(f"  face validity      : pass {len(f)}/{len(E)}, wrong {f.err_raw.mean():.3f}, off by >2x in {f.big_raw.mean():.2f}")
    g = E[E.gate]
    print(f"  acceptance gate    : pass {len(g)}/{len(E)}, wrong {g.err_raw.mean() if len(g) else float('nan'):.3f}, off by >2x in {g.big_raw.mean() if len(g) else float('nan'):.2f}")
    print(f"  recalibrate (all)  : wrong {E.err_recal.mean():.3f}, off by >2x in {E.big_recal.mean():.2f}")
    print(f"  recalibrate (gate) : wrong {g.err_recal.mean() if len(g) else float('nan'):.3f}")
    print("  by outcome (trust-always vs recalibrated, share wrong / share off >2x):")
    print(E.groupby("outcome")[["err_raw", "err_recal", "big_raw", "big_recal"]].mean().round(3).to_string())
    print("  correlation of log ratio, past vs new campaign (cases):", round(stats.spearmanr(np.log(E.ratio_past.clip(1e-3)), np.log(E.ratio_new.clip(1e-3)))[0], 2))
    print("  passing gate:", g[["model", "anchor", "outcome", "past", "ratio_past", "ratio_new"]].round(2).to_string(index=False) if len(g) else "none")
    T = trans()
    print("\nB. TRANSACTIONS: held-out heavy-buyer share (top decile) implied by simulated alpha; wrong if |share error| > 0.10")
    print(f"  cells {len(T)}; wrong overall {T.wrong.mean():.2f}")
    print(f"  face validity (mean within 50%): pass {T.face.sum()}, wrong among pass {T[T.face].wrong.mean():.2f}")
    print(f"  history gate (mean and zero share): pass {T.gate.sum()}, wrong among pass {T[T.gate].wrong.mean() if T.gate.any() else float('nan'):.2f}")
    print(T.groupby("design").agg(cells=("wrong", "size"), wrong=("wrong", "mean"), face=("face", "sum"), gate=("gate", "sum")).round(2).to_string())
    print(T[T.gate].groupby("design").wrong.agg(["size", "mean"]).round(2).to_string())
    E.to_csv("report/backtest_email.csv", index=False); T.to_csv("report/backtest_trans.csv", index=False)


main()
