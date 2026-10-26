# Amendment 1 to pre-registration #320110 (written 2026-10-26, before any C2 confirmatory output was generated)

Registered as AsPredicted #320124 (type: observational/archival; bundled as overlapping with #320110; confirmation email received 2026-10-26).
The registered answers are in prereg/ASPREDICTED_2_ANSWERS.md.

Reason: a literature check after registration found that (i) several groups already evaluate LLM click prediction on the Upworthy Research Archive, with weak
accuracy and a finding that persona conditioning does not help (arXiv 2609.25010; Spotify Engineering 2026; arXiv 2606.17165), and (ii) prior work on reasoning
and bias is mixed and does not vary reasoning effort as a dial. The field test is therefore redesigned to test a theory-derived moderator and to include a
no-persona comparison. The H6 grid is replicated on new respondents as registered. C1 is unchanged.

## C2 changes (substantive; submitted as a second AsPredicted pre-registration before the C2 confirmatory run)
1. Moderator (from V1, textual channel): each test is classified as cue-contrast if its headline arms disagree on at least one of four lexical cues
   (digit present; question mark; word from a fixed negative/loss lexicon; second-person pronoun), otherwise non-cue. The rule is in pilot/analyze_c2.py and is fixed.
2. Predictions: P7a, excess winner agreement over test-specific chance is higher in cue-contrast than in non-cue tests (pooled over models, bootstrap CI over tests);
   P7b, the calibration slope (predicted on observed log-odds differences) exceeds 1 in cue-contrast tests; P7c, the no-persona arm does at least as well as the persona arm.
3. Arms: persona (demographics only) and no-persona (a typical US social-media adult), five draws per test per model, temperature 0.7, reasoning effort low.
4. Clarification of the calibration slope: predicted regressed on observed (slope > 1 = twin overstates). The registered text said 'observed on predicted', which contradicts its stated meaning.
   Development on the exploratory package showed that sampling noise in the observed log-odds differences biases this slope toward zero, so P7b is evaluated on the
   disattenuated slope (denominator corrected by the sampling variance of the observed differences); the raw slope is also reported.
5. Test selection: 1,000 tests from the confirmatory package (seed 2026) with 2-6 arms, distinct headlines, at least 1,000 impressions per arm, created outside the
   archive's documented randomization-problem window (2013-06-25 to 2014-01-10). The imbalance-flag column is not in the December 2020 files.
6. Development used only the exploratory package (150 tests, seed 11); no confirmatory-package outputs have been generated.

## H6 confirmatory grid (as registered, with these specifications)
- 100 new respondents (outside all mega-study files and outside C1), 4 models x 3 effort levels x 3 temperatures, C1 booklet, battery A (16 answerable + 10 invented, abstain nudge),
  battery B (10 additional invented items, no abstain nudge in the instructions). Code: pilot/run_h6c.py; analysis: pilot/analyze_h6c.py, committed before outputs.
- Predictions as registered: P4 (higher reasoning effort reduces cue-based effects and factual error), P5 (positive within-model co-movement). The exploratory pilot pointed the other way
  for bias; the registered directions are kept, so a contradiction will be reported as disconfirmation.
- Gemini 3.7 Flash cannot disable reasoning; its levels are low, medium, high mapped to levels 0, 1, 2.
