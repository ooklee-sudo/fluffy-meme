"""Build headline-only Upworthy tests and empirical-Bayes 'true' CTRs."""
import sys, numpy as np, pandas as pd
src, out = sys.argv[1], sys.argv[2]
d = pd.read_csv(src, low_memory=False)
d = d[d.impressions > 0].copy()
d['headline'] = d.headline.astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
# arm = distinct headline within a test (pool over images/excerpts)
a = (d.groupby(['clickability_test_id', 'headline'], as_index=False)
       .agg(impressions=('impressions', 'sum'), clicks=('clicks', 'sum'),
            excerpt=('excerpt', 'first'), n_img=('eyecatcher_id', 'nunique'),
            created_at=('created_at', 'min')))
t = a.groupby('clickability_test_id').agg(K=('headline', 'size'), minimp=('impressions', 'min'))
keep = t[(t.K >= 3) & (t.K <= 8) & (t.minimp >= 1000)].index
a = a[a.clickability_test_id.isin(keep)].copy()
# empirical Bayes on logit CTR within test
p = (a.clicks + 0.5) / (a.impressions + 1)
a['y'] = np.log(p / (1 - p))
a['v'] = 1 / (a.clicks + 0.5) + 1 / (a.impressions - a.clicks + 0.5)
a['dev'] = a.y - a.groupby('clickability_test_id').y.transform('mean')
Kc = a.groupby('clickability_test_id').y.transform('size')
tau2 = max(((a.dev**2) * Kc / (Kc - 1)).mean() - a.v.mean(), 1e-6)
w = tau2 / (tau2 + a.v)
mu = a.groupby('clickability_test_id').y.transform('mean')
a['y_true'] = mu + w * (a.y - mu)
a['p_true'] = 1 / (1 + np.exp(-a.y_true))
print('tests', a.clickability_test_id.nunique(), 'arms', len(a))
print('tau (logit SD of headline effects) =', round(np.sqrt(tau2), 3),
      '| mean sampling SD =', round(np.sqrt(a.v.mean()), 3), '| mean shrink w =', round(w.mean(), 2))
a.to_csv(out, index=False)
