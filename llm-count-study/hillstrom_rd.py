"""Absolute lift (risk difference) with paired-bootstrap CIs from saved Hillstrom runs. No API calls.

  python hillstrom_rd.py --runs runs_hillstrom --data hillstrom.csv

RD = rate(email arm) - rate(no email). `gap` = RD(men's email) - RD(women's email): does the simulator
tell the two emails apart? * = CI excludes the real value from the randomized test.
"""
import argparse, glob, json, os
import numpy as np, pandas as pd
import run_hillstrom as h


def real_rd(data):
    out = {}
    c = data[data.segment == "No E-Mail"]
    for outcome, col in (("visit", "visit"), ("purchase", "conversion")):
        res = {}
        for arm in h.ARMS[1:]:
            t = data[data.segment == arm]
            d = t[col].mean() - c[col].mean()
            se = np.sqrt(t[col].var() / len(t) + c[col].var() / len(c))
            res[arm] = (d, d - 1.96 * se, d + 1.96 * se)
        gap_se = np.sqrt(sum(data[data.segment == a][col].var() / (data.segment == a).sum() for a in h.ARMS[1:]))
        g = res["Mens E-Mail"][0] - res["Womens E-Mail"][0]
        res["gap"] = (g, g - 1.96 * gap_se, g + 1.96 * gap_se)
        out[outcome] = res
    return out


def boot_rd(ctrl, men, women, B, rng):
    ok = ~(np.isnan(ctrl) | np.isnan(men) | np.isnan(women))
    c, m, w = ctrl[ok], men[ok], women[ok]
    est = (m.mean() - c.mean(), w.mean() - c.mean(), m.mean() - w.mean())
    bs = []
    for _ in range(B):
        i = rng.integers(0, len(c), len(c))
        bs.append((m[i].mean() - c[i].mean(), w[i].mean() - c[i].mean(), m[i].mean() - w[i].mean()))
    bs = np.array(bs)
    return [(est[k], *np.percentile(bs[:, k], [2.5, 97.5])) for k in range(3)]


def cell(v, real):
    star = "*" if not (v[1] <= real[0] <= v[2]) and not (real[1] <= v[0] <= real[2]) else ""
    return f"{v[0]:+.3f} [{v[1]:+.3f},{v[2]:+.3f}]{star}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs_hillstrom")
    ap.add_argument("--data", default="hillstrom.csv")
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    real = real_rd(h.load_data(a.data))
    print("REAL risk differences (95% CI):")
    for o in real:
        print(f"  {o:9s} men {real[o]['Mens E-Mail'][0]:+.4f}  women {real[o]['Womens E-Mail'][0]:+.4f}  "
              f"gap(men-women) {real[o]['gap'][0]:+.4f} [{real[o]['gap'][1]:+.4f},{real[o]['gap'][2]:+.4f}]")
    print("\n* = simulated CI and real CI do not overlap (the simulated interval excludes the real point and vice versa)\n")
    agg, order = {}, []
    for d in sorted(glob.glob(os.path.join(a.runs, "*"))):
        f, c = os.path.join(d, "hillstrom_raw.csv"), os.path.join(d, "config.json")
        if not (os.path.exists(f) and os.path.exists(c)):
            continue
        cfg = json.load(open(c)); raw = pd.read_csv(f)
        n = int(raw.i.max()) + 1
        cols = {}
        for r in raw.itertuples():
            v = h.parse(r.method, str(r.raw))
            cols.setdefault((r.method, r.outcome, r.arm), np.full(n, np.nan))[r.i] = np.nan if v is None else v
        key = (cfg["model"], bool(cfg["anchor"]))
        if key not in agg:
            agg[key] = {"cols": {}, "seeds": []}; order.append(key)
        agg[key]["seeds"].append(cfg["seed"])
        for k, v in cols.items():  # pool the customers of all seeds
            agg[key]["cols"][k] = np.concatenate([agg[key]["cols"][k], v]) if k in agg[key]["cols"] else v
    rows = []
    rng = np.random.default_rng(100)
    for (model, anchor) in order:
        cols = agg[(model, anchor)]["cols"]
        for outcome in h.OUTCOMES:
            for label, method in (("A_yesno", "A"), ("C_prob", "C"), ("C_sampled", "C")):
                def arr(arm):
                    x = cols[(method, outcome, arm)].copy()
                    if label == "C_sampled":
                        ok = ~np.isnan(x); x[ok] = (rng.random(ok.sum()) < x[ok]).astype(float)
                    return x
                m_, w_, g_ = boot_rd(arr("No E-Mail"), arr("Mens E-Mail"), arr("Womens E-Mail"), a.boot, rng)
                rows.append(dict(model=model, anchor=anchor, method=label, outcome=outcome,
                                 seeds=len(agg[(model, anchor)]["seeds"]),
                                 RD_men=cell(m_, real[outcome]["Mens E-Mail"]),
                                 RD_women=cell(w_, real[outcome]["Womens E-Mail"]),
                                 gap=cell(g_, real[outcome]["gap"]),
                                 men_over_real=round(m_[0] / real[outcome]["Mens E-Mail"][0], 1)))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(a.runs, "hillstrom_rd.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
