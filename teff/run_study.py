"""Revision study: matched-cell, attractor-grid and probe stages.

Usage:
  python run_study.py matched --model Qwen/Qwen2.5-0.5B-Instruct --n 40
  python run_study.py grid    --model ... --n 30
  python run_study.py probe   --model ...
Outputs go to results/<stage>_<model>.json (+ .npz with per-step arrays).
"""
import argparse
import json
import os
import time

import numpy as np

from teff_core import (GRID, LM, PROBE_INSTR, TASKS, cell_seed, ece_5bin,
                       entropy_nats, make_user, softmax, teff_cell, teff_dist,
                       boot_teff)

M_GRID = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]
N_STEPS = 6
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def short(name):
    return name.split("/")[-1]


def hist_text(items, idx):
    return " ".join(items[i] for i in idx)


def dedup_idx(idx):
    """Collapse runs of identical consecutive items (label-free history repair)."""
    out = []
    for i in idx:
        if not out or out[-1] != i:
            out.append(i)
    return out


def probe_m(lm, task, instr=None):
    """Attractor strengths by the manuscript's probe rule (Section 4.1).

    p(correct next | clean prompt, m repeated items) at T = 0.15.
    sticky: smallest m with p < 0.05; weak: largest probed m below sticky with
    p > 0.95; strong: smallest probed m >= 2 * sticky.
    """
    items = TASKS[task]["items"]
    cand = lm.cand_ids(items)
    pre = lm.chat_prefix(make_user(task, instr=instr))
    p = {}
    for m in M_GRID:
        z = lm.last_logits(pre, hist_text(items, [0, 1] + [1] * m))[cand].numpy()
        p[m] = float(softmax(z[None], 0.15)[0, 2])
    sticky = next((m for m in M_GRID if p[m] < 0.05), None)
    weak = None
    if sticky is not None:
        below = [m for m in M_GRID if m < sticky and p[m] > 0.95]
        weak = max(below) if below else None
    strong = None
    if sticky is not None:
        big = [m for m in M_GRID if m >= 2 * sticky]
        strong = min(big) if big else None
    return dict(p=p, weak=weak, sticky=sticky, strong=strong)


def run_cell(lm, task, m, T, n, pressure=None, contam=None, seed_key="",
             probe_instr=None):
    """n trajectories of N_STEPS choices. Returns per-step arrays."""
    items = TASKS[task]["items"]
    K = len(items)
    cand = lm.cand_ids(items)
    att = items[1]
    pre_s = lm.chat_prefix(make_user(task, pressure, contam, att, probe_instr))
    pre_c = lm.chat_prefix(make_user(task, instr=probe_instr))
    rng = np.random.default_rng(cell_seed(lm.name, task, m, T, pressure,
                                          contam, seed_key))
    idxs = [[0, 1] + [1] * m for _ in range(n)]
    rows = dict(Z=[], Vs=[], Vr=[], Vp=[], Vd=[], y=[], tid=[], last=[], step=[])
    for t in range(N_STEPS):
        ht = [hist_text(items, ix) for ix in idxs]
        hr = [hist_text(items, list(range(ix[-1] + 1))) for ix in idxs]
        Z = lm.logits_batch(pre_s, ht)
        Vs = lm.logits_batch(pre_c, ht)
        Vr = lm.logits_batch(pre_c, hr)
        Vp = lm.logits_batch(pre_c, [items[0]] * n)
        Vd = lm.logits_batch(pre_c, [hist_text(items, dedup_idx(ix)) for ix in idxs])
        for tr in range(n):
            z = Z[tr][cand].numpy().astype(np.float64)
            y = int(rng.choice(K, p=softmax(z, T)))
            for k, v in (("Z", z),
                         ("Vs", Vs[tr][cand].numpy().astype(np.float64)),
                         ("Vr", Vr[tr][cand].numpy().astype(np.float64)),
                         ("Vp", Vp[tr][cand].numpy().astype(np.float64)),
                         ("Vd", Vd[tr][cand].numpy().astype(np.float64)),
                         ("y", y), ("tid", tr), ("last", idxs[tr][-1]),
                         ("step", t)):
                rows[k].append(v)
            idxs[tr].append(y)
    out = {k: np.array(v) for k, v in rows.items()}
    out["comps"] = [tuple(ix[-N_STEPS:]) for ix in idxs]
    return out


def cell_stats(c, T, with_boot=False):
    """Indicators on one cell (all trajectories pooled)."""
    Z, y, last = c["Z"], c["y"], c["last"]
    n = len(y)
    r = np.arange(n)
    P = softmax(Z, T)
    correct = (y == last + 1).astype(float)
    s = dict(n_traj=int(c["tid"].max() + 1), acc=float(correct.mean()),
             lock=float((y == 1).mean()),
             rep=float((y == last).mean()),
             entropy=entropy_nats(P), conf=float(P[r, y].mean()),
             ece=ece_5bin(P[r, y], correct))
    cnt = {}
    for cmp_ in c["comps"]:
        cnt[cmp_] = cnt.get(cmp_, 0) + 1
    pr = np.array(list(cnt.values())) / len(c["comps"])
    s["sem_ent_discrete"] = float(-(pr * np.log(pr)).sum())
    for tag, V in (("same", c["Vs"]), ("repair", c["Vr"]), ("prior", c["Vp"]),
                   ("dedup", c["Vd"])):
        e = teff_cell(V, y, T)
        d = teff_dist(Z, V, T)
        pref = softmax(V, T)
        # divergence and log-likelihood baselines at the NOMINAL temperature
        kl = float((P * (np.log(np.clip(P, 1e-300, None)) -
                         np.log(np.clip(pref, 1e-300, None)))).sum(1).mean())
        s[tag] = dict(
            teff=e["teff"], lo=e["lo"], hi=e["hi"], open_hi=e["open_hi"],
            at_boundary=e["at_boundary"], identified=e["identified"],
            mean_ref_prob=e["mean_ref_prob"], nll_nom=e["nll_nom_per_step"],
            ll_at_teff=e["ll_per_step"], kl_nom=kl,
            teff_dist=d["teff_dist"], kl_res=d["kl_res"],
            ref_top1_match=float((pref.argmax(1) == y).mean()))
        if with_boot and tag == "same":
            lo, hi = boot_teff(V, y, T, c["tid"])
            s[tag]["boot_lo"], s[tag]["boot_hi"] = lo, hi
    return s


def traj_values(c, T):
    """Per-trajectory indicator values (for AUC)."""
    out = []
    for tr in range(int(c["tid"].max() + 1)):
        sel = c["tid"] == tr
        Z, y = c["Z"][sel], c["y"][sel]
        r = np.arange(len(y))
        P = softmax(Z, T)
        v = dict(entropy=entropy_nats(P), conf=float(P[r, y].mean()),
                 conf_steps=P[r, y].round(5).tolist(),
                 correct_steps=(y == c["last"][sel] + 1).astype(int).tolist(),
                 comp=[int(i) for i in y])
        for tag, key in (("same", "Vs"), ("repair", "Vr"), ("prior", "Vp"),
                         ("dedup", "Vd")):
            V = c[key][sel]
            pref = softmax(V, T)
            v["nll_" + tag] = float(-np.log(np.clip(pref[r, y], 1e-300, None)).mean())
            v["kl_" + tag] = float((P * (np.log(np.clip(P, 1e-300, None)) -
                                         np.log(np.clip(pref, 1e-300, None)))
                                    ).sum(1).mean())
            e = teff_cell(V, y, T)
            v["teff_" + tag] = e["teff"]
            v["teffint_" + tag] = [e["lo"], e["hi"]]
            v["ident_" + tag] = e["identified"]
            v["teffdist_" + tag] = teff_dist(Z, V, T)["teff_dist"]
        out.append(v)
    return out


def stage_matched(lm, n, tasks, temps, conds, out):
    res = {}
    traj = {}
    t0 = time.time()
    for task in tasks:
        pr = probe_m(lm, task)
        res[task] = dict(probe=pr, cells={})
        m = pr["sticky"]
        if m is None:
            continue
        for T in temps:
            for cname, (pres, cont) in conds.items():
                key = f"{T}|{cname}"
                c = run_cell(lm, task, m, T, n, pres, cont, "matched")
                st = cell_stats(c, T, with_boot=True)
                res[task]["cells"][key] = st
                traj[f"{task}|{key}"] = traj_values(c, T)
                print(f"[{short(lm.name)}] {task} m={m} T={T} {cname:8s} "
                      f"acc={st['acc']:.2f} lock={st['lock']:.2f} "
                      f"Teff={st['same']['teff']:.2f} "
                      f"ni={not st['same']['identified']} "
                      f"({time.time() - t0:.0f}s)", flush=True)
        json.dump(dict(model=lm.name, n=n, res=res, traj=traj),
                  open(out, "w"))
    json.dump(dict(model=lm.name, n=n, res=res, traj=traj,
                   fwd_s=lm.time_fwd, n_fwd=lm.n_fwd), open(out, "w"))


def stage_grid(lm, n, tasks, temps, out):
    res = {}
    t0 = time.time()
    for task in tasks:
        res[task] = {}
        for m in M_GRID:
            for T in temps:
                c = run_cell(lm, task, m, T, n, seed_key="grid")
                st = cell_stats(c, T)
                res[task][f"{m}|{T}"] = dict(
                    acc=st["acc"], n=st["n_traj"], lock=st["lock"],
                    se=float(np.sqrt(st["acc"] * (1 - st["acc"]) /
                                     (st["n_traj"] * N_STEPS))),
                    entropy=st["entropy"], conf=st["conf"], ece=st["ece"],
                    sem_ent=st["sem_ent_discrete"],
                    same=st["same"], repair=st["repair"], prior=st["prior"])
            print(f"[{short(lm.name)}] grid {task} m={m} "
                  f"({time.time() - t0:.0f}s)", flush=True)
        json.dump(dict(model=lm.name, n=n, res=res), open(out, "w"))


def stage_refcmp(lm, n, tasks, out):
    """Alternative reference constructions on the sticky (T=0.15, 0.8, 2.0) and
    strong (T=0.15) attractors, clean prompt plus the three distortions."""
    res, traj = {}, {}
    t0 = time.time()
    for task in tasks:
        pr = probe_m(lm, task)
        res[task] = dict(probe=pr, cells={})
        plan = []
        if pr["sticky"] is not None:
            for T in (0.15, 0.8, 2.0):
                for cname, pc in CONDS_MAIN.items():
                    plan.append((pr["sticky"], "sticky", T, cname, pc))
        if pr["strong"] is not None:
            plan.append((pr["strong"], "strong", 0.15, "clean", (None, None)))
        for m, reg, T, cname, (pres, cont) in plan:
            c = run_cell(lm, task, m, T, n, pres, cont, "refcmp")
            key = f"{reg}|{m}|{T}|{cname}"
            res[task]["cells"][key] = cell_stats(c, T)
            traj[f"{task}|{key}"] = traj_values(c, T)
            print(f"[{short(lm.name)}] refcmp {task} {key} "
                  f"({time.time() - t0:.0f}s)", flush=True)
        json.dump(dict(model=lm.name, n=n, res=res, traj=traj), open(out, "w"))


def stage_probe(lm, out):
    res = {}
    for task in TASKS:
        res[task] = dict(main=probe_m(lm, task),
                         alt=probe_m(lm, task, PROBE_INSTR[task]))
    json.dump(dict(model=lm.name, res=res), open(out, "w"))
    for task, r in res.items():
        print(task, {k: (v["weak"], v["sticky"], v["strong"])
                     for k, v in r.items()})


CONDS_MAIN = {"clean": (None, None), "P0": ("P0", None), "C0": (None, "C0"),
              "P0+C0": ("P0", "C0")}
CONDS_VAR = dict(CONDS_MAIN, **{
    "P1": ("P1", None), "P2": ("P2", None), "C1": (None, "C1"),
    "C2": (None, "C2"), "P0+C2": ("P0", "C2"), "P1+C1": ("P1", "C1"),
    "P1+C2": ("P1", "C2"), "P2+C2": ("P2", "C2")})

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["matched", "grid", "probe", "refcmp"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--tasks", default="alphabet,months,planets,numbers")
    ap.add_argument("--temps", default="")
    ap.add_argument("--variants", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    lm = LM(a.model)
    tasks = a.tasks.split(",")
    out = os.path.join(OUT, f"{a.stage}_{short(a.model)}.json")
    if a.stage == "probe":
        stage_probe(lm, out)
    elif a.stage == "refcmp":
        stage_refcmp(lm, a.n, tasks, out)
    elif a.stage == "matched":
        temps = [float(x) for x in (a.temps or "0.8,2.0").split(",")]
        stage_matched(lm, a.n, tasks, temps,
                      CONDS_VAR if a.variants else CONDS_MAIN, out)
    else:
        temps = [float(x) for x in (a.temps or "0.15,0.8,1.2,2.0,3.0,4.0").split(",")]
        stage_grid(lm, a.n, tasks, temps, out)
