import json, math, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
A = json.load(open("results/ripple_qwen15.json")); B = json.load(open("results/ripple_rule_qwen15.json"))
lab = lambda r: {"none": "amend only", "unscoped": f"KL all (λ={r['lam']:g})", "ss": "stream-scoped", "dep": "dependency-scoped"}[r["method"]] + (f" + list κ={r['kappa']:g}" if r["kappa"] else "")
print("RIPPLE EXPERIMENT (Qwen2.5-1.5B, seed 1): base_new / ripple / keep_base / keep_dep / currency (ceiling)")
for rho in (0.3, 0.7):
    print(f"-- rho={rho}")
    for r in [x for x in A if x["rho"] == rho]:
        print(f"  {lab(r):34s} base={r['base_new']:.2f} ripple={r['ripple']:.2f} keepB={r['keep_base']:.2f} keepD={r['keep_dep']:.2f} cur={r['currency']:.2f} ({r['ceiling']:.2f})")
print("\nRULE-STATEMENT VARIANT (rules in launch data): ripple / in-context ripple / currency")
for r in B: print(f"  rho={r['rho']} {lab(r):30s} ripple={r['ripple']:.2f} ctx={r['ripple_ctx']:.2f} keepD={r['keep_dep']:.2f} cur={r['currency']:.2f}")
kap = [r for r in A if r["method"] == "ss" and r["rho"] == 0.3 and r["kappa"] in (0.0, 0.6, 1.0)]
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for rho, c in ((0.3, "#2c7fb8"), (0.7, "#c0392b")):
    ks = (0.0, 0.6, 1.0)
    pts = [next(x for x in A if x["rho"] == rho and x["method"] == "ss" and x["kappa"] == k) for k in ks]
    ax[0].plot(ks, [p["ripple"] for p in pts], "o-", color=c, label=f"ρ={rho}: ripple"); ax[0].plot(ks, [p["currency"] for p in pts], "s--", color=c, alpha=.6, label=f"ρ={rho}: currency")
ax[0].plot([0, 1], [0, 1], "k:", lw=1); ax[0].set_xlabel("completeness of consequential-amendment list κ"); ax[0].set_title("Stream-scoped KL + list"); ax[0].legend(fontsize=7)
names = ["amend only", "KL all λ=1", "KL all λ=10", "stream-scoped", "dep-scoped", "ss + list κ=1"]
sel = lambda rho: [next(x for x in A if x["rho"] == rho and ((x["method"] == "none") if i == 0 else (x["method"] == "unscoped" and x["lam"] == 1) if i == 1 else (x["method"] == "unscoped" and x["lam"] == 10) if i == 2 else (x["method"] == "ss" and x["kappa"] == 0) if i == 3 else (x["method"] == "dep" and x["kappa"] == 0) if i == 4 else (x["method"] == "ss" and x["kappa"] == 1)))for i in range(6)]
for k, rho in enumerate((0.3, 0.7)):
    s = sel(rho); xs = range(6)
    ax[1 + k].bar([x - .2 for x in xs], [p["base_new"] for p in s], .2, label="revised base facts", color="#2c7fb8")
    ax[1 + k].bar(list(xs), [p["ripple"] for p in s], .2, label="dependents (ripple)", color="#c0392b")
    ax[1 + k].bar([x + .2 for x in xs], [p["keep_base"] for p in s], .2, label="unrevised base kept", color="#999999")
    ax[1 + k].set_xticks(list(xs)); ax[1 + k].set_xticklabels(names, rotation=35, ha="right", fontsize=7); ax[1 + k].set_title(f"ρ={rho}"); ax[1 + k].set_ylim(0, 1.05)
ax[1].legend(fontsize=7)
plt.tight_layout(); plt.savefig("results/ripple_summary.png", dpi=200)
