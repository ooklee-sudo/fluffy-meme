"""Paired daily-cost difference of adding the routed judge to L1+L2 (cost model of Section 4.4):
cost = 150*k* + 0.0001*classifier calls + 0.002*judge calls + 1*false blocks + H*residual hallucinations, 200 queries/day.
Positive difference = the judge saves money. Usage: python cost_heldout.py <judge> [credit]"""
import json, os, re, sys
import numpy as np
from scipy import stats

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
JUDGE = sys.argv[1]; CREDIT = len(sys.argv) > 2 and sys.argv[2] == "credit"
GENS = ["qwen0.5b", "smollm360m", "qwen1.5b"]
Q = 200


def kp(l): return int(stats.poisson.ppf(0.95, l)) if l > 0 else 0


def uns(raw):
    m = re.search(r"(UN\s*SUPPORT|SUPPORT)", raw.upper()); return bool(m) and m.group(1).startswith("UN")


def load(g):
    G = [json.loads(l) for l in open(f"{RES}/gen_{g}.jsonl")]
    J = {}
    for l in open(f"{RES}/judge_{JUDGE}_{g}.jsonl"):
        r = json.loads(l); J[r["id"]] = r
    n = len(G)
    ab = np.array([r["abstain"] for r in G]); H = np.array([(not r["abstain"]) and r["halluc"] for r in G])
    ok = np.array([(not r["abstain"]) and not r["halluc"] for r in G])
    l1 = np.array([bool(r.get("l1_block")) for r in G]); l2 = np.array([bool(r.get("l2_block")) for r in G])
    sc = np.array([r.get("l2_score", 1.0) for r in G])
    l3 = np.array([uns(J[r["id"]]["raw"]) and (CREDIT or not J[r["id"]]["failure"]) if r["id"] in J else False for r in G])
    return dict(n=n, ab=ab, H=H, ok=ok, l1=l1, l2=l2, sc=sc, l3=l3)


def cost(a, harm, with_judge):
    n = a["n"]; scale = Q / n
    b12 = a["l1"] | a["l2"]
    routed = (~b12) & (a["sc"] < 0.9) & ~a["ab"]
    blocked = b12 | (routed & a["l3"]) if with_judge else b12
    pass_h = (a["H"] & ~blocked).sum() * scale
    fb = (a["ok"] & blocked).sum() * scale
    k = kp(pass_h) if False else kp((a["H"] & ~blocked).sum() * scale)
    calls_cls = (~a["ab"]).sum() * scale; calls_j = (routed.sum() * scale) if with_judge else 0
    return 150 * k + 0.0001 * calls_cls + 0.002 * calls_j + fb + harm * pass_h


rng = np.random.default_rng(0)
print(f"judge={JUDGE}{' (credit)' if CREDIT else ''}: daily saving from adding the routed judge to L1+L2 (positive = judge saves money)")
for harm in (0, 100, 1000):
    for g in GENS:
        a = load(g)
        d0 = cost(a, harm, False) - cost(a, harm, True)
        bs = []
        for _ in range(500):
            ix = rng.integers(0, a["n"], a["n"]); b = {k: (v[ix] if isinstance(v, np.ndarray) else v) for k, v in a.items()}; b["n"] = a["n"]
            bs.append(cost(b, harm, False) - cost(b, harm, True))
        print(f"  harm=${harm:<5} {g:11s} saving ${d0:8.0f}  [{np.percentile(bs,2.5):.0f}, {np.percentile(bs,97.5):.0f}]")
