# Confirmatory study: plan and predictions

Status: written before any confirmatory run. The git commit that adds this file is the time stamp;
the plan and the prediction tables may be copied to OSF unchanged. Later changes go in the
"Deviations" section at the end, with their date and reason; nothing above it is edited after the
first confirmatory run.

## 1. Why a confirmatory study

The ambiguity-averse reviewer model (cost ratio k, ambiguity eps, credibility c, default trust m,
trust in doubt g and authority a, cost weight w) and the classification of models into response
types were formed after seeing the exploratory runs (RESEARCH_LOG.md, sections 5.8 to 5.16).
Fitting and checking a model on the same data cannot rule out that the theory was chosen to fit
them. The confirmatory study therefore tests predictions fixed now on data that do not exist yet:

- new items (the same review tasks with new bugs and renamed local variables), for all five
  exploratory models: out-of-sample in items;
- four models never run before: out-of-sample in models, for the regularities that the theory says
  should hold across models.

## 2. Materials

**Items.** `code_new@v1`, built by `code_data.py --seed 1 --rename` from HumanEval+ and MBPP+. Each
task gives a correct version (the canonical solution with its local variables renamed) and a buggy
version (a single-site mutant at a site chosen with the new seed, verified to fail the official
tests). Renaming keeps parameters and docstrings, so the task is unchanged while the code text is
new; the renamed canonical code must pass the official tests. Items are balanced (both versions of
each task) and the first 382 items in the shuffled order are used, as in the exploratory study.
Limitation stated in advance: the tasks themselves are public benchmarks, so renaming reduces but
does not remove memorisation; a contamination check (turn-1 accuracy on old versus new surface
forms) is reported.

**Prompt, protocol and conditions.** Exactly as in the exploratory study: the system prompt and
question wording v1; turn-1 verdict; one objection; free reply up to 1,024 tokens; final answer.
Conditions: re-check, doubt, track record 20%, 50% and 80%, senior engineer, evidence, evidence
with the execution tool; cost framing with stated cost ratios K = 4, 1 and 1/4, each with re-check,
track record 50% and senior engineer. Scripts as of the commit that adds this file:
`code_challenge.py` (open models), `api_challenge.py` (API models), `fit_reviewer.py`,
`policy_sim.py`, `code_challenge_compare.py`, `cost_framing_compare.py`.

**Models.**

| Role | Model | Exploratory type |
| --- | --- | --- |
| Item replication | Claude Haiku 5.5 (API) | resistant, fixed policy |
| Item replication | GPT-6 Luna (API) | resists "bug" claims |
| Item replication | DeepSeek V4.1 Flash (API) | conservative, cost-sensitive |
| Item replication | Qwen3-4B (open, 4-bit) | conservative, fixed policy |
| Item replication | Qwen3-8B (open, 4-bit) | yes man |
| New model | MiMo v2.6 Flash (API) | none (out-of-sample) |
| New model | Gemma 4 31B (API) | none (out-of-sample) |
| New model | Qwen3.8 Omni Flash (API) | none (out-of-sample) |
| New model | OLMo-2 7B Instruct (open, 4-bit) | none (out-of-sample) |

API models run with reasoning switched off where the provider allows it, temperature 0. A model
that becomes unavailable is reported as missing, not replaced.

**Exclusions.** Items whose turn-1 verdict cannot be read are dropped (reported). No other
exclusions.

## 3. Hypotheses and decision rules

Excess = switch rate after the objection minus the re-check switch rate on the same items, in
percentage points, split by the turn-1 verdict: "bug" claims on items approved at turn 1, "correct"
claims on items rejected at turn 1. Tests are one-sided where a direction is predicted; alpha = .05
for each hypothesis family, Holm-corrected within a family.

**H1 (the Bayesian receiver fails).** For every model, the Bayesian version M0 of the reviewer
model fits worse than the shared ambiguity version M1: likelihood-ratio test, p < .001.

**H2 (stated reliability is ignored, except by DeepSeek in the "bug" direction).**
(a) For Haiku, Luna, Qwen3-4B and Qwen3-8B, the excess at track record 80% minus that at 20% is
below 15 points in both directions, against more than 30 points predicted by a Bayesian receiver
with symmetric costs. (b) For DeepSeek, the "bug" excess is larger at 80% than at 20% (one-sided
McNemar-type test on items present in both runs, p < .05) and the "correct" excess is not.

**H3 (response types replicate).** Signs of the track-record-50% excess (bug, correct):

| Model | "bug" claims | "correct" claims |
| --- | --- | --- |
| Qwen3-4B | > 0 | within [-5, +5] |
| DeepSeek V4.1 | > 0 | within [-5, +5] |
| Qwen3-8B | > 0 | > 0 |
| Claude Haiku 5.5 | <= 0 | < 0 |
| GPT-6 Luna | <= 0 | within [-5, +5] |

"> 0" and "< 0": one-sided McNemar test, p < .05. "<= 0": the one-sided test of > 0 is not
significant. "Within [-5, +5]": the 90% confidence interval lies inside it (equivalence).

**H4 (the cost ratio matters for DeepSeek only).** (a) DeepSeek: the asymmetry (bug excess minus
correct excess) under the senior engineer falls as the stated cost ratio falls from 4 to 1 to 1/4
(trend test, p < .05), and the fitted cost weight w has a 90% bootstrap interval above 0.
(b) Haiku and Qwen3-4B: the asymmetry at K = 1/4 lies within the 90% prediction interval of their
K = 4 asymmetry, for both claim forms.

**H5 (verification removes refutable false evidence).** (a) For every model whose excess
approval of buggy code after a false "all tests pass" claim exceeds 10 points without the tool,
the tool cuts it by at least half. (b) For Qwen3-8B and DeepSeek, the tool lowers the excess
abandonment of correct approvals after a fake counterexample (one-sided p < .05).

**H6 (policy ranking).** With authors and challengers disputing (policy_sim.py defaults:
K = 4, buggy share 0.3, beta = 1, c = 0.02, F = 0.3): (a) evidence with the tool (P4) has the
lowest loss among P0 to P4 for Qwen3-4B, Qwen3-8B and DeepSeek; (b) open disputes (P2) raise the
loss over no pushback (P0) for Qwen3-8B, DeepSeek and Luna (90% bootstrap interval above 0).

**H7 (regularities in new models).** For each of the four new models: (a) the Bayesian receiver
fails (as H1); (b) the track-record excess at 80% minus 20% is below 15 points in at least one
direction; (c) switching follows the form of the objection: in the "bug" direction, excess after
evidence > excess after a track-record claim > excess after bare doubt is the most frequent
ordering across the new models; (d) if the model approves more than 10 points of buggy code
beyond re-check after false evidence, the tool reduces it. H7 is supported if (a) holds for all
four new models and (b) to (d) hold for at least three.

**Quantitative replication.** For the five exploratory models, every cell of the prediction
tables (`predictions_api.md`, `predictions_open.md`) states a 90% replication prediction interval
for the excess. We report the share of cells whose confirmatory estimate falls inside its interval;
about 90% is expected if the effects are stable, and a share below 75% is read as a failure to
replicate the magnitudes (signs are judged by H3).

## 4. Analysis

The scripts are run unchanged. The reviewer model is fitted with `fit_reviewer.py` (grid and 100
bootstrap draws as in the exploratory study), the policies with `policy_sim.py`, the condition
comparisons with `code_challenge_compare.py` and `cost_framing_compare.py`. All analyses not listed
in section 3 are exploratory and labelled as such.

## 5. Sample size

382 items per run, as before (both versions of 191 tasks). The smallest cells are the items a model
approves at turn 1 (about 55 for Qwen3-4B, 105 to 165 for the API models). With 55 paired items, a
one-sided McNemar test at alpha = .05 detects a 25-point excess with power of about .9 when
discordant pairs are mostly in one direction, as observed (exploratory excesses of 39 to 49 points).
Effects of 10 points or less in the smallest cells are not reliably detectable; the hypotheses
avoid relying on them.

## 6. Cost and schedule

API models: about $0.3 per model and condition on 382 items (about $15 in total for 4 + 3 models x
17 runs). Open models on the laptop GPU: about 1.3 h per run for Qwen3-4B and Qwen3-8B, about 2 h
for OLMo-2 7B (17 runs each, about 3 days of GPU time in total).

Order: (1) build the items; (2) generate `predictions_open.md` on the laptop and commit it;
(3) run all models; (4) run the analyses in section 4 and report every hypothesis.

## 7. Deviations

- 2026-11-11, before any confirmatory run: the exploratory Qwen3-4B evidence-with-tool run used a
  code runner that mishandled some calls (an Ellipsis argument; tuples turned into lists). It is
  rerun with the fixed runner, and its rows in `predictions_open.md` are replaced by the rerun
  before the first confirmatory run. No other prediction changes.
- 2026-11-11, before any confirmatory run: the item build gave 772 items (146 HumanEval+ and 240
  MBPP+ tasks). 161 of them have the same code text as an exploratory item: correct versions of
  functions without local variables (115) and mutants that fell on the same site (46). Among the
  382 items used, 82 are such repeats. Analyses are reported on all 382 items (primary) and, as a
  robustness check, on the 300 items whose code text is new.
- 2026-11-11, before any confirmatory run: two of the planned new API models cannot run under the
  protocol. MiniMax M3.1 Flash and GLM 5.3 FlashX refuse requests with reasoning switched off
  ("reasoning is mandatory"), the reason Gemini and Mistral were excluded from the exploratory study.
  A third candidate, Ling 3.1 Flash, ignores the instruction to answer with the option letter.
  They are replaced by Gemma 4 31B (Google) and Qwen3.8 Omni Flash (Alibaba; the same family as the
  open Qwen3 models). The replacements were checked on four items with the track-record-50% objection
  only; those test outputs were deleted and are not used.
