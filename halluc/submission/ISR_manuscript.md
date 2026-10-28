# Where to Look First: Heterogeneity, Position, and the Value of Targeted Verification of Language-Model Output

## Abstract

Organizations that deploy generative AI cannot have a person verify every sentence it produces, yet the usual summary of reliability, a single hallucination rate, says nothing about where scarce verification effort should go. We treat hallucinations as events of a doubly stochastic (Cox) process over the units of a generated text and characterize their structure by an intensity function and by overdispersion. We show that the excess of an observed Fano factor over its independent benchmark equals the summed covariance of the latent error probabilities, which links a descriptive statistic to the part of the risk that a verifier can learn. Using three public collections of human hallucination annotations (FActScore, WikiBio-GPT3, RAGTruth) we find that clustering depends on the task: it is strong when a model writes biographies from parametric knowledge (Fano factor 0.46 against an independent benchmark of 0.28) and absent in source-grounded summarization once the generating model and source length are controlled (1.03 against 1.03). Risk rises toward the end of a text; a lead-sentence concentration that appears in judge-based analysis is an artifact of how errors are defined. We derive the cost-minimizing verification policy, show that the value of targeting equals the smaller of the total surplus and the total waste across units, and show that adaptive reallocation pays only where documents differ in latent difficulty. On human labels, knowing which model wrote a text is the most valuable allocation signal, whereas position alone adds little. Calibrating a human-in-the-loop extension with published verifier data, we find that an automated screen helps mainly by speeding review, not by improving accuracy. We discuss implications for provenance disclosure and task-specific verification policy.

**Keywords:** generative AI; hallucination; verification; resource allocation; point processes; human–AI collaboration; IT governance


## 1. Introduction

A firm that uses a large language model to draft biographies, summaries, or reports faces a verification problem before it faces a modeling problem. The text is cheap to produce and expensive to check. A reviewer with a fixed budget will examine some parts of the output and leave others unchecked, and the quality of that choice determines how many errors survive. The standard way of reporting reliability does not inform the choice. A hallucination rate of ten percent is compatible with errors scattered evenly over every document, in which case no part of the output deserves more attention than another, and it is equally compatible with errors concentrated in a few documents or in particular stretches of text, in which case a reviewer who knows where to look can do far better than one who samples at random.

This paper asks two questions. First, how are hallucinations distributed over the units of a generated text, and under which conditions do they cluster? Second, what follows for the allocation of verification effort? We answer the first empirically, using human annotations that were produced independently of any automated judge, and the second with a decision model that is simple enough to yield closed-form results and rich enough to connect to the data.

The paper is written for two audiences: researchers who study human–AI collaboration, information technology governance, and the management of machine-generated content, and managers who decide how the review of such content is staffed and prioritized. In the terminology of the journal's article types it is a paper that develops an analytical model and tests its implications out of sample on human annotations released by others.

We make four contributions. The first is a measurement framework. We model hallucinations as events of a doubly stochastic process and report an intensity function together with overdispersion, rather than one rate. A lemma shows that the excess of the observed Fano factor over the benchmark of independent errors equals the sum of pairwise covariances of the latent error probabilities. The excess therefore measures exactly the part of the risk that units share, which is the part a verifier can exploit and learn.

The second contribution is a set of empirical regularities that are explicitly conditional on the task. In biography generation from parametric knowledge, errors cluster strongly across documents. In summarization of a supplied source, they hardly cluster once the generating model and the length of the source are taken into account. In both settings the probability of error rises toward the end of a text. We also report a negative result that we regard as methodologically useful. Analyses that define an error as a claim contradicted by the reference show a strong concentration of errors in the lead sentence. The concentration disappears when errors are defined as unsupported claims, and it reverses in human annotations. It is an artifact of how verifiability varies across a text.

The third contribution is a decision model. We characterize the cost-minimizing policy as a threshold rule, show that the value of targeting over uniform verification equals the smaller of two totals, and show that adaptive reallocation is valuable only when documents differ in latent difficulty and the budget can be moved across them. The fourth is a calibration of a human-in-the-loop extension with published data on human verification accuracy and time. It shows that an automated screen is valuable mainly because it speeds review, and that its value disappears when it fails to improve the reviewer's accuracy.

These results bear directly on how organizations should design the systems and policies through which people review machine-generated content, and Section 8 draws out implications for provenance, task-specific verification policy, human–AI collaboration, and reporting. The remainder of the paper is organized as follows. Section 2 reviews related work. Section 3 presents the model. Section 4 describes the data and the measurement choices. Sections 5 and 6 report the empirical regularities and the performance of allocation policies on human labels. Section 7 introduces human verifiers into the model. Section 8 discusses implications, and Section 9 states the limitations of the evidence.


## 2. Background and Related Work

**Hallucination and factuality evaluation.** Surveys document the prevalence of hallucination across generation tasks (Ji et al. 2023). For long-form text, evaluation has moved from whole-response judgments to the verification of individual facts. FActScore decomposes a generation into atomic facts and reports the share supported by a knowledge source, and it released human annotations of biographies produced by several systems (Min et al. 2023). Long-form factuality benchmarks extend this approach with automated search-based raters (Wei et al. 2024). Sentence-level human labels for biographies written by GPT-3 were released with SelfCheckGPT (Manakul et al. 2023), and RAGTruth provides human-marked hallucination spans for responses from six models in retrieval-augmented tasks, among them summarization (Niu et al. 2024). We use these three annotation collections as our primary evidence.

**Position, context, and error propagation.** Recent work reports that unsupported content becomes more common later in long outputs, both in biographies and in long-document summarization (Tu et al. 2025; Yang et al. 2025) [AUTHORS: verify author lists and venues of these two entries]. Another line argues that a model may commit to an early error and then produce further errors it would not otherwise make, a phenomenon called snowballing (Zhang et al. 2024). Our contribution relative to this work is to treat the structure of errors as a statistical object, with an intensity function and a dispersion measure, and to ask what it implies for verification effort.

**Reliability models and resource allocation.** Software reliability growth models describe failures as a non-homogeneous Poisson process whose intensity declines as testing proceeds, and they were used early to formulate optimal release and testing-effort decisions (Goel and Okumoto 1979). Our setting differs in two respects. The intensity is not necessarily decreasing in the position within a text, and it is random across documents, which places the model in the class of doubly stochastic Poisson processes (Cox 1955). Self-exciting processes are a natural alternative for contagious events (Hawkes 1971); we find no support for self-excitation in our data, although the evidence is limited (Section 9).

**Information systems and organizational perspectives.** Research on human–AI collaboration documents that delegating work to AI and reviewing its output involves cognitive challenges and can raise or lower performance depending on the task (Fügener et al. 2021, 2022; Dell'Acqua et al. 2023). The question of how much to verify has an older counterpart in the economics of costly state verification and auditing (Townsend 1979; Gale and Hellwig 1985; Border and Sobel 1987). We bring the second tradition to bear on the first, with the difference that the unit being verified is generated by a stochastic process rather than reported by a strategic agent (Section 8.1). Closely related work audits the behavior of language models before deployment, linking a model's stated reasoning to its final decisions in economic-game and delegation scenarios (Leng and Yuan 2026). We address a complementary problem: given a model whose outputs contain factual errors, where should scarce human verification go once the model is in use? Audit selection has also been studied as an algorithm-design problem in information systems research: scoring models rank providers or claims by suspicion, and when audited parties respond, the objective is extended to include the deterrence that an audit produces (Bouayad et al. 2019). Our setting has the scoring but, absent retraining on audit outcomes, not the deterrence, because the verified content is produced by a model that does not respond to being checked.

**Human verification of AI output.** Studies of human–AI decision making show that people tend to rely on AI advice even when it is wrong, and that interface designs that force deliberation can reduce overreliance (Buçinca et al. 2021; Parasuraman and Manzey 2010). In a study of crowdworkers checking claims, language-model explanations made verification faster than retrieved passages while leaving accuracy similar, and they induced overreliance when the explanation was wrong (Si et al. 2024) [AUTHORS: verify]. Explanations can reduce overreliance when they are cheap to check (Vasconcelos et al. 2023). A recent economic analysis frames the effects of AI progress as a race between cheap automation and costly human verification (Catalini et al. 2026) [AUTHORS: working paper; verify status]. We contribute a model of where verification effort should be placed, connected to the empirical structure of errors and to published parameters of human verification.


## 3. A Cox-Process Model of Verification Allocation

### 3.1 Setup

A document *d* consists of units *t* = 1, …, *n~d~* (sentences in our application). Let *Y~dt~* ∈ {0, 1} indicate an error in unit *t*. Let Θ~d~ denote latent properties of the document, and let *x~d~* denote characteristics that a verifier observes at no cost, such as the identity of the generating model. We assume that, conditional on (*x~d~*, Θ~d~), the errors are independent with probabilities

*p~dt~* = σ(*f*(*t*) + β′*x~d~* + *Z~d~* + η~dt~),

where σ is the logistic function, *f* is a position profile, *Z~d~* ∼ N(0, τ²) is a document-level difficulty, and η~dt~ is a local component with mean zero. This is a Bernoulli analogue of a Cox process. We write *q~dt~* = E[*p~dt~* | *x~d~*] for the predictive error probability given what the verifier knows.

A verification plan *v~dt~* ∈ {0, 1} costs *c* per verified unit. Verification of an erroneous unit detects and repairs the error with probability δ. An undetected error costs *L*. The expected cost of a plan is

*C*(**v**) = Σ *c v~dt~* + Σ *L q~dt~* (1 − δ *v~dt~*).

### 3.2 Overdispersion and shared difficulty

For a window *W* of units let *N* = Σ~t∈W~ *Y~t~*. Let *p̄~t~* = E[*p~t~* | *x*].

**Lemma 1.** Var(*N*) = Σ~t∈W~ *p̄~t~*(1 − *p̄~t~*) + Σ~s≠t∈W~ Cov(*p~s~*, *p~t~*).

Hence the amount by which the observed Fano factor exceeds the benchmark that treats errors as independent with probabilities *p̄~t~* is determined entirely by the covariances of the latent probabilities. Variation that is idiosyncratic to a unit cancels. What remains is the variation shared across units, whether through a document-level or a local component. This is the part of the risk that a verifier can learn by looking at a few units, and the part that covariates can capture.

### 3.3 Optimal policies

**Proposition 1 (threshold policy).** Suppose costs are equal and *q~dt~* = *h*(*f*(*t*) + β′*x~d~*) with *h* increasing. A policy that minimizes expected cost under a budget of *B* verified units verifies exactly the units whose index *u~dt~* = *f*(*t*) + β′*x~d~* exceeds a threshold determined by *B*. If *f* is quasi-convex, the verified set in each document is the union of an initial block and a final block, and both blocks widen as the budget grows.

**Proposition 2 (value of targeting rises with heterogeneity).** With equal costs and a budget of *k* units out of *N*, the gain of targeted over uniform verification, *G~k~*(**q**) = δ[Σ~top\ *k*~ *q~i~* − (*k*/*N*) Σ *q~i~*], is nonnegative, equals zero when all *q~i~* are equal, and, for vectors with the same sum, is larger for the vector that majorizes the other.

**Proposition 3 (adaptivity operates across documents).** Suppose costs are equal, the local component is absent, and each document has a single shared *Z~d~*. For any posterior over *Z~d~*, the ranking of units within a document by posterior predictive error probability coincides with their ranking by *f*(*t*) + β′*x~d~*. Consequently an adaptive policy that re-ranks units after observing verification outcomes gains nothing over a static policy when each document has its own budget. Gains from adaptivity arise only when budget can be reallocated across documents, and they increase with the dispersion τ of document difficulty.

### 3.4 Stakes, cost, and the value of targeting

**Proposition 4.** A policy that minimizes expected cost verifies unit *t* if and only if δ *L q~t~* ≥ *c*. Let *a~t~* = δ *L q~t~* − *c*. Uniform random verification of a fraction φ has expected net benefit φ Σ *a~t~*, which is linear in φ, so its best choice is to verify all units or none, with benefit (Σ *a~t~*)⁺. The value of targeting over the better of these two is

*V* = Σ *a~t~*⁺ − (Σ *a~t~*)⁺ = min(Σ *a~t~*⁺, Σ *a~t~*⁻).

Targeting is valuable only when the population contains both units that are worth verifying and units that are not, and its value is the smaller of the total surplus of the first group and the total waste of the second. It vanishes if the ratio *L*/*c* is so small that no unit is worth verifying or so large that every unit is.

### 3.5 Screening before human review

Suppose an automated screen costs *c₁* per unit, flags an erroneous unit with probability δ₁, and flags a correct unit with probability *f*₁, with δ₁ > *f*₁. Flagged units are passed to a human who checks them at cost *c₂* and detects an error with probability δ₂. The expected net values of three actions for a unit with error probability *q* are

*N*(*q*) = 0,  *H*(*q*) = δ₂ *L q* − *c₂*,  *S*(*q*) = δ₁ δ₂ *L q* − *c₁* − *c₂* [*q* δ₁ + (1 − *q*) *f*₁],

for taking no action, direct human verification, and screening followed by review of flagged units.

**Proposition 5.** Assume δ₁ δ₂ *L* > *c₂*(δ₁ − *f*₁), so that screening is useful at all. The three values are then linear in *q* with slopes 0 < slope(*S*) < slope(*H*) = δ₂ *L*. The optimal action is therefore none for low *q*, screening for intermediate *q*, and direct human verification for high *q*, and the screening region is nonempty if and only if

*c₁* < *c₂* (δ₁ − *f*₁)(1 − *q~h~*),  *q~h~* = *c₂*/(δ₂ *L*).

Screening pays when its discriminating power, multiplied by the human cost it saves on correct units, exceeds its own price. Section 7 relaxes the assumption that human detection does not depend on the screen's output; in that case the ordering of regions in Proposition 5 can fail, while the envelope argument still holds. Proofs are in Online Appendix A.


## 4. Data and Measurement

### 4.1 Public human annotations

We use three collections of human annotations. None involves a model-based judge.

*FActScore annotations.* Human annotators labeled the atomic facts of biographies of 183 entities written by InstructGPT, ChatGPT, and PerplexityAI as supported, not supported, or irrelevant with respect to Wikipedia (Min et al. 2023). We treat a sentence as erroneous if any of its relevant facts is not supported, and we exclude sentences without a relevant fact.

*WikiBio-GPT3.* Biographies of 238 individuals generated by GPT-3, with sentence-level labels *accurate*, *minor inaccurate*, and *major inaccurate* (Manakul et al. 2023). The broad event is any inaccuracy and the strict event is a major inaccuracy.

*RAGTruth, summarization.* Summaries of news articles by six models (GPT-4, GPT-3.5-turbo, Llama-2 at 7B, 13B, and 70B, and Mistral-7B-Instruct) with human-marked hallucination spans (Niu et al. 2024). We segment each response into sentences, mark a sentence as erroneous if a span overlaps it, and use the 4,732 responses of acceptable quality with at least four sentences. The strict event restricts spans to conflict-type labels.

### 4.2 Units, events, and statistics

The unit is the sentence. For clustering we compute the Fano factor of counts of errors in non-overlapping windows of three (or five) consecutive sentences and compare it with its distribution under independent errors whose probabilities come from a logistic model in the log position, augmented with the generating model and the log length of the source where available. The distribution under the benchmark is obtained by parametric simulation, and we report a one-sided Monte Carlo *p* value. Document-level heterogeneity is summarized by the standard deviation τ of a random intercept, estimated by marginal likelihood. For allocation we use five-fold cross-fitting over documents: the risk model is fitted on training documents and policies are scored on held-out documents, so that the share of errors caught is estimated out of sample. Confidence intervals bootstrap documents.

### 4.3 A judge-based pipeline, and why it needs human validation

To study additional models we generated biographies for the 487 entities of the FActScore prompt set with five open models (Gemma-3 at 4B, 12B, and 27B, Mistral-Small-3.2, and Llama-4-Scout), and summaries of the corresponding Wikipedia articles with three of them. Each text was decomposed into numbered sentences and each claim was judged against the reference article as supported, contradicted, or not found, by two language-model judges (Claude Haiku 5.5 and Mistral Medium 3.5). A sentence was marked erroneous either if it contained a contradicted claim (the *contradiction* event) or if it contained any claim not supported (the *unsupported* event).

We validated the judges against the FActScore human labels (Online Appendix B). Treating a sentence as erroneous when the judge found any unsupported claim, agreement with the human label was moderate (Cohen's κ 0.63 and 0.66), the judges flagged more sentences than humans did, and sensitivity was high. The stricter contradiction event had a precision of about 0.87 but a sensitivity of only about 0.34, because the human label does not distinguish contradicted from unverifiable claims. We use the judge-based pipeline for two purposes only: to extend the policy evaluation to additional models, and to document the measurement artifact in Section 5.4. Every substantive claim in Sections 5 to 7 rests on human labels.


## 5. Empirical Regularities

### 5.1 Clustering depends on the task

Table 1 reports clustering and its determinants on the public human labels.

**Table 1.** Clustering and position on public human labels. Fano factors are for windows of three sentences. "Null" is the mean under independent errors with the same covariates.

| Collection | Docs | Sents. | Rate | Lead / later | Fano obs. / null | *p* | τ |
|---|---:|---:|---:|---|---|---:|---:|
| WikiBio-GPT3, any inaccuracy | 237 | 1,905 | 0.731 | 0.705 / 0.734 | 0.46 vs 0.28 | 0.003 | 1.97 |
| WikiBio-GPT3, major only | 237 | 1,905 | 0.399 | 0.160 / 0.433 | 1.22 vs 0.67 | 0.003 | 2.68 |
| RAGTruth summarization, all models, any span | 4,732 | 28,290 | 0.062 | 0.046 / 0.066 | 1.03 vs 1.03 | 0.349 | 0.06 |
| RAGTruth summarization, conflict spans only | 4,732 | 28,290 | 0.025 | 0.020 / 0.026 | 1.00 vs 1.01 | 0.635 | 0.13 |

For the FActScore annotations, which we analyze for documents of at least eight evaluable sentences and a window of five, the observed Fano factor exceeds its benchmark for ChatGPT (0.71 against 0.41, *p* = 0.005, 84 documents) and PerplexityAI (1.32 against 0.77, *p* = 0.005, 113 documents). For InstructGPT only 24 documents qualify and the test has little power (0.45 against 0.35, *p* = 0.149).

Clustering is therefore clear when models write biographies from parametric knowledge. Errors concentrate in some documents: the standard deviation of document difficulty on the logit scale is 2.0 (broad event) and 2.7 (strict event) in WikiBio, and 1.7 in the pooled FActScore annotations. In source-grounded summarization, the pooled data show no excess dispersion once the generating model and the source length are controlled. Among individual models, a small excess appears for GPT-3.5-turbo (1.21 against 0.99), GPT-4 (1.10 against 0.98), and Llama-2-70B (1.05 against 0.96) under the broad event, and none for the other three models. These models have very low error rates (a sentence-level rate between 0.009 and 0.048), and the excess disappears under the strict event. We read the evidence as showing that most of the variation in summarization errors is explained by which model wrote the text, with little residual document-level structure.

### 5.2 Risk rises toward the end of a text

In WikiBio the error rate rises over the five position quintiles from 0.68 to 0.77 under the broad event and from 0.23 to 0.49 under the strict event. In the FActScore annotations the lead sentence is less error-prone than later sentences for all three systems (0.59 against 0.80 for InstructGPT, 0.48 against 0.66 for ChatGPT, and 0.14 against 0.32 for PerplexityAI), and a fitted position profile is increasing. In RAGTruth the weaker models show the same pattern under the broad event: for Mistral-7B the rate over quintiles is 0.095, 0.131, 0.164, 0.177, and 0.181, and for Llama-2-7B it is 0.086, 0.090, 0.100, 0.137, and 0.127. Under the strict event the profiles are largely flat, and for GPT-4 the small lead excess (0.034 against 0.013) concerns a rate below two percent. Overall, late sentences are riskier, consistent with reports of declining factuality in the later parts of long outputs.

### 5.3 Source length

RAGTruth also lets us ask whether longer sources are associated with more errors. The sentence-level error rate does not increase with the length of the source: it is 0.066, 0.063, and 0.060 across tertiles under the broad event (0.029, 0.025, and 0.022 under the strict event). The probability that a response contains at least one error does increase (0.268, 0.305, and 0.331), and the coefficient on log source length in a logit model with model fixed effects is 0.25 (*z* = 3.3) under the broad event but only 0.09 (*z* = 1.0) under the strict event. We did not control for the number of sentences in a response, which is likely to grow with source length and so mechanically raises the chance of at least one error. The sources span roughly 1,300 to 7,300 characters (5th to 95th percentile), so this analysis does not speak to genuinely long contexts. We therefore claim no relation between context length and the density of errors.

### 5.4 A measurement artifact: the lead sentence

In our judge-based pipeline the contradiction event shows a striking concentration of errors in the lead sentence. For biographies written by Gemma-3-27B, 82 percent of lead sentences contain a contradicted claim, against 20 percent of later sentences. If the event is instead defined as any unsupported claim, the figures are 93 and 92 percent, which are indistinguishable (and uninformative, because the rate is nearly saturated). In the human annotations the lead sentence is less error-prone, not more. The explanation is verifiability. Lead sentences contain facts that the reference states directly, such as dates and places of birth, which can be contradicted. Later sentences contain general statements that the reference neither confirms nor refutes and which a contradiction-based event therefore never flags. A position effect measured with a contradiction event partly measures how verifiable each position is. We recommend that studies of position effects state their event definition explicitly and check it against human labels.


## 6. Allocation Policies on Human Labels

We evaluate policies out of sample on the human labels. A *static* policy ranks units by the predictive error probability from a logistic risk model with a random document intercept, whose features are those a verifier knows at no cost. An *adaptive* policy, available when a budget is shared across documents, updates the posterior of each document's difficulty after every verification and re-ranks. The outcome is the share of all errors caught.

**Table 2.** Gain over uniform allocation (share of all errors caught; 95% bootstrap CI), human labels, five-fold cross-fitting.

| Setting | Budget | Static − uniform | Adaptive − static |
|---|---|---|---|
| WikiBio, position only, per-document budget, any inaccuracy | 30% | +0.012 [+0.002, +0.023] | n/a |
| WikiBio, position only, per-document budget, major only | 30% | +0.039 [+0.020, +0.060] | n/a |
| RAGTruth, position only, per-document budget | 30% | +0.042 [+0.020, +0.063] | n/a |
| RAGTruth, shared budget, position + generating model + log source length | 10% | +0.177 [+0.154, +0.201] | −0.003 |
| RAGTruth, shared budget, position + generating model + log source length | 30% | +0.333 [+0.306, +0.360] | −0.002 |
| WikiBio, shared budget, major only | 30% | +0.033 [+0.011, +0.057] | +0.183 [+0.090, +0.268] |
| WikiBio, shared budget, major only | 50% | n/a | +0.180 [+0.114, +0.242] |
| WikiBio, shared budget, any inaccuracy | 50% | n/a | +0.078 [+0.021, +0.137] |

Three conclusions follow. First, position alone provides a modest gain, and its direction is to verify later sentences first: verifying only the lead sentence catches fewer errors than uniform verification in the FActScore annotations (0.084 against 0.127 at a ten percent budget). Second, a document-level signal carries by far the largest value. Knowing which model wrote a summary and verifying the output of weaker models first catches 17.7 percentage points more errors than uniform verification at a ten percent budget and 33.3 at a thirty percent budget. This signal is, however, unsurprising, since it is widely known that models differ in reliability. It matters in practice because it is available without cost, and it suggests that provenance information has direct value for verification. Third, adaptive reallocation is valuable exactly where the model predicts. In WikiBio, where documents differ strongly in latent difficulty (τ between 2.0 and 2.7), learning a document's difficulty from a few verifications raises the share of errors caught by up to 18 percentage points. In RAGTruth, where there is no residual document-level structure, it gains nothing. This pattern is what Proposition 3 predicts.


## 7. Human Verifiers and the Economics of Screening

### 7.1 The value of targeting under realistic detection

The results in Section 6 assume that a human check catches an error with certainty. Published data suggest otherwise. In a study of 80 crowdworkers verifying difficult claims, accuracy without assistance was 0.59, and it was 0.73 with retrieved passages and 0.74 with a language-model explanation (Si et al. 2024). [AUTHORS: the figures we cite from this study were obtained through a machine-assisted extraction of the paper's full text and must be checked against the published tables before submission.] We therefore recompute Proposition 4 with δ equal to 0.75 and 0.60, treating accuracy as an approximation of the probability of catching an error. For RAGTruth summaries with the generating model and source length as signals, targeting saves 25.4 percent of cost relative to the better of verifying everything or nothing at *L*/*c* = 20 when δ = 0.75, and 13.4 percent when δ = 0.60 (32.4 percent at δ = 1). At δ = 1, with position as the only signal, the saving is at most 3.4 percent. For WikiBio with the broad event, in which the error rate is 73 percent, targeting is worth essentially nothing at any ratio, because nearly every sentence is worth verifying.

### 7.2 Screening and reliance on the machine

We next measure the quality of an automated screen directly. We treat the judges' flags in the FActScore annotations as the output of a screen and compare them with human labels. The screen's sensitivity δ₁ is 0.94 and its false-flag rate *f*₁ is 0.31 for Claude Haiku 5.5, and 0.88 and 0.23 for Mistral Medium 3.5. Proposition 5 then implies that screening is worthwhile only if its cost is below roughly 41 to 57 percent of a human check, depending on the loss ratio.

Proposition 5 assumes that the reviewer's accuracy does not depend on what the screen says. The behavioral evidence points the other way. Reviewers shown a model explanation verified claims in about 1.0 minute rather than 2.5 minutes, but they were far more accurate when the explanation was right (0.87) than when it was wrong (0.35) (Si et al. 2024). We extend the model accordingly: a flagged unit costs *c~A~* = 0.40 *c₂* to review, an error in a flagged unit is caught with probability *d~A~*, and a correct unit that has been flagged wrongly is accepted as erroneous with probability 0.65, which costs a share λ of *L*. Because the screened path can now be both faster and more accurate than a direct check, the ordering of regions in Proposition 5 can break: screening can dominate direct verification even for units with a high error probability. The envelope argument continues to hold; only the order of the regions depends on the parameters.

Applied to the real flags and human labels, the screened policy reduces expected cost by 28 to 44 percent relative to the best policy without a screen at the baseline setting with *c~A~* = 0.40 and *d~A~* = 0.87 (Table 3, first row), and by 15 to 57 percent across the grid of screen costs and values of λ that we examined. This result is not robust. Table 3 varies the two parameters that come from the published study.

**Table 3.** Cost saving of "screen all units, human reviews flagged units" over the best policy without a screen (verify nothing, verify everything, or verify by risk), by loss ratio *L*/*c₂*. Screen cost 0.10 *c₂*, λ = 0.25, Claude Haiku 5.5 flags on FActScore human labels.

| Review cost *c~A~* / accuracy *d~A~* | 3 | 5 | 8 | 12 | 20 |
|---|---:|---:|---:|---:|---:|
| 0.40 / 0.87 | 43.7% | 42.2% | 37.3% | 32.8% | 27.5% |
| 0.40 / 0.73 | 27.4% | 21.4% | 11.1% | 1.9% | −8.6% |
| 0.40 / 0.60 | 12.3% | 2.1% | −13.3% | −26.7% | −42.2% |
| 0.70 / 0.73 | 12.4% | 9.9% | 2.0% | −5.1% | −13.6% |
| 1.00 / 0.87 | 13.7% | 19.2% | 19.2% | 18.6% | 17.5% |
| 1.00 / 0.73 | −2.6% | −1.6% | −7.0% | −12.2% | −18.6% |

The saving depends on the assumption that review of a flagged unit is more accurate than a direct check. If the screen merely speeds review without improving accuracy (*d~A~* = 0.73), the saving is positive only when review is cheap and the loss ratio is moderate, and if the screen lowers accuracy (*d~A~* = 0.60) it is negative. In the study we draw on, overall accuracy with an explanation (0.74) was the same as with retrieved passages (0.73), because the gain when the machine was right offset the loss when it was wrong. The value of 0.87 is conditional on a correct machine and is an upper bound. What the evidence supports is the time saving, roughly 60 percent. We conclude that an automated screen is justified chiefly by the speed it gives the reviewer and only when it does not impair accuracy.


## 8. Implications for Information Systems Research and Practice

### 8.1 Verification as a managed resource

Generative AI changes where the cost of producing information lies. The marginal cost of a draft approaches zero, while the cost of establishing that the draft is correct remains with people. The decision studied here, how much of an output to check and which parts, is therefore a management problem that recurs in every deployment, and the budget for checking is a control variable much like an audit budget. The structure of our problem resembles classical theories of costly state verification and auditing (Townsend 1979; Gale and Hellwig 1985; Border and Sobel 1987), in which a principal can observe the true state only by paying to verify it. There is one difference that matters for the form of the optimal policy. In those theories the verified party reports strategically, so optimal verification is typically stochastic and exists to deter misreporting. A language model does not respond strategically to being checked. Its errors arise from a random process whose intensity the organization can estimate, and the optimal policy is a deterministic threshold rule (Proposition 4) rather than a randomized audit. Audit-selection algorithms in information systems research likewise rely on scores that rank items by estimated risk and, when audited parties respond, add deterrence to the objective (Bouayad et al. 2019); our problem retains the scoring and loses the deterrence. This is both a simplification and a boundary: if users could adapt prompts or workflows in response to known verification practices, the strategic elements of the audit literature would re-enter.

### 8.2 Provenance as information-system design

In our data the single most valuable signal for allocating effort was the identity of the model that wrote the text. With a ten percent verification budget, a reviewer who prioritized RAGTruth summaries by generating model would have caught about 28 percent of the annotated errors, against 10 percent for a reviewer who sampled at random. At a thirty percent budget the figures are 63 and 30 percent. The signal costs nothing when the system that produced a text records it. This points to a modest but concrete design requirement. Workflow systems that route generated content to reviewers should attach to each output the identity and version of the model, the task type, and whether the generation was grounded in a supplied source, and they should rank review queues by empirically estimated risk. These requirements are close in spirit to documentation practices that report intended uses and measured performance of models (Mitchell et al. 2019), but they are operational: the documentation is used at run time to decide which outputs a person sees first.

The value of this signal rests on differences in reliability between models, and it falls as those differences shrink. A firm that standardizes on one model forgoes the signal. It then relies on the within-model structure, namely position and, for tasks resting on parametric knowledge, document-level risk.

Provenance metadata kept to route review should not be confused with labels shown to audiences, because disclosure can change the behavior of those who produce content. In creative work with a text-to-image tool, creators who anticipated that their use of generative AI would be disclosed to an audience largely withdrew from the process and left image generation to the tool; the authors suggest that more nuanced, process-level provenance records, in the manner of content-provenance standards, may mitigate this, and they leave open whether the effect extends to writing and to more technical tasks (Jussupow et al. 2026). Whether recording which model produced a text changes how its authors use the tool is, in our setting, an open question that an experiment would have to answer.

### 8.3 Task–technology fit for verification policy

The central empirical finding is that the structure of errors depends on the task, and hence the appropriate verification policy does too. This is a form of task–technology fit (Goodhue and Thompson 1995) applied to the verification process, and it echoes field evidence that the usefulness of AI varies sharply across tasks that appear similar, a "jagged" frontier (Dell'Acqua et al. 2023). Table 4 summarizes the policy implications of our evidence.

**Table 4.** Task type, observed error structure, and implied verification policy.

| Task | Observed structure (human labels) | Implied policy |
|---|---|---|
| Writing from parametric knowledge (biographies) | Strong document-level clustering; risk rises toward the end of the text | Verify later sentences first; reallocate effort across documents as verified outcomes arrive, because a document's difficulty is learned from a few checks |
| Summarizing a supplied source | Little residual clustering once the model is known; risk rises toward the end only for weaker models | Allocate by generating model and position; adaptive reallocation is not repaid |
| Settings with high base error rates | Almost every unit is worth checking | Targeting adds little; the decision is whether to check at all (Proposition 4) |

The last row follows from Proposition 4 and from WikiBio, where 73 percent of sentences contain an inaccuracy under the broad definition. When errors are that common, the practical question is not where to look but whether the output should be used without a rewrite.

### 8.4 Human–AI collaboration in verification

Automating part of verification with another model is an obvious response to the cost problem, and it connects to research on collaboration between people and AI systems, which finds both gains and cognitive pitfalls (Fügener et al. 2021, 2022). Our calibration contributes a specific result. An automated screen is valuable chiefly because it speeds the reviewer's work, a saving of roughly sixty percent of review time in the study we draw on, and it ceases to be valuable if it reduces the reviewer's accuracy (Section 7.2 and Table 3). Because people tend to follow machine advice whether or not it is right (Parasuraman and Manzey 2010), the design of the interface through which flags are presented is part of the verification system. Designs that require an independent judgment before the flag is revealed can limit overreliance, although they may cost speed and are rated less favorably by users (Buçinca et al. 2021). Our model suggests where such designs matter most: for units of high predicted risk, where the cost of an accepted false flag or a missed error is largest and where direct human verification may dominate screening. Experimental work on delegation to an image classifier found that a probability-of-correctness signal shown before a decision and feedback on outcomes shown afterwards helped users judge when to rely on the machine only in combination, each alone having no effect or a negative effect on combined performance (Taudien et al. 2026). The authors caution that such signals help only if they reflect actual performance and vary meaningfully across tasks. The analogue in our setting is the predicted risk of a unit, whose usefulness depends on its calibration and on its dispersion (Proposition 2), with the results of earlier checks playing the role of outcome feedback.

### 8.5 Governance and reporting

A single hallucination rate is a poor reporting standard for assurance and for service agreements. At minimum, a report on the reliability of a generative system should give the error rate by task and by generating model, the profile of the rate over the position within the output, and a measure of the dispersion of errors across documents, such as the excess Fano factor and the estimated document-level standard deviation. These quantities are inexpensive to compute from a labeled sample. They tell a manager whether to expect errors to be spread out or concentrated, whether verification should be adaptive, and where the first checkpoints belong. We did not study how large a labeled sample is needed to estimate them reliably, and we regard this as an important practical question.

### 8.6 Measurement practice

The lead-sentence artifact of Section 5.4 illustrates a general hazard for research that relies on automated judges. A judge-based pipeline can produce a structured pattern, here a position effect, that reflects how the event is defined rather than how the model behaves. Studies that report position or clustering effects based on automated judgments should state the event definition explicitly and validate the pattern against independent human labels. The same applies to organizational monitoring dashboards that rely on automated checkers.

### 8.7 Predictions and a research agenda

The model implies several predictions that we have not tested with human subjects and that we state here as hypotheses for future work in the laboratory and in the field.

*Prediction 1.* Under a fixed verification budget, providing reviewers with the identity of the generating model, and a ranking of outputs by estimated risk, increases the share of errors that they catch, and the increase is larger the greater the differences in reliability between the models in use.

*Prediction 2.* The net effect of an automated flag on the value of verification is mediated by the reviewer's accuracy conditional on whether the flag is right. A flag that speeds review without changing accuracy yields positive value only when the loss from an undetected error is moderate relative to the cost of review.

*Prediction 3.* Adaptive reallocation of effort across documents increases the share of errors caught in tasks with strong document-level clustering and has no effect where clustering is absent.

*Prediction 4.* Verification effort is allocated better by reviewers who see the position within a document than by those who do not, and the effect is larger for tasks in which risk rises toward the end of the text.

*Prediction 5.* Showing reviewers the predicted risk of each unit together with the outcomes of their earlier checks improves their allocation of effort more than showing either alone. This extends to verification the finding that certainty and outcome information help users decide when to rely on a machine only in combination (Taudien et al. 2026).

These predictions can be tested in experiments in which people verify generated text under controlled conditions. Such experiments would also supply the quantities that we could only borrow from the literature, namely the probability that a person detects an error, the time it takes, and the loss associated with a missed error in a realistic organizational setting.


## 9. Limitations

The human annotations evaluate output from models of different vintages: GPT-3 for WikiBio, InstructGPT, ChatGPT, and PerplexityAI for FActScore, and six models from 2023 for RAGTruth. Results for current models may differ. The RAGTruth responses are short (a median of about five sentences) and error rates for the strongest models are one or two percent, which limits the power to detect clustering. The sources in RAGTruth are short, so we cannot say anything about genuinely long contexts, and our test for an effect of source length did not control for response length.

We did not test the hypothesis that errors beget errors with human labels. A prefix-intervention experiment based on judge labels, described in Online Appendix B, finds no increase in the error rate after an erroneous prefix, but it asked the generator to continue a given text rather than its own output, and the labels were produced by a language-model judge. We therefore report the absence of snowballing as a secondary observation.

The parameters of human verification are borrowed from one published study with a different task: true-or-false judgment of short claims, not error detection in model-generated sentences. We used accuracy as a stand-in for the probability of detecting an error. Moreover, no source we found provides the loss from an undetected error, so the ratio of loss to verification cost is varied over a grid rather than estimated. The screening analysis uses judges that had access to the reference text; without a reference, their discrimination would be lower. Finally, the policy evaluation is offline: no verifier took part in a field or laboratory experiment, and the model's predictions about human behavior remain to be tested.


## 10. Conclusion

A single hallucination rate hides the information that matters for verification: where errors are, and whether a verifier can learn where they will be. We showed that overdispersion measures the shared part of risk, that errors cluster by document when models write from parametric knowledge but hardly cluster in source-grounded summarization, and that risk rises toward the end of a text. Targeted verification beats uniform verification, but most of its value comes from knowing which model produced the text rather than from position, and adaptive reallocation pays only where documents differ in latent difficulty. When human reliance on machine advice is taken into account, an automated screen is worth its cost mainly because it makes review faster. These conclusions are conditional on the task and on the parameters of human verification, which we calibrated from the literature rather than measured. A laboratory or field study of verifiers working with and without machine flags is the natural next step.


## References

[AUTHORS: every entry must be verified against the original source. Format follows the pattern of reference lists in published ISR articles (surname and initials, year in parentheses, abbreviated journal names); the official INFORMS reference-style guide has not been read, so abbreviations may need adjustment.]

Border KC, Sobel J (1987) Samurai accountant: A theory of auditing and plunder. *Rev. Econom. Stud.* 54(4):525–540.

Bouayad L, Padmanabhan B, Chari K (2019) Audit policies under the sentinel effect: Deterrence-driven algorithms. *Inform. Systems Res.* 30(2):466–485.

Buçinca Z, Malaya MB, Gajos KZ (2021) To trust or to think: Cognitive forcing functions can reduce overreliance on AI in AI-assisted decision-making. *Proc. ACM Human-Comput. Interaction* 5(CSCW1):Article 188.

Catalini C, Hui X, Wu J (2026) Some simple economics of AGI. Preprint, arXiv:2602.20946. [AUTHORS: verify authors and status.]

Cox DR (1955) Some statistical methods connected with series of events. *J. Roy. Statist. Soc. Ser. B* 17(2):129–164.

Dell'Acqua F, McFowland E III, Mollick ER, Lifshitz-Assaf H, Kellogg K, Rajendran S, Krayer L, Candelon F, Lakhani KR (2023) Navigating the jagged technological frontier: Field experimental evidence of the effects of AI on knowledge worker productivity and quality. Working paper 24-013, Harvard Business School, Boston.

Fügener A, Grahl J, Gupta A, Ketter W (2021) Will humans-in-the-loop become borgs? Merits and pitfalls of working with AI. *MIS Quart.* 45(3):1527–1556.

Fügener A, Grahl J, Gupta A, Ketter W (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Inform. Systems Res.* 33(2):678–696.

Gale D, Hellwig M (1985) Incentive-compatible debt contracts: The one-period problem. *Rev. Econom. Stud.* 52(4):647–663.

Goel AL, Okumoto K (1979) Time-dependent error-detection rate model for software reliability and other performance measures. *IEEE Trans. Reliability* R-28(3):206–211.

Goodhue DL, Thompson RL (1995) Task-technology fit and individual performance. *MIS Quart.* 19(2):213–236.

Hawkes AG (1971) Spectra of some self-exciting and mutually exciting point processes. *Biometrika* 58(1):83–90.

Ji Z, Lee N, Frieske R, Yu T, Su D, Xu Y, Ishii E, Bang YJ, Madotto A, Fung P (2023) Survey of hallucination in natural language generation. *ACM Comput. Surveys* 55(12):Article 248.

Jussupow E, Bauer K, Heigl RM, Vogt B, Hinz O (2026) The indirect disclosure effect: How disclosing generative AI use impacts human creative collaboration with AI. *Inform. Systems Res.* Published online ahead of print August 27, https://doi.org/10.1287/isre.2024.0951.

Leng Y, Yuan Y (2026) SUVA: A probabilistic framework for auditing LLMs with an application to social preferences. *Inform. Systems Res.* 37(3):1805–1830.

Manakul P, Liusie A, Gales MJF (2023) SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models. *Proc. 2023 Conf. Empirical Methods Natural Language Processing* (Association for Computational Linguistics).

Marshall AW, Olkin I, Arnold BC (2011) *Inequalities: Theory of Majorization and Its Applications*, 2nd ed. (Springer, New York).

Min S, Krishna K, Lyu X, Lewis M, Yih W, Koh PW, Iyyer M, Zettlemoyer L, Hajishirzi H (2023) FActScore: Fine-grained atomic evaluation of factual precision in long form text generation. *Proc. 2023 Conf. Empirical Methods Natural Language Processing* (Association for Computational Linguistics).

Mitchell M, Wu S, Zaldivar A, Barnes P, Vasserman L, Hutchinson B, Spitzer E, Raji ID, Gebru T (2019) Model cards for model reporting. *Proc. Conf. Fairness, Accountability, Transparency* (ACM, New York), 220–229.

Niu C, Wu Y, Zhu J, Xu S, Shum K, Zhong R, Song J, Zhang T (2024) RAGTruth: A hallucination corpus for developing trustworthy retrieval-augmented language models. *Proc. 62nd Annual Meeting Assoc. Comput. Linguistics* (Association for Computational Linguistics).

Parasuraman R, Manzey DH (2010) Complacency and bias in human use of automation: An attentional integration. *Human Factors* 52(3):381–410.

Si C, et al. (2024) Large language models help humans verify truthfulness—except when they are convincingly wrong. *Proc. 2024 Conf. North Amer. Chapter Assoc. Comput. Linguistics* (Association for Computational Linguistics). arXiv:2310.12558. [AUTHORS: complete author list and venue.]

Taudien A, Fügener A, Gupta A, Ketter W (2026) Enhancing AI use: How complementary system information drives delegation frequency and effectiveness. *Inform. Systems Res.* Published online ahead of print September 4, https://doi.org/10.1287/isre.2024.1330. [AUTHORS: update volume and pages if the article has appeared in an issue.]

Townsend RM (1979) Optimal contracts and competitive markets with costly state verification. *J. Econom. Theory* 21(2):265–293.

Tu, et al. (2025) Investigating factuality in long-form text generation: The roles of self-known and self-unknown. *Proc. 2025 Conf. Empirical Methods Natural Language Processing*. arXiv:2411.15993. [AUTHORS: complete author list.]

Vasconcelos H, Jörke M, Grunde-McLaughlin M, Gerstenberg T, Bernstein MS, Krishna R (2023) Explanations can reduce overreliance on AI systems during decision-making. *Proc. ACM Human-Comput. Interaction* 7(CSCW1):Article 129.

Wei J, et al. (2024) Long-form factuality in large language models. *Adv. Neural Inform. Processing Systems*, vol. 37. arXiv:2403.18802. [AUTHORS: complete author list.]

Yang, et al. (2025) Hallucinate at the last in long response generation: A case study on long document summarization. Preprint, arXiv:2505.15291. [AUTHORS: complete author list and venue.]

Zhang M, Press O, Merrill W, Liu A, Smith NA (2024) How language model hallucinations can snowball. *Proc. 41st Internat. Conf. Machine Learn.* (PMLR).
