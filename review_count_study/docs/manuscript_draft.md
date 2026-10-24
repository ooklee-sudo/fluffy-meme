# Do disagreements between LLM-inferred and actual star ratings predict review helpfulness? A replication and extension with count models and three language models

*Draft for* Marketing Letters *(Replication Corner; limit: 4,000 words including abstract, text, and references; at most three tables or figures — verify current rules before submission). Items marked [TODO] must be resolved before submission.*

## Abstract

Winter, Zacharias, and Hartwig (2026) report that the gap between a large language model's (LLM) inference of a review's star rating and the rating its author actually gave predicts lower helpfulness, particularly for experience goods. We revisit this claim using 25,783 Amazon reviews from four product categories, three LLMs from different model families, each run with our own prompt and with the original prompt, and models suited to count outcomes. The LLMs recover authors' ratings closely (r = .89–.92), yet larger gaps do not predict fewer helpful votes. In Tobit models that mirror the original specification and in negative binomial models, the gap is positively associated with helpful votes (incidence rate ratios of 1.19–1.36 across six model–prompt combinations); the sign is stable, whereas statistical significance varies with the LLM and prompt in some specifications. The gap-by-experience-good interaction is not significant in any combination. A zero-inflated specification collapses to the negative binomial, so excess zeros do not explain the pattern. Review length and images remain the strongest predictors. We do not replicate the original experiment and therefore cannot assess the proposed mechanism. The observational link between LLM–star disagreement and helpfulness appears sensitive to sample, outcome model, and product coding, and it should be interpreted with caution.

**Keywords:** large language models, online reviews, review helpfulness, sentiment analysis, replication, count models

## 1. Introduction

Platforms rely on helpful votes to surface useful reviews, which makes it valuable to predict helpfulness soon after a review is posted (Mudambi and Schuff 2010; Ceylan, Diehl, and Proserpio 2024). [TODO: confirm that these sources support the platform-ranking claim, or cite the sources used by Winter et al. for it.] Winter, Zacharias, and Hartwig (2026; hereafter WZH) propose a lightweight predictor. A general-purpose LLM is asked to infer the star rating from the review text alone, and the absolute deviation from the rating the reviewer actually chose serves as the predictor. Analyzing 28,900 reviews from a consumer platform, WZH find that this deviation predicts lower helpfulness for experience goods (Tobit interaction β = −7.239, p < .001). An experiment with 1,063 participants further indicates that the deviation works through readers' own misjudgment of the intended rating. The result is appealing because it requires neither training data nor fine-tuning.

Three features of the original study make a replication informative. First, helpfulness is a non-negative count with a large mass at zero (54% of reviews in WZH), yet it was analyzed with a Tobit model that presumes a normally distributed latent variable; count models are the conventional alternative (Cameron and Trivedi 2013). Second, the analysis rests on a single LLM version, which the authors acknowledge as a limitation. Third, the product classification covers twelve products.

We therefore ask whether an LLM's rating inference agrees with authors' ratings in a different sample, and whether agreement differs for hedonic goods; whether the LLM–star gap predicts lower helpfulness, and more strongly for experience goods, once the same outcome is analyzed with Tobit and with count models; and whether these conclusions depend on the LLM that generates the inference. Our contribution is a conceptual replication that draws on a larger, publicly available data source, three LLMs from different families, count-data models, and an explicit diagnosis of zero inflation. Because we do not replicate WZH's experiment (Study 3), we cannot speak to the mechanism they propose.

## 2. Theoretical background and hypotheses

**Why a text–rating gap might matter.** Reviews help customers by reducing information asymmetry before purchase (Kübler et al. 2024), and they are most useful when they are easy to process and internally consistent (WZH, citing Mudambi, Schuff, and Zhang 2014). When the text of a review conveys a different evaluation from its star rating, readers must reconcile two signals, which raises the cost of extracting the intended message. WZH reason that an LLM's disagreement with the author's own rating offers a cheap proxy for this kind of inconsistency: text that is ambiguous or incoherent to a model is likely to be difficult for readers as well (WZH, citing Liu et al. 2023). If readers vote for reviews they find helpful, a larger gap should accordingly predict fewer helpful votes.

**Moderation by product type.** The value of consistent information should depend on how hard a product is to evaluate before purchase. Search goods have core qualities that can be assessed from seller-provided information, whereas experience goods must be consumed first (Nelson 1970; Hsieh, Chiu, and Chiang 2005). Readers who research experience goods depend more on consistent, easily processed information (WZH), which implies that the penalty for a large gap should be stronger for experience goods. Prior work also shows that review characteristics matter differently across product types (Mudambi and Schuff 2010). [TODO: verify that their finding on rating extremity by product type is described accurately before citing it for this claim.]

**LLM accuracy and emotionality.** AI systems are often expected to perform worse where emotions are salient, as in hedonic consumption (Longoni and Cian 2022; Xiao and Kumar 2021, both cited by WZH). WZH test whether the gap is larger for hedonic goods and find the opposite, which they attribute to the more explicitly evaluative language of hedonic reviews. We repeat this test with our own category-level classification.

**Hypotheses.** Because we conceptually replicate WZH, we adopt their predictions as the confirmatory benchmark.

- *H1 (original).* A larger gap between the author's rating and the LLM-inferred rating predicts fewer helpful votes.
- *H2 (original).* The negative association in H1 is stronger for experience goods than for search goods.
- *H3 (original, Study 1).* The gap is smaller for reviews of hedonic goods than for reviews of utilitarian goods.

We add two robustness questions that go beyond the original study. RQ1 asks whether conclusions about H1–H3 change when the LLM is replaced by models from other families or when our prompt is replaced by the original one, since a gap defined by a single model and prompt could reflect their idiosyncrasies. RQ2 asks whether conclusions change when helpful votes are modeled as counts rather than with a Tobit model. Count models are the usual choice for non-negative integer outcomes with many zeros (Cameron and Trivedi 2013), and a zero-inflated specification lets us check whether the abundance of zeros requires a separate generating process.

**A competing account (post hoc).** A pilot analysis of 2,000 reviews, conducted before the main analysis, suggested that the gap may be associated positively, not negatively, with votes. One possible mechanism is that reviews that are difficult to classify are often mixed or moderate, and readers may find balanced reviews more credible and informative than uniformly extreme ones. We treat this as an exploratory explanation rather than a hypothesis and do not test it directly.

## 3. Data and measures

**Sample.** We use the Amazon Reviews 2023 data (Hou et al. 2024). The raw category files are sorted by user, so we read random byte windows from four category files and keep every review of the users fully contained in a window. The categories approximate WZH's two-by-two design: Cell Phones and Accessories (search, hedonic), Office Products (search, utilitarian), Beauty and Personal Care (experience, hedonic), and Home and Kitchen (experience, utilitarian). **This category-level assignment is ours, and it is coarser than WZH's product-level coding, which draws on Kübler et al. (2024).** We cap reviews per user at five, draw 6,500 reviews per category, and remove reviews without text as well as duplicates. The final sample contains 25,783 reviews (25,711–25,783 depending on the LLM and prompt, after dropping responses that could not be parsed as a rating). Because the windows over-represent prolific reviewers and reviews cluster within users, we cluster standard errors by product, as in WZH, and by user in a robustness check. [TODO: add sampling code and review IDs to the replication package.]

**Helpfulness.** The outcome is the number of helpful votes. It is highly skewed (mean = 0.89, SD = 10.1, maximum = 1,130), and 78.7% of reviews have no votes.

**LLM rating inference and gap.** Each LLM received only the review text and returned the star rating (1–5) it believed the author had given (temperature 0, JSON output). The gap is the absolute difference between the author's rating and the inferred rating. We use three models accessed through a common interface: Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano. We run each LLM with two prompts. Our own prompt returns JSON (temperature 0). The second is the original system prompt reported in the supplementary material of WZH: "You are a classifier. Your job is to tell me the star rating of a product review. Treat every prompt as if it were a review. Answer only with the corresponding number between 1 and 5." As in the original, the review text is sent unwrapped as the user message and the temperature is 0.2. The supplement lists the three sentences separately, so we joined them with spaces; the original separator is unknown. WZH used OpenAI models, whereas our three models are other LLMs, and the original date of access (December 2025) and model versions cannot be matched.

**Controls.** Following WZH, we control for review length in characters, rating dummies (one star as the reference), an image indicator, and review age in days. We lack their video indicator and a product-level review count. Experience good is a dummy for Beauty and Home and Kitchen.

**Models.** We estimate (a) a Tobit model, left-censored at zero, with standard errors clustered by product, mirroring WZH; (b) a negative binomial model (NB2) with log review age as an exposure offset and the same controls, with review length entered in logs and the dispersion parameter estimated from an auxiliary regression; and (c) a zero-inflated negative binomial (ZINB) model as a diagnostic. Code and the replication package are available at [TODO: repository link]; raw review text is not redistributed.

**Preregistration and process.** The study was not preregistered. We first analyzed a 2,000-review pilot, and the design of the main analysis followed it. We report every model estimated for the main question. [TODO: add a statement on the use of AI tools in analysis and drafting, following the journal's current policy.]

## 4. Results

### 4.1 LLM inference of star ratings (Study 1 analogue)

All three LLMs reproduce authors' ratings well (Table 1). Correlations range from .889 to .923, exact agreement from 64.6% to 79.0%, and the share of reviews differing by two or more stars from 3.6% to 4.0%. These figures are at least as favorable as those in WZH (r = .763, about 37% misclassified). With the original prompt, agreement is similar (r = .888–.921; exact agreement 67.6–78.3%; two or more stars apart in 3.0–3.8% of reviews). With our prompt the gap is largest for three-star reviews, which is intuitive but differs from WZH, where one-star reviews deviate most. With the original prompt the pattern depends on the LLM: the mean gap of one-star reviews ranges from 0.17 (Llama) to 0.54 (GPT-4.1 nano), and equals that of three-star reviews (0.53) only for GPT-4.1 nano, so the star-by-star profile in WZH is not consistently reproduced. WZH also report smaller gaps for hedonic goods (β = −.058, p < .001). In our data the hedonic coefficient is near zero for every LLM and prompt (our prompt: −.010, p = .25; +.003, p = .72; −.004, p = .66; original prompt: −.006, p = .49; −.002, p = .79; −.005, p = .61), so H3 is not supported, although our hedonic coding is only category-level.

**Table 1. Agreement between authors' and LLM-inferred ratings**

| LLM | N | r | Exact match | Off by ≥2 stars | Hedonic coefficient on gap (p) |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | 25,783 | .907 | 70.7% | 3.6% | −.010 (.25) |
| Llama 3.3 70B | 25,783 | .923 | 79.0% | 3.8% | +.003 (.72) |
| GPT-4.1 nano | 25,751 | .889 | 64.6% | 4.0% | −.004 (.66) |

*Note.* OLS of the gap on a hedonic indicator, rating dummies, length, and age, with standard errors clustered by product. The gap correlates across LLMs at .63–.76.

### 4.2 Gap and helpfulness (Study 2 analogue)

Table 2 reports the main results. In the Tobit models that mirror WZH, the gap has a positive coefficient in Model 1 (0.82–0.98, all p ≤ .04) and in Model 2, where it captures the effect for search goods (1.28–1.45, p ≤ .026). The sign agrees with WZH's Model 2 coefficient for search goods (+4.345), although the scale differs because our counts are much smaller. The gap-by-experience interaction is negative, as in WZH (−0.59 to −1.07), but never significant (p = .12–.40). H1 is therefore not supported: the association is positive, not negative.

The negative binomial models point the same way. A one-star larger gap is associated with 22–26% more helpful votes (IRR = 1.22–1.26, p ≤ .003, Model 1). With the interaction included, the gap effect for search goods ranges from 1.25 to 1.36, and the interaction IRR is 1.02 (Claude), 0.82 (Llama), and 0.90 (GPT), none significant (p = .09–.88), so H2 is not supported. The sign of the interaction varies across LLMs, which indicates that the moderation is not robust (RQ1), whereas the main association is stable across LLMs and across Tobit and count models (RQ1, RQ2). Clustering by user instead of product leaves the interaction essentially unchanged (e.g., IRR = 0.820, 95% CI [0.650, 1.034] for Llama).

Control variables behave as in WZH. Longer reviews and reviews with images attract more helpful votes (length IRR ≈ 2.7 per log unit; image IRR ≈ 5.4–5.6), and older reviews accumulate more votes in the Tobit models.

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

With the original prompt (Table 3), the sign of the gap effect and the null interaction are unchanged. The NB2 Model 1 gap IRR is 1.21–1.28 (p ≤ .015) for all three LLMs. The Tobit gap coefficient in Model 2 remains significant for Claude (p = .044) and Llama (p = .026) but not for GPT-4.1 nano (0.71, p = .16), for which the NB2 Model 2 gap effect is also marginal (IRR = 1.19, p = .097). The interaction stays insignificant (Tobit p = .16–.46; NB2 p = .34–.83). What varies with the LLM and prompt is therefore the significance of the gap effect, not its sign.

**Table 3. Gap and helpful votes with the original WZH prompt**

| | Claude Haiku 5.5 | Llama 3.3 70B | GPT-4.1 nano |
|---|---|---|---|
| *Tobit, Model 1:* gap | 0.82 (p = .024) | 0.84 (p = .04) | 0.45 (p = .18) |
| *Tobit, Model 2:* gap (search goods) | 1.13 (p = .044) | 1.34 (p = .026) | 0.71 (p = .16) |
| *Tobit, Model 2:* gap × experience | −0.60 (p = .46) | −1.01 (p = .16) | −0.54 (p = .44) |
| *NB2, Model 1:* gap, IRR [95% CI] | 1.21 [1.04, 1.40] | 1.28 [1.11, 1.49] | 1.21 [1.05, 1.38] |
| *NB2, Model 2:* gap (search goods), IRR | 1.25 [1.00, 1.57] | 1.36 [1.12, 1.64] | 1.19 [0.97, 1.46] |
| *NB2, Model 2:* gap × experience, IRR | 0.92 [0.70, 1.22] | 0.89 [0.69, 1.14] | 1.03 [0.79, 1.34] |

*Note.* Same specification as Table 2. System prompt as reported in WZH's supplementary material, temperature 0.2, review text sent unwrapped.

### 4.3 Excess zeros

Because about 79% of reviews have no votes, we compared NB2 with a ZINB model whose zero-inflation component depends on a constant and the experience dummy. For all three LLMs the log-likelihoods of the two models are identical to the second decimal (e.g., −22,339.85 for both models for Claude), the implied probability of a structural zero falls below 10⁻⁹⁴, and AIC favors NB2 by four points. The inflation component is not identified, and the zero-inflated model collapses to NB2. The zeros are thus consistent with the negative binomial distribution itself. The count-part gap IRR equals that of the NB2 fitted by maximum likelihood in the same comparison (1.235 in both for Claude); Table 2 uses a GLM NB2 with moment-based dispersion and therefore shows slightly different values.

## 5. Discussion

**What we replicate.** LLMs infer star ratings from text with high accuracy, and the gap carries information about helpfulness. The pattern of control variables (length, images, age) matches the original study, and the positive gap coefficient for search goods in WZH's Model 2 is reproduced in sign and, for most specifications, significance. This is less surprising than it may seem: WZH's own robustness check with GPT-5-nano (Web Appendix 4) also yields a positive coefficient for search goods (+6.29, p = .001), together with a negative interaction (−8.46, p < .001). The negative association that the original abstract describes is thus confined to the interaction with experience goods.

**What we do not replicate.** First, larger gaps do not predict lower helpfulness in our observational data; the association is positive and holds across three LLMs, two outcome models, and both clustering choices. Second, the stronger penalty proposed for experience goods is not supported: the interaction is insignificant, and in the count model its sign varies by LLM. Third, hedonic goods do not show smaller gaps.

**Possible explanations (untested).** Reviews with large gaps are disproportionately mixed or moderate, and readers may regard such reviews as balanced and informative even though a classifier finds them harder to label, which would yield more votes. Differences in sample (Amazon 2023 versus a scrape of first-page results for twelve search terms), categories, and the outcome model may also matter. In particular, WZH's search–experience contrast rests on twelve products (383 product clusters in the Tobit model), so product-specific features could contribute to their interaction; we cannot test this. WZH's experiment isolates readers' perceived inconsistency in a controlled setting. Our observational result does not contradict that mechanism, but it shows that the mechanism need not translate into a negative observational association.

**Limitations.** The study was not preregistered and followed a pilot. Product classification is category-level and ours, which weakens the experience-good and hedonic tests relative to the original. Window-based sampling over-represents prolific reviewers; clustering and a per-user cap mitigate this but do not remove it. Our main prompt differs from the original; with the original prompt (separator unknown) the sign and the null interaction are unchanged, but significance of the gap effect varies by LLM, and all of our LLMs differ from those WZH used. Helpful votes depend on how many readers see a review, which we cannot observe (see Kübler et al. 2024 for the role of readers' limited attention [TODO: verify]). Tobit assumes a normal latent variable for a count with 79% zeros; the negative binomial agrees on the main result, but both approaches are observational. Finally, we do not replicate the experiment.

**Implications.** For platforms, the practical value of an LLM–star gap as an inexpensive helpfulness predictor is unclear: its association with votes is positive here, and length and images are far stronger predictors. For researchers, conclusions about LLM–human disagreement should be tested with count models and with more than one LLM, because the gap itself correlates only moderately across models (.63–.76) even when conclusions agree.

## References

Brandes, L., Godes, D., & Mayzlin, D. (2022). Extremity bias in online reviews: The role of attrition. *Journal of Marketing Research*, 59, 675–695. [TODO: keep only if cited in the final text]

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. [TODO: verify edition details]

Ceylan, G., Diehl, K., & Proserpio, D. (2024). Words meet photos: When and why photos increase review helpfulness. *Journal of Marketing Research*, 61, 5–26.

Hou, Y., Li, J., He, Z., Yan, A., Chen, X., & McAuley, J. (2024). Bridging language and items for retrieval and recommendation. arXiv:2403.03952.

Hsieh, Y.-C., Chiu, H.-C., & Chiang, M.-Y. (2005). Maintaining a committed online customer: A study across search-experience-credence products. *Journal of Retailing*, 81, 75–82.

Kübler, R. V., Lobschat, L., Welke, L., & van der Meij, H. (2024). The effect of review images on review helpfulness: A contingency approach. *Journal of Retailing*, 100, 5–23.

Liu, A., Wu, Z., Michael, J., Suhr, A., West, P., Koller, A., Swayamdipta, S., Smith, N., & Choi, Y. (2023). We're afraid language models aren't modeling ambiguity. In *Proceedings of EMNLP 2023* (pp. 790–807). Association for Computational Linguistics.

Longoni, C., & Cian, L. (2022). Artificial intelligence in utilitarian vs. hedonic contexts: The "word-of-machine" effect. *Journal of Marketing*, 86, 91–108.

Mudambi, S., & Schuff, D. (2010). Research note: What makes a helpful online review? A study of customer reviews on Amazon.com. *MIS Quarterly*, 34, 185–200.

Mudambi, S. M., Schuff, D., & Zhang, Z. (2014). Why aren't the stars aligned? An analysis of online review content and star ratings. *2014 47th Hawaii International Conference on System Sciences*, 3139–3147.

Nelson, P. (1970). Information and consumer behavior. *Journal of Political Economy*, 78, 311–329. [TODO: verify]

Winter, C. G. H., Zacharias, N. A., & Hartwig, M. (2026). Using LLMs as sentiment analyzers to predict review helpfulness: First insights to open the black box. *Marketing Letters*, 37, Article 30. https://doi.org/10.1007/s11002-026-09824-7

Xiao, L., & Kumar, V. (2021). Robotics for customer service: A useful complement or an ultimate substitute? *Journal of Service Research*, 24, 9–29.
