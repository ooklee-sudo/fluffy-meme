import json, sys, statistics as st
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/zen/x/replication_package/results/"
SD = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/"
mean = st.mean
# composition of one amending instrument, taken from the real bank at k = 0.5:
# 27 amended provisions = 6 net thresholds + 7.5 listed time limits/amounts (listed) + 7.5 unlisted siblings + 6 gross dependents
N_L, N_S, N_G = 13.5, 7.5, 6.0
POL = ["A", "S", "D", "F", "R"]
NAMES = {"A": "Amend only", "S": "Stream-scoped retention", "D": "Dependency-scoped retention", "F": "Full consequential listing", "R": "Retrieval, fully refreshed store"}

def params(real, rag, ctl="keep_control_hard"):
    def g(m, l, kA, kd, key):
        v = [r[key] for r in real if r["method"] == m and r["lam"] == l and r["kA"] == kA and r["kdep"] == kd and r[key] == r[key]]
        return mean(v)
    def rg(fmt, key):
        v = [r[key] for r in rag if r["variant"] == "launch" and r["format"] == fmt and r[key] == r[key]]
        return mean(v)
    p = {}
    for pol, (m, l) in {"A": ("none", 0.0), "S": ("ss", 10.0), "D": ("dep", 10.0)}.items():
        p[pol] = dict(l=g(m, l, .5, 0, "listed"), s=g(m, l, .5, 0, "unlisted_AB"), g=g(m, l, .5, 0, "ripple_dep"), c=g(m, l, .5, 0, ctl))
    p["F"] = dict(l=g("ss", 10.0, 1, 1, "listed"), s=1.0, g=1.0, c=g("ss", 10.0, 1, 1, ctl))
    p["R"] = dict(l=rg("rag_full", "listed"), s=rg("rag_full", "unlisted_AB"), g=rg("rag_full", "ripple_dep"), c=rg("rag_full", "keep_control"))
    return p

def cost(p, pol, kappa, nc, ec=1.0):
    """expected total cost in units of lambda (cost of one wrong answer on one provision)"""
    loss = N_L * (1 - p[pol]["l"]) + N_S * (1 - p[pol]["s"]) + N_G * (1 - p[pol]["g"]) + nc * ec * (1 - p[pol]["c"])
    extra = (N_S + N_G) if pol in ("F", "R") else 0.0
    return loss + kappa * extra

def best(p, kappa, nc, ec=1.0, pols=POL):
    return min(pols, key=lambda j: cost(p, j, kappa, nc, ec))

def breakevens(p):
    out = {}
    # F beats D iff kappa < kappa_star
    dl = lambda j, nc=0: cost(p, j, 0.0, nc)
    out["kappa_star_F_vs_D"] = (dl("D") - dl("F")) / (N_S + N_G)   # nc term handled below
    out["kappa_star_F_vs_A"] = None
    return out

def kstar(p, a, b, nc):
    return (cost(p, a, 0.0, nc) - cost(p, b, 0.0, nc)) / (N_S + N_G)  # valid when b is a listing policy and a is not

def nc_star_D_vs_A(p):
    # D beats A iff nc*(cA_loss - cD_loss) > D's extra loss on l,s,g
    dA = 1 - p["A"]["c"]; dD = 1 - p["D"]["c"]
    gain_per_nc = dA - dD
    pay = (N_L * (p["A"]["l"] - p["D"]["l"]) + N_S * (p["A"]["s"] - p["D"]["s"]) + N_G * (p["A"]["g"] - p["D"]["g"]))
    return pay / gain_per_nc if gain_per_nc > 0 else float("inf")

if __name__ == "__main__":
    real = json.load(open(R + "reallaw_v2.json")); rag = json.load(open(R + "rag_qwen7b.json"))
    p = params(real, rag)
    print(json.dumps(p, indent=1))
    print("nc* D vs A (hard)", nc_star_D_vs_A(p), " (easy)", nc_star_D_vs_A(params(real, rag, "keep_control")))
    for nc in (66, 500, 5000):
        print(nc, "kstar F vs D", kstar(p, "D", "F", nc), "F vs A", kstar(p, "A", "F", nc))
