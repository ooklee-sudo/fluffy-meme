---
title: "Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs"
---

**Journal:** Empirical Software Engineering (Springer). **Article type:** Original research. **Status:** working draft, not yet submitted. To be re-typeset in the publisher's LaTeX template before submission.

**Authors:** [Author names, affiliations, ORCID, corresponding author e-mail]

## Abstract

Software that wraps or serves large language models (LLMs) is widely believed to degrade as the world drifts away from the data a model was trained on, and practitioners are advised to refresh models and their serving stacks on a schedule that balances cost against degradation. We ask whether the public record of the LLM software ecosystem is consistent with this view. We formalize a simple replacement model in which errors accumulate with drift and a refresh resets them at a fixed cost, derive three testable implications, and confirm by simulation that the model's parameters are recoverable when the assumptions hold. We then test the implications on three sources of evidence: weekly bug-report counts and release dates for three widely used open-source repositories (vLLM, Hugging Face Transformers, Ollama; 773 repository-weeks, 408 releases), and 478,498 English conversations from the WildChat corpus (April 2023 to April 2024) from which we measure prompt-distribution drift and user corrections. The evidence does not support the depreciation view. Bug reports are highest just after a release and then decline; the probability of a release does not rise with the time since the last one; and, once repeated automated prompt templates are removed, our drift measure does not predict user corrections. We also show that an uncorrected drift measure appears to predict corrections (p = 0.009) only because a single template comes to dominate the data. We discuss what these results imply for researchers who want to study AI-system maintenance, list the design requirements for a valid test, and release a replication package.

**Keywords:** software maintenance, large language models, concept drift, release engineering, mining software repositories, negative results

## 1 Introduction

Anyone who has run a language-model application in production has met the claim that it will age. The base model is frozen at a training cutoff, users keep asking about things that happened afterward, and the share of requests that go badly is expected to creep up until someone retrains, fine-tunes, or upgrades. The same expectation is built into practitioner guidance on monitoring and into the research literature on concept drift. It also shapes decisions: if degradation accumulates, a team should refresh before it becomes costly, and the right refresh interval depends on how fast the system degrades and how expensive a refresh is.

This paper asks a plain empirical question about that belief. If degradation accumulates and teams respond to it, what should we see in public data, and do we see it? Two signatures follow from the replacement-problem logic that software maintenance research has long borrowed from reliability engineering. First, the rate of reported problems should rise with the time since the last refresh. Second, the chance that a refresh happens in a given week should rise with the same elapsed time, since the longer the system has aged, the more likely a manager is to decide that renewal is worth its cost. A third signature concerns the cause: measured drift between user requests and the model's training window should predict worse outcomes.

We examine all three. For the first two we use the issue trackers and release histories of three open-source projects that sit between users and models. For the third we use a public corpus of real user conversations with ChatGPT-family models. Our contributions are as follows.

1. A small, explicit model of refresh timing that yields testable implications and whose parameters can be recovered by simulation, which we use as a benchmark for what the data would have to look like (Section 3).
2. Empirical evidence from three repositories and 478,498 conversations that the signatures of accumulating degradation are absent (Section 5).
3. A methodological caution: a plausible drift measure produced a statistically significant association with user corrections until we removed repeated automated templates (Section 5.3). We document how the contamination arises and how to detect it.
4. A replication package containing collection, measurement, and analysis code, and the weekly aggregates (Data availability).

We emphasize at the outset what the study does not show. The data cannot tell us whether commercial operators refresh in response to degradation, and a null result in open-source repositories does not imply that degradation is absent in production. It does tell us that these public sources are poor instruments for studying the question, and Section 6 draws out what a valid test would need.

**Research questions.**

- **RQ1.** Does the weekly rate of bug reports in LLM-ecosystem repositories increase with the time since the last release?
- **RQ2.** Does the probability of a release increase with the time since the last release?
- **RQ3.** Does measured prompt-distribution drift in a public chat corpus predict higher rates of user corrections?

## 2 Background and Related Work

**Software maintenance and release engineering.** Studies of rapid-release practice show that release cadence is often a fixed organizational choice, and that releases themselves are a source of defects and regressions. A repository with a regular cadence offers little room for timing decisions to respond to system state. We return to this point when interpreting RQ2.

**Mining software repositories.** Issue counts have long been used as a proxy for software quality, with well-known caveats: they reflect user attention and project popularity as much as defects, and labeling practices vary. We handle these concerns with an exposure offset and a keyword-and-label definition of a bug report (Section 4.1), and we revisit them in Section 6.

**Machine learning systems and technical debt.** Work on hidden technical debt in machine learning systems and on monitoring of deployed models argues that these systems accumulate maintenance burdens that traditional software does not. The concept-drift literature documents performance decline when the data distribution shifts, and studies of language models show worse performance on text from after the training period. These studies measure how quickly performance declines; they do not study how maintainers respond.

**Replacement and maintenance optimization.** The operations literature on optimal replacement derives threshold policies in which an asset is renewed once a deterioration index passes a critical level. Rust's dynamic discrete-choice formulation of bus-engine replacement made it possible to estimate renewal costs from observed replacement timing. Our model in Section 3 is a deliberately small member of that family, used here as a source of testable implications rather than as an estimator.

[Before submission: expand each paragraph with full citations and add the release-engineering and defect-prediction studies most relevant to LLM tooling. Verify every reference against the source.]

## 3 A Model of Refresh Timing and Its Testable Implications

### 3.1 Model

Time is discrete (weeks). Let $x_t$ be the accumulated drift since the last refresh. Each week drift advances, and each week the maintainer chooses to keep the system or refresh it. Errors arrive as a Poisson process with rate $\lambda_0+\gamma x_t$, where $\gamma>0$ is the marginal effect of drift. Each error costs the maintainer an amount $c$. A refresh costs $RC$ and resets drift. Payoffs include an unobserved shock with a Type I extreme-value distribution, so the refresh probability in state $x$ is logistic in the difference between the values of refreshing and keeping.

### 3.2 Properties used in the tests

The Bellman operator is a contraction, so the value function exists and is unique. By induction on value iteration, the value of keeping is non-increasing in $x$ and the value of refreshing does not depend on $x$, so the refresh probability is non-decreasing in drift. We also computed, for a wide range of parameter values, that the optimal drift threshold is increasing in the refresh cost and in the speed of drift, and decreasing in the discount factor (Appendix A). These comparative statics are numerical regularities, not proved results.

### 3.3 Testable implications

- **H1 (error signature).** The expected error count is increasing in the time since the last refresh: $\gamma>0$.
- **H2 (timing signature).** The refresh hazard is non-decreasing in the time since the last refresh.
- **H3 (drift signature).** Where drift can be measured directly, higher drift predicts a higher error rate.

RQ1 to RQ3 test H1 to H3, respectively. Because the cost of a refresh is identified only if H1 and H2 hold, a failure of either implies that estimating the cost from these data would not be interpretable, so we do not report such an estimate.

### 3.4 Simulation benchmark

To make sure the tests would detect the signatures if they were present, we simulated the model with $\gamma=0.5$, $RC=40$, $\lambda_0=5$, drift increments Poisson(1), and discount factor 0.95. The optimal policy refreshes at drift 14, where the expected error rate is 12.0, 2.4 times the baseline. Across 100 replications of 3,000 weeks, the two-step estimator recovered $\gamma$ (mean 0.499, SD 0.011) and $RC$ (mean 39.9, SD 1.0); estimating $\gamma$ and $RC$ jointly from choice data alone gave $RC$ with mean 40.1 and SD 3.0. Precision falls with sample length: the SD of the estimated $RC$ is 6.7 at 100 weeks, 4.8 at 250 weeks, 2.8 at 500 weeks, and 2.1 at 1,000 weeks. The repositories we study have between 173 and 414 weekly observations, so a cost estimate would be imprecise even under ideal conditions, which is a further reason to focus on testing H1 to H3.

## 4 Study Design

### 4.1 Repository data (RQ1, RQ2)

**Selection.** We looked for open-source projects in the LLM ecosystem whose releases are made by people and are neither absent nor automated. Of the six candidates we first tried, three were unusable: Qwen2.5 (0 GitHub releases in 140 weeks) and DeepSeek-V3 (1 release in 94 weeks) publish model weights elsewhere, and llama.cpp publishes automated builds (185 releases in 188 weeks) that carry no timing decision. The retained projects are vLLM, Hugging Face Transformers, and Ollama. This is a convenience sample chosen to satisfy these criteria, not a random sample, and we list it in full so that readers can judge the selection.

**Collection.** Using the GitHub REST API we collected every issue (excluding pull requests) created since 1 January 2023 and every non-draft, non-prerelease release. Issues were aggregated by ISO week. A bug report is an issue with a label containing "bug" or a title matching a fixed keyword list (bug, error, crash, fail, wrong, incorrect, regression, broken, exception). The age of a repository-week is the number of weeks since the last release.

| Repository | Weeks | Releases | Median cycle (weeks) | Mean bugs per week |
|---|---|---|---|---|
| vLLM | 186 | 76 | 2 | 54.3 |
| Transformers | 414 | 186 | 2 | 8.4 |
| Ollama | 173 | 146 | 1 | 36.3 |

### 4.2 Chat corpus (RQ3)

We use WildChat-1M, a public corpus of conversations with OpenAI chat models collected between April 2023 and April 2024. We kept English conversations (478,498 across 57 ISO weeks) and, for the drift tests, conversations with models whose training cutoff we assume to be around September 2021 (the gpt-3.5-turbo variants and gpt-4-0314 and gpt-4-0613; 381,201 conversations, of which 121,648 have at least two user turns). We use only aggregates and binary features; no conversation text is stored.

**Outcome.** A user correction is a later user turn whose opening words match a fixed pattern of correction or negative feedback (for example "no", "that's wrong", "that doesn't work", "try again", "you misunderstood"). Among multi-turn conversations, 3.2 percent contain at least one correction, and 1.25 percent of later user turns are corrections. Section 4.4 reports a validation of this detector, which turned out to have low recall.

**Drift.** We use two measures. The weekly measure is the Jensen–Shannon divergence between the distribution of first-prompt words in that week and in a reference window (the first four eligible weeks), computed over the 5,000 most frequent reference words. The conversation-level measure flags prompts that mention a year after the cutoff (2022 to 2024) or a product launched after it.

### 4.3 Analysis

For RQ1, we fit Poisson regressions of weekly bug counts on the weeks since release with an offset equal to the log of total weekly issues and a linear time trend. For RQ2, we fit logistic regressions of a release in a given week on the weeks since release, capping age at eight weeks. We report 90 percent intervals from a bootstrap that resamples whole release cycles. Because resampling cycles disturbs the time ordering, these intervals are indicative and should not be read as exact coverage. For RQ3, we regress the weekly correction rate on the drift measure by weighted least squares with autocorrelation-robust standard errors, adding a time trend and then controls for task mix (code share, log prompt length, mean turns, jailbreak-prompt share). At the conversation level, we fit logistic regressions of any correction on the drift flags with week fixed effects and week-clustered standard errors.

### 4.4 Validation of the correction detector

We drew a stratified random sample of 400 later user turns from four WildChat shards: 150 flagged by the detector (stratum A; 1,164 in the sampled shards), 150 unflagged turns containing a weak cue such as "error", "wrong", "I meant", "doesn't", or "again" (B; 5,419), and 100 unflagged turns without a cue (C; 98,958). The sample was shuffled and presented without its stratum, together with the tail of the preceding assistant message. A turn was labelled positive if it reports that the assistant's previous output was wrong, failed, or was not what was wanted (explicit rejection, "I meant", a factual correction, an error message from running the output, or a complaint), and negative if it is a new request, a refinement, a continuation, or an answer to the assistant's question; unclear cases were marked ambiguous. **The labelling was done by a single LLM annotator (Claude), not by humans**, using a codebook fixed beforehand; this is a limitation, and a human re-labelling of the same sample is planned before submission. Precision is the positive rate in stratum A; recall is the stratum-A share of the estimated positives in the population, using stratum sizes as weights; intervals are bootstrap percentile intervals, and ambiguous cases are counted as half-positive (sensitivity bounds are given in the text).

## 5 Results

### 5.1 RQ1: Bug reports fall after a release

Bug counts are highest in the first week after a release and decline afterward. For Transformers, the mean is 8.9 bugs per week in the first week, 4.0 in the second, 4.8 in weeks three and four, and 2.2 in weeks five to eight. For vLLM, the corresponding means are 60.3, 39.5, 40.2, and 26.7. The fitted slopes on age are negative for Transformers ($-0.016$ per week on the log scale) and vLLM ($-0.004$), and positive for Ollama (0.076).

| Repository | Bug log-rate slope | 90% interval | Release-hazard logit slope | 90% interval |
|---|---|---|---|---|
| vLLM | $-0.004$ | $[-0.077, -0.002]$ | 0.122 | $[-0.025, 0.719]$ |
| Transformers | $-0.016$ | $[-0.189, -0.018]$ | $-0.066$ | $[-0.144, 0.051]$ |
| Ollama | 0.076 | $[0.013, 0.127]$ | 0.116 | $[-0.342, 1.360]$ |

The positive Ollama slope rests on ages of one and two weeks only, since the project releases almost every week. In two of three repositories, then, the evidence points the opposite way from H1: the time just after a release is when the most problems are reported, which is consistent with releases introducing defects, with a burst of attention after announcements, or both. We cannot separate these explanations with issue counts alone.

### 5.2 RQ2: Release probability does not rise with age

For Transformers, the share of weeks with a release is about 47 percent at age one, 44 percent at age two, 43 percent at age three, and 42 percent at age four, which is flat and consistent with a fixed cadence. Release-hazard slopes have intervals that include zero in all three repositories (Table above). We therefore find no support for H2. Cadence-driven releasing leaves little scope for the timing of a refresh to respond to the state of the system, and the evidence is compatible with schedule-driven rather than state-driven release decisions.

### 5.3 RQ3: Drift does not predict corrections once templates are removed

With the raw drift measure, the weekly correction rate for the gpt-3.5 family is positively associated with drift after controlling for a time trend (slope 0.032, standard error 0.012, p = 0.009, 51 weeks). The association weakens when task-mix controls are added (0.021, p = 0.19), and the drift measure is almost collinear with time (correlation 0.93). Inspection of the underlying features reveals why. The share of weekly conversations mentioning a product from a short list of post-cutoff image and language tools rose from under 1 percent to 81 percent over the sample, because a single automated prompt template (a prompt-generation script) came to dominate the traffic. The drift measure was tracking the arrival of that template.

When we drop repeated first-prompt prefixes (retaining at most five conversations with the same first 80 characters per week), weekly drift ranges from 0.044 to 0.158 and its correlation with time falls to 0.60. The estimated slopes are 0.018 (p = 0.25) without further controls, 0.019 (p = 0.35) with a time trend, and 0.029 (p = 0.32) with task-mix controls. None is distinguishable from zero. Weekly analyses for the gpt-4 models rest on only eight weeks and are not informative.

At the conversation level, with week fixed effects, mentioning a post-cutoff year is not associated with a correction in the gpt-3.5 family (odds ratio 0.92, 95% CI 0.77 to 1.09; n = 110,319) or in the gpt-4 models (1.51, 0.86 to 2.63; n = 11,329). The product-mention flag gives 1.45 (0.80 to 2.63) and 1.29 (0.59 to 2.80) for the two groups, with intervals that include one. We do not find support for H3.

### 5.4 Validation of the correction detector

Of the 150 flagged turns, 119 were labelled positive and 5 ambiguous, a precision of 0.81 (90% interval 0.76 to 0.86; 0.79 to 0.83 under the two extreme treatments of ambiguous cases). Recall, however, is low: 44 of the 150 unflagged turns with a weak cue and 3 of the 100 unflagged turns without a cue were positive, so we estimate that the detector captures about 14 percent of corrections (90% interval 10 to 25 percent; 13 to 17 percent across the ambiguity treatments), for an F1 of about 0.24. About 25 percent of corrections occur in the cue stratum and 60 percent in the no-cue stratum. The most common missed cases are error messages or stack traces pasted back after running generated code, statements of the form "I meant ...", and corrections that do not begin with a negation.

This matters for RQ3. If the detector's misses were unrelated to drift, the correction rate we analysed would be a noisy, attenuated measure of the true rate, which would bias a drift coefficient toward zero and widen its interval; the null result for H3 is therefore weaker evidence than it would be with an accurate outcome. We cannot rule out that misses are related to the task mix (code-related turns are the main source of missed positives), in which case the bias could go either way. A second-generation detector that covers pasted error output and "I meant" constructions, evaluated on a fresh labelled sample, is the necessary next step; we do not use the present labels to tune the detector and then evaluate it on the same sample.

## 6 Discussion

**What the results mean.** None of the three signatures of accumulating degradation appears in these data. We take care not to read this as evidence that LLM-based systems do not degrade. The repositories we examine are developer tools whose releases follow engineering cadence, feature work, and defect fixes, so their release timing is not the decision the model describes. The chat corpus records users of a hosted service whose operator, not the users, decides when the model changes. What the results do show is that open-source release data and public chat logs are poor instruments for studying maintenance timing under drift, and that the apparent effects in such data can be artifacts.

**Why a valid test is hard.** Four requirements are not met by the data we could obtain, and they define what a future study needs. (1) The state variable must be measured directly and must vary independently of calendar time; with a single trending series, drift and time cannot be separated. (2) The outcome must measure model errors, not user attention or traffic mix; bug counts and correction regexes both fail on this point. (3) The refresh decision must be made by an identifiable maintainer facing the cost of acting, and the dates of refreshes must be known, not inferred from release tags. (4) The panel must be long enough to estimate a cost: our simulation shows that fewer than about 250 weekly observations per unit give an imprecise cost.

**A cautionary result for drift measurement.** The most transferable finding may be negative methodological. A reasonable-looking drift measure and a conventional regression produced a significant result that vanished when a single automated template was removed. Anyone computing distributional drift on public chat logs should check for repeated templates, report how much of the drift is attributable to the most frequent prompts, and test whether results survive de-duplication.

**Implications for practice.** Teams should be cautious about transferring scheduling advice from monitoring dashboards to release planning without evidence on their own error data. The post-release surge in bug reports suggests that the cost of a refresh may include a regression burden that standard cost models omit, and a team should account for it when deciding how often to refresh.

## 7 Threats to Validity

**Construct validity.** Bug reports measure what users choose to report, which depends on popularity and on attention around a release; our offset and trend controls address this only partly. The bug definition combines labels and keywords and may misclassify issues; we did not validate a sample of bug labels, and doing so is the first extension we would make. The correction measure is a pattern on the opening words of a user turn. Our validation (Section 5.4) found a precision of about 0.81 but a recall of only about 0.14; the validation labels were produced by a single LLM annotator and not yet by humans. The weekly drift measure captures change in word distribution and is affected by task mix and by automated traffic; our de-duplication addresses the dominant template we found but not necessarily all.

**Internal validity.** Because drift, calendar time, and model-version changes move together, associations are hard to attribute; we report collinearity and show results with and without a trend. The assumption that several model versions share a cutoff of about September 2021 is an approximation based on public statements and may be wrong for individual versions. Our bootstrap resamples cycles, which disturbs the time ordering, so interval estimates are indicative.

**External validity.** Three repositories chosen under explicit criteria are not a sample of the ecosystem, and one chat corpus from a single service and period is not a sample of deployments. The results should not be generalized to commercial operators or to other model families.

**Conclusion validity.** Several tests have wide intervals, and absence of a significant result is not evidence of absence. We therefore describe the evidence as not supporting the hypotheses and give interval estimates, and we avoid claims that the effects are zero.

**Reproducibility.** Collection depends on the state of the GitHub API at the time of collection (issues can be edited or deleted), and the replication package includes the weekly aggregates we used.

## 8 Conclusion

We asked whether the public record of the LLM software ecosystem shows the signatures of a system that degrades as drift accumulates and is refreshed in response. In three repositories and nearly half a million public conversations, it does not: problems peak after releases, release probability does not rise with age, and a de-duplicated drift measure does not predict user corrections. The more useful outcome may be the list of requirements for a valid test and the demonstration that a single automated template can manufacture a drift effect. We hope the replication package helps others with better-instrumented data, such as operators' own error logs and refresh histories, to carry out the test that these sources cannot.

## Appendix A. Numerical Comparative Statics (Simulation)

| Refresh cost $RC$ | 10 | 20 | 40 | 80 | 160 |
|---|---|---|---|---|---|
| Optimal drift threshold | 7 | 10 | 14 | 21 | 32 |

| Drift speed $\mu$ | 0.5 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|
| Optimal drift threshold | 11 | 14 | 17 | 19 |

| Discount factor $\beta$ | 0.90 | 0.95 | 0.99 |
|---|---|---|---|
| Optimal drift threshold | 16 | 14 | 13 |

## Declarations

**Funding.** [To be completed.]

**Conflicts of interest.** [To be completed.]

**Ethical approval and data protection.** The study uses public repository metadata and the public WildChat corpus (distributed with hashed identifiers). We store only aggregate counts and binary features and do not store or publish conversation text. [Confirm with the institutional review board whether review is required.]

**Data availability.** The replication package (collection, measurement and analysis scripts, weekly aggregates, simulation code) is available at [repository URL / archived DOI to be added]. Raw GitHub data can be re-collected with the supplied scripts; WildChat-1M is available from its publisher.

**Author contributions.** [To be completed.]

**Use of AI tools.** [Describe the use of AI assistance in drafting and coding, following the journal's policy.]

## References

Duncan, A. J. (1956). The economic design of $\bar X$ charts used to maintain current control of a process. *Journal of the American Statistical Association*, 51(274), 228–242.

Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A. (2014). A survey on concept drift adaptation. *ACM Computing Surveys*, 46(4), Article 44.

Lazaridou, A., et al. (2021). Mind the gap: Assessing temporal generalization in neural language models. *Advances in Neural Information Processing Systems*, 34.

Luu, K., et al. (2022). Time waits for no one! Analysis and challenges of temporal misalignment. *Proceedings of NAACL 2022*.

Rust, J. (1987). Optimal replacement of GMC bus engines: An empirical model of Harold Zurcher. *Econometrica*, 55(5), 999–1033.

Sculley, D., et al. (2015). Hidden technical debt in machine learning systems. *Advances in Neural Information Processing Systems*, 28.

Zhao, W., et al. (2024). WildChat: 1M ChatGPT interaction logs in the wild. *International Conference on Learning Representations*. [Verify.]

[Add remaining references for Section 2 and verify all entries against the originals.]
