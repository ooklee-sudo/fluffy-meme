"""Re-run every human-label analysis of the paper on a chosen human label set.
ANALYSIS_PLAN_THIRD_CODER.md replaces the investigator-adjudicated labels ('final') with the v3 labels ('v3').
Same definitions as analysis_v2relabel.py, analysis_v4_headline.py, analysis_v4b.py, analysis_h5c_h8.py and
analysis_robust_headline.py; day-cluster bootstraps are vectorized (same resampling scheme, 10,000 draws).
Run from misq_note/hf:  python analysis_reanalysis.py final|v3 [--no-placebo]
"""
import sys, json, numpy as np, pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score as ck
HC = sys.argv[1]; PLACEBO = '--no-placebo' not in sys.argv
rng = np.random.default_rng(20261015)
T = pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep = T.ep.values; mid = T.mid.values; spr = T.spread.values
def mk(maxage):
    def P(s):
        i = np.searchsorted(tep, s, side='right') - 1
        return np.nan if i < 0 or s - tep[i] > maxage else mid[i]
    return P
P = mk(600)
def nticks(a, b): return int(np.searchsorted(tep, b, side='left') - np.searchsorted(tep, a, side='left'))
L = pd.read_csv('model_v2_labels_191.csv', dtype={'id': str}).merge(
    pd.read_csv('human_labels_191_v3.csv', dtype={'id': str})[['id', 'v3', 'third_only', 'v3_how']], on='id')
a = pd.read_csv('raw/truth_archive.csv', dtype={'id': str}); a['ep'] = pd.to_datetime(a.created_at, utc=True, format='ISO8601').map(lambda x: x.timestamp())
H = L.merge(a[['id', 'ep']], on='id').sort_values('ep').reset_index(drop=True)
H['gap'] = H.ep.diff().fillna(1e9); H['day'] = pd.to_datetime(H.ep, unit='s', utc=True).dt.date.astype(str)
H['hum'] = H[HC]
H['cons'] = (H.source == 'consensus') if HC == 'final' else (H.v3_how == 'consensus')
allep = H.ep.values
SG = {'ESC': 1, 'DEESC': -1}
R = {'human_label': HC}

# ---------- day-cluster bootstrap helpers ----------
def dcb_stat(v, days, stat=np.mean, B=10000):
    ud = np.unique(days); g = {u: v[days == u] for u in ud}
    o = [stat(np.concatenate([g[u] for u in rng.choice(ud, len(ud))])) for _ in range(B)]
    return [float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5))]

# ---------- union frame (Table 3, decomposition, simulation frame) ----------
E = H[H.gap >= 3 * 3600].copy(); E['r30'] = 100 * np.log((E.ep + 1800).map(P) / E.ep.map(P)); E = E[E.r30.notna()].copy()
R['union_events'] = int(len(E))
days = np.array(sorted(E.day.unique())); di = E.day.map({d: i for i, d in enumerate(days)}).values
W = np.stack([np.bincount(r, minlength=len(days)) for r in rng.integers(0, len(days), (10000, len(days)))])
def bmean(col, c):
    m = (E[col] == c).values; a_ = np.bincount(di, weights=SG[c] * E.r30.values * m, minlength=len(days)); n_ = np.bincount(di, weights=m.astype(float), minlength=len(days))
    with np.errstate(invalid='ignore', divide='ignore'): return (W @ a_) / (W @ n_)
def cmean(col, c): s = E[E[col] == c]; return float((SG[c] * s.r30).mean()) if len(s) else np.nan
SETS = {'human': 'hum', 'model1': 'model1', 'v2_majority': 'v2_maj', 'v2_opus': 'v2_run1', 'v2_sonnet': 'v2_run2', 'v2_haiku': 'v2_run3', 'v2_sonnet_repeat': 'v2_run4'}
R['table3'] = {}
for nm, col in SETS.items():
    o = {}
    for c in ('DEESC', 'ESC'):
        v = SG[c] * E[E[col] == c].r30.values; b = bmean(col, c); b = b[~np.isnan(b)]
        o[c] = dict(n=int(len(v)), mean=float(v.mean()), median=float(np.median(v)), p_two=float(stats.wilcoxon(v).pvalue),
                    ci=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))])
        if nm != 'human':
            d = bmean('hum', c) - bmean(col, c); d = d[~np.isnan(d)]
            o[c]['diff_human_minus'] = dict(diff=cmean('hum', c) - cmean(col, c), ci=[float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
                                            p_two=float(min(1, 2 * min((d <= 0).mean(), (d >= 0).mean()))))
    R['table3'][nm] = o
def prf(pred, true, c):
    tp = ((pred == c) & (true == c)).sum(); return dict(precision=float(tp / max((pred == c).sum(), 1)), recall=float(tp / max((true == c).sum(), 1)), n_pred=int((pred == c).sum()))
def ac1(a_, b_):
    cats = sorted(set(a_) | set(b_)); po = (a_.values == b_.values).mean(); pi = np.array([((a_ == c).mean() + (b_ == c).mean()) / 2 for c in cats]); pe = (pi * (1 - pi)).sum() / (len(cats) - 1); return float((po - pe) / (1 - pe))
def bk(x, y, B=2000):
    x, y = x.reset_index(drop=True), y.reset_index(drop=True); n = len(x)
    ks = [ck(x.iloc[i], y.iloc[i]) for i in (rng.integers(0, n, n) for _ in range(B))]; return [float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5))]
R['table2'] = {nm: dict(kappa=float(ck(H.hum, H[col])), kappa_ci=bk(H.hum, H[col]), ac1=ac1(H.hum, H[col]), ESC=prf(H[col], H.hum, 'ESC'), DEESC=prf(H[col], H.hum, 'DEESC'))
               for nm, col in SETS.items() if nm != 'human'}
R['human_counts'] = H.hum.value_counts().to_dict()

# ---------- decomposition (Table 4) ----------
R['decomposition'] = {}
for nm, col in (('model1', 'model1'), ('v2_majority', 'v2_maj')):
    R['decomposition'][nm] = {}
    for c in ('ESC', 'DEESC'):
        ma = E[E[col] == c]; muH = cmean('hum', c); o = dict(events=int(len(ma)), model_mean=cmean(col, c), human_mean=muH, groups={})
        for h in ('ESC', 'DEESC', 'MIXED', 'OTHER'):
            g = ma[ma.hum == h]; m_ = float((SG[c] * g.r30).mean()) if len(g) else None
            o['groups'][h] = dict(n=int(len(g)), mean=m_, contribution=(len(g) / len(ma)) * (m_ - muH) if len(g) else 0.0)
        o['gap'] = o['model_mean'] - muH; R['decomposition'][nm][c] = o

# ---------- headline, sample reconciliation, adjudication split ----------
def events(mask=None, gap_h=3, col='hum'):
    d = H.copy(); d['lab'] = d[col]
    if mask is not None: d.loc[~mask(d), 'lab'] = 'OTHER'
    keep = (d.gap >= gap_h * 3600) if gap_h > 0 else np.ones(len(d), bool)
    k = d[keep & d.lab.isin(['ESC', 'DEESC'])].copy(); k['sgn'] = np.where(k.lab == 'ESC', 1, -1); return k
def post(k, win=30, maxage=600):
    Pm = mk(maxage); w = win * 60; k = k.copy()
    k['p0'] = k.ep.map(Pm); k['post'] = k.sgn * 100 * np.log(k.ep.add(w).map(Pm) / k.p0); k['pre'] = k.sgn * 100 * np.log(k.p0 / k.ep.sub(w).map(Pm)); return k
def summ(s, ci=True):
    v = s.post.values; o = dict(n=int(len(v)), days=int(s.day.nunique()), mean=float(v.mean()), median=float(np.median(v)), p_two=float(stats.wilcoxon(v).pvalue))
    if ci: o['ci_mean'] = dcb_stat(v, s.day.values); o['ci_median'] = dcb_stat(v, s.day.values, np.median)
    return o
K = post(events()); V = K.dropna(subset=['post'])
R['headline'] = {c: summ(V[V.lab == c]) for c in ('DEESC', 'ESC')}
K5 = post(events(), win=5).dropna(subset=['post']); R['headline_5min'] = {c: float(K5[K5.lab == c].post.mean()) for c in ('DEESC', 'ESC')}
R['difference_classes_mannwhitney_p'] = float(stats.mannwhitneyu(V[V.lab == 'DEESC'].post, V[V.lab == 'ESC'].post).pvalue)
k3 = events(); k3['p0'] = k3.ep.map(P); k3['p30'] = (k3.ep + 1800).map(P); k3['m60'] = (k3.ep - 3600).map(P)
k3['nowin'] = k3.p0.isna() | k3.p30.isna(); k3['wk'] = pd.to_datetime(k3.ep, unit='s', utc=True).dt.dayofweek >= 5
R['reconciliation'] = dict(after_filter=int((H.gap >= 3 * 3600).sum()), signal={c: int((k3.lab == c).sum()) for c in ('DEESC', 'ESC')},
    with_window={c: int(((k3.lab == c) & ~k3.nowin).sum()) for c in ('DEESC', 'ESC')},
    with_window_and_m60={c: int(((k3.lab == c) & ~k3.nowin & k3.m60.notna()).sum()) for c in ('DEESC', 'ESC')},
    dropped={c: int(((k3.lab == c) & k3.nowin).sum()) for c in ('DEESC', 'ESC')},
    dropped_weekend_share=float(k3[k3.nowin].wk.mean()), all_signal_weekend_share=float(k3.wk.mean()))
R['adjudication'] = {}
for nm, mask in (('all', None), ('consensus_only', lambda d: d.cons), ('not_consensus', lambda d: ~d.cons)):
    kk = post(events(mask=mask)).dropna(subset=['post'])
    R['adjudication'][nm] = {c: (summ(kk[kk.lab == c]) if (kk.lab == c).sum() >= 6 else dict(n=int((kk.lab == c).sum()), mean=float(kk[kk.lab == c].post.mean()) if (kk.lab == c).any() else None)) for c in ('DEESC', 'ESC')}
R['label_counts_by_class'] = {c: int((H.hum == c).sum()) for c in ('ESC', 'DEESC', 'MIXED', 'OTHER')}
R['not_consensus_by_class'] = {c: int(((H.hum == c) & ~H.cons).sum()) for c in ('ESC', 'DEESC')}

# ---------- robustness (Table 8) ----------
def cell(k):
    o = {}
    for c in ('DEESC', 'ESC'):
        s = k[k.lab == c]; v = s.dropna(subset=['post']); b = s.dropna(subset=['post', 'pre']); x = dict(n=int(len(v)))
        if len(v) >= 6:
            x.update(mean=float(v.post.mean()), median=float(v.post.median()), p_post=float(stats.wilcoxon(v.post).pvalue))
            if len(b) >= 6:
                d = b.post - b.pre; x.update(n_paired=int(len(b)), mean_pre=float(b.pre.mean()), paired=float(d.mean()), p_paired=float(stats.wilcoxon(d).pvalue))
        o[c] = x
    return o
R['robustness'] = {'baseline': cell(post(events())), 'no_cluster_filter': cell(post(events(gap_h=0))), 'six_hour_filter': cell(post(events(gap_h=6))),
                   'consensus_only': cell(post(events(mask=lambda d: d.cons)))}
for w in (5, 15, 60): R['robustness'][f'window_{w}'] = cell(post(events(), win=w))
kb = events(); kb = kb[~kb.day.isin(('2026-03-23', '2026-04-07'))]; R['robustness']['drop_big_days'] = cell(post(kb))
R['robustness']['dropped_events_big_days'] = int(len(events()) - len(kb))
for gh in (1, 2): R['robustness'][f'cluster_{gh}h'] = cell(post(events(gap_h=gh)))
R['loo'] = {}
for c in ('DEESC', 'ESC'):
    v = V[V.lab == c].post.values; loo = [np.delete(v, i).mean() for i in range(len(v))]
    R['loo'][c] = dict(min=float(min(loo)), max=float(max(loo)), top3_share=float(np.sort(v)[-3:].sum() / v.sum()), largest=[float(x) for x in np.sort(v)[-3:]])
idx = [np.searchsorted(tep, e, side='right') - 1 for e in V.ep]
R['spread'] = dict(median_spread=float(np.median(spr[idx])), median_price=float(np.median(V.p0)), median_abs_move=float(np.median(np.abs(np.exp(V.post / 100 * V.sgn) * V.p0 - V.p0))))

# ---------- placebo, drift-matched placebo, pre-post drift, figure ----------
if PLACEBO:
    def cands(ev, B=60):
        pools = []
        for r in ev.itertuples():
            base = np.floor(r.ep / 3600) * 3600; wk = pd.Timestamp(r.ep, unit='s', tz='UTC').weekday() >= 5; cs = []
            for dd in (-3, -2, -1, 1, 2, 3):
                for _ in range(B):
                    t = base + dd * 86400 + rng.uniform(0, 3600)
                    if (pd.Timestamp(t, unit='s', tz='UTC').weekday() >= 5) != wk or np.min(np.abs(allep - t)) <= 7200: continue
                    p0 = P(t); p30 = P(t + 1800)
                    if np.isnan([p0, p30]).any(): continue
                    m30 = P(t - 1800); m60 = P(t - 3600); m5 = P(t - 300)
                    cs.append(dict(t=t, post30=r.sgn * 100 * np.log(p30 / p0), pre30=r.sgn * 100 * np.log(p0 / m30) if not np.isnan(m30) else np.nan,
                                   pre60=r.sgn * 100 * np.log(m5 / m60) if not np.isnan(m60) and not np.isnan(m5) else np.nan, tc=nticks(t - 1800, t)))
            pools.append(pd.DataFrame(cs))
        return pools
    def simmean(pools, ok, key, n=10000, sub=None):
        arrs = [(sub[i] if sub else pools[i])[key].dropna().values for i in ok]; arrs = [x for x in arrs if len(x)]
        return np.array([np.mean([x[rng.integers(len(x))] for x in arrs]) for _ in range(n)])
    V['m30'] = V.ep.sub(1800).map(P); V['m60'] = V.ep.sub(3600).map(P); V['m5'] = V.ep.sub(300).map(P)
    V['pre30'] = V.sgn * 100 * np.log(V.p0 / V.m30); V['pre60'] = V.sgn * 100 * np.log(V.m5 / V.m60); V['tc'] = [nticks(e - 1800, e) for e in V.ep]
    R['placebo'] = {}; FIG = {'offsets': list(range(-60, 61, 5))}
    for c in ('DEESC', 'ESC'):
        s = V[V.lab == c].reset_index(drop=True); pools = cands(s); ok = [i for i, p in enumerate(pools) if len(p)]
        o = dict(n=int(len(s)), n_with_pool=len(ok))
        sims = simmean(pools, ok, 'post30'); obs = float(s.post.iloc[ok].mean())
        o['same_hour'] = dict(observed=obs, placebo_mean=float(sims.mean()), p95=float(np.percentile(sims, 95)), p99=float(np.percentile(sims, 99)), share_ge=float((sims >= obs).mean()))
        sub = {}
        for i in ok:   # drift-matched: 20% of candidates whose pre-30 return is closest to the event's
            p = pools[i].dropna(subset=['pre30'])
            if len(p) >= 10 and not np.isnan(s.pre30.iloc[i]):
                kq = max(5, int(0.2 * len(p))); sub[i] = p.iloc[np.argsort(np.abs(p.pre30.values - s.pre30.iloc[i]))[:kq]]
        okm = list(sub); sims = np.array([np.mean([sub[i].post30.values[rng.integers(len(sub[i]))] for i in okm]) for _ in range(10000)])
        obs_m = float(s.post.iloc[okm].mean())
        o['drift_matched'] = dict(n=len(okm), observed=obs_m, event_pre30_mean=float(s.pre30.iloc[okm].mean()), placebo_mean=float(sims.mean()), p95=float(np.percentile(sims, 95)), share_ge=float((sims >= obs_m).mean()))
        dm = s.m60.notna() & s.m5.notna(); okd = [i for i in ok if dm.iloc[i]]
        o['drift'] = dict(n=len(okd))
        for key, col in (('pre30', 'pre30'), ('pre60', 'pre60')):
            obs = float(s[col].iloc[okd].mean()); sims = simmean(pools, okd, key)
            o['drift'][key] = dict(observed=obs, placebo_mean=float(sims.mean()), p95=float(np.percentile(sims, 95)), share_ge=float((sims >= obs).mean()))
        obs = float(s.tc.iloc[okd].mean()); sims = simmean(pools, okd, 'tc'); o['drift']['ticks_pre30_ratio'] = float(obs / sims.mean())
        R['placebo'][c] = o
        # figure: event path and placebo band
        offs = np.arange(-60, 61, 5)
        def path(eps, sg):
            p0 = np.array([P(e) for e in eps]); return np.array([sg * 100 * np.log(np.array([P(e + o_ * 60) for e in eps]) / p0) for o_ in offs]).T
        Mx = path(s.ep.values, s.sgn.values)
        f = dict(n=int(len(s)), mean=np.nanmean(Mx, 0).tolist(), median=np.nanmedian(Mx, 0).tolist(), se=(np.nanstd(Mx, 0, ddof=1) / np.sqrt((~np.isnan(Mx)).sum(0))).tolist())
        sims = []
        for _ in range(1000):
            ts = np.array([pools[i].t.values[rng.integers(len(pools[i]))] for i in ok]); sims.append(np.nanmean(path(ts, s.sgn.values[ok]), 0))
        sims = np.array(sims); f['placebo_lo'] = np.nanpercentile(sims, 2.5, 0).tolist(); f['placebo_hi'] = np.nanpercentile(sims, 97.5, 0).tolist()
        FIG[c] = f
    R['figure_path'] = FIG
json.dump(R, open(f'results_reanalysis_{HC}.json', 'w'), indent=1, default=float)
show = {k: R[k] for k in ('union_events', 'headline', 'headline_5min', 'reconciliation', 'adjudication', 'not_consensus_by_class', 'loo', 'spread') if k in R}
print(json.dumps(show, indent=1, default=float)[:6000])
