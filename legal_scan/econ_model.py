"""Economic model of update governance for a knowledge-bearing language-model system.
Policies j: A amend only, S stream-scoped retention, D dependency-scoped retention, F full consequential listing (list all affected provisions),
R retrieval over a fully refreshed store (identification cost borne partly by the legislature: share theta).
Per amendment event, policy j leaves r_j provisions wrong (stale amended/dependent provisions plus collateral damage to controls).
Wrong provisions accumulate until a full refresh (cost F) resets the stock. Events arrive at rate alpha; each wrong provision-year costs ell.
Average cost rate of policy j with refresh interval T:  alpha*c*m_j + F/T + ell*alpha*r_j*T/2  ->  T*=sqrt(2F/(ell*alpha*r_j)),  Phi_j = alpha*c*m_j + sqrt(2*F*ell*alpha*r_j)."""
import json, math, statistics as st
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
mean = st.mean
POL = ["A", "S", "D", "F", "R"]
NAMES = {"A": "Amend only", "S": "Stream-scoped retention", "D": "Dependency-scoped retention", "F": "Full consequential listing", "R": "Retrieval, refreshed store"}

def outcomes(real, rag, ctl="keep_control_hard", kA=0.5):
    g = lambda m, l, ka, kd, key: mean([r[key] for r in real if r["method"] == m and r["lam"] == l and r["kA"] == ka and r["kdep"] == kd and r[key] == r[key]])
    rg = lambda var, fmt, key: mean([r[key] for r in rag if r["variant"] == var and r["format"] == fmt and r[key] == r[key]])
    p = {}
    for pol, (m, l) in {"A": ("none", 0.0), "S": ("ss", 10.0), "D": ("dep", 10.0)}.items():
        p[pol] = dict(l=g(m, l, kA, 0, "listed"), s=g(m, l, kA, 0, "unlisted_AB"), g=g(m, l, kA, 0, "ripple_dep"), c=g(m, l, kA, 0, ctl))
    p["F"] = dict(l=g("ss", 10.0, 1, 1, "listed"), s=1.0, g=1.0, c=g("ss", 10.0, 1, 1, ctl))
    p["R"] = dict(l=rg("launch", "rag_full", "listed"), s=rg("launch", "rag_full", "unlisted_AB"), g=rg("launch", "rag_full", "ripple_dep"), c=rg("launch", "rag_full", "keep_control"))
    return p

def composition(bank, kA=0.5):
    ch = [f for f in bank if f["kind"] == "changed"]
    A = [f for f in ch if f["cluster"] in "AB"]; Cb = [f for f in ch if f["cluster"] == "C" and f["role"] == "base"]; Cd = [f for f in ch if f["cluster"] == "C" and f["role"] == "dependent"]
    return dict(NL=len(Cb) + kA * len(A), NS=(1 - kA) * len(A), NG=len(Cd), NC=sum(f["kind"] == "control" for f in bank))

def resid(p, comp, nc=None):
    nc = comp["NC"] if nc is None else nc
    return {j: comp["NL"] * (1 - p[j]["l"]) + comp["NS"] * (1 - p[j]["s"]) + comp["NG"] * (1 - p[j]["g"]) + nc * (1 - p[j]["c"]) for j in p}

def labor(comp, theta=0.2):
    n = comp["NS"] + comp["NG"]
    return {"A": 0.0, "S": 0.0, "D": 0.0, "F": n, "R": theta * n}

def phi(r, m, alpha, c, F, ell=1.0):
    return {j: alpha * c * m[j] + math.sqrt(2 * F * ell * alpha * r[j]) for j in r}

def best(r, m, alpha, c, F, pols=POL):
    ph = phi(r, m, alpha, c, F); return min(pols, key=lambda j: ph[j])

def index_listing(r, m, alpha, c, F, ell=1.0, vs="D", pol="F"):
    """Psi = (sqrt-term of the refresh-only policy)/(listing labor cost); listing preferred iff Psi > 1"""
    return math.sqrt(2 * F * ell * alpha * r[vs]) / (alpha * c * m[pol])

if __name__ == "__main__":
    R = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/zen/x/replication_package/"
    real = json.load(open(R + "results/reallaw_v2.json")); rag = json.load(open(R + "results/rag_qwen7b.json")); bank = json.load(open(R + "real_law/real_fact_bank_v2.json"))
    comp = composition(bank); p = outcomes(real, rag); r = resid(p, comp); m = labor(comp)
    print("composition", comp); print("residual wrong per event r_j", {j: round(v, 2) for j, v in r.items()})
    for alpha, c, F in ((2, 5, 200), (2, 1, 200), (12, 5, 200), (0.5, 5, 200), (2, 20, 200)):
        ph = phi(r, m, alpha, c, F); print(f"alpha={alpha} c={c} F={F}", {j: round(v, 1) for j, v in ph.items()}, "->", best(r, m, alpha, c, F), " Psi(F vs D)=", round(index_listing(r, m, alpha, c, F), 2))
