"""Audit published or own exposure estimates against the detectability bound.
Usage: python audit.py INPUT.csv [OUTPUT.csv]
Columns: study, outcome, estimate, se, A, beta, k (or sigma_s), [R], [g], [gamma_max]
For every row it reports gamma* (coefficient implied by assimilation share g*A with effect beta), the MDE (2.8 SE), whether gamma* is detectable,
the adoption share needed for detection, and the classification of the estimate (rules i-iii)."""
import sys, csv
from detectability import detectability, classify
rows = list(csv.DictReader(open(sys.argv[1])))
out = []
for r in rows:
    f = lambda k, d=None: float(r[k]) if r.get(k) not in (None, '') else d
    d = detectability(f('A'), f('beta'), f('se'), sigma_s=f('sigma_s'), k=f('k'), R=f('R', 1.0), g=f('g', 1.0))
    cls = classify(f('estimate'), f('se'), d['gamma_star'], gamma_max=f('gamma_max'))
    out.append({**{k: r[k] for k in ('study', 'outcome', 'estimate', 'se')}, 'gamma_star': round(d['gamma_star'], 4), 'mde': round(d['mde'], 4),
                'detectable': d['detectable'], 'required_adoption': None if d['required_adoption'] is None else round(d['required_adoption'], 3), 'classification': cls})
w = csv.DictWriter(open(sys.argv[2], 'w', newline='') if len(sys.argv) > 2 else sys.stdout, fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
