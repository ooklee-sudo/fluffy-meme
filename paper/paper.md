---
title: "Beyond the Poisson Assumption: Count-Based Screening for LLM-Generated Scholarly Text"
subtitle: "Working paper: pilot evidence from three generators"
---

# Abstract

Scholarly publishers face a new screening problem: language models now write plausible papers faster than anyone can check them. We examine a transparent and nearly free screen built on counts of small linguistic events, such as parentheses, semicolons, passive clauses, and discourse markers. Using 474 human-written papers from 2015–2019 and matched papers from GPT-4o, Claude, and Llama, we find that human text is not Poisson, so a simple distance from a Poisson process detects almost nothing. Richer count-based features detect machine text well only for the generator on which they were trained. A model of how events cluster across window sizes improves transfer to an unseen generator (AUC 0.89 to 0.93). Compared with zero-shot LLM judges, the screen is far cheaper and sometimes better, and combining the two works best, although Claude's papers evade every method we tried. The evidence comes from three generators and one genre.

**Keywords:** information quality, synthetic text detection, count data, dispersion, generalization, scholarly publishing

# 1. Introduction

Fluent, well-organized prose has long served as weak evidence of effort in scholarly publishing. Large language models undermine even that. A model can draft an abstract, a methods section, or a plausible set of results in a minute, and the output is often good enough to survive a quick read. For publishers, preprint servers, and research-integrity offices, the practical question is therefore no longer whether such text exists. It is whether it can be screened at a cost that scales with submission volume, and in a way that an editor can understand and contest.

Current options fit this need poorly. Asking a strong model to grade a document, the approach known as LLM-as-a-judge (Zheng et al. 2023), is flexible, but every call costs money, the verdict depends on the wording of the prompt and on the judge's own tendencies, and the reasoning cannot be audited statistically. Embedding-based comparisons such as MAUVE (Pillutla et al. 2021) and BERTScore (Zhang et al. 2020) are cheaper, but they mostly measure whether two sets of texts *mean* similar things. They say little about whether the texts *behave* alike in small, countable habits, such as how often a semicolon appears in a section.

We start from a simple observation. Writers do not plan how many parentheses a paragraph will contain. Such events accumulate as a by-product of content and habit, which is the setting in which count models are natural. Language models, by contrast, are trained to make each next token locally likely, and decoding choices can smooth or regularize how often particular forms recur. If so, machine-written text may differ from human text in the *distribution* of event counts, and not only in their averages, and a transparent statistical screen could detect this at almost no cost.

The classical benchmark for counts of independent events is the Poisson distribution, whose variance equals its mean. An earlier version of this project took for granted that human scientific writing roughly follows this benchmark and that machine text departs from it. We test that premise instead of adopting it, and we test something that detection studies often leave implicit: whether a detector built on one generator still works on another. Three questions organize the paper, in the order a screening organization would ask them.

- **RQ1 (Distributional fit).** Do human-authored papers follow a Poisson process in the selected events, and how does machine-generated text differ?
- **RQ2 (Detection and transfer).** How well do count-based features separate human from machine-generated papers, which part of the signal carries the discrimination, and does a detector built on one generator work on another?
- **RQ3 (Cost).** What does screening cost in time and money, compared with an LLM judge?

We make four contributions. First, we show that human text departs systematically from the Poisson benchmark, which explains why a single Poisson-distance score fails. Second, we document how sharply detection degrades across generators and which features transfer best. Third, we propose a scale-dependent clustering model, a doubly stochastic Poisson process, and test it on an open-weight generator that played no part in its development. Fourth, we compare the screen with two LLM judges and evaluate two ways of combining them, including the cost implications. Whether explainable statistical evidence improves the decisions of human reviewers is a separate question that requires a controlled experiment; we have not run one.

# 2. Background

**Information quality and governance.** Research on information quality treats accuracy and credibility as properties that organizations must monitor actively. Generative models change the economics of that monitoring, because producing plausible content is now cheaper than verifying it. Cost per screened document therefore belongs among the outcomes alongside detection accuracy, a view in keeping with the design-science tradition, in which an artifact is judged by whether it solves an organizational problem at acceptable cost (Hevner et al. 2004).

**Detection of machine-generated text.** Existing detectors include supervised classifiers, methods that use a language model's own probabilities (for example, Gehrmann et al. 2019; Mitchell et al. 2023), and judge-style evaluation by a second model. Most are opaque to the person who must act on them, and many deteriorate when the generating model changes. We give up some flexibility in exchange for transparency: every quantity we use traces back to a specific, countable feature.

**Count data and dispersion.** For counts of independent events in fixed windows, the Poisson model implies a dispersion index, the variance divided by the mean, of one. Real text rarely satisfies this, because topics, sections, and formatting conventions make events cluster. Count-data methods accommodate extra variation, for instance through the negative binomial family (Cameron and Trivedi 2013). We therefore read the dispersion index descriptively, as a summary of how clustered a document's events are.

# 3. Data and Methods

## 3.1 Human-authored papers

We sampled English-language papers published between 2015 and 2019, before large language models were widely used for scientific writing. Papers came from the open-access subset of PubMed Central (medicine; 300 sampled) and from arXiv (computer science; 200 sampled), drawn at random within each source. For PubMed Central we used the body paragraphs of the article XML. For arXiv we converted the PDFs to text, removed the reference list, and rejoined broken lines. We excluded documents shorter than 1,500 words, and the analysis requires at least four 500-token windows, which left 474 human papers.

## 3.2 Machine-generated papers

For each sampled paper we asked a generator to write a paper on the same topic, given the original title and abstract, using one of three prompts of increasing detail. We used three generators through a commercial API gateway: GPT-4o, Claude Sonnet 5.5, and Llama 3.3 70B Instruct, an open-weight model. A single request produced only about 800 words from GPT-4o, too short for window-based analysis, so each paper was written in four requests (introduction, methods, results, and discussion with conclusion) and concatenated. Prompts were processed in a fixed random order, so each generator's sample is random across fields.

GPT-4o produced 245 unique papers, with a median length of about 2,750 words; one source had been generated twice during testing, and we kept one record. Claude produced 152 papers (median 4,566 words, range 3,667 to 5,134). We capped generation at that number to limit cost, not because of any property of the output. Llama produced 202 unique papers (median about 2,970 words, range 2,355 to 7,926), again keeping one record for a source generated twice. Llama was added last, after the clustering model of Section 3.5 had been developed, and it serves as the confirmatory test. Because the generators wrote papers of different lengths, every document is truncated to the same length before analysis.

## 3.3 Events and windows

Each document is cut into consecutive windows of 500 whitespace-delimited tokens, and only the first four windows (2,000 tokens) are kept for every document, human or machine, so that length cannot drive any result. In each window we count seven events: parentheses, square brackets, semicolons, paired quotation marks, a list of fourteen discourse markers (for example, *however*, *therefore*, *moreover*), passive constructions (a form of *be* plus a participle, found by pattern matching), and nominalizations (words ending in *-tion*, *-ment*, or *-ity*). The patterns for passives and nominalizations are approximate and misclassify some words.

For each document and event we compute the mean count per window, which we call the *rate*, and the dispersion index. A document-level Poisson test compares (n − 1) times the dispersion index with a chi-squared distribution with n − 1 degrees of freedom, with separate tail probabilities for over- and under-dispersion. With only four windows per document these tests have low power, so the rejection rates we report understate the true departure from Poisson behavior.

## 3.4 Poisson-Score and baseline features

The Poisson-Score maps a document into the interval [0, 1) according to its mean absolute standardized deviation, across all events, from a human reference distribution of log rates and log dispersion indices. The reference is estimated on human training documents only, within each cross-validation fold. As a richer baseline we use the fourteen underlying quantities (seven rates and seven dispersion indices) as inputs to logistic regression. When an event never occurs in a document its dispersion is undefined, and we set it to one; this affects mainly square brackets in machine text, where most papers contain none.

## 3.5 Scale-dependent clustering model

A single dispersion index at one window size says whether events cluster but not how. We therefore developed a model that describes the structure of clustering across scales. We treat the occurrences of each event as a doubly stochastic Poisson process, or Cox process: events arrive as a Poisson process whose rate varies along the document. For such a process, the Fano factor in a window of w tokens is F(w) = 1 + Var(Λ_w) / E(Λ_w), where Λ_w is the rate integrated over the window. If rate fluctuations are positively correlated over long ranges, as when citations gather in an introduction or passives in a methods section, F(w) grows with w. A pure Poisson process gives F(w) = 1 at every scale.

We estimate F(w) for each event at four window sizes (50, 100, 200, and 400 tokens) within the same 2,000 tokens, and summarize each event by three quantities: its rate per 500 tokens, the mean log Fano factor across scales (the overall level of clustering), and the slope of log F(w) on log w (how quickly clustering grows with scale). Estimation is by moment matching and not a full likelihood fit. Fano factors are clipped to [0.05, 20] and set to one when an event does not occur. The result is 21 features (seven events by three quantities), against 14 in the baseline.

The comparison between the baseline (rates plus the 500-token dispersion index) and the new features was fixed before the model was run, with cross-generator AUC in both directions and human-only detection as the outcomes. We report every result of that comparison, including those that do not favor the new model, and we did not tune window sizes or any other setting on these data. The model was, however, designed after we had seen the baseline results, a limitation we return to in Section 6.

## 3.6 Evaluation design

Detection is evaluated by five-fold cross-validation in which all material from one source paper stays in one fold, so that a human paper and its machine-written counterpart never straddle the training and test sets. We report the area under the ROC curve (AUC) with 95% bootstrap intervals over documents. To study transfer, we train on human papers plus papers from one generator and test on held-out human papers plus papers from another. We also evaluate detectors trained on human papers only: a Mahalanobis distance from the human feature distribution (Ledoit–Wolf covariance), chosen as the primary method before the results were seen, and, as secondary methods, a one-class support vector machine and an isolation forest, all with default settings. These yield an anomaly score, and we ask how well it separates held-out human papers from each generator's papers.

Because the clustering model was developed on the GPT-4o and Claude data, we tested it on Llama papers that played no part in its development. This test was fixed before the Llama papers were generated: train on human papers plus both other generators pooled, never on Llama, and compare the baseline with the new features by a paired bootstrap of the AUC difference. The analysis code, prompts, and generated papers are in the project repository, and the human papers can be re-collected with the included script.

## 3.7 LLM judges, fusion, and cascade

To compare with the black-box approach, we asked two models, zero-shot and at temperature 0, to estimate for each excerpt the probability (0 to 100) that it was written by an AI language model: GPT-4o and Gemini 2.5 Pro. Both received one fixed prompt. They saw a random sample of 500 excerpts (200 human papers, of which 120 were from medicine and 80 from computer science, and 100 papers from each generator), in random order, with opaque identifiers and no labels. Each excerpt was the same first 2,000 tokens used for the count-based features. To remove trivial cues we stripped markdown symbols and bare section titles from every excerpt, whatever its source. Gemini 2.5 Pro reasons before answering, so we allowed it up to 8,000 output tokens, and 12 of its 500 answers were empty or unreadable. In the main analysis a document is excluded for every method if either judge's answer is unreadable, which leaves 196 human papers and 92 to 95 papers per generator; as a sensitivity check we score unreadable answers as 50, meaning no information.

For each generator, each judge is compared with two count-based detectors evaluated on the same documents, one using the baseline features and one using the clustering features. Each detector is trained on human papers plus the *other two* generators and never on the generator being tested, which makes it comparable to a judge that has not seen that generator. Differences are tested with a paired bootstrap computed separately for each judge. We also report medicine papers alone, whose text comes from clean XML, because the arXiv text comes from PDF conversion and could carry artifacts that a judge might pick up. GPT-4o is also one of the generators, so its verdicts on GPT-4o papers involve self-recognition; Gemini is not a generator.

Because the screen and the judges may fail in different places, we also tested a simple fusion. For each target generator, the clustering-based screen score and the Gemini score were each converted to a rank within the evaluated pool of human and target papers, which uses no labels, and the two ranks were averaged (fusion F1, the primary fusion). Two secondary fusions were specified in advance: the larger of the two ranks (F2), and the average of the screen and both judges (F3). No weights were fitted, so the fusion cannot overfit the 500 judged documents. Finally, we simulated a cascade in which a judge is called only on documents that a free screen finds suspicious. The screen scores every document, and only the top share q of the pool (10, 20, 30, 50, or 100%) is sent to the Gemini judge; documents that are not sent cannot be flagged. For the documents sent, the final score is either the judge's score alone (C1, with ties broken by the screen) or the mean of the screen's rank in the pool and the judge's rank among the documents sent (C2). We report the share of machine papers flagged when at most 5% of all human papers are flagged, together with the judge cost implied by q. Because the judged sample holds far more machine papers than a real submission stream would, the primary evaluation resamples pools in which machine papers make up 10% of the total (300 bootstrap pools); pools as sampled, with about one third machine papers, are a secondary evaluation. The fusion and the cascade, and the scripts that evaluate them, were specified before they were run.

# 4. Results

## 4.1 Human text is not Poisson (RQ1)

Table 1 reports, for each event, the median dispersion index and the share of documents whose counts reject the Poisson null in the direction of over-dispersion. Only discourse markers behave roughly as the Poisson model predicts in human text, with a median index of 1.00 and a rejection rate of 6%, close to the 5% expected by chance. Punctuation is clearly over-dispersed: 49% of documents reject the null for square brackets, 42% for parentheses, and 36% for semicolons. Citations and formulas plausibly gather in particular parts of a paper, such as the introduction and methods, and this is exactly the kind of clustering that a Poisson model cannot represent.

| Event | Human: index (% over) | GPT-4o: index (% over) | Claude: index (% over) | Llama: index (% over) |
|:--|--:|--:|--:|--:|
| Square brackets | 2.53 (48.8) | 1.33 (36.4) | 1.22 (22.0) | 2.00 (38.5) |
| Parentheses | 2.22 (42.2) | 1.78 (28.6) | 2.21 (40.1) | 2.02 (39.6) |
| Semicolons | 2.00 (36.2) | 1.00 (12.4) | 2.00 (36.0) | 2.00 (35.0) |
| Nominalizations | 1.67 (27.4) | 0.76 (7.3) | 1.10 (15.1) | 1.27 (21.8) |
| Quotation marks | 1.30 (24.4) | 3.00 (60.0) | 2.00 (37.7) | 3.00 (55.3) |
| Passive constructions | 1.20 (18.8) | 2.51 (47.3) | 1.79 (37.5) | 2.02 (35.1) |
| Discourse markers | 1.00 (6.2) | 1.11 (7.8) | 1.22 (4.6) | 1.11 (9.4) |

: Table 1. Median dispersion index and percentage of documents rejecting the Poisson null toward over-dispersion (5% level), by source. Index = variance / mean; 1 indicates Poisson behavior.

Machine text departs from human text in both directions, which argues against the tempting story that it is uniformly too regular. Nominalizations are less dispersed in all three generators (medians of 0.76, 1.10, and 1.27, against 1.67 in human text), so they are spread more evenly. Passive constructions and quotation marks are more dispersed in all three (passives 2.51, 1.79, and 2.02 against 1.20; quotation marks 3.00, 2.00, and 3.00 against 1.30). That these directions agree across generators makes them more credible as features of machine writing than as quirks of one model. Figure 1 shows the distributions for human and GPT-4o text. One caution applies to the passive result. Because each paper was generated section by section and the four retained windows roughly follow those sections, elevated passive dispersion may partly reflect a procedural artifact, since passive voice concentrates in methods text. We could not separate the two with the present data.

![Figure 1. Distribution of log2 dispersion indices by event for human-authored and GPT-4o papers. Dashed line: Poisson (index of 1). Square brackets for GPT-4o are degenerate because most machine papers contain none (index set to one by convention).](fig_dispersion.png)

## 4.2 Detection within and across generators (RQ2)

A single Poisson-Score performs close to chance, with AUCs of 0.54 for GPT-4o, 0.51 for Claude, and 0.53 for Llama. Treating its fourteen components as separate predictors changes the picture. When the detector is trained and tested on human papers plus one generator, cross-validated logistic regression reaches an AUC of 0.987 for GPT-4o, 0.913 for Claude, and 0.962 for Llama. Event rates carry most of this signal (AUC 0.97 for GPT-4o and 0.90 for Claude), and dispersion alone remains informative (0.86 and 0.75). Table 2 shows why the rates are specific to each generator. GPT-4o uses far fewer square brackets, semicolons, and quotation marks than human authors and more nominalizations and discourse markers. Claude differs in another way: it uses *more* semicolons than human authors (3.54 per 500 tokens, against 1.95) and more quotation marks, and fewer discourse markers (1.08 against 1.84). Llama shows a third pattern, with many parentheses and few brackets. Because semicolons fall below the human rate for one generator and rise above it for another, no rule based on average frequency can describe machine text in general.

| Event | Human | GPT-4o | Claude | Llama |
|:--|--:|--:|--:|--:|
| Parentheses | 9.80 | 7.39 | 11.39 | 14.66 |
| Square brackets | 4.46 | 0.21 | 0.41 | 0.17 |
| Semicolons | 1.95 | 0.51 | 3.54 | 1.17 |
| Quotation marks | 0.95 | 0.53 | 1.23 | 0.55 |
| Discourse markers | 1.84 | 2.38 | 1.08 | 2.12 |
| Passive constructions | 8.08 | 6.18 | 8.61 | 6.51 |
| Nominalizations | 24.43 | 34.08 | 27.34 | 26.67 |

: Table 2. Mean event count per 500-token window, by source.

Performance falls sharply when the detector meets a generator it was not trained on (Table 3). A GPT-4o-trained detector reaches an AUC of 0.73 on Claude papers (95% interval 0.69 to 0.78), down from 0.99 on GPT-4o itself, and a Claude-trained detector reaches 0.81 on GPT-4o papers (0.78 to 0.84). The gap between within-generator and cross-generator AUC is large for every feature family, so calibration on one generator should not be assumed to protect against another. Rates transfer worst (0.66 and 0.73), whereas dispersion transfers better (0.70 and 0.81) and equals the combined model in the Claude-to-GPT-4o direction. This fits the sign pattern in Table 2: differences in rates reverse across generators, while the differences in dispersion for passives, quotation marks, and nominalizations point the same way (Table 1). Dispersion is the more portable signal, but even it is far from sufficient on its own.

| Train → Test | Rates | Dispersion | Both |
|:--|:--|:--|:--|
| GPT-4o → GPT-4o | 0.971 [0.96, 0.98] | 0.856 [0.83, 0.88] | 0.987 [0.98, 0.99] |
| Claude → Claude | 0.904 [0.88, 0.93] | 0.751 [0.71, 0.80] | 0.913 [0.89, 0.94] |
| GPT-4o → Claude | 0.659 [0.62, 0.70] | 0.704 [0.65, 0.75] | 0.730 [0.69, 0.78] |
| Claude → GPT-4o | 0.728 [0.69, 0.76] | 0.808 [0.77, 0.84] | 0.810 [0.78, 0.84] |

: Table 3. AUC (95% bootstrap interval) by training and test generator and feature family. Training and test folds are grouped by source paper; test documents include held-out human papers.

## 4.3 Detection from human text alone (RQ2)

A screening organization might prefer a detector that needs no examples of machine text, because such examples go stale as models change. We therefore trained detectors on human papers only and scored how unusual each held-out document looks (Table 4). The result is negative. The Mahalanobis detector specified in advance reaches an AUC of 0.56 on GPT-4o papers and 0.46 on Claude papers with all fourteen features, and the secondary methods do not change the picture. Across three methods, three feature families, and the two generators studied at that stage, AUCs range from 0.45 to 0.66, and many intervals include 0.5. The best single value (0.66, a one-class SVM on rates for GPT-4o) was not chosen in advance and is not one we would rely on.

| Method (human-only) | Features | GPT-4o | Claude |
|:--|:--|:--|:--|
| Mahalanobis (primary) | Rates | 0.597 [0.55, 0.64] | 0.466 [0.42, 0.52] |
| Mahalanobis (primary) | Dispersion | 0.507 [0.46, 0.55] | 0.510 [0.45, 0.56] |
| Mahalanobis (primary) | Both | 0.563 [0.52, 0.60] | 0.462 [0.41, 0.52] |
| One-class SVM | Both | 0.610 [0.56, 0.65] | 0.475 [0.42, 0.53] |
| Isolation forest | Both | 0.473 [0.43, 0.52] | 0.468 [0.42, 0.52] |

: Table 4. AUC (95% bootstrap interval) for detectors trained on human papers only. Scores are anomaly scores; test sets are held-out human papers (grouped by source paper) plus papers from the named generator. The full grid, including rates-only and dispersion-only variants for each method, is in the project repository.

The contrast with Table 3 is instructive. Supervised detectors succeed because they learn the *direction* in which a generator departs from human writers. Human papers already differ widely among themselves in these features, across fields, sections, and authors, so machine text is seldom far from the human cloud in an absolute sense; it is displaced from the center in particular directions, and a distance from the human distribution does not capture that displacement.

## 4.4 A scale-dependent clustering model (RQ2)

Table 5 compares the clustering features with the baseline on the GPT-4o and Claude data on which the model was developed, so these results are exploratory. Differences are computed with a paired bootstrap on identical documents, which is more informative than comparing separate intervals. The new features help in seven of the eight comparisons, in the sense that the interval for the difference excludes zero or sits at its edge. The largest gain is for dispersion-only detection within a generator (+0.07 for GPT-4o). Transfer to an unseen generator improves from 0.73 to 0.76 (GPT-4o to Claude) and from 0.81 to 0.85 (Claude to GPT-4o) when rates are included; without rates, the improvement for GPT-4o to Claude cannot be distinguished from zero. The slope alone is a weak predictor (AUC 0.67 to 0.82), so the gains come mainly from the level of clustering across scales and from the richer description, not from the slope itself. The model does not rescue human-only detection on these data: a Mahalanobis detector on the new features reaches 0.59 for GPT-4o and 0.49 for Claude, essentially as before.

| Train → Test | Baseline AUC | New AUC | Difference [95% CI] |
|:--|--:|--:|:--|
| *Rates plus clustering features* | | | |
| GPT-4o → GPT-4o | 0.987 | 0.991 | +0.004 [−0.000, +0.008] |
| Claude → Claude | 0.914 | 0.946 | +0.032 [+0.017, +0.050] |
| GPT-4o → Claude | 0.729 | 0.755 | +0.026 [+0.001, +0.052] |
| Claude → GPT-4o | 0.809 | 0.849 | +0.040 [+0.019, +0.062] |
| *Clustering features only (no rates)* | | | |
| GPT-4o → GPT-4o | 0.856 | 0.927 | +0.071 [+0.045, +0.096] |
| Claude → Claude | 0.751 | 0.794 | +0.043 [+0.004, +0.082] |
| GPT-4o → Claude | 0.704 | 0.730 | +0.026 [−0.017, +0.071] |
| Claude → GPT-4o | 0.808 | 0.858 | +0.050 [+0.021, +0.077] |

: Table 5. Baseline (500-token dispersion index) versus scale-dependent clustering features, development data. Baseline values differ from Table 3 by at most 0.001 because of a small change in how counts are split at window boundaries.

The confirmatory test uses the Llama papers, which played no part in developing the model, with an analysis specified before they were generated. Trained on human papers plus GPT-4o and Claude pooled, the baseline features detect Llama papers with an AUC of 0.886 (95% interval 0.86 to 0.91), and the new features reach 0.932 (0.91 to 0.95), a difference of +0.046 (0.030 to 0.063; Table 6). The improvement also appears when training on either generator alone, so it does not depend on the pooling choice.

| Trained on (plus human papers) | Baseline AUC | New AUC | Difference [95% CI] |
|:--|:--|:--|:--|
| GPT-4o and Claude (primary) | 0.886 [0.86, 0.91] | 0.932 [0.91, 0.95] | +0.046 [+0.030, +0.063] |
| GPT-4o only | 0.913 [0.89, 0.93] | 0.953 [0.94, 0.97] | +0.041 [+0.027, +0.054] |
| Claude only | 0.737 [0.70, 0.77] | 0.796 [0.76, 0.83] | +0.058 [+0.034, +0.084] |

: Table 6. Confirmatory test: detection of Llama 3.3 70B papers by detectors that never saw Llama. Baseline = rates plus the 500-token dispersion index; New = rates plus scale-dependent clustering features.

Three further Llama results are exploratory. Llama papers are easy to detect within their own class: with human and Llama papers the baseline reaches 0.962 and the new features 0.984, and with clustering features alone the new model reaches 0.914 against 0.764 for the baseline dispersion index. A detector trained on Llama transfers well to GPT-4o (baseline 0.938, new 0.969) but poorly to Claude (0.745 and 0.763), which reinforces the impression that Claude papers are the hardest of the three to detect from other generators. And a human-only Mahalanobis detector on the new features reaches 0.65 (0.60 to 0.69) on Llama, against 0.51 for the baseline, the first human-only result in our data that is clearly above chance, though 0.65 is not a level we would deploy.

## 4.5 Comparison with LLM judges (RQ2, RQ3)

Table 7 gives the AUC of each method for separating human papers from each generator's papers on the judged excerpts. The two judges differ greatly. GPT-4o as judge is a modest detector of GPT-4o papers (AUC 0.76) and Llama papers (0.85) and worse than chance on Claude papers (0.45). At a threshold of 50 it flags 24% of human papers as AI-generated, against 59% of GPT-4o papers, 85% of Llama papers, and only 11% of Claude papers. Gemini 2.5 Pro is much stronger on two generators, with AUCs of 0.97 for both GPT-4o and Llama papers, and it flags only 2% of human papers while flagging 86% of GPT-4o and 89% of Llama papers. On Claude papers, however, it reaches only 0.66 and flags 1% of them, fewer than the 2% of human papers it flags.

| Target generator | GPT-4o judge | Gemini 2.5 Pro judge | Screen, baseline features (unseen) | Screen, clustering features (unseen) |
|:--|:--|:--|:--|:--|
| GPT-4o (n = 196 / 92) | 0.760 [0.70, 0.81] | 0.972 [0.95, 0.99] | 0.927 [0.90, 0.95] | 0.946 [0.92, 0.97] |
| Claude (n = 196 / 94) | 0.450 [0.39, 0.51] | 0.656 [0.59, 0.72] | 0.759 [0.70, 0.82] | 0.775 [0.72, 0.83] |
| Llama (n = 196 / 95) | 0.846 [0.80, 0.89] | 0.974 [0.95, 0.99] | 0.884 [0.85, 0.92] | 0.933 [0.90, 0.96] |

: Table 7. AUC (95% bootstrap interval) on the same documents. "Unseen" means trained on human papers plus the other two generators, never on the target. Sample sizes are human / machine documents. Scoring the unreadable Gemini answers as 50 instead of excluding them changes the Gemini AUCs to 0.970, 0.653, and 0.973.

How the screen compares with a judge therefore depends on the judge. Against GPT-4o, the clustering features are better on all three generators (paired AUC differences of +0.19 for GPT-4o, 95% interval 0.13 to 0.25; +0.33 for Claude, 0.24 to 0.40; and +0.09 for Llama, 0.04 to 0.14). Against Gemini 2.5 Pro the comparison reverses for two generators and holds for the third. The clustering features are lower on Llama papers (−0.04, interval −0.08 to −0.01), lower on GPT-4o papers by an amount whose interval reaches zero (−0.03, interval −0.06 to +0.01), and higher on Claude papers (+0.12, interval 0.04 to 0.20). The baseline features trail Gemini on GPT-4o (−0.05) and Llama (−0.09) and lead on Claude (+0.10). Medicine papers alone give similar results (Gemini 0.95, 0.58, and 0.96; clustering screen 0.93, 0.77, and 0.92), so extraction artifacts in the arXiv text do not explain the pattern. Claude's papers are the hardest to detect for every method we tried. The screen does best on them, but an AUC of about 0.77 is far from adequate. The comparison also carries an asymmetry: the screen uses labeled examples from other generators and the judges use none, so they answer different practical questions, namely what can be done with no examples of machine text at all, and what a cheap screen achieves once some are available.

## 4.6 Combining the screen with a judge (RQ2, RQ3)

Averaging the ranks of the screen and the Gemini judge gave an AUC of 0.994 on GPT-4o papers and 0.989 on Llama papers, better than either component alone (Table 8). The gain over Gemini is small but clear (+0.022, 95% interval 0.008 to 0.040, for GPT-4o; +0.014, 0.001 to 0.031, for Llama), and the gain over the screen is larger (+0.048 and +0.055). On Claude papers the fusion reached 0.790, far above the judge (+0.134, interval 0.092 to 0.177) but not distinguishable from the screen alone (+0.015, interval −0.028 to 0.059). The share of papers detected at a 5% false-positive rate shows the practical effect more plainly: 98% of GPT-4o papers against 87% for the judge and 64% for the screen, 96% of Llama papers against 89% and 73%, and 39% of Claude papers against 17% for the screen and 1% for the judge. The secondary fusions were less useful. Taking the larger rank (F2) was no better than the judge for GPT-4o and Llama and worse than the screen for Claude, and adding the weak GPT-4o judge (F3) did not help beyond F1.

| Target generator | Screen (clustering) | Gemini judge | Fusion F1 | Detected at 5% FPR: screen / Gemini / F1 |
|:--|:--|:--|:--|:--|
| GPT-4o | 0.946 [0.92, 0.97] | 0.972 [0.95, 0.99] | 0.994 [0.99, 1.00] | 0.64 / 0.87 / 0.98 |
| Claude | 0.775 [0.72, 0.83] | 0.656 [0.59, 0.72] | 0.790 [0.73, 0.84] | 0.17 / 0.01 / 0.39 |
| Llama | 0.933 [0.90, 0.96] | 0.974 [0.95, 0.99] | 0.989 [0.98, 1.00] | 0.73 / 0.89 / 0.96 |

: Table 8. AUC (95% bootstrap interval) of the primary fusion (F1, mean rank of the screen and Gemini scores) and its components on the same documents as Table 7, and the share of machine papers detected at a 5% false-positive rate on human papers. The 5% thresholds are set on the same documents and are descriptive, not estimates of deployed performance.

Fusion runs the judge on every document and so costs as much as the judge. The cascade is a cheaper alternative (Table 9). When machine papers make up 10% of the pool, sending only the top 30% of documents to the judge detects 95% of GPT-4o papers at a 5% false-positive rate (interval 0.86 to 1.00), the same as judging everything (0.95), at 30% of the cost; with 20% the rate falls to 86%. For Llama papers a share of 50% matches full judging (0.97 against 0.96 for the judge alone), and 30% gives 0.89. Claude papers stay hard at every setting: detection remains between 0.30 and 0.38 for q from 10% to 30%, and judging everything with the judge alone detects only 12%, so additional judge calls add little for this generator and the screen supplies most of what is detected. The savings depend on how rare machine papers are. In the secondary evaluation, with about one third of the pool machine-written, detection at q = 30% falls to 0.76 for GPT-4o papers and 0.78 for Llama papers, and q must reach about 50% to recover 0.92 to 0.95. The share judged must therefore exceed the share of machine papers by a margin, which means an organization would need to know roughly how common such papers are.

| Target generator | Share judged (q) | Judge cost per 1,000 docs | Detected, judge only (C1) | Detected, rank fusion (C2) |
|:--|:--|:--|:--|:--|
| GPT-4o | 20% | US$3.5 | 0.86 [0.73, 1.00] | 0.86 [0.73, 1.00] |
| | 30% | US$5.2 | 0.95 [0.86, 1.00] | 0.96 [0.86, 1.00] |
| | 50% | US$8.7 | 0.96 [0.86, 1.00] | 0.97 [0.91, 1.00] |
| | 100% | US$17.4 | 0.95 [0.82, 1.00] | 0.97 [0.86, 1.00] |
| Claude | 20% | US$3.5 | 0.38 [0.11, 0.59] | 0.38 [0.11, 0.59] |
| | 30% | US$5.2 | 0.36 [0.09, 0.59] | 0.36 [0.09, 0.59] |
| | 50% | US$8.7 | 0.19 [0.05, 0.50] | 0.35 [0.09, 0.59] |
| | 100% | US$17.4 | 0.12 [0.00, 0.32] | 0.37 [0.09, 0.59] |
| Llama | 20% | US$3.5 | 0.82 [0.64, 0.95] | 0.82 [0.64, 0.95] |
| | 30% | US$5.2 | 0.89 [0.73, 1.00] | 0.89 [0.73, 1.00] |
| | 50% | US$8.7 | 0.97 [0.86, 1.00] | 0.95 [0.82, 1.00] |
| | 100% | US$17.4 | 0.96 [0.86, 1.00] | 0.93 [0.79, 1.00] |

: Table 9. Simulated cascade, pools with 10% machine papers. Share of machine papers flagged when at most 5% of human papers are flagged, with 95% intervals over bootstrap pools. Costs use the measured Gemini price of US$0.0174 per document. Sending 10% of documents detected 0.60, 0.30, and 0.66 for GPT-4o, Claude, and Llama papers.

## 4.7 Cost (RQ3)

Computing all events and the baseline indices took 4 to 6 milliseconds per document on one CPU core, roughly 160 to 230 documents per second depending on machine load, with no external service calls, so the marginal monetary cost is zero. For the judges we measured about US$0.0073 and 1.7 seconds per excerpt for GPT-4o (US$3.63 for 500 excerpts) and about US$0.0174 and 23.4 seconds per excerpt for Gemini 2.5 Pro (US$8.68), a figure that includes the reasoning tokens it produced. Screening 1,000 documents would thus cost about US$7 and half an hour of sequential calls with GPT-4o, and about US$17 and more than six hours with Gemini, against no marginal cost and a few seconds for the count-based features. In the cascade, judge cost scales with the share of documents sent. These figures depend on the judge model, the prompt length, and the pricing and speed at the time. For context on the generation side, producing one paper in four requests cost about US$0.04 for GPT-4o, US$0.13 for Claude, and US$0.002 for Llama 3.3 70B through the gateway we used.

# 5. Discussion

Two findings qualify the intuition that motivated this study. Human scientific text is not Poisson, so a single distance from a Poisson process has almost no discriminating power. And the richer description that does work, a vector of rates and dispersion indices, works well mainly for the generator on which it was built. High within-generator accuracy is easy to obtain and easy to over-read. When the detector meets a generator it has not seen, accuracy falls to roughly 0.73 to 0.81, which is useful as a weak signal but not as a decision rule. Event rates are especially fragile because each generator has its own stylistic habits, some of which point in opposite directions relative to human writers. An organization that deployed such a screen would need to recalibrate it for each generator and venue, and expect it to decay as models change.

The clustering model improves matters somewhat. The gains are modest, a few hundredths of AUC, but they appear in nearly every comparison and held in a test fixed in advance on an unseen open-weight generator (+0.046). Dispersion also generalizes better than rates, and the direction of several dispersion differences agrees across generators. If a general signature of machine text exists in these features, it is more likely to be found in how events cluster than in how often they occur. We offer this as a hypothesis for larger studies with more generators, not as an established finding. We also tested the obvious way around generator-specific calibration, a screen that models human text alone and flags departures from it. It did not work here (Section 4.3), so avoiding the need for generator examples carries a large cost in accuracy, at least with these features and these simple models.

The judge comparison shows that the usefulness of an LLM judge depends heavily on which model is asked. GPT-4o as a judge was weak and, for Claude papers, wrong in the wrong direction. Gemini 2.5 Pro was excellent on GPT-4o and Llama papers, with almost no false alarms on human text, and it beat our cheap detectors there. Yet the same judge almost never flagged Claude papers, which suggests that even a strong judge can have a blind spot for the strongest generators. This blind spot is the more worrying result, because a screening organization cannot know in advance which kind of generator it faces. The count-based screen was weaker than the strong judge on two generators and stronger on the third, at a cost that is orders of magnitude lower. The two approaches look complementary. A simple rank average, specified in advance, improved on either alone for two generators and detected far more Claude papers than the judge did; a cascade that sends only the highest-scoring documents to the judge kept most of the judge's detection of GPT-4o and Llama papers at a fraction of the cost, provided machine papers were a small share of the pool. Neither arrangement helps much for Claude papers, which no method we tried detects well, and the fusion forgoes the screen's cost advantage because it needs the judge on every document. We tested one prompt and no examples for each judge, and a few-shot or fine-tuned judge could behave differently.

For governance, the practical value of these features lies in transparency and cost, not accuracy. A flag such as "unusually clustered passive constructions and almost no bracketed citations" can be explained to an author or an editor, and it costs nothing to compute. It is best treated as a low-cost first filter whose output is routed to human review, and not as grounds for action on its own.

# 6. Limitations

This is a pilot study, and its limits are material. The evidence comes from three commercial or hosted generators and a single genre, English-language scientific papers, so the results may not carry over to other models, languages, or text types. The sharp drop in transfer between GPT-4o and Claude is itself a warning that future releases may differ. Samples are modest: the Claude sample (152) is smaller than the GPT-4o (245) and Llama (202) samples because we capped generation to limit cost, and bootstrap intervals for cross-generator AUCs are about ±0.05. The confirmatory test uses one held-out generator, and the judged subset is small enough that the fusion and cascade results, which resample fewer than 100 distinct machine papers per generator, should be read as indicative.

Several features of the data construction could affect the results. We generated papers in four requests to reach analyzable length, which may introduce structural artifacts, such as inflated passive dispersion, and which is not how most users would produce a paper; Claude also wrote longer sections than GPT-4o, and we controlled for length only by truncation. Human papers come from two pipelines (XML and PDF conversion) while machine papers are plain text, so differences in how citations, formulas, and figures appear could shift counts, although medicine-only results suggest that extraction artifacts do not drive the judge comparison. Our prompts asked for in-text citations and a given structure, and rate differences such as those in square brackets may reflect these instructions and citation conventions; we did not examine citation style directly. Sampling human papers from 2015–2019 avoids contamination but may differ in style from papers written today.

The measurement and inference choices also have limits. Four windows per document give dispersion tests low power and make per-document dispersion estimates noisy, and passive and nominalization detection rely on patterns, not a parser. The clustering model was designed after we had seen the baseline results on GPT-4o and Claude, and the development comparisons (Table 5) include eight paired tests without correction for multiplicity. The Llama test is the stronger evidence, but it is one test, on one generator and one genre, using the same human papers as the development data. Its estimates rely on moment matching with four scales and are noisy for rare events. The one-class detectors were simple, using default settings and a small feature set, so Section 4.3 shows that these particular detectors fail, not that no human-only detector can succeed. The 5%-false-positive thresholds in the fusion and cascade analyses are set on the evaluated documents and are optimistic, rank normalization depends on the mix of documents in the pool, and the cascade assumes the prevalence of machine papers is known.

Finally, the comparison set is incomplete. We tested two zero-shot judges with one prompt on 500 excerpts of 2,000 tokens; GPT-4o is also a generator, so its verdicts on GPT-4o papers involve self-recognition, and twelve Gemini answers (2.4%) were unreadable and excluded, although scoring them as 50 gave the same conclusions. A different prompt, a few-shot or fine-tuned judge, or full papers might do better, and the count-based detectors use labeled examples that the judges do not. We did not run MAUVE or BERTScore, so we make no claim of advantage over embedding-based metrics. We did not test paraphrasing or light human editing of machine text, either of which could erode the signal, and we did not test whether explainable evidence improves the decisions of human reviewers.

# 7. Directions for Future Research

Four steps would turn this pilot into a fuller test. The first is to add generators, especially further open-weight models and future releases, evaluating each as a held-out case and replacing the Poisson benchmark with a negative binomial reference. The second is to extend the comparison with few-shot and fine-tuned judges and with MAUVE and BERTScore on identical documents, and to test the cascade on a real submission stream with realistic prevalence. The third is to test robustness to paraphrasing and light human editing, and to replicate the clustering model on new documents, ideally with full likelihood estimation, for example through a log-Gaussian Cox process, in place of moment matching. The fourth is a randomized experiment in which domain experts classify real and fabricated papers under three conditions (no indicator, an unexplained AI score, and an explainable count-based indicator), analyzed with ANOVA and planned contrasts after an a priori power analysis. Pre-registering the feature list, windows, and analysis plan would guard against analytic flexibility.

# 8. Conclusion

Counting small linguistic events is a cheap and transparent way to screen scholarly text, but the simplest version of the idea, a distance from a Poisson process, fails because human text is not Poisson. Richer count-based features detect machine-written papers well within a generator, and accuracy falls to between 0.73 and 0.81 on an unseen one. Dispersion transfers better than rates, and a model of how events cluster across scales improved detection modestly and consistently, including in a test fixed in advance on an open-weight generator. Against two zero-shot LLM judges, the screen beat GPT-4o, trailed a stronger judge (Gemini 2.5 Pro) on two generators, and beat it on the third, Claude, which both judges rarely flagged. Combining the screen with the stronger judge did better than either alone, and a cascade kept most of the judge's detection at a fraction of its cost when machine papers were rare. The evidence is limited to three generators, one genre, and two judges, and whether the approach helps human reviewers or compares well with embedding-based metrics remains untested.

# References

Cameron, A. C., and Trivedi, P. K. 2013. *Regression Analysis of Count Data* (2nd ed.). Cambridge, UK: Cambridge University Press.

Gehrmann, S., Strobelt, H., and Rush, A. M. 2019. "GLTR: Statistical Detection and Visualization of Generated Text," in *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations*, Florence, Italy, pp. 111–116.

Hevner, A. R., March, S. T., Park, J., and Ram, S. 2004. "Design Science in Information Systems Research," *MIS Quarterly* (28:1), pp. 75–105.

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., and Finn, C. 2023. "DetectGPT: Zero-Shot Machine-Generated Text Detection Using Probability Curvature," in *Proceedings of the 40th International Conference on Machine Learning*.

Pillutla, K., Swayamdipta, S., Zellers, R., Thickstun, J., Welleck, S., Choi, Y., and Harchaoui, Z. 2021. "MAUVE: Measuring the Gap Between Neural Text and Human Text Using Divergence Frontiers," in *Advances in Neural Information Processing Systems* (34).

Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., and Artzi, Y. 2020. "BERTScore: Evaluating Text Generation with BERT," in *Proceedings of the International Conference on Learning Representations*.

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., and Stoica, I. 2023. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems* (36), Datasets and Benchmarks Track.
