"""Pilot analysis of agent-side tool errors in SWE-agent trajectories.
 (1) clustering: P(error | previous error) vs P(error | previous success), against a within-trajectory permutation null
     that keeps every trajectory's error count (pure heterogeneity);
 (2) contagion with trajectory fixed effects: conditional logit of error_t on the decayed sum of past errors;
 (3) discrete-time Hawkes fit per model and branching ratio;
 (4) early warning: predicting final failure from the first k steps (error count vs excitation);
 (5) escalation rules: hand off when excitation exceeds c vs when errors reach m.
python3 -I pilot_analysis.py events.parquet out.json"""
import sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, GroupKFold
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(0)
df = pd.read_parquet(sys.argv[1]); df = df[df.n_steps >= 6].reset_index(drop=True)
E = [np.array(e, int) for e in df.errors]; out = {"n_traj": len(df), "models": df.model.value_counts().to_dict()}
# (1) clustering vs permutation
def trans(seqs):
    a = b = c = d_ = 0
    for e in seqs:
        p, q = e[:-1], e[1:]; a += (q & p).sum(); b += p.sum(); c += (q & (1 - p)).sum(); d_ += (1 - p).sum()
    return a / b, c / d_
p11, p01 = trans(E); perm = []
for _ in range(200):
    pe = [rng.permutation(e) for e in E]; x, y = trans(pe); perm.append(x - y)
out["clustering"] = dict(p_err_after_err=round(p11, 3), p_err_after_ok=round(p01, 3), diff=round(p11 - p01, 3),
                         perm_null_mean=round(float(np.mean(perm)), 3), perm_null_95=round(float(np.percentile(perm, 95)), 3))
# (2) fixed-effects (within-trajectory) linear probability and conditional logit on decayed past errors
def excite(e, delta):
    s = np.zeros(len(e)); acc = 0.0
    for t in range(len(e)): s[t] = acc; acc = acc * delta + e[t]
    return s
from statsmodels.discrete.conditional_models import ConditionalLogit
res = {}
sub = rng.choice(len(df), size=min(4000, len(df)), replace=False)
for delta in (0.3, 0.6, 0.8):
    y, X, g = [], [], []
    for i in sub:
        e = E[i]; s = excite(e, delta); t = np.arange(len(e))
        y += list(e[1:]); X += [[s[k], np.log1p(t[k])] for k in range(1, len(e))]; g += [i] * (len(e) - 1)
    y, X, g = np.array(y), np.array(X), np.array(g)
    keep = pd.Series(y).groupby(g).transform(lambda v: 0 < v.sum() < len(v)).values
    m = ConditionalLogit(y[keep], X[keep], groups=g[keep]).fit(disp=0)
    res[delta] = dict(beta_excitation=round(float(m.params[0]), 3), se=round(float(m.bse[0]), 3), beta_logstep=round(float(m.params[1]), 3), llf=round(float(m.llf), 1))
out["fixed_effects_logit"] = res
# placebo: same model on permuted sequences (heterogeneity only)
delta = 0.6; pb = []
for rep in range(5):
    y, X, g = [], [], []
    for i in sub[:2000]:
        e = rng.permutation(E[i]); s = excite(e, delta); t = np.arange(len(e))
        y += list(e[1:]); X += [[s[k], np.log1p(t[k])] for k in range(1, len(e))]; g += [i] * (len(e) - 1)
    y, X, g = np.array(y), np.array(X), np.array(g)
    keep = pd.Series(y).groupby(g).transform(lambda v: 0 < v.sum() < len(v)).values
    pb.append(float(ConditionalLogit(y[keep], X[keep], groups=g[keep]).fit(disp=0).params[0]))
out["fixed_effects_placebo_beta_mean"] = round(float(np.mean(pb)), 3)
# (3) discrete-time Hawkes per model: P(e_t=1) = 1 - exp(-(mu + alpha * S_t)), S_t with decay delta; n = alpha / (1 - delta)
def hawkes_fit(seqs):
    def nll(th):
        mu, al, de = np.exp(th[0]), np.exp(th[1]), 1 / (1 + np.exp(-th[2])); tot = 0.0
        for e in seqs:
            s = excite(e, de); lam = mu + al * s; p = np.clip(1 - np.exp(-lam), 1e-9, 1 - 1e-9)
            tot -= (e * np.log(p) + (1 - e) * np.log(1 - p)).sum()
        return tot
    r = minimize(nll, [np.log(0.1), np.log(0.2), 0.0], method="Nelder-Mead", options=dict(maxiter=600))
    mu, al, de = np.exp(r.x[0]), np.exp(r.x[1]), 1 / (1 + np.exp(-r.x[2]))
    def nll0(th):
        mu = np.exp(th[0]); return -sum((e * np.log(1 - np.exp(-mu)) + (1 - e) * (-mu)).sum() for e in seqs)
    r0 = minimize(nll0, [np.log(0.2)], method="Nelder-Mead")
    return dict(mu=round(mu, 3), alpha=round(al, 3), delta=round(de, 3), branching=round(al / (1 - de), 3), LR_vs_poisson=round(2 * (r0.fun - r.fun), 1), n=len(seqs))
hk = {}
for mdl, grp in df.groupby("model"):
    idx = grp.index.values; idx = rng.choice(idx, size=min(3000, len(idx)), replace=False)
    hk[mdl] = hawkes_fit([E[i] for i in idx])
out["hawkes"] = hk
# (4) early warning
K = 8; rows = []
for i, e in enumerate(E):
    if len(e) <= K: continue
    rows.append(dict(i=i, inst=df.instance_id[i], resolved=int(df.resolved[i]), cnt=e[:K].sum(), exc=excite(np.r_[e[:K], 0], 0.6)[-1], last=e[K - 1]))
W = pd.DataFrame(rows); y = 1 - W.resolved.values; gk = GroupKFold(5)
auc = {}
for name, cols in (("error_count", ["cnt"]), ("excitation", ["exc"]), ("both", ["cnt", "exc"])):
    p = cross_val_predict(LogisticRegression(max_iter=1000), W[cols].values, y, cv=gk, groups=W.inst.values, method="predict_proba")[:, 1]
    auc[name] = round(roc_auc_score(y, p), 3)
out["early_warning_auc_first8_steps"] = auc; out["failure_rate"] = round(float(y.mean()), 3)
# (5) escalation rules: frontier of (share of failures caught, share of successes handed off)
def rule_curve(score_fn, thresholds):
    pts = []
    for c in thresholds:
        caught = fp = 0
        for i, e in enumerate(E):
            hit = any(score_fn(e, t) >= c for t in range(len(e)))
            if df.resolved[i]: fp += hit
            else: caught += hit
        nf = (~df.resolved).sum(); ns = df.resolved.sum(); pts.append((round(caught / nf, 3), round(fp / ns, 3)))
    return pts
cnt_fn = lambda e, t: e[:t + 1].sum()
exc_fn = lambda e, t: excite(np.r_[e[:t + 1], 0], 0.6)[-1]
out["escalation_count_rule"] = dict(zip([str(m) for m in (2, 3, 4, 5, 6, 8)], rule_curve(cnt_fn, (2, 3, 4, 5, 6, 8))))
out["escalation_excitation_rule"] = dict(zip([str(c) for c in (1.0, 1.5, 2.0, 2.5, 3.0)], rule_curve(exc_fn, (1.0, 1.5, 2.0, 2.5, 3.0))))
json.dump(out, open(sys.argv[2], "w"), indent=1); print(json.dumps(out, indent=1))
