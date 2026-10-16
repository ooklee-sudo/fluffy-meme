# Related work (searched 2026-10-16)

Status column: **verified** = title/authors/abstract read via the arXiv API or the publisher page in this session;
**search only** = known from search-result summaries, not opened; **memory** = from memory, not checked.

## A. LLM synthetic consumers / market research
| Work | Finding relevant to this study | Status |
|---|---|---|
| Brand, Israeli, Ngwe. *Using GPT for Market Research* (HBS WP 23-062, 2023; updated 2025) | GPT-3(.5) WTP and conjoint results look realistic; authors urge validation against real data | search only |
| Maier et al. *LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings*, arXiv:2510.08338 | Direct numeric ratings give unrealistic distributions; SSR reaches **90% of human test-retest reliability**, KS similarity > 0.85 (57 surveys, 9,300 responses) | verified |
| Kaiser et al., *NIM Marketing Intelligence Review* 18(1) | Synthetic respondents show less variation and inflated positive attitudes toward familiar brands | search only |
| Chu et al. arXiv:2510.18155 (marketing multi-agent simulation) | Virtual town, discount strategies; age bias | verified (abstract) |
| Huang & Wang, *LLM-Powered Virtual Population for Demand Simulation and Pricing*, arXiv:2606.16183 | Persona mixture; aggregate demand as binomial; single-period, no repeat counts | verified |
| Sashihara et al., arXiv:2511.13233 | Uses "distribution of purchase counts per buyer" as a validation metric in a simulated marketplace; no NB fit | search only |

## B. Variance collapse / sampling failure
| Work | Finding | Status |
|---|---|---|
| Jang, Lee, Kim, arXiv:2607.25292 | Instruction-tuned models collapse to one output; describing a distribution beats per-call sampling | verified |
| Gu et al., *Do LLMs Play Dice?*, arXiv:2404.09043 | LLMs understand probabilities but struggle to sample; code tools help partly | verified |
| Zhang et al., *Verbalized Sampling*, arXiv:2510.01171 | Prompting for several answers with probabilities restores diversity (creative tasks) | verified (title/authors) |
| Li, Li, Qiu, arXiv:2507.02919 | Silicon samples collapse toward majority view within subgroups | verified (title/authors) |
| Ku et al., arXiv:2607.03091 | Collapse also occurs in supervised baselines (random forest); severity is model-dependent | verified (title/authors) |
| Zhou et al., arXiv:2409.02601 | ChatGPT answer distributions more deterministic and normal-looking than humans' | verified (title/authors) |
| Zhang, Zhang, Zhao, *Predicting Effects, Missing Distributions*, arXiv:2510.03310 | LLMs often reproduce hypothesis-test outcomes but not full distributions; dispersion mismatch matters; CoT and tuning help | verified |
| Tigre & Souto, arXiv:2609.13148 | Variance compression and coefficient sign flips in LLM consumer panels; diagnostics | verified (title/authors); date 2026-06-03 does not match ID prefix, recheck |

## C. Effects of treatments
| Work | Finding | Status |
|---|---|---|
| Hewitt et al., *Predicting results of social science experiments using LLMs* (Stanford) | 70 survey experiments; r ~0.85 with true effects; effect sizes systematically overstated | search only |
| Horton (2023), arXiv:2301.07543, *Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?* | Qualitatively similar results to classic experiments | verified |

## D. Count-data background (from memory, verify before citing)
Ehrenberg (1959) NBD for purchase frequency; Schmittlein, Morrison & Colombo (1987) Pareto/NBD; Fader, Hardie & Lee (2005) BG/NBD; Cameron & Trivedi (1990) overdispersion test; Fader & Hardie (2001) CDNOW.

## Corrections to the proposal's reference list
1. arXiv:2305.02531 is Goli & Singh, *Can LLMs Capture Human Preferences?* (intertemporal choice), not Brand, Israeli, Ngwe. Brand et al. is *Using GPT for Market Research*.
2. The "about 90% correlation" for purchase intent is wrong: the source (arXiv:2510.08338) reports 90% of human test-retest reliability and KS similarity > 0.85.
3. Horton's full title should be cited.
4. alphaxiv.org/abs/2607.18310 not opened; unverified.

## Gap check
No paper found that evaluates LLM-generated per-customer purchase counts against Poisson/NB fits. Closest: 2510.03310 (dispersion mismatch), 2404.09043 (sampling), 2606.16183 (aggregate binomial demand), 2511.13233 (count metric, no fit). Claim holds only within this search.
