# Simulated MISQ review, round 2 (three independent readers of MANUSCRIPT_MISQ_v2.md, 2026-10-14)

Readers: Reviewer 1 (IS theory and fit), Reviewer 2 (econometrics and design), Associate Editor (presentation and desk decision). Each read the manuscript without seeing our own conclusions. Verdicts: Reviewer 1 reject; Reviewer 2 major revision bordering on reject; Associate Editor desk-reject in current form (invite resubmission of a re-framed paper).

## Points on which all three agree
1. The information-theoretic account is a measurement vocabulary, not a tested theory. Of P1–P7 none has a clean positive test (P4 marginal, 0.0014 bits; P2 in the tariff sample is volatility-confounded). The abstract, 5.2 and the conclusion still lead with the framework. The one discriminating test (P6) contradicted it.
2. The only strong empirical result is the human-label co-movement in one episode (n = 29 and 16). It depends on a few events, a label-dependent cluster filter and a sample that changed three times; the pre-post excess (+0.48, p = 0.030) is fragile and the placebo shows the 30 minutes before the post also exceed the placebo.
3. Label validity (κ 0.29–0.56 against humans) is poor; the 2017–21 oil and tariff "sign flip" rests on model labels, and the sign-flip narrative should leave the abstract.
4. "Pre-registered" is overstated: plans are repository files, many written after outcomes were seen; commit dates cluster on 13–14 October 2026.
5. Appendix D (Musk, GDELT, LLM releases) is a different paper; D.3 contains unverified recollections and should go.
6. The paper is a research log: length, abstract (about 480 words), repeated hedges, five-versus-seven proposition mismatch, and no IS-specific (platform/artifact) theory.

## Items the readers raised that I checked against the manuscript and code
- Correct: the abstract's human κ "0.61 to 0.69" does not match the body (round 1 human–human 0.51; round 2 0.69; 0.61 is not stated as a κ in Section 4.6); the intro says "five implications" while 2.4 states seven propositions; "double digits" holds for 7 April (−12.0%) but not for 23 March (−9.8%); the summary of sample sizes shifts between 33, 25, 29 and 26 events with no reconciliation table; the staleness rule (last tick within 10 minutes, MAXAGE = 600 s in the code) and the CFD spread are not reported in the text.
- Incorrect or outdated: the manuscript no longer contains "pending" for H5c in 4.2 or 5.4 (it was removed); the manuscript is about 11,400 words, not 14,000; the code does handle staleness (10-minute cutoff) though the text does not say so.
- Not yet checked: the Holm family for P4 (Reviewer 2 says p = 0.041 would be 0.16 within a family of four); leave-two-out of the headline on human labels; the 191-to-45 reconciliation; whether round-3 weekend posts explain 87 → 45; U and |z| sharing a volatility denominator (true by construction in the code: both use the 60-day volatility, to be stated).

## Prioritized actions (consolidated)
A. Decide the claim. Recast as a descriptive and measurement paper built on the Hormuz episode: (i) posting is overdispersed and follows volatility; (ii) human-labelled posts co-move with oil at tick level, comparable in size to the pre-post drift; (iii) model labels would have produced a false one-sided headline. Information theory becomes motivation and a short section saying which implications were tested and failed. Change the title.
B. Cut and move: Appendix D to an online appendix or remove (delete D.3); 4.4, 4.5 and P7 to a supplement; target about 8,000–9,000 words.
C. Robustness of the headline: leave-two-out, fixed label-independent cluster rule (2/3/6 hours), both-coders-agree-only labels, window choice (15/30/60), a 191 → 45 reconciliation table, spread and staleness-cutoff sensitivity, exchange futures for a subsample if obtainable.
D. Multiplicity and status: a table giving each reported number its status (confirmatory / amended / exploratory / post hoc), the family used for Holm, two-sided and adjusted p-values; stop calling P4 "supported".
E. Abstract: about 200 words, at most five numbers, no sign-flip, state the null results plainly.
F. Consistency fixes: five versus seven implications; κ range; "double digits"; sample-size table; terminology (proposition versus hypothesis labels); unify the outcome definition (two-hour versus 30-minute tick).
G. Complete or remove: human labels for the 2017–21 oil sample (or drop the sign-flip), USD/CNH, Appendix B, the AI declaration, repository DOI, blind-review version.
H. IS fit: add a section on what the case means for IS (platform speech as data, LLM coders as measurement instruments, a validation workflow) and engage IS literature; otherwise target a finance or computational-social-science venue.
