# Do gaps between LLM-inferred and actual star ratings predict review helpfulness? A replication and extension with count models and three language models

*Draft for Marketing Letters, Replication Corner (limit: 4,000 words including abstract, text and references; at most three tables/figures — verify current rules before submission). Items marked [TODO] must be resolved before submission.*

## Abstract

Winter, Zacharias and Hartwig (2026) report that the gap between a large language model's (LLM) star-rating inference and the rating a reviewer actually gave predicts lower review helpfulness, especially for experience goods. We re-examine this claim with 25,783 Amazon reviews from four product categories, three LLMs from different families, and models designed for count outcomes. LLM-inferred ratings agree closely with authors' ratings (r = .89–.92). However, we do not find that larger gaps predict fewer helpful votes. In Tobit models that mirror the original specification and in negative binomial models, the gap is positively associated with helpful votes (incidence rate ratios 1.22–1.36), consistently across all three LLMs, whereas the gap-by-experience-good interaction is not significant. A zero-inflated model collapses to the negative binomial, so excess zeros do not drive the results. Review length and images remain the strongest predictors. The original mediation evidence comes from an experiment we do not replicate. Our results therefore suggest that the observational link between LLM–star disagreement and helpfulness is sensitive to sample, outcome model and product coding, and should be interpreted cautiously.

**Keywords:** large language models, online reviews, review helpfulness, sentiment analysis, replication, count models

## 1. Introduction

Helpful votes are widely used to surface useful reviews, so predicting helpfulness soon after a review is posted is valuable for platforms (Mudambi and Schuff 2010; Ceylan, Diehl and Proserpio 2024). [TODO: confirm that these two sources support the platform-ranking claim, or cite WZH's sources for it.] Winter, Zacharias and Hartwig (2026; hereafter WZH) propose a lightweight predictor: ask a general-purpose LLM to infer the star rating from review text alone and measure the absolute deviation from the reviewer's actual rating. Across 28,900 reviews from a consumer platform, WZH find that this deviation predicts lower helpfulness for experience goods (Tobit interaction β = −7.239, p < .001), and an experiment with 1,063 participants shows that the deviation operates through readers' own misreading of the intended rating. The finding is attractive because it requires no training data or fine-tuning.

Three features of the original study make a replication informative. First, the helpfulness outcome is a non-negative count with a large mass at zero (54% in WZH), which was analyzed with a Tobit model that assumes a normally distributed latent variable; count models are the standard alternative (Cameron and Trivedi 2013). Second, the original analysis relies on one LLM version, and WZH themselves list this as a limitation. Third, the original product classification (search vs. experience, hedonic vs. utilitarian) covers 12 products.

We therefore ask: (1) Does an LLM's rating inference agree with authors' ratings in a different sample, and does agreement differ for hedonic goods? (2) Does the LLM–star gap predict lower helpfulness, and is this more pronounced for experience goods, when the same outcome is analyzed with Tobit and with count models? (3) Do conclusions depend on which LLM produces the inference? Our contribution is a conceptual replication with a larger, publicly available data source, three LLMs from different families, count models, and an explicit zero-inflation diagnosis. We do not replicate WZH's experiment (Study 3), so we cannot speak to the proposed mechanism.

## 2. Theoretical background and hypotheses

**Why a text–rating gap might matter.** Reviews help customers by reducing information asymmetry before purchase (Kübler et al. 2024), and they are most useful when they are easy to process and internally consistent (WZH, citing Mudambi, Schuff and Zhang 2014). A review whose text conveys a different evaluation than its star rating forces readers to reconcile two signals and raises the cost of extracting the intended message. WZH reason that an LLM's disagreement with the author's own rating is a cheap proxy for such inconsistency: text that is ambiguous or incoherent for a model is also likely to be difficult for readers (WZH, citing Liu et al. 2023). If readers vote for reviews they find helpful, a larger gap should therefore predict fewer helpful votes.

**Moderation by product type.** The value of consistent information should depend on how hard a product is to evaluate before purchase. Search goods have core qualities that can be assessed from seller information, whereas experience goods must be experienced first (Nelson 1970; Hsieh, Chiu and Chiang 2005). Readers of reviews for experience goods rely more heavily on reviews and, according to WZH, should be more dependent on cognitively easy and consistent information. This yields the prediction that the penalty of a large gap is stronger for experience goods. Earlier work also shows that review characteristics matter differently across product types (Mudambi and Schuff 2010 [TODO: verify that their finding on rating extremity by product type is described accurately before citing it for this claim]).

**LLM accuracy and emotionality.** AI systems are often expected to perform worse when emotions are salient, as in hedonic consumption (Longoni and Cian 2022; Xiao and Kumar 2021, both cited by WZH). WZH test whether the gap is larger for hedonic goods and find the opposite, which they attribute to more explicitly evaluative language in hedonic reviews. We replicate this test with our own category-level classification.

**Hypotheses.** Because we conceptually replicate WZH, we state their predictions as the confirmatory benchmark.

- *H1 (original):* A larger gap between the author's rating and the LLM-inferred rating predicts fewer helpful votes.
- *H2 (original):* The negative association in H1 is stronger for experience goods than for search goods.
- *H3 (original, Study 1):* The gap is smaller for reviews of hedonic goods than for reviews of utilitarian goods.

We add two robustness questions that go beyond the original. *RQ1:* Do conclusions about H1–H3 change when the LLM is replaced by models from other families? A gap defined by a single model could reflect that model's idiosyncrasies. *RQ2:* Do conclusions change when helpful votes are modeled as counts rather than with a Tobit model that assumes a normal latent variable? Count models are the usual choice for non-negative integer outcomes with a large mass at zero (Cameron and Trivedi 2013), and a zero-inflated specification allows us to check whether the abundance of zeros requires a separate process.

**A competing account (post hoc).** Our pilot analysis of 2,000 reviews, which preceded the main analysis, suggested that the gap might be positively rather than negatively associated with votes. One possible mechanism is that reviews that are hard to classify are often mixed or moderate reviews, and readers may find balanced reviews more credible and informative than uniformly extreme ones. We treat this as an exploratory explanation, not a hypothesis, and do not test it directly with our data.

## 3. Data and measures

**Sample.** We use the Amazon Reviews 2023 data (Hou et al. 2024). The raw category files are sorted by user, so we read random byte windows from four category files and keep every review of users fully contained in a window. Product categories were chosen to approximate WZH's 2 × 2 design: Cell Phones and Accessories (search, hedonic), Office Products (search, utilitarian), Beauty and Personal Care (experience, hedonic) and Home and Kitchen (experience, utilitarian). **This category-level assignment is ours and is coarser than WZH's product-level coding based on Kübler et al. (2024).** We cap reviews per user at five, draw 6,500 reviews per category, drop reviews without text and duplicates, and obtain 25,783 reviews (25,751 for one LLM after 32 invalid responses). Because windows over-represent prolific reviewers and reviews cluster within users, we cluster standard errors at the product (as WZH) and, in a robustness check, at the user level. [TODO: report sampling code and review IDs in the replication package.]

**Helpfulness.** The outcome is the number of helpful votes. It is highly skewed (mean 0.89, SD 10.1, maximum 1,130) and 78.7% of reviews have zero votes.

**LLM rating inference and gap.** Each LLM received only the review text and was asked to return the star rating (1–5) it believes the author gave (temperature 0, JSON output). The gap is the absolute difference between the author's rating and the inferred rating. We use three models accessed through a common API: Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano. **We wrote our own prompt; the original prompt is in WZH's technical appendix and [TODO: consult it and either align the wording or document the differences].**

**Controls.** As in WZH: review length (characters), rating dummies (one star as reference), an image indicator, and review age in days. We lack their video indicator and product-level review count. Experience good is a dummy for Beauty and Home and Kitchen.

**Models.** (a) Tobit, left-censored at zero, with standard errors clustered by product, mirroring WZH. (b) Negative binomial (NB2) with log review age as exposure offset and the same controls (length enters in logs); the dispersion parameter is estimated from an auxiliary regression. (c) A zero-inflated negative binomial (ZINB) as a diagnostic. All code and the replication package are available at [TODO: repository link]; raw review text is not redistributed.

**Preregistration.** The study was not preregistered. We first analyzed a 2,000-review pilot, and the design of the main analysis followed that pilot. We report all models we estimated for the main question.

## 4. Results

### 4.1 LLM inference of star ratings (Study 1 analogue)

Table 1 shows that all three LLMs reproduce authors' ratings well. Correlations range from .889 to .923, exact agreement from 64.6% to 79.0%, and the share of reviews that differ by two or more stars from 3.6% to 4.0%. These figures are at least as good as in WZH (r = .763, about 37% misclassified). The gap is largest for three-star reviews and smallest for one- and five-star reviews, which is intuitive but differs from WZH's finding that one-star reviews deviate most. WZH also report smaller gaps for hedonic goods (β = −.058, p < .001). In our data the hedonic coefficient is close to zero for every LLM (−.010, p = .25; +.003, p = .72; −.004, p = .66), so H3 is not supported in our data, although our hedonic coding is only category-level.

**Table 1. Agreement between authors' and LLM-inferred ratings**

| LLM | N | r | Exact match | Off by ≥2 stars | Hedonic coefficient on gap (p) |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | 25,783 | .907 | 70.7% | 3.6% | −.010 (.25) |
| Llama 3.3 70B | 25,783 | .923 | 79.0% | 3.8% | +.003 (.72) |
| GPT-4.1 nano | 25,751 | .889 | 64.6% | 4.0% | −.004 (.66) |

*Note.* OLS of the gap on a hedonic indicator, rating dummies, length and age, standard errors clustered by product. The gap is correlated across LLMs at .63–.76.

### 4.2 Gap and helpfulness (Study 2 analogue)

Table 2 presents the main results. In the Tobit models that mirror WZH, the gap has a **positive** coefficient in Model 1 (0.82–0.98, all p ≤ .04) and in Model 2, where it represents the effect for search goods (1.28–1.45, p ≤ .026). The sign agrees with WZH's Model 2 coefficient for search goods (+4.345), although the scale differs because our counts are much smaller. The gap-by-experience interaction is negative, as in WZH (−0.59 to −1.07), but never significant (p = .12–.40).

H1 is therefore not supported: the association is positive, not negative. The negative binomial models lead to the same conclusion. A one-star larger gap is associated with 22–26% more helpful votes (IRR 1.22–1.26, p ≤ .003, Model 1). With the interaction included, the gap effect for search goods is 1.25–1.36 and the interaction IRR is 1.02 (Claude), 0.82 (Llama) and 0.90 (GPT), none significant (p = .09–.88), so H2 is not supported. The sign of the interaction differs across LLMs, which signals that the moderation is not robust (RQ1), while the main association is stable across LLMs and across Tobit and count models (RQ1, RQ2). Clustering by user instead of product leaves the interaction unchanged (e.g., IRR = 0.820, 95% CI [0.650, 1.034] for Llama).

Controls behave as in WZH. Longer reviews and reviews with images receive more helpful votes (length IRR ≈ 2.7 per log unit, images IRR ≈ 5.4–5.6), and older reviews accumulate more votes in Tobit models.

**Table 2. Gap and helpful votes**

| | Claude Haiku 5.5 | Llama 3.3 70B | GPT-4.1 nano |
|---|---|---|---|
| *Tobit, Model 1:* gap | 0.98 (p = .014) | 0.82 (p = .04) | 0.90 (p = .01) |
| *Tobit, Model 2:* gap (search goods) | 1.28 (p = .026) | 1.38 (p = .025) | 1.45 (p = .007) |
| *Tobit, Model 2:* gap × experience | −0.59 (p = .40) | −1.07 (p = .12) | −1.05 (p = .13) |
| *NB2, Model 1:* gap, IRR [95% CI] | 1.26 [1.10, 1.44] | 1.24 [1.08, 1.42] | 1.22 [1.08, 1.38] |
| *NB2, Model 2:* gap (search goods), IRR | 1.25 [1.03, 1.50] | 1.36 [1.11, 1.66] | 1.29 [1.08, 1.54] |
| *NB2, Model 2:* gap × experience, IRR | 1.02 [0.79, 1.31] | 0.82 [0.65, 1.03] | 0.90 [0.72, 1.14] |

*Note.* WZH (Tobit, Model 2): gap +4.345 (p = .014); gap × experience −7.239 (p < .001). Controls: length, rating dummies, image indicator, review age; NB2 uses a log-age offset. Standard errors clustered by product.

### 4.3 Excess zeros

Because about 79% of reviews have no votes, we compared NB2 with a ZINB whose zero-inflation component depends on a constant and the experience dummy. For all three LLMs the log-likelihoods are identical to the second decimal (e.g., −22,339.85 for both models for Claude), the implied probability of a structural zero is below 10⁻⁹⁴, and AIC favors NB2 by four points. The inflation component is not identified, and the zero-inflated model collapses to NB2. The zeros are thus consistent with the negative binomial distribution, and the count-part gap IRR equals that of the NB2 fitted by maximum likelihood in the same comparison (1.235 vs. 1.235 for Claude; Table 2 uses a GLM NB2 with moment-based dispersion, hence slightly different values).

## 5. Discussion

**What we replicate.** LLMs can infer star ratings from text with high accuracy, and the gap carries information about helpfulness. In addition, the pattern of control variables (length, images, age) matches the original study, and the positive coefficient of the gap for search goods in WZH's Model 2 is reproduced in sign and significance.

**What we do not replicate.** (i) Larger gaps do not predict lower helpfulness in our observational data; the association is positive and robust across three LLMs, outcome models and clustering choices. (ii) The proposed stronger penalty for experience goods is not supported: the interaction is insignificant, and in the count model its sign varies by LLM. (iii) Hedonic goods do not show smaller gaps.

**Possible explanations (not tested).** Reviews with large gaps are disproportionately mixed or moderate reviews, which may be read as balanced and informative, producing more votes even though an algorithm finds them harder to classify. Differences in sample (Amazon 2023 versus a scrape of first-page results for 12 search terms), categories, and the outcome model may also matter. WZH's experiment isolates readers' perceived inconsistency in a controlled setting; our observational result does not contradict that mechanism but shows that it does not translate into a negative observational association in our data.

**Limitations.** First, the study was not preregistered and followed a pilot. Second, product classification is category-level and ours, so the experience and hedonic tests are weaker than in the original. Third, windows-based sampling over-represents prolific reviewers; clustering and a per-user cap mitigate but do not remove this. Fourth, our prompt differs from the original, and the LLMs are different models. Fifth, helpful votes depend on how many readers see a review, which we cannot observe (see Kübler et al. 2024 for discussion of readers' limited attention; [TODO: verify]). Sixth, Tobit assumes a normal latent variable for a count with 79% zeros; the negative binomial agrees on the main result, but both are observational. Finally, we do not replicate the experiment.

**Implications.** For platforms, the practical value of an LLM–star gap as a cheap helpfulness predictor is unclear: its association with votes is positive here, and length and images are far stronger predictors. For researchers, conclusions about LLM–human disagreement should be tested with count models and more than one LLM, because the gap itself is only moderately correlated across models (.63–.76) even when conclusions agree.

## References

Brandes, L., Godes, D., & Mayzlin, D. (2022). Extremity bias in online reviews: The role of attrition. *Journal of Marketing Research*, 59, 675–695. [TODO: cite only if used in final text]

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. [TODO: verify edition details]

Ceylan, G., Diehl, K., & Proserpio, D. (2024). Words meet photos: When and why photos increase review helpfulness. *Journal of Marketing Research*, 61, 5–26.

Hsieh, Y.-C., Chiu, H.-C., & Chiang, M.-Y. (2005). Maintaining a committed online customer: A study across search-experience-credence products. *Journal of Retailing*, 81, 75–82.

Liu, A., Wu, Z., Michael, J., Suhr, A., West, P., Koller, A., Swayamdipta, S., Smith, N., & Choi, Y. (2023). We're afraid language models aren't modeling ambiguity. In *Proceedings of EMNLP 2023* (pp. 790–807). Association for Computational Linguistics.

Longoni, C., & Cian, L. (2022). Artificial intelligence in utilitarian vs. hedonic contexts: The "word-of-machine" effect. *Journal of Marketing*, 86, 91–108.

Mudambi, S. M., Schuff, D., & Zhang, Z. (2014). Why aren't the stars aligned? An analysis of online review content and star ratings. *2014 47th Hawaii International Conference on System Sciences*, 3139–3147.

Nelson, P. (1970). Information and consumer behavior. *Journal of Political Economy*, 78, 311–329. [TODO: verify]

Xiao, L., & Kumar, V. (2021). Robotics for customer service: A useful complement or an ultimate substitute? *Journal of Service Research*, 24, 9–29.

Hou, Y., Li, J., He, Z., Yan, A., Chen, X., & McAuley, J. (2024). Bridging language and items for retrieval and recommendation. arXiv:2403.03952.

Kübler, R. V., Lobschat, L., Welke, L., & van der Meij, H. (2024). The effect of review images on review helpfulness: A contingency approach. *Journal of Retailing*, 100, 5–23.

Mudambi, S., & Schuff, D. (2010). Research note: What makes a helpful online review? A study of customer reviews on Amazon.com. *MIS Quarterly*, 34, 185–200.

Winter, C. G. H., Zacharias, N. A., & Hartwig, M. (2026). Using LLMs as sentiment analyzers to predict review helpfulness: First insights to open the black box. *Marketing Letters*, 37, Article 30. https://doi.org/10.1007/s11002-026-09824-7
