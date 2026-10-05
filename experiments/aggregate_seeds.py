#!/usr/bin/env python3
"""Aggregate several seeds of unlearn_audit_exp.py outputs into mean / sd / 95% CI tables.

Layout under --root (what RUNPOD.md produces):
  main/ + extra/   -> seed 0   (retrain.json from main; unlearn.json merged from main and extra)
  seed1/ ... seedK -> seeds 1..K (retrain.json, unlearn.json)
Usage:  python experiments/aggregate_seeds.py --root /workspace/results
Note: the seed also changes which authors form each group, so between-seed variation includes group composition.
"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unlearn_audit_exp import shapley_from_table, v_table, NG

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def load_json(p): return json.load(open(p)) if os.path.exists(p) else None


def load_seed(dirs):
    retr, unl = None, {}
    for d in dirs:
        r = load_json(os.path.join(d, "retrain.json"))
        if r is not None and retr is None: retr = r
        u = load_json(os.path.join(d, "unlearn.json"))
        if u: unl.update({int(k): v for k, v in u.items()})
    return retr, unl


def seed_stats(retr, unl):
    U = {int(k): v for k, v in retr["U"].items()}
    out = {"shapley": shapley_from_table(v_table(U)), "vN": v_table(U)[(1 << NG) - 1],
           "author_empty": float(np.mean(U[0]["groups"])), "author_full": float(np.mean(U[(1 << NG) - 1]["groups"])),
           "control": retr.get("control_relearn"), "by_s": {}}
    for s, r in sorted(unl.items()):
        Uh = {int(k): v for k, v in r["Uhat"].items()}
        A = lambda t: float(np.mean(t["groups"]))
        eps0 = A(Uh[0]) + Uh[0]["general"] - A(U[0]) - U[0]["general"]
        rho0 = float(np.mean(np.array(Uh[0]["groups"]) - np.array(U[0]["groups"])))
        kap0 = -(Uh[0]["general"] - U[0]["general"])
        phi_eps = shapley_from_table({m: A(Uh[m]) - A(U[m]) for m in Uh})
        phi_set = shapley_from_table({m: A(Uh[m]) - A(U[0]) for m in Uh})
        seq = np.mean([x["credit"] for x in r["seq"]], axis=0)
        rl = r["relearn_empty"]
        out["by_s"][s] = {"eps0": eps0, "rho0": rho0, "kappa0": kap0, "L1_eps": float(np.abs(phi_eps).sum()),
                          "L1_seq_set": float(np.abs(seq - np.array(phi_set)).sum()),
                          "relearn_before": rl["before"]["public"], "relearn_after": rl["after"]["public"],
                          "excess_recovery": rl["after"]["public"] - (out["control"]["after"]["public"] if out["control"] else float("nan"))}
    ss = sorted(out["by_s"]); cross = None
    for a, b in zip(ss, ss[1:]):
        ea, eb = out["by_s"][a]["eps0"], out["by_s"][b]["eps0"]
        if ea > 0 >= eb: cross = a + (b - a) * ea / (ea - eb); break
    out["sign_change"] = cross
    return out


def ms(x):
    x = np.array([v for v in x if v is not None and not (isinstance(v, float) and math.isnan(v))], float); n = len(x)
    if n == 0: return "n/a"
    if n == 1: return f"{x[0]:.3f} (n=1)"
    sd = x.std(ddof=1); h = T975.get(n - 1, 1.96) * sd / math.sqrt(n)
    return f"{x.mean():.3f} ± {sd:.3f} [{x.mean() - h:.3f}, {x.mean() + h:.3f}] (n={n})"


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", default="/workspace/results"); p.add_argument("--out", default=None)
    a = p.parse_args()
    seeds = {}
    if os.path.isdir(os.path.join(a.root, "main")):
        seeds[0] = load_seed([os.path.join(a.root, "main"), os.path.join(a.root, "extra")])
    for d in sorted(os.listdir(a.root)):
        if d.startswith("seed") and d[4:].isdigit(): seeds[int(d[4:])] = load_seed([os.path.join(a.root, d)])
    stats = {k: seed_stats(*v) for k, v in seeds.items() if v[0] is not None}
    lines = ["# Seed aggregation (mean ± sd [95% CI t-interval], n = number of seeds)", ""]
    lines += ["## Per-seed exact Shapley values (groups differ by seed)", "", "| seed | Shapley values | sum = v(N) | spread (max-min) | author U(empty) -> U(full) | control relearn before -> after |", "|---|---|---|---|---|---|"]
    for k, st in sorted(stats.items()):
        c = st["control"]; cs = f"{c['before']['public']:.3f} -> {c['after']['public']:.3f}" if c else "n/a"
        lines.append(f"| {k} | {', '.join(f'{x:.4f}' for x in st['shapley'])} | {st['vN']:.4f} | {max(st['shapley']) - min(st['shapley']):.4f} | {st['author_empty']:.3f} -> {st['author_full']:.3f} | {cs} |")
    lines += ["", f"Spread across seeds: {ms([max(s['shapley']) - min(s['shapley']) for s in stats.values()])}", f"v(N) across seeds: {ms([s['vN'] for s in stats.values()])}",
              f"Sign change of eps(empty) (strength, linear interp.): {ms([s['sign_change'] for s in stats.values()])}", ""]
    allS = sorted({s for st in stats.values() for s in st["by_s"]})
    lines += ["## Unlearning strengths", "", "| s | eps(0) | rho(0) | L1(phi(eps)) | L1(seq-set) | relearn after | excess over control |", "|---|---|---|---|---|---|---|"]
    for s in allS:
        g = lambda key: [st["by_s"][s][key] for st in stats.values() if s in st["by_s"]]
        lines.append(f"| {s} | {ms(g('eps0'))} | {ms(g('rho0'))} | {ms(g('L1_eps'))} | {ms(g('L1_seq_set'))} | {ms(g('relearn_after'))} | {ms(g('excess_recovery'))} |")
    txt = "\n".join(lines); print(txt)
    if a.out: open(a.out, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
