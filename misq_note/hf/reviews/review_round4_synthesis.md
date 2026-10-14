# Simulated MISQ review, round 4 (three independent readers of MANUSCRIPT_MISQ_v4_blind.md, 2026-10-14)

Verdicts: Reviewer 1 (IS and measurement) reject as a MISQ research article, borderline as a Research Note if rebuilt as a single-question measurement paper; Reviewer 2 (econometrics) major revision; Associate Editor desk reject as a research article, Research Note or methods venue suggested.

## Agreed by all three
1. The paper is still more than one paper: the information-theoretic section (Section 2, 3.4, 4.6, Table 7, Appendix E), the arrival-process material (4.1, Appendix D) and the Twitter-era/LLM-release appendices dilute the measurement question. Cut to a single-question note (about 5,000–7,000 words).
2. Human labels are not ground truth and not outcome-blind: coders remembered the war, the investigator who adjudicated knew the hypotheses, and 66% of final escalation labels were adjudicated. Need an independent blind third coder; model-versus-each-coder agreement; a latent-class (Dawid–Skene) analysis.
3. "Attenuation" and "detectable (p = 0.04)" are not established: 12 label-set contrasts without multiplicity control; the one significant contrast (human minus original model, p = .038) is borderline; the class sets differ in membership, so the difference is event selection, not classical attenuation; a significant-versus-non-significant contrast is not a test.
4. The model re-labelling does not show "not a prompt problem": one vendor's family, versions unrecorded, no few-shot or other-family run, arbitrary κ ≥ 0.60 rule against a human ceiling of 0.61–0.67.
5. Identification: the placebo is not matched on volatility, drift or news; the 5–15 minute defence was chosen after seeing Table 6; CFD timestamps, roll and same-second ticks; three events carry 54% of the de-escalation mean.
6. Differential selection: 48% of escalation signal posts versus 22% of de-escalation posts have no window (83% weekends/closed).
7. Hygiene and blinding: placeholders (model versions, AI declaration, repository), the reference-check note, "pre-specified, not pre-specified", dangling "results file and the results file" in Appendix C, Appendix A rows with stale numbers, identifying phrases (the authors' repository, department, principal investigator, commit dates).

## Verified discrepancies
- Section 3.5 "pre-specified, not pre-specified" (introduced by my global replacement); Appendix C "the results file and the results file" (file-name removal).
- Appendix A rows for H5c and H7 quote the earlier sample and one-sided p (+0.62 vs 0.22; +0.53 vs 0.26; escalation p = 0.007) while Section 4.5 reports the headline sample and two-sided p (+1.04 vs 0.20; +0.48 vs 0.20; p = .013).
- Bootstrap for label-set differences used 4,000 resamples; the plan said 10,000. Plan item D(iv) (adjudicated items set to OTHER) is equivalent to the "consensus only" rows but is not labelled as such.
- Table 6 uses one-sided p; other tables two-sided.

## Consolidated plan
A. Mechanical fixes now: typos, Appendix A rows, B deviation, D(iv) labelling, two-sided Table 6, remove reference-check note, anonymization, abstract trimmed.
B. New analyses now (plan amended before computing): drift-and-volatility-matched placebo; next-open returns for the excluded weekend/closed posts; discordant-event decomposition (what the model sets add and what those posts return); forest plot of label-set estimates.
C. Needs the author: an independent blind third coder for the adjudicated items; a second episode or the 2017–21 oil tweets with human labels; other model families and a few-shot variant; exchange futures data.
D. Restructure into a focused note: move Section 2, 3.4, 4.6, Table 7 and 4.1 detail into appendices; retitle and shorten the abstract to about 150 words.
