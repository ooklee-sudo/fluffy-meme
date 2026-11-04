---
title: "Filter or Prior? What LLM Synthetic Agents Are Worth in Experimentation Pipelines"
author:
  - "[Author name], [Affiliation]"
---

**Abstract.** Platforms increasingly consider large language model (LLM) "digital twins" to pre-screen A/B tests before spending human traffic. We ask when such synthetic evidence can be trusted and what it is worth. Pre-registered studies across five model families show that twins recover the direction of cue-based effects such as framing and anchoring, but they misstate magnitudes. They also reverse the sign of default effects depending on whether the paradigm is familiar from training text. We translate these validity results into a decision model in which a single quantity, the twin–outcome correlation ρ, determines when pre-screening pays. On 500 public Upworthy headline tests, four current models reach ρ = 0.13–0.23. At these values, using twins to discard candidates doubles the expected loss in click-through rate at realistic budgets. Using them as a calibrated prior is safe but saves only 1–3% of traffic. We close with rules practitioners can apply before putting synthetic agents into an experimentation pipeline.

**Keywords:** large language models, synthetic agents, digital twins, A/B testing, experimentation platforms

---

Digital platforms run experiments continuously. They test defaults in sign-up flows, price displays, recommendation layouts, and headlines. Each experiment costs traffic and time, and many candidate designs never reach a test. LLMs offer a tempting shortcut. A "digital twin" conditions a model on a person's profile and asks how that person would respond [1]–[3]. If twins behaved like users, a platform could screen thousands of designs before spending human traffic.

Most evaluations ask whether twins reproduce known behavioral effects *on average* [4]–[6]. An engineer building a pipeline needs answers to different questions:

- For *this* kind of effect and *this* model version, is the twin informative about direction, about magnitude, or about neither?
- If the twin is informative, is it informative enough to change what gets tested?

This article answers both. We first summarize a set of pre-registered studies that map where twins are valid. We then turn that map into a decision model and test it on real A/B outcomes. The answer is sobering but actionable. Twins carry a real but weak signal, and how a pipeline uses that signal matters more than whether the signal exists.

## Where synthetic agents are valid

An LLM's answer to a decision scenario draws on three sources: regularities about how people respond in text, normative reasoning, and the persona it is given. Human biases also arise from processes a text-only agent does not bear: defaults, for example, work partly because acting costs effort and attention [7]. Training corpora also contain many descriptions of canonical experiments, so a model may reproduce an effect by recall rather than by generalizing the mechanism [8]. We therefore treat a twin as a *measurement instrument* and ask under which conditions its readings can be trusted. We propose four conditions. The treatment must act through the *text* of the stimulus, such as words, numbers, and option structure (V1). The effect must not depend on effort or transaction costs, which are real for humans and free for a model (V2). The paradigm must not be memorized from training data (V3). The agent's reasoning regime must match the human one (V4).

We derived seven propositions from these conditions and tested them on new data under two pre-registrations (AsPredicted #320110 and #320124). Human benchmarks come from Twin-2K-500, a public panel of 2,058 U.S. respondents [3], and its accompanying mega-study [6]. The tests ran on five model families, three persona formats, a reasoning-effort by temperature grid, and 13 model versions (see the sidebar). Table 1 condenses the results into a validity map.

> **Sidebar: Study design at a glance**
>
> - **Exploratory (not registered):** twin simulations of 772 panelists; a reasoning-by-temperature pilot. These generated the propositions.
> - **Confirmatory twin study:** 600 new respondents, 9 items (framing, anchoring, attraction, fairness, and a canonical and a novel default), 5 model families, 3 persona formats; 9,000 calls.
> - **Confirmatory reasoning grid:** 4 models × 3 reasoning-effort levels × 3 temperatures, with a bias battery and factual batteries; 10,800 calls.
> - **Stability study (exploratory):** 13 model versions × 2 prompt templates; 5,200 calls.
> - **Field evaluation:** 500 Upworthy headline tests × 4 current models × 3 draws; 6,000 calls (this article).
>
> No new human data were collected. All runs together cost about 310 USD in API fees. Prompts, outputs, code, and the deviation log are public.

**Table 1. Validity map across 26 configurations (13 model versions × 2 prompt templates).**

| Effect type | Direction valid | Magnitude valid | Rule |
|---|---|---|---|
| Anchoring | 100% | 12–15% | Rank alternatives; size with a human pilot |
| Loss framing | 92% | 8% | Rank alternatives; watch for extreme outliers |
| Attraction (decoy) | 85% | 12% | Validate per model |
| Fairness | 77% | 27% | Validate per model |
| Defaults (canonical and novel) | 15% | 4–15% | Do not use |
| Headlines (field) | +9 pts over chance | slope 0.26 | Weak prior only |

Four findings drive the map.

**Familiarity, not mechanism, explains much of the apparent fidelity.** On the canonical organ-donation default, twins overstated the human effect in four of five models (by +8.7 points pooled). On a novel green-energy default to which humans respond strongly, twins understated the effect in all five models (by −26.3 points). Adding a one-line note that names the phenomenon under study raised canonical effects in all five models. The sign of a default effect thus depends on whether the paradigm appears in training text. This violates V3 and makes defaults unusable.

**Cue-based effects are direction-valid but not magnitude-valid.** We predicted that twins would overshoot framing and anchoring. They did not do so reliably. Framing exceeded the human effect in only two of five models, and anchoring fell below it on average. Direction, however, was right in most configurations.

**More reasoning is not debiasing.** Raising reasoning effort cut factual errors from about 7% to under 1%. It also *raised* the bias index (coefficient +0.27) and the framing effect. Factual error and bias did not move together; their within-model correlation was −0.19. Capability gains therefore do not translate into better models of users (V4).

**Errors belong to model versions.** Prompt wording barely mattered: validity levels agreed across templates for 86% of model–effect pairs. In contrast, 68% of the variance in twin–human discrepancies was a model-by-effect interaction. Agreement between consecutive versions of the same family ranged from 43% to 100%. A validation result therefore expires when the model changes.

The map tells a team *where* twins carry information. It does not tell them whether that information is worth acting on. The next two sections address that question.

## From validity to value: a decision model

Consider a test, in the sense of standard online controlled experiments [9], with K candidate treatments, true effects θ₁ … θ_K, and a budget of N impressions. A twin returns a score s_k for each candidate. Let ρ be the correlation between twin scores and true effects within a test. The validity map gives ρ a meaning: direction-valid effects have ρ > 0, and sign-reversing effects such as defaults can have ρ < 0. Under a Gaussian approximation, the probability that the twin orders a random pair of candidates correctly is ½ + arcsin(ρ)/π. A reported agreement rate therefore translates directly into ρ.

A pipeline can use twin scores in three ways:

- **Filter:** test only the m highest-scoring candidates, giving each N/m impressions.
- **Prior:** test all K candidates, but combine the data with a prior centered on a calibrated function of s_k.
- **Replace:** ship the top-scoring candidate without a test.

Filtering trades two forces. Fewer arms mean more traffic per arm and less sampling error. But the best arm may be discarded before any human sees it, and no amount of later traffic can recover it. When ρ = 0, the discard probability is 1 − m/K, and it is higher when ρ < 0. Three results follow:

1. If ρ ≤ 0, filtering is no better than random filtering, and random filtering is worse than testing all candidates.
2. If ρ > 0, there is a break-even budget N\*. Filtering lowers expected loss only when N < N\*, and N\* grows with ρ and with the spread of true effects.
3. A prior calibrated on held-out tests does not increase expected loss in expectation. Its benefit shrinks as N grows and the data dominate.

Figure 1b shows N\* in a model calibrated to Upworthy (base click-through rate 1.5%, logit standard deviation of true headline effects 0.30, K = 5, m = 2). For ρ ≤ 0.1, filtering never pays. At ρ = 0.3, it pays only below about 1,200 impressions per test. Even at ρ = 0.7, N\* is under 10,000. A typical Upworthy test used about 20,000 impressions.

![Figure 1. (a) Expected click-through-rate (CTR) loss, relative to the best headline, for five ways of using twins, averaged over 500 Upworthy tests (ensemble of four models). (b) Break-even budget N\* below which filtering beats testing all candidates, as a function of the twin–outcome correlation ρ. The shaded band marks the ρ values observed for the four models.](figure1.png)

## Field evaluation on 500 Upworthy tests

The Upworthy Research Archive contains 32,487 headline experiments run on a news site in 2013–2015, with impressions and clicks for every variant [10]. We drew 500 tests at random from the confirmatory release. Each had three to eight distinct headlines with at least 1,000 impressions each. To separate true differences from sampling noise, we estimated each headline's click-through rate with empirical-Bayes shrinkage: the standard deviation of true headline effects is 0.30 on the logit scale, and the average sampling standard deviation is 0.20. Four current low-cost models scored all headlines of each test three times, in shuffled order. They used the same no-persona prompt that performed best in our confirmatory field study. For budgets from 2,000 to 64,000 impressions, we then simulated 400 A/B tests per test and policy. A random-filter policy served as a placebo for the gain from simply testing fewer arms. The prior's calibration was cross-fitted across two halves of the tests.

**Table 2. What synthetic pre-screening is worth (500 tests; CTR loss at 16,000 impressions).**

| Model | Pairwise agreement | Implied ρ | Best headline discarded by filter | Loss: test all | Loss: twin filter | Loss: twin prior | Traffic saved by prior |
|---|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | 0.542 | 0.13 | 41% | 4.06% | 8.81% | 4.02% | 1% |
| DeepSeek V4.1 Flash | 0.572 | 0.23 | 38% | 4.04% | 8.08% | 3.95% | 3% |
| Gemini 3.7 Flash | 0.559 | 0.18 | 41% | 4.07% | 8.81% | 3.99% | 2% |
| GPT-6 luna | 0.555 | 0.17 | 42% | 4.05% | 9.05% | 4.02% | 1% |
| Ensemble | 0.566 | 0.21 | 40% | 4.02% | 8.68% | 3.97% | 2% |

*A random filter discards the best headline in 50% of tests and has a loss of 11.4% (ensemble). Relying on the twin alone yields a loss of 16.7%.*

The results line up with the model (Table 2, Figure 1a).

**The signal is real.** Every model discards the best headline less often than chance (38–42% vs. 50%), and every twin filter beats the random filter at every budget.

**The signal is weak.** Implied ρ ranges from 0.13 to 0.23. Averaging the four models raises it only slightly, to 0.21, which is consistent with errors that are shared across models.

**Filtering is the wrong way to use it.** Even at 2,000 impressions, the smallest budget simulated, testing all headlines beats the twin filter for every model. At 16,000 impressions, filtering *doubles* the expected loss (8.7% vs. 4.0%). Because the winner is often gone before the test starts, the filter's loss levels off near 7.7%. The loss from testing all headlines keeps falling, to 1.4% at 64,000 impressions.

**The prior is safe but small.** Combining twin scores with the data never hurts, but it saves only 1–3% of traffic for the same expected loss.

The archive is public and predates all four models, so some memorization of winners cannot be excluded. Memorization would inflate ρ. Our conclusion that the signal is too weak to filter is therefore, if anything, optimistic about the twins.

## Rules for practitioners

The validity map and the decision model together yield five rules:

1. **Estimate ρ for the exact model version and effect type before use.** A battery of a few hundred past A/B tests with known outcomes is enough. Re-estimate whenever the model version changes, because errors are version-specific.
2. **Never filter when ρ ≤ 0.1 or when the effect is not direction-valid.** Defaults, inertia, and friction effects fall in this group. Filtering on them is worse than filtering at random.
3. **Filter only when the per-test budget is below N\*(ρ).** With effect spreads like Upworthy's, that means fewer than about 1,000 impressions at ρ ≈ 0.3. Such budgets are typical of long-tail or low-traffic surfaces, not of a platform's main pipeline.
4. **Otherwise, use twin scores only as a calibrated prior, and expect savings of a few percent.** Never ship on twin evidence alone.
5. **Report the configuration.** Record the model identifier and access date, the persona format, the prompt, the reasoning setting, the estimated ρ, and the share of unusable outputs. Synthetic evidence that cannot be audited should not drive design decisions.

The rules are deliberately quantitative. A team that wants to use synthetic agents more aggressively needs to show a higher ρ for its configuration, not argue that LLMs "think like humans" [11], [12].

## Limitations

Human benchmarks come from one U.S. online panel and cover seven effects. Field outcomes come from one publisher and one kind of treatment (headlines), with click-through as the only metric. The decision model assumes normally distributed effects and equal allocation across arms. Adaptive designs such as bandits may change the size of the gap between filtering and testing all candidates; we leave them to future work. Model versions change quickly, so our numbers will date; the method of estimating ρ and comparing the budget with N\* will not. Independent studies of the same archive likewise find weak click prediction and no benefit from personas [13], [14]. This suggests our estimates are not an artifact of one prompt.

## Conclusion

Synthetic agents are neither valid nor invalid in general. In our data, they knew the direction of cue-based effects, misjudged magnitudes and defaults, and gave a weak signal about which real headlines win. For an experimentation pipeline, the useful question is not whether twins are informative but whether they are informative enough to change what gets tested. At current levels, they are not. Platforms should use them as a cheap, calibrated prior, keep human traffic for the decisions, and re-check ρ every time the model changes.

## Acknowledgments

[To be added.] Data and code: [repository URL].

## References

[1] J. J. Horton, A. Filippas, and B. S. Manning, "Large language models as simulated economic agents: What can we learn from homo silicus?," NBER Working Paper 31122, 2023.

[2] L. P. Argyle, E. C. Busby, N. Fulda, J. R. Gubler, C. Rytting, and D. Wingate, "Out of one, many: Using language models to simulate human samples," *Political Analysis*, vol. 31, no. 3, pp. 337–351, 2023.

[3] O. Toubia, G. Z. Gui, T. Peng, D. J. Merlau, A. Li, and H. Chen, "Twin-2K-500: A data set for building digital twins of over 2,000 people based on their answers to over 500 questions," *Marketing Science*, 2025.

[4] G. V. Aher, R. I. Arriaga, and A. T. Kalai, "Using large language models to simulate multiple humans and replicate human subject studies," in *Proc. 40th Int. Conf. Machine Learning (ICML)*, 2023, pp. 337–371.

[5] M. Binz et al., "A foundation model to predict and capture human cognition," *Nature*, vol. 644, pp. 1002–1009, 2025.

[6] T. Peng, G. Gui, M. Brucks et al., "Digital twins are funhouse mirrors: Five systematic distortions," arXiv:2509.19088, 2026.

[7] J. M. Jachimowicz, S. Duncan, E. U. Weber, and E. J. Johnson, "When and why defaults influence decisions: A meta-analysis of default effects," *Behavioural Public Policy*, vol. 3, no. 2, pp. 159–186, 2019.

[8] N. Carlini, D. Ippolito, M. Jagielski, K. Lee, F. Tramèr, and C. Zhang, "Quantifying memorization across neural language models," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2023.

[9] R. Kohavi, D. Tang, and Y. Xu, *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing*. Cambridge, U.K.: Cambridge Univ. Press, 2020.

[10] J. N. Matias, K. Munger, M. Aubin Le Quere, and C. Ebersole, "The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media," *Scientific Data*, vol. 8, art. 195, 2021.

[11] J. Hullman, D. Broska, H. Sun, and A. Shaw, "This human study did not involve human subjects: Validating LLM simulations as behavioral evidence," arXiv:2602.15785, 2026.

[12] S. Wang, K. Hunt, S. Tang, and K. Joseph, "When can LLM digital twins reduce human measurement? From behavioral fidelity to statistical substitutability," arXiv:2609.07987, 2026.

[13] J. Persson, M. Schultzberg, and S. Ankargren, "Statistical foundations of LLM-based A/B testing: A surrogacy framework for human causal inference," arXiv:2606.17165, 2026.

[14] A. C. Maiorano, "Do synthetic personas predict real audience response? A sim-to-real study where a no-persona baseline beats persona-based copy simulation," arXiv:2609.25010, 2026.

## About the author

**[Author name]** is [position] at [affiliation]. [Research interests.] Contact: [email].
