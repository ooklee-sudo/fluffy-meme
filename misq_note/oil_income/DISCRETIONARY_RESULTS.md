# Discretionary vs essential retail sales, Mar–Jul 2026 (pre-registered, `ANALYSIS_PLAN_DISCRETIONARY.md`)
Script `analysis_discretionary.py`; output `results_discretionary.json`; data Census MRTS (NSA, nominal), 415 months through 2026-07; ten reference years (2026 + 9 placebo).

**H_D1 (discretionary falls relative to essential) is not supported; the sign is opposite.** R = ln(DISC) − ln(ESS): D_2026 = +0.065, the highest of the ten years (placebo range −0.023..+0.043; one-sided "low" p = 1.00; two-sided perm p = 0.10).
- DISC (furniture 442, electronics/appliances 443, clothing 448, sporting/hobby/books 451, misc. 453): +0.035 (p = 0.20); every category is above forecast (442 +0.010, 443 +0.055, 448 +0.017, 451 +0.072, 453 +0.049). H_D2 (mean of the five < 0) fails: mean +0.041.
- ESS: −0.030 (lowest of ten, one-sided p = 0.10), driven by health and personal care stores 446 (−0.065, lowest of ten) while grocery 4451 is −0.011 (p = 0.5). The ratio rise comes largely from the essential side falling.
- Others: motor vehicles 441 +0.022; building materials 444 +0.053; department stores +0.023; general merchandise 4523 +0.009; gasoline stations 447 +0.191 (price effect); nonstore 454 +0.040; food services 722 +0.003.
- Checks: ratio D with training 24 months +0.030, 48 months +0.086, no trend +0.040, Mar–Jun +0.061: all positive.

**Reading.** In national nominal sales through July 2026, discretionary store categories did not fall; they ran above their pre-war trend. Candidate explanations (not tested): tariff-driven and general price increases in nominal goods sales, pull-forward, or the model's trend extrapolation; the drop in health/personal-care stores is unexplained here. Evidence for "war suppresses non-essential consumption" is absent in these data, and the one-sided test strongly rejects the directional hypothesis. No deflator was used, so real quantities could still differ.
