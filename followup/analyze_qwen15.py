import json, math, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
full = json.load(open("results/qwen15_full.json")); auto = json.load(open("results/autoscope_qwen15.json"))
nz = lambda x: None if x is None or (isinstance(x, float) and math.isnan(x)) else x
# ---- Experiment 1: unscoped KL, currency vs lambda
un = {(r["rho"], r["lam"]): r for r in full if r["q"] is None}
sc = {(r["rho"], r["q"]): r for r in full if r["q"] is not None}
print("EXPERIMENT 1 (seed 1): currency (continuity) by rho x lambda")
for rho in (0.1, 0.3, 0.5, 0.7, 0.9):
    cells = [f"lam={l}: {un[(rho,l)]['currency']:.2f} ({un[(rho,l)]['continuity']:.2f})" if (rho, l) in un else f"lam={l}: n/a" for l in (0, 1, 10)]
    best = max((un[(rho, l)]["currency"], l) for l in (0, 1, 10) if (rho, l) in un)
    print(f" rho={rho}: " + " | ".join(cells) + f" | best lam={best[1]} ({best[0]:.2f}), max(rho,1-rho)={max(rho,1-rho):.2f}")
print("\nSCOPED lam=10, record accuracy q: currency  vs refined formula (1-rho)+rho*q")
for rho in (0.3, 0.7):
    print(f" rho={rho}: " + " | ".join(f"q={q}: {sc[(rho,q)]['currency']:.2f} (formula {(1-rho)+rho*q:.2f})" for q in (0.5, 0.7, 0.9, 1.0)))
# ---- Experiment 2: SS-KL
def get(rho, cov, method, lam, m=1.0):
    for r in auto:
        if (r["rho"], r["cov"], r["method"], r["lam"], r.get("match", 1.0)) == (rho, cov, method, lam, m): return r
print("\nEXPERIMENT 2 (seed 1): SS-KL vs unscoped; formula (1-rho)+rho*c*m")
rows = []
for rho in (0.3, 0.7):
    for cov in (1.0, 0.6):
        base = {n: get(rho, cov, *a)["currency"] for n, a in {"none": ("none", 0.0), "KL1": ("unscoped", 1.0), "KL10": ("unscoped", 10.0)}.items() if get(rho, cov, *a)}
        bu = max(base.values())
        out = []
        for m in (1.0, 0.8, 0.6):
            r = get(rho, cov, "ss", 10.0, m)
            out.append((m, r["currency"], (1 - rho) + rho * cov * m, r["currency"] - bu))
        rows.append((rho, cov, base, bu, out))
        print(f" rho={rho} c={cov} | none {base.get('none',float('nan')):.2f} KL1 {base.get('KL1',float('nan')):.2f} KL10 {base['KL10']:.2f} | best unscoped {bu:.2f} | " +
              " | ".join(f"m={m}: {c:.2f} (formula {f:.2f}, vs best {d:+.2f})" for m, c, f, d in out))
dev = [abs(c - f) for *_, out in rows for m, c, f, d in out]
print(f"\nformula max abs deviation over {len(dev)} SS-KL cells: {max(dev):.3f}, mean {sum(dev)/len(dev):.3f}")
# ---- figures
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for l, c in ((0, "#c0392b"), (1, "#2c7fb8"), (10, "#1b7837")):
    xs = [r for r in (0.1, 0.3, 0.5, 0.7, 0.9) if (r, l) in un]
    ax[0].plot(xs, [un[(r, l)]["currency"] for r in xs], "o-", color=c, label=f"KL weight λ={l}")
ax[0].plot([0.1, 0.9], [0.9, 0.1], "k:", label="1−ρ (full retention)"); ax[0].set_xlabel("share of superseded facts ρ"); ax[0].set_ylabel("currency"); ax[0].set_title("Unscoped KL"); ax[0].legend(fontsize=7)
for rho, c in ((0.3, "#2c7fb8"), (0.7, "#c0392b")):
    qs = (0.5, 0.7, 0.9, 1.0); ax[1].plot(qs, [sc[(rho, q)]["currency"] for q in qs], "o-", color=c, label=f"ρ={rho}")
    ax[1].plot(qs, [(1 - rho) + rho * q for q in qs], "--", color=c, alpha=.5)
    ax[1].axhline(un[(rho, 0)]["currency"], color=c, ls=":", alpha=.6)
ax[1].set_xlabel("record accuracy q (dashed: (1−ρ)+ρq; dotted: no constraint)"); ax[1].set_title("Scoped KL, record with errors"); ax[1].legend(fontsize=7)
for (rho, cov, base, bu, out), mk in zip(rows, ("o", "s", "^", "D")):
    ax[2].plot([m for m, *_ in out], [d for *_, d in out], mk + "-", label=f"ρ={rho}, c={cov}")
ax[2].axhline(0, color="k", lw=.8); ax[2].set_xlabel("matching accuracy m"); ax[2].set_ylabel("SS-KL currency − best unscoped"); ax[2].set_title("Stream-scoped KL vs best unscoped"); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig("results/qwen15_summary.png", dpi=200)
