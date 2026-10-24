"""Sensitivity analysis for misclassified product-level labels (experience, hedonic) by maximum likelihood (EM).

The LLM label L is an error-prone measure of the human-consensus label T. Given sensitivity Se = P(L=1|T=1),
specificity Sp = P(L=0|T=0) and prevalence pi = P(T=1) (Rogan-Gladen from the observed LLM share), the observed-data
likelihood is  prod_p  sum_T  P(L_p|T) P(T) prod_{i in p} P(y_i | T, x_i; theta).  The EM algorithm alternates
(E) posterior P(T_p=1 | L_p, y, x; theta), which uses the OUTCOME as well as the label, and (M) a weighted fit of the
outcome model on the stacked data (each review twice, T=1 and T=0, with posterior weights).
Using only predictive values P(T|L) to impute T ignores the outcome and would attenuate effects again, so it is not used.
Se and Sp are drawn from Beta posteriors of the validation counts, so the spread of corrected estimates across draws
reflects uncertainty about the error rates ONLY; sampling variance of the corrected estimates is not recomputed
(compare with the observed confidence interval). Assumptions: non-differential misclassification, error rates equal
across categories, validation sample (n=100) representative.

Usage: python misclass_sensitivity.py --data prod_ours_claude/replication_data.csv --validation validation/product_label_validation_P101-P200.csv --draws 80
"""
import argparse
import multiprocessing as mp

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.special import expit
from scipy.stats import nbinom, norm

import models

D = None
F_NB = "count ~ gap * T + np.log(len_chars) + C(star_f) + has_image"
F_OLS = "gap ~ T + C(star_f) + len_chars + age"


def init(path):
    global D
    D = pd.read_csv(path)
    D["pid"] = pd.factorize(D.parent_asin)[0]


def counts(v, human, llm, pos):
    return (int(((v[llm] == pos) & (v[human] == pos)).sum()), int(((v[llm] != pos) & (v[human] == pos)).sum()),
            int(((v[llm] != pos) & (v[human] != pos)).sum()), int(((v[llm] == pos) & (v[human] != pos)).sum()))


def prior_lik(L, se, sp, pi):
    """log P(T=1,L) and log P(T=0,L) per product."""
    return (np.log(pi) + np.where(L == 1, np.log(se), np.log(1 - se)),
            np.log(1 - pi) + np.where(L == 1, np.log(1 - sp), np.log(sp)))


def stacked_fit(d, w1, formula, family, offset=None):
    s = pd.concat([d.assign(T=1), d.assign(T=0)], ignore_index=True)
    w = np.concatenate([w1, 1 - w1])
    kw = dict(offset=np.log(s.exposure)) if offset else {}
    return smf.glm(formula, data=s, family=family, freq_weights=w, **kw).fit()


def em(d, L_prod, pid, se, sp, pi, formula, kind, alpha=None, iters=12, tol=1e-4):
    """Returns the fitted stacked model after EM. d has one row per review; L_prod indexed by pid (0..P-1)."""
    n_p = pid.max() + 1
    lp1, lp0 = prior_lik(L_prod, se, sp, pi)
    w_rev = np.where(L_prod[pid] == 1, 0.95, 0.05)  # start close to the observed label
    fam = sm.families.NegativeBinomial(alpha=alpha) if kind == "nb" else sm.families.Gaussian()
    old = None
    for _ in range(iters):
        res = stacked_fit(d, w_rev, formula, fam, offset=(kind == "nb"))
        d1, d0 = d.assign(T=1), d.assign(T=0)
        if kind == "nb":
            mu1 = res.predict(d1, offset=np.log(d.exposure)); mu0 = res.predict(d0, offset=np.log(d.exposure))
            y = d["count"].values; r = 1 / alpha
            ll1 = nbinom.logpmf(y, r, r / (r + mu1)); ll0 = nbinom.logpmf(y, r, r / (r + mu0))
        else:
            mu1, mu0 = res.predict(d1), res.predict(d0); sd = np.sqrt(res.scale)
            y = d["gap"].values; ll1 = norm.logpdf(y, mu1, sd); ll0 = norm.logpdf(y, mu0, sd)
        s1 = np.bincount(pid, ll1, n_p) + lp1; s0 = np.bincount(pid, ll0, n_p) + lp0
        w_prod = expit(s1 - s0); w_rev = w_prod[pid]
        cur = res.params.values
        if old is not None and np.max(np.abs(cur - old)) < tol:
            break
        old = cur
    return res


def rc_values(L, se, sp, q):
    """Regression calibration: E[T|L] from sensitivity, specificity and the observed LLM share q (Rogan-Gladen prevalence)."""
    pi = float(np.clip((q + sp - 1) / (se + sp - 1), 1e-4, 1 - 1e-4))
    ppv = min(1.0, se * pi / q); npv = min(1.0, sp * (1 - pi) / (1 - q))
    return np.where(L == 1, ppv, 1 - npv), pi


def one_draw_rc(args):
    """Regression-calibration estimates for one draw of (Se, Sp). Valid for linear models under non-differential
    misclassification; approximate for the log-linear NB2 model."""
    seed, alpha, cnt_e, cnt_h, q_e, q_h = args
    rng = np.random.default_rng(seed)
    prods = D.drop_duplicates("pid").sort_values("pid")
    out = {}
    for tag, cnt, q, col in (("e", cnt_e, q_e, "experience"), ("h", cnt_h, q_h, "hedonic")):
        tp, fn, tn, fp = cnt
        se, sp = rng.beta(tp + 1, fn + 1), rng.beta(tn + 1, fp + 1)
        if se + sp <= 1.0:
            return None
        ev, pi = rc_values(prods[col].values.astype(int), se, sp, q)
        d = D.assign(T=ev[D.pid.values])
        groups = d.pid.values
        if tag == "e":
            f = smf.glm(F_NB, data=d, family=sm.families.NegativeBinomial(alpha=alpha), offset=np.log(d.exposure)).fit(cov_type="cluster", cov_kwds={"groups": groups})
            c = f.cov_params(); b = f.params
            out.update(gap=b["gap"], gap_se=f.bse["gap"], inter=b["gap:T"], inter_se=f.bse["gap:T"],
                       net=b["gap"] + b["gap:T"], net_se=float(np.sqrt(c.loc["gap", "gap"] + c.loc["gap:T", "gap:T"] + 2 * c.loc["gap", "gap:T"])))
        else:
            o = smf.ols(F_OLS, data=d).fit(cov_type="cluster", cov_kwds={"groups": groups})
            out.update(hed=o.params["T"], hed_se=o.bse["T"])
    return out


def one_draw(args):
    seed, alpha, cnt_e, cnt_h, q_e, q_h = args
    rng = np.random.default_rng(seed)
    P = D.pid.max() + 1
    prods = D.drop_duplicates("pid").sort_values("pid")
    out = {}
    for tag, cnt, q, col in (("e", cnt_e, q_e, "experience"), ("h", cnt_h, q_h, "hedonic")):
        tp, fn, tn, fp = cnt
        se, sp = rng.beta(tp + 1, fn + 1), rng.beta(tn + 1, fp + 1)
        if se + sp <= 1.0:
            return None
        pi = float(np.clip((q + sp - 1) / (se + sp - 1), 1e-4, 1 - 1e-4))
        L = prods[col].values.astype(int)
        if tag == "e":
            res = em(D, L, D.pid.values, se, sp, pi, F_NB, "nb", alpha=alpha)
            b, c = res.params, res.cov_params()
            out.update(gap=b["gap"], inter=b["gap:T"], net=b["gap"] + b["gap:T"], sens_e=se, spec_e=sp, prev_e=pi)
        else:
            res = em(D, L, D.pid.values, se, sp, pi, F_OLS, "ols")
            out.update(hed=res.params["T"], sens_h=se, spec_h=sp, prev_h=pi)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--validation", required=True)
    ap.add_argument("--draws", type=int, default=80); ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--out"); ap.add_argument("--method", choices=["em", "rc"], default="em",
                    help="em: maximum likelihood (uses the outcome); rc: regression calibration (E[T|L], no outcome model)")
    a = ap.parse_args()
    init(a.data)
    v = pd.read_csv(a.validation)
    cnt_e = counts(v, "consensus_good_type", "llm_good_type", "experience"); cnt_h = counts(v, "consensus_motive", "llm_motive", "hedonic")
    prods = D.drop_duplicates("pid"); q_e, q_h = prods.experience.mean(), prods.hedonic.mean()
    rhs0 = "gap * experience + np.log(len_chars) + C(star_f) + has_image"
    alpha = models._estimate_alpha(D, [rhs0])
    g = pd.factorize(D.parent_asin)[0]
    obs = smf.glm("count ~ " + rhs0, data=D, family=sm.families.NegativeBinomial(alpha=alpha), offset=np.log(D.exposure)).fit(cov_type="cluster", cov_kwds={"groups": g})
    obs_h = smf.ols("gap ~ hedonic + C(star_f) + len_chars + age", data=D).fit(cov_type="cluster", cov_kwds={"groups": g})
    # sanity check: with Se=Sp=1 the EM must reproduce the observed-label fit
    with mp.Pool(a.procs, initializer=init, initargs=(a.data,)) as pool:
        res = [r for r in pool.map(one_draw_rc if a.method == "rc" else one_draw, [(s, alpha, cnt_e, cnt_h, q_e, q_h) for s in range(a.draws)]) if r]
    R = pd.DataFrame(res)
    if a.out:
        R.to_csv(a.out, index=False)
    pr = lambda x: np.percentile(x, [2.5, 50, 97.5])
    cov = obs.cov_params(); nb = obs.params["gap"] + obs.params["gap:experience"]
    nse = float(np.sqrt(cov.loc["gap", "gap"] + cov.loc["gap:experience", "gap:experience"] + 2 * cov.loc["gap", "gap:experience"]))
    def rubin(q, se):
        q, se = np.asarray(q), np.asarray(se); K = len(q)
        return q.mean(), float(np.sqrt((se ** 2).mean() + (1 + 1 / K) * q.var(ddof=1)))
    print(f"method {a.method} | draws used: {len(R)} of {a.draws} | LLM shares: experience {q_e:.3f}, hedonic {q_h:.3f}")
    for name, ob, ose, col, ex in (("NB2 gap IRR (search goods)", obs.params["gap"], obs.bse["gap"], "gap", True),
                                   ("NB2 gap x experience IRR", obs.params["gap:experience"], obs.bse["gap:experience"], "inter", True),
                                   ("NB2 net gap IRR (experience goods)", nb, nse, "net", True),
                                   ("Gap ~ hedonic (OLS coef.)", obs_h.params["hedonic"], obs_h.bse["hedonic"], "hed", False)):
        f = np.exp if ex else (lambda x: x); lo, md, hi = pr(R[col])
        txt = f"{name:36s} observed {f(ob):.3f} [{f(ob-1.96*ose):.3f}, {f(ob+1.96*ose):.3f}] | corrected median {f(md):.3f}, range over error-rate draws [{f(lo):.3f}, {f(hi):.3f}]"
        if a.method == "rc":
            qb, se = rubin(R[col], R[col + "_se"]); txt += f" | pooled (Rubin) {f(qb):.3f} [{f(qb-1.96*se):.3f}, {f(qb+1.96*se):.3f}]"
        print(txt)


if __name__ == "__main__":
    main()
