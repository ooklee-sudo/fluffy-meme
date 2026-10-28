# Derivation: detectability bound for exposure-based designs

**Setting.** Occupation j (j = 1..J) has a true share s_j of work that a technology can take over. In the sector a share A_acq of employers has acquired the technology, of which a share g has assimilated it (A = g A_acq). An assimilating employer changes demand for the occupation's work by beta log points (displacement, reinstatement and scale effects netted out). To first order, the outcome change in occupation j is

    y_j = A * beta * s_j + eta_j + eps_cj      (eta_j: occupation shock common to its cells, eps_cj: cell noise)

Exposure is a noisy proxy of s_j up to scale, e_j = lam * s_j + u_j (u independent of s, eta, eps), with reliability R = lam^2 var(s) / var(e). The design regresses y on z_j = (e_j - mean(e)) / sd(e).

**Proposition 1 (implied coefficient).** The population coefficient on z is

    gamma* = A * beta * sigma_s * sqrt(R),      A = g * A_acq,

where sigma_s is the cross-occupation SD of s. *Proof.* gamma = A beta cov(s, z) / var(z) and var(z) = 1. With e = lam s + u, cov(s, z) = lam var(s) / sd(e) = sigma_s * (lam sigma_s / sd(e)) = sigma_s sqrt(R). QED.
The manuscript's equation (5) is the case R = 1 and sigma_s = 1/k, i.e. the most exposed occupation has s = 1 and lies k SD above the mean. Because s <= 1, any exposure score read as an actual share of work gives a *smaller* sigma_s and therefore a smaller gamma*: the k-based calculation is the most favourable to detection (in our data sigma_s = 0.039 if the scores are read as shares, versus 1/k = 0.19).

**Proposition 2 (attenuation).** With classical error, gamma* is multiplied by sqrt(R), while the minimum detectable effect depends on the standard error only, so noise in exposure cannot make an assimilation effect easier to detect.

**Proposition 3 (minimum detectable effect and standard error).** MDE = (z_{1-alpha/2} + z_{power}) SE = 2.80 SE for alpha = .05 and power = .80. For J occupation clusters with C cells each,
SE ~ sqrt((sigma_eta^2 + (A beta sigma_s)^2 (1-R) + sigma_eps^2 / C) / J). The middle term is the part of the true task share that noisy exposure fails to explain; it acts as an occupation-level shock and matters only when the assimilation effect is large.

**Corollary (required adoption).** Complete assimilation is detectable only if |gamma*| >= MDE, i.e. A >= MDE / (|beta| sigma_s sqrt(R)); if this exceeds one, no adoption level suffices. With a logistic adoption path the first year in which A(t) reaches the required share is the earliest detection date (Table 6 of the manuscript).
When the SE depends on the effect through the middle term, the self-consistent smallest signal scale X = |A beta sigma_s| solves X (J R - c^2 (1-R)) = c^2 (sigma_eta^2 + sigma_eps^2/C), with c = 2.80 (`required_effect_scale`); no solution exists if J R <= c^2 (1-R).

**Classification of an observed estimate** (rules (i)-(iii) of Section 4): uninformative if |gamma*| < MDE; rejects complete assimilation if the estimate is significantly smaller in magnitude than gamma*; attributable to other causes if significantly larger than the largest plausible gamma_max; otherwise consistent with complete assimilation.

**Assumptions and limits.** First-order (linear) mapping from adoption to demand change; classical measurement error independent of s; no spillovers across occupations; controls enter only through a user-supplied `retention` factor (we do not derive it); cluster-robust SEs with few effective clusters over-reject (see README), so the bound should be used with randomization or wild-bootstrap inference.
