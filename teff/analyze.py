"""Aggregate the revision study into the tables used in the manuscript/response.

  python analyze.py            # reads results/*.json, writes results/summary.json
"""
import glob
import json
import os

import numpy as np

from run_study import M_GRID

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
rng = np.random.default_rng(7)
B = 1000


def load(prefix):
    out = {}
    for f in sorted(glob.glob(os.path.join(RES, prefix + "_*.json"))):
        d = json.load(open(f))
        out[d["model"].split("/")[-1]] = d
    return out


def auc(a, b):
    """P(b > a) with ties 1/2."""
    a, b = np.asarray(a), np.asarray(b)
    gt = (b[:, None] > a[None, :]).mean()
    eq = (b[:, None] == a[None, :]).mean()
    return gt + 0.5 * eq


def two_sided(a):
    return max(a, 1 - a)


def boot_mean_ci(x, f=np.mean):
    x = np.asarray(x)
    v = [f(x[rng.integers(0, len(x), len(x))]) for _ in range(B)]
    return np.percentile(v, [2.5, 97.5])


def ece5(conf, corr):
    conf, corr = np.asarray(conf), np.asarray(corr)
    bins = np.minimum((conf * 5).astype(int), 4)
    e = 0.0
    for b in range(5):
        m = bins == b
        if m.any():
            e += m.mean() * abs(conf[m].mean() - corr[m].mean())
    return e


def sem_exact(comps):
    t = [tuple(c) for c in comps]
    _, cnt = np.unique(np.array(t), axis=0, return_counts=True)
    p = cnt / len(t)
    return float(-(p * np.log(p)).sum())


MARGINS = dict(entropy=0.10, conf=0.05, ece=0.10, sem=0.50, teff=0.50,
               nll=0.10, kl=0.10, teffdist=0.50, klres=0.10)


def indicator_series(traj, name, T):
    """Per-trajectory arrays needed to recompute a cell indicator on a resample."""
    if name == "entropy":
        return np.array([t["entropy"] for t in traj]), np.mean
    if name == "conf":
        return np.array([t["conf"] for t in traj]), np.mean
    if name == "nll":
        return np.array([t["nll_same"] for t in traj]), np.mean
    if name == "kl":
        return np.array([t["kl_same"] for t in traj]), np.mean
    raise KeyError(name)


def cell_value_boot(traj, name, T, margin_scale=1.0):
    """Return (value, lo, hi) of a cell indicator with trajectory bootstrap."""
    n = len(traj)
    if name in ("entropy", "conf", "nll", "kl"):
        x, f = indicator_series(traj, name, T)
        return float(f(x)), *boot_mean_ci(x, f)
    if name == "ece":
        conf = [np.array(t["conf_steps"]) for t in traj]
        cor = [np.array(t["correct_steps"]) for t in traj]

        def f(idx):
            return ece5(np.concatenate([conf[i] for i in idx]),
                        np.concatenate([cor[i] for i in idx]))
    elif name == "sem":
        comps = [t["comp"] for t in traj]

        def f(idx):
            return sem_exact([comps[i] for i in idx])
    else:
        raise KeyError(name)
    v = f(range(n))
    vals = [f(rng.integers(0, n, n)) for _ in range(B)]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(v), float(lo), float(hi)


def flag(clean, dist, name, margin):
    v0, lo, hi = clean
    v1 = dist[0]
    return (v1 < lo or v1 > hi) and abs(v1 - v0) >= margin


def matched_analysis(M):
    """Detection counts and AUC per model for main and variant conditions."""
    out = {}
    for model, d in M.items():
        traj, res = d["traj"], d["res"]
        out[model] = dict(flags={}, auc={}, ident={}, cells={})
        conds = sorted({k.split("|")[2] for k in traj})
        for cond in conds:
            if cond == "clean":
                continue
            fl = {k: [0, 0] for k in ["entropy", "conf", "ece", "sem", "nll",
                                      "kl", "teff", "teffdist", "klres"]}
            aucs = {k: [] for k in ["entropy", "conf", "gap", "nll_same",
                                    "kl_same", "teff_same", "teffdist_same",
                                    "nll_repair", "kl_repair", "teff_repair"]}
            for task, tdict in res.items():
                for T in (0.8, 2.0):
                    ck, dk = f"{T}|clean", f"{T}|{cond}"
                    if ck not in tdict["cells"] or dk not in tdict["cells"]:
                        continue
                    tc, td = traj[f"{task}|{ck}"], traj[f"{task}|{dk}"]
                    sc, sd = tdict["cells"][ck], tdict["cells"][dk]
                    for ind in ["entropy", "conf", "ece", "sem", "nll", "kl"]:
                        c0 = cell_value_boot(tc, ind, T)
                        c1 = cell_value_boot(td, ind, T)
                        fl[ind][1] += 1
                        fl[ind][0] += flag(c0, c1, ind, MARGINS[ind])
                    # T_eff (pooled, same-history reference) with the stored
                    # trajectory-bootstrap interval of the clean cell
                    s0, s1 = sc["same"], sd["same"]
                    if s0["identified"] and s1["identified"]:
                        fl["teff"][1] += 1
                        diff = (s1["teff"] - T) - (s0["teff"] - T)
                        out_ci = s1["teff"] < s0["boot_lo"] or s1["teff"] > s0["boot_hi"]
                        fl["teff"][0] += bool(out_ci and abs(diff) >= MARGINS["teff"])
                    fl["teffdist"][1] += 1
                    fl["teffdist"][0] += abs(s1["teff_dist"] - s0["teff_dist"]) >= MARGINS["teffdist"]
                    fl["klres"][1] += 1
                    fl["klres"][0] += abs(s1["kl_res"] - s0["kl_res"]) >= MARGINS["klres"]
                    for k in aucs:
                        if k == "gap":
                            a = [np.mean(t["conf_steps"]) - np.mean(t["correct_steps"]) for t in tc]
                            b = [np.mean(t["conf_steps"]) - np.mean(t["correct_steps"]) for t in td]
                        else:
                            a, b = [t[k] for t in tc], [t[k] for t in td]
                        aucs[k].append(two_sided(auc(a, b)))
            out[model]["flags"][cond] = {k: v for k, v in fl.items()}
            out[model]["auc"][cond] = {k: float(np.mean(v)) for k, v in aucs.items() if v}
        # identification statistics for the same-history reference
        thr = {"0.99": 0, "0.999": 0, "0.9999": 0, "interval": 0, "n": 0}
        widths = []
        for task, tdict in res.items():
            for k, s in tdict["cells"].items():
                r = s["same"]
                thr["n"] += 1
                thr["0.99"] += r["mean_ref_prob"] <= 0.99
                thr["0.999"] += r["mean_ref_prob"] <= 0.999
                thr["0.9999"] += r["mean_ref_prob"] <= 0.9999
                ok = (not r["at_boundary"]) and (not r["open_hi"]) and r["hi"] / r["lo"] <= 4.0
                thr["interval"] += ok
                widths.append(r["hi"] / r["lo"])
        # share of the context-induced divergence that a rescaling can remove
        sc_ex = {}
        for task, tdict in res.items():
            for k, s_ in tdict["cells"].items():
                T_, cond_ = k.split("|")
                if cond_ == "clean" or s_["same"]["kl_nom"] < 0.05:
                    continue
                sc_ex.setdefault(cond_, []).append(1 - s_["same"]["kl_res"] / s_["same"]["kl_nom"])
        out[model]["scale_explained"] = {c: dict(mean=float(np.mean(v)), n=len(v))
                                         for c, v in sc_ex.items()}
        out[model]["ident"] = dict(thr, median_hi_over_lo=float(np.median(widths)))
        # per-trajectory interval width (six choices)
        tw = [t["teffint_same"][1] / t["teffint_same"][0]
              for v in traj.values() for t in v if "teffint_same" in t]
        out[model]["ident"]["traj_median_hi_over_lo"] = float(np.median(tw)) if tw else None
        out[model]["ident"]["traj_frac_ratio_gt4"] = float(np.mean(np.array(tw) > 4)) if tw else None
    return out


def h_analysis(M):
    """H1 and H3 on every wording (matched cells; Teff - T, same-history ref)."""
    out = {}
    pairs = [("P0+C0", "P0"), ("P0+C2", "P0"), ("P1+C1", "P1"),
             ("P1+C2", "P1"), ("P2+C2", "P2")]
    for model, d in M.items():
        res = d["res"]
        o = dict(h1={}, h3={}, c_alone={})
        for task_cells in [res]:
            pass

        def gap(task, T, cond):
            s = res[task]["cells"].get(f"{T}|{cond}")
            if s is None or not s["same"]["identified"]:
                return None
            return s["same"]["teff"] - T

        conds = {k.split("|")[1] for t in res.values() for k in t["cells"]}
        for cond in sorted(conds - {"clean"}):
            up = tot = 0
            diffs = []
            for task in res:
                for T in (0.8, 2.0):
                    g, g0 = gap(task, T, cond), gap(task, T, "clean")
                    if g is None or g0 is None:
                        continue
                    tot += 1
                    up += (g - g0) >= 0.5
                    diffs.append(g - g0)
            o["h1"][cond] = dict(raised=up, identified=tot,
                                 mean_shift=float(np.mean(diffs)) if diffs else None)
        for both, press in pairs:
            ds = []
            for task in res:
                for T in (0.8, 2.0):
                    gb, gp = gap(task, T, both), gap(task, T, press)
                    if gb is None or gp is None:
                        continue
                    ds.append(gb - gp)
            o["h3"][f"{both} vs {press}"] = dict(
                n=len(ds), mean=float(np.mean(ds)) if ds else None,
                n_ge_05=int(np.sum(np.abs(ds) >= 0.5)) if ds else 0)
        out[model] = o
    return out


def grid_analysis(G, P):
    """Curve shapes on the full m-grid and by independently selected regimes."""
    out = {}
    for model, d in G.items():
        res = d["res"]
        o = {}
        for task, cells in res.items():
            temps = sorted({float(k.split("|")[1]) for k in cells})
            rows = {}
            for m in M_GRID:
                acc = np.array([cells[f"{m}|{T}"]["acc"] for T in temps])
                se = np.array([cells[f"{m}|{T}"]["se"] for T in temps])
                j = int(np.argmax(acc))
                interior = 0 < j < len(temps) - 1
                margin = min(acc[j] - acc[0], acc[j] - acc[-1])
                se_ok = margin >= 2 * np.sqrt(se[j] ** 2 + max(se[0], se[-1]) ** 2)
                rows[m] = dict(acc=acc.round(3).tolist(),
                               peak_T=temps[j], peak_acc=float(acc[j]),
                               interior=bool(interior and margin >= 0.10 and se_ok),
                               lock0=cells[f"{m}|{temps[0]}"]["lock"])
            o[task] = dict(temps=temps, by_m=rows)
        # regimes chosen on the main prompt vs on an independent wording
        sel = {}
        if model in P:
            for task in o:
                pr = P[model]["res"][task]
                sel[task] = {"main": {k: pr["main"][k] for k in ("weak", "sticky", "strong")},
                             "alt": {k: pr["alt"][k] for k in ("weak", "sticky", "strong")}}
        o["_regimes"] = sel
        counts = {}
        for src in ("main", "alt"):
            c = {r: [0, 0] for r in ("weak", "sticky", "strong")}
            for task in sel:
                for r in c:
                    m = sel[task][src][r]
                    if m is None:
                        continue
                    c[r][1] += 1
                    c[r][0] += o[task]["by_m"][m]["interior"]
            counts[src] = c
        o["_interior_counts"] = counts
        # interior peaks over the whole m axis (no regime selection at all)
        allm = {}
        for task in o:
            if task.startswith("_"):
                continue
            allm[task] = [m for m in M_GRID if o[task]["by_m"][m]["interior"]]
        o["_interior_m"] = allm
        out[model] = o
    return out


def threshold_sensitivity(G):
    """Identification flag under alternative saturation thresholds (grid cells)."""
    out = {}
    for model, d in G.items():
        rows = []
        for task, cells in d["res"].items():
            for k, c in cells.items():
                r = c["same"]
                ok_int = (not r["at_boundary"]) and (not r["open_hi"]) and r["hi"] / r["lo"] <= 4.0
                rows.append((r["mean_ref_prob"], ok_int, c["lock"], k.split("|")[1]))
        mrp = np.array([x[0] for x in rows])
        out[model] = dict(
            n=len(rows),
            ni_099=int((mrp > 0.99).sum()), ni_0999=int((mrp > 0.999).sum()),
            ni_09999=int((mrp > 0.9999).sum()),
            ni_interval=int(sum(not x[1] for x in rows)),
            between_099_and_0999=int(((mrp > 0.99) & (mrp <= 0.999)).sum()),
            interval_ni_but_below_0999=int(sum((not x[1]) and x[0] <= 0.999 for x in rows)))
    return out


def locked_analysis(G):
    """Fully locked cells (clean prompt, T=0.15, lock-in >= 0.95)."""
    rows = []
    for model, d in G.items():
        for task, cells in d["res"].items():
            for m in M_GRID:
                c = cells.get(f"{m}|0.15")
                if c is None or c["lock"] < 0.95:
                    continue
                rows.append(dict(
                    model=model, task=task, m=m, lock=c["lock"], acc=c["acc"],
                    entropy=c["entropy"], conf=c["conf"], ece=c["ece"],
                    sem=c["sem_ent"],
                    same_ident=c["same"]["identified"], same_teff=c["same"]["teff"],
                    same_mrp=c["same"]["mean_ref_prob"],
                    repair_ident=c["repair"]["identified"], repair_teff=c["repair"]["teff"],
                    repair_nll=c["repair"]["nll_nom"], repair_kl=c["repair"]["kl_nom"],
                    repair_top1=c["repair"]["ref_top1_match"],
                    prior_ident=c["prior"]["identified"], prior_teff=c["prior"]["teff"],
                    prior_nll=c["prior"]["nll_nom"], prior_top1=c["prior"]["ref_top1_match"]))
    return rows


def ref_strategy_matched(M):
    """Identification and fit of the three reference constructions on matched cells."""
    out = {}
    for model, d in M.items():
        acc = {t: dict(n=0, ident=0, teff_ge_05=0, top1=[], nll=[])
               for t in ("same", "repair", "prior")}
        for task, td in d["res"].items():
            for k, s in td["cells"].items():
                if k.endswith("|clean"):
                    continue
                for tag in acc:
                    r = s[tag]
                    acc[tag]["n"] += 1
                    acc[tag]["ident"] += r["identified"]
                    acc[tag]["top1"].append(r["ref_top1_match"])
                    acc[tag]["nll"].append(r["nll_nom"])
        out[model] = {t: dict(n=v["n"], identified=v["ident"],
                              mean_top1=float(np.mean(v["top1"])),
                              mean_nll=float(np.mean(v["nll"])))
                      for t, v in acc.items()}
    return out


def refcmp_analysis(R):
    """Same-history / gold-repaired / de-duplicated references."""
    out = {}
    for model, d in R.items():
        res, traj = d["res"], d["traj"]
        locked, ident = [], {t: [0, 0] for t in ("same", "repair", "dedup")}
        aucs = {t: [] for t in ("same", "repair", "dedup")}
        auc_teff = {t: [] for t in ("same", "repair", "dedup")}
        nll_cells = {t: [] for t in ("same", "repair", "dedup")}
        for task, td in res.items():
            for key, st in td["cells"].items():
                reg, m, T, cond = key.split("|")
                T = float(T)
                for t in ident:
                    ident[t][1] += 1
                    ident[t][0] += st[t]["identified"]
                if cond == "clean" and T == 0.15 and st["lock"] >= 0.9:
                    locked.append(dict(
                        task=task, regime=reg, m=int(m), lock=st["lock"], acc=st["acc"],
                        entropy=st["entropy"], conf=st["conf"], ece=st["ece"],
                        **{f"{t}_{k}": st[t][k] for t in ident
                           for k in ("identified", "teff", "nll_nom", "ref_top1_match")}))
                if cond != "clean" and T in (0.8, 2.0) and cond in ("P0", "C0", "P0+C0"):
                    ck = f"{reg}|{m}|{T}|clean"
                    for t in aucs:
                        a = [x["nll_" + t] for x in traj[f"{task}|{ck}"]]
                        b = [x["nll_" + t] for x in traj[f"{task}|{key}"]]
                        aucs[t].append(two_sided(auc(a, b)))
                        a = [x["teff_" + t] for x in traj[f"{task}|{ck}"]]
                        b = [x["teff_" + t] for x in traj[f"{task}|{key}"]]
                        auc_teff[t].append(two_sided(auc(a, b)))
                        nll_cells[t].append(st[t]["nll_nom"])
        out[model] = dict(
            locked=locked,
            identified={t: f"{a}/{b}" for t, (a, b) in ident.items()},
            auc_nll={t: float(np.mean(v)) for t, v in aucs.items() if v},
            auc_teff={t: float(np.mean(v)) for t, v in auc_teff.items() if v},
            mean_nll_distorted={t: float(np.mean(v)) for t, v in nll_cells.items() if v})
    return out


def free_analysis(F):
    out = {}
    for model, d in F.items():
        res = d["res"]
        se = d.get("se", {})
        o = {}
        for key, c in res.items():
            task, T, cond = key.split("|")
            o[key] = dict(
                teff=c["teff"], lo=c["lo"], hi=c["hi"], nll=c["nll"], ent=c["ent"],
                kl=c["kl"], acc=c["acc"], lock=c["lock"], ntok=c["ntok"],
                first_full=c["first_full"], first_restricted=c["first_restricted"],
                first_in_cand=c["first_in_cand"], t_main=c["timing"]["t_main"],
                t_ref=c["timing"]["t_ref"], steps=c["timing"]["steps"],
                se_nli=se.get(key, {}).get("se_nli"),
                se_exact=se.get(key, {}).get("se_exact"),
                n_clusters=se.get(key, {}).get("n_clusters"))
        # detection: pairs clean vs P0 / C0 / P0+C0 / C2 for T and task
        det = {}
        for cond in ("P0", "C0", "P0+C0", "C2"):
            cnt = {k: 0 for k in ("ent", "nll", "kl", "teff", "se_nli", "se_exact")}
            n = 0
            auc_ = {k: [] for k in ("ent", "nll", "kl", "teff")}
            for key in res:
                task, T, c = key.split("|")
                if c != cond:
                    continue
                ck = f"{task}|{T}|clean"
                a, b = res[ck], res[key]
                n += 1
                for ind in ("ent", "nll", "kl"):
                    xa, xb = np.array(a["traj"][ind]), np.array(b["traj"][ind])
                    lo, hi = boot_mean_ci(xa)
                    cnt[ind] += bool((xb.mean() < lo or xb.mean() > hi) and
                                     abs(xb.mean() - xa.mean()) >= 0.10)
                    auc_[ind].append(two_sided(auc(xa, xb)))
                ta, tb = np.array(a["traj"]["teff"]), np.array(b["traj"]["teff"])
                auc_["teff"].append(two_sided(auc(ta, tb)))
                cnt["teff"] += bool(b["teff"] > a["hi"] or b["teff"] < a["lo"]) and \
                    abs(b["teff"] - a["teff"]) >= 0.5
                if se.get(key) and se.get(ck):
                    for ind in ("se_nli", "se_exact"):
                        cnt[ind] += bool(
                            (se[key][ind] > se[ck]["boot_hi"] or se[key][ind] < se[ck]["boot_lo"])
                            and abs(se[key][ind] - se[ck][ind]) >= 0.5) if ind == "se_nli" \
                            else bool(abs(se[key][ind] - se[ck][ind]) >= 0.5)
            det[cond] = dict(n=n, flags=cnt,
                             auc={k: float(np.mean(v)) for k, v in auc_.items() if v})
        o["_detection"] = det
        # runtime
        tm = np.mean([c["timing"]["t_main"] for c in res.values()])
        tr = np.mean([c["timing"]["t_ref"] for c in res.values()])
        o["_runtime"] = dict(t_main=float(tm), t_ref=float(tr),
                             overhead=float(tr / tm),
                             nli_seconds=d.get("nli_seconds"),
                             nli_calls=d.get("nli_calls"))
        out[model] = o
    return out


if __name__ == "__main__":
    M, G, P, F = load("matched"), load("grid"), load("probe"), load("free")
    R = load("refcmp")
    summ = {}
    if M:
        summ["matched"] = matched_analysis(M)
        summ["hypotheses"] = h_analysis(M)
        summ["ref_strategy_matched"] = ref_strategy_matched(M)
        summ["runtime_matched"] = {m: dict(fwd_s=d.get("fwd_s"), n_fwd=d.get("n_fwd"))
                                   for m, d in M.items()}
    if G:
        summ["grid"] = grid_analysis(G, P)
        summ["locked"] = locked_analysis(G)
        summ["threshold_sensitivity"] = threshold_sensitivity(G)
    if P:
        summ["probe"] = {m: d["res"] for m, d in P.items()}
    if F:
        summ["free"] = free_analysis(F)
    if R:
        summ["refcmp"] = refcmp_analysis(R)
    json.dump(summ, open(os.path.join(RES, "summary.json"), "w"), indent=1,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("wrote summary.json with", list(summ))
