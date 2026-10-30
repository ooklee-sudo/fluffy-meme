"""Analysis fixed in PREREG.md. Usage: python analyze_heldout.py [judge]  (judge: qwen1.5b | smollm1.7b)"""
import json, os, sys
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
GENS = ["qwen0.5b", "smollm360m", "qwen1.5b"]
NAMES = {"qwen0.5b": "Qwen2.5-0.5B", "smollm360m": "SmolLM2-360M", "qwen1.5b": "Qwen2.5-1.5B"}
JUDGE = sys.argv[1] if len(sys.argv) > 1 else "qwen1.5b"
QPD = 200
B = 1000
# original 300-question results (Tables 5, 7 and Section 5.2 of the manuscript)
ORIG = {"qwen0.5b": dict(p0=60.3, c2=89.5, c3=58.0, fb2=15.1, fb3=24.4, ratio_full=1.5, ratio_routed=2.1, k=(139, 19, 17)),
        "smollm360m": dict(p0=65.0, c2=96.9, c3=48.2, fb2=70.9, fb3=16.5, ratio_full=1.6, ratio_routed=1.9, k=(149, 8, 8)),
        "qwen1.5b": dict(p0=47.0, c2=81.6, c3=58.9, fb2=15.4, fb3=22.8, ratio_full=1.3, ratio_routed=2.3, k=(110, 24, 24))}


def load(gen):
    g = {}
    for l in open(os.path.join(RES, f"gen_{gen}.jsonl")):
        r = json.loads(l); g[r["id"]] = r
    j = {}
    p = os.path.join(RES, f"judge_{JUDGE}_{gen}.jsonl")
    for l in open(p):
        r = json.loads(l); j[r["id"]] = r
    return g, j


def kpois(lam):
    return int(stats.poisson.ppf(0.95, lam)) if lam > 0 else 0


def arrays(g, j):
    ids = list(g)
    n = len(ids)
    ab = np.array([g[i]["abstain"] for i in ids])
    H = np.array([(not g[i]["abstain"]) and g[i]["halluc"] for i in ids])
    ok = np.array([(not g[i]["abstain"]) and not g[i]["halluc"] for i in ids])
    z = lambda key: np.array([bool(g[i].get(key, False)) for i in ids])
    l1, l2 = z("l1_block"), z("l2_block")
    score = np.array([g[i].get("l2_score", 1.0) for i in ids])
    l3 = np.array([bool(j[i]["unsupported"] and not j[i]["failure"]) if i in j else False for i in ids])
    fail = np.array([bool(j[i]["failure"]) if i in j else False for i in ids])
    routed = (~l2) & (score < 0.9) & ~ab
    return dict(n=n, ab=ab, H=H, ok=ok, l1=l1, l2=l2, l3=l3, fail=fail, routed=routed)


def stat(a):
    n, H, ok = a["n"], a["H"], a["ok"]
    nH, nok = H.sum(), ok.sum()
    c2 = (a["l2"] & H).sum() / nH
    c3 = (a["l3"] & H).sum() / nH
    fb2 = (a["l2"] & ok).sum() / nok
    fb3 = (a["l3"] & ok).sum() / nok
    ind = (1 - c2) * (1 - c3)
    full_pass = (H & ~a["l2"] & ~a["l3"]).sum() / nH
    routed_block = a["l2"] | (a["routed"] & a["l3"])
    routed_pass = (H & ~routed_block).sum() / nH
    p0 = nH / n
    k_none = kpois(QPD * p0)
    k_l2 = kpois(QPD * p0 * (1 - c2))
    k_full = kpois(QPD * p0 * full_pass)
    k_routed = kpois(QPD * p0 * routed_pass)
    a2, b2 = (H & a["l2"] & a["l3"]).sum(), (H & a["l2"] & ~a["l3"]).sum()
    c_, d_ = (H & ~a["l2"] & a["l3"]).sum(), (H & ~a["l2"] & ~a["l3"]).sum()
    phi = (a2 * d_ - b2 * c_) / np.sqrt(max((a2 + b2) * (c_ + d_) * (a2 + c_) * (b2 + d_), 1e-12))
    return dict(p0=100 * p0, c1=100 * (a["l1"] & H).sum() / nH, c2=100 * c2, c3=100 * c3, fb2=100 * fb2, fb3=100 * fb3,
                phi=phi, ind=100 * ind, full=100 * full_pass, routed=100 * routed_pass,
                ratio_full=full_pass / ind if ind > 0 else np.nan, ratio_routed=routed_pass / ind if ind > 0 else np.nan,
                k_none=k_none, k_l2=k_l2, k_full=k_full, k_routed=k_routed,
                red_l2=100 * (1 - k_l2 / k_none) if k_none else np.nan,
                fail_rate=a["fail"][~a["ab"]].mean() * 100, nH=int(nH), nok=int(nok),
                fisher=stats.fisher_exact([[a2, b2], [c_, d_]])[1])


def boot(a, rng):
    idx = rng.integers(0, a["n"], a["n"])
    b = {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in a.items()}
    b["n"] = a["n"]
    return b


out = {}
lines = [f"# Held-out replication (N = 1,000 fresh SQuAD 2.0 questions); judge = {JUDGE}\n"]
for gname in GENS:
    try:
        g, j = load(gname)
    except FileNotFoundError:
        continue
    a = arrays(g, j)
    s = stat(a)
    rng = np.random.default_rng(0)
    bs = [stat(boot(a, rng)) for _ in range(B)]
    ci = {k: (float(np.nanpercentile([x[k] for x in bs], 2.5)), float(np.nanpercentile([x[k] for x in bs], 97.5)))
          for k in ("phi", "ratio_full", "ratio_routed", "k_none", "k_l2", "k_routed", "red_l2", "c2", "c3", "fb2", "fb3")}
    out[gname] = dict(stat=s, ci=ci, orig=ORIG[gname], n_items=a["n"])
    f = lambda k, d=1: f"{s[k]:.{d}f}"
    c = lambda k, d=1: f"[{ci[k][0]:.{d}f}, {ci[k][1]:.{d}f}]"
    o = ORIG[gname]
    lines += [f"## {NAMES[gname]}  (n questions = {a['n']}, hallucinations = {s['nH']}, correct answers = {s['nok']})\n",
              "| measure | held-out | 95% CI | original (300 q) |", "|---|---|---|---|",
              f"| hallucination rate % | {f('p0')} | | {o['p0']} |",
              f"| L2 clearance c2 % | {f('c2')} | {c('c2')} | {o['c2']} |",
              f"| L3 clearance c3 % | {f('c3')} | {c('c3')} | {o['c3']} |",
              f"| L2 false-block % | {f('fb2')} | {c('fb2')} | {o['fb2']} |",
              f"| L3 false-block % | {f('fb3')} | {c('fb3')} | {o['fb3']} |",
              f"| judge failure rate % | {f('fail_rate')} | | 25-30 |",
              f"| phi(L2, L3 catch) | {f('phi',2)} | {c('phi',2)} | 0.11-0.15 |  (Fisher p = {s['fisher']:.3f})",
              f"| passing both: observed (full) / independence % | {f('full')} / {f('ind')} | | |",
              f"| ratio observed/independence (full) | {f('ratio_full',2)} | {c('ratio_full',2)} | {o['ratio_full']} |",
              f"| ratio observed/independence (routed) | {f('ratio_routed',2)} | {c('ratio_routed',2)} | {o['ratio_routed']} |",
              f"| k* none / L2 / L2+L3 routed (200 q/day) | {s['k_none']} / {s['k_l2']} / {s['k_routed']} | {c('k_none',0)} / {c('k_l2',0)} / {c('k_routed',0)} | {o['k'][0]} / {o['k'][1]} / {o['k'][2]} |",
              f"| capacity reduction by L2 % | {f('red_l2')} | {c('red_l2')} | |\n"]
json.dump(out, open(os.path.join(RES, f"analysis_{JUDGE}.json"), "w"), indent=1, default=float)
open(os.path.join(RES, f"analysis_{JUDGE}.md"), "w").write("\n".join(lines))
print("\n".join(lines))
