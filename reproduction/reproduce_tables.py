"""Reproduce Tables 4-5 (European exposure gradients and detectability) from public data.
Usage: python reproduce_tables.py DATA_DIR SCORES_JSONL OUT_DIR
Inputs: Eurostat jvs_a_isco3_r1 (oja.pkl), ESCO->O*NET-SOC crosswalk (esco_onet.xlsx), O*NET 29.1 Task Statements,
        LLM scores per task statement (scores.jsonl from score_tasks.py)."""
import sys, os, json
import numpy as np, pandas as pd
import statsmodels.api as sm

DATA, SCORES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20260428)
YEARS = [2019, 2020, 2021, 2023, 2024]; BASE = 2022

# ---------- outcome: country x ISCO-3 cells ----------
oja = pd.read_pickle(os.path.join(DATA, 'oja.pkl'))
o = oja[(oja.indic_em == 'OJA') & (oja.geo.str.len() == 2) & (oja.isco08.str.len() == 5) & oja.isco08.str.startswith('OC')].copy()
o['occ'] = o.isco08.str[2:]
p = o.pivot_table(index=['geo', 'occ'], columns='time', values='v')
p = p[p['2022'] >= 1.0].dropna()                       # >= 1,000 adverts in base year (values in thousands)
cells = p.reset_index()[['geo', 'occ']].copy()
for y in YEARS:
    cells[f'y{y}'] = np.log(p[str(y)].values / p['2022'].values)
print('cells', len(cells), 'occupations', cells.occ.nunique(), 'countries', cells.geo.nunique())

# ---------- exposure: mean task score / 2, pooled over unique tasks of O*NET occupations mapped to ISCO-3 ----------
cw = pd.read_excel(os.path.join(DATA, 'esco_onet.xlsx'), header=3)
cw.columns = ['esco', 'esco_title', 'soc', 'soc_title']
cw['isco3'] = cw.esco.astype(str).str.extract(r'^(\d{3})')[0]
ts = pd.read_csv(os.path.join(DATA, 'onet/db_29_1_text/Task Statements.txt'), sep='\t')[['O*NET-SOC Code', 'Task']]
sc = pd.DataFrame([json.loads(l) for l in open(SCORES)]).drop_duplicates('task').set_index('task')
rows = []
for occ in sorted(cells.occ.unique()):
    socs = set(cw.loc[cw.isco3 == occ, 'soc'])
    tasks = ts[ts['O*NET-SOC Code'].isin(socs)].Task.drop_duplicates()
    s = sc.reindex(tasks)
    rows.append({'occ': occ, 'n_soc': len(socs), 'n_tasks': len(tasks), 'vis': s.visual.mean() / 2, 'txt': s.text.mean() / 2,
                 'vis_share_nonzero': (s.visual > 0).mean()})
ex = pd.DataFrame(rows).set_index('occ')
for c in ('vis', 'txt'):
    ex['z_' + c] = (ex[c] - ex[c].mean()) / ex[c].std(ddof=1)
print('corr(visual, text exposure) across occupations: %.3f' % ex[['vis', 'txt']].corr().iloc[0, 1])
print('top z visual:\n', ex.sort_values('z_vis', ascending=False).head(6)[['vis', 'z_vis', 'n_tasks']])
ex.to_csv(os.path.join(OUT, 'exposure_by_isco3.csv'))
df = cells.merge(ex[['z_vis', 'z_txt']], left_on='occ', right_index=True)

# ---------- regressions: per-year, country FE, cluster by ISCO-3 ----------
def fit(y, controls, d=df):
    X = d[['z_vis'] + controls].copy()
    X = pd.concat([X, pd.get_dummies(d.geo, drop_first=True, dtype=float)], axis=1)
    m = sm.OLS(d[y], sm.add_constant(X)).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.occ)[0]})
    return m.params['z_vis'], m.bse['z_vis']

def perm_p(y, controls, B=5000):
    """Randomization p: permute visual exposure across occupations, re-estimate (FWL with within-country demeaning)."""
    occs = np.array(sorted(df.occ.unique())); idx = pd.Series(range(len(occs)), index=occs)[df.occ].values
    g = pd.factorize(df.geo)[0]
    def demean(M):
        M = np.asarray(M, float).copy()
        for k in np.unique(g): M[g == k] -= M[g == k].mean(axis=0)
        return M
    Y = demean(df[[y]].values); C = demean(df[controls].values) if controls else np.zeros((len(df), 0))
    zv = ex.loc[occs, 'z_vis'].values
    def coef(zvec):
        V = demean(zvec[idx][:, None]); X = np.hstack([V, C])
        return np.linalg.lstsq(X, Y, rcond=None)[0][0, 0]
    obs = coef(zv); draws = np.array([coef(rng.permutation(zv)) for _ in range(B)])
    return float((np.abs(draws) >= abs(obs) - 1e-12).mean())

res = {}
for spec, ctrl in (('preferred', ['z_txt']), ('no_lm', [])):
    for y in YEARS:
        b, se = fit(f'y{y}', ctrl)
        res[(spec, y)] = dict(b=b, se=se, mde=2.8 * se)
for y in YEARS:
    res[('preferred', y)]['p_rand'] = perm_p(f'y{y}', ['z_txt'])
    res[('no_lm', y)]['p_rand'] = perm_p(f'y{y}', [])

# ---------- pre-trend and deviation: joint stacked model with year-specific slopes ----------
def stacked(controls):
    parts = []
    for y in YEARS:
        d = df[['geo', 'occ', 'z_vis', 'z_txt', f'y{y}']].rename(columns={f'y{y}': 'y'}); d['t'] = y; parts.append(d)
    S = pd.concat(parts, ignore_index=True)
    S['gy'] = S.geo + '_' + S.t.astype(str)
    cols = []
    for y in YEARS:
        S[f'v{y}'] = S.z_vis * (S.t == y)
        cols.append(f'v{y}')
        if controls:
            S[f'l{y}'] = S.z_txt * (S.t == y); cols.append(f'l{y}')
    X = pd.concat([S[cols], pd.get_dummies(S.gy, drop_first=True, dtype=float)], axis=1)
    m = sm.OLS(S.y, sm.add_constant(X)).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(S.occ)[0]})
    names = [f'v{y}' for y in YEARS]
    return m.params[names].values, m.cov_params().loc[names, names].values
beta, V = stacked(True)
tt = {y: i for i, y in enumerate(YEARS)}
def deviation(include_base):
    pre = [2019, 2020, 2021] + ([2022] if include_base else [])
    xs = np.array(pre, float); xbar = xs.mean()
    w = np.zeros(len(YEARS))                          # slope = sum w_t * beta_t (base-year beta is 0 by construction)
    for yr in (2019, 2020, 2021): w[tt[yr]] = (yr - xbar) / ((xs - xbar) ** 2).sum()
    slope = w @ beta; se_slope = np.sqrt(w @ V @ w)
    icpt_w = np.zeros(len(YEARS))
    for yr in (2019, 2020, 2021): icpt_w[tt[yr]] = 1 / len(pre)
    out = {'slope': slope, 'slope_se': se_slope}
    for y in (2023, 2024):
        a = icpt_w - w * xbar                         # intercept at x=0 (year 0) as linear combination
        # prediction at year y: intercept + slope*y
        pred_w = a + w * y
        e = np.zeros(len(YEARS)); e[tt[y]] = 1
        dw = e - pred_w
        out[y] = (float(dw @ beta), float(np.sqrt(dw @ V @ dw)))
    return out
dev3, dev4 = deviation(False), deviation(True)

# ---------- write tables ----------
k_top = ex.z_vis.sort_values(ascending=False)
summary = {
    'n_cells': int(len(df)), 'n_occ': int(df.occ.nunique()), 'n_countries': int(df.geo.nunique()),
    'corr_vis_txt': float(ex[['vis', 'txt']].corr().iloc[0, 1]),
    'top_z': {k: float(v) for k, v in k_top.head(5).items()},
    'z_265': float(ex.loc['265', 'z_vis']) if '265' in ex.index else None,
    'z_216': float(ex.loc['216', 'z_vis']) if '216' in ex.index else None,
    'table4': {f'{s}_{y}': v for (s, y), v in res.items()},
    'trend_3pt': dev3, 'trend_4pt': dev4,
}
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, default=float)
print(json.dumps(summary, indent=1, default=float))
