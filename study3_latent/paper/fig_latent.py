"""Figure: LLM-label DiD and corrected DiDs (percentage points, 95% CI) for the three content outcomes."""
import json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = json.load(open('results_latent.json'))['outcomes']
OUT = [('defect', 'Defect reported'), ('neg', 'Negative sentiment'), ('perfpos', 'Performance praised')]
EST = [('naive', 'LLM labels (uncorrected)', '#2a78d6', 'o'), ('fe', 'Corrected: FE estimate / J', '#eb6834', 's'), ('cell', 'Corrected: latent cell prevalences', '#1baf7a', '^')]
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': MUTED, 'xtick.color': MUTED, 'ytick.color': INK})
fig, ax = plt.subplots(figsize=(7.2, 3.6))
for i, (k, lab) in enumerate(OUT):
    o = R[k]; vals = {'naive': (o['naive_fe']['b'], o['boot']['naive_fe_ci']), 'fe': (o['did_corrected_fe'], o['boot']['did_corrected_fe_ci']),
                      'cell': (o['did_latent_cells'], o['boot']['did_latent_ci'])}
    for j, (e, name, col, mk) in enumerate(EST):
        y = len(OUT) - 1 - i + (0.22 - 0.22 * j); b, ci = vals[e]
        ax.errorbar(100 * b, y, xerr=[[100 * (b - ci[0])], [100 * (ci[1] - b)]], fmt=mk, color=col, ms=7, lw=2, capsize=3, label=name if i == 0 else None)
ax.axvline(0, color=INK, lw=.8); ax.set_yticks(range(len(OUT))); ax.set_yticklabels([l for _, l in OUT][::-1])
ax.set_xlabel('Treated × post DiD (percentage points; 95% product-cluster bootstrap CI)'); ax.grid(axis='x', color=GRID, lw=.6)
ax.legend(frameon=False, loc='lower center', bbox_to_anchor=(.5, 1.0), ncol=3, fontsize=8)
fig.tight_layout(); fig.savefig('fig_latent_did.png', dpi=220); print('ok')
