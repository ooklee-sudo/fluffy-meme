"""ANALYSIS_PLAN_THIRD_CODER.md. Part 1 (agreement, v3 final labels) needs no prices; parts 2-4 need raw5m_duka/ticks_WTI.csv.gz.
Run from misq_note/hf:  python analysis_third_coder.py <filled third-coder xlsx> [--market]"""
import sys, json, collections, numpy as np, pandas as pd, openpyxl
from sklearn.metrics import cohen_kappa_score as ck
rng = np.random.default_rng(20261015)
C = ['ESC', 'DEESC', 'MIXED', 'OTHER']
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
rows = list(wb['Coding'].iter_rows(min_row=2, values_only=True))
third = pd.DataFrame({'item': [int(r[0]) for r in rows], 'h3': [str(r[2]).strip().upper() for r in rows], 'conf3': [r[3] for r in rows]})
assert third.h3.isin(C).all(), third.h3.unique()
K = pd.read_csv('third_coder_key_PRIVATE.csv', dtype={'id': str}).merge(third, on='item')
adj, ctl = K[K.kind == 'adjudicated'], K[K.kind != 'adjudicated']
adjA = adj[adj.hA.notna()]   # one adjudicated item has no label from coder A; it is left out of comparisons with A
def boot_k(a, b, B=2000):
    a, b = a.reset_index(drop=True), b.reset_index(drop=True); n = len(a)
    ks = [ck(a.iloc[i], b.iloc[i]) for i in (rng.integers(0, n, n) for _ in range(B))]
    return [float(np.nanpercentile(ks, 2.5)), float(np.nanpercentile(ks, 97.5))]
R = {'n_adjudicated': int(len(adj)), 'n_controls': int(len(ctl))}
R['agreement'] = {
  'third_vs_A_adjudicated': dict(kappa=float(ck(adjA.h3, adjA.hA)), ci=boot_k(adjA.h3, adjA.hA), acc=float((adjA.h3 == adjA.hA).mean()), n=int(len(adjA))),
  'third_vs_B_adjudicated': dict(kappa=float(ck(adj.h3, adj.hB)), ci=boot_k(adj.h3, adj.hB), acc=float((adj.h3 == adj.hB).mean())),
  'third_vs_investigator_adjudicated': dict(kappa=float(ck(adj.h3, adj.final)), ci=boot_k(adj.h3, adj.final), acc=float((adj.h3 == adj.final).mean())),
  'third_vs_consensus_controls': dict(kappa=float(ck(ctl.h3, ctl.final)), ci=boot_k(ctl.h3, ctl.final), acc=float((ctl.h3 == ctl.final).mean())),
  'third_vs_A_controls': dict(kappa=float(ck(ctl.h3, ctl.hA))), 'third_vs_B_controls': dict(kappa=float(ck(ctl.h3, ctl.hB)))}
R['reliable'] = R['agreement']['third_vs_consensus_controls']['kappa'] >= 0.40
# v3 final rule (fixed in the plan)
def v3(r):
    votes = [v for v in (r.hA, r.hB, r.h3) if isinstance(v, str)]   # a missing coder label casts no vote
    c = collections.Counter(votes); top, n = c.most_common(1)[0]
    if n >= 2: return top, ('majority with third coder' if r.h3 == top else 'coders A and B')
    return ('MIXED' if 'MIXED' in c else 'OTHER'), 'three-way tie rule'
adj = adj.copy(); adj[['v3', 'how']] = adj.apply(lambda r: pd.Series(v3(r)), axis=1)
R['items_missing_coder_label'] = int(adj.hA.isna().sum() + adj.hB.isna().sum())
R['tie_rule_items'] = int((adj.how == 'three-way tie rule').sum())
R['changed'] = {'n': int((adj.v3 != adj.final).sum()),
                'from_to': {f'{a}->{b}': int(n) for (a, b), n in collections.Counter(zip(adj.final, adj.v3)).items() if a != b}}
R['investigator_vs_v3_by_class'] = {c: dict(investigator=int((adj.final == c).sum()), v3=int((adj.v3 == c).sum()), third_only=int((adj.h3 == c).sum())) for c in C}
H = pd.read_csv('human_labels_191.csv', dtype={'id': str})
H['v3'] = H.final; H['third_only'] = H.final; H['v3_how'] = np.where(H.source == 'adjudicated', 'unresolved', 'consensus')
m = adj.set_index('id')
for col, src in (('v3', 'v3'), ('third_only', 'h3')):
    H.loc[H.id.isin(m.index), col] = H.loc[H.id.isin(m.index), 'id'].map(m[src])
H.loc[H.id.isin(m.index), 'v3_how'] = H.loc[H.id.isin(m.index), 'id'].map(m['how'])
R['unmatched_adjudicated_in_191'] = int(((H.source == 'adjudicated') & ~H.id.isin(m.index)).sum())
R['counts_191'] = {k: H[k].value_counts().to_dict() for k in ('final', 'v3', 'third_only')}
H.to_csv('human_labels_191_v3.csv', index=False)
print(json.dumps(R, indent=1, default=float))
if '--market' not in sys.argv:
    json.dump(R, open('results_third_coder.json', 'w'), indent=1, default=float); sys.exit()

# ---------- parts 2-4: market analyses with v3 final ----------
from scipy import stats
L = pd.read_csv('model_v2_labels_191.csv', dtype={'id': str}).merge(H[['id', 'v3', 'third_only', 'v3_how']], on='id')
T = pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep = T.ep.values; mid = T.mid.values
def P(s):
    i = np.searchsorted(tep, s, side='right') - 1
    return np.nan if i < 0 or s - tep[i] > 600 else mid[i]
a = pd.read_csv('raw/truth_archive.csv', dtype={'id': str}); a['ep'] = pd.to_datetime(a.created_at, utc=True, format='ISO8601').map(lambda x: x.timestamp())
D = L.merge(a[['id', 'ep']], on='id').sort_values('ep').reset_index(drop=True)
D['gap'] = D.ep.diff().fillna(1e9); D['day'] = pd.to_datetime(D.ep, unit='s', utc=True).dt.date.astype(str)
D['r30'] = 100 * np.log((D.ep + 1800).map(P) / D.ep.map(P))
E = D[(D.gap >= 3 * 3600) & D.r30.notna()].copy()
days = np.array(sorted(E.day.unique())); di = E.day.map({d: i for i, d in enumerate(days)}).values
IDX = rng.integers(0, len(days), (10000, len(days)))          # day-cluster bootstrap draws, shared across statistics
W = np.stack([np.bincount(row, minlength=len(days)) for row in IDX])   # resample weights per day
def daysums(col, c):
    sg = 1 if c == 'ESC' else -1; m = (E[col] == c).values
    return np.bincount(di, weights=sg * E.r30.values * m, minlength=len(days)), np.bincount(di, weights=m.astype(float), minlength=len(days))
def cm(df, col, c):
    s = df[df[col] == c]; return ((1 if c == 'ESC' else -1) * s.r30).mean() if len(s) else np.nan
def bmean(col, c):
    a, n = daysums(col, c)
    with np.errstate(invalid='ignore', divide='ignore'): return (W @ a) / (W @ n)
def clean(x): return x[~np.isnan(x)]
R['events'] = int(len(E))
R['headline'] = {}
for col in ('final', 'v3', 'third_only'):
    o = {}
    for c in ('DEESC', 'ESC'):
        s = E[E[col] == c]; v = (1 if c == 'ESC' else -1) * s.r30.values
        b = clean(bmean(col, c))
        o[c] = dict(n=int(len(v)), days=int(s.day.nunique()), mean=float(v.mean()), median=float(np.median(v)),
                    p_two=float(stats.wilcoxon(v).pvalue), ci=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))])
    R['headline'][col] = o
R['decision_escalation_robust'] = bool(R['headline']['v3']['ESC']['ci'][0] > 0)
def prf(pred, true, c):
    tp = ((pred == c) & (true == c)).sum(); return dict(precision=float(tp / max((pred == c).sum(), 1)), recall=float(tp / max((true == c).sum(), 1)))
R['label_sets_vs_v3'] = {}
for nm, col in (('model1', 'model1'), ('v2_majority', 'v2_maj')):
    diff = {}
    for c in ('DEESC', 'ESC'):
        b = clean(bmean('v3', c) - bmean(col, c))
        diff[c] = dict(model_mean=float(cm(E, col, c)), v3_mean=float(cm(E, 'v3', c)), diff=float(cm(E, 'v3', c) - cm(E, col, c)),
                       ci=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))], p_two=float(min(1, 2 * min((b <= 0).mean(), (b >= 0).mean()))))
    R['label_sets_vs_v3'][nm] = dict(kappa=float(ck(D.v3, D[col])), ESC=prf(D[col], D.v3, 'ESC'), DEESC=prf(D[col], D.v3, 'DEESC'), difference=diff)
R['split_v3'] = {c: E[E.v3 == c].v3_how.value_counts().to_dict() for c in ('DEESC', 'ESC')}
R['split_v3_all191'] = {c: D[D.v3 == c].v3_how.value_counts().to_dict() for c in ('DEESC', 'ESC')}
json.dump(R, open('results_third_coder.json', 'w'), indent=1, default=float)
print(json.dumps({k: R[k] for k in ('events', 'headline', 'decision_escalation_robust', 'label_sets_vs_v3', 'split_v3')}, indent=1, default=float))
