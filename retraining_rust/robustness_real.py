"""Robustness of the pooled GitHub diagnostics: (a) all eligible repos; (b) drop repos with median
cycle <= 1 week; (c) hazard conditional on surviving age 1 (ages >= 2) to remove hot-fix releases;
(d) bug slope without the issue-volume offset. Random-effects pooling as in diagnostics_real.py."""
import sys, glob, json
import numpy as np
import diagnostics_real as dr

def est_variant(n, a_, d, age, t, variant):
    if variant == "no_offset":
        X = np.c_[np.ones(len(n)), age, t - t.mean()]; return dr.pois(n, X, np.zeros(len(n)))[1], None
    if variant == "age2plus":
        m = age >= 2
        if m.sum() < 40 or d[m].sum() < 5: return None, None
        return None, dr.logit(d[m].astype(float), np.c_[np.ones(m.sum()), np.minimum(age[m], 8)])[1]
    return dr.est(n, a_, d, age, t)

res = {}
paths = sorted(glob.glob(sys.argv[1] + "/*.csv")); boot = 150
for variant in ("base", "no_offset", "age2plus"):
    rows = []
    for p in paths:
        n, a_, d, age, cyc, t = dr.load(p)
        if d.sum() < 10 or len(n) < 80: continue
        med = np.median(np.diff(np.where(d == 1)[0]))
        g = est_variant(n, a_, d, age, t, variant)
        rng = np.random.default_rng(0); cycles = np.unique(cyc); bs = []
        for _ in range(boot):
            r = np.concatenate([np.where(cyc == c)[0] for c in rng.choice(cycles, len(cycles))])
            try: bs.append(est_variant(n[r], a_[r], d[r], age[r], t[r], variant))
            except Exception: pass
        bs = np.array([[np.nan if v is None else v for v in b] for b in bs], float)
        rows.append(dict(name=p.split("/")[-1][:-4], med=med, b=g[0], h=g[1], sb=np.nanstd(bs[:, 0], ddof=1) if g[0] is not None else None, sh=np.nanstd(bs[:, 1], ddof=1) if g[1] is not None else None))
    for label, sel in (("all", lambda r: True), ("median cycle > 1 week", lambda r: r["med"] > 1)):
        rs = [r for r in rows if sel(r)]
        out = {}
        for key, sk in (("bug", ("b", "sb")), ("hazard", ("h", "sh"))):
            v = [(r[sk[0]], r[sk[1]]) for r in rs if r[sk[0]] is not None and r[sk[1]]]
            if len(v) >= 2:
                m, s, tau2 = dr.dl([x[0] for x in v], [x[1] for x in v]); out[key] = dict(k=len(v), est=round(m, 4), ci=[round(m - 1.96 * s, 4), round(m + 1.96 * s, 4)], tau2=round(tau2, 4))
        res[f"{variant} | {label}"] = out
        print(f"{variant:9s} | {label:22s}", json.dumps(out))
json.dump(res, open("robustness_real.json", "w"), indent=1)
