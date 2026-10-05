import sys, json, numpy as np
from scipy.stats import spearmanr, linregress
from games import shapley, loo

def comps(u, n):  # u[..., mask, n+1] -> auth utility, gen utility
    return u[..., :n].mean(-1), u[..., n]

def bs_ci(f, x, y, B=2000, seed=0):
    r = np.random.default_rng(seed); vals = []
    for _ in range(B):
        i = r.integers(0, len(x), len(x))
        if len(set(x[i])) > 1: vals.append(f(x[i], y[i]))
    return np.percentile(vals, [2.5, 97.5]).round(3).tolist()

def analyze(path, lam=1.0):
    d = np.load(path); n = int(np.log2(d["U"].shape[0])); M = 1 << n; full = M - 1
    out = {"n": n}; ua, ug = comps(d["U"], n)
    games = {"auth": ua - ua[0], "gen": ug - ug[0]}
    games["total"] = games["auth"] + lam * games["gen"]
    phi = {k: shapley(g, n) for k, g in games.items()}
    out["phi_v"] = {k: v.round(4).tolist() for k, v in phi.items()}
    out["loo_v"] = {k: loo(g, n).round(4).tolist() for k, g in games.items()}
    out["v(N)"] = {k: round(float(g[full]), 4) for k, g in games.items()}
    # seed noise vs marginal effect (retrain)
    ns = d["noise"]; sd = [(m, *[float(np.std(comps(ns[i][:, None, :], n)[j].ravel(), ddof=1)) for j in (0, 1)]) for i, m in enumerate(d["noise_masks"])]
    out["seed_noise_sd(auth,gen)"] = [[int(m), round(a, 4), round(g, 4)] for m, a, g in sd]
    out["median_|LOO|(auth)"] = round(float(np.median(np.abs(loo(games["auth"], n)))), 4)
    out["median_|phi|(auth)"] = round(float(np.median(np.abs(phi["auth"]))), 4)
    out["strengths"] = d["strengths"].tolist(); res = []
    for si, st in enumerate(d["strengths"]):
        ha, hg = comps(d["Uh"][si], n); r = {"steps": int(st)}
        eps = {"auth": ha - ua, "gen": hg - ug}; eps["total"] = eps["auth"] + lam * eps["gen"]
        vh = {k: (ha - ua[0]) if k == "auth" else (hg - ug[0]) if k == "gen" else (ha - ua[0]) + lam * (hg - ug[0]) for k in eps}
        pe = {k: shapley(e, n) for k, e in eps.items()}; ph = {k: shapley(v, n) for k, v in vh.items()}
        r["eps0"] = {k: round(float(e[0]), 4) for k, e in eps.items()}
        # rho (excess on forgotten groups) and kappa (deficit elsewhere), eps = rho - kappa for the auth+gen total
        du = d["Uh"][si] - d["U"]; rho = np.zeros(M); kap = np.zeros(M)
        for m in range(M):
            f = [g for g in range(n) if not (m >> g) & 1]; k = [g for g in range(n) if (m >> g) & 1]
            rho[m] = du[m, f].sum() / n if f else 0
            kap[m] = -(du[m, k].sum() / n + lam * du[m, n])
        r["rho0"], r["kappa0"] = round(float(rho[0]), 4), round(float(kap[0]), 4)
        r["sum_phi_vhat_minus_vN"] = round(float(ph["total"].sum() - games["total"][full]), 4)  # identity: = -eps(0)
        r["phi_eps_auth"] = pe["auth"].round(4).tolist()
        r["bias_L1(auth)"] = round(float(np.abs(pe["auth"]).sum()), 4)
        r["spearman(phi_v, phi_vhat)"] = round(float(spearmanr(phi["auth"], ph["auth"])[0]), 3)
        # sequential variant
        sp, sv = d["seq_perms"][si], d["seq_vals"][si]; seqphi = np.zeros(n); cnt = np.zeros(n)
        for p, v in zip(sp, sv):
            for k, g in enumerate(p):
                seqphi[g] += v[k, :n].mean() - v[k + 1, :n].mean(); cnt[g] += 1
        seqphi /= cnt
        r["phi_seq_auth"] = seqphi.round(4).tolist()
        r["order_dependence_L1(auth)"] = round(float(np.abs(seqphi - ph["auth"]).sum()), 4)
        r["spearman(phi_seq, phi_vhat_setfn)"] = round(float(spearmanr(seqphi, ph["auth"])[0]), 3)
        r["phi_vhat_auth"] = ph["auth"].round(4).tolist()
        res.append(r)
    out["by_strength"] = res
    out["relearn_attack_auth@T=empty"] = {"steps": d["strengths"].tolist(), "relearn_k=[0,5,20,60]": comps(d["attack"], n)[0].round(3).tolist(), "retrain_baseline": round(float(ua[0]), 3)}
    reps = d["reps"]
    if len(set(reps.tolist())) > 1:   # manipulation setting
        out["P1"] = {"LOO_dup_groups": [round(loo(games["auth"], n)[g], 4) for g in (0, 1)], "phi_dup_groups": phi["auth"][:2].round(4).tolist()}
        k = np.log2(np.array(reps[2:], float)); P3 = []
        for si, st in enumerate(d["strengths"]):
            dphi = np.array(res[si]["phi_vhat_auth"])[2:] - phi["auth"][2:]
            lr = linregress(k, dphi)
            P3.append({"steps": int(st), "slope_per_doubling": round(lr.slope, 4), "CI95": bs_ci(lambda a, b: linregress(a, b).slope, k, dphi), "spearman(k, dphi)": round(float(spearmanr(k, dphi)[0]), 3)})
        out["P3"] = P3; out["reps"] = reps.tolist()
        out["P3_phi_v_vs_k"] = round(float(linregress(k, phi["auth"][2:]).slope), 4)
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        o = analyze(p); json.dump(o, open(p.replace(".npz", "_analysis.json"), "w"), indent=1); print(json.dumps(o, indent=1)[:6000])
