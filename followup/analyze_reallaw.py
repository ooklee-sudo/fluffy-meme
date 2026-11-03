import json, statistics as st, collections, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = json.load(open("results/reallaw_qwen7b.json")) + json.load(open("results/reallaw_sweep_qwen7b.json"))
R = [r for r in R if r["kdep"] == 0 and (r["method"], r["lam"]) in (("none", 0.0), ("dep", 10.0), ("ss", 10.0))]
g = collections.defaultdict(list)
for r in R: g[(r["method"], r["kA"])].append(r)
names = {"none": "stream only", "dep": "dependency-scoped KL", "ss": "stream-scoped KL"}
mean = lambda v, k: st.mean([x[k] for x in v if x[k] == x[k]])
rng = lambda v, k: (min(x[k] for x in v if x[k] == x[k]), max(x[k] for x in v if x[k] == x[k]))
print("kA sweep, Qwen2.5-7B, seeds 1-3 (mean [min-max]); n_stream = facts in the update stream (8 net thresholds always included)")
print(f"{'method':22s} {'kA':>5s} {'n_str':>5s} {'listed':>14s} {'AB-unlisted':>15s} {'control':>14s} {'currency_all':>15s}")
for m in ("none", "dep", "ss"):
    for kA in (0.1, 0.25, 0.5, 0.75):
        v = g.get((m, kA)); 
        if not v: continue
        f = lambda k: f"{mean(v,k):.2f} [{rng(v,k)[0]:.2f}-{rng(v,k)[1]:.2f}]"
        print(f"{names[m]:22s} {kA:5.2f} {mean(v,'n_stream'):5.1f} {f('listed'):>14s} {f('unlisted_AB'):>15s} {f('keep_control'):>14s} {f('currency_all'):>15s}")
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6)); col = {"none": "#c0392b", "dep": "#1b7837", "ss": "#2c7fb8"}
for m in ("none", "dep", "ss"):
    ks = [k for k in (0.1, 0.25, 0.5, 0.75) if (m, k) in g]
    for a, key, t in ((ax[0], "unlisted_AB", "unlisted time-limit / amount provisions\n(new value without being in the update)"), (ax[1], "listed", "provisions in the update (new value)"), (ax[2], "currency_all", "all changed provisions (new value)")):
        a.plot(ks, [mean(g[(m, k)], key) for k in ks], "o-", color=col[m], label=names[m]); a.set_title(t, fontsize=9); a.set_xlabel("share kA of time-limit/amount provisions in the update"); a.set_ylim(-0.02, 1.05)
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig("results/reallaw_sweep.png", dpi=200)
