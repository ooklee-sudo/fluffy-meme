---
title: "Counting What Machines Cannot Fake? A Pilot Study of Poisson-Based Screening for LLM-Generated Scholarly Text"
subtitle: "Working paper, pilot evidence (two generators; human-subject experiment not yet conducted)"
---

# Abstract

Organizations that publish or archive scholarly documents now face a screening problem: language models can produce papers faster and more cheaply than anyone can check them. Two common remedies, LLM-as-a-judge and embedding-based similarity metrics, are either expensive and prompt-dependent or insensitive to fine-grained statistical structure. We study a lightweight alternative that treats the occurrence of selected linguistic events (special punctuation, discourse markers, passive constructions, nominalizations) as count processes and asks how far a document departs from human-authored text. Using 474 human-written papers from PubMed Central and arXiv (2015–2019) and matched papers from two generators (GPT-4o, 245 papers; Claude Sonnet 5.5, 152 papers), we report four findings. First, human text is not Poisson: for punctuation events, 36–49% of documents reject the Poisson null because of over-dispersion. Second, a single Poisson-distance index performs near chance (AUC 0.52–0.54), but a vector of event rates and dispersion indices separates human from machine text well when the detector is trained and tested on the same generator (AUC 0.99 for GPT-4o, 0.91 for Claude). Third, this performance does not transfer: a detector trained on one generator reaches only 0.73 (GPT-4o to Claude) and 0.81 (Claude to GPT-4o) on the other. Fourth, dispersion transfers better than event rates, which differ in sign across generators; this is the clearest support we find for the count-process idea. Screening costs nothing per document and runs at about 160 documents per second on one CPU core. The evidence is limited to two commercial generators and one genre, and we do not test adversarial editing, comparison with black-box metrics, or the effect on human reviewers.

**Keywords:** information quality, synthetic text detection, count data, dispersion, generalization, scholarly publishing

# 1. Introduction

Scholarly publishing has long treated fluent, well-structured prose as weak evidence of effort. Large language models weaken even that signal. A model can draft an abstract, a methods section, or a plausible set of results in a minute, and the output is often good enough to survive a quick read. For publishers, preprint servers, and research-integrity offices, the practical question is no longer whether such text exists but whether it can be screened at a cost that scales with submission volume, and in a way that a human reviewer can understand and contest.

Current options fit this need poorly. Asking a strong model to grade a document (LLM-as-a-judge; Zheng et al., 2023) is flexible, but each call costs money, the verdict depends on prompt wording and on the judge's own preferences, and the reasoning cannot be audited in any statistical sense. Embedding-based comparisons such as MAUVE (Pillutla et al., 2021) and BERTScore (Zhang et al., 2020) are cheaper, but they mainly measure whether two sets of texts *mean* similar things. They say little about whether the texts *behave* alike at the level of small, countable habits, such as how often a semicolon appears in a section.

This paper pursues a different idea. Writers do not plan the frequency of small linguistic events. A parenthesis here, a passive clause there: these accumulate as a by-product of content and habit, which is the setting in which count models are natural. Language models, in contrast, are trained to make each next token locally likely, and decoding choices can smooth or regularize how often particular forms recur. If so, machine-written text may differ from human text in the *distribution* of event counts, not only in their average, and a transparent statistical lens could pick this up at almost no cost.

The classical benchmark for counts of independent events is the Poisson distribution, whose variance equals its mean. An earlier version of this project assumed that human-authored scientific text approximately follows this benchmark and that LLM output departs from it. We test that assumption directly rather than adopting it. We also test something that detection studies often leave implicit: whether a detector built on one generator still works on another. We ask three questions, in the order a screening organization would:

- **RQ1 (Distributional fit).** Do human-authored papers follow a Poisson process in the selected events, and how does LLM-generated text differ?
- **RQ2 (Detection and transfer).** How well do Poisson-based quantities separate human from LLM-generated papers, which part of the signal (rates or dispersion) carries the discrimination, and does a detector built on one generator work on another?
- **RQ3 (Cost).** What does screening with these quantities cost in time and money?

A further question concerns whether explainable statistical evidence improves the decisions of human reviewers. It requires a controlled experiment with participants, which we have not run; we describe the intended design in Section 7 and report no results for it.

# 2. Background

**Information quality and governance.** The information quality literature treats accuracy and credibility as properties an organization has to monitor, not assume. Generative models change the economics of that monitoring because producing plausible content is now cheaper than verifying it. Screening cost per document is therefore a legitimate outcome alongside detection accuracy, a view consistent with the design-science tradition in information systems, in which an artifact is judged by whether it solves an organizational problem at acceptable cost (Hevner et al., 2004).

**Detection of machine-generated text.** Existing detectors include supervised classifiers, methods based on a language model's own probabilities (for example, Gehrmann et al., 2019; Mitchell et al., 2023), and judge-style evaluation. Most are opaque to the end user, and many degrade when the generating model changes. We trade breadth for transparency: every quantity we use can be traced to a specific, countable feature.

**Count data and dispersion.** For counts of independent events in fixed windows, the Poisson model implies a dispersion index (variance divided by mean) of one. Real text typically violates this, because topics, sections, and formatting conventions make events cluster. Count-data methods handle this by allowing extra variation, as in the negative binomial family (Cameron & Trivedi, 2013). The dispersion index is therefore best read as a descriptive summary of how clustered a document's events are, and we use it that way.

# 3. Data and Measures

## 3.1 Human-authored papers

We sampled English-language papers published between 2015 and 2019, before widespread use of LLMs for scientific writing. Papers came from the PubMed Central open-access subset (medicine; 300 sampled) and arXiv (computer science; 200 sampled), drawn at random within each source. For PubMed Central we used body paragraphs from the article XML. For arXiv we converted PDFs to text, removed the reference list, and joined broken lines. Documents shorter than 1,500 words were excluded, and the analysis requires at least four 500-token windows, which left 474 human papers.

## 3.2 Synthetic papers

For each sampled paper we asked a generator to write a paper on the same topic, given the original title and abstract, using one of three prompts of increasing detail. We used two generators through a commercial API gateway: GPT-4o and Claude Sonnet 5.5. A single request yielded only about 800 words from GPT-4o, too short for window-based analysis, so each paper was generated in four requests (introduction, methods, results, discussion and conclusion) and concatenated. Prompts were presented in a fixed random order, so each subset is random across fields.

GPT-4o produced 245 unique papers (one source had been generated twice during testing and we kept one record), with a median of about 2,750 words. Claude produced 152 papers, with a median of 4,566 words (range 3,667 to 5,134); generation was stopped at that number because of budget, not because of any property of the output. Because Claude wrote longer papers, all documents are truncated to the same length before analysis (Section 3.3). Both sets passed the length requirement.

## 3.3 Events and windows

Each document is cut into consecutive windows of 500 whitespace-delimited tokens, and only the first four windows (2,000 tokens) are retained for every document, human or synthetic, so that length cannot drive any result. In each window we count seven events: parentheses, square brackets, semicolons, paired quotation marks, a list of fourteen discourse markers (for example, *however*, *therefore*, *moreover*), passive constructions (a form of *be* plus a participle, identified by pattern matching), and nominalizations (words ending in *-tion*, *-ment*, *-ity*). The passive and nominalization patterns are approximate and will misclassify some words.

For each document and event we compute the mean count per window (the *rate*) and the dispersion index. A document-level Poisson test uses the statistic (n − 1) × dispersion index, compared to a chi-squared distribution with n − 1 degrees of freedom, with separate tail probabilities for over- and under-dispersion. With only four windows per document, these tests have low power, so rejection rates understate true departures from Poisson behavior.

## 3.4 Poisson-Score and feature vector

The Poisson-Score maps a document into the interval [0, 1) from its mean absolute standardized deviation, across all events, from a human reference distribution of (log) rates and (log) dispersion indices. The reference is estimated only on human training documents within each cross-validation fold. We also evaluate the underlying fourteen quantities (seven rates and seven dispersion indices) with logistic regression. Documents with no occurrences of an event have undefined dispersion, which we set to one (log zero); this affects mainly square brackets in synthetic text, where most papers contain none.

## 3.5 Evaluation

Detection is evaluated by five-fold cross-validation with all material from the same source paper kept in the same fold, so that a human paper and its synthetic counterpart never straddle training and test sets. We report the area under the ROC curve (AUC), with 95% bootstrap intervals over documents. To study transfer, we train on human papers plus papers from one generator and test on held-out human papers plus papers from the other generator, in both directions. The analysis code, prompts, and generated papers are in the project repository; the human papers can be re-collected with the included script.

# 4. Results

## 4.1 Human text is not Poisson (RQ1)

Table 1 reports, for each event, the median dispersion index and the share of documents whose counts reject the Poisson null in the direction of over-dispersion. Only discourse markers behave approximately as the Poisson model predicts in human text: the median index is 1.00 and 6% of documents reject, close to the 5% expected by chance. Punctuation events are clearly over-dispersed, with 49% of documents rejecting for square brackets, 42% for parentheses, and 36% for semicolons. Citations and formulas plausibly cluster in particular parts of a paper, such as the introduction and methods, and this clustering is exactly what a Poisson model cannot represent.

| Event | Human: index (% over) | GPT-4o: index (% over) | Claude: index (% over) |
|:--|--:|--:|--:|
| Square brackets | 2.53 (48.8) | 1.33 (36.4) | 1.22 (22.0) |
| Parentheses | 2.22 (42.2) | 1.78 (28.6) | 2.21 (40.1) |
| Semicolons | 2.00 (36.2) | 1.00 (12.4) | 2.00 (36.0) |
| Nominalizations | 1.67 (27.4) | 0.76 (7.3) | 1.10 (15.1) |
| Quotation marks | 1.30 (24.4) | 3.00 (60.0) | 2.00 (37.7) |
| Passive constructions | 1.20 (18.8) | 2.51 (47.3) | 1.79 (37.5) |
| Discourse markers | 1.00 (6.2) | 1.11 (7.8) | 1.22 (4.6) |

: Table 1. Median dispersion index and percentage of documents rejecting the Poisson null toward over-dispersion (5% level), by source. Index = variance / mean; 1 indicates Poisson behavior.

Machine text departs from human text in both directions, which argues against the simple story that it is uniformly "too regular". Nominalizations are less dispersed in both generators (medians 0.76 and 1.10, against 1.67 in human text), meaning they are spread more evenly. Passive constructions and quotation marks are more dispersed in both (passive 2.51 and 1.79 against 1.20; quotation marks 3.00 and 2.00 against 1.30). These directions agree across the two generators, which makes them more credible as features of machine writing than as quirks of one model. Figure 1 shows the full distributions for GPT-4o and human text.

![Figure 1. Distribution of log2 dispersion indices by event for human-authored and GPT-4o papers. Dashed line: Poisson (index of 1). Square brackets for GPT-4o are degenerate because most synthetic papers contain none (index set to one by convention).](fig_dispersion.png)

One caution applies to the passive result. Because we generated each paper section by section, and the four retained windows roughly track those sections, elevated passive dispersion may partly reflect a procedural artifact (passive voice is concentrated in methods text) rather than a general property of the models. We could not separate the two with the present data.

## 4.2 Detection within a generator (RQ2)

The single-index Poisson-Score performs close to chance: AUC 0.54 for GPT-4o and 0.52 for Claude. Treating its fourteen components as separate predictors changes the picture. With human papers and one generator, cross-validated logistic regression reaches AUC 0.987 for GPT-4o and 0.913 for Claude (Table 3, diagonal). Detection is clearly easier for GPT-4o than for Claude.

Event *rates* carry most of this within-generator signal (AUC 0.97 and 0.90), and dispersion alone remains informative (0.86 and 0.75). Table 2 shows why rates are generator-specific. GPT-4o uses far fewer square brackets, semicolons, and quotation marks than human authors, and more nominalizations and discourse markers. Claude differs in a different way: it uses *more* semicolons than human authors (3.54 per 500 tokens, against 1.95) and more quotation marks, and fewer discourse markers (1.08 against 1.84). Semicolons are lower than human in one generator and higher in the other, so a rule based on average frequency cannot describe machine text in general.

| Event | Human | GPT-4o | Claude |
|:--|--:|--:|--:|
| Parentheses | 9.80 | 7.39 | 11.39 |
| Square brackets | 4.46 | 0.21 | 0.41 |
| Semicolons | 1.95 | 0.51 | 3.54 |
| Quotation marks | 0.95 | 0.53 | 1.23 |
| Discourse markers | 1.84 | 2.38 | 1.08 |
| Passive constructions | 8.08 | 6.18 | 8.61 |
| Nominalizations | 24.43 | 34.08 | 27.34 |

: Table 2. Mean event count per 500-token window, by source.

## 4.3 Detection across generators (RQ2)

Table 3 gives the central robustness result. When the detector is trained on human text plus one generator and tested on the other, performance falls sharply. A GPT-4o-trained detector reaches an AUC of 0.73 on Claude papers (95% interval 0.69 to 0.78), down from 0.99 on GPT-4o itself. A Claude-trained detector reaches 0.81 on GPT-4o papers (0.78 to 0.84).

| Train → Test | Rates | Dispersion | Both |
|:--|:--|:--|:--|
| GPT-4o → GPT-4o | 0.971 [0.96, 0.98] | 0.856 [0.83, 0.88] | 0.987 [0.98, 0.99] |
| Claude → Claude | 0.904 [0.88, 0.93] | 0.751 [0.71, 0.80] | 0.913 [0.89, 0.94] |
| GPT-4o → Claude | 0.659 [0.62, 0.70] | 0.704 [0.65, 0.75] | 0.730 [0.69, 0.78] |
| Claude → GPT-4o | 0.728 [0.69, 0.76] | 0.808 [0.77, 0.84] | 0.810 [0.78, 0.84] |

: Table 3. AUC (95% bootstrap interval) by training and test generator and feature family. Training and test folds are grouped by source paper; test documents include held-out human papers.

Two patterns stand out. First, the gap between within-generator and cross-generator AUC is large for every feature family, so a detector calibrated on one generator should not be assumed to protect against another. Second, rates transfer worst (0.66 and 0.73), and dispersion transfers better (0.70 and 0.81), matching or exceeding the combined model in the Claude-to-GPT-4o direction. This is consistent with the sign pattern in Table 2: rate differences reverse across generators, while dispersion differences for passives, quotation marks, and nominalizations point the same way (Table 1). Dispersion is the more portable signal, though even it is far from sufficient on its own.

## 4.4 Cost (RQ3)

Computing all events and indices took about 6 milliseconds per document on one CPU core (roughly 160 documents per second) with no external service calls, so the marginal monetary cost is zero. For context on the generation side, producing one paper through four requests cost about US$0.04 and 38 seconds on average for GPT-4o, and about US$0.13 and 100 seconds for Claude, through the gateway we used. We did not run an LLM-as-a-judge baseline, so we cannot report a measured cost or latency ratio between the two screening methods; any such comparison would depend on the judge model, prompt length, and pricing at the time.

# 5. Discussion

The headline lessons are two. The intuitive version of the idea does not hold: human scientific text is not Poisson, and a single "distance from Poisson" score has almost no discriminating power. And the version that does work, a vector of rates and dispersion indices, works well only for the generator it was built on.

The second lesson matters for practice. High within-generator accuracy is easy to obtain and easy to over-read. When the detector meets a generator it has not seen, accuracy falls to roughly 0.73 to 0.81, which is useful as a weak signal but not as a decision rule. Event rates are especially fragile, because each generator has its own stylistic habits, including habits that point in opposite directions relative to human writers. An organization that deployed such a screen would need to recalibrate per generator and per venue, and to expect decay as models change.

The result is less discouraging for the count-process idea than for the rate-based version. Dispersion generalizes better than rates, and the direction of several dispersion differences agrees across two generators. If a general machine-text signature exists in these features, it is more likely to be found in how events cluster than in how often they occur. We see this as a hypothesis for larger studies with more generators, including open-weight models, rather than an established finding. A screen that models human text alone, and flags departures from it without training on any generator, may also transfer better; we have not tested this.

For governance, the practical value of these features is transparency and cost, not accuracy. A flag such as "unusually clustered passive constructions and almost no bracketed citations" can be explained to an author or editor, and it costs nothing to compute. It should therefore be treated as a low-cost first filter whose output is routed to human review, not as grounds for action on its own.

# 6. Limitations

This is a pilot, and several limitations are material.

1. **Two generators, both commercial.** The findings come from GPT-4o and Claude Sonnet 5.5. The large cross-generator drop is itself a warning that results for other models, including open-weight ones and future releases, may differ.
2. **Sample sizes.** The Claude sample (152) is smaller than the GPT-4o sample (245) and was cut short by budget. Bootstrap intervals for cross-generator AUCs are about ±0.05.
3. **Section-wise generation.** Papers were produced in four requests to reach analyzable length. This may introduce structural artifacts, including inflated passive dispersion, and it is not how most real users would produce a paper. Claude also wrote substantially longer sections than GPT-4o, and we did not control for that beyond truncating to the same length.
4. **Extraction differences.** Human papers come from two pipelines (XML and PDF conversion) while synthetic papers are plain text. Differences in how citations, formulas, and figures appear in extracted text could affect counts.
5. **Short windows and low power.** Four windows per document limit the power of dispersion tests and make per-document dispersion estimates noisy.
6. **Approximate events.** Passive and nominalization detection relies on patterns, not a parser.
7. **Prompting.** Our prompts asked for in-text citations and a particular structure. Rate differences (for example, in square brackets) may reflect these instructions and citation conventions, and we did not examine citation style directly.
8. **Pre-LLM human sample.** Sampling human papers from 2015–2019 avoids contamination but may differ in style from papers written today.
9. **No adversaries.** We did not test paraphrasing or light human editing of machine text, either of which could erode the signal.
10. **No black-box baselines and no reviewer experiment.** We did not compare against LLM-as-a-judge, MAUVE, or BERTScore, and we did not test whether explainable evidence improves human decisions. Claims about relative advantage over those methods are therefore not supported by this study.

# 7. Planned Extensions

Four steps would turn this pilot into a test of the full proposal. (i) Add further generators, especially open-weight models, and evaluate each as held out, together with a negative binomial reference and a human-only (one-class) detector that uses no generator data. (ii) Run MAUVE, BERTScore, and an LLM-as-a-judge baseline on identical documents, recording latency and cost. (iii) Test robustness to paraphrasing and light human editing. (iv) Conduct a randomized experiment in which domain experts classify real and fabricated papers under three conditions (no indicator, an unexplained AI score, and an explainable event-based indicator), analyzed with ANOVA and planned contrasts after an a priori power analysis. Pre-registering the feature list, windows, and analysis plan would guard against analytic flexibility.

# 8. Conclusion

Counting small linguistic events is a cheap and transparent way to screen scholarly text, but the simplest version of the idea, measuring distance from a Poisson process, does not work, because human text is not Poisson. A richer set of count-based features detects machine-generated papers well within a generator, but accuracy falls to between 0.73 and 0.81 on an unseen generator. Dispersion transfers better than event rates, and that is the clearest sign in our data that the count-process view captures something general. The evidence is limited to two generators and one genre, and whether the approach helps human reviewers or outperforms black-box metrics remains untested.

# References

*Verify details before submission.*

Cameron, A. C., and Trivedi, P. K. 2013. *Regression Analysis of Count Data* (2nd ed.). Cambridge University Press.

Gehrmann, S., Strobelt, H., and Rush, A. M. 2019. "GLTR: Statistical Detection and Visualization of Generated Text," in *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations*.

Hevner, A. R., March, S. T., Park, J., and Ram, S. 2004. "Design Science in Information Systems Research," *MIS Quarterly* (28:1), pp. 75–105.

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., and Finn, C. 2023. "DetectGPT: Zero-Shot Machine-Generated Text Detection Using Probability Curvature," in *Proceedings of the 40th International Conference on Machine Learning*.

Pillutla, K., Swayamdipta, S., Zellers, R., Thickstun, J., Welleck, S., Choi, Y., and Harchaoui, Z. 2021. "MAUVE: Measuring the Gap Between Neural Text and Human Text Using Divergence Frontiers," in *Advances in Neural Information Processing Systems* (34).

Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., and Artzi, Y. 2020. "BERTScore: Evaluating Text Generation with BERT," in *International Conference on Learning Representations*.

Zheng, L., Chiang, W.-L., Sheng, Y., et al. 2023. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems* (36).
