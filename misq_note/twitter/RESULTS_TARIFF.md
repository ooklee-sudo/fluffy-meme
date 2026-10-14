# Tariff/trade/China tweets, 2017–2021: confirmatory test (plan: ANALYSIS_PLAN_TARIFF.md with Amendment 1; code: build_frame_tariff.py, analysis_tariff.py; output: results_tariff.json)

Frame 937 tweets; 632 pass the three-hour filter; 410 have a valid S&P 500 CFD tick window (222 excluded: weekend/overnight, no tick within 10 minutes). By year 32, 131, 148, 99. Labels: two independent model instances (κ = 0.80); human labels for this sample are pending (sheets sent), so every directional result is conditional on model labels. USD/CNH ticks (H11) have not been downloaded; H11 is not reported. Mean |z| = 0.96 (median 0.55).

## Propositions HI1–HI3 (label-free; |z| on N_c, U, N_c × U; year fixed effects; day-clustered SE; one-sided; Holm)
| Hypothesis | Coefficient (SE) | One-sided p | Holm-adjusted | Decision |
|---|---|---|---|---|
| HI1 novelty N_c | −0.05 (0.68) | 0.53 | 0.74 | Not supported |
| HI2 prior uncertainty U | +0.40 (0.10) | 4.5e-5 | 1.4e-4 | **Supported** |
| HI3 N_c × U | +0.32 (0.97) | 0.37 | 0.74 | Not supported |
TF-IDF novelty (robustness): +0.15 (SE 0.32), p = 0.32.
Caveat that limits what HI2 means: U is the log ratio of the recent (5-day) to the long-run (60-day) daily S&P volatility, and |z| is scaled by the long-run volatility, so the result is what volatility clustering alone predicts. It is consistent with the account but does not distinguish it from the ordinary persistence of volatility. In the oil sample (RESULTS_TWITTER.md) the same coefficient was positive but not significant (p = 0.15).

## H10 (agreed model labels; directional S&P return in %, one-sided Wilcoxon; DEESC = +r, ESC = −r)
| Class | n | mean 30 min | median | p (> 0) | mean pre-30 | post − pre | p (post > pre) |
|---|---|---|---|---|---|---|---|
| DEESC (S&P up) | 70 | +0.085 | +0.027 | 0.0007 | +0.013 | +0.074 | 0.099 |
| ESC (S&P down) | 50 | +0.046 | +0.028 | 0.024 | +0.000 | +0.030 | 0.048 |
Decision: H10's post-window tests are supported for both classes (small effects, 0.05–0.09% of the index); the post-versus-pre comparison is supported for escalation (p = 0.048) and not for de-escalation (p = 0.099).

## H12 (state-dependent sign; pre-registered in Amendment 1 before returns were examined): **not supported, and in the opposite direction**
Regression dir30 = α_class + β·(s × R), n = 108 tweets with an agreed label and a defined regime R (64 DEESC, 44 ESC): β = −0.097 (SE 0.032); one-sided p (β > 0) = 0.9987; two-sided p = 0.003. The messages that continue the recent regime moved the market more than messages that ran against it. Tercile means of the directional return (aligned / middle / opposed): DEESC +0.119 / +0.115 / +0.045; ESC +0.150 / +0.025 / −0.084.
By the rule fixed in the plan, the sign-flip reading of the oil results carries no theoretical weight, and the manuscript's third-contribution paragraph about the sign is removed.

## Limits
Model labels only; 35% of kept tweets have no tick window; R requires at least three labelled signal tweets in 30 days (108 of 120 signal tweets); effects are small in index terms; HI2 is confounded with volatility clustering; the CFD is a proxy; human labels pending.
