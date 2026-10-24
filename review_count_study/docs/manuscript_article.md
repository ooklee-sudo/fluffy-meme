# Does disagreement between LLM-inferred and actual star ratings predict review helpfulness? Evidence from three language models and 26,000 Amazon reviews

*Draft for* Marketing Letters *(regular article; limit: 5,000 words including abstract, text, and references; up to four tables or figures; online appendix up to 2,000 words — verify current rules before submission).*

## Abstract

Large language models (LLMs) can infer the star rating a reviewer gave from the review text alone. Winter, Zacharias, and Hartwig (2026) report that the gap between this inference and the actual rating predicts lower helpfulness, especially for experience goods. We test this claim with 25,783 Amazon reviews, three LLMs run with two prompts (one from the original study), count models, and product-level goods labels validated by two human coders. Inferred ratings track authors' ratings closely (r = .89–.92). Larger gaps go with more, not fewer, helpful votes (incidence rate ratios 1.19–1.36), and the interaction with experience goods is not significant. The association holds within rating levels and arises when the text is more critical than the rating, not when it is more positive. Hedonic goods show smaller gaps once goods are classified at the product level.

**Keywords:** large language models, online reviews, review helpfulness, sentiment analysis, count models, goods classification

## 1. Introduction

Helpful votes are one of the main devices platforms use to sort the enormous volume of consumer reviews. Because only a small share of readers vote, helpful reviews can quickly lose visibility, so ranking helpful reviews first, and anticipating helpfulness soon after a review is posted, is valuable (Ceylan, Diehl, and Proserpio 2024). Research on what makes a review helpful has examined length, rating extremity, depth, images, and emotional content (Mudambi and Schuff 2010; Cao, Duan, and Gan 2011; Yin, Bond, and Zhang 2014; Ceylan et al. 2024).

Winter, Zacharias, and Hartwig (2026; hereafter WZH) proposed an unusually inexpensive predictor. A general-purpose LLM guesses, from the review text alone, the star rating the author gave, and the absolute distance between that guess and the actual rating is taken as a sign of inconsistency in the text. Across 28,900 reviews, this distance predicted lower helpfulness for experience goods (Tobit interaction β = −7.239, p < .001), and an experiment with 1,063 participants suggested that the effect runs through readers' difficulty in recovering the intended rating. Because the approach needs neither training data nor fine-tuning, the result is of obvious practical interest.

Several features of the original design leave questions open. Helpfulness is a non-negative count with a large mass at zero (54% of WZH's reviews), yet it was modeled with a Tobit specification that treats it as a censored normal variable; count models are the usual alternative (Cameron and Trivedi 2013). The inference rests on a single LLM version, a limitation the authors acknowledge, and the search–experience contrast draws on twelve products. Finally, the gap is a single number that can arise in two ways, because the text may be more positive or more negative than the rating, and the inconsistency account does not distinguish them.

We study 25,783 Amazon reviews of 20,670 products in four categories, with three LLMs from different families, each run with our own prompt and with the prompt reported by WZH. Our contribution is threefold. First, we test WZH's predictions in a different, publicly available data source with count models. Second, we replace category-level assumptions about search, experience, hedonic, and utilitarian goods with product-level labels that two human coders validated, and we assess how label error could affect the results. Third, we examine what the gap captures by estimating it within rating levels and by separating the two directions of disagreement. The first two parts are confirmatory tests of WZH's predictions; the third is exploratory. We find that the LLMs recover authors' ratings well but that larger gaps are associated with more helpful votes, not fewer, and that the association comes from text that is more critical than the rating. We did not replicate WZH's experiment, so our evidence concerns the observational association and not the mechanism they propose.

## 2. Background and hypotheses

### 2.1 The gap as inconsistency

Reviews help customers mainly by reducing information asymmetry before purchase (Kübler et al. 2024), and they do so best when they are easy to process and internally consistent (WZH, citing Mudambi, Schuff, and Zhang 2014). A review whose text conveys a different evaluation from its star rating forces readers to reconcile two signals. WZH argue that an LLM's disagreement with the author's own rating is a cheap proxy for such inconsistency, on the assumption that text a model finds ambiguous is also hard for people to read (WZH, citing Liu et al. 2023). If readers vote for reviews they find helpful, a larger gap should predict fewer helpful votes.

### 2.2 Product type and LLM accuracy

The cost of inconsistency should depend on how hard a product is to evaluate before purchase. The core qualities of search goods can be assessed from seller-provided information, whereas experience goods have to be consumed first (Nelson 1970; Hsieh, Chiu, and Chiang 2005), so readers researching experience goods lean more on consistent information (WZH). Earlier work likewise shows that review characteristics matter differently across product types: Mudambi and Schuff (2010) found that extreme ratings are less helpful than moderate ones for experience goods. A further expectation concerns the LLM itself. AI systems are often thought to perform worse where emotions are salient, as in hedonic consumption (Longoni and Cian 2022; Xiao and Kumar 2021, both cited by WZH), yet WZH found smaller gaps for hedonic goods and attribute this to their more explicitly evaluative language.

### 2.3 An alternative: critical text as informational value

The inconsistency account treats every gap alike. A gap can, however, arise in two ways. The LLM may read the text as more positive than the rating, as when a low rating accompanies praise, or as more negative, as when a generous rating accompanies criticism. The inconsistency account predicts a negative association for both. An informational-value account predicts an asymmetry. Readers weigh negative information more heavily, a well-known negativity bias (Yin, Bond, and Zhang 2014), and the content of the text, not only the stars, drives helpfulness votes: Cao, Duan, and Gan (2011) report that semantic features matter more than stylistic ones and that reviews with strongly positive or negative opinions draw more votes than mixed or neutral ones. Text that is more critical than the rating then offers a balanced, diagnostic evaluation, whereas praise attached to a low rating offers no comparable signal. This alternative emerged after our first look at the data, from a 2,000-review pilot that suggested a positive association between gap and votes, so we treat it as exploratory.

### 2.4 Hypotheses

Because we test WZH's claims, we adopt their predictions as the confirmatory benchmark. H1a: a larger gap predicts fewer helpful votes. H2: the negative association is stronger for experience goods than for search goods. H3: the gap is smaller for reviews of hedonic goods than for utilitarian goods. The informational-value account gives an exploratory competing prediction. H1b: a larger gap predicts more helpful votes. H4: the association is stronger when the LLM reads the text as more negative than the rating than when it reads the text as more positive, and it persists within rating levels. Two research questions go beyond the original. RQ1 asks whether conclusions change with the LLM, the prompt (ours or WZH's), or the goods classification (category-level or product-level). RQ2 asks whether they change when helpful votes are modeled as counts, for which a zero-inflated specification also checks whether the abundance of zeros requires a separate process.

## 3. Data and measures

**Sample.** We use Amazon Reviews 2023 (Hou et al. 2024). The raw category files are sorted by user, so we read random byte windows from four category files and keep every review of the users who fall entirely inside a window. The categories approximate WZH's two-by-two design: Cell Phones and Accessories (assumed search, hedonic), Office Products (search, utilitarian), Beauty and Personal Care (experience, hedonic), and Home and Kitchen (experience, utilitarian). We cap reviews per user at five, draw 6,500 reviews per category, and remove reviews without text and duplicates, which leaves 25,783 reviews (25,729–25,783 depending on the LLM and prompt, after dropping unparseable responses). The sample is broad rather than deep, with about 1.3 reviews per product. Windows over-represent prolific reviewers, and reviews cluster within users, so we cluster standard errors by product, as WZH do, and by user as a check. The sampling code and the IDs of all sampled reviews are in the replication package. The outcome is the number of helpful votes (mean = 0.89, SD = 10.1, maximum = 1,130; 78.7% zeros).

**Gap.** Each LLM received only the review text and returned the star rating (1–5) it believed the author had given. The gap is the absolute difference from the author's rating. We use Claude Haiku 5.5, Llama 3.3 70B Instruct, and GPT-4.1 nano, each with two prompts: our own (JSON output, temperature 0) and the system prompt in WZH's supplementary material, an instruction to act as a classifier and answer only with a number from 1 to 5, sent with the unwrapped review text at temperature 0.2 (Web Appendix A). The supplement lists the prompt's sentences separately, so the original separator is unknown; WZH used OpenAI models, and their versions and access date cannot be matched. To reduce model-specific noise we also compute an ensemble gap from the mean of the three LLMs' inferred ratings, and we split the signed difference into the part where the LLMs read the text as more positive than the rating and the part where they read it as more negative.

**Goods classification.** Category-level coding is coarse, so we also classified every sampled product with Claude Haiku 5.5 from its title, category path, features, and description, using the definitions in WZH's tradition: a search good's main quality can be judged before purchase from seller information; an experience good's cannot; hedonic goods are bought mainly for pleasure, utilitarian goods for a functional task (Web Appendix B). Llama 3.3 70B labeled a random 3,000 products as a check (agreement 88.8% and κ = .755 for search versus experience; 87.6% and κ = .698 for hedonic versus utilitarian). Two human coders then labeled a random sample of 100 products, working independently according to their instructions, after a calibration round on a different 100 products; agreement between the coders was κ = .93 for search versus experience and κ = .86 for hedonic versus utilitarian. Against the coders' consensus, the LLM labels agreed on 92.0% (κ = .82) and 90.0% (κ = .76) of products, and its errors lean toward assigning the experience and hedonic labels (Web Appendix B). Table 3 shows that the category assumptions differ markedly from the product-level labels.

**Models.** Controls follow WZH: review length, rating dummies (one star as reference), an image indicator, and review age; we lack their video indicator and product-level review count. We estimate (a) a Tobit model, left-censored at zero, with standard errors clustered by product, mirroring WZH; (b) a negative binomial model (NB2) with log review age as an exposure offset and log length; and (c) a zero-inflated negative binomial (ZINB) as a diagnostic. Code and the replication package are available at [anonymized repository link to be inserted at submission]; raw review text is not redistributed.

**Process.** The study was not preregistered. The project began with exploratory analyses of LLM-coded content features of reviews in two 2,000-review samples (Yelp and Amazon) that showed no stable effects and are not reported here; we then analyzed a 2,000-review Amazon pilot of the gap, and the design of the main analysis followed it. The direction analysis in Section 4.4 was added after the main results. We report every model estimated for the main question. Generative AI was used in this project in two ways. First, the LLMs named above served as research objects and measurement instruments. Second, the author used an AI coding assistant (Claude, Anthropic) to write and run analysis code and to draft and edit text; the author checked the code against the logged outputs and takes full responsibility for the content.

## 4. Results

### 4.1 LLM inference of star ratings

All three LLMs recover authors' ratings well (Table 1): r = .888–.923, exact agreement 64.6–79.0%, and two or more stars apart in 3.0–4.0% of reviews across both prompts. These figures are at least as favorable as WZH's (r = .763, about 37% misclassified). The star-by-star profile of the gap is less stable. With our prompt it is largest for three-star reviews, whereas WZH found one-star reviews deviating most; under the original prompt the mean one-star gap ranges from 0.17 (Llama) to 0.54 (GPT-4.1 nano), against 0.53–0.67 for three-star reviews, so WZH's profile is not consistently reproduced.

**Table 1. Agreement between authors' and LLM-inferred ratings, and the hedonic coefficient on the gap**

| Prompt | LLM | r | Exact match | Hedonic coef., category (p) | Hedonic coef., product (p) |
|---|---|---|---|---|---|
| Ours | Claude Haiku 5.5 | .907 | 70.7% | −.010 (.247) | −.029 (.001) |
| Ours | Llama 3.3 70B | .923 | 79.0% | +.003 (.715) | −.017 (.031) |
| Ours | GPT-4.1 nano | .889 | 64.6% | −.004 (.663) | −.017 (.078) |
| Original | Claude Haiku 5.5 | .896 | 70.8% | −.006 (.447) | −.026 (.004) |
| Original | Llama 3.3 70B | .921 | 78.3% | −.002 (.795) | −.017 (.032) |
| Original | GPT-4.1 nano | .888 | 67.6% | −.005 (.604) | −.020 (.025) |

*Note.* OLS of the gap on a hedonic indicator, rating dummies, length, and age; standard errors clustered by product. The gap correlates across LLMs at .63–.76.

### 4.2 Gap and helpfulness

Table 2 reports the negative binomial results for all twelve combinations of LLM, prompt, and goods classification; Tobit estimates are in Web Appendix C. With category-level coding, a one-star larger gap goes with 20–28% more helpful votes (IRR 1.20–1.28, p ≤ .016). The Tobit gap coefficient is also positive (Model 2: 0.71–1.45, significant in four of six combinations; Model 1: 0.45–0.98, significant except for GPT-4.1 nano under the original prompt, p = .18). WZH's own Model 2 yields a positive coefficient for search goods as well (+4.345), as does their GPT-5-nano check (+6.29, p = .001; Web Appendix 4 of WZH), so the negative association described in their abstract is confined to the interaction with experience goods. H1a is therefore not supported, and the data favor H1b: the association is positive.

The interaction, however, is not significant. With category-level coding the NB2 interaction IRR ranges from 0.82 to 1.03 (p = .09–.88), and the Tobit interaction from −0.50 to −1.06 (p = .12–.54); its sign varies across LLMs. Product-level labels do not change this conclusion. The gap effect stays positive (IRR 1.22–1.29, p ≤ .005), the NB2 interaction IRR is below 1 in all six combinations (0.80–0.98), directionally as in WZH, but only one of the six p-values falls below .05 (Llama with our prompt, p = .049, not corrected for multiple comparisons), and the Tobit interaction ranges from −0.39 to −0.82 (p = .29–.58). Point estimates imply that the net gap effect for experience goods is not negative (e.g., 1.30 × 0.95 ≈ 1.23 for Claude with our prompt; products of point estimates, not tested). H2 is not supported. Because classification error biases interactions toward zero, this null should be read as "not detected with these labels" and not as evidence of absence. A sensitivity analysis that corrects for the labels' error rates (Web Appendix E) moves the interaction further below one in all six combinations (median corrected IRR 0.74–0.97), but every interval that includes the uncertainty of the error rates contains one, and the corrected net gap effect for experience goods is about 1.0–1.2.

Controls behave as in WZH: longer reviews and reviews with images attract more votes (length IRR ≈ 2.7 per log unit; image IRR ≈ 5.4–5.6). Clustering by user rather than product leaves the interaction essentially unchanged (e.g., IRR = 0.820, 95% CI [0.650, 1.034], Llama, our prompt, category labels).

**Table 2. Negative binomial results by goods classification**

| Prompt | LLM | Gap IRR, Model 1 (category) | Gap × experience IRR (category) | Gap IRR, Model 1 (product) | Gap × experience IRR (product) |
|---|---|---|---|---|---|
| Ours | Claude Haiku 5.5 | 1.26 (.001) | 1.02 (.878) | 1.28 (<.001) | 0.95 (.673) |
| Ours | Llama 3.3 70B | 1.24 (.003) | 0.82 (.090) | 1.25 (.002) | 0.80 (.049) |
| Ours | GPT-4.1 nano | 1.22 (.001) | 0.90 (.380) | 1.23 (.001) | 0.88 (.295) |
| Original | Claude Haiku 5.5 | 1.20 (.016) | 0.93 (.607) | 1.23 (.005) | 0.83 (.147) |
| Original | Llama 3.3 70B | 1.28 (.001) | 0.89 (.338) | 1.29 (.001) | 0.87 (.268) |
| Original | GPT-4.1 nano | 1.21 (.007) | 1.03 (.827) | 1.22 (.004) | 0.98 (.870) |

*Note.* IRR (p). Controls: length (logs), rating dummies, image indicator; log review age as offset; standard errors clustered by product. WZH (Tobit, Model 2): gap +4.345; gap × experience −7.239 (p < .001).

### 4.3 Goods classification and the hedonic hypothesis

WZH report smaller gaps for hedonic goods (β = −.058, p < .001). With category-level coding the hedonic coefficient is near zero in all six LLM–prompt combinations (−.010 to +.003). With product-level labels it is negative in all six (−.017 to −.029) and significant in five (p ≤ .032; GPT-4.1 nano with our prompt, p = .078; Table 1). H3 is therefore supported once hedonic goods are identified at the product level, at roughly 30–50% of the original effect size. The category-level null reflects an artifact of the assignment: product-level labels classify only 12% of Cell Phones and Accessories products as hedonic (Table 3). Correcting for the labels' measured error rates would enlarge the hedonic coefficients by about 60–70%, but with only 100 validated products the intervals that include error-rate uncertainty contain zero (Web Appendix E).

**Table 3. Goods classification: category assumption versus product-level LLM labels**

| Category | Products | Assumed type | Experience goods (labels) | Hedonic goods (labels) |
|---|---|---|---|---|
| Cell Phones and Accessories | 4,987 | search, hedonic | 5.4% | 11.6% |
| Office Products | 5,239 | search, utilitarian | 15.9% | 11.6% |
| Beauty and Personal Care | 5,194 | experience, hedonic | 88.5% | 48.3% |
| Home and Kitchen | 5,252 | experience, utilitarian | 33.6% | 29.3% |

*Note.* Labels from Claude Haiku 5.5. Agreement with two-coder consensus (n = 100): κ = .82 (search/experience), .76 (hedonic/utilitarian). Cross-LLM κ = .755 and .698 (n = 2,999 products).

### 4.4 Why is the association positive? Direction and rating level

Table 4 reports exploratory analyses of what the gap captures, using the ensemble gap. The ensemble gap goes with 29% more helpful votes per star (IRR 1.29, 95% CI [1.12, 1.48]), and with 24% more when votes are winsorized at the 99.9th percentile (76 votes), so extreme counts do not drive the result. The association is not confined to reviews with moderate ratings. Within five-star reviews, which make up 64% of the sample, the IRR is 1.27 [1.05, 1.54]; within four-star and three-star reviews it is 1.41 and 1.34; the one- and two-star estimates are positive but imprecise (1.09 and 1.31; N = 3,246 and 1,439).

The direction of the disagreement matters. A gap in which the LLMs read the text as more negative than the rating goes with 35% more votes per star (IRR 1.35 [1.17, 1.56]), whereas a gap in which they read the text as more positive shows no association (1.00 [0.76, 1.31]); the two differ (ratio 1.35, p = .036). Within three-star and four-star reviews, where both directions are possible, the more-negative reading has IRR 1.38 [1.09, 1.74] and 1.45 [1.10, 1.90], and the more-positive reading is not associated with votes (Web Appendix G). The original prompt gives the same pattern (more negative 1.39 [1.17, 1.65], more positive 0.90 [0.67, 1.23], ratio 1.54, p = .007). H4 is therefore supported. The ensemble gap by product-level classification again shows a positive effect for search goods (1.39 [1.16, 1.67]) and an interaction below one that is not significant (0.86 [0.67, 1.11]). Because rating and direction are mechanically linked (a five-star review can only be read as more negative), the signed gap is estimated with rating dummies, and these results are associations from observational data.

**Table 4. Direction of the disagreement and rating level (ensemble gap, our prompt; negative binomial IRR per star)**

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

*Note.* Ensemble gap = |author's rating − mean of the three LLMs' inferred ratings|. The signed versions are the part of the difference in which the LLMs read the text as more positive (or more negative) than the rating; both enter one model. In Panel A the search-goods and interaction rows use product-level labels. Controls: log length, image indicator, rating dummies (omitted within a rating stratum); log review age as offset; standard errors clustered by product. The original-prompt version and the 3- and 4-star direction estimates are in Web Appendix G.

### 4.5 Excess zeros

With about 79% of reviews at zero, we compared NB2 with a ZINB whose inflation component depends on a constant and the experience dummy. In all twelve combinations the log-likelihoods differ by at most 0.01, the implied probability of a structural zero is below 10⁻⁹⁰, and AIC favors NB2 by four points. The inflation component is not identified and the model collapses to NB2: the zeros are consistent with the negative binomial itself (Web Appendix D).

## 5. Discussion

We examined whether the gap between an LLM's inferred star rating and the actual rating predicts review helpfulness. LLMs infer star ratings with high accuracy, the control variables behave as in the original study, and the positive coefficient for search goods in WZH's Model 2 is reproduced. The negative association between gap and helpfulness that WZH describe is not. In our data the association is positive across three LLMs, two prompts, two goods classifications, and two outcome models, and it arises where the text is more critical than the rating. The interaction with experience goods is directionally consistent with WZH once goods are classified at the product level, but it is nowhere significant.

These results contribute in three ways. For theory on review helpfulness, they suggest that a text–rating disagreement is not necessarily a processing cost. When the text is more critical than a generous rating, the disagreement may signal a balanced evaluation that readers value, an interpretation consistent with the negativity bias and content-driven helpfulness reported in earlier work (Cao, Duan, and Gan 2011; Yin, Bond, and Zhang 2014), though we cannot observe readers' reasons. For measurement, they show that conclusions about LLM-based measures can depend on how the outcome is modeled (count versus Tobit), on the LLM and prompt, and on how goods are classified; the hedonic result in particular appears only with product-level labels, and a sensitivity analysis shows how label error could matter. For practice, they cast doubt on using the gap to down-rank reviews: it is positively associated with votes, and length and images are far stronger predictors.

Several limitations qualify these conclusions. The study was not preregistered, followed a pilot, and its direction analysis is exploratory. The data are observational, and helpful votes depend on how many readers see a review, which we cannot observe (WZH, citing Kübler et al. 2024, note that readers can process only a limited number of reviews). Product labels are LLM-generated and were validated on only 100 products (κ = .76–.82 against two coders); their errors lean toward experience and hedonic labels, which can bias the interaction estimates, and in two combinations they come from the same model family that inferred the ratings. The decision rules for the coders were refined after a calibration round. Window-based sampling over-represents prolific reviewers, and the sample is broad rather than deep, so product-level fixed effects are not available. Our main prompt differs from the original; under the original prompt the sign and the null interaction are unchanged, but the significance of the gap effect varies by LLM (Web Appendix C), and our LLMs differ from WZH's. Tobit assumes a normal latent variable for a count with 79% zeros. We make many comparisons without multiplicity correction, and we do not replicate the experiment.

Future research could test the proposed asymmetry experimentally by manipulating whether a generous rating is paired with critical text or a low rating with praise and measuring readers' perceived helpfulness, credibility, and effort. Human coding of content balance would show whether the more-negative readings correspond to two-sided reviews, and platform data on exposure would separate reader attention from evaluation.

## References

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. https://doi.org/10.1017/CBO9781139013567

Cao, Q., Duan, W., & Gan, Q. (2011). Exploring determinants of voting for the "helpfulness" of online user reviews: A text mining approach. *Decision Support Systems*, 50(2), 511–521. https://doi.org/10.1016/j.dss.2010.11.009

Ceylan, G., Diehl, K., & Proserpio, D. (2024). Words meet photos: When and why photos increase review helpfulness. *Journal of Marketing Research*, 61(1), 5–26. https://doi.org/10.1177/00222437231169711

Hou, Y., Li, J., He, Z., Yan, A., Chen, X., & McAuley, J. (2024). Bridging language and items for retrieval and recommendation. arXiv:2403.03952.

Hsieh, Y.-C., Chiu, H.-C., & Chiang, M.-Y. (2005). Maintaining a committed online customer: A study across search-experience-credence products. *Journal of Retailing*, 81(1), 75–82. https://doi.org/10.1016/j.jretai.2005.01.006

Kübler, R. V., Lobschat, L., Welke, L., & van der Meij, H. (2024). The effect of review images on review helpfulness: A contingency approach. *Journal of Retailing*, 100(1), 5–23. https://doi.org/10.1016/j.jretai.2023.09.001

Liu, A., Wu, Z., Michael, J., Suhr, A., West, P., Koller, A., Swayamdipta, S., Smith, N., & Choi, Y. (2023). We're afraid language models aren't modeling ambiguity. In *Proceedings of EMNLP 2023* (pp. 790–807). Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.emnlp-main.51

Longoni, C., & Cian, L. (2022). Artificial intelligence in utilitarian vs. hedonic contexts: The "word-of-machine" effect. *Journal of Marketing*, 86(1), 91–108. https://doi.org/10.1177/0022242920957347

Mudambi, S., & Schuff, D. (2010). Research note: What makes a helpful online review? A study of customer reviews on Amazon.com. *MIS Quarterly*, 34(1), 185–200. https://doi.org/10.2307/20721420

Mudambi, S. M., Schuff, D., & Zhang, Z. (2014). Why aren't the stars aligned? An analysis of online review content and star ratings. *2014 47th Hawaii International Conference on System Sciences*, 3139–3147. https://doi.org/10.1109/HICSS.2014.389

Nelson, P. (1970). Information and consumer behavior. *Journal of Political Economy*, 78(2), 311–329. https://doi.org/10.1086/259630

Winter, C. G. H., Zacharias, N. A., & Hartwig, M. (2026). Using LLMs as sentiment analyzers to predict review helpfulness: First insights to open the black box. *Marketing Letters*, 37, Article 30. https://doi.org/10.1007/s11002-026-09824-7

Xiao, L., & Kumar, V. (2021). Robotics for customer service: A useful complement or an ultimate substitute? *Journal of Service Research*, 24(1), 9–29. https://doi.org/10.1177/1094670519878881

Yin, D., Bond, S. D., & Zhang, H. (2014). Anxious or angry? Effects of discrete emotions on the perceived helpfulness of online reviews. *MIS Quarterly*, 38(2), 539–560. https://doi.org/10.25300/MISQ/2014/38.2.10
