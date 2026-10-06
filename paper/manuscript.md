---
title: "Auditing LLM-Generated Scholarly Text with Poisson Statistics: A White-Box Approach to Information Quality Assurance"
---

::: {custom-style="Abstract Heading"}
Abstract
:::

Large language models (LLMs) now produce scholarly-looking text at a volume that human screening cannot match, and the tools available for checking that text are either expensive, opaque, or both. This paper proposes and evaluates the Poisson-Score, a document-level indicator that measures how far the occurrence of a small set of stylistic events departs from a count process with a constant rate. The events are academic punctuation and symbols, discourse markers, and passive and nominalized constructions, all of which are central to English scientific prose. Following the design science tradition, we specify the artifact, derive hypotheses about its detection performance, its operating cost, and its value to human reviewers, and describe a three-part evaluation: a benchmark of 5,000 human-authored and 5,000 LLM-generated papers, a cost and latency comparison against an LLM-as-a-judge pipeline, and a between-subjects experiment in which researchers classify papers with no aid, a black-box score, or a Poisson-based explanation. [Results summary to be inserted once data collection is complete.] The study contributes a transparent and inexpensive instrument for information quality audits, evidence on when explanation improves human decisions about machine-generated content, and practical guidance for editors, repository managers, and organizations that curate synthetic data.

**Keywords:** Information quality, large language models, synthetic data, design science, explainable decision support, Poisson process, text auditing

# 1 Introduction

The scholarly record is a piece of information infrastructure. Journals, preprint servers, indexing services, and systematic review teams all rest on the assumption that a document that reads like a research paper was, in some meaningful sense, written by a researcher. That assumption has become harder to defend. Current LLMs can draft an abstract, a literature review, or a results section that is fluent, correctly formatted, and plausible to a non-specialist reader, at a marginal cost close to zero. The same capability supplies the synthetic corpora that organizations increasingly use to train and fine-tune their own models. When such corpora circulate without reliable provenance, two kinds of damage follow. Readers lose the ability to trust what they find, and downstream systems trained on contaminated text may degrade in ways that are difficult to trace (Shumailov et al. 2024). Both problems are, at bottom, problems of information quality (Wang and Strong 1996).

Information systems (IS) scholars have long argued that quality has to be assessed from the standpoint of the people and processes that use information, and that assessment must be operational, repeatable, and affordable (Lee et al. 2002; Pipino et al. 2002). Existing approaches to judging machine-generated text meet these requirements only partly. Using a strong LLM as an evaluator is flexible, but every document costs a model call, results shift with the wording of the prompt, and the evaluator brings its own stylistic preferences to the task (Zheng et al. 2023). Embedding-based measures such as MAUVE and BERTScore compare texts in a learned semantic space (Pillutla et al. 2021; Zhang et al. 2020). They are well suited to asking whether two collections say similar things, and poorly suited to asking whether the fine-grained texture of one collection resembles that of another. Likelihood-based detectors such as GLTR and DetectGPT need access to a scoring model and can be fragile when generators, domains, or decoding settings change (Gehrmann et al. 2019; Mitchell et al. 2023; Sadasivan et al. 2023). They have also been shown to misclassify the writing of non-native English speakers at troubling rates (Liang et al. 2023). Watermarking offers a cleaner solution, but only for text from cooperating providers (Kirchenbauer et al. 2023). Finally, almost none of these tools were designed with the human reviewer in mind. An editor who is told that a manuscript is "92% likely to be machine-generated" has a number but no evidence, and no principled way to weigh the one against the other (Rudin 2019).

We start from a different observation. A human author does not choose where to put a parenthesis, a semicolon, a "however," or a passive verb by consulting a global plan. These choices are made locally, sentence by sentence, in response to the content at hand, and over a stretch of ordinary prose they accumulate into counts per unit of text that behave, to a useful first approximation, like the counts produced by a random process with a stable rate. An LLM, by contrast, produces text under a decoding regime (temperature, nucleus truncation, and post-training toward a polished register) that is known to reshape the statistics of what is generated (Holtzman et al. 2020). If the reshaping touches the way stylistic events are spaced through a document, then the departure of event counts from a constant-rate count process may be a signal. The Poisson distribution, the canonical model for counts of independent events at a constant rate, gives that departure a precise and interpretable reference point. We do not claim that human writing is exactly Poisson; the corpus linguistics literature has documented burstiness in word use for decades (Church and Gale 1995; Katz 1996). Our claim is narrower and testable: that the *pattern* of departure from the Poisson benchmark differs systematically between human and machine text for a well-chosen set of events, and that this difference can be turned into a cheap, explainable measurement.

This idea leads to three research questions.

- **RQ1 (Effectiveness).** To what extent does a Poisson-based indicator detect LLM-generated scholarly text, both on its own and in addition to existing black-box measures?
- **RQ2 (Cost efficiency).** How much does a Poisson-based audit reduce latency and monetary cost relative to an LLM-as-a-judge audit at comparable scale?
- **RQ3 (Decision performance).** Does giving human reviewers an explainable Poisson-based indicator improve their accuracy in identifying machine-generated papers, compared with no support and with a black-box score of equal predictive accuracy?

We answer them with a design science study (Hevner et al. 2004; Gregor and Hevner 2013). We first specify the artifact, which we call the Poisson-Score, and justify its construction. We then evaluate it on a benchmark of 10,000 scientific papers, in a cost experiment against an LLM judge, and in a randomized behavioral experiment with researchers as participants. The paper makes three contributions. First, it offers an instrument for information quality assurance that is transparent by construction: every score decomposes into counts of named linguistic events that a reviewer can inspect. Second, it brings a classical statistical lens to a problem that is currently dominated by neural methods, and it is explicit about the assumptions under which that lens is valid. Third, it provides evidence on a question of direct relevance to IS research on decision support, namely whether explanation of the right kind, as opposed to prediction alone, improves human judgment when the object of judgment is machine-generated content.

The remainder of the paper is organized as follows. Section 2 reviews the relevant literature. Section 3 describes the design of the Poisson-Score. Section 4 develops hypotheses. Section 5 presents the research design, and Section 6 the analysis plan and the structure of the results. Section 7 discusses implications and limitations, and Section 8 concludes.

# 2 Theoretical Background

## 2.1 Information Quality and Synthetic Data

The IS literature treats data quality as fitness for use by data consumers, a perspective that extends well beyond accuracy to include believability, objectivity, reputation, and interpretability (Wang and Strong 1996). Measurement frameworks built on this view stress that quality has to be assessed by procedures that organizations can actually run (Lee et al. 2002; Pipino et al. 2002). Synthetic text changes the problem in two respects. It can satisfy surface criteria such as completeness and consistent representation while failing deeper ones, since the writer of the text may have no commitment to the claims it makes. And because it is cheap, it enters information systems in volume, so that quality assurance must scale. Evidence from the machine learning literature suggests that the stakes extend to model development itself: models trained recursively on generated data lose information about the tails of the original distribution (Shumailov et al. 2024). For an organization that maintains a text corpus, knowing how much of it is synthetic, and being able to explain how it knows, is therefore a data governance requirement and not merely a curiosity.

## 2.2 Evaluating and Detecting Machine-Generated Text

Three families of methods are relevant. The first uses an LLM as evaluator. Strong models agree with human preferences at rates that make them attractive substitutes for human annotation, but they exhibit position, verbosity, and self-preference biases and their outputs depend on the prompt (Zheng et al. 2023). The second family compares distributions in an embedding space. MAUVE quantifies the gap between model-generated and human text through divergence frontiers computed on learned representations (Pillutla et al. 2021), and BERTScore matches contextual token embeddings between a candidate and a reference (Zhang et al. 2020). Both inherit the properties of the encoder: they are sensitive to meaning and topic, and less so to the fine-grained frequency structure of function words and punctuation. The third family consists of detectors that exploit the statistical signature of generation, whether through token-rank and probability visualizations (Gehrmann et al. 2019), curvature of the log-probability surface (Mitchell et al. 2023), or trained classifiers. Their performance degrades under paraphrasing and distribution shift (Sadasivan et al. 2023), they may disadvantage non-native writers (Liang et al. 2023), and humans can be misled in turn when machine text is made to look natural (Ippolito et al. 2020). Cryptographic or statistical watermarks are a promising complement but require the cooperation of the generator (Kirchenbauer et al. 2023).

What is missing is a method that is cheap enough to screen at scale, independent of any particular generator, and transparent enough to be placed in front of a human decision maker. The Poisson-Score is intended to occupy that position.

## 2.3 Count Processes in Language

Statistical analyses of authorship have used word counts since at least Mosteller and Wallace (1964), who modeled the rates of function words with Poisson and negative binomial distributions to attribute the disputed *Federalist* papers. Later work showed that content words are often bursty, in the sense that a word that has appeared once is much more likely to appear again nearby than a constant-rate model predicts, and that the right description is a Poisson mixture rather than a single Poisson (Church and Gale 1995; Katz 1996). Frequent and topic-neutral items behave much closer to the constant-rate benchmark than rare and topical ones, which is one reason we restrict our attention to stylistic events that appear regularly in all kinds of scientific writing. For statistical modeling, the standard toolkit for count data, including Poisson regression, quantification of over-dispersion, and the negative binomial alternative, is mature (Cameron and Trivedi 2013; Hilbe 2011).

On the linguistic side, scientific English has well-documented register features: heavy use of nominalization and passive voice, dense use of parenthetical material and citations, and a set of metadiscourse devices that organize an argument (Biber 1988; Hyland 2005). Generative models trained and then tuned toward helpful and polished output tend to overuse some of these devices and to place them with unusual regularity. Decoding itself can contribute to this uniformity, because truncation methods remove the low-probability continuations that make human text less predictable (Holtzman et al. 2020). We treat these as plausible mechanisms, not as established facts, and the empirical work below is designed so that they can fail.

## 2.4 Explanation and Human Reliance on Decision Aids

IS research has a rich tradition on how explanations in intelligent systems affect users. Explanations improve performance mainly when they supply information that users can use to evaluate the system's advice, and the type and timing of the explanation matter (Dhaliwal and Benbasat 1996; Gregor and Benbasat 1999). Work on automation shows that people tend either to over-rely on aids, which produces complacency, or to under-rely on them, which produces what has been called algorithm aversion once they see the aid err (Parasuraman and Manzey 2010; Dietvorst et al. 2015). Trust is best when it is calibrated to the actual reliability of the aid (Lee and See 2004). Explanations are expected to help with calibration, but it is not guaranteed that they do; a persuasive explanation can raise confidence without improving accuracy (Miller 2019). A further argument, advanced on both ethical and practical grounds, is that for high-stakes decisions one should prefer models that are interpretable from the start to black boxes explained after the fact (Rudin 2019). A count-based indicator is interpretable in exactly this sense, and RQ3 asks whether that interpretability turns into measurable decision benefit.

# 3 Design of the Poisson-Score

## 3.1 Event Families

We define three families of countable events, selected because they are (a) frequent in scientific English, (b) cheap to detect with deterministic rules, and (c) plausibly shaped by the way LLMs generate text.

*Punctuation and symbols* (P). Parentheses, square brackets, semicolons, quotation marks, and inline mathematical or numerical notation. These are tied to how authors insert citations, define terms, and report quantities.

*Discourse markers* (D). A fixed lexicon of logical connectives and stance adverbials common in academic prose (for example, "furthermore," "moreover," "therefore," "in contrast," "crucially"), compiled from the metadiscourse literature (Hyland 2005) and extended with a pilot analysis of generated text.

*Passive voice and nominalization* (N). Passive constructions identified through part-of-speech patterns (a form of *be* followed by a past participle), and nominalizations identified by suffix (-tion, -ment, -ity, -ness) after filtering a list of common non-derived words.

All rules are published with the replication materials so that any score can be traced back to the specific tokens that produced it.

## 3.2 Construction

Let a document *i* be a sequence of tokens divided into *W_i* consecutive, non-overlapping windows of fixed length *L* (our default is *L* = 200 tokens; Section 5.4 reports sensitivity to 100 and 400). For each event family *k* and window *w*, let *N_ikw* denote the event count. If events of family *k* occurred at a constant rate within the document, the window counts would be independent draws from a Poisson distribution with mean $\lambda_{ik}$, which we estimate by the document mean $\hat{\lambda}_{ik}$.

Two quantities are then computed. The first is the index of dispersion, $\mathrm{ID}_{ik} = s^2_{ik} / \hat{\lambda}_{ik}$, the ratio of the sample variance of window counts to their mean. It equals one under the Poisson benchmark, exceeds one when events are clumped (over-dispersion), and falls below one when events are spaced more evenly than chance would allow (under-dispersion). We retain it as a signed diagnostic, because it tells a reviewer which way a document departs from the benchmark. The second is an unsigned distance. Window counts are binned into the categories 0, 1, 2, 3, and 4 or more, and we compute the Hellinger distance between the empirical distribution $\hat{p}_{ik}$ and the Poisson distribution $\pi_{ik}$ with mean $\hat{\lambda}_{ik}$:

$$H_{ik} = \sqrt{1 - \sum_{c} \sqrt{\hat{p}_{ikc}\,\pi_{ikc}}}, \qquad H_{ik} \in [0,1].$$

The Poisson-Score of document *i* is the mean over the *K* = 3 families:

$$\text{Poisson-Score}_i = \frac{1}{K}\sum_{k=1}^{K} H_{ik}.$$

Two design choices deserve comment. First, we use an unsigned distance because the direction of the departure is not something we assume in advance. Our conjecture is that LLM text departs from the benchmark, and the proposition that it does so through over-dispersion in some families and through excessive regularity in others is one the data should settle. Second, with a few dozen windows per document, the empirical distribution is noisy and the Hellinger distance has an upward finite-sample bias. The bias affects both classes of documents but depends on length, so we include the number of windows as a control in every model and report a length-matched analysis as a robustness check.

A corpus-level version supports the auditing use case in which an organization wants to know how far a *collection* departs from a trusted human reference. For a collection *C*, we pool the binned window counts, compute the Hellinger distance to the pooled human reference distribution, and report bootstrap confidence intervals over documents.

## 3.3 What the Score Does and Does Not Assume

Because the idea is easy to over-read, we state the assumptions. The Poisson-Score does not assume that human writing is Poisson. It uses the Poisson distribution as a fixed reference against which both classes of documents are measured, in the same way that a thermometer's zero is a convention. To assess how much the choice of reference matters, we compute a parallel score, the NB-Score, in which the benchmark is a negative binomial distribution fitted to the human training documents, which allows for the document-level heterogeneity that burstiness implies (Church and Gale 1995). If the two scores perform similarly, the simple benchmark is sufficient. If the NB-Score is much better, then the field's earlier findings on burstiness matter more than we expect, and we say so.

The score also does not read the content. A paper on a different subject, written by the same person, would receive a similar score, and this is part of the intended behavior, since it makes the instrument insensitive to topic. The cost is that a person or system who knows the score exists can adapt text to it. We return to this in Section 7.3.

# 4 Hypotheses

**Effectiveness.** If decoding and post-training reshape the spacing of stylistic events in the ways described in Section 2.3, the Poisson-Score should differ between machine-generated and human-written papers, in the sense that the distance to the constant-rate benchmark is larger for one class than the other. We predict the larger distance for machine-generated text, because the mechanisms we have identified tend to push counts toward regularity or clumping that human writers, who vary their rhetorical moves with content, do not produce to the same extent.

> **H1a.** Controlling for length, generator, domain, and prompt complexity, a higher Poisson-Score is associated with a higher probability that a document is LLM-generated.
>
> **H1b.** Adding the Poisson-Score to a set of baseline indicators (embedding-based and likelihood-based) increases the area under the ROC curve (AUC) for detecting LLM-generated documents.
>
> **H1c.** The Poisson-Score discriminates documents from generators that were not used when the score's reference distribution and decision threshold were calibrated.

H1c matters because the practical value of a detector depends on its behavior on tomorrow's models. Event rates are a property of how text is written and not of which model wrote it, and we therefore expect some generalization, though not necessarily to the same degree as within a generator.

**Cost efficiency.** The Poisson-Score requires tokenization and rule matching, which can be done on commodity hardware, while an LLM judge requires a long prompt and a model call for every document. We expect the former to be orders of magnitude cheaper per document.

> **H2.** A Poisson-Score audit has lower per-document latency and lower per-document monetary cost than an LLM-as-a-judge audit of the same documents.

This hypothesis is close to a mechanical consequence of the architectures, so its value lies in the size of the difference and its sensitivity to batching, parallelism, and the choice of judge, which we estimate and report with confidence intervals, not in the sign.

**Decision performance.** Following the explanation literature, an aid improves human decisions when it provides evidence that users can evaluate for themselves (Dhaliwal and Benbasat 1996; Gregor and Benbasat 1999). A black-box score gives a reviewer a recommendation she can only accept or reject on faith, and this invites the miscalibrated reliance described by Parasuraman and Manzey (2010) and Lee and See (2004). A Poisson-based explanation points to specific, checkable features, such as an unusually even spacing of connectives, that a trained reader can verify against the text. We expect this to yield better decisions than either no aid or a black-box score of equal predictive accuracy.

> **H3a.** Reviewers who receive the explainable Poisson-based indicator (Condition C) classify documents more accurately than reviewers who receive no indicator (Condition A).
>
> **H3b.** Reviewers in Condition C classify documents more accurately than reviewers who receive a black-box score (Condition B).

We pose the contrast between Conditions A and B as an exploratory question and make no directional prediction, because the literature gives reasons to expect both benefit and harm from an unexplained but accurate aid (Dietvorst et al. 2015). We also examine confidence calibration as a secondary outcome, since an explanation that raises confidence without raising accuracy would be a negative finding of practical importance (Miller 2019).

# 5 Research Design

## 5.1 Study 1: Benchmark Construction and Detection Performance

**Human corpus.** We draw 5,000 English-language research papers at random from arXiv and from the PubMed Central open access subset, stratified by field (computer science, physics, biomedicine, and social science) in proportions that we fix before sampling. To avoid contamination with machine-generated text, we sample only papers first published before November 2022. We use the abstract, introduction, and discussion sections, which are the parts of papers most likely to be machine-drafted and which are comparable in structure across fields.

**Synthetic corpus.** For every sampled paper we extract the title and a short keyword description and use them to prompt four generators to write the same sections, yielding 5,000 synthetic papers in total, with the generator rotated across topics so that each generator produces roughly 1,250 documents. At the time of writing, the generators are GPT-4o, Claude 3.5, Llama 3, and Mistral; we will record exact model versions, decoding parameters, and access dates and will update the list if these models are superseded before data collection. We vary prompt complexity at three levels (a bare title prompt; a prompt that adds an outline and style instructions; and a prompt that adds a writing sample from the target field and an instruction to vary sentence structure), which serves as a control variable and as a stress test.

**Splits.** The data are divided into a calibration set, a validation set, and a test set. One generator is withheld entirely from calibration and validation to address H1c, and the procedure is repeated so that each generator serves once as the withheld model.

**Baselines.** We compare against (a) an LLM-as-a-judge classifier with a fixed prompt and temperature zero, (b) MAUVE computed between document-level samples and the human reference, (c) a BERTScore-based nearest-reference measure, (d) a likelihood-based detector in the DetectGPT family, and (e) a supervised classifier on TF-IDF features, to check that the Poisson-Score is not merely recovering something that a bag-of-words model finds more easily.

**Goodness-of-fit diagnostics.** Before using the Poisson benchmark we examine how well it describes human documents. For each event family we run a chi-squared goodness-of-fit test on the binned window counts of each human document and report the share of documents for which the Poisson hypothesis is not rejected, along with the distribution of ID. We treat this as a diagnostic and not as a precondition. If a substantial share of human documents are over-dispersed, the NB-Score becomes the primary instrument, and we report the change.

**Primary model.** For document *i* generated under condition *g* (generator), *d* (domain), and *p* (prompt complexity), we estimate

$$\Pr(\text{Synthetic}_i = 1) = \operatorname{logit}^{-1}\!\left(\beta_0 + \beta_1\,\text{Poisson-Score}_i + \boldsymbol{\beta}_2^{\top}\mathbf{Z}_i\right),$$

where $\mathbf{Z}_i$ contains generator indicators, domain indicators, prompt complexity, and the log of the number of windows. For human documents, generator and prompt complexity are coded as a reference category and the model is estimated on the pooled sample, with additional models within each generator. H1a is supported if $\beta_1 > 0$ with a confidence interval that excludes zero. Standard errors are clustered by topic, because each human paper and its synthetic counterpart share a topic.

**Incremental validity.** For H1b we compare the cross-validated AUC of a classifier built from the baseline indicators with that of the same classifier augmented with the Poisson-Score, using DeLong's test for correlated ROC curves (DeLong et al. 1988). We also report precision and recall at fixed false-positive rates of 1% and 5%, since an editor's real constraint is how many human authors can be wrongly flagged.

**Fairness check.** Given documented bias against non-native writers (Liang et al. 2023), we compare false positive rates for human papers whose first author's affiliation is in a country where English is not an official language with those of the remaining papers. Affiliation is an imperfect proxy for language background, and we say so when reporting.

## 5.2 Study 2: Cost and Latency

We run the Poisson-Score pipeline and the LLM-as-a-judge pipeline on random batches of 1,000 documents from the test set, repeated thirty times. For the first we use a single named machine configuration and report wall-clock time per document under one thread and under full parallelism. For the second we record time per document through the provider's API, tokens consumed, and the list price in effect on the date of data collection, which we report. Outcomes are median and 95th-percentile latency, throughput in documents per second, and cost per 1,000 documents. For H2 we compare batch-level means with the Wilcoxon signed-rank test, and we report the ratio of costs and its bootstrap confidence interval. Because the cost of API calls changes frequently, we also report the break-even price at which the judge would match the Poisson pipeline.

## 5.3 Study 3: Human Decision Experiment

**Participants.** Participants are researchers and peer reviewers with at least one peer-reviewed publication, recruited through university mailing lists and professional panels. A sample of 30 to 50 people, as is common in laboratory studies, would be adequate to detect only very large effects in a three-group comparison. A one-way ANOVA with three groups requires roughly 66 participants in total to detect a large effect (Cohen's *f* = 0.40) at 80% power and α = .05 (Cohen 1988; Faul et al. 2007). We therefore target 90 participants, 30 per condition, and we will refine this figure by simulation of the mixed-effects model described below before data collection starts and register it in advance.

**Design.** Participants are randomly assigned to one of three conditions in a between-subjects design: A, no indicator; B, a black-box probability that the document is machine-generated; C, the Poisson-Score together with its explanation (the signed dispersion indices for each event family, a plot of window counts against the Poisson benchmark, and the tokens that were counted). The key control is that the indicators in B and C are matched in predictive accuracy: the black-box score comes from a supervised classifier whose accuracy on the stimulus set is calibrated to equal that of the Poisson-based classifier. Without this match, a difference between B and C could simply reflect a difference in how good the advice is, and not in how it is presented.

**Task and stimuli.** Each participant reviews 12 documents (6 human, 6 synthetic) drawn from the held-out test set, in randomized order, balanced across fields and generators. For each document they judge whether it was written by a human or generated by an LLM and rate their confidence on a seven-point scale. Participants in C receive a short tutorial on how to read the explanation, and participants in all conditions complete the same tutorial on the task itself. We include attention checks and a manipulation check on whether participants report having used the indicator.

**Outcomes and analysis.** The primary outcome is decision accuracy. Following the planned design, we first test differences in participant-level accuracy with a one-way ANOVA and planned contrasts for H3a and H3b, with Tukey adjustment for multiple comparisons. Because every participant sees multiple documents and every document is seen by multiple participants, we also estimate a mixed-effects logistic model,

$$\operatorname{logit}\Pr(\text{Correct}_{pj}=1) = \gamma_0 + \gamma_1 B_p + \gamma_2 C_p + u_p + v_j,$$

with random intercepts for participant ($u_p$) and document ($v_j$), using the *lme4* package (Bates et al. 2015). Secondary outcomes are confidence, calibration (the relation between confidence and correctness), time per document, and a reliance measure, defined as the rate at which participants' judgments agree with the indicator when the indicator is wrong. The last measure speaks directly to whether explanation prevents blind trust in an aid.

**Ethics.** The study will be submitted for institutional review board approval before recruitment. Participants are informed that some documents are machine-generated, and no deception is involved beyond the random mix of stimuli.

## 5.4 Robustness

We examine whether the results hold when (a) the window length is 100 or 400 tokens, (b) each event family is used alone, to see which carries the signal, (c) the NB-Score replaces the Poisson-Score, (d) synthetic documents are paraphrased by a second LLM before scoring, which is the standard attack on detectors (Sadasivan et al. 2023), (e) the discourse marker lexicon is replaced by a lexicon that excludes the words from our pilot analysis, and (f) documents are length-matched across the two classes.

# 6 Analysis Plan and Structure of Results

This section is a template. No data have yet been collected, and all quantities are marked for completion. We include it so that the analysis is fixed in advance of seeing results, and we intend to register it publicly.

**Table 1. Hypotheses and Decision Rules**

| Hypothesis | Test | Supported if |
|:---------|:-----------------|:------------------------------|
| H1a | Logit coefficient on Poisson-Score | $\beta_1 > 0$, 95% CI excludes 0 |
| H1b | DeLong test of AUC with vs. without Poisson-Score | Increase in AUC with p < .05, Holm-adjusted |
| H1c | AUC on withheld generator | Lower 95% CI bound for AUC above .50 in every fold |
| H2 | Wilcoxon signed-rank on latency; ratio of cost per 1,000 documents | Lower latency and lower cost for the Poisson pipeline, 95% CI excludes parity |
| H3a | Planned contrast C vs. A (ANOVA; mixed logit) | C > A, p < .05 |
| H3b | Planned contrast C vs. B (ANOVA; mixed logit) | C > B, p < .05 |

**Table 2. Detection Performance on the Test Set** [To be completed]

| Method | AUC | F1 | TPR at 1% FPR | TPR at 5% FPR |
|:---------------------|:-----:|:-----:|:-----:|:-----:|
| LLM-as-a-judge | [ ] | [ ] | [ ] | [ ] |
| MAUVE | [ ] | [ ] | [ ] | [ ] |
| BERTScore-based | [ ] | [ ] | [ ] | [ ] |
| Likelihood-based detector | [ ] | [ ] | [ ] | [ ] |
| TF-IDF classifier | [ ] | [ ] | [ ] | [ ] |
| Poisson-Score | [ ] | [ ] | [ ] | [ ] |
| Baselines + Poisson-Score | [ ] | [ ] | [ ] | [ ] |

**Table 3. Logistic Regression of Document Class on Poisson-Score** [To be completed]

| Variable | Coefficient | SE | Odds ratio |
|:-----------------------------|:-----:|:-----:|:-----:|
| Poisson-Score | [ ] | [ ] | [ ] |
| Log (number of windows) | [ ] | [ ] | [ ] |
| Generator (reference: human) | [ ] | [ ] | [ ] |
| Domain | [ ] | [ ] | [ ] |
| Prompt complexity | [ ] | [ ] | [ ] |

**Table 4. Cost and Latency per 1,000 Documents** [To be completed]

| Pipeline | Median latency (s/doc) | 95th pct. latency | Throughput (docs/s) | Cost (USD) |
|:----------------------|:-----:|:-----:|:-----:|:-----:|
| Poisson-Score | [ ] | [ ] | [ ] | [ ] |
| LLM-as-a-judge | [ ] | [ ] | [ ] | [ ] |

**Table 5. Decision Accuracy by Condition** [To be completed]

| Condition | n | Mean accuracy | SD | Mean confidence | Reliance when indicator wrong |
|:----------------------|:---:|:-----:|:-----:|:-----:|:-----:|
| A: No indicator | [ ] | [ ] | [ ] | [ ] | n/a |
| B: Black-box score | [ ] | [ ] | [ ] | [ ] | [ ] |
| C: Poisson explanation | [ ] | [ ] | [ ] | [ ] | [ ] |

**Figure 1** will plot, for one human and one synthetic document per generator, the observed window-count distribution against the Poisson benchmark for each event family. **Figure 2** will show ROC curves for all methods, and **Figure 3** the distribution of signed dispersion indices by class and event family. The last figure is the one that settles the direction question raised in Section 3.2.

# 7 Discussion

## 7.1 Expected Contributions to Research

Whatever the results turn out to be, the study speaks to three conversations. The first concerns information quality. By treating the authorship process as a source of measurable regularities, it proposes quality indicators that are defined on the statistical structure of text and not on its semantics, which complements existing dimensions of data quality (Wang and Strong 1996). The second concerns the design of detection and evaluation tools. The study compares a classical, low-parameter instrument with neural methods under the same protocol and tests them under generator shift, and a negative result on H1b or H1c would be informative in its own right, since it would show where simple statistics stop adding value. The third concerns explainable decision support. Most evidence on explanation comes from tasks in which the AI judges a quantity the user can also judge. Here the user is asked to detect a property of the text that is hard to perceive directly, and the explanation is a transformation of the same text into countable cues. Whether this helps, and whether it helps by improving calibration or merely by raising confidence, bears on how IS researchers should think about the design of explanations (Gregor and Benbasat 1999; Lee and See 2004).

## 7.2 Implications for Practice

Journals and conference organizers could use a count-based audit as a first-pass screen that costs almost nothing per submission, reserving closer reading for flagged items and presenting the editor with the specific cues that triggered the flag. Repository maintainers and organizations that assemble training corpora could apply the corpus-level version to estimate how far a new batch departs from a trusted human reference before admitting it. The design of the study suggests two cautions. A flag is evidence that merits human attention and not a verdict, and the false-positive analysis for non-native writers should be read before any institution adopts a threshold. Moreover, thresholds should be set from the cost of wrongly accusing an author, which is a policy choice that the instrument cannot make.

## 7.3 Limitations

Several limitations are inherent in the design. First, the instrument is exposed to adaptation. An author who knows the Poisson-Score can instruct a model to vary its use of connectives, or can edit text by hand until it passes, and a motivated adversary will do so. Robustness check (d) probes the simplest version of this attack, but the broader lesson is that any fixed statistic becomes less informative once it is used to make consequential decisions, and a practical deployment would need to rotate or randomize the event families. Second, text produced jointly by a human and an LLM, which is probably the dominant form in practice, falls between the two classes we study, and our binary design cannot say how the score behaves for lightly edited or partially generated text. Third, the benchmark is limited to English-language scientific prose in a handful of fields, and the event definitions are language-specific. The approach may carry over to other languages and genres but this is an empirical question that we do not test. Fourth, the generators are a snapshot, and the models available to authors will have changed by the time the paper is read. The leave-one-generator-out design addresses this only partially. Fifth, laboratory participants who are told that some documents are synthetic are more vigilant than real reviewers, so Study 3 may overstate absolute accuracy, though the comparison between conditions should be less affected. Sixth, even a very large effect in a modest sample of researchers does not guarantee that editors working under time pressure will use an explanation as intended, and field evidence would be a natural next step.

## 7.4 Directions for Future Research

Three extensions seem most valuable. One is to move from detection to the quality of synthetic data in a stricter sense, asking whether corpus-level departure from the human benchmark predicts the downstream performance of models trained on that corpus. A second is to study mixed authorship, where the unit of interest is the share or location of machine-written passages within a document, which the window-level counts used here could support. A third is to examine how institutions respond to such indicators over time, including strategic adaptation by authors, which would connect this work to the IS literature on governance and on the unintended consequences of metrics.

# 8 Conclusion

The growing volume of machine-generated scholarly text creates a quality assurance problem that existing tools address expensively, opaquely, or only for cooperating generators. We propose a measurement that is none of these. The Poisson-Score counts a small set of stylistic events, compares how they are spaced through a document with a constant-rate benchmark, and reports the result in a form that a reviewer can inspect. We have specified the artifact, stated the assumptions under which it is meaningful, formulated hypotheses on its detection performance, cost, and effect on human judgment, and laid out an evaluation designed so that each hypothesis can fail. If the hypotheses hold, organizations that depend on the integrity of text have a cheap first line of defense and a concrete example of explanation that serves the human who has to decide. If they do not, the results will indicate where classical statistics are insufficient for the task and where the effort of the field is better spent.

# References

::: {custom-style="Reference"}
Bates, D., Mächler, M., Bolker, B., and Walker, S. 2015. "Fitting Linear Mixed-Effects Models Using lme4," *Journal of Statistical Software* (67:1), pp. 1-48.

Biber, D. 1988. *Variation Across Speech and Writing*, Cambridge, UK: Cambridge University Press.

Cameron, A. C., and Trivedi, P. K. 2013. *Regression Analysis of Count Data* (2nd ed.), Cambridge, UK: Cambridge University Press.

Church, K. W., and Gale, W. A. 1995. "Poisson Mixtures," *Natural Language Engineering* (1:2), pp. 163-190.

Cohen, J. 1988. *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.), Hillsdale, NJ: Lawrence Erlbaum Associates.

DeLong, E. R., DeLong, D. M., and Clarke-Pearson, D. L. 1988. "Comparing the Areas under Two or More Correlated Receiver Operating Characteristic Curves: A Nonparametric Approach," *Biometrics* (44:3), pp. 837-845.

Dhaliwal, J. S., and Benbasat, I. 1996. "The Use and Effects of Knowledge-Based System Explanations: Theoretical Foundations and a Framework for Empirical Evaluation," *Information Systems Research* (7:3), pp. 342-362.

Dietvorst, B. J., Simmons, J. P., and Massey, C. 2015. "Algorithm Aversion: People Erroneously Avoid Algorithms after Seeing Them Err," *Journal of Experimental Psychology: General* (144:1), pp. 114-126.

Faul, F., Erdfelder, E., Lang, A.-G., and Buchner, A. 2007. "G*Power 3: A Flexible Statistical Power Analysis Program for the Social, Behavioral, and Biomedical Sciences," *Behavior Research Methods* (39:2), pp. 175-191.

Gehrmann, S., Strobelt, H., and Rush, A. M. 2019. "GLTR: Statistical Detection and Visualization of Generated Text," in *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations*, pp. 111-116.

Gregor, S., and Benbasat, I. 1999. "Explanations from Intelligent Systems: Theoretical Foundations and Implications for Practice," *MIS Quarterly* (23:4), pp. 497-530.

Gregor, S., and Hevner, A. R. 2013. "Positioning and Presenting Design Science Research for Maximum Impact," *MIS Quarterly* (37:2), pp. 337-355.

Hevner, A. R., March, S. T., Park, J., and Ram, S. 2004. "Design Science in Information Systems Research," *MIS Quarterly* (28:1), pp. 75-105.

Hilbe, J. M. 2011. *Negative Binomial Regression* (2nd ed.), Cambridge, UK: Cambridge University Press.

Holtzman, A., Buys, J., Du, L., Forbes, M., and Choi, Y. 2020. "The Curious Case of Neural Text Degeneration," in *Proceedings of the 8th International Conference on Learning Representations*.

Hyland, K. 2005. *Metadiscourse: Exploring Interaction in Writing*, London: Continuum.

Ippolito, D., Duckworth, D., Callison-Burch, C., and Eck, D. 2020. "Automatic Detection of Generated Text Is Easiest When Humans Are Fooled," in *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*.

Katz, S. M. 1996. "Distribution of Content Words and Phrases in Text and Language Modelling," *Natural Language Engineering* (2:1), pp. 15-59.

Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., and Goldstein, T. 2023. "A Watermark for Large Language Models," in *Proceedings of the 40th International Conference on Machine Learning*.

Lee, J. D., and See, K. A. 2004. "Trust in Automation: Designing for Appropriate Reliance," *Human Factors* (46:1), pp. 50-80.

Lee, Y. W., Strong, D. M., Kahn, B. K., and Wang, R. Y. 2002. "AIMQ: A Methodology for Information Quality Assessment," *Information & Management* (40:2), pp. 133-146.

Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., and Zou, J. 2023. "GPT Detectors Are Biased Against Non-Native English Writers," *Patterns* (4:7), 100779.

Miller, T. 2019. "Explanation in Artificial Intelligence: Insights from the Social Sciences," *Artificial Intelligence* (267), pp. 1-38.

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., and Finn, C. 2023. "DetectGPT: Zero-Shot Machine-Generated Text Detection Using Probability Curvature," in *Proceedings of the 40th International Conference on Machine Learning*.

Mosteller, F., and Wallace, D. L. 1964. *Inference and Disputed Authorship: The Federalist*, Reading, MA: Addison-Wesley.

Parasuraman, R., and Manzey, D. H. 2010. "Complacency and Bias in Human Use of Automation: An Attentional Integration," *Human Factors* (52:3), pp. 381-410.

Pillutla, K., Swayamdipta, S., Zellers, R., Thickstun, J., Welleck, S., Choi, Y., and Harchaoui, Z. 2021. "MAUVE: Measuring the Gap Between Neural Text and Human Text Using Divergence Frontiers," in *Advances in Neural Information Processing Systems 34*.

Pipino, L. L., Lee, Y. W., and Wang, R. Y. 2002. "Data Quality Assessment," *Communications of the ACM* (45:4), pp. 211-218.

Rudin, C. 2019. "Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and Use Interpretable Models Instead," *Nature Machine Intelligence* (1:5), pp. 206-215.

Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., and Feizi, S. 2023. "Can AI-Generated Text Be Reliably Detected?" arXiv:2303.11156.

Shumailov, I., Shumaylov, Z., Zhao, Y., Papernot, N., Anderson, R., and Gal, Y. 2024. "AI Models Collapse When Trained on Recursively Generated Data," *Nature* (631:8022), pp. 755-759.

Wang, R. Y., and Strong, D. M. 1996. "Beyond Accuracy: What Data Quality Means to Data Consumers," *Journal of Management Information Systems* (12:4), pp. 5-33.

Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., and Artzi, Y. 2020. "BERTScore: Evaluating Text Generation with BERT," in *Proceedings of the 8th International Conference on Learning Representations*.

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., and Stoica, I. 2023. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems 36*.
:::
