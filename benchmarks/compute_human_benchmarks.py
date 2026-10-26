"""Human benchmark effects from the public Twin-2K-500 mega-study (Peng et al.), HF dataset
LLM-Digital-Twin/Twin-2K-500-Mega-Study (apache-2.0). Usage:
  python3 compute_human_benchmarks.py <dir containing the three *-00000-of-00001.parquet files>
Conditions are coded from the displayed survey text, not from the EmbeddedData 'target' tag,
which is inverted relative to the text shown in targeting_fairness."""
import sys, json, re
import numpy as np, pandas as pd
from scipy import stats

D = sys.argv[1]

def questions(o, out):
    if isinstance(o, dict):
        if 'QuestionID' in o: out.append(o); return
        for v in o.values(): questions(v, out)
    elif isinstance(o, list):
        for v in o: questions(v, out)

def load(name):
    d = pd.read_parquet(f'{D}/{name}-00000-of-00001.parquet'); rows = []
    for _, r in d.iterrows():
        out = []; questions(json.loads(r['survey_json_with_human_response'])['Elements'], out)
        for q in out:
            a = q.get('Answers')
            if q.get('is_descriptive') or not isinstance(a, dict): continue
            rows.append(dict(PID=r['PID'], qname=q.get('QuestionName'), sel=a.get('SelectedText'), text=r['survey_text']))
    return pd.DataFrame(rows)

def prop_effect(p1, n1, p0, n0):
    diff = p1 - p0; se = np.sqrt(p1*(1-p1)/n1 + p0*(1-p0)/n0)
    lor = np.log(p1/(1-p1)) - np.log(p0/(1-p0))
    se_l = np.sqrt(1/(n1*p1*(1-p1)) + 1/(n0*p0*(1-p0)))
    return diff, se, lor, se_l, 2*(1-stats.norm.cdf(abs(diff/se)))

def report(label, diff, se, lor, se_l, p):
    print(f'{label}: diff={diff:.3f} [{diff-1.96*se:.3f},{diff+1.96*se:.3f}] logOR={lor:.2f} '
          f'[{lor-1.96*se_l:.2f},{lor+1.96*se_l:.2f}] d~{lor*np.sqrt(3)/np.pi:.2f} p={p:.3g}')

# Defaults: share of donors / green-energy customers, opt-out vs opt-in
f = load('default_eric')
for lab, out_q, in_q, out_pos, in_pos in [('Organ donation', 'OPTOUT_Organ', 'OPTIN_Organ', 1, 2),
                                          ('Green energy', 'OPTOUT_Green', 'OPTIN_Green', 1, 2)]:
    # position 1 of opt-out = keep default (donor/green); position 2 of opt-in = change to donor/green
    o = f[f.qname == out_q]; i = f[f.qname == in_q]
    po = (o.sel.str.startswith(('You are therefore currently a potential donor', 'Stay with GreenGrid'))).mean()
    pi = (i.sel.str.startswith(('If you wish to change', 'Switch to GreenGrid'))).mean()
    print(f'{lab}: opt-out {po:.3f} (n={len(o)}), opt-in {pi:.3f} (n={len(i)})')
    report(lab, *prop_effect(po, len(o), pi, len(i)))

# Attraction effect: share of target among choosers of the two focal options, with vs without decoy
c = load('context_effects')
S = {'TV': ('HD-558', 'Hal-B', 'Bin.TV_TC'), 'Printer': ('1000AX', 'L22', 'Bin.Printer_TC'), 'Cell': ('X-3A', '5C-S', 'Bin.Cell_TC')}
ests = []
for k, (tgt, decoy, bq) in S.items():
    b = c[c.qname == bq]; a = c[(c.qname == 'Attr_' + k) & (c.sel != decoy)]
    r = prop_effect((a.sel == tgt).mean(), len(a), (b.sel == tgt).mean(), len(b)); ests.append(r[2:4])
    report('Attraction ' + k, *r)
w = np.array([1/s**2 for _, s in ests]); m = np.array([l for l, _ in ests])
pl = (w*m).sum()/w.sum(); sp = np.sqrt(1/w.sum())
print(f'Attraction pooled logOR={pl:.2f} [{pl-1.96*sp:.2f},{pl+1.96*sp:.2f}] d~{pl*np.sqrt(3)/np.pi:.2f}')

# Targeting fairness: rating of broad vs demographically targeted ad
t = load('targeting_fairness'); t = t[t.qname == 'fair1'].copy()
t['targeted'] = t.text.str.contains('advertise the snacks to women directly')
t['y'] = t.sel.str.extract(r'^(\d)')[0].astype(float)
a, b = t[t.targeted].y, t[~t.targeted].y
sd = np.sqrt(((len(a)-1)*a.var() + (len(b)-1)*b.var())/(len(a)+len(b)-2))
print(f'Fairness: targeted {a.mean():.2f} (n={len(a)}) vs broad {b.mean():.2f} (n={len(b)}), d={(a.mean()-b.mean())/sd:.2f}, p={stats.ttest_ind(a,b).pvalue:.2g}')
