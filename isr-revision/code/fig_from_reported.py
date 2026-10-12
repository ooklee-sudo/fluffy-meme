"""Figures 1-3 drawn from estimates reported in the manuscript (Table 1, Sections 5.1-5.5).

Run:  python fig_from_reported.py  -> writes PNG and PDF files to ./figures
Replace the hard-coded numbers with the replication package output if they change.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})
Z = 1.96

# ---------------------------------------------------------------- Table 1
T1 = [  # repo, median cycle, bug slope (b), se, hazard slope, se
    ("anthropic-sdk-python", 1, -0.023, 0.079, -0.255, 0.095),
    ("flash-attention", 2, -0.005, 0.014, -0.272, 0.069),
    ("lm-evaluation-harness", 9, 0.013, 0.018, 0.365, 0.198),
    ("whisper.cpp", 4, 0.008, 0.010, -0.103, 0.065),
    ("transformers", 1, 0.000, 0.026, -0.031, 0.098),
    ("accelerate", 4, -0.021, 0.032, 0.168, 0.133),
    ("diffusers", 3, 0.004, 0.012, 0.002, 0.064),
    ("peft", 7, -0.016, 0.018, 0.127, 0.082),
    ("text-generation-inference", 2, -0.094, 0.038, -0.290, 0.139),
    ("trl", 2, -0.048, 0.029, 0.023, 0.123),
    ("FastChat", 3, 0.007, 0.055, -0.439, 1.096),
    ("autogen", 1, -0.024, 0.046, -0.491, 0.280),
    ("semantic-kernel", 1, -0.231, 0.066, -0.333, 0.153),
    ("TensorRT-LLM", 6, 0.020, 0.015, 0.224, 0.166),
    ("ollama", 1, 0.067, 0.027, -0.128, 0.327),
    ("openai-python", 1, -0.039, 0.054, -0.535, 0.120),
    ("llama_index", 1, -0.016, 0.032, -0.615, 0.107),
    ("sglang", 2, -0.002, 0.012, 0.175, 0.117),
    ("vllm", 2, 0.003, 0.009, 0.473, 0.201),
]
POOLED = {"bug": (-0.0029, -0.015, 0.010), "haz": (-0.090, -0.211, 0.030)}


def forest(ax, labels, est, se, pooled, xlim, title, xlabel, weekly, order):
    y = np.arange(len(order)) + 2
    for yy, i in zip(y, order):
        lo, hi = est[i] - Z * se[i], est[i] + Z * se[i]
        color = "0.55" if weekly[i] else "black"
        ax.plot([max(lo, xlim[0]), min(hi, xlim[1])], [yy, yy], color=color, lw=1)
        ax.plot(est[i], yy, "o", ms=3.5, color=color)
        if lo < xlim[0]:
            ax.annotate("", (xlim[0], yy), (xlim[0] + 0.04 * (xlim[1] - xlim[0]), yy),
                        arrowprops=dict(arrowstyle="->", color=color, lw=0.8))
        if hi > xlim[1]:
            ax.annotate("", (xlim[1], yy), (xlim[1] - 0.04 * (xlim[1] - xlim[0]), yy),
                        arrowprops=dict(arrowstyle="->", color=color, lw=0.8))
    p, lo, hi = pooled
    ax.fill([lo, p, hi, p], [0.6, 0.95, 0.6, 0.25], color="black")
    ax.axvline(0, color="0.3", lw=0.6, ls=":")
    ax.set_yticks(list(y) + [0.6])
    ax.set_yticklabels([labels[i] for i in order] + ["Pooled (random effects)"])
    ax.set_xlim(xlim)
    ax.set_ylim(0, len(order) + 2.5)
    ax.set_title(title, loc="left", fontsize=9)
    ax.set_xlabel(xlabel)


labels = [r[0] for r in T1]
weekly = np.array([r[1] == 1 for r in T1])
order = np.argsort([r[4] for r in T1])          # common order: by release-hazard slope
fig, axes = plt.subplots(1, 2, figsize=(7.2, 5.4))
forest(axes[0], labels, np.array([r[2] for r in T1]), np.array([r[3] for r in T1]),
       POOLED["bug"], (-0.40, 0.25), "(a) Bug reports, specification (b)",
       "Log bug rate, change per week of age", weekly, order)
forest(axes[1], labels, np.array([r[4] for r in T1]), np.array([r[5] for r in T1]),
       POOLED["haz"], (-1.3, 1.0), "(b) Release hazard",
       "Log-odds of release, change per week of age", weekly, order)
axes[1].set_yticklabels([])
fig.text(0.01, 0.005, "Notes. Points are repository-level estimates with 95% intervals (cycle bootstrap). "
         "Grey: median release cycle of one week.\nArrows mark intervals truncated at the axis limit. "
         "Diamonds: random-effects pooled estimate and 95% interval.\nRows are ordered by the release-hazard slope.", fontsize=7)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(f"{OUT}/fig1_repository_slopes.png"); fig.savefig(f"{OUT}/fig1_repository_slopes.pdf")

# ---------------------------------------------------------------- RQ1 specifications
specs = [("(a) No volume adjustment", -0.026, -0.050, -0.002, False),
         ("(b) Offset: log total issues", -0.0029, -0.015, 0.010, True),
         ("(c) Control: log non-bug issues", -0.019, -0.040, 0.002, False),
         ("(d) (c) + age 1-3 indicators", 0.017, -0.003, 0.038, True)]
fig, ax = plt.subplots(figsize=(6.0, 2.5))
for k, (lab, p, lo, hi, primary) in enumerate(specs[::-1]):
    c = "black" if primary else "0.6"
    ax.plot([lo, hi], [k, k], color=c, lw=1.6)
    ax.plot(p, k, "s" if primary else "o", color=c, ms=5)
ax.axvline(0, color="0.3", lw=0.6, ls=":")
ax.axvspan(-0.02, 0.02, color="0.92", zorder=0)
ax.set_yticks(range(4)); ax.set_yticklabels([s[0] for s in specs[::-1]])
ax.set_xlabel("Pooled log bug-rate slope per week of age (95% CI)")
ax.text(0.0, 3.55, "equivalence bound ±0.02", ha="center", fontsize=7, color="0.35")
ax.set_ylim(-0.6, 3.8)
fig.text(0.01, 0.01, "Black: primary tests of H1 (Section 4.3). Grey: biased downward by the post-release burst.",
         fontsize=7)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(f"{OUT}/fig2_rq1_specifications.png"); fig.savefig(f"{OUT}/fig2_rq1_specifications.pdf")

# ---------------------------------------------------------------- RQ3 and RQ4
rq3 = [  # label, coef, se, group
    ("Bug reports, 1-week lag", 0.261, 0.095, "Non-bug issues held fixed"),
    ("Non-bug issues", 0.233, 0.082, "Non-bug issues held fixed"),
    ("Bug reports, 3-week avg.", 0.332, 0.108, "Non-bug issues held fixed"),
    ("Bug reports, 1-week lag", 0.191, 0.123, "Total issues held fixed"),
    ("Total issues", 0.225, 0.105, "Total issues held fixed"),
    ("Bug reports, 3-week avg.", 0.272, 0.123, "Total issues held fixed"),
]
rq4 = [("Work age, joint", 0.182, 0.029, 0.335), ("Calendar age, joint", 0.065, -0.089, 0.219),
       ("Work age, alone", 0.223, 0.132, 0.314), ("Calendar age, alone", 0.173, 0.079, 0.267)]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axes[0]
ypos = [6.5, 5.5, 4.5, 2.5, 1.5, 0.5]
for y, (lab, b, s, grp) in zip(ypos, rq3):
    isbug = lab.startswith("Bug")
    c = "black" if isbug else "0.55"
    ax.plot([b - Z * s, b + Z * s], [y, y], color=c, lw=1.4)
    ax.plot(b, y, "o", color=c, ms=4)
ax.set_yticks(ypos); ax.set_yticklabels([r[0] for r in rq3])
ax.text(-0.25, 7.3, "Non-bug issues held fixed", fontsize=7.5, style="italic")
ax.text(-0.25, 3.3, "Total issues held fixed", fontsize=7.5, style="italic")
ax.axvline(0, color="0.3", lw=0.6, ls=":")
ax.set_xlim(-0.25, 0.65); ax.set_ylim(0, 7.8)
ax.set_xlabel("Log-odds of a release per SD (95% CI)")
ax.set_title("(a) RQ3: response to issue volume", loc="left", fontsize=9)
ax = axes[1]
for y, (lab, p, lo, hi) in zip([3, 2, 0.8, -0.2], rq4):
    c = "black" if "Work" in lab else "0.55"
    ax.plot([lo, hi], [y, y], color=c, lw=1.4); ax.plot(p, y, "D", color=c, ms=4)
ax.set_yticks([3, 2, 0.8, -0.2]); ax.set_yticklabels([r[0] for r in rq4])
ax.axvline(0, color="0.3", lw=0.6, ls=":")
ax.set_xlabel("Log-odds per week (95% CI)")
ax.set_title("(b) RQ4: regular releases", loc="left", fontsize=9)
fig.text(0.01, 0.01, "Notes. Panel (a): clustered 95% intervals; wild cluster bootstrap p-values are in Section 5.3. "
         "Panel (b): random-effects pooled estimates;\nwithin-repository correlation of the two ages is 0.74.",
         fontsize=7)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(f"{OUT}/fig3_rq3_rq4_coefficients.png"); fig.savefig(f"{OUT}/fig3_rq3_rq4_coefficients.pdf")
print("written to", OUT)
