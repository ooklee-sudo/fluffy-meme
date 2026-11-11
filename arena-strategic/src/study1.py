"""Study 1: identity-leak LPM with fixed effects (pair-ordered, prompt cluster, language), SE clustered by pair."""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
D = '/home/user/data'
P = pd.read_pickle(f'{D}/study1_panel.pkl')
scr = sys.argv[1] if len(sys.argv) > 1 else None
if scr:  # replace regex leak flag by LLM-confirmed, non-induced self-disclosure
    s = pd.read_pickle(f'{D}/screen.pkl')
    ok = s[(s.self_disclosure == True)]
    good = set(zip(ok[ok.user_induced == False].id, ok[ok.user_induced == False].side))
    ind = set(zip(ok[ok.user_induced == True].id, ok[ok.user_induced == True].side))
    key = list(zip(P.cid, P.side)); okey = list(zip(P.cid, P.side.map({'a': 'b', 'b': 'a'})))
    P['induced'] = [k in ind for k in key]; P['opp_induced'] = [k in ind for k in okey]
    P['leak'] = [int(k in good) for k in key]; P['opp_leak'] = [int(k in good) for k in okey]
    P['ask'] = (P.ask.astype(bool) | P.induced | P.opp_induced).astype(int)
# main sample: neither model leaks except possibly the focal one; no user-induced identity talk; no false claims
S = P[(P.opp_leak == 0) & (P.ask == 0) & (P.other_claim == 0) & (P.opp_other_claim == 0)].dropna(subset=['tok_diff']).copy()
# keep only ordered pairs with at least one leak (identifying variation) to keep FE small
S = S[S.groupby('opair').leak.transform('max') == 1]
print('rows', len(S), 'leaked', S.leak.sum(), 'pairs', S.opair.nunique())
ctrl = 'tok_diff + hdr_diff + lst_diff + bold_diff + ref + opp_ref + C(np.minimum(turns,4))'
fe = 'C(opair) + C(cl50) + C(lang)'
def fit(f, data, y='win'):
    m = smf.ols(f'{y} ~ {f}', data).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(data.pair)[0]})
    return m
res = {}
for name, f in [('no controls', f'leak + {fe}'), ('+ rule controls', f'leak + {ctrl} + {fe}'),
                ('+ short-prompt FE, cl100', f'leak + {ctrl} + short_prompt + C(opair) + C(cl100) + C(lang)')]:
    m = fit(f, S); res[name] = (m.params['leak'], m.bse['leak'], m.pvalues['leak'])
    print(f'{name:28s} beta={m.params["leak"]:+.4f} se={m.bse["leak"]:.4f} p={m.pvalues["leak"]:.3g}')
for y in ['lose', 'tie', 'bothbad']:
    m = fit(f'leak + {ctrl} + {fe}', S, y); print(f'   outcome {y:8s} beta={m.params["leak"]:+.4f} se={m.bse["leak"]:.4f}')
# H1a: top-3 developer; H1b: repeat voters within session (140k has session ids only)
S['repeat'] = (S.prior_votes > 0).astype(int)
for v in ['top3', 'repeat']:
    m = fit(f'leak + leak:{v} + {v} + {ctrl} + {fe}', S)
    print(f'H1 x {v:6s} leak={m.params["leak"]:+.4f} ({m.bse["leak"]:.4f})  interaction={m.params[f"leak:{v}"]:+.4f} ({m.bse[f"leak:{v}"]:.4f}) p={m.pvalues[f"leak:{v}"]:.3g}')
# by developer of leaking model
for dv in ['xai', 'anthropic', 'google', 'openai', 'alibaba']:
    sub = S[S.dev == dv]
    if sub.leak.sum() >= 20:
        m = fit(f'leak + {ctrl} + C(opair) + C(cl20) + C(lang)', sub); print(f'  dev={dv:10s} n_leak={sub.leak.sum():4d} beta={m.params["leak"]:+.4f} ({m.bse["leak"]:.4f})')
S.to_pickle(f'{D}/study1_sample{"_scr" if scr else ""}.pkl')
