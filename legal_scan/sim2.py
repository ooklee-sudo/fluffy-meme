import json, sys, numpy as np, warnings
warnings.filterwarnings("ignore")
import statsmodels.api as sm
import sim_regress as S
def run(tag):
    bank, rows = S.load("v3/real_law/real_fact_bank_v3.json", f"part/reallaw_{tag}.json", ("none",))
    base = S.build(bank, rows)
    # same_change: a listed provision carries the same old->new change
    byseed = {(r["seed"], r["kA"]): set(r["listed_idx"]) for r in rows}
    for d in base:
        L = byseed[(d["seed"], d["k"])]; f = bank[d["i"]]
        d["same"] = int(any(bank[j]["old"].strip() == f["old"].strip() and bank[j]["new"].strip() == f["new"].strip() for j in L if j != d["i"]))
    sib = [d for d in base if not d["dep"]]
    print("==", tag, "unlisted sibling obs", len(sib))
    for s in (0, 1):
        v = [d["ok"] for d in sib if d["same"] == s]; print(f"  same old->new change among listed = {s}: follow {np.mean(v):.2f} (n={len(v)})")
    for s in (0, 1):
        sub = [d for d in sib if d["same"] == s]
        if len(sub) < 30: continue
        q = np.quantile([d["sim"] for d in sub], [0, 1/3, 2/3, 1]); out = []
        for a, b in zip(q[:-1], q[1:]):
            v = [d["ok"] for d in sub if a <= d["sim"] <= b]; out.append(f"{np.mean(v):.2f}(n={len(v)})")
        print(f"  within same={s}: follow by sim tercile {out}")
    y = np.array([d["ok"] for d in sib], float); X = np.array([[1, d["sim"], d["same"]] for d in sib], float); g = np.array([d["i"] for d in sib])
    r = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": g})
    print(f"  logit (siblings only): sim {r.params[1]:+.2f} (se {r.bse[1]:.2f}, p={r.pvalues[1]:.3f}); same-change {r.params[2]:+.2f} (se {r.bse[2]:.2f}, p={r.pvalues[2]:.3f})")
    dep = [d for d in base if d["dep"]]
    print(f"  derived dependents unlisted: follow {np.mean([d['ok'] for d in dep]):.2f} (n={len(dep)}, distinct provisions {len({d['i'] for d in dep})})")
for t in ("v3qwen3", "v3qwen25", "v3olmo3"): run(t)
