# Do disagreements between LLM-inferred and actual star ratings predict review helpfulness? A replication and extension

*Draft for* Marketing Letters *(Replication Corner; limit: 4,000 words including abstract, text, and references; at most three tables or figures that do not count toward the limit; web appendix up to 2,000 words — verify current rules before submission). Items marked [TODO] must be resolved before submission.*

## Abstract

Winter, Zacharias, and Hartwig (2026) report that the gap between a large language model's (LLM) inferred star rating and the rating an author gave predicts lower review helpfulness, especially for experience goods. We revisit this claim with 25,783 Amazon reviews, three LLMs from different families run with two prompts (including the original), count models, and product-level goods classification. Inferred ratings track authors' ratings closely (r = .89–.92). Larger gaps do not predict fewer helpful votes: in Tobit and negative binomial models the association is positive (incidence rate ratios 1.19–1.36), and the experience-good interaction is not significant. Hedonic goods show smaller gaps once goods are classified at the product rather than the category level. We do not replicate the original experiment and cannot assess its mechanism.

**Keywords:** large language models, online reviews, review helpfulness, sentiment analysis, replication, count models

## 1. Introduction

Helpful votes are one of the main devices platforms use to sort the enormous volume of consumer reviews, and anticipating a review's helpfulness soon after it is posted would let useful content surface earlier (Mudambi and Schuff 2010; Ceylan, Diehl, and Proserpio 2024). [TODO: confirm that these sources support the platform-ranking claim, or cite the sources used by Winter et al. for it.] Winter, Zacharias, and Hartwig (2026; hereafter WZH) proposed an unusually inexpensive predictor. A general-purpose large language model (LLM) guesses, from the review text alone, the star rating the author gave, and the absolute distance between that guess and the actual rating is taken as a sign of inconsistency in the text. Across 28,900 reviews, this distance predicted lower helpfulness for experience goods (Tobit interaction β = −7.239, p < .001), and an experiment with 1,063 participants suggested that the effect runs through readers' difficulty in recovering the intended rating. Because the approach needs neither training data nor fine-tuning, the result is of obvious practical interest.

Several features of the original design leave room for a second look. Helpfulness is a non-negative count with a large mass at zero (54% of WZH's reviews), yet it was modeled with a Tobit specification that treats it as a censored normal variable; count models are the usual alternative (Cameron and Trivedi 2013). The inference rests on a single LLM version, a limitation the authors acknowledge, and the search–experience contrast draws on twelve products.

We report a conceptual replication built around three questions. Does an LLM's rating inference agree as closely with authors' ratings in a different, publicly available sample, and does agreement differ for hedonic goods? Does the gap predict lower helpfulness, particularly for experience goods, when the outcome is analyzed with Tobit and with count models? And do the answers depend on the LLM, the prompt, or how goods are classified? We did not replicate WZH's experiment, so our evidence concerns the observational association and not the mechanism they propose.

## 2. Background and hypotheses

Reviews help customers mainly by reducing information asymmetry before purchase (Kübler et al. 2024), and they do so best when they are easy to process and internally consistent (WZH, citing Mudambi, Schuff, and Zhang 2014). A review whose text conveys a different evaluation from its star rating forces readers to reconcile two signals. WZH argue that an LLM's disagreement with the author's own rating is a cheap proxy for such inconsistency, on the assumption that text a model finds ambiguous is also hard for people to read (WZH, citing Liu et al. 2023).

The cost of inconsistency should depend on how hard a product is to evaluate before purchase. The core qualities of search goods can be assessed from seller-provided information, whereas experience goods have to be consumed first (Nelson 1970; Hsieh, Chiu, and Chiang 2005), so readers researching experience goods lean more on consistent information (WZH). Earlier work likewise suggests that review characteristics matter differently across product types (Mudambi and Schuff 2010). [TODO: verify that their finding on rating extremity by product type is described accurately before citing it for this claim.] A further expectation concerns the LLM itself: AI systems are often thought to perform worse where emotions are salient, as in hedonic consumption (Longoni and Cian 2022; Xiao and Kumar 2021, both cited by WZH). WZH found smaller gaps for hedonic goods and attribute this to their more explicitly evaluative language.

Because we conceptually replicate WZH, we adopt their predictions as the confirmatory benchmark. H1: a larger gap predicts fewer helpful votes. H2: the negative association is stronger for experience goods than for search goods. H3: the gap is smaller for reviews of hedonic goods than for utilitarian goods. Two research questions go beyond the original. RQ1 asks whether conclusions change with the LLM, the prompt (ours versus WZH's), or the goods classification (category-level versus product-level). RQ2 asks whether they change when helpful votes are modeled as counts, for which a zero-inflated specification also checks whether the abundance of zeros requires a separate process.

A competing account emerged after our first look at the data. A 2,000-review pilot, run before the main analysis, suggested a positive association between gap and votes. One possible reason is that reviews that are hard to classify are often mixed or moderate, and readers may find balanced reviews more credible than uniformly extreme ones. We treat this as an exploratory, post hoc explanation and do not test it.

## 3. Data and measures

**Sample.** We use Amazon Reviews 2023 (Hou et al. 2024). The raw category files are sorted by user, so we read random byte windows from four category files and keep every review of the users who fall entirely inside a window. The categories approximate WZH's two-by-two design: Cell Phones and Accessories (assumed search, hedonic), Office Products (search, utilitarian), Beauty and Personal Care (experience, hedonic), and Home and Kitchen (experience, utilitarian). We cap reviews per user at five, draw 6,500 reviews per category, and remove reviews without text and duplicates, which leaves 25,783 reviews (25,711–25,783 depending on the LLM and prompt, after dropping unparseable responses). Windows over-represent prolific reviewers, and reviews cluster within users, so we cluster standard errors by product, as WZH do, and by user as a check. [TODO: add sampling code and review IDs to the replication package.] The outcome is the number of helpful votes (mean = 0.89, SD = 10.1, maximum = 1,130; 78.7% zeros).

**Gap.** Each LLM received only the review text and returned the star rating (1–5) it believed the author had given. The gap is the absolute difference from the author's rating. We use Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano, each with two prompts: our own (JSON output, temperature 0) and the system prompt in WZH's supplementary material, an instruction to act as a classifier and answer only with a number from 1 to 5, sent with the unwrapped review text at temperature 0.2 (Web Appendix A). The supplement lists the prompt's sentences separately, so the original separator is unknown; WZH used OpenAI models, and their versions and access date cannot be matched.

**Goods classification.** Category-level coding is coarse, so we also classified every sampled product (20,672 products) with Claude Haiku 5.5 from its title, category path, features, and description, using the definitions in WZH's tradition: a search good's main quality can be judged before purchase from seller information; an experience good's cannot; hedonic goods are bought mainly for pleasure, utilitarian goods for a functional task (Web Appendix B). Llama 3.3 70B labeled a random 3,000 products as a check. Agreement was 88.8% for search versus experience (κ = .755) and 87.6% for hedonic versus utilitarian (κ = .698). Two human coders then labeled a random sample of 100 products independently, after a calibration round on a different 100 products; agreement between the coders was κ = .93 for search versus experience and κ = .86 for hedonic versus utilitarian. Against the coders' consensus, the LLM labels agreed on 92.0% (κ = .82) and 90.0% (κ = .76) of products, and its errors lean toward assigning the experience and hedonic labels (Web Appendix B). Table 3 shows that the category assumptions differ markedly from the product-level labels.

**Models.** Controls follow WZH: review length, rating dummies (one star as reference), an image indicator, and review age; we lack their video indicator and product-level review count. We estimate (a) a Tobit model, left-censored at zero, with standard errors clustered by product, mirroring WZH; (b) a negative binomial model (NB2) with log review age as an exposure offset and log length; and (c) a zero-inflated negative binomial (ZINB) as a diagnostic. Code and the replication package are available at [TODO: repository link]; raw review text is not redistributed. The study was not preregistered: we analyzed a 2,000-review pilot first, and the main design followed it. We report every model estimated for the main question. [TODO: add a statement on the use of AI tools in analysis and drafting, following the journal's current policy.]

## 4. Results

### 4.1 LLM inference of star ratings

All three LLMs recover authors' ratings well (Table 1): r = .888–.923, exact agreement 64.6–79.0%, and two or more stars apart in 3.0–4.0% of reviews across both prompts. These figures are at least as favorable as WZH's (r = .763, about 37% misclassified). The star-by-star profile of the gap is less stable. With our prompt it is largest for three-star reviews, whereas WZH found one-star reviews deviating most; under the original prompt the mean one-star gap ranges from 0.17 (Llama) to 0.54 (GPT-4.1 nano), against 0.53–0.67 for three-star reviews, so WZH's profile is not consistently reproduced.

WZH report smaller gaps for hedonic goods (β = −.058, p < .001). With category-level coding the hedonic coefficient is near zero in all six LLM–prompt combinations (−.010 to +.003). With product-level labels it is negative in all six (−.017 to −.029) and significant in five (p ≤ .032; GPT-4.1 nano with our prompt, p = .078). H3 is therefore supported once hedonic goods are identified at the product level, at roughly 30–50% of the original effect size.

**Table 1. Agreement between authors' and LLM-inferred ratings, and the hedonic coefficient on the gap**

| Prompt | LLM | r | Exact match | Hedonic coef., category (p) | Hedonic coef., product (p) |
|---|---|---|---|---|---|
| Ours | Claude Haiku 5.5 | .907 | 70.7% | −.010 (.25) | −.029 (.001) |
| Ours | Llama 3.3 70B | .923 | 79.0% | +.003 (.72) | −.017 (.031) |
| Ours | GPT-4.1 nano | .889 | 64.6% | −.004 (.66) | −.017 (.078) |
| Original | Claude Haiku 5.5 | .897 | 70.9% | −.006 (.49) | −.026 (.004) |
| Original | Llama 3.3 70B | .921 | 78.3% | −.002 (.79) | −.017 (.032) |
| Original | GPT-4.1 nano | .888 | 67.6% | −.005 (.61) | −.021 (.025) |

*Note.* OLS of the gap on a hedonic indicator, rating dummies, length, and age; standard errors clustered by product. The gap correlates across LLMs at .63–.76.

### 4.2 Gap and helpfulness

Table 2 reports the negative binomial results for all twelve combinations of LLM, prompt, and goods classification; Tobit estimates are in Web Appendix C. With category-level coding, a one-star larger gap goes with 21–28% more helpful votes (IRR 1.21–1.28, p ≤ .015). The Tobit gap coefficient is also positive (Model 2: 0.71–1.45, significant in five of six combinations; Model 1: 0.45–0.98, significant except for GPT-4.1 nano under the original prompt, p = .18). WZH's own Model 2 yields a positive coefficient for search goods as well (+4.345), as does their GPT-5-nano check (+6.29, p = .001; Web Appendix 4 of WZH), so the negative association described in their abstract is confined to the interaction with experience goods. H1 is therefore not supported: the association is positive rather than negative.

The interaction, however, is not significant. With category-level coding the NB2 interaction IRR ranges from 0.82 to 1.03 (p = .09–.88), and the Tobit interaction from −0.54 to −1.06 (p = .12–.46); its sign varies across LLMs. Product-level labels do not change this conclusion. The gap effect stays positive (IRR 1.22–1.29, p ≤ .005), the NB2 interaction IRR is below 1 in all six combinations (0.80–0.98), directionally as in WZH, but only one of the six p-values falls below .05 (Llama with our prompt, p = .049, not corrected for multiple comparisons), and the Tobit interaction ranges from −0.39 to −0.82 (p = .29–.58). Point estimates imply that the net gap effect for experience goods is not negative (e.g., 1.30 × 0.95 ≈ 1.23 for Claude with our prompt; products of point estimates, not tested). H2 is not supported. Because classification error biases interactions toward zero, this null should be read as "not detected with these labels" and not as evidence of absence.

Controls behave as in WZH: longer reviews and reviews with images attract more votes (length IRR ≈ 2.7 per log unit; image IRR ≈ 5.4–5.6). Clustering by user rather than product leaves the interaction essentially unchanged (e.g., IRR = 0.820, 95% CI [0.650, 1.034], Llama, our prompt, category labels).

**Table 2. Negative binomial results by goods classification**

| Prompt | LLM | Gap IRR, Model 1 (category) | Gap × experience IRR (category) | Gap IRR, Model 1 (product) | Gap × experience IRR (product) |
|---|---|---|---|---|---|
| Ours | Claude Haiku 5.5 | 1.26 (.001) | 1.02 (.88) | 1.28 (<.001) | 0.95 (.67) |
| Ours | Llama 3.3 70B | 1.24 (.003) | 0.82 (.09) | 1.25 (.002) | 0.80 (.049) |
| Ours | GPT-4.1 nano | 1.22 (.001) | 0.90 (.38) | 1.23 (.001) | 0.88 (.30) |
| Original | Claude Haiku 5.5 | 1.21 (.015) | 0.92 (.58) | 1.23 (.005) | 0.83 (.15) |
| Original | Llama 3.3 70B | 1.28 (.001) | 0.89 (.34) | 1.29 (.001) | 0.87 (.27) |
| Original | GPT-4.1 nano | 1.21 (.007) | 1.03 (.83) | 1.22 (.004) | 0.98 (.87) |

*Note.* IRR (p). Controls: length (logs), rating dummies, image indicator; log review age as offset; standard errors clustered by product. WZH (Tobit, Model 2): gap +4.345; gap × experience −7.239 (p < .001).

**Table 3. Goods classification: category assumption versus product-level LLM labels**

| Category | Products | Assumed type | Experience goods (labels) | Hedonic goods (labels) |
|---|---|---|---|---|
| Cell Phones and Accessories | 4,987 | search, hedonic | 5.4% | 11.6% |
| Office Products | 5,239 | search, utilitarian | 15.9% | 11.6% |
| Beauty and Personal Care | 5,194 | experience, hedonic | 88.5% | 48.3% |
| Home and Kitchen | 5,252 | experience, utilitarian | 33.6% | 29.3% |

*Note.* Labels from Claude Haiku 5.5. Agreement with two-coder consensus (n = 100): κ = .82 (search/experience), .76 (hedonic/utilitarian). Cross-LLM κ = .755 and .698 (n = 2,999 products).

### 4.3 Excess zeros

With about 79% of reviews at zero, we compared NB2 with a ZINB whose inflation component depends on a constant and the experience dummy. In all twelve combinations the log-likelihoods are identical to the second decimal, the implied probability of a structural zero is below 10⁻⁹⁰, and AIC favors NB2 by four points. The inflation component is not identified and the model collapses to NB2: the zeros are consistent with the negative binomial itself (Web Appendix D).

## 5. Discussion

Our replication reproduces part of WZH's evidence and fails to reproduce the part that carries the headline claim. LLMs infer star ratings with high accuracy, the control variables behave as in the original, and the positive gap coefficient for search goods is reproduced. Hedonic goods show smaller gaps, but only once goods are classified at the product level; the category-level null was an artifact of assigning, for example, all Cell Phones and Accessories to hedonic goods, where product-level labels classify only 12% as hedonic. The interaction with experience goods is the piece we do not reproduce. It is directionally consistent with WZH in the product-level count models but nowhere significant, and we cannot rule out that noisy labels mask it.

We can only speculate about the remaining discrepancy. Reviews with large gaps are disproportionately mixed or moderate, and readers may regard them as balanced and informative even though a classifier finds them harder to label. The samples also differ: Amazon 2023 versus a scrape of first-page results for twelve search terms, thousands of products with about 1.3 reviews each versus 383 product clusters, and different outcome models. WZH's search–experience contrast rests on twelve products, so product-specific features could contribute to their interaction, which we cannot test. Their experiment isolates readers' perceived inconsistency in a controlled setting; our observational result does not contradict that mechanism but shows that it need not appear as a negative association in field data.

Several limitations qualify these conclusions. The study was not preregistered and followed a pilot. Product labels are LLM-generated and were validated on only 100 products (κ = .76–.82 against two coders); their errors lean toward experience and hedonic labels, which can bias the interaction estimates, and in two combinations they come from the same model family that inferred the ratings. Window-based sampling over-represents prolific reviewers. Our main prompt differs from the original; under the original prompt the sign and the null interaction are unchanged, but the significance of the gap effect varies by LLM (Web Appendix C), and our LLMs differ from WZH's. Helpful votes depend on how many readers see a review, which we cannot observe (see Kübler et al. 2024 [TODO: verify]). Tobit assumes a normal latent variable for a count with 79% zeros, and both approaches are observational. We make twelve comparisons without multiplicity correction and do not replicate the experiment.

For platforms, the value of an LLM–star gap as an inexpensive helpfulness predictor is unclear: its association with votes is positive here, and length and images are far stronger predictors. For researchers, the sensitivity of the hedonic result to goods classification and the instability of the interaction across LLMs suggest checking conclusions with product-level coding, count models, and more than one LLM, because the gap itself correlates only moderately across models (.63–.76).

## References

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
