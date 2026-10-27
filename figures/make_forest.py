"""Figure 1: forest plot of twin effects against public human benchmarks (confirmatory study C1).
Usage: python3 make_forest.py <results/c1/final_effects.csv> <out_prefix>"""
import sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
C = pd.read_csv(sys.argv[1]); OUT = sys.argv[2]
HCI = {'default_organ': (-3.5, 12.3), 'default_green': (16.9, 32.4), 'attraction': (0.11, 0.62), 'fair': (-0.75, -0.33), 'frame': (0.67, 0.85), 'anch_africa': (0.69, 0.87), 'anch_redwood': (1.59, 1.79)}
TITLE = {'default_organ': 'Organ-donation default\n(canonical; points)', 'default_green': 'Green-energy default\n(novel; points)', 'attraction': 'Attraction effect\n(log odds ratio)', 'fair': 'Targeting fairness\n(Cohen\'s d)',
         'frame': 'Loss framing\n(Cohen\'s d)', 'anch_africa': 'Anchoring, African UN members\n(d on log estimates)', 'anch_redwood': 'Anchoring, redwood height\n(d on log estimates)'}
XLIM = {'default_organ': (-85, 85), 'default_green': (-85, 55), 'attraction': (-3.2, 4.2), 'fair': (-2.6, 1.2), 'frame': (-1.5, 3.5), 'anch_africa': (-0.8, 3.2), 'anch_redwood': (-0.5, 6.2)}
MODELS = [('anthropic/claude-haiku-5.5', 'Claude Haiku 5.5'), ('google/gemini-3.7-flash', 'Gemini 3.7 Flash'), ('openai/gpt-5.6-luna', 'GPT-5.6 luna'), ('x-ai/grok-4.3', 'Grok 4.3'), ('meta-llama/llama-4-maverick', 'Llama 4 Maverick')]
ARCH = [('demo', 'Demographics only', '#E69F00', 'o'), ('summary', 'Persona summary (primary)', '#0072B2', 'D'), ('theory', 'Theory-explicit prompt', '#009E73', 's')]
order = ['default_organ', 'default_green', 'attraction', 'fair', 'frame', 'anch_africa', 'anch_redwood']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(4, 2, figsize=(6.9, 9.8)); axes = axes.ravel()
rows = []; ypos = {}
for mi, (m, _) in enumerate(MODELS):
    for ai, (a, *_r) in enumerate(ARCH): ypos[(m, a)] = -(mi * 4 + ai)
for ax, it in zip(axes, order):
    h = C[C['item'] == it].human.iloc[0]; lo, hi = HCI[it]; xl = XLIM[it]
    ax.axvspan(lo, hi, color='#BBBBBB', alpha=.45, lw=0); ax.axvline(h, color='#444444', lw=1.1)
    ax.axvline(0, color='#888888', lw=.6, ls=':')
    for m, _ in MODELS:
        for a, _lab, col, mk in ARCH:
            r = C[(C['item'] == it) & (C.model == m) & (C.arch == a)]
            if r.empty: continue
            r = r.iloc[0]; y = ypos[(m, a)]; tw = r.twin; l, u = r.D_lo + r.human, r.D_hi + r.human
            ax.plot([max(l, xl[0]), min(u, xl[1])], [y, y], color=col, lw=1.3, solid_capstyle='butt', alpha=.9 if a == 'summary' else .75)
            if xl[0] <= tw <= xl[1]: ax.plot(tw, y, mk, color=col, ms=4.6 if a == 'summary' else 3.6, mec='white', mew=.5)
            else:
                edge = xl[1] if tw > xl[1] else xl[0]; ax.plot(edge, y, '>' if tw > xl[1] else '<', color=col, ms=5, clip_on=False); ax.text(edge - (0.03 if tw > xl[1] else -0.03) * (xl[1] - xl[0]), y + .55, f'{tw:.1f}', ha='right' if tw > xl[1] else 'left', va='bottom', fontsize=5.6, color=col)
    ax.set_xlim(*xl); ax.set_ylim(-19.2, 0.9); ax.set_title(TITLE[it], fontsize=7.8, loc='left', fontweight='bold')
    ax.set_yticks([ypos[(m, 'summary')] for m, _ in MODELS] if it in ('default_organ', 'attraction', 'frame', 'anch_redwood') else [])
    if it in ('default_organ', 'attraction', 'frame', 'anch_redwood'): ax.set_yticklabels([lab for _, lab in MODELS], fontsize=7)
    ax.tick_params(axis='y', length=0); ax.grid(axis='x', color='#EEEEEE', lw=.6); ax.set_axisbelow(True)
    ax.text(h, 0.9, '', ha='center')
ax = axes[7]; ax.axis('off')
for i, (a, lab, col, mk) in enumerate(ARCH): ax.plot([0.04], [0.82 - i * 0.12], mk, color=col, ms=6, transform=ax.transAxes); ax.text(0.12, 0.82 - i * 0.12, lab, transform=ax.transAxes, va='center', fontsize=7.3)
ax.add_patch(plt.Rectangle((0.0, 0.40), 0.08, 0.07, color='#BBBBBB', alpha=.6, transform=ax.transAxes)); ax.text(0.12, 0.435, 'Human 95% interval (public data)', transform=ax.transAxes, va='center', fontsize=7.3)
ax.plot([0.04, 0.04], [0.26, 0.34], color='#444444', lw=1.2, transform=ax.transAxes); ax.text(0.12, 0.30, 'Human estimate', transform=ax.transAxes, va='center', fontsize=7.3)
ax.text(0.0, 0.10, 'Bars: twin 95% bootstrap interval over 600 simulated respondents.\nTriangles at the panel edge: estimate outside the axis range (value shown).', transform=ax.transAxes, fontsize=6.4, va='top', color='#333333')
fig.tight_layout(); fig.savefig(OUT + '.png', dpi=300); fig.savefig(OUT + '.pdf'); print('saved')
