import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
d = new_doc(spacing=1.3, running="Supplementary Information")
TITLE(d, "Supplementary Information", size=15)
P(d, "Detecting machine-written scholarly text depends on the generator and on what authors know", indent=False, align="center", italic=True, after=10, spacing=1.15)
P(d, "This document contains proofs of Propositions 1 to 7 and the supplementary tables. All table values are taken from the source manuscript. Items marked [authors to restore] could not be recovered from the PDF.", indent=False, size=10.5, after=8, spacing=1.2)

H1(d, "1. Proofs")
P(d, "**Setting.** A share π of documents are machine-written. The screen assigns each document a score *s* with likelihood ratio ℓ(*s*) = *f*_{M}(*s*)/*f*_{H}(*s*), nondecreasing in *s*; the posterior probability that a document with score *s* is machine-written is *p* = πℓ/(πℓ + 1 − π). A judged document is flagged with probability *J* if machine-written and *a* if human, independently of *s* given the class. Costs are *c*_{J} per judge call, *c*_{R} per flagged paper investigated (assumed to settle its status) and *L* per machine paper that is not flagged. Throughout, *L* > *c*_{R} and *J* > *a*.", indent=False, spacing=1.2)
P(d, "**Proposition 1 (when to call the judge).** Sending a document with posterior *p* to the judge reduces expected cost by *V*(*p*) = *p*[(*L* − *c*_{R})*J* + *c*_{R}*a*] − (*c*_{J} + *c*_{R}*a*). It is worth sending if and only if *p* ≥ τ = (*c*_{J} + *c*_{R}*a*)/((*L* − *c*_{R})*J* + *c*_{R}*a*), and if (*L* − *c*_{R})*J* ≤ *c*_{J} then τ ≥ 1 and the judge is never worth calling.", indent=False, spacing=1.2)
PROOF(d, "Not sending leaves expected cost *Lp*. Sending costs *c*_{J} + *c*_{R}(*pJ* + (1 − *p*)*a*) + *Lp*(1 − *J*): the judge fee, the investigation of flagged papers (machine papers flagged with probability *J*, human with probability *a*), and the loss from unflagged machine papers. The difference is *V*(*p*) = *Lp* − *c*_{J} − *c*_{R}(*pJ* + (1 − *p*)*a*) − *Lp*(1 − *J*) = *p*[*LJ* − *c*_{R}*J* + *c*_{R}*a*] − (*c*_{J} + *c*_{R}*a*), which is linear and increasing in *p*. Setting *V*(*p*) ≥ 0 gives *p* ≥ τ. If (*L* − *c*_{R})*J* ≤ *c*_{J}, then the numerator of τ is at least the denominator, so τ ≥ 1 and no posterior justifies the call. ∎")
P(d, "Since *p* = πℓ/(πℓ + 1 − π), the condition *p* ≥ τ is equivalent, for τ < 1, to ℓ(*s*) ≥ ℓ^{*} = ((1 − π)/π)·τ/(1 − τ).", indent=False, spacing=1.2)
P(d, "**Proposition 2 (depth).** The set of documents worth judging, {*s* : ℓ(*s*) ≥ ℓ^{*}}, expands as ℓ^{*} falls, and ℓ^{*} is decreasing in π. The cost-minimizing depth is nondecreasing in π, in *J* and in *L*, and nonincreasing in *c*_{J} and *c*_{R}.", indent=False, spacing=1.2)
PROOF(d, "Write τ = *N*/*D* with *N* = *c*_{J} + *c*_{R}*a* and *D* = (*L* − *c*_{R})*J* + *c*_{R}*a*. τ is increasing in *c*_{J} (*N* rises, *D* is unchanged). Because *L* > *c*_{R}, *D* is increasing in *J* and in *L*, so τ is decreasing in both. The derivative with respect to *c*_{R} is ∂τ/∂*c*_{R} = [*aD* − *N*(*a* − *J*)]/*D*² = [*aLJ* + *c*_{J}(*J* − *a*)]/*D*², which is positive when *J* > *a*; τ is therefore increasing in *c*_{R}. ℓ^{*} is increasing in τ and, for fixed τ, decreasing in π; and ℓ is nondecreasing in *s*, so the set {ℓ ≥ ℓ^{*}} grows when ℓ^{*} falls. A deeper cascade sends more documents to the judge, so depth is nondecreasing where τ falls or π rises. ∎")
P(d, "**Proposition 3 (blind spots).** τ rises as *J* falls, and the judge is never worth calling when *J* ≤ *c*_{J}/(*L* − *c*_{R}). If the screen cannot tell generators apart, the relevant detection rate for a stream that mixes generators with weights *w*_{g} is the weighted mean *J̄* = Σ_{g} *w*_{g}*J*_{g}, so a generator that the judge cannot detect lowers the judge's value for the whole stream.", indent=False, spacing=1.2)
PROOF(d, "∂τ/∂*J* = −*N*(*L* − *c*_{R})/*D*² < 0. The condition for τ ≥ 1 is shown in Proposition 1. If the screen is uninformative about the generator, the probability that a machine paper is flagged is, by the law of total probability, Σ_{g} *w*_{g}*J*_{g}; hence the model of Proposition 1 applies with *J* replaced by *J̄*, and *J̄* falls whenever any *J*_{g} falls. ∎")
P(d, "**Proposition 4 (precision at low base rates).** Among documents an unscreened judge flags, the machine-written share is π*J*/(π*J* + (1 − π)*a*). It is low when π is small, even for a small false-alarm rate. Screening before judging raises the base rate among judged documents, and therefore raises this share and reduces wasted investigations.", indent=False, spacing=1.2)
PROOF(d, "By Bayes' rule, Pr(machine | flagged) = π*J*/(π*J* + (1 − π)*a*), which is increasing in π and tends to 0 as π → 0 for any *a* > 0. Among documents with screen score above a threshold, the base rate is π′ = Pr(machine | score above threshold) ≥ π whenever ℓ is nondecreasing (a higher score cannot make a machine paper less likely). Substituting π′ for π raises the share. With *J* = 0.86 and *a* = 0.02 the share is about 23% at π = 1%, 77% at 10% and 93% at 30%. ∎")
P(d, "**Strategic evasion.** A machine-using author chooses effort *e* ∈ [0, 1] at cost (κ/2)*e*², which lowers the detection probability to *d*(*e*), with *d*(0) = *d*_{0} the rate against a non-adaptive author. The author gains *B* if the paper passes and loses *P* if it is detected, so *u*(*e*) = *B*(1 − *d*(*e*)) − *P d*(*e*) − (κ/2)*e*² = *B* − (*B* + *P*)*d*(*e*) − (κ/2)*e*². Maximizing *u* is equivalent to minimizing *m d*(*e*) + *e*²/2, with *m* = (*B* + *P*)/κ.", indent=False, spacing=1.2)
P(d, "**Proposition 5 (evasion rises with the stakes).** If *d* is differentiable, decreasing and convex, the optimal effort *e*^{*} satisfies *m*|*d*′(*e*^{*})| = *e*^{*}, or *e*^{*} = 1 at the corner. Effort is nondecreasing in *m* and in the steepness of *d*, so equilibrium detection *d*(*e*^{*}) falls as the stakes rise or evasion becomes cheaper.", indent=False, spacing=1.2)
PROOF(d, "The objective *m d*(*e*) + *e*²/2 has second derivative *m d*″(*e*) + 1 > 0 for convex *d*, so it is strictly convex and the first-order condition *m d*′(*e*) + *e* = 0 characterizes the interior optimum; the corner applies when the condition holds with *e* > 1. Differentiating the first-order condition, d*e*^{*}/d*m* = −*d*′(*e*^{*})/(*m d*″(*e*^{*}) + 1) ≥ 0 because *d*′ < 0. A steeper |*d*′| raises the left side *m*|*d*′| of the condition at every *e*, so the solution moves up. Since *d* is decreasing, *d*(*e*^{*}) is nonincreasing in *m*. ∎")
P(d, "**Proposition 6 (the detectability paradox).** If *d*(*e*) = *d*_{0}(1 − *e*), then *e*^{*} = min(1, *m d*_{0}) and *d*(*e*^{*}) = *d*_{0}(1 − *m d*_{0}) whenever *m d*_{0} ≤ 1. Equilibrium detection is maximized at *d*_{0} = 1/(2*m*), where it equals 1/(4*m*), and decreases in *d*_{0} beyond that point.", indent=False, spacing=1.2)
PROOF(d, "The first-order condition gives *e* = *m d*_{0}, which is interior when *m d*_{0} < 1. Substituting, *d*(*e*^{*}) = *d*_{0}(1 − *m d*_{0}). Its derivative in *d*_{0} is 1 − 2*m d*_{0}, which is positive below *d*_{0} = 1/(2*m*) and negative above, so the maximum is at 1/(2*m*), with value (1/(2*m*))(1/2) = 1/(4*m*). ∎")
P(d, "**Proposition 7 (robust design).** Consider two screens with detection curves *d*_{A}(*e*) and *d*_{B}(*e*), where *d*_{B} is flat in *e* because its features cannot be edited cheaply. Suppose *d*_{B}(0) < *d*_{A}(0) and that *d*_{A} falls steeply in the sense that *d*_{A}(1) < *d*_{B}(0). Then there is a threshold *m̂* such that the screen built on B has higher equilibrium detection for every *m* > *m̂*.", indent=False, spacing=1.2)
PROOF(d, "For the flat curve, *d*_{B}′ = 0, so the author's first-order condition gives *e*_{B}^{*} = 0 and equilibrium detection is *d*_{B}(0) for every *m*. For screen A, equilibrium detection *D*_{A}(*m*) = *d*_{A}(*e*_{A}^{*}(*m*)) equals *d*_{A}(0) at *m* = 0, is nonincreasing in *m* by Proposition 5, and converges to *d*_{A}(1) as *m* → ∞ (the optimal effort tends to the corner 1). Because *D*_{A}(0) > *d*_{B}(0) > *d*_{A}(1) and *D*_{A} is nonincreasing and continuous, *m̂* = inf{*m* : *D*_{A}(*m*) ≤ *d*_{B}(0)} exists and *D*_{A}(*m*) ≤ *d*_{B}(0) for all *m* ≥ *m̂*. ∎")
P(d, "*Note on Proposition 7.* The source manuscript states the condition as “*d*_{A} falls steeply”. We have made this precise as *d*_{A}(1) < *d*_{B}(0), which holds in the data (detection at full attack 0.08 for the full screen against 0.34 for the hard-to-edit screen). [Authors to confirm that this reading matches the intended statement.]", indent=False, size=10.5, spacing=1.2)

H1(d, "2. Supplementary tables")
TABLE(d, "**Supplementary Table 1 | Screens trained on human papers only.** AUC (95% bootstrap interval); scores are anomaly scores and test sets are held-out human papers (grouped by source paper) plus papers from the named generator. A Mahalanobis screen on the clustering features reaches 0.59, 0.49 and 0.65 on GPT-4o, Claude and Llama papers.",
 [["Method (human-only)", "Features", "GPT-4o", "Claude"],
  ["Mahalanobis (primary)", "Rates", "0.597 [0.55, 0.64]", "0.466 [0.42, 0.52]"],
  ["Mahalanobis (primary)", "Dispersion", "0.507 [0.46, 0.55]", "0.510 [0.45, 0.56]"],
  ["Mahalanobis (primary)", "Both", "0.563 [0.52, 0.60]", "0.462 [0.41, 0.52]"],
  ["One-class SVM", "Both", "0.610 [0.56, 0.65]", "0.475 [0.42, 0.53]"],
  ["Isolation forest", "Both", "0.473 [0.43, 0.52]", "0.468 [0.42, 0.52]"]],
 widths=[1.9, 1.2, 1.7, 1.7], size=9, note="The Llama column of this table is missing from the source PDF (clipped at the page edge) [authors to restore].")
TABLE(d, "**Supplementary Table 2 | Baseline versus scale-dependent clustering features, development data (exploratory).** Baseline values differ from Table 1 of the main text by at most 0.001 because of a small change in how counts are split at window boundaries.",
 [["Train → test", "Baseline AUC", "Clustering AUC", "Difference [95% CI]"],
  ["*Rates plus clustering features*", "", "", ""],
  ["GPT-4o → GPT-4o", "0.987", "0.991", "+0.004 [−0.000, +0.008]"],
  ["Claude → Claude", "0.914", "0.946", "+0.032 [+0.017, +0.050]"],
  ["GPT-4o → Claude", "0.729", "0.755", "+0.026 [+0.001, +0.052]"],
  ["Claude → GPT-4o", "0.809", "0.849", "+0.040 [+0.019, +0.062]"],
  ["*Clustering features only (no rates)*", "", "", ""],
  ["GPT-4o → GPT-4o", "0.856", "0.927", "+0.071 [+0.045, +0.096]"],
  ["Claude → Claude", "0.751", "0.794", "+0.043 [+0.004, +0.082]"],
  ["GPT-4o → Claude", "0.704", "0.730", "+0.026 [−0.017, +0.071]"],
  ["Claude → GPT-4o", "0.808", "0.858", "+0.050 [+0.021, +0.077]"]],
 widths=[2.4, 1.2, 1.3, 1.9], size=9)
TABLE(d, "**Supplementary Table 3 | Expected cost per 1,000 documents (US$)** for the equal-weight mixture of generators, with review at US$20 per flagged paper (assumed). *q*^{*} is the share of all documents sent to the judge at the cascade optimum.",
 [["Loss per miss", "Judge price", "Base rate", "Best *q*^{*}", "No screening", "Screen only", "Judge on all", "Cascade", "Saving vs judge-all"],
  ["US$100", "×1", "1%", "14%", "1,000", "973", "948", "594", "37%"],
  ["US$100", "×1", "10%", "41%", "10,000", "6,225", "5,652", "5,420", "4%"],
  ["US$100", "×1", "30%", "67%", "30,000", "12,647", "16,104", "15,955", "1%"],
  ["US$100", "×100", "1%", "5%", "1,000", "973", "2,671", "767", "71%"],
  ["US$100", "×100", "10%", "24%", "10,000", "6,225", "7,374", "6,051", "18%"],
  ["US$100", "×100", "30%", "56%", "30,000", "12,647", "17,826", "16,959", "5%"],
  ["US$500", "×1", "1%", "36%", "5,000", "3,465", "2,582", "2,284", "12%"],
  ["US$500", "×1", "10%", "59%", "50,000", "12,092", "21,986", "21,795", "1%"],
  ["US$500", "×100", "1%", "18%", "5,000", "3,465", "4,304", "2,713", "37%"],
  ["US$500", "×100", "10%", "45%", "50,000", "12,092", "23,708", "22,684", "4%"]],
 widths=[0.7, 0.6, 0.6, 0.6, 0.8, 0.8, 0.8, 0.7, 0.8], size=8.5)
TABLE(d, "**Supplementary Table 4 | Screen recall at several depths.** Share of machine papers sent to the judge, and sent and flagged, when the screen passes the stated share of human papers (empirical rates; no independence assumed).",
 [["Target", "5%: sent / flagged", "20%", "50%", "100%"],
  ["GPT-4o", "0.64 / 0.55", "0.98 / 0.85", "1.00 / 0.87", "1.00 / 0.87"],
  ["Claude", "0.17 / 0.00", "0.61 / 0.00", "0.86 / 0.00", "1.00 / 0.01"],
  ["Llama", "0.73 / 0.66", "0.87 / 0.80", "0.99 / 0.89", "1.00 / 0.89"],
  ["Mixture", "0.51 / 0.41", "0.82 / 0.55", "0.95 / 0.59", "1.00 / 0.59"]],
 widths=[1.2, 1.5, 1.3, 1.3, 1.3], size=9)
TABLE(d, "**Supplementary Table 5 | Simulated cascade with bootstrap pools in which machine papers are 10% of the pool.** Share of machine papers flagged when at most 5% of human papers are flagged (95% intervals over bootstrap pools).",
 [["Target", "Share judged (*q*)", "Judge cost per 1,000 docs", "Detected, judge only", "Detected, rank fusion"],
  ["GPT-4o", "20%", "US$3.5", "0.86 [0.73, 1.00]", "0.86 [0.73, 1.00]"],
  ["GPT-4o", "30%", "US$5.2", "0.95 [0.86, 1.00]", "0.96 [0.86, 1.00]"],
  ["GPT-4o", "50%", "US$8.7", "0.96 [0.86, 1.00]", "0.97 [0.91, 1.00]"],
  ["GPT-4o", "100%", "US$17.4", "0.95 [0.82, 1.00]", "0.97 [0.86, 1.00]"],
  ["Claude", "20%", "US$3.5", "0.38 [0.11, 0.59]", "0.38 [0.11, 0.59]"],
  ["Claude", "30%", "US$5.2", "0.36 [0.09, 0.59]", "0.36 [0.09, 0.59]"],
  ["Claude", "50%", "US$8.7", "0.19 [0.05, 0.50]", "0.35 [0.09, 0.59]"],
  ["Claude", "100%", "US$17.4", "0.12 [0.00, 0.32]", "0.37 [0.09, 0.59]"],
  ["Llama", "20%", "US$3.5", "0.82 [0.64, 0.95]", "0.82 [0.64, 0.95]"],
  ["Llama", "30%", "US$5.2", "0.89 [0.73, 1.00]", "0.89 [0.73, 1.00]"],
  ["Llama", "50%", "US$8.7", "0.97 [0.86, 1.00]", "0.95 [0.82, 1.00]"],
  ["Llama", "100%", "US$17.4", "0.96 [0.86, 1.00]", "0.93 [0.79, 1.00]"]],
 widths=[1.0, 1.1, 1.5, 1.7, 1.7], size=9,
 note="Sending 10% of documents detected 0.60, 0.30 and 0.66 for GPT-4o, Claude and Llama papers. With about one third of the pool machine-written, detection at a 30% share falls to 0.76 for GPT-4o papers and 0.78 for Llama papers, and about 50% must be judged to recover 0.92 to 0.95.")
TABLE(d, "**Supplementary Table 6 | Median dispersion index and percentage of documents rejecting the Poisson null toward over-dispersion (5% level), by source.** Index = variance / mean; 1 indicates Poisson behaviour.",
 [["Event", "Human: index (% over)", "GPT-4o", "Claude", "Llama"],
  ["Square brackets", "2.53 (48.8)", "1.33 (36.4)", "1.22 (22.0)", "2.00 (38.5)"],
  ["Parentheses", "2.22 (42.2)", "1.78 (28.6)", "2.21 (40.1)", "2.02 (39.6)"],
  ["Semicolons", "2.00 (36.2)", "1.00 (12.4)", "2.00 (36.0)", "2.00 (35.0)"],
  ["Nominalizations", "1.67 (27.4)", "0.76 (7.3)", "1.10 (15.1)", "1.27 (21.8)"],
  ["Quotation marks", "1.30 (24.4)", "3.00 (60.0)", "2.00 (37.7)", "3.00 (55.3)"],
  ["Passive constructions", "1.20 (18.8)", "2.51 (47.3)", "1.79 (37.5)", "2.02 (35.1)"],
  ["Discourse markers", "1.00 (6.2)", "1.11 (7.8)", "1.22 (4.6)", "1.11 (9.4)"]],
 widths=[1.7, 1.5, 1.3, 1.3, 1.3], size=9)
TABLE(d, "**Supplementary Table 7 | Mean event count per 500-token window, by source.**",
 [["Event", "Human", "GPT-4o", "Claude", "Llama"],
  ["Parentheses", "9.80", "7.39", "11.39", "14.66"],
  ["Square brackets", "4.46", "0.21", "0.41", "0.17"],
  ["Semicolons", "1.95", "0.51", "3.54", "1.17"],
  ["Quotation marks", "0.95", "0.53", "1.23", "0.55"],
  ["Discourse markers", "1.84", "2.38", "1.08", "2.12"],
  ["Passive constructions", "8.08", "6.18", "8.61", "6.51"],
  ["Nominalizations", "24.43", "34.08", "27.34", "26.67"]],
 widths=[2.0, 1.1, 1.1, 1.1, 1.1], size=9)
TABLE(d, "**Supplementary Table 8 | Detection by feature set under no attack and full attack, mixture of generators.**",
 [["Feature set", "e = 0: AUC / detected", "e = 1: AUC / detected"],
  ["Passive and nominalization only", "0.780 / 0.34", "0.779 / 0.33"],
  ["Five edited events only", "0.849 / 0.35", "0.491 / 0.00"],
  ["All seven events", "0.889 / 0.53", "0.664 / 0.08"]],
 widths=[2.8, 1.9, 1.9], size=9)
TABLE(d, "**Supplementary Table 9 | Equilibrium evasion effort and the detection rate that remains** (share detected at a 5% false-positive rate), by the ratio of the stakes to the cost of evasion *m* = (*B* + *P*)/κ.",
 [["*m*", "Full screen: *e*^{*}", "Full screen: detection", "Hard-to-edit only: *e*^{*}", "Hard-to-edit only: detection"],
  ["0.10", "0.11", "0.41", "0.00", "0.34"],
  ["0.25", "0.25", "0.25", "0.01", "0.34"],
  ["0.50", "0.25", "0.25", "0.02", "0.34"],
  ["1.00", "0.41", "0.19", "0.04", "0.34"],
  ["2.00", "0.50", "0.15", "0.08", "0.34"],
  ["4.00", "0.75", "0.10", "0.16", "0.33"]],
 widths=[0.8, 1.3, 1.5, 1.6, 1.7], size=9, note="The full screen's equilibrium detection falls below that of the hard-to-edit screen at *m* ≈ 0.16 (Proposition 7).")
TABLE(d, "**Supplementary Table 10 | Effect of a generic LLM rewrite on detection by the clustering screen.** AUC / share of machine papers detected at a 5% false-positive rate, on the same papers before and after the rewrite. The last two columns exclude Llama, the attacker, from training; for Llama papers the two protocols are identical.",
 [["Target", "Original", "Rewritten", "Original (Llama excluded)", "Rewritten (Llama excluded)"],
  ["GPT-4o", "0.950 / 0.71", "0.924 / 0.54", "0.830 / 0.20", "0.813 / 0.11"],
  ["Claude", "0.773 / 0.22", "0.884 / 0.42", "0.750 / 0.21", "0.905 / 0.51"],
  ["Llama", "0.932 / 0.70", "0.935 / 0.63", "0.932 / 0.70", "0.935 / 0.63"],
  ["Mixture", "0.885 / 0.54", "0.914 / 0.53", "0.837 / 0.37", "0.884 / 0.42"]],
 widths=[1.0, 1.4, 1.4, 1.6, 1.6], size=9)
TABLE(d, "**Supplementary Table 11 | Mean event count per 500-token window before and after the LLM rewrite** (original → rewritten).",
 [["Event", "Human", "GPT-4o", "Claude", "Llama"],
  ["Parentheses", "9.80", "7.33 → 5.00", "11.38 → 5.72", "14.79 → 7.38"],
  ["Square brackets", "4.46", "0.23 → 0.06", "0.50 → 0.15", "0.12 → 0.02"],
  ["Semicolons", "1.95", "0.53 → 0.18", "3.54 → 1.53", "1.26 → 0.56"],
  ["Passive constructions", "8.08", "6.31 → 5.38", "8.71 → 6.76", "6.47 → 5.57"]],
 widths=[1.9, 1.0, 1.5, 1.5, 1.5], size=9)
TABLE(d, "**Supplementary Table 12 | Hybrid attack on the same 300 machine papers, with Llama (the rewriter) excluded from the screen's training.** AUC / share detected at a 5% false-positive rate.",
 [["Condition", "GPT-4o", "Claude", "Llama", "Mixture"],
  ["Original (no attack)", "0.830 / 0.20", "0.750 / 0.21", "0.932 / 0.70", "0.837 / 0.37"],
  ["Rewrite only", "0.813 / 0.11", "0.905 / 0.51", "0.935 / 0.63", "0.884 / 0.42"],
  ["Feature-aware edit only (e = 1)", "0.804 / 0.13", "0.495 / 0.03", "0.727 / 0.13", "0.675 / 0.10"],
  ["Rewrite, then edit (e = 0.5)", "0.770 / 0.10", "0.674 / 0.09", "0.782 / 0.21", "0.742 / 0.13"],
  ["Rewrite, then edit (e = 1)", "0.800 / 0.10", "0.541 / 0.03", "0.723 / 0.13", "0.688 / 0.09"]],
 widths=[2.2, 1.1, 1.1, 1.1, 1.1], size=9,
 note="Under the standard protocol the mixture results are 0.885 / 0.54 (original), 0.914 / 0.53 (rewrite only), 0.664 / 0.09 (edit only), 0.742 / 0.12 (hybrid at e = 0.5) and 0.681 / 0.07 (hybrid at e = 1).")
TABLE(d, "**Supplementary Table 13 | The screen, the Gemini judge and their rank-average fusion before and after the attacks.** AUC / share of machine papers detected at a 5% false-positive rate. The screen is trained without the target generator and without Llama, so its original-text values differ from those in the main text.",
 [["Target", "Condition", "Screen", "Gemini judge", "Fusion"],
  ["GPT-4o", "Original", "0.817 / 0.12", "0.972 / 0.87", "0.966 / 0.82"],
  ["GPT-4o", "Edit only", "0.791 / 0.08", "0.980 / 0.85", "0.962 / 0.82"],
  ["GPT-4o", "Hybrid attack", "0.790 / 0.07", "0.975 / 0.87", "0.958 / 0.77"],
  ["Claude", "Original", "0.746 / 0.22", "0.656 / 0.01", "0.774 / 0.35"],
  ["Claude", "Edit only", "0.493 / 0.03", "0.734 / 0.05", "0.664 / 0.11"],
  ["Claude", "Hybrid attack", "0.536 / 0.03", "0.840 / 0.35", "0.760 / 0.26"],
  ["Llama", "Original", "0.929 / 0.73", "0.974 / 0.89", "0.989 / 0.96"],
  ["Llama", "Edit only", "0.721 / 0.15", "0.986 / 0.95", "0.943 / 0.66"],
  ["Llama", "Hybrid attack", "0.724 / 0.15", "0.985 / 0.90", "0.937 / 0.65"]],
 widths=[1.0, 1.4, 1.4, 1.5, 1.4], size=9)
TABLE(d, "**Supplementary Table 14 | Cascade before and after the hybrid attack.** Share of machine papers detected when at most 5% of human papers are flagged, in pools with 10% machine papers (95% intervals over bootstrap pools). The screen is trained without the target generator and without Llama.",
 [["Target", "Share judged (*q*)", "Original", "Hybrid attack"],
  ["GPT-4o", "30%", "0.76 [0.59, 0.91]", "0.70 [0.48, 0.91]"],
  ["GPT-4o", "50%", "0.90 [0.73, 1.00]", "0.89 [0.73, 1.00]"],
  ["GPT-4o", "100%", "0.93 [0.77, 1.00]", "0.93 [0.77, 1.00]"],
  ["Claude", "30%", "0.30 [0.05, 0.55]", "0.20 [0.05, 0.36]"],
  ["Claude", "50%", "0.12 [0.00, 0.34]", "0.31 [0.09, 0.52]"],
  ["Claude", "100%", "0.11 [0.00, 0.27]", "0.41 [0.18, 0.64]"],
  ["Llama", "30%", "0.88 [0.73, 1.00]", "0.54 [0.32, 0.73]"],
  ["Llama", "50%", "0.96 [0.86, 1.00]", "0.78 [0.59, 0.91]"],
  ["Llama", "100%", "0.96 [0.86, 1.00]", "0.94 [0.82, 1.00]"]],
 widths=[1.0, 1.4, 2.0, 2.0], size=9)
H1(d, "3. Cost of the screens and of generation")
P(d, "Computing all events and the baseline indices took 4 to 6 milliseconds per document on one CPU core (roughly 160 to 230 documents per second, depending on machine load), with no external service calls. The judges cost about US$0.0073 and 1.7 seconds per excerpt for GPT-4o (US$3.63 for 500 excerpts) and about US$0.0174 and 23.4 seconds per excerpt for Gemini 2.5 Pro (US$8.68), including its reasoning tokens. Screening 1,000 documents would thus cost about US$7 and half an hour of sequential calls with GPT-4o, and about US$17 and more than six hours with Gemini. Producing one machine paper in four requests cost about US$0.04 for GPT-4o, US$0.13 for Claude and US$0.002 for Llama through the gateway we used.", indent=False, spacing=1.2)
d.save("NMI_Screening_Supplementary_Information.docx"); print("saved")
