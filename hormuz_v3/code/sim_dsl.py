"""Correction demo: if only a random fraction of the 191 posts had human labels, how close do
naive model-label, human-only, PPI and DSL estimates of the class response come to the full human-label estimate?

Estimand (finite population): theta_c = mean directional 30-min WTI return over the events whose final human label is c,
on the 95 events of Table 3 (three-hour filter, valid 30-minute window).
Run from misq_note/hf:  python dsl/sim_dsl.py [human label column: final (default) | v3]
"""
import json, sys, numpy as np, pandas as pd
HCOL = sys.argv[1] if len(sys.argv) > 1 else 'final'
SUF = '' if HCOL == 'final' else '_' + HCOL
rng = np.random.default_rng(20261015)
REPS = 2000
FRACS = [0.10, 0.20, 0.30, 0.40, 0.50]
RUNS = ['model1', 'v2_run1', 'v2_run2', 'v2_run3', 'v2_run4']

# ---------- events (same construction as analysis_v2relabel.py) ----------
L = pd.read_csv('model_v2_labels_191.csv', dtype={'id': str})
if HCOL != 'final':
    L = L.merge(pd.read_csv('human_labels_191_v3.csv', dtype={'id': str})[['id', HCOL]], on='id')
L['final'] = L[HCOL]   # the human reference label used throughout
T = pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep = T.ep.values; mid = T.mid.values
def P(s):
    i = np.searchsorted(tep, s, side='right') - 1
    return np.nan if i < 0 or s - tep[i] > 600 else mid[i]
a = pd.read_csv('raw/truth_archive.csv', dtype={'id': str})
a['ep'] = pd.to_datetime(a.created_at, utc=True, format='ISO8601').map(lambda x: x.timestamp())
D = L.merge(a[['id', 'ep']], on='id').sort_values('ep').reset_index(drop=True)
D['gap'] = D.ep.diff().fillna(1e9)
D['day'] = pd.to_datetime(D.ep, unit='s', utc=True).dt.date.astype(str)
D['r30'] = 100 * np.log((D.ep + 1800).map(P) / D.ep.map(P))
D['event'] = (D.gap >= 3 * 3600) & D.r30.notna()
E = D[D.event]
print('events', len(E))

def full(col, c):
    s = E[E[col] == c]; sg = 1 if c == 'ESC' else -1
    return float((sg * s.r30).mean()), int(len(s))
check = {f'{col}_{c}': full(col, c) for col in ('final', 'model1', 'v2_maj') for c in ('DEESC', 'ESC')}
print('replication of Table 3 (mean, n):', check)

# ---------- estimators ----------
def ratio(a, b):
    """theta = sum a / sum b with influence-function SE (events treated as independent)."""
    th = a.sum() / b.sum(); ifn = (a - th * b) / b.mean()
    return th, ifn.std(ddof=1) / np.sqrt(len(a))

def estimates(lab, c, surrogate):
    """lab: boolean array over all 191 posts (human label observed). Returns {method: (est, se)} on events."""
    sg = 1.0 if c == 'ESC' else -1.0
    ev = D.event.values; y = sg * D.r30.values
    h = (D.final.values == c).astype(float)
    m = (D[surrogate].values == c).astype(float)
    pi = lab.mean()
    out = {}
    # naive: model label only
    out['naive'] = ratio((y * m)[ev], m[ev])
    # human only: the labelled events
    sel = ev & lab
    out['human_only'] = ratio((y * h)[sel], h[sel]) if h[sel].sum() >= 2 else (np.nan, np.nan)
    # PPI (lambda = 1): surrogate indicator corrected by the labelled residual, inverse-probability weighted
    ht = m + lab / pi * (h - m)
    out['ppi'] = ratio((y * ht)[ev], ht[ev])
    # DSL: cross-fitted P(H=c | votes of the five model runs), then the same design-based correction
    votes = sum((D[r].values == c).astype(int) for r in RUNS)
    g = np.zeros(len(D)); idx = np.flatnonzero(lab); folds = np.array_split(rng.permutation(idx), 5)
    pbar = h[lab].mean()
    for k in range(5):
        tr = np.setdiff1d(idx, folds[k])
        tab = {v: (h[tr][votes[tr] == v].sum() + 2 * pbar) / ((votes[tr] == v).sum() + 2) for v in range(6)}
        fit = np.array([tab[v] for v in votes])
        g[folds[k]] = fit[folds[k]]
        g[~lab] += fit[~lab] / 5          # unlabelled posts: average of fold models
    hd = g + lab / pi * (h - g)
    out['dsl'] = ratio((y * hd)[ev], hd[ev])
    return out

truth = {c: full('final', c)[0] for c in ('DEESC', 'ESC')}
rows = []
for surrogate in ('v2_maj', 'model1'):
    for frac in FRACS:
        k = int(round(frac * len(D)))
        for rep in range(REPS):
            lab = np.zeros(len(D), bool); lab[rng.choice(len(D), k, replace=False)] = True
            for c in ('DEESC', 'ESC'):
                for meth, (est, se) in estimates(lab, c, surrogate).items():
                    rows.append((surrogate, frac, rep, c, meth, est, se))
R = pd.DataFrame(rows, columns=['surrogate', 'frac', 'rep', 'cls', 'method', 'est', 'se'])
R['truth'] = R.cls.map(truth)
R['lo'] = R.est - 1.96 * R.se; R['hi'] = R.est + 1.96 * R.se
R['covers'] = (R.lo <= R.truth) & (R.truth <= R.hi)
R['excl0'] = R.lo > 0
S = (R.groupby(['surrogate', 'cls', 'method', 'frac'])
       .apply(lambda g: pd.Series(dict(mean=g.est.mean(), bias=(g.est - g.truth).mean(),
                                       rmse=np.sqrt(((g.est - g.truth) ** 2).mean()),
                                       ci_width=(g.hi - g.lo).mean(), covers=g.covers.mean(),
                                       excl0=g.excl0.mean(), failed=g.est.isna().mean())), include_groups=False)
       .reset_index())
R.to_csv(f'dsl/sim_draws{SUF}.csv.gz', index=False, compression='gzip')
S.to_csv(f'dsl/sim_summary{SUF}.csv', index=False)
fe = {c: ratio(((1 if c == 'ESC' else -1) * E.r30.values * (E.final.values == c)),
               (E.final.values == c).astype(float)) for c in ('DEESC', 'ESC')}
json.dump(dict(human_label=HCOL, events=int(len(E)), truth=truth, full_human_se={c: float(v[1]) for c, v in fe.items()},
               replication=check, reps=REPS, fracs=FRACS), open(f'dsl/sim_meta{SUF}.json', 'w'), indent=1)
pd.set_option('display.width', 200)
print(S.round(3).to_string(index=False))
