import json, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
r = json.load(open("toy_cl_results.json")); seeds = list(r["seeds"])
names = {"naive_sequential": "Naive sequential", "replay": "Replay (γ=0.65)",
         "replay_proximal_kl": "Replay + proximal KL", "replay_dual_kl": "Replay + dual KL"}
fin = lambda c, k, s: r["seeds"][s]["cells"][c][-1][k]
A0 = {s: r["seeds"][s]["A_launch"] for s in seeds}
lines = ["| Cell | A after B | Drop on A | B after B | per-seed A / B |", "|---|---|---|---|---|"]
for c, n in names.items():
    a = np.array([fin(c, "A", s) for s in seeds]); b = np.array([fin(c, "B", s) for s in seeds])
    d = np.array([A0[s] - fin(c, "A", s) for s in seeds])
    ps = "; ".join(f"{x:.3f}/{y:.3f}" for x, y in zip(a, b))
    lines.append(f"| {n} | {a.mean():.3f} ({a.std(ddof=1):.3f}) | {d.mean():.3f} ({d.std(ddof=1):.3f}) | {b.mean():.3f} ({b.std(ddof=1):.3f}) | {ps} |")
lines += ["", "Launch A accuracy per seed: " + ", ".join(f"{s}: {A0[s]:.3f}" for s in seeds),
          f"Parameters: {r['n_params']}, vocab: {r['vocab_size']}, split sizes (seed {seeds[0]}): {r['seeds'][seeds[0]]['sizes']}", "",
          "Launch-KL sweep (replay + b2, no proximal term), mean over seeds:", "", "| b2 | A after B | B after B |", "|---|---|---|"]
sw = list(r["seeds"][seeds[0]]["sweep"])
for b in sw:
    a = np.mean([r["seeds"][s]["sweep"][b][-1]["A"] for s in seeds]); bb = np.mean([r["seeds"][s]["sweep"][b][-1]["B"] for s in seeds])
    lines.append(f"| {b} | {a:.3f} | {bb:.3f} |")
open("results_table.md", "w").write("\n".join(lines)); print("\n".join(lines))

fig, ax = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
col = dict(zip(names, ["#c0392b", "#2c7fb8", "#7b3294", "#1b7837"]))
for k, t in enumerate(["A", "B"]):
    for c, n in names.items():
        Y = np.array([[0] + [e[t] for e in r["seeds"][s]["cells"][c]] for s in seeds])
        Y[:, 0] = [A0[s] if t == "A" else r["seeds"][s]["stageA"][-1]["B"] for s in seeds]
        x = np.arange(Y.shape[1]); ax[k].plot(x, Y.mean(0), color=col[c], label=n)
        ax[k].fill_between(x, Y.min(0), Y.max(0), color=col[c], alpha=.15)
    ax[k].set_title(f"Stream {t} test accuracy during update on B"); ax[k].set_xlabel("epoch of Stream B (0 = launch)")
ax[0].set_ylabel("token accuracy"); ax[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig("fig_forgetting.png", dpi=200)
