"""Figure 1: reliability paradox, debt per task D(q) from Result 4 of the TEM model."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def D(q, eta, phi, alpha, qbar):
    return q * (1 - eta * phi) * (1 - (1 - alpha) * np.minimum(1, q / qbar))

q = np.linspace(0.0, 0.6, 601)
rat = D(q, 0.5, 1.0, 0.0, 0.125)
beh = D(q, 0.5, 0.6, 0.2, 0.458)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
fig, ax = plt.subplots(figsize=(3.1, 2.05), dpi=300)
ax.plot(q, beh, color="#eb6834", lw=1.6)
ax.plot(q, rat, color="#2a78d6", lw=1.6)
ax.invert_xaxis()
ax.set_xlabel("Error rate of generated code  (more reliable model →)")
ax.set_ylabel("Debt per task")
ax.set_xlim(0.6, 0); ax.set_ylim(0, 0.115)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#888"); ax.spines["bottom"].set_color("#888")
ax.tick_params(colors="#444", length=2)
ax.grid(axis="y", color="#e5e5e5", lw=0.5); ax.set_axisbelow(True)
ax.annotate("", xy=(0.286, 0.1002), xytext=(0.458, 0.0641),
            arrowprops=dict(arrowstyle="->", color="#333", lw=0.7))
ax.plot([0.458, 0.286], [0.0641, 0.1002], "o", ms=3, color="#eb6834")
ax.text(0.30, 0.106, "+56%", ha="center", fontsize=7, color="#222")
ax.text(0.59, 0.097, "With biases", color="#222", fontsize=6.5)
ax.text(0.50, 0.005, "Fully rational developer", color="#222", fontsize=6.5)
ax.text(0.0, 0.112, "Illustrative parameter values", ha="right", fontsize=5.5, color="#666", style="italic")
fig.tight_layout(pad=0.3)
fig.savefig("fig1.png")
print(D(np.array([0.458, 0.286]), 0.5, 0.6, 0.2, 0.458), rat.max(), q[rat.argmax()])
