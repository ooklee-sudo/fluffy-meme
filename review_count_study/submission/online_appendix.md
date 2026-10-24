# Web Appendix

## A. Original star-inference prompt (WZH 2026)

The supplementary material of Winter, Zacharias, and Hartwig (2026; Web Appendix 7, GUIDE-LLM items B.3, C.1, C.2) reports the system prompt as three strings: "You are a classifier. Your job is to tell me the star rating of a product review." / "Treat every prompt as if it were a review." / "Answer only with the corresponding number between 1 and 5." The review text is the user message, temperature 0.2, one completion per review, stateless calls. How the strings were combined is not shown; we joined them with single spaces. The original runs used OpenAI models via API; we ran Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano through a common API gateway. Responses that could not be parsed to a single rating from 1 to 5 were dropped (0–0.3% per run). Our own prompt asks for a JSON object with the rating and runs at temperature 0.

## B. Product-level goods classification

Each sampled product (20,672) was described by its title, main category, category path (last four levels), up to three feature bullets, and the first 250 characters of the description, and classified by Claude Haiku 5.5 at temperature 0 with a system prompt that defined four labels. Search: the product's main quality can be judged reliably before purchase from seller-provided information (specifications, dimensions, compatibility, photos, ratings). Experience: the main quality can only be judged after using, tasting, wearing, or trying the product (fit, comfort, taste, scent, skin reaction, feel, durability, how well it works). Hedonic: bought mainly for pleasure, enjoyment, sensory or emotional value, or self-expression. Utilitarian: bought mainly to perform a functional task or solve a practical need. The prompt gave WZH's four anchors (smartphone = search, hedonic; printer = search, utilitarian; mascara = experience, hedonic; vacuum cleaner = experience, utilitarian) and asked for a JSON object with a generic product type and the two labels. Two products could not be parsed. Llama 3.3 70B labeled a random 3,000 products; one could not be parsed.

Agreement on the 2,999 products labeled by both models: search versus experience 88.8% (κ = .755); hedonic versus utilitarian 87.6% (κ = .698); both dimensions 77.6%. Disagreements on the hedonic dimension were mainly products that Llama labeled hedonic and Claude utilitarian (327 products) rather than the reverse (45), i.e., Llama labeled more products as hedonic. Claude's labels in the analysis sample: 37.0% experience and 22.5% hedonic. Human validation. Two coders labeled a simple random sample of 200 products, drawn from all labeled products and blind to the LLM labels and to review data. The first 100 products served as a calibration round: the coders' agreement was low (κ = .27 for search versus experience, κ = .42 for hedonic versus utilitarian after two revisions of one coder's sheet; κ ≈ 0 for both dimensions in its first version), the coder guide was extended with decision rules for standardized accessories and decorative functional goods, and one coder's labels were revised after receiving feedback on specific items. Because that feedback used these items, they are not treated as validation data. The remaining 100 products (P101–P200) were coded with the extended guide; the coders were instructed to work independently and without access to the LLM labels. [AUTHORS TO CONFIRM: whether the qualification quiz was completed and how independence between the coders was ensured.] Agreement between the coders was 97% for search versus experience (κ = .926, 95% CI .83–1.00) and 94% for hedonic versus utilitarian (κ = .855, 95% CI .73–.95); 91 products received identical labels on both dimensions. Nine products with disagreements (five hair- or beard-care products, one beard trimmer, one set of chalkboard tags, one adhesive tape, and one vacuum cleaner) were resolved jointly by the two coders; the five hair-care products received one common decision. The decision rules were set after the calibration round, and the adjudication rules were set after seeing the disagreements, which we report as a limitation.

Against the coders' consensus, the LLM labels agreed on 92.0% of products for search versus experience (κ = .820, 95% CI .69–.93) and 90.0% for hedonic versus utilitarian (κ = .758, 95% CI .61–.89). Errors were one-sided: in 8 cases the LLM assigned experience where the coders said search (none in the opposite direction), and in 8 cases it assigned hedonic where the coders said utilitarian (2 in the opposite direction). Treating each disagreement as the label of either coder instead of the consensus gives κ between .77 and .84 (search versus experience) and between .72 and .80 (hedonic versus utilitarian). The validation sample is small, so these intervals are wide, and it cannot show how label error is distributed across categories.

## C. Full estimates for all twelve combinations

Gap coefficients, Tobit (left-censored at 0) with standard errors clustered by product (p in parentheses), and negative binomial (NB2) incidence rate ratios with 95% intervals. Tobit Model 1 omits the interaction; Model 2 adds gap × experience. NB2 Model 1 omits the interaction; Model 2 adds it (the gap row is then the effect for search goods). Controls: review length, rating dummies, image indicator, review age; NB2 uses log review age as offset.

| Prompt | LLM | Goods labels | Tobit M1 gap | Tobit M2 gap | Tobit M2 gap × exp | NB2 M1 gap IRR | NB2 M2 gap IRR | NB2 M2 gap × exp IRR |
|---|---|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | category | 0.98 (.014) | 1.28 (.026) | -0.59 (.404) | 1.26 [1.10, 1.44] | 1.25 [1.03, 1.50] | 1.02 [0.79, 1.31] |
| ours | Llama 3.3 70B | category | 0.82 (.040) | 1.38 (.025) | -1.06 (.123) | 1.24 [1.08, 1.42] | 1.36 [1.11, 1.66] | 0.82 [0.65, 1.03] |
| ours | GPT-4.1 nano | category | 0.90 (.010) | 1.45 (.007) | -1.06 (.131) | 1.22 [1.08, 1.38] | 1.29 [1.08, 1.54] | 0.90 [0.72, 1.14] |
| original | Claude Haiku 5.5 | category | 0.78 (.032) | 1.02 (.061) | -0.50 (.537) | 1.20 [1.03, 1.40] | 1.25 [1.00, 1.56] | 0.93 [0.71, 1.22] |
| original | Llama 3.3 70B | category | 0.84 (.041) | 1.34 (.026) | -1.01 (.165) | 1.28 [1.11, 1.49] | 1.36 [1.12, 1.64] | 0.89 [0.69, 1.14] |
| original | GPT-4.1 nano | category | 0.45 (.180) | 0.71 (.158) | -0.54 (.439) | 1.21 [1.05, 1.38] | 1.19 [0.97, 1.46] | 1.03 [0.79, 1.34] |
| ours | Claude Haiku 5.5 | product | 1.01 (.012) | 1.33 (.012) | -0.82 (.291) | 1.28 [1.12, 1.46] | 1.30 [1.11, 1.53] | 0.95 [0.73, 1.22] |
| ours | Llama 3.3 70B | product | 0.81 (.040) | 1.03 (.054) | -0.51 (.440) | 1.25 [1.09, 1.43] | 1.35 [1.13, 1.60] | 0.80 [0.65, 1.00] |
| ours | GPT-4.1 nano | product | 0.91 (.009) | 1.11 (.016) | -0.49 (.474) | 1.23 [1.09, 1.39] | 1.29 [1.11, 1.49] | 0.88 [0.70, 1.11] |
| original | Claude Haiku 5.5 | product | 0.81 (.025) | 1.05 (.031) | -0.61 (.487) | 1.23 [1.07, 1.43] | 1.31 [1.10, 1.57] | 0.83 [0.64, 1.07] |
| original | Llama 3.3 70B | product | 0.83 (.042) | 1.03 (.053) | -0.46 (.523) | 1.29 [1.12, 1.49] | 1.36 [1.15, 1.61] | 0.87 [0.68, 1.12] |
| original | GPT-4.1 nano | product | 0.47 (.167) | 0.61 (.169) | -0.39 (.577) | 1.22 [1.07, 1.40] | 1.23 [1.04, 1.46] | 0.98 [0.76, 1.27] |

For comparison, WZH report Tobit Model 1 gap −0.650 (p = .428), Model 2 gap +4.345 (p = .014), gap × experience −7.239 (p < .001), and in their GPT-5-nano check +6.29 (p = .001) and −8.46 (p < .001). Scales differ: WZH's Tobit intercepts are about −63 to −79, which indicates far larger vote counts than in our sample (mean 0.89); 54% of their reviews are censored at zero.

Clustering by user instead of product changes the NB2 interaction p-value by at most about .01 in the combinations inspected (e.g., Llama, our prompt, category labels: IRR 0.820, p = .093 by user versus .090 by product).

## D. Zero-inflation diagnostics

For each combination we compared NB2 with a zero-inflated negative binomial (logit inflation on a constant and the experience dummy; same count-part covariates; log review age as exposure). In every case the inflation intercept diverged and the log-likelihood equals that of NB2 (difference at most 0.001), so the model is not identified beyond NB2 (a boundary solution, not a convergence failure).

| Prompt | LLM | Goods labels | logLik NB2 | logLik ZINB | AIC NB2 / ZINB | Implied P(structural zero) |
|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | category | -22339.85 | -22339.85 | 44701.7 / 44705.7 | 2.55e-102 |
| ours | Llama 3.3 70B | category | -22345.46 | -22345.46 | 44712.9 / 44716.9 | 3.72e-99 |
| ours | GPT-4.1 nano | category | -22294.33 | -22294.33 | 44610.7 / 44614.7 | 5.89e-95 |
| original | Claude Haiku 5.5 | category | -22318.98 | -22318.97 | 44660.0 / 44663.9 | 9.60e-107 |
| original | Llama 3.3 70B | category | -22340.87 | -22340.87 | 44703.7 / 44707.7 | 1.23e-103 |
| original | GPT-4.1 nano | category | -22274.91 | -22274.91 | 44571.8 / 44575.8 | 1.76e-96 |
| ours | Claude Haiku 5.5 | product | -22342.92 | -22342.92 | 44707.8 / 44711.8 | 5.85e-96 |
| ours | Llama 3.3 70B | product | -22349.81 | -22349.81 | 44721.6 / 44725.6 | 4.59e-98 |
| ours | GPT-4.1 nano | product | -22299.12 | -22299.12 | 44620.2 / 44624.2 | 2.37e-91 |
| original | Claude Haiku 5.5 | product | -22317.98 | -22317.98 | 44658.0 / 44662.0 | 6.20e-101 |
| original | Llama 3.3 70B | product | -22346.10 | -22346.10 | 44714.2 / 44718.2 | 2.44e-102 |
| original | GPT-4.1 nano | product | -22278.01 | -22278.01 | 44578.0 / 44582.0 | 3.52e-91 |

## E. Sensitivity to misclassified product labels

The product-level labels come from an LLM and contain errors. Against the two-coder consensus (100 products), the labels had sensitivity 1.00 (29/29) and specificity .89 (63/71) for experience goods, and sensitivity .92 (24/26) and specificity .89 (66/74) for hedonic goods. Because misclassifying the moderator can bias an interaction toward zero, we corrected the key estimates for these error rates by regression calibration. In each of 120 draws, sensitivity and specificity were drawn from Beta posteriors (uniform prior) given the validation counts; the true prevalence was backed out of the observed LLM share (Rogan–Gladen identity); and each product's expected true label, E[T | LLM label], computed from the implied positive and negative predictive values, replaced the LLM label in the Model 2 negative binomial regression of Table 2 and in the regression of the gap on the hedonic indicator. We report the median and the range of the corrected estimates over the draws, and estimates pooled with Rubin's rules, which add the between-draw variance to the clustered sampling variance so that the intervals reflect uncertainty about the error rates. The method assumes that misclassification is non-differential (independent of helpful votes and of the gap), that error rates are equal across categories, and that the validation sample is representative; none of these assumptions can be tested here. Regression calibration is exact for linear models and approximate for the log-linear negative binomial model.

**Table E1. Gap × experience interaction and net gap effect for experience goods, before and after correction**

| Prompt | LLM | Gap × experience IRR, observed [95% CI] | Corrected: median (range over error-rate draws) | Corrected, pooled [95% CI] | Net gap IRR, experience goods: observed | Net gap IRR, corrected, pooled [95% CI] |
|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | 0.946 [0.732, 1.223] | 0.928 (0.888–0.938) | 0.924 [0.636, 1.343] | 1.234 | 1.206 [0.879, 1.656] |
| ours | Llama 3.3 70B | 0.805 [0.649, 0.999] | 0.745 (0.629–0.777) | 0.734 [0.525, 1.026] | 1.084 | 0.993 [0.772, 1.277] |
| ours | GPT-4.1 nano | 0.885 [0.704, 1.112] | 0.847 (0.770–0.868) | 0.840 [0.599, 1.179] | 1.138 | 1.082 [0.824, 1.421] |
| original | Claude Haiku 5.5 | 0.826 [0.638, 1.069] | 0.771 (0.665–0.801) | 0.762 [0.516, 1.123] | 1.086 | 1.005 [0.729, 1.386] |
| original | Llama 3.3 70B | 0.868 [0.675, 1.115] | 0.825 (0.738–0.848) | 0.817 [0.563, 1.185] | 1.178 | 1.112 [0.813, 1.521] |
| original | GPT-4.1 nano | 0.979 [0.756, 1.267] | 0.971 (0.955–0.975) | 0.970 [0.666, 1.412] | 1.204 | 1.194 [0.881, 1.617] |

**Table E2. Hedonic coefficient on the gap, before and after correction**

| Prompt | LLM | Observed [95% CI] | Corrected: median (range over error-rate draws) | Corrected, pooled [95% CI] |
|---|---|---|---|---|
| ours | Claude Haiku 5.5 | −0.029 [−0.046, −0.011] | −0.048 (−0.102 to −0.037) | −0.058 [−0.201, 0.085] |
| ours | Llama 3.3 70B | −0.017 [−0.032, −0.002] | −0.028 (−0.060 to −0.022) | −0.034 [−0.125, 0.057] |
| ours | GPT-4.1 nano | −0.017 [−0.036, 0.002] | −0.028 (−0.061 to −0.022) | −0.034 [−0.133, 0.064] |
| original | Claude Haiku 5.5 | −0.026 [−0.043, −0.008] | −0.043 (−0.091 to −0.033) | −0.052 [−0.182, 0.078] |
| original | Llama 3.3 70B | −0.017 [−0.032, −0.001] | −0.028 (−0.060 to −0.022) | −0.034 [−0.124, 0.057] |
| original | GPT-4.1 nano | −0.020 [−0.038, −0.003] | −0.034 (−0.073 to −0.026) | −0.041 [−0.149, 0.067] |

The corrected interactions lie further below one (medians 0.745–0.971) than the observed ones (0.805–0.979 in these refits), but every pooled interval includes one, and the corrected net gap effect for experience goods stays near or above one (pooled estimates 0.99–1.21, all intervals include one). The corrected hedonic coefficients are 1.6–1.7 times larger than the observed ones (−0.028 to −0.048), which matches the factor of about 1.7 implied by the error rates, but the pooled intervals include zero because the validation sample is small. A likelihood-based (EM) variant, run for one combination (Claude, our prompt, 80 draws), gave similar corrected experience estimates (interaction 0.960, range 0.904–1.045; net gap IRR 1.211) but a hedonic coefficient of −0.083, about three times the observed value and well above what the error rates imply for a linear association. We attribute this to the Gaussian outcome model fitting the discrete, skewed gap poorly and therefore do not use EM for the hedonic coefficient. Overall, the correction moves the interaction in the direction reported by WZH but does not make it detectable, and the validation sample is too small for precise correction.

## F. Replication package

Planned contents: review IDs of the sampled reviews, the LLM-inferred ratings for each LLM and prompt, product-level labels, and analysis code. Raw review text and metadata are not redistributed (Amazon Reviews 2023 is available from its authors; cite Hou et al. 2024). [AUTHORS TO COMPLETE: anonymized repository link.]
