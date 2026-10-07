"""Paired bootstrap of AUC differences (new minus baseline) on identical documents."""
import numpy as np, runpy, io, contextlib
from sklearn.metrics import roc_auc_score
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ns = runpy.run_path("newmodel.py", run_name="lib")    # reuse data + functions without printing tables
sup = ns["sup"]
def diff(train, test, new, base, B=2000):
    y1, s1 = sup(train, test, new); y2, s2 = sup(train, test, base); assert (y1 == y2).all()
    r = np.random.RandomState(7); d = []
    for _ in range(B):
        i = r.randint(0, len(y1), len(y1))
        if y1[i].min() != y1[i].max(): d.append(roc_auc_score(y1[i], s1[i]) - roc_auc_score(y1[i], s2[i]))
    d = np.array(d); return roc_auc_score(y1, s1) - roc_auc_score(y1, s2), np.percentile(d, [2.5, 97.5]), (d <= 0).mean()
pairs = [("NEW: rates+(a,b)", "baseline: rates+disp500"), ("NEW: (a,b) only", "baseline: disp500 only")]
print(f"{'comparison':54s}{'train->test':16s}{'dAUC':>8s}  95% CI            P(d<=0)")
for new, base in pairs:
    for tr, te in [("gpt4o", "gpt4o"), ("claude", "claude"), ("gpt4o", "claude"), ("claude", "gpt4o")]:
        d, (lo, hi), p = diff(tr, te, new, base)
        print(f"{new+' - '+base:54s}{tr+'->'+te:16s}{d:+8.3f}  [{lo:+.3f},{hi:+.3f}]  {p:.3f}")
