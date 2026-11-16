"""Economic model, pattern (twin) structure. Types of provision after an update stream:
 L: amended and listed;  T: amended, unlisted, a listed 'twin' carries the same change;  U: amended, unlisted, no twin listed (singleton in the update stream);
 G: derived dependent, unlisted;  K: unrelated control (collateral damage).
Policies: A amend only; S stream-scoped retention; D dependency-scoped retention; P = D + list one representative of every uncovered change pattern + all derived dependents (pattern listing);
F = list everything affected (full listing); R = retrieval over a refreshed store (share theta of identification cost borne by the operator)."""
import json, math, collections, statistics as st
import numpy as np
mean = st.mean
import sim_regress as S

def per_type_rates(bank, rows, method, lam, kAs=None):
    """follow rates by type, pooled over seeds and amendment shares kA, from per-fact outcomes"""
    out = collections.defaultdict(list); ctl = []; comp = collections.defaultdict(list); unc = []
    for r in rows:
        if r["method"] != method or r["lam"] != lam or r["kdep"] != 0 or (kAs and r["kA"] not in kAs): continue
        listed = set(r["listed_idx"]); cnt = collections.Counter()
        pats_all = collections.defaultdict(list)
        for i, f in enumerate(bank):
            if f["kind"] != "changed": continue
            key = (f["old"].strip(), f["new"].strip()); isdep = (f["cluster"] == "C" and f["role"] == "dependent")
            if not isdep: pats_all[key].append(i)
            if i in listed: out["L"].append(r["ok"][i]); cnt["L"] += 1; continue
            if isdep: out["G"].append(r["ok"][i]); cnt["G"] += 1; continue
            twin = any((bank[j]["old"].strip(), bank[j]["new"].strip()) == key for j in listed if j != i)
            t = "T" if twin else "U"; out[t].append(r["ok"][i]); cnt[t] += 1
        # uncovered patterns: patterns (non-dependent amended provisions) with no listed member
        unc.append(sum(1 for k, v in pats_all.items() if not any(i in listed for i in v)))
        for t in "LTUG": comp[t].append(cnt[t])
        ctl += r["ctl_hard_ok"]
    p = {t: (mean(out[t]) if out[t] else float("nan")) for t in "LTUG"}; p["K"] = mean(ctl)
    c = {t: mean(comp[t]) for t in "LTUG"}; c["K"] = sum(f["kind"] == "control" for f in bank); c["UNC"] = mean(unc)
    return p, c

def policies(bank, rows, kAs=(0.5,)):
    # follow rates of twins are pooled over all kA (more data); composition at kA = 0.5
    pA, cA = per_type_rates(bank, rows, "none", 0.0, kAs); pD, cD = per_type_rates(bank, rows, "dep", 10.0, kAs); pS, cS = per_type_rates(bank, rows, "ss", 10.0, kAs)
    allk = (0.1, 0.25, 0.5, 0.75)
    pA_all, _ = per_type_rates(bank, rows, "none", 0.0, allk); pD_all, _ = per_type_rates(bank, rows, "dep", 10.0, allk)
    comp = cA  # composition at kA = 0.5
    P = {"A": dict(pA), "S": dict(pS), "D": dict(pD)}
    # pattern listing: D plus a listed representative for every uncovered pattern and all dependents listed.
    # Residual: unlisted twins follow at the rate observed when a twin was listed (inference, not directly tested);
    # singletons U become twins only through listing representatives (each uncovered pattern is listed once), so U -> 0 residual; G listed.
    P["P"] = dict(L=1.0, T=pD_all["T"], U=pD_all["T"], G=1.0, K=pD["K"])
    P["F"] = dict(L=1.0, T=1.0, U=1.0, G=1.0, K=pD["K"])
    P["R"] = None
    return P, comp, dict(pA_all=pA_all, pD_all=pD_all)

def resid(P, comp, nc=None):
    nc = comp["K"] if nc is None else nc
    out = {}
    for j, p in P.items():
        if p is None: continue
        if j == "P":   # after listing representatives all previously uncovered singletons/patterns have a listed twin
            n_T = comp["T"] + comp["U"] - comp["UNC"]; n_U = 0.0
            out[j] = n_T * (1 - p["T"]) + nc * (1 - p["K"])
        else:
            out[j] = comp["L"] * (1 - p["L"]) + comp["T"] * (1 - p["T"]) + comp["U"] * (1 - p["U"]) + comp["G"] * (1 - p["G"]) + nc * (1 - p["K"])
    return out

def labor(comp):
    return {"A": 0.0, "S": 0.0, "D": 0.0, "P": comp["UNC"] + comp["G"], "F": comp["T"] + comp["U"] + comp["G"]}

def phi(r, m, alpha, c, F, ell=1.0):
    return {j: alpha * c * m[j] + math.sqrt(2 * F * ell * alpha * r[j]) for j in r}

if __name__ == "__main__":
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else "v3qwen3"
    bank = json.load(open("v3/real_law/real_fact_bank_v3.json")); rows = [r for r in json.load(open(f"part/reallaw_{tag}.json")) if "ok" in r]
    P, comp, extra = policies(bank, rows)
    print(tag, "composition (kA=0.5):", {k: round(v, 1) for k, v in comp.items()})
    for j in ("A", "S", "D"): print(" ", j, {k: round(v, 2) for k, v in P[j].items()})
    print("  pooled-kA follow, twin/singleton: A", round(extra["pA_all"]["T"], 2), round(extra["pA_all"]["U"], 2), " D", round(extra["pD_all"]["T"], 2), round(extra["pD_all"]["U"], 2))
    r = resid(P, comp); m = labor(comp)
    print("  residual wrong provisions per event:", {k: round(v, 1) for k, v in r.items()}, "| labor:", {k: round(v, 1) for k, v in m.items()})
    for alpha, c, F in ((2, 2, 300), (2, 5, 300), (2, 1, 300), (6, 2, 300), (0.5, 2, 300)):
        ph = phi(r, m, alpha, c, F); print(f"  alpha={alpha} c={c} F={F}:", {k: round(v, 1) for k, v in ph.items()}, "->", min(ph, key=ph.get))
