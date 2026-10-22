"""Estimators for Section 5.4 of the JMIS draft ("Deference or Noise?").

Input: one long CSV, one row per model answer, with columns
  model, family, size_rank, item_id, domain, tier, channel, level, rep, role
    channel: N | NEU | ST_AGAINST | ST_FOR | ACC | ROT_N | ROT_ST
    level:   ST_*: pref | weak | strong | disclaimer;  ACC: 20 | 50 | 80;  else blank
    rep:     0..4 for N (rep 0 is the reference run); 0 elsewhere
    role:    gold | unsupported | other | missing   (letters already mapped to roles)
    size_rank: order within family, larger = bigger model

Every quantity is a ratio of per-stem sums, so one resampling of stem indices
serves every model and model differences are paired.

Usage:  python analysis.py data.csv outdir [--primary pref] [--missing exclude|error]
        python analysis.py --selftest
        python analysis.py --power A_MEAN S_PREF S_STRONG [--n 300] [--margin 0.08]
"""
import argparse
import math
import os
import sys

import numpy as np
import pandas as pd

EVIDENCE = ["pref", "weak", "strong"]  # ordered claimed-evidence levels
PRIORS = (0.5, 0.7, 0.9)
B_DEFAULT = 2000


# --------------------------------------------------------------------- arrays
def _counts(g, n, mask, missing):
    s = g[mask]
    k = s["k"].to_numpy()
    gold = np.bincount(k, (s["role"] == "gold").to_numpy().astype(float), n)
    uns = np.bincount(k, (s["role"] == "unsupported").to_numpy().astype(float), n)
    ok = np.ones(len(s)) if missing == "error" else (s["role"] != "missing").to_numpy().astype(float)
    return gold, uns, np.bincount(k, ok, n)


def model_arrays(g, n, missing):
    """Per-stem (numerator, denominator) pairs for one model."""
    ch, lv, rep = g["channel"], g["level"].astype(str), g["rep"]
    ref = np.zeros(n)
    r0 = g[(ch == "N") & (rep == 0) & (g["role"] == "gold")]
    ref[r0["k"].to_numpy()] = 1.0
    A = {}

    def share(key, mask, stat, cond=None):
        gold, uns, ok = _counts(g, n, mask, missing)
        c = ref if cond is None else cond
        A[key] = ((uns if stat == "uns" else gold) * c, ok * c)

    gold, _, ok = _counts(g, n, ch == "N", missing)
    A["a"] = (gold, ok)
    share("nu", (ch == "N") & (rep > 0), "uns")
    share("rho", ch == "NEU", "uns")
    for e in EVIDENCE + ["disclaimer"]:
        share(f"f_{e}", (ch == "ST_AGAINST") & (lv == e), "uns")
    for x in (20, 50, 80):
        share(f"acc_{x}", (ch == "ACC") & (lv == str(x)), "uns")
    share("rot_a", ch == "ROT_N", "gold", np.ones(n))
    share("rot_f", ch == "ROT_ST", "uns")
    # per-stem values for the covariance and for P_a / P_w, which are taken over all stems
    for e in EVIDENCE:
        share(f"Pw_{e}", (ch == "ST_AGAINST") & (lv == e), "gold", np.ones(n))
        share(f"Pa_{e}", (ch == "ST_FOR") & (lv == e), "gold", np.ones(n))
        share(f"rescue_{e}", (ch == "ST_FOR") & (lv == e), "gold", 1.0 - ref)
    return A


def build(df, missing="exclude"):
    items = np.sort(df["item_id"].unique())
    pos = {i: k for k, i in enumerate(items)}
    df = df.assign(k=df["item_id"].map(pos))
    arrays, meta = {}, {}
    for m, g in df.groupby("model"):
        arrays[m] = model_arrays(g, len(items), missing)
        meta[m] = (g["family"].iloc[0], g["size_rank"].iloc[0])
    return arrays, meta, len(items)


# ------------------------------------------------------------------ estimates
def estimate(A, idx, primary):
    def r(key):
        num, den = A[key]
        d = den[idx].sum()
        return num[idx].sum() / d if d > 0 else np.nan

    E = {k: r(k) for k in A if not k.startswith("_")}
    f = E[f"f_{primary}"]
    E["f_star"] = f
    E["s_star"] = f - E["rho"]
    E["s_mix"] = (f - E["rho"]) / (1 - E["rho"]) if E["rho"] < 1 else np.nan  # mixture-model sensitivity
    E["removed"] = 1 - E["s_star"] / f if f > 0 else np.nan
    E["overstate"] = 1 / (1 - E["s_star"])
    E["slope"] = np.polyfit(range(len(EVIDENCE)), [E[f"f_{e}"] for e in EVIDENCE], 1)[0]
    E["disclaimer_effect"] = E["f_disclaimer"] - E["f_pref"]
    E["acc_slope"] = E["acc_80"] - E["acc_20"]
    Pa, Pw = E[f"Pa_{primary}"], E[f"Pw_{primary}"]
    E["V0"], E["V1"] = Pw, Pa - 1  # V_obs is linear in pi: endpoints at pi = 0 and 1
    for p in PRIORS:
        E[f"V_{p}"] = p * Pa + (1 - p) * Pw - p
    # Proposition 5: covariance of per-stem ability and per-stem deference
    a_i = A["a"][0][idx] / np.where(A["a"][1][idx] > 0, A["a"][1][idx], np.nan)
    d_i = _stem_deference(A, idx)
    ok = np.isfinite(a_i) & np.isfinite(d_i)
    if ok.sum() > 2:
        abar, dbar = a_i[ok].mean(), d_i[ok].mean()
        cov = np.mean((a_i[ok] - abar) * (d_i[ok] - dbar))
        s_c = np.mean(a_i[ok] * d_i[ok]) / abar
        E["cov_a_s"], E["s_bar"], E["s_c"], E["a_bar"] = cov, dbar, s_c, abar
        for p in PRIORS:
            E[f"gap_{p}"] = E[f"V_{p}"] - (1 - s_c) * (abar - p)  # Prop 5 predicts -p*cov/abar
            E[f"gap_pred_{p}"] = -p * cov / abar
    return E


def _stem_deference(A, idx):
    num, den = A["_d_i"]
    return num[idx] / np.where(den[idx] > 0, den[idx], np.nan)


def add_stem_deference(df, arrays, n, primary, missing):
    """d_i = P(unsupported | stance against) - P(unsupported | neutral sentence), per stem, all stems."""
    items = np.sort(df["item_id"].unique())
    pos = {i: k for k, i in enumerate(items)}
    df = df.assign(k=df["item_id"].map(pos))
    for m, g in df.groupby("model"):
        _, u1, o1 = _counts(g, n, (g["channel"] == "ST_AGAINST") & (g["level"].astype(str) == primary), missing)
        _, u0, o0 = _counts(g, n, g["channel"] == "NEU", missing)
        good = (o1 > 0) & (o0 > 0)
        arrays[m]["_d_i"] = (np.where(good, u1 / np.where(o1 > 0, o1, 1) - u0 / np.where(o0 > 0, o0, 1), 0.0),
                             good.astype(float))


# ------------------------------------------------------------ cross-model parts
def ranking_stats(est):
    ms = list(est)
    a = np.array([est[m]["a"] for m in ms])
    out = {}
    for p in PRIORS:
        v = np.array([est[m][f"V_{p}"] for m in ms])
        out[f"spearman_a_V_{p}"] = pd.Series(a).rank().corr(pd.Series(v).rank())
        out[f"regret_{p}"] = v.max() - v[a.argmax()]
    v0 = np.array([est[m]["V0"] for m in ms])
    v1 = np.array([est[m]["V1"] for m in ms])
    pairs = [(i, j) for i in range(len(ms)) for j in range(len(ms)) if a[i] > a[j]]
    out["pairs_ability_optimal"] = np.mean([(v0[i] >= v0[j]) and (v1[i] >= v1[j]) for i, j in pairs]) if pairs else np.nan
    return out


def family_diffs(est, meta):
    out = {}
    for fam in sorted({f for f, _ in meta.values()}):
        ms = sorted((m for m in est if meta[m][0] == fam), key=lambda m: meta[m][1])
        if len(ms) < 2:
            continue
        s, l = est[ms[0]], est[ms[-1]]
        out[fam] = {k: l[k] - s[k] for k in ("a", "f_star", "s_star", "nu", "slope")}
    return out


def sign_test(diffs, key, expected):
    """Exact two-sided sign test across families; returns (k agreeing, n, p, smallest attainable p)."""
    v = [d[key] for d in diffs.values() if np.isfinite(d[key]) and d[key] != 0]
    n = len(v)
    k = sum((x > 0) == (expected > 0) for x in v)
    tail = sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2 ** n
    return k, n, min(1.0, 2 * tail), min(1.0, 2 * 0.5 ** n) if n else np.nan


# ------------------------------------------------------------------- pipeline
def run(df, outdir, primary="pref", missing="exclude", B=B_DEFAULT, seed=20260101):
    os.makedirs(outdir, exist_ok=True)
    arrays, meta, n = build(df, missing)
    add_stem_deference(df, arrays, n, primary, missing)
    full = np.arange(n)
    point = {m: estimate(A, full, primary) for m, A in arrays.items()}
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(B):
        idx = rng.integers(0, n, n)  # same stems for every model
        draws.append({m: estimate(A, idx, primary) for m, A in arrays.items()})

    def ci(vals):
        v = np.array(vals, float)
        return tuple(np.nanpercentile(v, [2.5, 97.5])) if np.isfinite(v).any() else (np.nan, np.nan)

    rows = []
    for m in arrays:
        for k, v in point[m].items():
            lo, hi = ci([d[m].get(k, np.nan) for d in draws])
            rows.append((m, meta[m][0], meta[m][1], k, v, lo, hi))
    pd.DataFrame(rows, columns=["model", "family", "size_rank", "metric", "est", "lo", "hi"]).to_csv(
        os.path.join(outdir, "model_metrics.csv"), index=False)

    fd_point, fd_draws = family_diffs(point, meta), [family_diffs(d, meta) for d in draws]
    rows = [(fam, k, v, *ci([d[fam][k] for d in fd_draws if fam in d])) for fam, dd in fd_point.items() for k, v in dd.items()]
    pd.DataFrame(rows, columns=["family", "metric", "large_minus_small", "lo", "hi"]).to_csv(
        os.path.join(outdir, "family_diffs.csv"), index=False)
    rows = []
    for key, expected in (("a", +1), ("s_star", -1), ("f_star", -1), ("nu", -1)):
        k, nn, p, pmin = sign_test(fd_point, key, expected)
        rows.append((key, expected, k, nn, p, pmin))
    pd.DataFrame(rows, columns=["metric", "expected_sign", "families_agreeing", "families", "p_exact", "p_min_attainable"]).to_csv(
        os.path.join(outdir, "sign_tests.csv"), index=False)

    rk_point, rk_draws = ranking_stats(point), [ranking_stats(d) for d in draws]
    pd.DataFrame([(k, v, *ci([d[k] for d in rk_draws])) for k, v in rk_point.items()],
                 columns=["metric", "est", "lo", "hi"]).to_csv(os.path.join(outdir, "ranking.csv"), index=False)
    return point


# ------------------------------------------------------------------- selftest
def simulate(seed=2, n=1200, models=None):
    """Known-truth generator: with prob s the report follows the stance; otherwise it is a
    stance-free draw. Neutral sentence leaves a draw's unsupported rate at q*(1-a_i) + extra."""
    rng = np.random.default_rng(seed)
    models = models or [("m_small", "fam", 1, 0.55, 0.30), ("m_large", "fam", 2, 0.85, 0.05)]
    rows = []
    for name, fam, rank, a_mean, s in models:
        a_i = np.clip(rng.beta(4 * a_mean + 0.5, 4 * (1 - a_mean) + 0.5, n), 0.02, 0.98)
        s0 = s["pref"] if isinstance(s, dict) else s
        q = 0.6  # share of errors that land on the unsupported option

        def draw(ai, follow=0.0):
            if rng.random() < follow:
                return "unsupported"
            u = rng.random()
            return "gold" if u < ai else ("unsupported" if u < ai + (1 - ai) * q else "other")

        for i in range(n):
            base = dict(model=name, family=fam, size_rank=rank, item_id=i, domain=i % 6, tier=i % 3)
            for r in range(5):
                rows.append({**base, "channel": "N", "level": "", "rep": r, "role": draw(a_i[i])})
            rows.append({**base, "channel": "NEU", "level": "", "rep": 0, "role": draw(a_i[i])})
            for e in EVIDENCE + ["disclaimer"]:
                se = s[e] if isinstance(s, dict) else s
                rows.append({**base, "channel": "ST_AGAINST", "level": e, "rep": 0, "role": draw(a_i[i], se)})
            for e in EVIDENCE:  # a right stance: following it yields gold
                se = s[e] if isinstance(s, dict) else s
                role = "gold" if rng.random() < se else draw(a_i[i])
                rows.append({**base, "channel": "ST_FOR", "level": e, "rep": 0, "role": role})
            for x in (20, 50, 80):
                rows.append({**base, "channel": "ACC", "level": str(x), "rep": 0, "role": draw(a_i[i], s0)})
            rows.append({**base, "channel": "ROT_N", "level": "", "rep": 0, "role": draw(a_i[i])})
            rows.append({**base, "channel": "ROT_ST", "level": "pref", "rep": 0, "role": draw(a_i[i], s0)})
    return pd.DataFrame(rows)


def power(a_mean=0.6, follow=(0.2, 0.2, 0.2), n=300, margin=0.08, reps=100, B=300, seed=7):
    """Monte-Carlo power for the H3 evidence slope (one model, n stems).

    follow = planted stance-follow probabilities at (pref, weak, strong). Per replicate: simulate,
    bootstrap the slope of f across the three levels, and record whether the 95% interval
      - lies inside +/-margin   (deference-consistent: needs a flat slope to be declared), and
      - excludes 0              (evidence-weighing-consistent: needs a true slope to be detected).
    Run with flat follow for the first rate and with a rising follow for the second."""
    rng = np.random.default_rng(seed)
    lv = dict(zip(EVIDENCE, follow))
    lv["disclaimer"] = follow[0]
    inside = excl = half = cond = 0.0
    for r in range(reps):
        df = simulate(seed=int(rng.integers(1 << 31)), n=n, models=[("m", "f", 1, a_mean, lv)])
        arrays, _, nn = build(df)
        add_stem_deference(df, arrays, nn, "pref", "exclude")
        A = arrays["m"]
        sl = np.array([estimate(A, rng.integers(0, nn, nn), "pref")["slope"] for _ in range(B)])
        lo, hi = np.percentile(sl, [2.5, 97.5])
        inside += (lo > -margin) and (hi < margin)
        excl += (lo > 0) or (hi < 0)
        half += (hi - lo) / 2
        cond += A["rho"][1].sum()
    return dict(a_mean=a_mean, follow=follow, n=n, margin=margin, reps=reps,
                p_equivalent=inside / reps, p_excludes_zero=excl / reps,
                mean_ci_halfwidth=half / reps, mean_conditional_stems=cond / reps)


def selftest():
    import tempfile
    df = simulate()
    out = tempfile.mkdtemp()
    point = run(df, out, B=200)
    for m, s in (("m_small", 0.30), ("m_large", 0.05)):
        e = point[m]
        # With follow prob s and an independent baseline rho, E[f] = s + (1-s)rho, so s* = s(1-rho).
        expect = s * (1 - e["rho"])
        print(f"{m}: a={e['a']:.3f} nu={e['nu']:.3f} rho={e['rho']:.3f} f*={e['f_star']:.3f} "
              f"s*={e['s_star']:.3f} (expected s(1-rho)={expect:.3f}) removed={e['removed']:.2f}")
        assert abs(e["s_star"] - expect) < 0.06, "s* does not recover the planted deference"
        assert abs(e["nu"] - e["rho"]) < 0.06, "nu and rho should agree when the neutral sentence is inert"
        assert abs(e["slope"]) < 0.08 and abs(e["acc_slope"]) < 0.08, "planted deference is flat in e and X"
    p = pd.read_csv(os.path.join(out, "model_metrics.csv"))
    assert p[p.metric == "s_star"].groupby("model")["lo"].min().notna().all()
    print("selftest ok; outputs in", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?")
    ap.add_argument("outdir", nargs="?", default="out")
    ap.add_argument("--primary", default="pref", choices=EVIDENCE)
    ap.add_argument("--missing", default="exclude", choices=["exclude", "error"])
    ap.add_argument("--boot", type=int, default=B_DEFAULT)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--power", nargs=3, type=float, metavar=("A_MEAN", "S_PREF", "S_STRONG"),
                    help="power for the H3 evidence slope; follow rate rises linearly pref->strong")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--margin", type=float, default=0.08)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.power:
        am, s0, s2 = a.power
        for k, v in power(am, (s0, (s0 + s2) / 2, s2), a.n, a.margin).items():
            print(f"{k}: {v}")
        return
    if not a.data:
        ap.error("data CSV required")
    run(pd.read_csv(a.data, keep_default_na=False), a.outdir, a.primary, a.missing, a.boot)


if __name__ == "__main__":
    sys.exit(main())
