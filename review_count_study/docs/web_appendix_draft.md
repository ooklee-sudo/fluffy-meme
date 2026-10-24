# Web Appendix (draft; limit 2,000 words excluding tables)

## A. Original star-inference prompt (WZH 2026)

The supplementary material of Winter, Zacharias, and Hartwig (2026; Web Appendix 7, GUIDE-LLM items B.3, C.1, C.2) reports the system prompt as three strings: "You are a classifier. Your job is to tell me the star rating of a product review." / "Treat every prompt as if it were a review." / "Answer only with the corresponding number between 1 and 5." The review text is the user message, temperature 0.2, one completion per review, stateless calls. How the strings were combined is not shown; we joined them with single spaces. The original runs used OpenAI models via API; we ran Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano through a common API gateway. Responses that could not be parsed to a single rating from 1 to 5 were dropped (0–0.3% per run). Our own prompt asks for a JSON object with the rating and runs at temperature 0.

## B. Product-level goods classification

Each sampled product (20,672) was described by its title, main category, category path (last four levels), up to three feature bullets, and the first 250 characters of the description, and classified by Claude Haiku 5.5 at temperature 0 with a system prompt that defined four labels. Search: the product's main quality can be judged reliably before purchase from seller-provided information (specifications, dimensions, compatibility, photos, ratings). Experience: the main quality can only be judged after using, tasting, wearing, or trying the product (fit, comfort, taste, scent, skin reaction, feel, durability, how well it works). Hedonic: bought mainly for pleasure, enjoyment, sensory or emotional value, or self-expression. Utilitarian: bought mainly to perform a functional task or solve a practical need. The prompt gave WZH's four anchors (smartphone = search, hedonic; printer = search, utilitarian; mascara = experience, hedonic; vacuum cleaner = experience, utilitarian) and asked for a JSON object with a generic product type and the two labels. Two products could not be parsed. Llama 3.3 70B labeled a random 3,000 products; one could not be parsed.

Agreement on the 2,999 products labeled by both models: search versus experience 88.8% (κ = .755); hedonic versus utilitarian 87.6% (κ = .698); both dimensions 77.6%. Disagreements on the hedonic dimension were mainly products that Llama labeled hedonic and Claude utilitarian (327 products) rather than the reverse (45), i.e., Llama labeled more products as hedonic. Claude's labels in the analysis sample: 37.0% experience and 22.5% hedonic. Human validation. Two coders labeled a simple random sample of 200 products, drawn from all labeled products and blind to the LLM labels and to review data. The first 100 products served as a calibration round: the coders' agreement was low (κ = .27 for search versus experience, κ = .42 for hedonic versus utilitarian after two revisions of one coder's sheet; κ ≈ 0 for both dimensions in its first version), the coder guide was extended with decision rules for standardized accessories and decorative functional goods, and one coder's labels were revised after receiving feedback on specific items. Because that feedback used these items, they are not treated as validation data. The remaining 100 products (P101–P200) were coded with the extended guide; the coders were instructed to work independently and without access to the LLM labels. [TODO: report whether the qualification quiz was completed and how independence was ensured.] Agreement between the coders was 97% for search versus experience (κ = .926, 95% CI .83–1.00) and 94% for hedonic versus utilitarian (κ = .855, 95% CI .73–.95); 91 products received identical labels on both dimensions. Nine products with disagreements (five hair- or beard-care products, one beard trimmer, one set of chalkboard tags, one adhesive tape, and one vacuum cleaner) were resolved jointly by the two coders; the five hair-care products received one common decision. The decision rules were set after the calibration round, and the adjudication rules were set after seeing the disagreements, which we report as a limitation.

Against the coders' consensus, the LLM labels agreed on 92.0% of products for search versus experience (κ = .820, 95% CI .69–.93) and 90.0% for hedonic versus utilitarian (κ = .758, 95% CI .61–.89). Errors were one-sided: in 8 cases the LLM assigned experience where the coders said search (none in the opposite direction), and in 8 cases it assigned hedonic where the coders said utilitarian (2 in the opposite direction). Treating each disagreement as the label of either coder instead of the consensus gives κ between .77 and .84 (search versus experience) and between .72 and .80 (hedonic versus utilitarian). The validation sample is small, so these intervals are wide, and it cannot show how label error is distributed across categories.

## C. Full estimates for all twelve combinations

Gap coefficients, Tobit (left-censored at 0) with standard errors clustered by product (p in parentheses), and negative binomial (NB2) incidence rate ratios with 95% intervals. Tobit Model 1 omits the interaction; Model 2 adds gap × experience. NB2 Model 1 omits the interaction; Model 2 adds it (the gap row is then the effect for search goods). Controls: review length, rating dummies, image indicator, review age; NB2 uses log review age as offset.

| Prompt | LLM | Goods labels | Tobit M1 gap | Tobit M2 gap | Tobit M2 gap × exp | NB2 M1 gap IRR | NB2 M2 gap IRR | NB2 M2 gap × exp IRR |
|---|---|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | category | 0.98 (.014) | 1.28 (.026) | -0.59 (.404) | 1.26 [1.10, 1.44] | 1.25 [1.03, 1.50] | 1.02 [0.79, 1.31] |
| ours | Llama 3.3 70B | category | 0.82 (.040) | 1.38 (.025) | -1.06 (.123) | 1.24 [1.08, 1.42] | 1.36 [1.11, 1.66] | 0.82 [0.65, 1.03] |
| ours | GPT-4.1 nano | category | 0.90 (.010) | 1.45 (.007) | -1.05 (.131) | 1.22 [1.08, 1.38] | 1.29 [1.08, 1.54] | 0.90 [0.72, 1.14] |
| original | Claude Haiku 5.5 | category | 0.82 (.024) | 1.13 (.044) | -0.60 (.462) | 1.21 [1.04, 1.40] | 1.25 [1.00, 1.57] | 0.92 [0.70, 1.22] |
| original | Llama 3.3 70B | category | 0.84 (.041) | 1.34 (.026) | -1.01 (.165) | 1.28 [1.11, 1.49] | 1.36 [1.12, 1.64] | 0.89 [0.69, 1.14] |
| original | GPT-4.1 nano | category | 0.45 (.181) | 0.71 (.158) | -0.54 (.437) | 1.21 [1.05, 1.38] | 1.19 [0.97, 1.46] | 1.03 [0.79, 1.34] |
| ours | Claude Haiku 5.5 | product | 1.01 (.012) | 1.33 (.012) | -0.82 (.291) | 1.28 [1.12, 1.46] | 1.30 [1.11, 1.53] | 0.95 [0.73, 1.22] |
| ours | Llama 3.3 70B | product | 0.81 (.040) | 1.03 (.054) | -0.51 (.440) | 1.25 [1.09, 1.43] | 1.35 [1.13, 1.60] | 0.80 [0.65, 1.00] |
| ours | GPT-4.1 nano | product | 0.91 (.009) | 1.11 (.016) | -0.49 (.474) | 1.23 [1.09, 1.39] | 1.29 [1.11, 1.49] | 0.88 [0.70, 1.11] |
| original | Claude Haiku 5.5 | product | 0.81 (.025) | 1.05 (.031) | -0.61 (.487) | 1.23 [1.07, 1.43] | 1.31 [1.10, 1.57] | 0.83 [0.64, 1.07] |
| original | Llama 3.3 70B | product | 0.83 (.042) | 1.03 (.053) | -0.46 (.523) | 1.29 [1.12, 1.49] | 1.36 [1.15, 1.61] | 0.87 [0.68, 1.12] |
| original | GPT-4.1 nano | product | 0.47 (.167) | 0.61 (.169) | -0.39 (.577) | 1.22 [1.07, 1.40] | 1.23 [1.04, 1.46] | 0.98 [0.76, 1.27] |

For comparison, WZH report Tobit Model 1 gap −0.650 (p = .428), Model 2 gap +4.345 (p = .014), gap × experience −7.239 (p < .001), and in their GPT-5-nano check +6.29 (p = .001) and −8.46 (p < .001). Scales differ: WZH's Tobit intercepts are about −63 to −79, which indicates far larger vote counts than in our sample (mean 0.89); 54% of their reviews are censored at zero.

Clustering by user instead of product changes the NB2 interaction p-value by at most about .01 in the combinations inspected (e.g., Llama, our prompt, category labels: IRR 0.820, p = .093 by user versus .090 by product).

## D. Zero-inflation diagnostics

For each combination we compared NB2 with a zero-inflated negative binomial (logit inflation on a constant and the experience dummy; same count-part covariates; log review age as exposure). In every case the inflation intercept diverged and the log-likelihood equals that of NB2, so the model is not identified beyond NB2 (a boundary solution, not a convergence failure).

| Prompt | LLM | Goods labels | logLik NB2 | logLik ZINB | AIC NB2 / ZINB | Implied P(structural zero) |
|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | category | -22339.85 | -22339.85 | 44701.7 / 44705.7 | 2.55e-102 |
| ours | Llama 3.3 70B | category | -22345.46 | -22345.46 | 44712.9 / 44716.9 | 3.72e-99 |
| ours | GPT-4.1 nano | category | -22291.97 | -22291.97 | 44605.9 / 44609.9 | 6.24e-95 |
| original | Claude Haiku 5.5 | category | -22307.74 | -22307.74 | 44637.5 / 44641.5 | 3.34e-116 |
| original | Llama 3.3 70B | category | -22340.87 | -22340.87 | 44703.7 / 44707.7 | 1.23e-103 |
| original | GPT-4.1 nano | category | -22274.58 | -22274.58 | 44571.2 / 44575.2 | 1.79e-96 |
| ours | Claude Haiku 5.5 | product | -22342.92 | -22342.92 | 44707.8 / 44711.8 | 5.85e-96 |
| ours | Llama 3.3 70B | product | -22349.81 | -22349.81 | 44721.6 / 44725.6 | 4.59e-98 |
| ours | GPT-4.1 nano | product | -22299.12 | -22299.12 | 44620.2 / 44624.2 | 2.37e-91 |
| original | Claude Haiku 5.5 | product | -22317.98 | -22317.98 | 44658.0 / 44662.0 | 6.20e-101 |
| original | Llama 3.3 70B | product | -22346.10 | -22346.10 | 44714.2 / 44718.2 | 2.44e-102 |
| original | GPT-4.1 nano | product | -22278.01 | -22278.01 | 44578.0 / 44582.0 | 3.52e-91 |

## E. Replication package

Planned contents: review IDs of the sampled reviews, the LLM-inferred ratings for each LLM and prompt, product-level labels, and analysis code. Raw review text and metadata are not redistributed (Amazon Reviews 2023 is available from its authors; cite Hou et al. 2024). [TODO: repository link and data-sharing check against the journal's data policy.]
