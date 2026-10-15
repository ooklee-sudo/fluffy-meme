"""Figure: median absolute error of each estimator against the full human-label estimate (v3), by share of posts with human labels."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
S = pd.read_csv('dsl/sim_summary_robust_v3.csv')
COL = {'naive': '#2a78d6', 'human_only': '#eb6834', 'dsl': '#1baf7a', 'ppi': '#eda100'}
NAME = {'naive': 'Model labels only', 'human_only': 'Human labels only', 'dsl': 'DSL', 'ppi': 'PPI'}
MK = {'naive': 'o', 'human_only': 's', 'dsl': '^', 'ppi': 'D'}
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.size': 8.5, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6, 'axes.axisbelow': True})
fig, ax = plt.subplots(2, 2, figsize=(7.6, 5.4), sharex=True)
for r, (sur, sname) in enumerate((('model1', 'Surrogate: model 1 labels'), ('v2_maj', 'Surrogate: v2 majority labels'))):
    for c_, (cls, cname) in enumerate((('ESC', 'Escalation (human estimate 0.45%, n = 10)'), ('DEESC', 'De-escalation (human estimate 0.94%, n = 32)'))):
        a = ax[r, c_]; d = S[(S.surrogate == sur) & (S.cls == cls)]
        for m in ('naive', 'human_only', 'dsl', 'ppi'):
            x = d[d.method == m].sort_values('frac'); xs = 100 * x.frac.values; y = x.mae_med.values
            a.plot(xs, y, color=COL[m], lw=2, marker=MK[m], ms=5, label=NAME[m], ls='--' if m == 'naive' else '-')
        a.set_ylim(0, 0.65); a.set_title(f'{cname}\n{sname}', fontsize=8.5, color=INK, loc='left')
        if c_ == 0: a.set_ylabel('Median absolute error (pp)')
        if r == 1: a.set_xlabel('Posts with human labels (%)')
        a.set_xticks([10, 20, 30, 40, 50])
h, l = ax[0, 0].get_legend_handles_labels(); fig.legend(h, l, loc='lower center', ncol=4, frameon=False)
fig.tight_layout(rect=(0, .05, 1, 1)); fig.savefig('figs/fig_correction_v3.png', dpi=220); print('ok')
