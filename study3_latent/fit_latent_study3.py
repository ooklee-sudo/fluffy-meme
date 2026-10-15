"""ANALYSIS_PLAN_LATENT.md: latent-class correction of the LLM-coded DiD outcomes, without gold labels.
Run from study3/ after classify.py S, Z, L:  python fit_latent_study3.py [--boot 500]"""
import sys, glob, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
from scipy import stats
sys.path.insert(0, '.')
from latent import fit, did, collapse, fit_pair_dependent
warnings.filterwarnings('ignore')
B = int(sys.argv[sys.argv.index('--boot') + 1]) if '--boot' in sys.argv else 500
rng = np.random.default_rng(20261015)
COLS = ['rid', 'overall', 'defect', 'price', 'durability', 'performance', 'fit', 'ease', 'design', 'service']
H = pd.concat([pd.read_csv(f, header=None, names=COLS) for f in sorted(glob.glob('out/H_*.csv'))]).drop_duplicates('rid')
A = pd.concat([pd.read_csv(f, header=None, names=COLS) for f in sorted(glob.glob('out/A_*.csv'))]).drop_duplicates('rid')
M = pd.read_csv('sample_meta.csv')
S = pd.read_csv('out_latent/S.csv'); Z = pd.read_csv('out_latent/Z.csv'); L = pd.read_csv('out_latent/L.csv')
D = M.merge(H, on='rid').merge(S[['rid', 'neg']].rename(columns={'neg': 'S_neg'}), on='rid', how='left') \
     .merge(Z[['rid', 'defect', 'neg', 'perfpos']].add_prefix('Z_').rename(columns={'Z_rid': 'rid'}), on='rid', how='left') \
     .merge(L.rename(columns={'defect': 'L_defect'}), on='rid', how='left')
D['H_defect'] = D.defect.astype(int); D['H_neg'] = (D.overall == 'neg').astype(int); D['H_perfpos'] = (D.performance == 1).astype(int)
D['star_neg'] = (D.rating <= 2).astype(int)
D['cell'] = 2 * D.treated + D.post; D['tp'] = D.treated * D.post
D['q'] = pd.to_datetime(D.ts, unit='ms').dt.to_period('Q').astype(str)
R = {'n': int(len(D)), 'n_S': int(D.S_neg.notna().sum()), 'n_Z': int(D.Z_defect.notna().sum()), 'n_L': int(D.L_defect.notna().sum())}
SPEC = {'defect': ['H_defect', 'Z_defect', 'L_defect'], 'neg': ['H_neg', 'S_neg', 'Z_neg'], 'perfpos': ['H_perfpos', 'Z_perfpos']}

# fast two-way within estimator (product and quarter effects) for the bootstrap; checked against pyfixest below
def fe_beta(y, x, g1, g2, it=200):
    y = y.astype(float).copy(); x = x.astype(float).copy()
    for _ in range(it):
        for g in (g1, g2):
            n = np.bincount(g); y -= (np.bincount(g, y) / n)[g]; x -= (np.bincount(g, x) / n)[g]
        if abs((np.bincount(g1, x) / np.bincount(g1)).max()) < 1e-10 and abs((np.bincount(g2, x) / np.bincount(g2)).max()) < 1e-10: break
    return (x * y).sum() / (x * x).sum()
D['g1'] = pd.factorize(D.pa)[0]; D['g2'] = pd.factorize(D.q)[0]

def estimate(df, out):
    cols = SPEC[out]; X = df[cols].to_numpy(float); Xc, cc, wc = collapse(X, df.cell.to_numpy())
    f = fit(Xc, cc, C=4, wt=wc)
    b = fe_beta(df[cols[0]].to_numpy(), df.tp.to_numpy(), pd.factorize(df.g1)[0], pd.factorize(df.g2)[0])
    return f, b
R['outcomes'] = {}
for out, cols in SPEC.items():
    o = {}
    m = pf.feols(f'{cols[0]} ~ tp | pa + q', data=D, vcov={'CRV1': 'pa'})
    o['naive_fe'] = dict(b=float(m.coef()['tp']), se=float(m.se()['tp']), p=float(m.pvalue()['tp']))
    f, b = estimate(D, out)
    o['fast_fe_check'] = float(b)
    o['latent'] = dict(classifiers=cols, p_cells=f['p'].tolist(), Se=dict(zip(cols, f['Se'][0].tolist())), Sp=dict(zip(cols, f['Sp'][0].tolist())),
                       J=dict(zip(cols, f['J'][0].tolist())), ll=float(f['ll']))
    o['did_latent_cells'] = float(did(f['p'])); o['did_corrected_fe'] = float(b / f['J'][0][0])
    o['naive_cell_did'] = {c: float(did(D.groupby('cell')[c].mean().to_numpy())) for c in cols}
    # over-identification: H accuracy varying by cell (only identified with >= 3 classifiers)
    if len(cols) >= 3:
        X = D[cols].to_numpy(float); Xc, cc, wc = collapse(X, D.cell.to_numpy())
        fv = fit(Xc, cc, C=4, vary_k=0, wt=wc); lr = 2 * (fv['ll'] - f['ll'])
        o['lr_H_cell_varying'] = dict(lr=float(lr), df=6, p=float(stats.chi2.sf(max(lr, 0), 6)),
                                      J_H_by_cell=(fv['Se'][:, 0] + fv['Sp'][:, 0] - 1).tolist())
        sub = D.dropna(subset=cols); Xs = sub[cols].to_numpy(int)
        f_ind = fit(Xs.astype(float), sub.cell.to_numpy(), C=4); f_dep = fit_pair_dependent(Xs, sub.cell.to_numpy(), (0, 2 if out == 'neg' else 1))
        lr2 = 2 * (f_dep['ll'] - f_ind['ll'])
        o['lr_pair_dependence'] = dict(pair=[cols[0], cols[2] if out == 'neg' else cols[1]], n=int(len(sub)), lr=float(lr2), df=2, p=float(stats.chi2.sf(max(lr2, 0), 2)))
    # bootstrap by product
    prods = D.pa.unique(); idx = {p_: np.flatnonzero(D.pa.to_numpy() == p_) for p_ in prods}; bs = []
    for r in range(B):
        pick = rng.choice(prods, len(prods)); rows = np.concatenate([idx[p_] for p_ in pick])
        dfb = D.iloc[rows].copy(); dfb['g1'] = np.repeat(np.arange(len(pick)), [len(idx[p_]) for p_ in pick])
        try:
            fb, bb = estimate(dfb, out); bs.append((did(fb['p']), bb / fb['J'][0][0], fb['J'][0][0], bb))
        except Exception: pass
    bs = np.array(bs)
    def ci(v): return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
    o['boot'] = dict(n=int(len(bs)), did_latent_ci=ci(bs[:, 0]), did_corrected_fe_ci=ci(bs[:, 1]), J_H_ci=ci(bs[:, 2]), naive_fe_ci=ci(bs[:, 3]))
    R['outcomes'][out] = o
# sensitivity: star rating as an additional test for negative sentiment
X = D[['H_neg', 'S_neg', 'Z_neg', 'star_neg']].to_numpy(float); Xc, cc, wc = collapse(X, D.cell.to_numpy()); f = fit(Xc, cc, C=4, wt=wc)
R['neg_with_stars'] = dict(J=f['J'][0].tolist(), did_latent_cells=float(did(f['p'])))
# dependence between the two LLM coders (descriptive; 399 reviews)
V = A.merge(H, on='rid', suffixes=('_A', '_H'))
R['llm_pair_399'] = {o: dict(agree=float(((V[c + '_A'].astype(str) == v) == (V[c + '_H'].astype(str) == v)).mean()))
                     for o, c, v in (('defect', 'defect', '1'), ('neg', 'overall', 'neg'), ('perfpos', 'performance', '1'))}
json.dump(R, open('results_latent.json', 'w'), indent=1, default=float)
for out, o in R['outcomes'].items():
    print(f"\n== {out}: naive FE b={o['naive_fe']['b']:.4f} (p={o['naive_fe']['p']:.3f}; fast check {o['fast_fe_check']:.4f})")
    print('   J by classifier', {k: round(v, 3) for k, v in o['latent']['J'].items()}, ' cell prevalences', np.round(o['latent']['p_cells'], 3))
    print(f"   corrected DiD: cells {o['did_latent_cells']:.4f} CI {np.round(o['boot']['did_latent_ci'], 4)};  FE/J {o['did_corrected_fe']:.4f} CI {np.round(o['boot']['did_corrected_fe_ci'], 4)}")
    for k in ('lr_H_cell_varying', 'lr_pair_dependence'):
        if k in o: print('  ', k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in o[k].items()})
print('\nneg with stars', R['neg_with_stars']); print('LLM pair (399)', R['llm_pair_399'])
