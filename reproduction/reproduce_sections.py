"""Sections 6.2, 7.3 and 7.5: barrier correlations, sector exposure, LFS employment, sector-level acquisition vs employment.
Usage: python reproduce_sections.py DATA_DIR OUT_DIR  (needs ai.pkl, ain2.pkl, egan2.pkl, egan22d.pkl, eisn2.pkl, egai2d.pkl,
indeed_sector.csv, esco_onet.xlsx, onet/, scores.jsonl in DATA_DIR; see README)."""
import sys, json, itertools
import numpy as np, pandas as pd
import statsmodels.api as sm
D, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(20260430); R = {}
AGG = {'EU27_2020', 'EA', 'EA19', 'EA20', 'EA21'}
EUR = set('AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK'.split())

# ---------------- 6.2 / Table 3: barriers among enterprises that considered AI ----------------
ai = pd.read_pickle(f'{D}/ai.pkl'); ai = ai[ai.time == '2025']
code = {'expertise': 'E_AI_BLE', 'legal': 'E_AI_BLEG', 'data_protection': 'E_AI_BCDP', 'costs': 'E_AI_BCST', 'ethics': 'E_AI_BEC',
        'data_availability': 'E_AI_BDDT', 'incompatibility': 'E_AI_BINC', 'not_useful': 'E_AI_BNU'}
eu = {k: float(ai[(ai.indic_is == c) & (ai.unit == 'PC_ENT_AI_EC') & (ai.size_emp == 'GE10') & (ai.geo == 'EU27_2020')].v.iloc[0]) for k, c in code.items()}
R['table3_eu27_pct_of_considerers'] = eu
R['table3_by_size'] = {sz: {k: float(ai[(ai.indic_is == c) & (ai.unit == 'PC_ENT_AI_EC') & (ai.size_emp == sz) & (ai.geo == 'EU27_2020')].v.iloc[0]) for k, c in code.items()} for sz in ('10-49', '50-249', 'GE250')}
acq = ai[(ai.indic_is == 'E_AI_TPVSG') & (ai.unit == 'PC_ENT') & (ai.size_emp == 'GE10')].set_index('geo').v
X = pd.DataFrame({k: ai[(ai.indic_is == code[k]) & (ai.unit == 'PC_ENT_AI_EC') & (ai.size_emp == 'GE10')].set_index('geo').v for k in ('costs', 'legal', 'data_protection', 'expertise')})
X['acq'] = acq; X = X.drop(index=[g for g in AGG if g in X.index]).dropna()
R['cross_country'] = {'n': int(len(X)), **{k: float(X.acq.corr(X[k])) for k in ('costs', 'legal', 'data_protection', 'expertise')}}

# ---------------- occupation exposure at ISCO one digit ----------------
cw = pd.read_excel(f'{D}/esco_onet.xlsx', header=3); cw.columns = ['esco', 'esco_title', 'soc', 'soc_title']
cw['isco1'] = cw.esco.astype(str).str.extract(r'^(\d)')[0]
ts = pd.read_csv(f'{D}/onet/db_29_1_text/Task Statements.txt', sep='\t')[['O*NET-SOC Code', 'Task']]
sc = pd.DataFrame([json.loads(l) for l in open(f'{D}/scores.jsonl')]).drop_duplicates('task').set_index('task')
exp1 = {}
for o in sorted(cw.isco1.dropna().unique()):
    tasks = ts[ts['O*NET-SOC Code'].isin(set(cw.loc[cw.isco1 == o, 'soc']))].Task.drop_duplicates()
    s = sc.reindex(tasks).visual.dropna(); exp1['OC' + o] = s.mean() / 2
R['exposure_isco1'] = exp1; print('ISCO-1 exposure:', {k: round(v, 3) for k, v in exp1.items()})

# ---------------- sector exposure and acquisition by sector ----------------
ain = pd.read_pickle(f'{D}/ain2.pkl'); eis = pd.read_pickle(f'{D}/eisn2.pkl')
SECT9 = list('CFGHIJLMN')
def sector_exposure(year='2022'):
    e = eis[(eis.sex == 'T') & (eis.age == 'Y_GE15') & (eis.time == year) & eis.isco08.isin(exp1.keys()) & eis.nace_r2.isin(SECT9)]
    w = e.pivot_table(index=['geo', 'nace_r2'], columns='isco08', values='v')
    ex = pd.Series(exp1)[w.columns]
    ok = w.notna()
    s = (w.fillna(0) * ex).sum(axis=1) / (w.fillna(0).sum(axis=1)); s[w.notna().sum(axis=1) < 5] = np.nan
    return s.rename('exposure')
se = sector_exposure()
types = {'visual': 'E_AI_TPVSG', 'text': 'E_AI_TNLG', 'image_recognition': 'E_AI_TIR', 'any': 'E_AI_TANY'}
A = {k: ain[(ain.indic_is == c) & ain.nace_r2.isin(SECT9)].set_index(['geo', 'nace_r2']).v for k, c in types.items()}
# EU27 sector-level correlation
eu_e = se.xs('EU27_2020', level='geo')
R['sector_corr_eu27'] = {k: float(eu_e.corr(A[k].xs('EU27_2020', level='geo').reindex(eu_e.index))) for k in types}
R['sector_corr_eu27_n'] = int(eu_e.notna().sum())
# country-sector cells with country fixed effects
cells = pd.concat(A, axis=1).join(se, how='inner'); cells = cells[~cells.index.get_level_values(0).isin(AGG)].dropna()
cells = cells[cells.index.get_level_values(0).isin(set(eis.geo) - AGG)]
cells = cells.reset_index(); cells.columns = ['geo', 'sec'] + list(types) + ['exposure']
cells['z'] = (cells.exposure - cells.exposure.mean()) / cells.exposure.std(ddof=1)
def fe_coef(d, y, zcol='z'):
    Xm = pd.concat([d[[zcol]], pd.get_dummies(d.geo, drop_first=True, dtype=float)], axis=1)
    return sm.OLS(d[y], sm.add_constant(Xm)).fit(cov_type='HC1')
res = {}
for y in types:
    m = fe_coef(cells, y); b = m.params['z']
    secs = np.array(sorted(cells.sec.unique())); zs = cells.groupby('sec').z.mean()
    draws = []
    for _ in range(3000):
        perm = dict(zip(secs, rng.permutation(zs.loc[secs].values)))
        d2 = cells.assign(zp=cells.sec.map(perm)); draws.append(fe_coef(d2, y, 'zp').params['zp'])
    res[y] = {'b': float(b), 'se': float(m.bse['z']), 'p_perm': float((np.abs(draws) >= abs(b)).mean())}
R['sector_exposure_acquisition_fe'] = {'n_cells': int(len(cells)), 'n_countries': int(cells.geo.nunique()), 'n_sectors': int(cells.sec.nunique()), **res}

# ---------------- 7.3: LFS employment ----------------
def lfs(df, age, sex='T'):
    return df[(df.age == age) & (df.sex == sex) & (df.geo == 'EU27_2020')]
def growth(piv, pre, post): return np.log(piv[post].mean(axis=1) / piv[pre].mean(axis=1))
e22 = pd.read_pickle(f'{D}/egan22d.pkl'); R['lfs_2digit'] = {}
for age in ('Y15-74', 'Y_GE15', 'Y15-64'):
    x = lfs(e22, age); p = x.pivot_table(index='nace_r2', columns='time', values='v')
    p = p[~p.index.isin(['TOTAL'])].dropna(subset=[str(y) for y in (2019, 2020, 2021, 2023, 2024, 2025)])
    g = growth(p, ['2019', '2020', '2021'], ['2023', '2024', '2025'])
    cre = [c for c in g.index if c in ('J59', 'J59_J60', 'M73', 'M74', 'M74_M75')]
    others = g.drop(cre)
    obs = g[cre].mean() - others.mean()
    draws = [g.loc[rng.choice(g.index, len(cre), replace=False)].mean() - 0 for _ in range(1)]
    dd = []
    for _ in range(5000):
        pick = rng.choice(len(g), len(cre), replace=False); mask = np.zeros(len(g), bool); mask[pick] = True
        dd.append(g.values[mask].mean() - g.values[~mask].mean())
    R['lfs_2digit'][age] = {'n_industries': int(len(g)), 'creative_codes': cre, 'creative_growth': {c: float(g[c]) for c in cre},
                            'median_all': float(g.median()), 'creative_minus_others': float(obs), 'p_rand': float((np.abs(dd) >= abs(obs)).mean())}
print(json.dumps(R['lfs_2digit'], indent=1, default=float))
ei = eis[(eis.sex == 'T') & (eis.age == 'Y_GE15') & (eis.geo == 'EU27_2020') & (eis.isco08 == 'OC2')]
p = ei.pivot_table(index='nace_r2', columns='time', values='v'); p = p[~p.index.isin(['TOTAL'])].dropna(subset=['2019', '2020', '2021', '2023', '2024', '2025'])
g = growth(p, ['2019', '2020', '2021'], ['2023', '2024', '2025'])
R['professionals_by_section'] = {'n_sections': int(len(g)), 'median': float(g.median()), **{s: float(g[s]) for s in ('J', 'M', 'R') if s in g.index}}
e2 = pd.read_pickle(f'{D}/egai2d.pkl'); x = e2[(e2.geo == 'EU27_2020') & (e2.sex == 'T') & (e2.age == 'Y15-74')]
p = x.pivot_table(index='isco08', columns='time', values='v'); gg = growth(p, ['2019', '2020', '2021'], ['2023', '2024', '2025'])
R['cultural_professionals_oc26'] = float(gg['OC26']) if 'OC26' in gg.index else None; R['oc2_all_2digit_median'] = float(gg.median())
# US Indeed sector postings (descriptive)
ind = pd.read_csv(f'{D}/indeed_sector.csv'); ind = ind[ind.variable == 'total postings'].copy(); ind['date'] = pd.to_datetime(ind.date)
ind['y'] = ind.date.dt.year; yr = ind.groupby(['display_name', 'y']).indeed_job_postings_index.mean().unstack()
ch = np.log(yr.loc[:, 2023:2025].mean(axis=1) / yr[2022]); pre = np.log(yr[2022] / yr[2020])
sel = ['Arts & Entertainment', 'Media & Communications', 'Marketing', 'Software Development', 'Data & Analytics']
R['indeed_2023_25_vs_2022'] = {'selected': {s: float(ch[s]) for s in sel}, 'median_all': float(ch.median()), 'n_sectors': int(len(ch)),
                               'rank_of_selected': {s: int(ch.rank()[s]) for s in sel}, 'pre_2022_vs_2020': {s: float(pre[s]) for s in sel}, 'pre_median': float(pre.median())}

# ---------------- 7.5: sector-level acquisition and employment growth ----------------
e2s = pd.read_pickle(f'{D}/egan2.pkl'); out75 = {}
for age in ('Y15-74', 'Y_GE15'):
    x = e2s[(e2s.age == age) & (e2s.sex == 'T') & e2s.nace_r2.isin(SECT9) & ~e2s.geo.isin(AGG)]
    p = x.pivot_table(index=['geo', 'nace_r2'], columns='time', values='v')
    cols = [str(y) for y in (2016, 2017, 2018, 2019, 2020, 2021, 2023, 2024, 2025)]
    p = p.dropna(subset=cols)
    gp = growth(p, ['2019', '2020', '2021'], ['2023', '2024', '2025']).rename('g_post'); gpre = growth(p, ['2016', '2017', '2018'], ['2019', '2020', '2021']).rename('g_pre')
    d = pd.concat([gp, gpre], axis=1).join(pd.concat(A, axis=1), how='inner').dropna().reset_index()
    d.columns = ['geo', 'sec', 'g_post', 'g_pre'] + list(types)
    d = d[d.geo.isin(EUR | {'NO', 'IS', 'CH', 'UK', 'TR', 'ME', 'MK', 'RS', 'AL', 'BA'})]
    sd_v = d.visual.std(ddof=1)
    for k in types: d['z_' + k] = (d[k] - d[k].mean()) / d[k].std(ddof=1)
    def fit(y, xs, d=d):
        Xm = pd.concat([d[xs], pd.get_dummies(d.geo, drop_first=True, dtype=float)], axis=1)
        return sm.OLS(d[y], sm.add_constant(Xm)).fit(cov_type='HC1')
    d['g_diff'] = d.g_post - d.g_pre
    m_post, m_pre, m_diff = fit('g_post', ['z_visual']), fit('g_pre', ['z_visual']), fit('g_diff', ['z_visual'])
    m_ctl = fit('g_diff', ['z_visual', 'z_text'])
    out75[age] = {'n_cells': int(len(d)), 'n_countries': int(d.geo.nunique()), 'sd_acq_pp': float(sd_v),
                  'post': [float(m_post.params['z_visual']), float(m_post.bse['z_visual'])],
                  'pre': [float(m_pre.params['z_visual']), float(m_pre.bse['z_visual'])],
                  'diff': [float(m_diff.params['z_visual']), float(m_diff.bse['z_visual'])],
                  'diff_with_text_control': [float(m_ctl.params['z_visual']), float(m_ctl.bse['z_visual'])],
                  'corr_visual_text': float(d.visual.corr(d.text)), 'corr_visual_any': float(d.visual.corr(d['any'])),
                  'implied_complete_assimilation_per_s': float(-0.5 * sd_v / 100)}
R['sector_employment'] = out75
print(json.dumps({k: v for k, v in R.items() if k not in ('lfs_2digit',)}, indent=1, default=float))
json.dump(R, open(f'{OUT}/sections_summary.json', 'w'), indent=1, default=float)
