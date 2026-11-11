import numpy as np, pandas as pd, statsmodels.formula.api as smf
D = '/home/user/data'
M = pd.read_pickle(f'{D}/study1_matched.pkl').dropna(subset=['deepseek_diff', 'qwen_diff']).copy()
M['q'] = (M.deepseek_diff + M.qwen_diff) / 2; M['qw'] = (M.deepseek_win + M.qwen_win) / 2
print('n', len(M), 'leaked', M.leak.sum())
print('judge agreement corr(diff) deepseek~qwen = %.2f' % M.deepseek_diff.corr(M.qwen_diff))
h = M.dropna(subset=['haiku_diff']); print('haiku subsample n=%d corr(avg open, haiku)=%.2f' % (len(h), h.q.corr(h.haiku_diff)))
print('human-vs-judge: corr(win, judge win prob)=%.2f' % M.win.corr(M.qw))
print('mean judge quality gap (focal-opp): leaked %.2f vs not %.2f' % (M[M.leak == 1].q.mean(), M[M.leak == 0].q.mean()))
ctrl = 'tok_diff + hdr_diff + lst_diff + bold_diff + ref + opp_ref + C(np.minimum(turns,4))'
fe = 'C(opair) + C(lang)'
fit = lambda f, d, y='win': smf.ols(f'{y} ~ {f}', d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.pair)[0]})
for name, f in [('matched, no controls', f'leak + {fe}'), ('+ rule controls', f'leak + {ctrl} + {fe}'),
                ('+ judges (avg)', f'leak + q + qw + {ctrl} + {fe}'), ('+ deepseek only', f'leak + deepseek_diff + deepseek_win + {ctrl} + {fe}'),
                ('+ qwen only', f'leak + qwen_diff + qwen_win + {ctrl} + {fe}')]:
    m = fit(f, M); print(f'{name:24s} beta={m.params["leak"]:+.4f} se={m.bse["leak"]:.4f} p={m.pvalues["leak"]:.3g}')
for y in ['lose', 'tie']:
    m = fit(f'leak + q + qw + {ctrl} + {fe}', M, y); print(f'   outcome {y}: beta={m.params["leak"]:+.4f} ({m.bse["leak"]:.4f})')
m = fit(f'leak*top3 + q + qw + {ctrl} + {fe}', M); print('H1a leak x top3 = %+.4f (%.4f) p=%.3g' % (m.params['leak:top3'], m.bse['leak:top3'], m.pvalues['leak:top3']))
# sharpened prediction: effect by tercile of |quality gap|
M['gap'] = pd.qcut(M.q.abs().rank(method='first'), 3, labels=['small', 'mid', 'large'])
for g, sub in M.groupby('gap', observed=True):
    m = fit(f'leak + q + qw + {ctrl} + C(opair)', sub); print(f'  |gap| {g:5s}: beta={m.params["leak"]:+.4f} ({m.bse["leak"]:.4f}) n_leak={sub.leak.sum()}')
# substantive prompts only (drop greetings / very short prompts)
m = fit(f'leak + q + qw + {ctrl} + {fe}', M[M.short_prompt == 0]); print('substantive prompts only: beta=%+.4f (%.4f) n_leak=%d' % (m.params['leak'], m.bse['leak'], M[M.short_prompt == 0].leak.sum()))
