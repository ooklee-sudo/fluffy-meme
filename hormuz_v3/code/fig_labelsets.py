"""Figure 1: mean directional 30-minute WTI return by class under each label set (results_reanalysis_<label>.json)."""
import sys, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
HC = sys.argv[1]; R = json.load(open(f'results_reanalysis_{HC}.json'))['table3']
ORDER = [('human', 'Human (v3)' if HC == 'v3' else 'Human (final)'), ('model1', 'Model 1 (original)'), ('v2_majority', 'v2 majority'), ('v2_opus', 'v2 opus'),
         ('v2_sonnet', 'v2 sonnet'), ('v2_haiku', 'v2 haiku'), ('v2_sonnet_repeat', 'v2 sonnet repeat')]
HI, GRAY, INK, MUTED = '#2a78d6', '#8a8984', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': MUTED, 'xtick.color': MUTED, 'ytick.color': INK})
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for a, (c, title) in zip(ax, (('DEESC', 'De-escalation'), ('ESC', 'Escalation'))):
    for i, (k, lab) in enumerate(ORDER):
        o = R[k][c]; y = len(ORDER) - 1 - i; col = HI if k == 'human' else GRAY
        a.errorbar(o['mean'], y, xerr=[[o['mean'] - o['ci'][0]], [o['ci'][1] - o['mean']]], fmt='o', color=col, ms=7, lw=2, capsize=3)
        a.text(o['ci'][1] + 0.03, y, f"n={o['n']}", va='center', fontsize=8, color=MUTED)
    a.axvline(0, color=INK, lw=.8); a.set_title(f'{title}: mean directional 30-min return', fontsize=9.5, color=INK)
    a.set_xlabel('% (day-clustered 95% CI)')
ax[0].set_yticks(range(len(ORDER))); ax[0].set_yticklabels([lab for _, lab in ORDER][::-1])
fig.tight_layout(); fig.savefig(f'figs/fig_labelsets_{HC}.png', dpi=220); print('ok')
