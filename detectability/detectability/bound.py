"""Detectability bound for exposure-based designs.

Setting. Occupation j has a true share s_j of work that a technology can take over. A share A of employers in the
sector has adopted and assimilated it (A = g * A_acq, with g the assimilated share of acquirers), and each assimilating
employer changes demand for the occupation's work by beta (log points). The design regresses the outcome (change in log
adverts, vacancies or employment) on exposure e_j, standardized to z_j. Exposure is a noisy proxy of s_j up to scale:
e_j = lam * s_j + u_j, with reliability R = lam^2 var(s) / var(e).

Result (population coefficient per SD of exposure, classical error, no controls):
    gamma* = g * A_acq * beta * sigma_s * sqrt(R)
where sigma_s is the cross-occupation SD of s_j. If the most exposed occupation has s = 1 and lies k SD above the mean,
sigma_s = 1/k and R = 1 gives gamma* = A beta / k, the special case used in the manuscript (equation 5).
The minimum detectable effect of a two-sided test of size alpha with power 1-kappa is MDE = (z_{1-alpha/2} + z_{1-kappa}) * SE.
"""
from math import sqrt, exp, log
from statistics import NormalDist

_N = NormalDist()

def crit(alpha=0.05, power=0.80):
    """Multiplier of the standard error: z_{1-alpha/2} + z_{power} (2.80 for alpha=.05, power=.80)."""
    return _N.inv_cdf(1 - alpha / 2) + _N.inv_cdf(power)

def mde(se, alpha=0.05, power=0.80):
    return crit(alpha, power) * se

def se_from_design(n_occ, sigma_eps, sigma_eta=0.0, cells_per_occ=1.0, retention=1.0, A=None, beta=None, sigma_s=None, R=1.0, g=1.0):
    """Approximate SE of the coefficient on standardized exposure, errors clustered by occupation.
    Noise: occupation-level shock (SD sigma_eta, common to all cells of an occupation) and cell-level noise (SD sigma_eps).
    If A, beta and sigma_s are given and R < 1, the part of the true task share that the noisy exposure does not explain adds an
    occupation-level noise term with variance (g*A*beta*sigma_s)^2 * (1 - R); it matters only when the assimilation effect is large.
    retention in (0,1] is the share of exposure variance left after partialling out controls."""
    extra = 0.0
    if A is not None and beta is not None and sigma_s is not None:
        extra = (g * A * beta * sigma_s) ** 2 * (1 - R)
    return sqrt((sigma_eta ** 2 + extra + sigma_eps ** 2 / cells_per_occ) / (n_occ * retention))

def required_effect_scale(n_occ, sigma_eps, sigma_eta=0.0, cells_per_occ=1.0, R=1.0, alpha=0.05, power=0.80):
    """Smallest value of |g*A*beta*sigma_s| (the 'signal scale') at which |gamma*| reaches the MDE when the SE itself depends on the
    signal through the unexplained-signal term. Solves X*(J*R - c^2*(1-R)) = c^2*(sigma_eta^2 + sigma_eps^2/C) with X = (g*A*beta*sigma_s)^2;
    returns None if the denominator is not positive (undetectable at any effect size)."""
    c = crit(alpha, power); sigma0 = sigma_eta ** 2 + sigma_eps ** 2 / cells_per_occ
    den = n_occ * R - c ** 2 * (1 - R)
    return None if den <= 0 else c * sqrt(sigma0 / den)

def gamma_star(A, beta, sigma_s=None, k=None, R=1.0, g=1.0, retention=1.0):
    """Coefficient per SD of exposure implied by assimilation share g*A with effect beta.
    Give sigma_s directly, or k (SD distance of an occupation with s = 1, so sigma_s = 1/k).
    retention scales the coefficient when controls absorb part of the exposure variance (user-supplied)."""
    if sigma_s is None:
        if k is None: raise ValueError('give sigma_s or k')
        sigma_s = 1.0 / k
    return g * A * beta * sigma_s * sqrt(R) * retention

def required_adoption(beta, mde_value, sigma_s=None, k=None, R=1.0, g=1.0, retention=1.0):
    """Smallest adoption share A at which |gamma*| reaches the MDE; None if above one."""
    if sigma_s is None: sigma_s = 1.0 / k
    a = mde_value / (abs(beta) * sigma_s * sqrt(R) * g * retention)
    return a if a <= 1 else None

def earliest_year(a0, required, slope, start=2025, horizon=2100):
    """First year in which a logistic adoption path (log-odds rise `slope` per year from share a0 in `start`) reaches `required`."""
    if required is None: return None
    if a0 >= required: return start
    for y in range(start, horizon):
        if 1 / (1 + exp(-(log(a0 / (1 - a0)) + slope * (y - start)))) >= required: return y
    return None

def classify(estimate, se, gamma, gamma_max=None, alpha=0.05, power=0.80):
    """Classification rule of the manuscript (Section 4): (i) uninformative if |gamma*| < MDE; (ii) rejects complete
    assimilation if the estimate is significantly smaller in magnitude than gamma*; (iii) attributable to other causes
    if significantly larger than the largest plausible gamma_max; otherwise consistent with complete assimilation."""
    z = _N.inv_cdf(1 - alpha / 2)
    if abs(gamma) < mde(se, alpha, power): return 'uninformative'
    if (abs(estimate) - abs(gamma)) / se < -z: return 'rejects complete assimilation'
    if gamma_max is not None and (abs(estimate) - abs(gamma_max)) / se > z: return 'other causes'
    return 'consistent with complete assimilation'

def detectability(A, beta, se, sigma_s=None, k=None, R=1.0, g=1.0, retention=1.0, alpha=0.05, power=0.80):
    if sigma_s is None: sigma_s = 1.0 / k
    gam = gamma_star(A, beta, sigma_s=sigma_s, R=R, g=g, retention=retention)
    m = mde(se, alpha, power)
    return {'gamma_star': gam, 'mde': m, 'ratio_gamma_to_mde': abs(gam) / m, 'detectable': abs(gam) >= m,
            'required_adoption': required_adoption(beta, m, sigma_s=sigma_s, R=R, g=g, retention=retention),
            'power_at_gamma_star': _N.cdf(abs(gam) / se - _N.inv_cdf(1 - alpha / 2))}
