"""ANALYSIS_PLAN_LATENT_VALIDATION.md: latent-class (no gold standard) vs human-label error rates on the 191 Hormuz posts.
Run from misq_note/hf:  python latent/validate_hormuz.py <path to study3/latent.py dir>"""
import sys, json, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, sys.argv[1]); from latent import fit, fit_pair_dependent
rng = np.random.default_rng(20261015); B = 1000
L = pd.read_csv('model_v2_labels_191.csv', dtype={'id': str}).merge(pd.read_csv('human_labels_191_v3.csv', dtype={'id': str})[['id', 'v3', 'hA', 'hB']], on='id')
L = L.merge(pd.read_csv('latent/hormuz_KZ.csv', dtype={'id': str}), on='id')
a = pd.read_csv('raw/truth_archive.csv', dtype={'id': str}); L = L.merge(a, on='id')
L['t'] = pd.to_datetime(L.created_at, utc=True, format='ISO8601'); L = L.sort_values('t').reset_index(drop=True)
L['blk'] = pd.qcut(L.t.rank(method='first'), 4, labels=False).astype(int)
MAP = {'esc': ('ESC', 'MIXED'), 'deesc': ('DEESC', 'MIXED')}
def b(col, o): return L[col].isin(MAP[o]).astype(int).to_numpy()
SETS = {'primary': lambda o: [('M1', b('model1', o)), ('K', L[f'K_{o}'].to_numpy()), ('Z', L[f'Z_{o}'].to_numpy())],
        'all_LLM': lambda o: [('M1', b('model1', o)), ('v2_opus', b('v2_run1', o)), ('v2_haiku', b('v2_run3', o))]}
REFS = {'v3': lambda o: b('v3', o), 'investigator': lambda o: b('final', o)}
cons = (L.hA == L.hB).to_numpy()
def human_rates(X, y, blk, mask=None):
    m = np.ones(len(y), bool) if mask is None else mask
    Se = [(X[m & (y == 1), k] == 1).mean() for k in range(X.shape[1])]; Sp = [(X[m & (y == 0), k] == 0).mean() for k in range(X.shape[1])]
    prev = [y[m & (blk == c)].mean() for c in range(4)]
    return np.array(Se), np.array(Sp), np.array(prev)
R = {'n': int(len(L)), 'block_sizes': L.blk.value_counts().sort_index().tolist()}
for o in MAP:
    for sname, sf in SETS.items():
        cl = sf(o); names = [n for n, _ in cl]; X = np.column_stack([x for _, x in cl]).astype(float); blk = L.blk.to_numpy()
        f = fit(X, blk, C=4); lat = dict(Se=f['Se'][0], Sp=f['Sp'][0], prev=f['p'])
        hum = {r: human_rates(X, rf(o), blk) for r, rf in REFS.items()}
        hum['consensus_only'] = human_rates(X, b('v3', o), blk, cons)
        bs = {'lat_Se': [], 'lat_Sp': [], 'lat_prev': [], 'hum_Se': [], 'hum_Sp': [], 'hum_prev': []}
        for _ in range(B):
            i = rng.integers(0, len(L), len(L))
            try: fb = fit(X[i], blk[i], C=4)
            except Exception: continue
            bs['lat_Se'].append(fb['Se'][0]); bs['lat_Sp'].append(fb['Sp'][0]); bs['lat_prev'].append(fb['p'])
            s_, p_, v_ = human_rates(X[i], b('v3', o)[i], blk[i]); bs['hum_Se'].append(s_); bs['hum_Sp'].append(p_); bs['hum_prev'].append(v_)
        ci = {k: (np.nanpercentile(np.array(v), 2.5, 0).tolist(), np.nanpercentile(np.array(v), 97.5, 0).tolist()) for k, v in bs.items()}
        hv = hum['v3']; inside = bool(ci['lat_Se'][0][0] <= hv[0][0] <= ci['lat_Se'][1][0] and ci['lat_Sp'][0][0] <= hv[1][0] <= ci['lat_Sp'][1][0])
        mad = float(np.mean(np.abs(lat['prev'] - hv[2])))
        o_ = dict(classifiers=names, latent={k: np.asarray(v).tolist() for k, v in lat.items()}, latent_ci=ci,
                  human={r: dict(Se=h[0].tolist(), Sp=h[1].tolist(), prev=h[2].tolist()) for r, h in hum.items()},
                  M1_human_inside_latent_ci=inside, prev_mean_abs_diff=mad, consistent=bool(inside and mad <= 0.05))
        fv = fit(X, blk, C=4, vary_k=0); lr = 2 * (fv['ll'] - f['ll']); o_['lr_M1_block_varying'] = dict(lr=float(lr), df=6, p=float(stats.chi2.sf(max(lr, 0), 6)))
        fd = fit_pair_dependent(X.astype(int), blk, (0, 2)); lr2 = 2 * (fd['ll'] - f['ll']); o_['lr_pair_dependence_first_third'] = dict(lr=float(lr2), df=2, p=float(stats.chi2.sf(max(lr2, 0), 2)))
        R[f'{o}_{sname}'] = o_
json.dump(R, open('latent/results_validation.json', 'w'), indent=1, default=float)
for k, v in R.items():
    if not isinstance(v, dict): continue
    print(f"\n== {k}  classifiers {v['classifiers']}  consistent={v['consistent']}  prev MAD={v['prev_mean_abs_diff']:.3f}")
    for j, n in enumerate(v['classifiers']):
        print(f"  {n:9s} Se latent {v['latent']['Se'][j]:.2f} [{v['latent_ci']['lat_Se'][0][j]:.2f},{v['latent_ci']['lat_Se'][1][j]:.2f}] human {v['human']['v3']['Se'][j]:.2f} (inv {v['human']['investigator']['Se'][j]:.2f})"
              f" | Sp latent {v['latent']['Sp'][j]:.2f} [{v['latent_ci']['lat_Sp'][0][j]:.2f},{v['latent_ci']['lat_Sp'][1][j]:.2f}] human {v['human']['v3']['Sp'][j]:.2f} (inv {v['human']['investigator']['Sp'][j]:.2f})")
    print('  prev latent', np.round(v['latent']['prev'], 2), ' human v3', np.round(v['human']['v3']['prev'], 2), ' LR block', round(v['lr_M1_block_varying']['p'], 3), ' LR dep', round(v['lr_pair_dependence_first_third']['p'], 3))
