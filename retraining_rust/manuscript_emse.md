---
title: "Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs"
---

**Journal:** Empirical Software Engineering (Springer). **Article type:** Original research. **Status:** working draft, not yet submitted; to be re-typeset in the publisher's template before submission.

**Authors:** [Author names, affiliations, ORCID iDs, corresponding author e-mail]

## Abstract

Software built around large language models (LLMs) is widely expected to degrade as the world drifts away from the data on which a model was trained, and practitioners are advised to refresh such systems on a schedule that balances the cost of renewal against the cost of degradation. We ask whether the public record of the LLM software ecosystem looks the way this view predicts. We state a small replacement model in which errors accumulate with drift and a refresh resets them at a fixed cost, derive three testable implications, and show by simulation that the model's parameters can be recovered when its assumptions hold. We then test the implications with weekly bug-report counts and release dates for 19 widely used open-source repositories (4,071 repository-weeks; 1,521 releases) and with 478,498 English conversations from the WildChat corpus (April 2023 to April 2024). None of the three implications is supported. Once total issue volume is controlled, bug reports do not rise with the time since the last release (pooled slope $-0.0005$ per week; 95% CI $-0.010$ to $0.009$); the probability of a release does not rise with that time either; and a measure of prompt drift does not predict user corrections once repeated automated templates are removed. The last test is weak, because our pattern-based detector finds only a small share of corrections and, in a validation sample, two labelers disagreed about what counts as one. We also show that an uncorrected drift measure appeared to predict corrections ($p = 0.009$) only because a single template had come to dominate the data. We list what a valid test of AI-system depreciation would require and release a replication package.

**Keywords:** software maintenance, large language models, concept drift, release engineering, mining software repositories, negative results

## 1 Introduction

Anyone who has run a language-model application in production has heard that it will age. The underlying model is frozen at a training cutoff, users keep asking about things that happened afterward, and the share of requests that go badly is expected to creep up until someone retrains, fine-tunes, or swaps the model. The same expectation runs through practitioner advice on monitoring and through the research literature on concept drift. It also shapes decisions. If degradation accumulates, a team should refresh before it becomes costly, and the right interval depends on how quickly the system degrades and how much a refresh costs.

This paper asks a plain empirical question about that belief: if degradation accumulates and teams respond to it, what should the public record show, and do we see it? Two signatures follow from the replacement logic that maintenance research has long borrowed from reliability engineering. The rate of reported problems should rise with the time since the last refresh, and the chance that a refresh happens in a given week should rise with that same elapsed time, since the longer a system has aged, the more likely it is that renewal is worth its cost. A third signature concerns the cause. Where drift between users' requests and a model's training window can be measured, more drift should go with worse outcomes.

We test all three. For the first two we use the issue trackers and release histories of 19 open-source projects that sit between users and models, such as inference engines, training libraries, and client SDKs. For the third we use a public corpus of real conversations with ChatGPT-family models. Our contributions are as follows.

1. A small, explicit model of refresh timing that yields testable implications and whose parameters can be recovered in simulation. We use it as a benchmark for what the data would have to look like (Section 3).
2. Evidence from 19 repositories and 478,498 conversations that the signatures of accumulating degradation are absent (Section 5).
3. A methodological caution. A plausible drift measure produced a statistically significant association with user corrections until we removed repeated automated templates, and we show how the contamination arises and how to detect it (Section 5.3).
4. A replication package with the collection, measurement, and analysis code and the weekly aggregates (Data availability).

We should say at the outset what the study does not show. The data cannot tell us whether commercial operators refresh in response to degradation, and a null result in open-source repositories does not imply that degradation is absent in production. What it does show is that these public sources are poor instruments for studying the question, and Section 6 sets out what a valid test would need.

**Research questions.**

- **RQ1.** Does the weekly rate of bug reports in LLM-ecosystem repositories increase with the time since the last release?
- **RQ2.** Does the probability of a release increase with the time since the last release?
- **RQ3.** Does measured prompt-distribution drift in a public chat corpus predict higher rates of user corrections?

## 2 Background and Related Work

**Release engineering and software quality.** Rapid-release practice has been studied extensively. Khomh et al. (2012), for example, compared Firefox versions built on shorter and traditional release cycles and found that the shorter cycles did not produce significantly more post-release bugs, although crashes appeared earlier in execution and bugs were fixed faster. Two points from this literature matter here. Release cadence is often a fixed organizational choice, and a release is itself an event that can introduce defects. A project that ships on a schedule leaves little room for the timing of a release to respond to the state of the system, which is the point we return to when interpreting RQ2.

**Machine-learning systems and technical debt.** Studies of industrial practice describe machine-learning work as data-centric and as bringing maintenance burdens that traditional software does not have (Sculley et al. 2015; Amershi et al. 2019). Software engineers have also begun to study the ecosystems around pre-trained models, for example how practitioners decide to reuse models from the Hugging Face registry (Jiang et al. 2023). Our setting overlaps with this work but isolates one mechanism: the loss of fit between a frozen model and a moving environment.

**Drift and temporal degradation.** The concept-drift literature documents declining predictive performance when the data distribution shifts (Gama et al. 2014). For language models, performance has been shown to be worse on text from after the training period (Lazaridou et al. 2021; Luu et al. 2022), and Chen et al. (2024) found that the behavior of hosted GPT-3.5 and GPT-4 services changed substantially between March and June 2023. These studies measure how performance changes. They do not study how, or whether, maintainers respond to it.

**Replacement and maintenance optimization.** The operations literature on optimal replacement derives threshold policies in which an asset is renewed once a deterioration index passes a critical level (for an early treatment in quality control, see Duncan 1956). Rust (1987) turned the replacement problem into an econometric one by adding unobserved payoff shocks, so that observed replacement timing could be used to estimate the cost of renewal; later work on conditional choice probabilities and on the properties of such estimators supplies the surrounding toolkit (Hotz and Miller 1993; Aguirregabiria and Mira 2010). The model in Section 3 is a deliberately small member of this family. We use it as a source of testable implications and not as an estimator.

## 3 A Model of Refresh Timing and Its Testable Implications

### 3.1 Model

Time is discrete and measured in weeks. A maintainer operates one deployed system. Let $x_t$ denote the drift accumulated since the system was last refreshed, where a refresh stands for any renewal action (retraining, fine-tuning, or upgrading the underlying model). Each week drift advances, and the maintainer chooses either to keep the system or to refresh it. Errors arrive as a Poisson process with rate $\lambda_0+\gamma x_t$, where $\gamma>0$ is the marginal effect of drift on the error rate. Each error costs the maintainer an amount $c$, and a refresh costs $RC$ and resets drift. Payoffs include an unobserved shock with a Type I extreme-value distribution, so the probability of a refresh in state $x$ is logistic in the difference between the value of refreshing and the value of keeping.

### 3.2 Properties used in the tests

The Bellman operator is a contraction, so the value function exists and is unique. By induction on value iteration, the value of keeping the system is non-increasing in $x$ while the value of refreshing does not depend on $x$, so the refresh probability is non-decreasing in drift. We also computed, over a wide range of parameter values, that the optimal drift threshold is increasing in the refresh cost and in the speed of drift and decreasing in the discount factor (Appendix A). These comparative statics are numerical regularities and not proved results.

### 3.3 Testable implications

- **H1 (error signature).** The expected error count increases with the time since the last refresh, that is, $\gamma>0$.
- **H2 (timing signature).** The refresh hazard is non-decreasing in the time since the last refresh.
- **H3 (drift signature).** Where drift can be measured directly, higher drift predicts a higher error rate.

RQ1 to RQ3 test H1 to H3, respectively. The cost of a refresh is identified only if H1 and H2 hold, so a failure of either means that a cost estimated from these data could not be interpreted, and we do not report one.

### 3.4 Simulation benchmark

To check that our tests would detect the signatures if they were present, we simulated the model with $\gamma=0.5$, $RC=40$, $\lambda_0=5$, Poisson(1) drift increments, and a discount factor of 0.95. The optimal policy refreshes at a drift of 14, where the expected error rate is 12.0, or 2.4 times the baseline. Across 100 replications of 3,000 weeks, a two-step estimator recovered $\gamma$ (mean 0.499, SD 0.011) and $RC$ (mean 39.9, SD 1.0), and estimating $\gamma$ and $RC$ jointly from choice data alone gave an $RC$ with mean 40.1 and SD 3.0. Precision falls with sample length: the SD of the estimated $RC$ is 6.7 at 100 weeks, 4.8 at 250 weeks, 2.8 at 500 weeks, and 2.1 at 1,000 weeks. The repositories we study have between 145 and 414 weekly observations, so a cost estimate would be imprecise even under ideal conditions. This is a further reason to concentrate on testing H1 to H3.

## 4 Study Design

### 4.1 Repository data (RQ1, RQ2)

**Selection.** We looked for open-source projects in the LLM ecosystem whose releases are made by people and are neither absent nor automated. The selection had three steps, and we report all of them. First, we tried six prominent candidates. Qwen2.5 (0 GitHub releases in 140 weeks) and DeepSeek-V3 (1 release in 94 weeks) publish model weights elsewhere, and llama.cpp publishes automated builds (185 releases in 188 weeks) that carry no timing decision. vLLM, Hugging Face Transformers, and Ollama were retained. Second, so as not to rely on three projects, we fixed a list of 17 further repositories before collecting any data on them: inference and training frameworks, client SDKs, agent frameworks, and evaluation tools in the LLM ecosystem, chosen by the authors from general knowledge of the field without looking at their issue or release histories. Third, we applied an eligibility rule that was also fixed in advance, namely at least 10 releases and at least 80 weeks of data. One of the 20 collected repositories (mlc-llm, with no releases) was ineligible, which leaves 19. This is a convenience sample of prominent projects and not a random sample of the ecosystem, and nearly all of them are software and tooling and not model-retraining pipelines. In what follows, a release is therefore a proxy for a refresh.

**Collection.** Using the GitHub REST API we collected every issue created since 1 January 2023 (excluding pull requests) and every non-draft, non-prerelease release. Issues were aggregated by ISO week. A bug report is an issue with a label containing "bug" or a title matching a fixed keyword list (bug, error, crash, fail, wrong, incorrect, regression, broken, exception). The age of a repository-week is the number of weeks since the last release.

| Repository | Weeks | Releases | Median cycle (weeks) | Bug log-rate slope (SE) | Release-hazard logit slope (SE) |
|---|---|---|---|---|---|
| anthropics/anthropic-sdk-python | 194 | 123 | 1 | -0.016 (0.079) | -0.229 (0.093) |
| Dao-AILab/flash-attention | 203 | 49 | 2 | -0.007 (0.016) | -0.294 (0.063) |
| EleutherAI/lm-evaluation-harness | 268 | 19 | 10 | 0.002 (0.019) | 0.117 (0.160) |
| ggml-org/whisper.cpp | 200 | 33 | 4 | 0.013 (0.016) | -0.105 (0.069) |
| Hugging Face Transformers | 414 | 186 | 2 | -0.016 (0.033) | -0.066 (0.063) |
| huggingface/accelerate | 293 | 60 | 4 | -0.033 (0.031) | 0.045 (0.077) |
| huggingface/diffusers | 222 | 61 | 2.5 | -0.001 (0.014) | -0.024 (0.057) |
| huggingface/peft | 194 | 30 | 7 | 0.004 (0.017) | 0.115 (0.073) |
| huggingface/text-generation-inference | 167 | 58 | 2 | -0.049 (0.036) | -0.153 (0.094) |
| huggingface/trl | 197 | 79 | 2 | -0.043 (0.037) | 0.038 (0.130) |
| lm-sys/FastChat | 185 | 14 | 3 | 0.003 (0.046) | -0.403 (1.014) |
| microsoft/autogen | 187 | 59 | 1 | -0.040 (0.037) | -0.482 (0.168) |
| microsoft/semantic-kernel | 189 | 121 | 1 | 0.003 (0.150) | -0.522 (0.111) |
| NVIDIA/TensorRT-LLM | 157 | 23 | 6 | 0.018 (0.016) | 0.172 (0.144) |
| Ollama | 173 | 146 | 1 | 0.076 (0.034) | 0.116 (0.541) |
| openai/openai-python | 299 | 181 | 1 | -0.027 (0.043) | -0.343 (0.049) |
| run-llama/llama_index | 198 | 153 | 1 | -0.031 (0.032) | -0.564 (0.098) |
| sgl-project/sglang | 145 | 50 | 2 | 0.002 (0.013) | 0.172 (0.089) |
| vLLM | 186 | 76 | 2 | -0.004 (0.012) | 0.122 (0.268) |

Table 1: Eligible repositories (4,071 repository-weeks; 1,521 releases) and repository-level slopes (Section 4.3).

### 4.2 Chat corpus (RQ3)

We use WildChat-1M (Zhao et al. 2024), a public corpus of conversations with OpenAI chat models collected between April 2023 and April 2024. We kept the English conversations (478,498 across 57 ISO weeks). For the drift tests we used conversations with models whose training cutoff we take to be about September 2021, namely the gpt-3.5-turbo variants, gpt-4-0314, and gpt-4-0613 (381,201 conversations, of which 121,648 have at least two user turns). We store only aggregates and binary features, and no conversation text is kept.

**Outcomes.** Our main outcome is a user correction, defined as a later user turn whose opening words match a fixed pattern of correction or negative feedback (for example "no", "that's wrong", "that doesn't work", "try again", "you misunderstood"). Among multi-turn conversations, 3.2 percent contain at least one such turn, and 1.25 percent of later user turns are corrections. A second detector (v2) adds cues anywhere in the first 200 characters, such as "I meant", pasted error output, and "still not working". Section 4.4 describes how both detectors were validated; the validation shows that their recall is low. As an outcome that does not rely on pattern matching, we also count re-asks, meaning consecutive user turns whose word sets overlap (Jaccard similarity of at least 0.6, with at least four words each).

**Drift.** We use two measures. The weekly measure is the Jensen–Shannon divergence between the distribution of first-prompt words in a given week and in a reference window (the first four eligible weeks), computed over the 5,000 most frequent reference words. The conversation-level measure flags prompts that mention a year after the cutoff (2022 to 2024) or a product launched after it.

### 4.3 Analysis

For RQ1 we fit Poisson regressions of weekly bug counts on the weeks since release, with an offset equal to the log of total weekly issues and a linear time trend. For RQ2 we fit logistic regressions of a release in a given week on the weeks since release, capping age at eight weeks. Repository-level standard errors come from a cluster bootstrap that resamples whole release cycles while keeping each observation's calendar time, and the repository-level slopes are pooled with a random-effects model (DerSimonian and Laird 1986). We report 95 percent intervals for the pooled estimates, together with robustness checks that drop the repositories with a median cycle of one week, condition on surviving the first week after a release (RQ2), and drop the issue-volume offset (RQ1).

For RQ3 we regress the weekly correction rate on the drift measure by weighted least squares with autocorrelation-robust standard errors, first with a time trend and then with controls for task mix (code share, log prompt length, mean number of turns, and the share of jailbreak-style prompts). At the conversation level we fit logistic regressions of any correction on the drift flags, with week fixed effects and standard errors clustered by week.

### 4.4 Validation of the correction detector

We validated the detectors in three stages. In the first stage we drew a stratified random sample of 400 later user turns from four WildChat shards: 150 flagged by the first detector (stratum A; 1,164 such turns in the sampled shards), 150 unflagged turns containing a weak cue such as "error", "wrong", "I meant", "doesn't", or "again" (B; 5,419), and 100 unflagged turns without a cue (C; 98,958). The sample was shuffled and shown without its stratum, together with the end of the preceding assistant message. A turn was labeled positive if it reported that the assistant's previous output was wrong, had failed, or was not what the user wanted (an explicit rejection, an "I meant" clarification, a factual correction, an error message from running the output, or a complaint). It was labeled negative if it was a new request, a refinement, a continuation, or an answer to a question the assistant had asked, and unclear cases were marked ambiguous. These labels were produced by a single AI annotator (Claude) using a codebook fixed beforehand, not by humans.

Because the first detector (v1) turned out to have low recall, we built a second one (v2) from the codebook categories and evaluated both on a fresh sample that had not been used in its design: 350 turns from four other shards (150 flagged by v2, 100 unflagged with a weak cue, and 100 unflagged without one; stratum sizes 5,513, 5,193, and 116,835), labeled by the same procedure. In the third stage, one of the authors labeled a random subsample of 100 of these 350 turns alone, with the same codebook and without access to the AI labels or detector flags.

Precision is the positive rate among flagged turns. Recall is the share of all estimated positives in the population that lie in the flagged stratum, with strata weighted by their population sizes. Intervals are bootstrap percentile intervals, and ambiguous cases are counted as half-positive; we give the extreme treatments in the text.

## 5 Results

### 5.1 RQ1: Bug reports do not increase with the age of a release

Pooling the 19 repository-level slopes with a random-effects model, the log-rate slope of bug reports on weeks since release is $-0.0005$ per week (95% CI $-0.010$ to $0.009$), with no detectable heterogeneity across repositories ($\tau^2 = 0$). The estimate is precise enough to rule out, for instance, a 1 percent weekly increase in the bug rate. Eight of the 19 repository-level slopes are positive and 11 are negative. This is not what H1 predicts.

Raw bug counts do fall with age. Without the offset for total issue volume the pooled slope is $-0.023$ (95% CI $-0.047$ to $0.001$), and in an early look at Transformers, bug counts fell from 8.9 per week in the first week after a release to 2.2 after five weeks. Once we account for the total number of issues filed, however, the decline disappears. The early surge therefore appears to be a general burst of issue-filing right after a release, driven by attention, announcements, and defects together, and not a change in the share of reports that concern bugs. Issue counts alone cannot separate these explanations.

### 5.2 RQ2: Release probability does not rise with age

The pooled release-hazard logit slope is $-0.125$ per week of age (95% CI $-0.228$ to $-0.022$; $\tau^2 = 0.036$), so a release is less likely, not more likely, in a given week when more weeks have passed since the last one. Eight of the 19 repository-level slopes are positive. The negative pooled estimate comes mostly from repositories that release weekly and publish hot-fixes soon after a release. Excluding the six repositories with a median cycle of one week gives $-0.016$ (95% CI $-0.101$ to $0.069$), and conditioning on surviving the first week (ages of two weeks or more) gives $-0.059$ (95% CI $-0.146$ to $0.029$). We therefore find no support for a hazard that rises with age, which H2 requires. The evidence fits releasing that follows a schedule or reacts to hot-fixes, and cadence-driven releasing leaves little scope for timing to respond to the state of the system.

### 5.3 RQ3: Drift does not predict corrections once templates are removed

**The raw drift measure.** With the raw measure, the weekly correction rate for the gpt-3.5 family is positively associated with drift once a time trend is included (slope 0.032, SE 0.012, $p = 0.009$; 51 weeks). The association weakens when task-mix controls are added (0.021, $p = 0.19$), and drift is nearly collinear with time (correlation 0.93). Inspecting the underlying features shows why. The share of weekly conversations mentioning a product from a short list of post-cutoff image and language tools rose from under 1 percent to 81 percent over the sample, because a single automated prompt template, a prompt-generation script, came to dominate the traffic. The drift measure was tracking the arrival of that template.

**After removing repeated templates.** When we keep at most five conversations per week with the same first 80 characters, weekly drift ranges from 0.044 to 0.158 and its correlation with time falls to 0.60. The estimated slopes are 0.018 ($p = 0.25$) without further controls, 0.019 ($p = 0.35$) with a time trend, and 0.029 ($p = 0.32$) with task-mix controls, and none is distinguishable from zero. At the conversation level, with week fixed effects, mentioning a post-cutoff year is not associated with a correction in the gpt-3.5 family (odds ratio 0.92, 95% CI 0.77 to 1.09; $n = 110{,}319$) or in the gpt-4 models (1.51, 0.86 to 2.63; $n = 11{,}329$). The product-mention flag gives 1.45 (0.80 to 2.63) and 1.29 (0.59 to 2.80), with intervals that include one. Weekly analyses for the gpt-4 models rest on only eight weeks and are not informative. We find no support for H3.

**A second detector and a pattern-free outcome.** Replacing the outcome with the higher-recall v2 detector (Section 5.4) leaves the gpt-3.5 conclusions unchanged. The weekly drift slopes are 0.015 ($p = 0.51$), 0.021 ($p = 0.47$), and $-0.023$ ($p = 0.78$) across the three specifications, and the conversation-level odds ratio for a post-cutoff year is 0.93 (95% CI 0.80 to 1.08; $n = 110{,}319$). For the gpt-4 models, v2 gives an odds ratio of 0.57 (0.44 to 0.73), an unexpected negative association that appears neither with v1 nor in the gpt-3.5 models. Because v2 flags pasted error output, this may reflect differences in task mix, such as the share of code-related turns, and not correction behavior, and we do not interpret it. Using re-asks as an outcome, 22 percent of multi-turn conversations contain one. We have not validated this proxy, and we expect it to be contaminated by batch workflows in which users submit the same instruction repeatedly with different content. The weekly gpt-3.5 slopes are 0.004 ($p = 0.97$), 0.043 ($p = 0.63$), and 0.367 ($p = 0.24$) across the three specifications, and the conversation-level odds ratio for a post-cutoff year is 0.87 (95% CI 0.79 to 0.97), so conversations that mention later years contain somewhat fewer re-asks, the opposite of H3. The weekly gpt-4 regressions, with eight observations and up to five regressors, are not interpretable.

**What the design could detect.** With standard errors of 0.020 (v1) and 0.028 (v2) in the specification with a time trend, a weekly slope would have to exceed about 0.057 (v1) or 0.079 (v2) to be detected with 80 percent power at the 5 percent level. Across the observed range of the drift measure, these thresholds correspond to increases of about 52 percent (v1) and 23 percent (v2) in the observed correction rate. The study can therefore exclude large effects only, and only for the share of corrections that the detectors capture.

### 5.4 Validation of the correction detector

**First sample (AI labels).** Of the 150 flagged turns, 119 were labeled positive and 5 ambiguous, which gives a precision of 0.81 (90% interval 0.76 to 0.86; 0.79 to 0.83 under the two extreme treatments of ambiguous cases). Recall is low. Of the 150 unflagged turns with a weak cue, 44 were positive, as were 3 of the 100 unflagged turns without a cue, so we estimate that the detector captures about 14 percent of corrections (90% interval 10 to 25 percent; 13 to 17 percent across treatments), for an F1 of about 0.24. Roughly a quarter of the corrections fall in the weak-cue stratum and 60 percent in the no-cue stratum. The most common misses are error messages and stack traces pasted back after running generated code, statements of the form "I meant ...", and corrections that do not begin with a negation.

**Second detector (fresh sample, AI labels).** On the fresh sample, v1 had a precision of 0.80 (90% interval 0.71 to 0.89) and a recall of 0.09 (0.06 to 0.14), consistent with the first sample. The v2 detector had a precision of 0.73 (0.68 to 0.79) and a recall of 0.27 (0.20 to 0.39), for an F1 of 0.39 (0.31 to 0.51) against 0.17 (0.12 to 0.24) for v1. Recall of v2 ranges from 0.24 to 0.30 across the ambiguity treatments. About 65 percent of the estimated corrections are in the no-cue stratum, which a pattern-based detector cannot reach.

**Human labels.** On the 100-turn subsample, the human labeler marked 55 turns as corrections, 34 as non-corrections, and 11 as unclear; the AI annotator marked 41, 53, and 6 on the same turns. On the 83 turns that both considered clear, agreement was 65 percent and Cohen's kappa (Cohen 1960) was 0.34, which is conventionally read as fair (Landis and Koch 1977). The disagreement is one-sided. Of the 29 discordant turns, 24 were corrections for the human and not for the AI annotator, and 5 the other way. The 24 are mostly requests to rewrite, revise, or redo an earlier output, resubmissions of a task template, and follow-up questions that challenge an earlier answer. The human appears to have applied a broader criterion, any turn asking for a different output, than our codebook, which treated refinements as non-corrections. We did not adjudicate the differences.

Because the human labels are more inclusive, they imply lower recall. Weighting the subsample back to the population, v1 has a precision of 0.90 (90% interval 0.77 to 1.00) and a recall of 0.05 (0.03 to 0.09), and v2 has a precision of 0.79 (0.69 to 0.89) and a recall of 0.12 (0.08 to 0.18), again counting ambiguous cases as half-positive. These intervals are wide because the subsample is small. Across labelers and detectors, recall falls between about 5 and 30 percent, and we regard it as low under any reasonable criterion, while the precision of flagged turns is acceptable. That two labelers working from the same codebook disagreed this much shows that "user correction" is not a self-evident construct.

**Implications for RQ3.** If the detectors' misses were unrelated to drift, the correction rate we analyzed would be a noisy and attenuated measure of the true rate. This would bias a drift coefficient toward zero and widen its interval, so the null result for H3 is weaker evidence than it would be with an accurate outcome. We cannot rule out that the misses are related to task mix, since code-related turns are the main source of missed positives, in which case the bias could go either way.

## 6 Discussion

**What the results mean.** None of the three signatures of accumulating degradation appears in these data, and we are careful not to read this as evidence that LLM-based systems do not degrade. The repositories we examined are developer tools whose releases follow engineering cadence, feature work, and defect fixes, so their release timing is not the decision that the model describes. The chat corpus records users of a hosted service, and it is the operator, not the users, who decides when the underlying model changes. What the results do show is that open-source release data and public chat logs are poor instruments for studying maintenance timing under drift, and that apparent effects in such data can be artifacts.

**Why a valid test is hard.** The data we could obtain fall short of four requirements, and together they describe what a future study needs. First, the state variable must be measured directly and must vary independently of calendar time, because with a single trending series drift and time cannot be separated. Second, the outcome must measure model errors and not user attention or traffic mix; bug counts and pattern-based correction detectors both fail here. Third, the refresh decision must be made by an identifiable maintainer who faces the cost of acting, and the dates of refreshes must be known and not inferred from release tags. Fourth, the panel must be long enough to estimate a cost, and our simulation suggests that fewer than about 250 weekly observations per unit leave the cost imprecise.

**A cautionary result for drift measurement.** The most transferable finding may be a methodological one. A reasonable-looking drift measure and a conventional regression produced a significant result that vanished when a single automated template was removed. Anyone computing distributional drift on public chat logs should check for repeated templates, report how much of the measured drift is attributable to the most frequent prompts, and test whether the results survive de-duplication.

**Implications for practice.** Our results offer limited practical guidance, and we would not read them as advice to stop refreshing. They suggest that a team should be wary of importing scheduling rules from monitoring dashboards without evidence from its own error data, since in the public data the time since the last release is not a useful predictor of problems. They also point to a cost that standard replacement models omit: the burst of issue-filing after a release suggests that a refresh comes with its own regression and support burden, which a team should count when it decides how often to refresh.

## 7 Threats to Validity

**Construct validity.** Bug reports measure what users choose to report, which depends on popularity and on attention around a release, and our offset and trend controls address this only in part. The bug definition combines labels and keywords and may misclassify issues; we did not validate a sample of bug labels, and doing so is the first extension we would make. The correction measure is a pattern on the opening words of a user turn. Our validation found a precision of about 0.8 and a recall between 0.05 and 0.3 depending on the detector and the labeler (Section 5.4), and the human validation rests on one labeler and 100 turns. Agreement between the human and AI labelers was only fair (kappa 0.34), and v2 was designed after the AI annotator had seen examples from the first sample, although it was evaluated on a fresh one. The weekly drift measure captures change in the word distribution and is affected by task mix and by automated traffic. Our de-duplication handles the dominant template we found, but not necessarily every one.

**Internal validity.** Because drift, calendar time, and model-version changes move together, associations are hard to attribute; we report the collinearity and show results with and without a trend. The assumption that several model versions share a training cutoff of about September 2021 is an approximation based on public statements and may be wrong for individual versions.

**External validity.** Twenty repositories chosen under explicit criteria are not a sample of the ecosystem, and they are software and tooling and not model-retraining pipelines. One chat corpus from a single service and period is not a sample of deployments either. The results should not be generalized to commercial operators or to other model families.

**Conclusion validity.** Several tests have wide intervals, and the absence of a significant result is not evidence of absence. We therefore say that the evidence does not support the hypotheses, give interval estimates, and avoid claiming that the effects are zero.

**Reproducibility.** Collection depends on the state of the GitHub API at the time of collection, since issues can be edited or deleted afterward, and for this reason the replication package includes the weekly aggregates we used.

## 8 Conclusion

We asked whether the public record of the LLM software ecosystem shows the signatures of a system that degrades as drift accumulates and is refreshed in response. In 19 repositories and nearly half a million public conversations it does not. Bug reports do not increase with the age of a release once total issue volume is controlled, release probability does not rise with age, and a de-duplicated measure of drift does not predict user corrections. The more useful results may be the list of requirements for a valid test and the demonstration that a single automated template can manufacture a drift effect. We hope that the replication package helps others with better-instrumented data, such as operators' own error logs and refresh histories, to run the test that these public sources cannot support.

## Appendix A. Numerical comparative statics (simulation)

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

**Funding.** [State the funding sources, or "The authors received no specific funding for this work."]

**Competing interests.** [State any competing interests, or "The authors have no competing interests to declare that are relevant to the content of this article."]

**Ethics approval and data protection.** The study uses public repository metadata and the public WildChat corpus, which is distributed with hashed identifiers. We store only aggregate counts and binary features and neither store nor publish conversation text. [Confirm with the institutional review board whether a formal review or exemption statement is required.]

**Data availability.** The replication package (collection, measurement, and analysis scripts; weekly aggregates; simulation code; labeling codebook and labels, without conversation text) is available at https://github.com/ooklee-sudo/fluffy-meme (directory `retraining_rust`). [Before submission, deposit a release in a permanent archive, such as Zenodo, and cite its DOI here.] Raw GitHub data can be re-collected with the supplied scripts, and WildChat-1M is available from its publisher.

**Author contributions.** [Describe each author's contribution, for example conceptualization, data collection, analysis, labeling, and writing.]

**Use of AI tools.** An AI assistant (Claude, Anthropic) was used to write and run analysis code, to draft and edit the manuscript text, and as an annotator in the validation of the correction detector (Section 4.4); its labels were compared with those of a human author, and the differences are reported in Section 5.4. The authors reviewed the outputs and take responsibility for the content. [Check the journal's current policy on disclosing AI use and adapt this statement accordingly.]

## References

Aguirregabiria, V., and Mira, P. (2010). Dynamic discrete choice structural models: A survey. *Journal of Econometrics*, 156(1), 38–67.

Amershi, S., Begel, A., Bird, C., DeLine, R., Gall, H., Kamar, E., Nagappan, N., Nushi, B., and Zimmermann, T. (2019). Software engineering for machine learning: A case study. In *Proceedings of the 41st International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP)*, 291–300.

Chen, L., Zaharia, M., and Zou, J. (2024). How is ChatGPT's behavior changing over time? *Harvard Data Science Review*, 6(2).

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46.

DerSimonian, R., and Laird, N. (1986). Meta-analysis in clinical trials. *Controlled Clinical Trials*, 7(3), 177–188.

Duncan, A. J. (1956). The economic design of $\bar X$ charts used to maintain current control of a process. *Journal of the American Statistical Association*, 51(274), 228–242.

Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A. (2014). A survey on concept drift adaptation. *ACM Computing Surveys*, 46(4), Article 44.

Hotz, V. J., and Miller, R. A. (1993). Conditional choice probabilities and the estimation of dynamic models. *Review of Economic Studies*, 60(3), 497–529.

Jiang, W., Synovic, N., Hyatt, M., Schorlemmer, T. R., Sethi, R., Lu, Y.-H., Thiruvathukal, G. K., and Davis, J. C. (2023). An empirical study of pre-trained model reuse in the Hugging Face deep learning model registry. In *Proceedings of the 45th IEEE/ACM International Conference on Software Engineering (ICSE)*.

Khomh, F., Dhaliwal, T., Zou, Y., and Adams, B. (2012). Do faster releases improve software quality? An empirical case study of Mozilla Firefox. In *Proceedings of the 9th IEEE Working Conference on Mining Software Repositories (MSR)*, 179–188.

Landis, J. R., and Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174.

Lazaridou, A., Kuncoro, A., Gribovskaya, E., Agrawal, D., Liska, A., Terzi, T., et al. (2021). Mind the gap: Assessing temporal generalization in neural language models. *Advances in Neural Information Processing Systems*, 34.

Luu, K., Khashabi, D., Gururangan, S., Mandyam, K., and Smith, N. A. (2022). Time waits for no one! Analysis and challenges of temporal misalignment. In *Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)*.

Rust, J. (1987). Optimal replacement of GMC bus engines: An empirical model of Harold Zurcher. *Econometrica*, 55(5), 999–1033.

Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., et al. (2015). Hidden technical debt in machine learning systems. *Advances in Neural Information Processing Systems*, 28.

Zhao, W., Ren, X., Hessel, J., Cardie, C., Choi, Y., and Deng, Y. (2024). WildChat: 1M ChatGPT interaction logs in the wild. In *International Conference on Learning Representations (ICLR)*.
