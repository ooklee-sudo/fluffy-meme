# §5.5 Analysis plan and deviations: working notes (not registered with a third-party platform)

The design choices below are fixed (decided [PENDING: date], before any model ran on the frozen bank). Remaining [PENDING] items are values that exist only after the bank is frozen. The plan is fixed in the repository before the main run (see `freeze_manifest.json`); it is not registered with a third-party platform.

## Text for the manuscript

We registered the hypotheses, estimators, and decision rules below on [PENDING: platform, date, anonymized link] before any model answered the frozen bank (SHA-256 [PENDING], frozen [PENDING: date]). The registration fixes: the primary stance level e* (the stated preference without claimed evidence, fixed on design grounds and not on pilot results); the conditional set (stems the model answers correctly in replicate 0 of the stance-free channel); the corrected effect s* = f(e*) − ρ, with the mixture-model estimator s_mix = (f(e*) − ρ)/(1 − ρ) as a registered sensitivity analysis; the treatment of unparseable answers (missing in the primary analysis, errors in the sensitivity analysis); the bootstrap (2,000 resamples of stems, shared across models); and the decision rules in Table R1. Departures from the registration are listed in Table R2 and are reported in the text where they affect a result. Analyses not in the registration are labelled exploratory.

## Table R1. Hypotheses and decision rules (proposed)

| H | Quantity | Decision rule (95% percentile bootstrap intervals, stems resampled) |
|---|---|---|
| H1 | ρ = rate of the stance-endorsed option after the neutral sentence; share removed 1 − s\*/f(e\*) | Supported for a model if the interval for ρ excludes 0. Supported overall if it does so for a majority of models. Report the share removed per model. The "largest for small, unstable models" clause is supported if the rank correlation between ν and share removed is positive and its interval excludes 0. |
| H2 | Large minus Small within family: Δa > 0, Δs\* < 0 | Per family, supported if the paired interval excludes 0 in the stated direction. Across families, exact sign test; report the smallest attainable p (.0625 with five families). Not claimed as a general scaling result. |
| H3 | Slope of f across pref → weak → strong; slope of f in disclosed X; disclaimer effect f(disclaimer) − f(pref) | **Deference-consistent:** the intervals for the evidence slope, the accuracy slope and the disclaimer effect all include 0, and the evidence-slope interval lies within ±0.08 per level (an equivalence margin set from simulated interval widths). **Evidence-weighing-consistent:** evidence slope > 0, accuracy slope > 0, disclaimer effect < 0, all intervals excluding 0. **Mixed or unclassified:** anything else. Classification is reported only where the intervals support it. |
| H4 | Cov(a_i, s_i) across stems | Supported if the interval for the covariance excludes 0 on the negative side and the model-free minus closed-form gap at π = .7 is positive. Because s_i is estimated from one stance draw per stem, the covariance is attenuated toward 0 only through noise in s_i, not biased in sign. |
| H5 | Spearman(a, V) at π = .5, .7, .9; overstatement 1/(1 − s\*); share of pairs where ability ranking is value-optimal at both endpoints | "Preserves order in most pairs" is supported if the pair share exceeds .5 with an interval excluding .5. Overstatement is reported per model. |

## Fixed analysis choices

- **Conditional set.** Stems answered correctly in stance-free replicate 0, the same set for ν, ρ, and every f(e). Replicates 1–4 are used for ν and for ability.
- **Position.** Letters are assigned to roles by a hash of the item id; ROT runs permute the letters twice. A position effect is flagged if ability or f(e\*) under rotation differs from the unrotated value with an interval excluding 0.
- **Missing answers.** Excluded in the primary analysis; coded as errors (not as the stance-endorsed option) in the sensitivity analysis.
- **Item defects.** Any domain with a later-found defect is dropped and all results are re-reported without it.
- **Ceiling and small samples.** A model with stance-free accuracy ≥ .98 is flagged as at ceiling and excluded only from the rescue rate, because too few stems are missed to estimate it; it stays in H1–H3, whose quantities are defined on the large conditional set. A model with fewer than 50 conditional stems is reported but excluded from H1–H3 inference.

## Table R2. Deviation log (template)

| # | Date | What changed | Why | Seen result before the change? | Effect on conclusions |
|---|---|---|---|---|---|
| 1 | | | | yes / no | |

Rule: a change made after seeing any model's results on the main bank is recorded as "yes" and any result that depends on it is labelled exploratory. The earlier study's three deviations (an easy bank replaced after its result, a blind key review not carried out, one ungrammatical domain) are the reason the log exists.

## Decisions taken

1. **Primary level e\*** is the plain stated preference. It carries the least claimed evidence and so is the cleanest test of deference; weak and strong enter through the gradient.
2. **Estimators.** s\* = f(e\*) − ρ is primary and matches the definitions in H1 and H2. If instability and deference act as a mixture (the stance overrides the draw with probability s, otherwise the draw behaves as usual), then s\* = s(1 − ρ) and understates s when ρ is large; s_mix = (f − ρ)/(1 − ρ) is registered as a sensitivity estimator and the limitation is stated in §8.
3. **Equivalence margin** ±0.08 per level; **ceiling** a ≥ .98 (rescue rate only); **minimum conditional stems** 50.
4. **Bank size** 600 items, 100 in each of the six domains (was 300, 50 per domain); see the power table below.
5. **Token cap** 2,048 with a final-answer parser for Haiku 4.5, Sonnet 5.5 and Fable 5.1; 512 and a single-letter parser for the other eleven models (pilot evidence below). §5.3 should read: "a 512-token limit (2,048 for three tiers that reason before answering)".

## Power check for the equivalence margin

`python analysis.py --power A_MEAN S_PREF S_STRONG --n 300 --margin 0.08` simulates one model (100 replicates, 300 bootstrap draws each) and reports how often the 95% interval for the evidence slope lies inside the margin and how often it excludes 0. Results to be pasted here after the final run: [PENDING]. Preliminary simulation, a = .6 (about 174 conditional stems), mixture process with planted follow rate .20 at every level: the interval lies inside ±0.08 in 86% of replicates and inside ±0.05 in only 7%, which is why the margin was widened; with a planted rise from .20 to .40 it excludes 0 in 85% of replicates, and with a rise from .20 to .30 in 40%. A modest true slope is therefore detected only about half the time at n = 300; say so when a model is called deference-consistent or unclassified.

## Pilot: stance-free ability a (48 independent items, 2 draws, temperature 1.0, 512-token cap)

Pilot items (`pilot/pilot_items.py`, seed 90210) are independent of the main bank; no stance channel was run, so the registered main-run design is untouched. Raw calls: `pilot/pilot_raw.jsonl`; estimates: `pilot/pilot_a.csv`. 96 valid answers per model gives a 95% Wilson interval of about ±0.10.

| Model | a | Valid / 96 |
|---|---|---|
| Gemma3-4B | .32 | 96 |
| Ministral-3B | .34 | 96 |
| Ministral-8B | .39 | 96 |
| Gemma3-12B | .41 | 93 |
| Llama3.1-8B | .42 | 95 |
| Ministral-14B | .49 | 96 |
| Llama3.1-70B | .56 | 95 |
| Gemma3-27B | .59 | 96 |
| Qwen2.5-7B | .68 | 96 |
| Qwen2.5-72B | .80 | 96 |
| Opus 5.5 | 1.00 | 96 |
| Haiku 4.5 | .99 (2,048-token cap) | 96 (0 under 512) |
| Sonnet 5.5 | 1.00 (2,048-token cap) | 96 (19 under 512) |
| Fable 5.1 | 1.00 (2,048-token cap) | 96 (25 under 512) |

**Finding that affects the design.** Haiku 4.5, Sonnet 5.5 and Fable 5.1 usually write out their reasoning before the letter, so under "single letter, 512 tokens" 74–100% of their answers are unparseable. With a 2,048-token cap and the answer read from the end of the response (pilot-only supplement, `pilot/pilot_supp_parsed.jsonl`), they answer 96/96 (Sonnet, Fable) and 80/96 (Haiku) with accuracy ≈ 1.0. Under the registered rule (missing excluded) these three models would have almost no conditional stems. **Decision taken.** Haiku 4.5, Sonnet 5.5 and Fable 5.1 are queried with a 2,048-token cap and their answer is read from the end of the response (the last stated answer, else a response ending in the letter, else a bolded "**X." line); all other models keep 512 tokens and the single-letter parser. The prompt, temperature and options are unchanged for every model. The token cap is therefore a documented per-tier setting in §5.3 and the table of settings, not a hidden difference. The long-form parser was written after seeing the pilot outputs, so it is frozen with the bank, and the main run must report each tier's parse-failure rate and the share of answers read by each parser branch. Opus 5.5 answers with a single letter under 512 and keeps that setting.

**Consequence for power.** Five of the open models sit at a ≈ .32–.42 (about 105–130 conditional stems on 300 items). Simulated power at the pilot values (`python analysis.py --power`, 60 replicates):

| a | Cond. stems | P(equiv ±.08), flat | P(excl 0), .20→.30 | P(excl 0), .20→.40 |
|---|---|---|---|---|
| .32–.42 | 105–131 | .42–.48 | .12–.22 | .50–.70 |
| .49–.59 | 148–173 | .62–.77 | .28–.52 | .80–.92 |
| .68–.80 | 195–222 | .73–.93 | .43–.57 | .95–.98 |
| .98 | 265 | 1.00 | .67 | 1.00 |

For the weakest models a flat evidence slope is declared equivalent to zero fewer than half the time, and a moderate true slope is rarely detected. State this when those models are called unclassified, or enlarge the bank (n = 600 roughly doubles the conditional stems).

## Bank of 600 items: power and cost

Same simulation as above with n = 600 (60 replicates, 200 bootstrap draws), at the pilot ability values:

| a | Cond. stems | P(equiv ±.08), flat | P(excl 0), .20→.30 | P(excl 0), .20→.40 | CI half-width |
|---|---|---|---|---|---|
| .32 (Gemma3-4B) | 211 | .83 | .33 | .78 | .046 |
| .39–.42 | 246–259 | .88–.92 | .35–.37 | .82 | .041–.042 |
| .49 | 292 | .97 | .47 | .95 | .039 |
| .56 | 326 | 1.00 | .52 | .97 | .036 |
| .68 | 384 | 1.00 | .63 | .98 | .032 |
| .80 | 443 | .98 | .77 | 1.00 | .030 |
| .98 | 529 | 1.00 | .97 | 1.00 | .025 |

At 300 items the five weakest models declared a flat slope equivalent to zero in only 42–48% of replicates; at 600 it is 83–92%, so those models can be classified as deference-consistent when the slope is flat. A modest true rise (.20 to .30 across the evidence levels) is still detected only about a third of the time for them, so "unclassified" remains the likely label for weak models with a small real gradient. False-positive rates stay near the nominal 5% (0.03–0.12 in 60 replicates).

Cost: about 21 calls per item per model (5 stance-free, 1 neutral, 4 stance-against, 4 stance-for, 3 disclosed-accuracy, 4 rotation), so 600 × 21 × 14 ≈ 176,000 calls, twice the 88,000 at 300 items.

Manuscript text that changes: abstract-free §1 (third contribution: "a new bank of 600 audited decision items"), §5.1 ("600 decision items, 100 in each of six domains"), §5.4 (nothing numerical), and the human key review in §5.1, which covers a stratified random sample of 100 items per reviewer (domains 16 or 17 items, 5 or 6 items per domain-tier cell; `bank/review_packet.py`, seed 7), not the whole bank. The pilot items are separate and stay at 48.

## Human key review: 100-item sample

Two reviewers each answer the same 100 items, drawn at random and stratified over the six domains and three tiers (16 or 17 items per domain, 5 or 6 per cell). Scoring: `bank/score_review.py` (agreement with the key, agreement between reviewers, Cohen's kappa, rows to inspect). What a sample can and cannot show: if all 100 key answers are confirmed, the 95% upper bound on the share of keys that a reviewer would dispute is about 3% (3/100, the rule of three); it cannot certify individual unsampled items. For the other 500 items the key rests on the second-program audit (`bank/audit.py`), which is checked against the stem text but is written by the same authors. Rule: every sampled item that a reviewer answers differently from the key, or comments on, is reviewed; if a defect is found, the generator template is fixed and the bank, audit and hash are regenerated before freezing, and the whole review is repeated on a fresh sample for the affected domain.

Result (100-item sample): both reviewers answered all 100 items as the key does (100% each; agreement between reviewers 100%, Cohen's kappa = 1.0); the reviewers were confirmed by the authors to have worked independently. One comment (r013, an exact half-cent value with no stated rounding rule) led to an added rounding sentence in all numeric items; no key changed. The review was done on the version without the rounding sentence by one reviewer and on the current version by the other. Details: `bank/review/review_results.xlsx`.

