"""Figure: estimated share of LLM-drafted-like text by filing quarter (from filing_quarter_data.csv)."""
import csv, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, MUTED, GRID, C1 = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1", "#2a78d6"
rows = list(csv.DictReader(open(sys.argv[1])))
x = list(range(len(rows))); f = lambda k: [float(r[k]) for r in rows]
q = [r["quarter"] for r in rows]; k_chat = q.index("2022Q4")
fig, ax = plt.subplots(figsize=(11, 4.6), facecolor=SURFACE); ax.set_facecolor(SURFACE)
ax.axvspan(-0.5, k_chat - 0.5, color="#efeeea", zorder=0)
ax.axvline(k_chat, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID); ax.tick_params(colors=MUTED, length=0)
ax.fill_between(x, f("lo"), f("hi"), color=C1, alpha=0.18, lw=0, zorder=2)
ax.plot(x, f("alpha"), color=C1, lw=2, marker="o", ms=6, mfc=C1, mec=SURFACE, mew=1.5, zorder=3)
ax.set_xticks(x[::2]); ax.set_xticklabels(q[::2], rotation=45, ha="right", fontsize=8.5)
ax.set_ylim(0, 0.125); ax.set_xlim(-0.5, len(x) - 0.3)
ax.set_ylabel("estimated share of LLM-drafted-like text (alpha-hat)", color=MUTED, fontsize=9)
ax.set_title("By filing quarter", loc="left", color=INK, fontsize=11, fontweight="bold")
ax.text(k_chat + 0.15, 0.118, "ChatGPT release\n(Nov 2022)", color=MUTED, fontsize=8.5, va="top")
ax.text(0, 0.118, "filed before\nChatGPT", color=MUTED, fontsize=8.5, va="top")
ax.annotate("2026Q1: only 292 documents\n(early-published filings)", (len(x) - 2, 0.086), xytext=(-175, 12), textcoords="offset points",
            color=MUTED, fontsize=8.5, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
fig.text(0.01, 0.01, "Pooled over 15 weekly samples (29,786 US pre-grant applications; ~2,000 per week), each document scored against the human model of its applicant group. "
         "Band: 95% bootstrap interval.\nDetector trained on LLM drafts; polished human text is not detected. Late quarters rest on few, early-published documents.",
         color=MUTED, fontsize=8, va="bottom")
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(sys.argv[2], dpi=170, facecolor=SURFACE); print("saved", sys.argv[2])
