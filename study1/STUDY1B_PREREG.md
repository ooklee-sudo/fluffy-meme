# Study 1b: registered plan (hard bank, open-weight panel)

Status: written before any model has seen the hard bank. Study 1 (Claude ladder, easy bank) is finished and is not changed by this plan.
Date of this plan: 2026-10-03. The commit that contains this file, `items_hard.py`, `audit_hard.py`, `models_hard.json` and `bank.py` is the registration; a second commit freezes
the main bank after the pilot gate (section 8). Nothing below may be edited after the freeze except by an entry in the deviations log at the end.

## 1. Why this study
Study 1 found normative consistency at ceiling (RN .992 to 1.000) and deference near floor (0 to 2.5 percent, 8 of 480 answers) on one commercial ladder. Direction hypotheses
about scale could not be tested. Study 1b changes two things only: the items are harder and the stance asserts support for the unsupported action; and an open-weight panel is added.

## 2. What changes relative to Study 1 (and what does not)
Same: three options with fixed roles (gold, unsupported, other); two channels (normative, social = normative plus one sentence); first choice; one completion per query; the system prompt
and parser; outcomes RN, RS, CondRS, Flip, CorrectSocial, calibration; analysis code (`analyze.py`, read-only); Large-minus-Small contrasts, equivalence margin of 5 points.
Different: (a) hard bank `items_hard.py` with six domains (two-stage gamble, rule with exception, ledger with credit and tax, under-determined case, versioned rule, units and ratios), 20 stems each;
(b) stance sentences assert uncheckable support (a colleague's review, experience, a lawyer's confirmation, precedent), so the manipulation is "stance with claimed support", not a bare preference;
(c) model panel in `models_hard.json`: four open-weight families (Qwen2.5 7B/72B; Llama-3.1 8B/70B; Gemma-3 4B/12B/27B; Ministral 3B/8B/14B) served through OpenRouter, and the Claude ladder again.
Reasoning-first families (Qwen3, gpt-oss) are excluded so that reasoning is not confounded with size; H4 of Study 1 is therefore not tested.

## 3. Hypotheses (same wording as Study 1, applied to two samples)
Samples: the open-weight sample (four families, fixed decoding as far as the host allows) and the Claude sample, analysed separately and never pooled with each other.
H1 Larger tier has higher RN. H2 Larger tier is not less deferential: Large minus Small on RS and CondRS has a 90 percent CI above -5 points (non-inferiority; equivalence if inside +-5).
H3 CondRS rises with tier (Large coefficient positive, Holm-adjusted over RN and Flip as implemented in `analyze.py`).
Claim about scale: stated as a pattern over families (exact sign test over the four open families; the Claude family reported separately). With four families the smallest possible two-sided p is .125.

## 4. Informativeness rule (post-collection, registered now)
The study counts as informative about a hypothesis only if the outcome has variance: pooled RN in the open sample between .35 and .95, and pooled CondRS above .02 in at least one tier.
If not, the result is reported as uninformative for that hypothesis and the bank is not changed again within Study 1b.

## 5. Data collection
Each model: 120 stems x 2 channels = 240 queries, one completion each, `max_new_tokens` 512, temperature 0 where the endpoint accepts it (`temperature_applied` is logged per row; Claude Sonnet, Opus, and
Fable calls carry no temperature). OpenRouter chooses the serving provider and quantization; the served provider is not controlled and is a limitation. Parse failures are coded zero on every indicator
and also analysed with failed rows dropped; if a model exceeds 5 percent failures it is kept and flagged, not replaced. No model is dropped or added after seeing results. Order is hash-interleaved.

## 6. Audit
`python audit_hard.py`: each stem must have three distinct options with the three roles; no digits in the stance sentences; all texts unique; gold letters balanced; the two channels must differ by exactly one
sentence; and an independent re-solver, which parses the stem text and not the generator parameters, must agree with the key on all 120 stems. A blind human review of the keys by two people who have not seen the
generator is planned (`audit.py` review-sheet machinery can be pointed at the hard bank); if it is not done it is reported as not done.

## 7. Pilot gate
Pilot bank: 8 stems per domain from a different seed (`python items_hard.py --pilot`), never in the main analysis. Pilot models: claude-haiku, qwen2.5-7b, llama3.1-8b, llama3.1-70b (96 queries each).
Gate (computed by `python audit_hard.py --pilot-gate`): (i) mean RN across pilot models in [.35, .90]; (ii) at least 4 of 6 domains with mean RN in [.15, .95]; (iii) at least one pilot model with conditional
deference of at least .05. If the gate fails, only difficulty parameters (margins, steps, distractors) may change, a new pilot seed is used, and the attempt is logged below. The main bank is not run before the gate passes.

## 8. Freeze
After "GATE PASSED": run `python items_hard.py` and `python audit_hard.py` (must print "mechanical problems: 0"), commit `items_hard.jsonl`, `gold_hard.json`, `MANIFEST_hard.json`, tag the commit `study1b-freeze`, then run `run_hard.bat`.

## 9. Analysis
`analyze.py` unchanged, run twice (open sample; Claude sample) as in `run_hard.bat`. Reported in full: model-level descriptives, pooled and by-family regressions, equivalence table, family-level contrasts, deference by
stance sentence, McNemar pairs for the Claude ladder. Domains 4 to 6 in the output are labelled as in Study 1; in the hard bank they are the under-determined, versioned-rule, and units domains. Exploratory (labelled as such): domain-level
results; the share of the "ask for the missing fact" answer in H4; the third-option rate by tier; comparison with Study 1 for the Claude ladder.

## 10. Known limitations stated in advance
Template-generated stems written by the research team; hosted open-weight inference without control of hardware; tiers inside families differ in more than size; single-turn first choices; the stance now carries
claimed support, so results are not comparable to Study 1 on the deference scale without caution.

## Deviations and attempts log
- 2026-10-03, pilot attempt 1 (seed 20251003): gate PASSED. Pilot RN by model: claude-haiku 1.000, llama3.1-70b .979, llama3.1-8b .562, qwen2.5-7b .500; mean RN .760; six of six domains inside [.15, .95];
  conditional deference .042, .191, .444, .458. No parameter was changed. The pilot completions are not used in any hypothesis test.
- 2026-10-03, freeze: bank generated by `items_hard.py` (seed 20251004), audited (mechanical problems: 0, independent re-solver agrees on all 120 stems), committed with `items_hard.jsonl`, `gold_hard.json`, `MANIFEST_hard.json`.
  Technical correction before the freeze: the bank files are written with LF line endings so that the hash is identical on Windows and Linux; `run_hard.bat` no longer regenerates the bank.

## Addendum 1: wording robustness (written 2026-10-03 after the main run, before these runs; exploratory)
Purpose: test whether the direction of the tier effect depends on the registered wording. All 14 models of the main run are re-queried on the same frozen bank with (a) system prompt variant 1, (b) system prompt variant 2 (both with stance set A),
and (c) the alternative stance set B (system prompt 0). The registered wording remains the primary analysis; `analyze.py` reports the robustness table for the pooled open sample and the conclusion is stated only if its sign is the same across wordings.
No model or item is added or dropped. Outcomes of the robustness runs are not used to change any conclusion of the primary analysis.

## Addendum 2: three further model families (written 2026-10-03 after the main run, before these runs; exploratory extension)
Purpose: more families for the family-level sign test. Added in `models_hard_ext.json`: OpenAI GPT-4.1 (nano, mini, full), Amazon Nova (micro, lite, pro), Cohere Command (R7B, R 08-2024, R+ 08-2024), all non-reasoning, hosted through the same aggregator, registered wording only.
Reported separately: (i) the five original families as registered; (ii) all eight families, with the exact sign test over eight families (smallest two-sided p = .0078). The registered primary analysis is not changed by these additions.

## Addendum 3: aligned-stance channel and the value of AI review (written 2026-10-03 after the main run, before these runs; confirmatory for the stated quantities, exploratory otherwise)
Motivation: the main design always sets the stance against the evidence (the requester is wrong). An economic reading of delegated review needs the case in which the requester is right as well, so that the delegate's behavior can be compared across the two cases.
Design: a third channel, `aligned`, with the same four stance sentences (set A) but with X = the gold action (`aligned_x` in `items_hard.py`, derived from the frozen bank; the frozen bank files are unchanged and `audit_hard.py` still matches them). Same system prompt, same 120 stems, one completion per query.
Models: the 14 models of the main run, registered wording only (`run_aligned.bat`). Normative and social completions are those of the main run (not re-queried).
Quantities, defined before the data: RN, Pw (correct when the stance is wrong, CorrectSocial), Pa (correct when the stance is right); CondRS = P(follows the wrong stance | RN = 1); Rescue = P(correct under a right stance | RN = 0);
V_obs(pi) = pi*Pa + (1-pi)*Pw - pi for pi in {.5, .7, .9} (accuracy of a requester who follows the delegate, minus the requester's own accuracy pi); V_model(pi) = (1 - CondRS)(RN - pi).
Registered questions: (1) is the delegate a pure yes-man, i.e. is Rescue equal to CondRS? Reported as the difference with a 95% bootstrap interval over stems for models with at least 10 stems at RN = 0; no directional claim is made. (2) Does ranking by RN rank models by V_obs? Spearman correlations over the ten open models and the best model by each criterion. (3) Within families, how does V_obs change from Small to Large? Paired bootstrap.
Sensitivity analyses, specified in advance: failed rows dropped; Domain 6 excluded (see next paragraph). Conclusions are stated only if they hold in all three versions.
Disclosed defect of the frozen bank, found while writing the aligned phrases: the stance phrase of Domain 6 stems in the stance-against-evidence channel is not grammatical (for example "we should outside the policy limit"). It was not changed (the bank is frozen and the main results were obtained with it). The aligned phrases of Domain 6 are grammatical.
Therefore Domain 6 is excluded in one sensitivity analysis, and the limitation is reported.
- 2026-10-03, Addendum 3 run (aligned channel, 14 models, registered wording): completed without changes to the plan. Main results (registered coding): Rescue exceeded CondRS in all ten open models (+.048 to +.509; 95% interval excludes 0 in seven); stance sensitivity S = Pa - Pw tracked CondRS (r = .98); model-free V_obs agreed with (1 - s)(a - pi) to within .052; ranking by RN vs V_obs Spearman .94 / .98 / .86 at pi = .5 / .7 / .9; best model by both: Qwen2.5-72B. Same conclusions with failed rows dropped and with Domain 6 excluded. Raw outputs: results\analysis_1b_aligned*.md on the author's computer.
- 2026-10-03, technical deviation during Addendum 1 and 2 runs: an upstream rate limit (HTTP 429) on one hosted model aborted the runner after five failed calls. The runner wrote failed-call rows (finish_reason beginning with "error:") that a resume would have treated as answered. Fix, applied before any further collection: 429 responses are retried with exponential backoff (up to 6 waits); `clean_errors.py` moves failed-call rows to a separate file so that they are queried again; failed calls never count as parse failures. The number of failed-call rows removed from each results file is reported. No item, model, or analysis rule was changed.
- 2026-10-03, analysis rule added after the Addendum 1 and 2 runs, before their results were read: failed-call rows are left out of every analysis (they are not answers), and a query that appears more than once is counted once (first row kept). The number of rows left out is printed by `analyze.py` and listed by `log_report.py`. The analysis crashed once on unequal row counts in a vendor-pair test before any result was produced; the test now aligns pairs by stem.
