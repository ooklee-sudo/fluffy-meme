"""Figure of the prevalence curve from a table of weekly estimates (curve_v1_data.csv).

    python plot_curve.py curve_v1_data.csv figures/prevalence_curve.png
Single y-axis per panel (alpha-hat = estimated share of LLM-drafted-like text, uncalibrated), 95% bootstrap bands
only for the all-documents series.
"""
import csv, sys, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
C1, C2 = "#2a78d6", "#eb6834"          # validated categorical slots 1 and 2 (blue, orange)

rows = list(csv.DictReader(open(sys.argv[1])))
d = [dt.datetime.strptime("20" + r["week"], "%Y%m%d") for r in rows]
f = lambda k: [float(r[k]) for r in rows]
chat = dt.datetime(2022, 11, 30)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True, facecolor=SURFACE)
for ax in axes:
    ax.set_facecolor(SURFACE)
    ax.axvspan(d[0] - dt.timedelta(days=60), chat, color="#efeeea", zorder=0)
    ax.axvline(chat, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_xlim(d[0] - dt.timedelta(days=60), d[-1] + dt.timedelta(days=150))
    ax.set_ylim(0, 0.085)
    ax.set_xticks([dt.datetime(y, 1, 1) for y in range(2021, 2027)])
    ax.set_xticklabels([str(y) for y in range(2021, 2027)])

a = axes[0]
a.fill_between(d, f("lo"), f("hi"), color=C1, alpha=0.18, lw=0, zorder=2)
a.plot(d, f("alpha"), color=C1, lw=2, marker="o", ms=6, mfc=C1, mec=SURFACE, mew=1.5, zorder=3)
a.set_title("All applications", loc="left", color=INK, fontsize=11, fontweight="bold")
a.text(d[0] - dt.timedelta(days=45), 0.080, "published\nbefore\nDec 2022", color=MUTED, fontsize=8.5, va="top")
a.text(chat + dt.timedelta(days=15), 0.0035, "ChatGPT\nNov 2022", color=MUTED, fontsize=8, va="bottom")
a.annotate(f"{f('alpha')[-1]:.3f}", (d[-1], f("alpha")[-1]), xytext=(8, 0), textcoords="offset points", color=INK, fontsize=9, va="center")
a.set_ylabel("estimated share of LLM-drafted-like text (alpha-hat)", color=MUTED, fontsize=9)

for ax, (k1, l1), (k2, l2), title in ((axes[1], ("us", "US applicants"), ("non_us", "non-US applicants"), "By applicant group"),
                                      (axes[2], ("small", "small firms (<10 apps/week)"), ("large", "large firms (≥10 apps/week)"), "By firm size")):
    for k, l, c in ((k1, l1, C1), (k2, l2, C2)):
        ax.plot(d, f(k), color=c, lw=2, marker="o", ms=5.5, mfc=c, mec=SURFACE, mew=1.5, zorder=3)
        ax.annotate(f"{l}  {f(k)[-1]:.3f}", (d[-1], f(k)[-1]), xytext=(8, 0), textcoords="offset points", color=INK, fontsize=8.5, va="center")
    ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
axes[1].set_xlim(axes[1].get_xlim()[0], d[-1] + dt.timedelta(days=620))
axes[2].set_xlim(axes[2].get_xlim()[0], d[-1] + dt.timedelta(days=880))
fig.text(0.01, 0.01, "Weekly samples of ~2,000 US pre-grant applications per publication week (n = 29,786 in total). Detector trained on LLM drafts (draft/expand); "
         "polished human text is not detected.\nShaded: published before Dec 2022. Publications lag filings by ~18 months. Band: 95% bootstrap interval.",
         color=MUTED, fontsize=8, va="bottom")
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(sys.argv[2], dpi=170, facecolor=SURFACE)
print("saved", sys.argv[2])
