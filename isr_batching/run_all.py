"""Fill the batched numbers of Sections 6.2, 6.3, 6.5, 6.7 and Table B5 in one go.

  python run_all.py --M 64 --b 0.10 --profile path/to/AzureLLMInferenceTrace_code_1week.csv --outdir out
Use --M-dedicated 77 to also regenerate the dedicated-server benchmark (b = 0) for the same profile.
"""
import argparse, csv, json, os, itertools
import numpy as np
from quasi_static import analyse, cosine_profile, load_hourly_profile, implied_c0_for_ratio, constrained_ratio_loss

ap = argparse.ArgumentParser()
ap.add_argument('--M', type=int, required=True, help='measured batch cap (KV cache)')
ap.add_argument('--b', type=float, required=True, help='measured beta/alpha')
ap.add_argument('--M-dedicated', type=int, default=77)
ap.add_argument('--profile', default='cosine'); ap.add_argument('--outdir', default='out')
ap.add_argument('--skip-67', action='store_true', help='skip the slow Sec. 6.7 computations')
a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
prof = cosine_profile() if a.profile == 'cosine' else load_hourly_profile(a.profile)
print('hourly profile / mean:', np.round(prof / prof.mean(), 2))

def row(tag, o):
    L2, L3, L4, L6 = (o['levels'][g] for g in (2, 3, 4, 6))
    return dict(case=tag, loss_flat=o['loss_flat'], loss_noprice=o['loss_noprice'], loss_2level=L2['loss'],
                toll_lowest=o['toll_lowest'], toll_lowerQ=o['toll_lower_quartile'], toll_peak=o['toll_peak'],
                slow_share_lowerQ=o['slow_share_lowQ'], slow_share_peak=o['slow_share_peak'], bound_9a=o['bound_cor9a'],
                **{f'rec{g}_exact': o['levels'][g]['recovery_exact'] for g in (2, 3, 4, 6)},
                **{f'rec{g}_quad': o['levels'][g]['recovery_quad'] for g in (2, 3, 4, 6)},
                p_levels2=';'.join(f'{p:.2f}' for p in L2['prices']), peak_hours_2level=len(L2['groups'][-1]))

rows = []
# --- Sec 6.2 / 6.3 / Table 2
for tag, M, b in [('dedicated', a.M_dedicated, 0.0), ('batched', a.M, a.b)]:
    for V, ratio, c0f in [(20, 1.4, 0), (20, 1.4, .15), (10, 1.2, 0), (40, 2.0, 0)]:
        o = analyse(prof, M, b, V, ratio, c0=c0f * V)
        rows.append(row(f'{tag};V={V};r={ratio};c0/V={c0f}', o))
        if (V, ratio, c0f) == (20, 1.4, 0): json.dump(o, open(f'{a.outdir}/{tag}_baseline.json', 'w'), indent=1)
# --- Sec 6.5 robustness grid (V x ratio x c0 x beta/alpha multiples)
for V, ratio, c0f, mult in itertools.product([10, 20, 40], [1.2, 1.4, 2.0], [0, .15], [0, .5, 1, 2]):
    b = a.b * mult
    # keep capacity comparable: for b>0 use measured M
    o = analyse(prof, a.M if b > 0 else a.M_dedicated, b, V, ratio, c0=c0f * V, Gs=(2, 3, 4, 6), ngrid=300)
    rows.append(row(f'grid;V={V};r={ratio};c0/V={c0f};b_mult={mult}', o))
with open(f'{a.outdir}/results.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# --- Table B5-style sweep: toll compression as beta/alpha grows (single engine, M adjusted by hand via --M list)
b5 = []
for b, M in [(0, 10), (.01, 11), (.03, 14), (.06, 22), (.10, 100)]:
    o = analyse(cosine_profile(), M, b, 20, 1.4, Gs=(2,))
    b5.append(dict(b=b, M=M, toll_low=o['toll_lowest'], toll_lowerQ=o['toll_lower_quartile'], toll_peak=o['toll_peak'],
                   slow_share_lowerQ=o['slow_share_lowQ'], flat_loss=o['loss_flat'], rec2=o['levels'][2]['recovery_exact']))
with open(f'{a.outdir}/tableB5_check.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(b5[0])); w.writeheader(); w.writerows(b5)

# --- Sec 6.7: implied serving cost for a 2:1 ratio, and constrained-ratio losses
if not a.skip_67:
    s67 = []
    for tag, M, b in [('dedicated', a.M_dedicated, 0.0), ('batched', a.M, a.b)]:
        for ratio in (1.2, 1.4, 2.0):
            s67.append(dict(case=tag, unpriced_ratio=ratio, implied_c0_over_V=implied_c0_for_ratio(prof, M, b, 20, ratio)))
        for c0f in (0, .2, .4):
            s67.append(dict(case=tag, c0_over_V=c0f, loss_ratio2_constrained=constrained_ratio_loss(prof, M, b, 20, 1.4, c0f * 20),
                            loss_flat=analyse(prof, M, b, 20, 1.4, c0=c0f * 20, Gs=(2,))['loss_flat']))
    json.dump(s67, open(f'{a.outdir}/sec67.json', 'w'), indent=1)
    for r in s67: print(r)
print(open(f'{a.outdir}/results.csv').read()[:3000])
