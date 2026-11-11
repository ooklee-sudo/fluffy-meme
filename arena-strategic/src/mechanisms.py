"""Disclosure-penalty mechanism tests on the full 140k panel (rule-based controls)."""
import sys, re, numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, 'src'); from leaks import RX_ANY, RX
D = '/home/user/data'
P = pd.read_pickle(f'{D}/study1_panel.pkl')
s = pd.read_pickle(f'{D}/screen.pkl')
conv = pd.read_pickle(f'{D}/140k.pkl').set_index('id')
lab = {}
for _, r in s.iterrows():
    if r.self_disclosure is True: lab[(r.id, r.side)] = 'prompted' if r.user_induced else 'unprompted'
    elif r.self_disclosure is False: lab[(r.id, r.side)] = 'thirdparty'
GEN = re.compile(r"\b(?:as an ai\b|i(?:'m| am) (?:just )?an ai\b|as a (?:large )?language model|i(?:'m| am) a (?:large )?language model|i(?:'m| am) an artificial intelligence)", re.I)
def generic(turns):
    for t in turns:
        if t and GEN.search(t) and not RX.search(t): return 1
    return 0
ga = {i: generic(c.a_turns) for i, c in conv.iterrows()}
gb = {i: generic(c.b_turns) for i, c in conv.iterrows()}
# position of the disclosure: opens the first reply (first 150 chars) vs elsewhere
def opens(turns):
    t = turns[0] if turns else ''
    m = RX.search(t or ''); return int(bool(m) and m.start() < 150)
oa = {i: opens(c.a_turns) for i, c in conv.iterrows()}; ob = {i: opens(c.b_turns) for i, c in conv.iterrows()}
other = {'a': 'b', 'b': 'a'}
P['grp'] = [lab.get((c, sd), 'none') for c, sd in zip(P.cid, P.side)]
P['opp_grp'] = [lab.get((c, other[sd]), 'none') for c, sd in zip(P.cid, P.side)]
P['generic'] = [(ga if sd == 'a' else gb)[c] for c, sd in zip(P.cid, P.side)]
P['opp_generic'] = [(gb if sd == 'a' else ga)[c] for c, sd in zip(P.cid, P.side)]
P['opens'] = [(oa if sd == 'a' else ob)[c] for c, sd in zip(P.cid, P.side)]
P.loc[(P.grp == 'none') & (P.generic == 1), 'grp'] = 'generic'
P.loc[(P.opp_grp == 'none') & (P.opp_generic == 1), 'opp_grp'] = 'generic'
# sample: opponent clean; each focal row in exactly one group
S = P[(P.opp_grp == 'none') & (P.other_claim == 0) & (P.opp_other_claim == 0)].dropna(subset=['tok_diff']).copy()
S = S[S.groupby('opair').grp.transform(lambda g: (g != 'none').any())]
print(len(S), S.grp.value_counts().to_dict())
ctrl = 'tok_diff + hdr_diff + lst_diff + bold_diff + ref + opp_ref + C(np.minimum(turns,4)) + short_prompt'
fe = 'C(opair) + C(cl50) + C(lang)'
for g in ['unprompted', 'prompted', 'generic', 'thirdparty']: S[g] = (S.grp == g).astype(int)
fit = lambda y, rhs, d: smf.ols(f'{y} ~ {rhs}', d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.pair)[0]})
rhs = f'unprompted + prompted + generic + thirdparty + {ctrl} + {fe}'
print('\nEffect on outcome relative to no-mention conversations (pp, cluster SE):')
for y in ['win', 'lose', 'tie', 'bothbad']:
    m = fit(y, rhs, S)
    print(f'  {y:8s}', '  '.join(f'{g}={100*m.params[g]:+.1f}({100*m.bse[g]:.1f})' for g in ['unprompted', 'prompted', 'generic', 'thirdparty']))
m = fit('lose', rhs, S); print('  test unprompted = prompted (lose): p=%.3g' % m.f_test('unprompted = prompted').pvalue, '| unprompted = generic: p=%.3g' % m.f_test('unprompted = generic').pvalue)
# net score: win - lose
S['net'] = S.win - S.lose
m = fit('net', rhs, S); print('  net (win-lose):', '  '.join(f'{g}={100*m.params[g]:+.1f}({100*m.bse[g]:.1f})' for g in ['unprompted', 'prompted', 'generic', 'thirdparty']))
# heterogeneity within unprompted
U = S[S.grp.isin(['none', 'unprompted'])].copy()
U['up_open'] = U.unprompted * U.opens; U['up_buried'] = U.unprompted * (1 - U.opens)
m = fit('net', f'up_open + up_buried + {ctrl} + {fe}', U); print('  unprompted, opens reply: %+.1f (%.1f)   buried later: %+.1f (%.1f)' % (100*m.params.up_open, 100*m.bse.up_open, 100*m.params.up_buried, 100*m.bse.up_buried))
U['up_short'] = U.unprompted * U.short_prompt; U['up_subst'] = U.unprompted * (1 - U.short_prompt)
m = fit('net', f'up_short + up_subst + {ctrl} + {fe}', U); print('  unprompted, greeting prompt: %+.1f (%.1f)   substantive prompt: %+.1f (%.1f)' % (100*m.params.up_short, 100*m.bse.up_short, 100*m.params.up_subst, 100*m.bse.up_subst))
for dv in ['xai', 'anthropic', 'google']:
    U[f'up_{dv}'] = U.unprompted * (U.dev == dv)
rest = U.unprompted * (~U.dev.isin(['xai', 'anthropic', 'google'])); U['up_rest'] = rest
m = fit('net', f'up_xai + up_anthropic + up_google + up_rest + {ctrl} + {fe}', U)
print('  by developer (net):', '  '.join(f'{d}={100*m.params["up_"+d]:+.1f}({100*m.bse["up_"+d]:.1f}) n={int(U["up_"+d].sum())}' for d in ['xai', 'anthropic', 'google', 'rest']))
