# AsPredicted answers (copy into the form; question wording may differ slightly on the live form)

## 1. Data collection: Have any data been collected for this study already?
Yes, partly. Exploratory twin simulations (five LLMs, 772 participants of the Twin-2K-500 mega-study, plus a reasoning-effort x temperature pilot) were run and seen before registration; propositions were formulated after seeing them. The confirmatory twin simulations (new respondents, new prompt template) and the field analysis on the Upworthy confirmatory package have NOT been run. Human benchmark effect sizes come from public data and are fixed in the registered document.

## 2. Hypothesis
When are LLM digital twins valid substitutes for human subjects? A twin is predicted to be valid only if (V1) the treatment acts through textual information, (V2) the effect is not mediated by effort or transaction costs, (V3) the paradigm is novel, not memorized, and (V4) the agent's reasoning regime matches the human one. With D = twin effect minus human effect:
P1 cue-based effects (loss framing, anchoring, attraction): D > 0 on canonical paradigms.
P2 defaults: D > 0 on the canonical paradigm (organ donation), D <= 0 on the novel paradigm (green energy).
P3 for defaults and fairness, D_novel - D_canonical < 0.
P4 higher reasoning effort reduces cue-based effects and factual error within model.
P5 across model x effort x temperature cells, standardized bias magnitude and factual error rate correlate positively within model.
P6 naming the phenomenon in the prompt increases effect magnitude on canonical paradigms.
P7 on public headline A/B tests, twin-predicted winners agree with observed winners above chance, and twin-predicted effects exceed observed effects.

## 3. Dependent variable
Defaults: opt-out minus opt-in share of the default-consistent choice (percentage points). Attraction: log odds ratio of choosing the target with vs without the decoy. Fairness: Cohen's d of the 9-point fairness rating (targeted vs broad advertising). Loss framing: Cohen's d of the 6-point program preference (loss vs gain frame). Anchoring: Cohen's d of log10 numeric estimates (high vs low anchor). Factual error rate: share of 16 answerable items answered wrongly (abstain counts as not wrong); fabrication rate: share of 10 invented-entity items answered with a non-abstain option. Field test: agreement of twin-predicted best headline with observed best headline; Spearman correlation of predicted and observed log odds of click; calibration slope of observed on predicted effect.

## 4. Conditions
Twin study: each simulated respondent is randomly assigned one condition per task (defaults: opt-in/opt-out; attraction: binary/decoy; fairness: targeted/broad; framing: gain/loss; anchoring: high/low anchor). Crossed with 5 models (claude-haiku-5.5, gpt-5.6-luna, gemini-3.7-flash, grok-4.3, llama-4-maverick) and 2 persona architectures (demographics only; Twin-2K-500 persona summary). Reasoning-effort grid: 3 effort levels x 3 temperatures (0, 0.7, 1.2) x 4 models. Field test: headline variants within each Upworthy test.

## 5. Analyses
Effect sizes with respondent-level bootstrap 95% CIs (2,000 resamples), computed per model and pooled. P1-P3 and P6: a proposition is "supported" if the sign holds in at least 4 of 5 models and the pooled CI excludes zero, "partly supported" if the sign holds in at least 4 of 5 but the pooled CI includes zero, otherwise "not supported". P4-P5: OLS with model fixed effects and heteroskedasticity-robust SEs on the 36 cells; P5 uses within-model Spearman correlation. Multiplicity: Benjamini-Hochberg across pooled tests (q = .05). Field test: exact binomial CI on agreement; support if the lower bound exceeds 0.5 in at least 3 of 5 models and the calibration slope exceeds 1.

## 6. Outliers and Exclusions
Responses that are not valid JSON or give an out-of-range option are excluded and counted per model; a cell with more than 10% exclusions is flagged and reported separately. Numeric estimates are log10-transformed and floored at 1; no other outlier removal. Field test: exclude tests flagged for randomization imbalance risk and tests with fewer than 1,000 impressions per arm; the winner-agreement metric uses only tests whose observed difference is significant at p < .05.

## 7. Sample Size
Twin study: 600 simulated respondents per phenomenon x persona architecture x model, drawn at random (seed 2026) from the Twin-2K-500 participants not included in the exploratory run (about 1,286); if fewer are available for a cell, all are used. Reasoning grid: 100 respondents per task and 100 for the factual battery per cell. Field test: 1,000 tests drawn at random (seed 2026) from the Upworthy confirmatory package, after the exclusions above. Total compute budget capped at 300 USD.

## 8. Anything else?
Primary analysis uses prompt template B (different wording and ordering from template A used in exploratory runs), temperature 0.7, low reasoning effort, one draw per respondent. Model versions and access dates are logged. Prompts, outputs, and code will be deposited publicly. Any deviation from this registration will be listed in the paper. Exploratory findings are labeled as exploratory.

## 9. Title / study type
"When are synthetic agents valid? Boundary conditions for LLM digital twins". Experiment (simulation) and secondary analysis of public field experiments.
