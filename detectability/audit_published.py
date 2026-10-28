"""Audit published estimates against the detectability bound. Usage: python audit_published.py examples/published_estimates.csv OUT_PREFIX
Exposure-gradient designs: per-SD estimate and SE -> MDE = 2.8 SE; minimum per-assimilator effect |beta_min| = MDE / (A * sigma_s) (R = 1, complete assimilation)
for adoption shares A in {0.05, 0.10, 0.40} and sigma_s in {0.19 (the manuscript's favourable case, k = 5.3), 0.10}; compared with the platform effect |beta| = 0.19.
Adoption-observed designs: the coefficient is already an effect of adoption or of firm-level AI use, so only the MDE is reported and compared with 0.19."""
import sys, csv, json
from statistics import NormalDist
PLATFORM = 0.19; CRIT = NormalDist().inv_cdf(0.975) + NormalDist().inv_cdf(0.80)
rows = list(csv.DictReader(open(sys.argv[1]))); out = []
for r in rows:
    est, se, div = float(r['estimate']) / float(r['per_sd_divisor']), float(r['se']) / float(r['per_sd_divisor']), float(r['per_sd_divisor'])
    mde = CRIT * se; d = {'id': r['id'], 'study': r['study'], 'design': r['design'], 'evidence': r['evidence'], 'estimate': round(est, 4), 'se': round(se, 4), 'mde': round(mde, 4), 'estimate_over_se': round(est / se, 2) if se else None}
    if r['design'] == 'exposure_gradient':
        for A in (0.05, 0.10, 0.40):
            for s in (0.19, 0.10):
                b = mde / (A * s); d[f'beta_min_A{A}_s{s}'] = round(b, 2)
                d[f'detects_platform_A{A}_s{s}'] = b <= PLATFORM
        d['gamma_star_platform_A0.40_s0.19'] = round(-0.40 * PLATFORM * 0.19, 4)
    else:
        d['mde_vs_platform_0.19'] = f'MDE {mde:.3f} <= 0.19: {mde <= PLATFORM}'
    out.append(d)
keys = sorted({k for d in out for k in d}, key=lambda k: (k not in ('id', 'study', 'design', 'evidence'), k))
with open(sys.argv[2] + '.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(out)
json.dump(out, open(sys.argv[2] + '.json', 'w'), indent=1)
for d in out: print({k: d.get(k) for k in ('id', 'design', 'estimate', 'se', 'mde', 'beta_min_A0.4_s0.19', 'beta_min_A0.1_s0.19', 'detects_platform_A0.4_s0.19', 'mde_vs_platform_0.19') if k in d})
