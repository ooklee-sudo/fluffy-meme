"""Figure 3: directional WTI path around human-labelled posts (mean ± 1 SE, median) with the 95% placebo band."""
import sys, json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
HC = sys.argv[1]; F = json.load(open(f'results_reanalysis_{HC}.json'))['figure_path']; x = np.array(F['offsets'])
MEAN, MED, BAND, INK, MUTED, GRID = '#2a78d6', '#eb6834', '#d9d8d3', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .5, 'axes.axisbelow': True})
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for a, (c, t) in zip(ax, (('DEESC', 'De-escalation'), ('ESC', 'Escalation'))):
    f = F[c]; m, se, md = map(np.array, (f['mean'], f['se'], f['median']))
    a.fill_between(x, f['placebo_lo'], f['placebo_hi'], color=BAND, lw=0, label='Placebo times, 95% band of mean')
    a.fill_between(x, m - se, m + se, color=MEAN, alpha=.18, lw=0)
    a.plot(x, m, color=MEAN, lw=2, label='Mean ± 1 SE'); a.plot(x, md, color=MED, lw=1.6, ls='--', label='Median')
    a.axvline(0, color=INK, lw=.8); a.axhline(0, color=INK, lw=.6)
    a.set_title(f'{t} (human labels), n = {f["n"]}', fontsize=10, color=INK); a.set_xlabel('Minutes relative to post'); a.set_xticks(range(-60, 61, 20))
ax[0].set_ylabel('Directional WTI return since post time (%)'); ax[0].legend(frameon=False, loc='upper left', fontsize=8)
fig.tight_layout(); fig.savefig(f'figs/fig_path_{HC}.png', dpi=220); print('ok')
