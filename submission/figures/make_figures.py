"""Draw Figures 1-5 of the manuscript from the plotted values (figure_data/*.csv)."""
import os, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure_data")
OUT = os.path.dirname(os.path.abspath(__file__))
C1, C2 = "#1f3b73", "#8c8c8c"

def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name), dpi=300); plt.close(fig)

# Figure 1
d = pd.read_csv(f"{D}/fig1_aio_event_study.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.6))
for slug, lab, col, off, mk in [("desktop", "Desktop", C1, -0.12, "o"), ("all", "All platforms", C2, 0.12, "s")]:
    s = d[d.slug == slug]
    ax.errorbar(s.e + off, s.att, yerr=[s.att - s.lo, s.hi - s.att], fmt=mk, color=col, ms=4, capsize=2, lw=1, label=lab)
ax.axhline(0, color="black", lw=0.8); ax.axvline(-0.5, color="gray", ls="--", lw=0.8)
ax.set_xlabel("Months relative to AI Overviews launch"); ax.set_ylabel("Effect on pageviews (%)")
ax.set_xticks(range(-8, 7)); ax.legend(frameon=False, loc="upper right")
save(fig, "Figure1_AIO_event_study.png")

# Figure 2
d = pd.read_csv(f"{D}/fig2_search_vs_meta.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.6))
qs = d[d.slug == "search"].q.tolist(); xi = range(len(qs))
ax.axvspan(qs.index("2021Q3"), qs.index("2022Q4"), color="gray", alpha=0.12, lw=0)
ax.plot(xi, d[d.slug == "meta"].g, color=C2, marker="s", ms=3, label="Meta (ad-cycle benchmark)")
ax.plot(xi, d[d.slug == "search"].g, color=C1, marker="o", ms=3, lw=2, label="Google Search & other")
ax.axvline(qs.index("2022Q4") + 0.5, color="gray", ls="--", lw=0.8)
ax.text(qs.index("2022Q4") + 0.7, -12, "ChatGPT (Nov 2022)", fontsize=8, color="dimgray")
ax.text(qs.index("2021Q3") + 0.2, 51, "ATT shock\nto Meta", fontsize=8, color="dimgray", va="top")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks([i for i, q in enumerate(qs) if q.endswith("Q1")]); ax.set_xticklabels([q[:4] for q in qs if q.endswith("Q1")])
ax.set_ylabel("Year-over-year revenue growth (log %)"); ax.legend(frameon=False, loc="upper right")
save(fig, "Figure2_search_vs_meta.png")

# Figure 3
d = pd.read_csv(f"{D}/fig3_clicks_cpc.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.4))
qs = d[d.slug == "clicks"].q.tolist(); xi = range(len(qs))
ax.plot(xi, d[d.slug == "clicks"].v, color=C2, marker="s", ms=4, label="Paid clicks")
ax.plot(xi, d[d.slug == "cpc"].v, color=C1, marker="o", ms=4, lw=2, label="Cost per click")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(list(xi)); ax.set_xticklabels([f"{q[4:]} '{q[2:4]}" for q in qs], fontsize=8)
ax.set_ylabel("Year-over-year change (%)"); ax.legend(frameon=False, loc="upper left")
save(fig, "Figure3_clicks_cpc.png")

# Figure 4
d = pd.read_csv(f"{D}/fig4_bing_share.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.6))
ms = d[d.s == "ww"].m.tolist(); xi = range(len(ms))
ax.plot(xi, d[d.s == "us"].v, color=C2, lw=1.5, label="United States, all devices")
ax.plot(xi, d[d.s == "ww"].v, color=C1, lw=2, label="Worldwide, desktop")
for m, lab, yy, ha, dx in [("2023-02", "Bing Chat", 12.6, "right", -0.5), ("2024-05", "AI Overviews", 12.6, "right", -0.5), ("2025-05", "AI Mode", 12.6, "left", 0.5)]:
    ax.axvline(ms.index(m), color="gray", ls="--", lw=0.8); ax.text(ms.index(m) + dx, yy, lab, fontsize=8, color="dimgray", ha=ha)
ax.set_xticks([i for i, m in enumerate(ms) if m.endswith("-01")]); ax.set_xticklabels([m[:4] for m in ms if m.endswith("-01")])
ax.set_ylabel("Bing share of search referrals (%)"); ax.set_ylim(3, 13); ax.legend(frameon=False, loc="lower right")
save(fig, "Figure4_bing_share.png")

# Figure 5
d = pd.read_csv(f"{D}/fig5_trust_shock_gap.csv", parse_dates=["d"])
fig, ax = plt.subplots(figsize=(6.5, 3.4))
segs = [("2024-04-15", "2024-05-13", "Before launch"), ("2024-05-14", "2024-05-22", "AI Overviews live"),
        ("2024-05-23", "2024-05-31", "Errors go viral"), ("2024-06-01", "2024-07-29", "After")]
for i, (a, b, lab) in enumerate(segs):
    s = d[(d.d >= a) & (d.d <= b)]
    if i % 2: ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="gray", alpha=0.12, lw=0)
    ax.hlines(s.v.mean(), pd.Timestamp(a), pd.Timestamp(b), color="black", lw=1.5)
    ax.text(pd.Timestamp(a), 15.5 - 1.1 * i, lab, fontsize=8, color="dimgray")
ax.plot(d.d, d.v, color=C1, lw=1.8)
ax.set_ylim(0, 16); ax.set_ylabel("English minus large editions (pp)")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %d"))
save(fig, "Figure5_trust_shock.png")
print("done")
