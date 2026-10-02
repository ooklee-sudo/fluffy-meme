"""Monte Carlo of a 36-month enterprise chatbot lifecycle on a cloud LLM API under version retirement and price change.
Empirical inputs (data/): version lifetimes (Gemini), notice periods (OpenAI), generation-to-generation price ratios (Gemini), wages (BLS).
Assumptions (not open data; varied in the sensitivity runs): migration effort, outage cost, flexibility premium, effort reduction, token volume.
usage: python sim.py [--n 20000] [--out results.md]
"""
import argparse, math
import numpy as np, pandas as pd

H = 36                      # horizon, months
R_MONTH = 0.10 / 12         # discount rate (assumption)
WAGE = 135980 / 2080 * 1.4  # BLS median software developer pay per hour times 1.4 overhead (overhead is an assumption)
WEEK = 40 * WAGE

g = pd.read_csv("data/gemini_lifecycles.csv", parse_dates=["release", "shutdown"])
g = g[~g.source.str.startswith("announced")]
LIFE = ((g.shutdown - g.release).dt.days / 30.44).values              # months, realised retirements
o = pd.read_csv("data/openai_deprecations.csv", parse_dates=["announced", "shutdown"])
NOTICE = ((o.shutdown - o.announced).dt.days).values                  # days of notice
p = pd.read_csv("data/gemini_prices.csv")
p["blend"] = (5 * p.input_usd_per_M + p.output_usd_per_M) / 6         # 5:1 input:output token mix (assumption)
RATIOS = []
for _, grp in p.groupby("tier"):
    b = grp.sort_values("generation").blend.values
    RATIOS += list(b[1:] / b[:-1])
RATIOS = np.array(RATIOS)
LOGR = np.log(RATIOS)
GEN_MONTHS = 5.7                                                       # mean months between flash-tier generations in the price table
BASE_BLEND = 1.25                                                      # gemini-3.6-flash, USD per 1M blended tokens


def beta(mu, sig, r):
    a = 0.5 - mu / sig ** 2
    return a + math.sqrt(a * a + 2 * r / sig ** 2)


def theta(sig_m):
    b = beta(0.0, sig_m, R_MONTH)
    return b / (b - 1)


def disc(m):
    return 1 / (1 + R_MONTH) ** m


def run(n, vol_m_tokens=1000.0, kw=(2, 4, 10), emerg=1.5, outage_day=2000.0, premium_w=6.0, phi=0.5, notice_scale=1.0,
        corr_alt=0.5, succ_ratio=None, sig_m=0.10, theta_override=None, seed=7):
    """Paired present-value costs (USD) for four strategies over H months, common random numbers.
    Two vendors have price levels A (current vendor) and B (alternative) that follow monthly log random walks with volatility sig_m and
    innovation correlation corr_alt (martingale prices). A retirement event reprices both vendors (current by r1, alternative by r2, r2 = r1 with probability corr_alt, else an independent draw from the observed
    generation ratios). After a switch the former vendor becomes the alternative with its own level, so there is no reset of the price gap.
    rigid: hard-wired, migrates only at retirement, to the same vendor's successor.
    flex: premium_w person-weeks up front, migration effort phi*K, at retirement moves to the cheaper of the successor and the alternative.
    flex_npv: flex plus early switching when the present value of the saving to the horizon exceeds the switching cost (multiple 1).
    flex_ro: flex plus early switching when the saving exceeds theta times the switching cost, theta = b/(b-1) (zero-drift one-shot form)."""
    rng = np.random.default_rng(seed)
    th = theta(sig_m) if theta_override is None else theta_override
    keys = ("rigid", "flex", "flex_npv", "flex_ro")
    out = {k: np.zeros(n) for k in keys}
    out.update({"sw_" + k: np.zeros(n) for k in keys}); out["forced"] = np.zeros(n)
    ratios = RATIOS if succ_ratio is None else np.array([succ_ratio])
    W = vol_m_tokens
    for i in range(n):
        K = rng.triangular(*kw) * WEEK
        life0 = rng.choice(LIFE) * rng.uniform(0.2, 1.0)
        forced = []; t = life0
        while t < H:
            r1 = rng.choice(ratios); r2 = r1 if rng.random() < corr_alt else rng.choice(ratios)
            forced.append((int(t), rng.choice(NOTICE) * notice_scale, r1, r2))
            t += rng.choice(LIFE) * rng.uniform(0.2, 1.0)
        zA = rng.normal(size=H); zB = corr_alt * zA + math.sqrt(1 - corr_alt ** 2) * rng.normal(size=H)
        fmap = {f[0]: f for f in forced}
        out["forced"][i] = len(forced)
        def mig(Kc, nd):
            short = max(0.0, 14 * (Kc / WEEK) - nd)
            return Kc * (emerg if short > 0 else 1.0) + short * outage_day
        for key in keys:
            flexible = key != "rigid"
            tco = premium_w * WEEK if flexible else 0.0
            A = 1.0; B = 1.0; thr = {"flex": None, "flex_npv": 1.0, "flex_ro": th}.get(key)
            for m in range(H):
                A *= math.exp(sig_m * zA[m] - 0.5 * sig_m ** 2); B *= math.exp(sig_m * zB[m] - 0.5 * sig_m ** 2)
                if m in fmap:
                    _, nd, r1, r2 = fmap[m]
                    if flexible:
                        tco += disc(m) * mig(phi * K, nd)
                        if B * r2 < A * r1:
                            A, B = B * r2, A * r1
                        else:
                            A, B = A * r1, B * r2
                    else:
                        tco += disc(m) * mig(K, nd); A *= r1
                elif thr is not None and B < A:
                    pv = sum(disc(k) for k in range(m, H)) * W * BASE_BLEND * (A - B)
                    cost = disc(m) * mig(phi * K, 1e9)
                    if pv >= thr * cost:
                        tco += cost; A, B = B, A; out["sw_" + key][i] += 1
                tco += disc(m) * W * BASE_BLEND * A
            out[key][i] = tco
    return out


def summarize(out, label, rows):
    base = out["rigid"]
    for k in ("flex", "flex_npv", "flex_ro"):
        d = base - out[k]
        se = d.std(ddof=1) / math.sqrt(len(d))
        rows.append((label, k, base.mean(), out[k].mean(), 100 * d.mean() / base.mean(), 100 * (d.mean() - 1.96 * se) / base.mean(), 100 * (d.mean() + 1.96 * se) / base.mean(), (d > 0).mean() * 100))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=20000); ap.add_argument("--out", default="results.md")
    a = ap.parse_args()
    print(f"lifetimes n={len(LIFE)} median {np.median(LIFE):.1f} mo; notice n={len(NOTICE)} median {np.median(NOTICE):.0f} d; price ratios n={len(RATIOS)} {np.round(RATIOS,2)}; wage/h {WAGE:.1f}")
    print("threshold multiple by monthly volatility:", {sg: round(theta(sg), 1) for sg in (0.05, 0.10, 0.20, 0.36)})
    rows = []
    base = dict(vol_m_tokens=1000, corr_alt=0.5)
    scen = {"base: 1B tokens/month, alt. price correlation 0.5": {},
            "volume 100M tokens/month": dict(vol_m_tokens=100), "volume 10B tokens/month": dict(vol_m_tokens=10000),
            "alt. price independent (0)": dict(corr_alt=0.0), "alt. price perfectly correlated (1)": dict(corr_alt=1.0),
            "successor price unchanged (no price shock)": dict(succ_ratio=1.0),
            "short notice (x0.1)": dict(notice_scale=0.1), "effort reduction phi=0.8 (small)": dict(phi=0.8),
            "premium 12 weeks": dict(premium_w=12.0), "effort 4-8-20 weeks": dict(kw=(4, 8, 20)),
            "price-gap volatility 0.36/month (data upper bound)": dict(sig_m=0.36), "price-gap volatility 0.05/month": dict(sig_m=0.05)}
    for lab, kw in scen.items():
        summarize(run(a.n, **{**base, **kw}), lab, rows)
    df = pd.DataFrame(rows, columns=["scenario", "strategy", "TCO_rigid", "TCO_strategy", "saving_pct", "lo", "hi", "share_better"])
    pd.set_option("display.width", 250); print(df.round(1).to_string(index=False))
    with open(a.out, "w") as f:
        f.write("| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n")
        for r in df.round(1).itertuples(index=False):
            f.write("| " + " | ".join(str(v) for v in r) + " |\n")
