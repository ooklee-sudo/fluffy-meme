# Online Appendix to "Where to Look First: Heterogeneity, Position, and the Value of Targeted Verification of Language-Model Output"

## Online Appendix A. Proofs

**Proof of Lemma 1.** By conditional independence given (*x*, Θ), Var(*N*) = E[Var(*N* | Θ)] + Var(E[*N* | Θ]) = Σ E[*p~t~*(1 − *p~t~*)] + Var(Σ *p~t~*). Now E[*p~t~*(1 − *p~t~*)] = *p̄~t~* − E[*p~t~*²] = *p̄~t~*(1 − *p̄~t~*) − Var(*p~t~*), and Var(Σ *p~t~*) = Σ Var(*p~t~*) + Σ~s≠t~ Cov(*p~s~*, *p~t~*). Adding the two expressions cancels the variances. ∎

**Proof of Proposition 1.** With equal costs the objective is linear in **v**, so the optimal plan verifies the *B* units with the largest *q*. Since *h* is increasing, the ranking of *q* equals the ranking of *u*, so the verified set is {*u* ≥ threshold}. If *f* is quasi-convex, then for a fixed *a~d~* = β′*x~d~* the set {*t* : *f*(*t*) + *a~d~* ≥ *c*} is the complement of an interval, that is, an initial block together with a final block. The blocks widen as the threshold falls. ∎

**Proof of Proposition 2.** The sum of the *k* largest entries of a vector is the maximum, over all subsets of size *k*, of a linear function of the vector, and it is symmetric in its arguments; hence it is Schur-convex (Marshall et al. 2011). The term (*k*/*N*) Σ *q~i~* is constant for vectors with a common sum. If all entries are equal, the top-*k* sum equals (*k*/*N*) Σ *q~i~*. ∎

**Proof of Proposition 3.** Fix any posterior of *Z~d~*. The posterior predictive probability of unit *t* is E[σ(*f*(*t*) + β′*x~d~* + *Z~d~*) | data], which is increasing in *f*(*t*) + β′*x~d~* for every posterior because σ is increasing. The units of one document share the posterior and β′*x~d~*, so their order by posterior predictive probability is the order of *f*(*t*). With per-document budgets an adaptive policy therefore verifies the same units as a static one. Between documents the posterior means of *Z~d~* differ and can reverse the order of units, which is the only source of gain. ∎

**Proof of Proposition 4.** The cost is separable and linear in each *v~t~*, so the rule is a unit-by-unit comparison of δ *L q~t~* with *c*. For uniform verification of a fraction φ, the expected benefit is φ Σ *a~t~*, maximized at φ ∈ {0, 1}, giving (Σ *a~t~*)⁺. The identity Σ *a~t~*⁺ − (Σ *a~t~*)⁺ = Σ *a~t~*⁺ − (Σ *a~t~*⁺ − Σ *a~t~*⁻)⁺ = min(Σ *a~t~*⁺, Σ *a~t~*⁻) completes the proof. ∎

**Proof of Proposition 5.** *N*, *H*, and *S* are linear in *q*, with slopes 0, δ₂ *L*, and δ₁δ₂ *L* − *c₂*(δ₁ − *f*₁). The slope of *H* exceeds that of *S* by δ₂ *L*(1 − δ₁) + *c₂*(δ₁ − *f*₁) > 0, and the slope of *S* is positive when screening is ever useful. The upper envelope of three lines with ordered slopes consists of the lines in that order, and the middle line contributes if and only if it lies above the intersection of the outer two. That intersection is at *q~h~* = *c₂*/(δ₂ *L*), where *S*(*q~h~*) = *c₂* δ₁(1 − *q~h~*) − *c₂* *f*₁(1 − *q~h~*) − *c₁* = *c₂*(δ₁ − *f*₁)(1 − *q~h~*) − *c₁*. ∎


## Online Appendix B. Supplementary Evidence

**B.1 Validation of the language-model judges against human labels.** On the FActScore annotations (3,549 to 3,654 sentences, depending on the judge), pooled over the three systems:

| Judge, event | Cohen's κ [95% CI] | Sensitivity | Specificity | Precision | Judge rate / human rate |
|---|---|---:|---:|---:|---|
| Claude Haiku 5.5, any unsupported claim | 0.633 [0.60, 0.66] | 0.936 | 0.686 | 0.778 | 0.650 / 0.540 |
| Mistral Medium 3.5, any unsupported claim | 0.660 [0.63, 0.70] | 0.885 | 0.770 | 0.822 | 0.587 / 0.545 |
| Claude Haiku 5.5, contradicted claim | 0.270 [0.24, 0.30] | 0.345 | 0.940 | 0.871 | 0.214 / 0.540 |
| Mistral Medium 3.5, contradicted claim | 0.270 [0.24, 0.30] | 0.340 | 0.946 | 0.884 | 0.209 / 0.545 |

Agreement between the two judges on summaries was low (κ = 0.13, 4,475 sentences), so we draw no substantive conclusions about summarization from the judge-based data.

**B.2 Prefix-intervention experiment.** For 250 of the generated biographies (Gemma-3-27B) that contained a contradicted sentence among their first eight, we kept the text up to and including the first such sentence and asked the generator to continue it, either with the sentence unchanged or with the sentence rewritten by the judge to remove the contradicted claims. After excluding 18 pairs in which the rewriting did not remove the contradiction or the original sentence was no longer judged contradicted, 232 pairs remained. The share of continuation sentences containing a contradicted claim was 0.182 after the erroneous prefix and 0.198 after the corrected prefix (difference −0.017, 95% CI [−0.034, +0.001]). The experiment gave the generator a text to continue rather than its own output, and its labels are judge-based.


