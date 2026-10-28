"""Write reproduced Tables 4-5 next to the values in the manuscript. Usage: python make_tables.py summary.json out.md"""
import json, sys
S = json.load(open(sys.argv[1])); T = S['table4']
ms = {  # manuscript values (b, se); None = not reported
 'preferred_2019': (0.024, 0.014), 'preferred_2020': (0.008, 0.013), 'preferred_2021': (0.011, None),
 'preferred_2023': (-0.016, 0.006), 'preferred_2024': (-0.012, 0.017),
 'no_lm_2019': (0.008, 0.013), 'no_lm_2020': (-0.002, 0.013), 'no_lm_2023': (-0.037, None), 'no_lm_2024': (-0.059, None)}
def f(b, se=None):
    s = f'{b:+.3f}'.replace('-', '−'); return s + (f' ({se:.3f})' if se is not None else '')
L = ['# Reproduced Tables 4–5 (public data; approximate)', '',
 f"Cells: {S['n_cells']}, occupations: {S['n_occ']}, countries: {S['n_countries']} (manuscript: 604 / 96 / 16).",
 f"Correlation of visual and text exposure across occupations: {S['corr_vis_txt']:.2f} (manuscript: 0.27).",
 f"Maximum standardized visual exposure k: ISCO 216 = {S['z_216']:.2f} (manuscript 5.7); ISCO 265 = {S['z_265']:.2f} (manuscript 6.2).", '',
 '## Table 4. Change in log adverts per SD of visual exposure, relative to 2022', '',
 '| Specification | Year | Reproduced b (SE) | Manuscript b (SE) | Randomization p | MDE (2.8 SE) |', '|:--|:--|--:|--:|--:|--:|']
for spec, lab in (('preferred', 'Country FE + text control'), ('no_lm', 'Country FE, no text control')):
    for y in (2019, 2020, 2021, 2023, 2024):
        r = T[f'{spec}_{y}']; m = ms.get(f'{spec}_{y}')
        L.append(f"| {lab} | {y} | {f(r['b'], r['se'])} | {f(*m) if m else 'n.r.'} | {r['p_rand']:.3f} | {r['mde']:.3f} |")
for key, lab in (('trend_4pt', 'trend fitted on 2019–2022 (2022 = 0)'), ('trend_3pt', 'trend fitted on 2019–2021')):
    t = S[key]
    L += ['', f"Linear pre-trend, {lab}: slope {t['slope']:+.4f} (SE {t['slope_se']:.4f}); manuscript −0.0072 (0.0047). "
          f"Deviation of 2023: {t['2023'][0]:+.3f} (SE {t['2023'][1]:.3f}); 2024: {t['2024'][0]:+.3f} (SE {t['2024'][1]:.3f}); manuscript −0.009 (0.007) and +0.002 (0.023)."]
k = S['z_216']
L += ['', f'## Table 5. Implied coefficients under complete assimilation (k = {k:.2f}, ISCO 216)', '',
      '### Panel A', '', '| Acquisition rate A^u | β = −0.19 | β = −0.50 | log change, most exposed (β = −0.50) |', '|:--|--:|--:|--:|']
for lab, A in (('9.6% (EU, all firms)', .0955), ('36.2% (publishing, film, broadcasting)', .3618), ('2.1% (text generation 2023)', .021)):
    L.append(f'| {lab} | {-A*.19/k:+.3f} | {-A*.5/k:+.3f} | {-A*.5:+.3f} |'.replace('-', '−'))
L += ['', '### Panel B', '', '| Year | Observed, preferred (SE) | Observed, no text control | MDE | MDE × k | Observed × k (preferred) |', '|:--|--:|--:|--:|--:|--:|']
for y in (2023, 2024):
    r = T[f'preferred_{y}']; n = T[f'no_lm_{y}']
    L.append(f"| {y} | {f(r['b'], r['se'])} | {f(n['b'])} | {r['mde']:.3f} | {r['mde']*k:.2f} | {f(r['b']*k)} |")
open(sys.argv[2], 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
