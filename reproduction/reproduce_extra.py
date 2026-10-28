"""Section 7.4 (acquisition interaction, Europe) and Section 7.1 Canadian series.
Usage: python reproduce_extra.py DATA_DIR OUT_DIR   (needs reproduce_tables.py outputs in OUT_DIR and noc_scores.jsonl in DATA_DIR)"""
import sys, os, json
import numpy as np, pandas as pd
import statsmodels.api as sm
D, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(20260429); res = {}

# ---------------- Europe: interaction with country-level acquisition ----------------
oja = pd.read_pickle(f'{D}/oja.pkl')
o = oja[(oja.indic_em == 'OJA') & (oja.geo.str.len() == 2) & (oja.isco08.str.len() == 5) & oja.isco08.str.startswith('OC')].copy()
o['occ'] = o.isco08.str[2:]
p = o.pivot_table(index=['geo', 'occ'], columns='time', values='v'); p = p[p['2022'] >= 1.0].dropna()
cells = p.reset_index()[['geo', 'occ']].copy()
for y in (2021, 2023, 2024): cells[f'y{y}'] = np.log(p[str(y)].values / p['2022'].values)
ex = pd.read_csv(f'{OUT}/exposure_by_isco3.csv', dtype={'occ': str}).set_index('occ')
cells = cells.merge(ex[['z_vis', 'z_txt']], left_on='occ', right_index=True)
ai = json.load(open(f'{D}/ai.json')); ids, sizes = ai['id'], ai['size']; cats = {k: list(ai['dimension'][k]['category']['index']) for k in ids}
acq = {}
for flat, v in ai['value'].items():
    flat = int(flat); idx = []
    for s in reversed(sizes): idx.append(flat % s); flat //= s
    r = {k: cats[k][i] for k, i in zip(ids, idx[::-1])}
    if r['indic_is'] == 'E_AI_TPVSG' and r['size_emp'] == 'GE10' and r['unit'] == 'PC_ENT' and r['time'] == '2025': acq[r['geo']] = v
acq = pd.Series(acq); c = cells[cells.geo.isin(acq.index)].copy()
sd = acq[sorted(c.geo.unique())].std(ddof=1)
print('countries with acquisition data:', c.geo.nunique(), 'of', cells.geo.nunique(), ' SD of acquisition (pp): %.2f' % sd)
def inter(d, a_by_geo, y):
    a = d.geo.map(a_by_geo); a = (a - a.mean()) / sd
    X = pd.DataFrame({'zv': d.z_vis, 'zvA': d.z_vis * a, 'zt': d.z_txt, 'ztA': d.z_txt * a})
    X = pd.concat([X, pd.get_dummies(d.geo, drop_first=True, dtype=float)], axis=1)
    m = sm.OLS(d[y], sm.add_constant(X)).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.occ)[0]})
    return m.params['zvA'], m.bse['zvA']
res['europe_interaction'] = {'n_countries': int(c.geo.nunique()), 'sd_acq_pp': float(sd)}
countries = sorted(c.geo.unique()); base = acq[countries]
for y in (2021, 2023, 2024):
    b, se = inter(c, base, f'y{y}')
    draws = []
    for _ in range(2000):
        perm = pd.Series(rng.permutation(base.values), index=countries)
        draws.append(inter(c, perm, f'y{y}')[0])
    res['europe_interaction'][y] = {'b': b, 'se': se, 'p_perm': float((np.abs(draws) >= abs(b)).mean())}
res['europe_interaction']['predicted_beta_-0.5'] = -0.5 * (sd / 100) / ex.z_vis.max()
print(json.dumps(res['europe_interaction'], indent=1, default=float))

# ---------------- Canada: unit-group vacancies, NOC two-digit fixed effects ----------------
v = pd.read_pickle(f'{D}/cad_panel.pkl'); duties = pd.read_pickle(f'{D}/noc_duties.pkl')
sc = pd.DataFrame([json.loads(l) for l in open(f'{D}/noc_scores.jsonl')]).drop_duplicates('task').set_index('task')
duties['duty'] = duties.duty.str.strip(); duties = duties.join(sc[['visual', 'text']], on='duty')
cx = duties.groupby('code').agg(vis=('visual', 'mean'), txt=('text', 'mean'), n=('duty', 'size')); cx[['vis', 'txt']] /= 2
b22 = v[v.year == 2022].pivot_table(index='code', columns='q', values='val').dropna()
keep = b22[b22.sum(axis=1) >= 1000].index.intersection(cx.index)
cx = cx.loc[keep]
for k in ('vis', 'txt'): cx['z_' + k] = (cx[k] - cx[k].mean()) / cx[k].std(ddof=1)
cx['grp'] = cx.index.str[:2]
print('Canada unit groups:', len(cx), ' two-digit groups:', cx.grp.nunique(), ' max z visual: %.2f' % cx.z_vis.max(), ' corr(vis,txt) %.2f' % cx[['vis', 'txt']].corr().iloc[0, 1])
print(cx.sort_values('z_vis', ascending=False).head(4)[['vis', 'z_vis']])
res['canada'] = {'n_groups': int(len(cx)), 'n_two_digit': int(cx.grp.nunique()), 'max_z': float(cx.z_vis.max()), 'corr_vis_txt': float(cx[['vis', 'txt']].corr().iloc[0, 1])}
def cad_year(y):
    vy = v[v.year == y].pivot_table(index='code', columns='q', values='val'); qs = [q for q in vy.columns]
    out = []
    for q_set in [qs]:
        pass
    b = v[v.year == 2022].pivot_table(index='code', columns='q', values='val')[qs]
    vv = vy[qs]; ok = vv.notna().all(axis=1) & b.notna().all(axis=1)
    d = cx.loc[cx.index.intersection(ok[ok].index)].copy()
    d['y'] = np.log(vv.loc[d.index].mean(axis=1) / b.loc[d.index].mean(axis=1))
    return d, qs
def cad_fit(d, y='y', permute=False):
    z = d.z_vis.copy()
    if permute: z = d.groupby('grp').z_vis.transform(lambda s: rng.permutation(s.values))
    X = pd.concat([pd.DataFrame({'zv': z, 'zt': d.z_txt}), pd.get_dummies(d.grp, drop_first=True, dtype=float)], axis=1)
    m = sm.OLS(d[y], sm.add_constant(X)).fit(cov_type='HC1')
    return m.params['zv'], m.bse['zv']
res['canada']['years'] = {}
for y in (2023, 2024, 2025, 2026):
    d, qs = cad_year(y); b, se = cad_fit(d)
    draws = [cad_fit(d, permute=True)[0] for _ in range(2000)]
    res['canada']['years'][y] = {'n': int(len(d)), 'quarters': qs, 'b': b, 'se': se, 'mde': 2.8 * se, 'p_rand': float((np.abs(draws) >= abs(b)).mean())}
print(json.dumps(res['canada'], indent=1, default=float))
json.dump(res, open(f'{OUT}/extra_summary.json', 'w'), indent=1, default=float)
