# Web Appendix

## A. Original star-inference prompt (WZH 2026)

The supplement of Winter, Zacharias, and Hartwig (2026; Web Appendix 7, items B.3, C.1, C.2) reports the system prompt as three strings: "You are a classifier. Your job is to tell me the star rating of a product review." / "Treat every prompt as if it were a review." / "Answer only with the corresponding number between 1 and 5." The review text is the user message, temperature 0.2, one stateless completion per review. How the strings were combined is not shown; we joined them with single spaces. The original runs used OpenAI models; we ran Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano through a common API gateway. Unparseable responses were dropped (0–0.3% per run). Our own prompt asks for a JSON object with the rating and runs at temperature 0.

## B. Product-level goods classification

Each sampled product (20,672) was described by its title, main category, category path (last four levels), up to three feature bullets, and the first 250 characters of the description, and classified by Claude Haiku 5.5 at temperature 0. The prompt defined four labels. Search: the main quality can be judged before purchase from seller-provided information. Experience: it can only be judged after use, taste, wear, or trial. Hedonic: bought mainly for pleasure, sensory or emotional value, or self-expression. Utilitarian: bought mainly for a functional task. It gave WZH's anchors (smartphone = search, hedonic; printer = search, utilitarian; mascara = experience, hedonic; vacuum cleaner = experience, utilitarian) and asked for a JSON object with a product type and the two labels. Llama 3.3 70B labeled a random 3,000 products as a check.

On the 2,999 products labeled by both models, agreement was 88.8% for search versus experience (κ = .755), 87.6% for hedonic versus utilitarian (κ = .698), and 77.6% on both. Llama labeled more products hedonic. 

Human validation. Two coders labeled a simple random sample of 200 products, blind to the LLM labels and review data. The first 100 were a calibration round: agreement was low (κ = .27 and .42 after two revisions of one coder's sheet; κ ≈ 0 in its first version), the coder guide was extended with decision rules for standardized accessories and decorative functional goods, and one coder's labels were revised after feedback on specific items. Because that feedback used these items, they are not validation data. The remaining 100 (P101–P200) were coded with the extended guide; the coders were instructed to work independently and without the LLM labels. [AUTHORS TO CONFIRM: whether the qualification quiz was completed and how independence was ensured.] Coder agreement was 97% for search versus experience (κ = .926, 95% CI .83–1.00) and 94% for hedonic versus utilitarian (κ = .855, CI .73–.95); 91 products had identical labels on both dimensions. Nine disagreements (five hair- or beard-care products, one beard trimmer, one set of chalkboard tags, one adhesive tape, one vacuum cleaner) were resolved jointly; The decision rules were set after the calibration round and the adjudication rules after seeing the disagreements, which we report as a limitation.

Against the consensus, the LLM labels agreed on 92.0% of products for search versus experience (κ = .820, CI .69–.93) and 90.0% for hedonic versus utilitarian (κ = .758, CI .61–.89). Errors were one-sided: in 8 cases the LLM assigned experience where the coders said search (none in reverse), and in 8 cases hedonic where the coders said utilitarian (2 in reverse).

## C. Full estimates for all twelve combinations

Tobit (left-censored at 0; p in parentheses) and NB2 incidence rate ratios with 95% intervals, standard errors clustered by product. Model 1 omits the interaction; Model 2 adds gap × experience (the gap row is then the effect for search goods). Controls as in the main text.

| Prompt | LLM | Goods labels | Tobit M1 gap | Tobit M2 gap | Tobit M2 gap × exp | NB2 M1 gap IRR | NB2 M2 gap IRR | NB2 M2 gap × exp IRR |
|---|---|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | category | 0.98 (.014) | 1.28 (.026) | -0.59 (.404) | 1.26 1.10–1.44 | 1.25 1.03–1.50 | 1.02 0.79–1.31 |
| ours | Llama 3.3 70B | category | 0.82 (.040) | 1.38 (.025) | -1.06 (.123) | 1.24 1.08–1.42 | 1.36 1.11–1.66 | 0.82 0.65–1.03 |
| ours | GPT-4.1 nano | category | 0.90 (.010) | 1.45 (.007) | -1.06 (.131) | 1.22 1.08–1.38 | 1.29 1.08–1.54 | 0.90 0.72–1.14 |
| original | Claude Haiku 5.5 | category | 0.78 (.032) | 1.02 (.061) | -0.50 (.537) | 1.20 1.03–1.40 | 1.25 1.00–1.56 | 0.93 0.71–1.22 |
| original | Llama 3.3 70B | category | 0.84 (.041) | 1.34 (.026) | -1.01 (.165) | 1.28 1.11–1.49 | 1.36 1.12–1.64 | 0.89 0.69–1.14 |
| original | GPT-4.1 nano | category | 0.45 (.180) | 0.71 (.158) | -0.54 (.439) | 1.21 1.05–1.38 | 1.19 0.97–1.46 | 1.03 0.79–1.34 |
| ours | Claude Haiku 5.5 | product | 1.01 (.012) | 1.33 (.012) | -0.82 (.291) | 1.28 1.12–1.46 | 1.30 1.11–1.53 | 0.95 0.73–1.22 |
| ours | Llama 3.3 70B | product | 0.81 (.040) | 1.03 (.054) | -0.51 (.440) | 1.25 1.09–1.43 | 1.35 1.13–1.60 | 0.80 0.65–1.00 |
| ours | GPT-4.1 nano | product | 0.91 (.009) | 1.11 (.016) | -0.49 (.474) | 1.23 1.09–1.39 | 1.29 1.11–1.49 | 0.88 0.70–1.11 |
| original | Claude Haiku 5.5 | product | 0.81 (.025) | 1.05 (.031) | -0.61 (.487) | 1.23 1.07–1.43 | 1.31 1.10–1.57 | 0.83 0.64–1.07 |
| original | Llama 3.3 70B | product | 0.83 (.042) | 1.03 (.053) | -0.46 (.523) | 1.29 1.12–1.49 | 1.36 1.15–1.61 | 0.87 0.68–1.12 |
| original | GPT-4.1 nano | product | 0.47 (.167) | 0.61 (.169) | -0.39 (.577) | 1.22 1.07–1.40 | 1.23 1.04–1.46 | 0.98 0.76–1.27 |

WZH report Tobit Model 1 gap −0.650 (p = .428), Model 2 gap +4.345 (p = .014), gap × experience −7.239 (p < .001), and in their GPT-5-nano check +6.29 (p = .001) and −8.46 (p < .001). Scales differ: their Tobit intercepts (about −63 to −79) indicate far larger vote counts than ours (mean 0.89). Clustering by user instead of product changes the NB2 interaction p-value by at most about .01 in the combinations inspected.

## D. Zero-inflation diagnostics

For each of the twelve combinations we compared NB2 with a zero-inflated negative binomial (logit inflation on a constant and the experience dummy; same count-part covariates; log review age as exposure). In every case the inflation intercept diverged and the log-likelihood equals that of NB2 (difference at most 0.01; NB2 log-likelihoods −22,274.91 to −22,349.81). The implied probability of a structural zero is between 10⁻⁹¹ and 10⁻¹⁰⁷, and AIC favors NB2 by four points in every case. The model is therefore not identified beyond NB2 (a boundary solution, not a convergence failure). The full table is in `results/tables.md` of the replication package.

## E. Sensitivity to misclassified product labels

Against the two-coder consensus (100 products), the labels had sensitivity 1.00 (29/29) and specificity .89 (63/71) for experience goods, and sensitivity .92 (24/26) and specificity .89 (66/74) for hedonic goods. Because misclassifying a moderator can bias an interaction toward zero, we corrected the key estimates by regression calibration. In each of 120 draws, sensitivity and specificity were drawn from Beta posteriors (uniform prior), the true prevalence was backed out of the observed LLM share (Rogan–Gladen), and each product's expected true label, E[T | LLM label], replaced the LLM label in the Model 2 negative binomial regression and in the regression of the gap on the hedonic indicator. We report the median and range over the draws and estimates pooled with Rubin's rules, so that intervals reflect uncertainty about the error rates. The method assumes non-differential misclassification, equal error rates across categories, and a representative validation sample, none of which can be tested here; it is approximate for the log-linear model.

**Table E1. Gap × experience interaction and net gap effect for experience goods, before and after correction**

| Prompt | LLM | Gap × experience IRR, observed (95% CI) | Corrected: median (range over error-rate draws) | Corrected, pooled (95% CI) | Net gap IRR, corrected, pooled (95% CI) |
|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | 0.946 0.732–1.223 | 0.928 (0.888–0.938) | 0.924 0.636–1.343 | 1.206 0.879–1.656 |
| ours | Llama 3.3 70B | 0.805 0.649–0.999 | 0.745 (0.629–0.777) | 0.734 0.525–1.026 | 0.993 0.772–1.277 |
| ours | GPT-4.1 nano | 0.885 0.704–1.112 | 0.847 (0.770–0.868) | 0.840 0.599–1.179 | 1.082 0.824–1.421 |
| original | Claude Haiku 5.5 | 0.826 0.638–1.069 | 0.771 (0.665–0.801) | 0.762 0.516–1.123 | 1.005 0.729–1.386 |
| original | Llama 3.3 70B | 0.868 0.675–1.115 | 0.825 (0.738–0.848) | 0.817 0.563–1.185 | 1.112 0.813–1.521 |
| original | GPT-4.1 nano | 0.979 0.756–1.267 | 0.971 (0.955–0.975) | 0.970 0.666–1.412 | 1.194 0.881–1.617 |

Corrected hedonic coefficients (regression of the gap on the hedonic indicator, median over draws) are −0.028 to −0.048, against observed −0.017 to −0.029 (observed and corrected values per combination: `results/sensitivity_rc.csv`). The pooled corrected intervals include zero in all six combinations (e.g., Claude, our prompt: observed −0.029 [−0.046, −0.011], corrected pooled −0.058 [−0.201, 0.085]).

The corrected interactions lie further below one (medians 0.745–0.971) than the observed ones, but every pooled interval includes one, and the corrected net gap effect for experience goods stays near or above one (0.99–1.21). The corrected hedonic coefficients are 1.6–1.7 times the observed ones, as the error rates imply. A likelihood-based (EM) variant for one combination (Claude, our prompt, 80 draws) gave similar experience estimates (interaction 0.960; net gap IRR 1.211) but a hedonic coefficient of −0.083, about three times the observed value; we attribute this to a poorly fitting Gaussian outcome model and do not use EM for the hedonic coefficient. Overall, the correction moves the interaction in the direction reported by WZH but does not make it detectable.
## F. Replication package

Review IDs, ratings and vote counts, LLM-inferred ratings, product labels (including validation labels), analysis code, and a reproduction script. Raw review text and metadata are not redistributed (Amazon Reviews 2023: Hou et al. 2024). [AUTHORS TO COMPLETE: anonymized repository link.]

## G. Rating-level and direction analyses (exploratory)

These analyses were added after the main results and are exploratory. The ensemble rating is the mean of the three LLMs' inferred ratings (one prompt at a time); the ensemble gap is its absolute difference from the author's rating. "More positive" is max(ensemble − author rating, 0) and "more negative" is max(author rating − ensemble, 0); both enter one NB2 regression with log length, an image indicator, and rating dummies (omitted within a rating stratum), log review age as offset, and standard errors clustered by product. Votes were winsorized at 76 (the 99.9th percentile). The ratio row is the ratio of the two directional IRRs (Wald test).

**Table G1. Our prompt (ensemble of three LLMs); IRR per one-star increase in the gap**

| Specification | N | IRR [95% CI] | p |
|---|---|---|---|
| **A. All reviews (ensemble gap)** | | | |
| Gap, all reviews | 25,750 | 1.29 [1.12, 1.48] | <.001 |
| Gap, votes winsorized at the 99.9th percentile | 25,750 | 1.24 [1.09, 1.41] | .001 |
| Gap, search goods (product labels) | 25,750 | 1.39 [1.16, 1.67] | <.001 |
| Gap × experience (product labels) | 25,750 | 0.86 [0.67, 1.11] | .243 |
| **B. Within author's star rating** | | | |
| Gap, 1-star reviews | 3,246 | 1.09 [0.77, 1.54] | .645 |
| Gap, 2-star reviews | 1,439 | 1.31 [0.72, 2.38] | .378 |
| Gap, 3-star reviews | 1,791 | 1.34 [1.06, 1.70] | .013 |
| Gap, 4-star reviews | 2,787 | 1.41 [1.07, 1.85] | .013 |
| Gap, 5-star reviews | 16,487 | 1.27 [1.05, 1.54] | .012 |
| **C. Direction of the disagreement (per star)** | | | |
| Text read as more positive than the rating | 25,750 | 1.00 [0.76, 1.31] | .994 |
| Text read as more negative than the rating | 25,750 | 1.35 [1.17, 1.56] | <.001 |
| Ratio more negative / more positive | 25,750 | 1.35 [1.02, 1.79] | .036 |
| 3-star only: more negative reading | 1,791 | 1.38 [1.09, 1.74] | .007 |
| 3-star only: more positive reading | 1,791 | 0.87 [0.48, 1.56] | .639 |
| 4-star only: more negative reading | 2,787 | 1.45 [1.10, 1.90] | .008 |
| 4-star only: more positive reading | 2,787 | 1.18 [0.61, 2.29] | .626 |

**Table G2. Original (WZH) prompt, direction of the disagreement (ensemble; IRR per star)**

| Specification | N | IRR [95% CI] | p |
|---|---|---|---|
| Text read as more positive than the rating | 25,683 | 0.90 [0.67, 1.23] | .520 |
| Text read as more negative than the rating | 25,683 | 1.39 [1.17, 1.65] | <.001 |
| Ratio more negative / more positive | 25,683 | 1.54 [1.12, 2.10] | .007 |
| 3-star only: more negative reading | 1,783 | 1.43 [1.09, 1.89] | .010 |
| 4-star only: more negative reading | 2,780 | 1.61 [1.18, 2.20] | .003 |

Both prompts show the same pattern. The ratio test is the only formal comparison of the directions (p = .036 and .007); no multiplicity correction was applied. For the original prompt the ensemble gap overall has IRR 1.28 [1.08, 1.51] (N = 25,683); by rating it is 0.95 (1 star), 1.28 (2), 1.35 (3), 1.52 (4), and 1.27 (5).
