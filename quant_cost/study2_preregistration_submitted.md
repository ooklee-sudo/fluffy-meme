# Study 2: AsPredicted 제출본 (실제 제출한 짧은 문안)

> **등록 정보: AsPredicted #326168, 2026-11-20 09:29(PT)에 등록. 본 수집 시작(2026-11-21 09:35 UTC)보다 앞섬. 주소 https://aspredicted.org/ak3v2a.pdf (익명 페이지이지만 항목 8에 소속과 IRB 번호가 있음).**
> 이 파일이 AsPredicted에 제출·승인된 문안이다. 긴 설명판은 `study2_preregistration_aspredicted.md`에 있고, 둘이 다르면 **이 파일이 기준**이다. 제출 후 설문·수치·제외 규칙을 바꾸지 않는다.

## 1. Data collection

It's complicated (사전 점검 10명 응답이 있음; 설명은 항목 8).

## 2. Hypothesis

Main question: Do vivid privacy-incident information and the format of AI performance presentation distort professionals' choice between a cloud AI service (API) and a local small language model, although neither changes the normatively relevant numbers?

Normative benchmark (risk-neutral, stated in the instructions): the local model's yearly net advantage is (B − E) + λL, and the normative willingness to pay (WTP) to eliminate the API's exposure risk is λL. With B = 100m, E = 180m, L = 2,000m (USD thousands, m = 0.6 to 1.2), the API is optimal at λ = 2% and the local model at λ = 6%, so normative ln(WTP/L) rises by ln 3 from 2% to 6%. Neither manipulation changes these numbers.

H2c (primary): Participants who read a fictional data-exposure incident report are less sensitive to the stated exposure probability than those who read a neutral news item: S = mean ln(WTP/L) at λ = 6% minus at λ = 2% is smaller in the incident group.

Secondary (Holm, family of two): H2a, the incident group has a higher mean ln(WTP/L). H3a, presenting accuracy alone (rather than accuracy plus cost per correct answer) lowers the probability of choosing the local model.

Planned mediation, not confirmatory: H2b, H3b. Exploratory: H5 (policy strictness and personal discretion moderate the incident effects), H2d, other moderators.

## 3. Dependent variable

In each of four scenarios: (1) choice of the local model vs. the API (binary); (2) WTP, the yearly amount the participant would pay to eliminate the API's exposure risk, entered in USD thousands between 0 and L/4 (higher entries set to L/4 and flagged), analysed as ln(WTP/L), with 0 replaced by 0.001 L. Derived: S per participant.
Measured after choice and WTP: own estimate of the yearly exposure probability (0–100%), perceived quality disadvantage of the local model (1–7), a comprehension check. Covariates: job function, seniority, decision and budget authority, AI experience, numeracy, privacy concern, risk attitude, industry, trade-secret value, discretion, ranking of sourcing factors, and organizational policy on external AI services (S8, asked before randomization).

## 4. Conditions

Mixed design. Between subjects: random assignment (50:50) to a fictional data-exposure incident report or a neutral news item of equal length, read before the scenarios. Within subjects, 2 × 2: stated yearly exposure probability (2% vs. 6%) × performance presentation (accuracy only vs. accuracy plus cost per correct answer). Every participant sees all four scenarios. Four business cases are assigned to the four cells by a Latin square (four versions); scenario order is randomized.

## 5. Analyses

H2c (primary, α = .05, two-sided): Welch t-test of S between groups, with Cohen's d and 95% CI. Robustness: linear mixed model of ln(WTP/L) on incident, λ level, their interaction, format, position, case, and a participant random intercept.
H2a and H3a (Holm, α = .05): H2a, Welch t-test of each participant's mean ln(WTP/L). H3a, mixed-effects logistic regression: local choice ~ format + λ level + incident + position + case + (1 | participant); the format coefficient is tested.
H2b, H3b: participant-level percentile bootstrap mediation (5,000 resamples), reported with 95% CIs, not interpreted confirmatorily. Manipulation checks are reported separately.
H5 (exploratory): linear models of S and of mean ln(WTP/L) on incident, policy strictness (S8 = 3 or 4 coded 0, 2 coded 1, 1 coded 2; "not sure" omitted) and their interaction; the same with discretion. Respondents with S8 = 1 are included in all analyses and also described separately. Exploratory analyses are labelled; models are reported with and without covariates.

## 6. Outliers and Exclusions

Eligibility (screened out before the scenarios): job function in IT, data, security, procurement, finance or general management; final, decisive, or deciding-group role in technology decisions; at least one of level ≥ manager, USD 10k budget authority, or final role; took part in a discussion about adopting an AI service in the past two years; organization of at least 10 employees. Policy and industry are not criteria: respondents whose organization prohibits external AI services entirely (S8 = 1), and those in defense or government, are retained in all analyses (a sensitivity analysis excluding S8 = 1 is reported).
Among eligible respondents we exclude those who: fail either of two attention checks; answer at least 2 of 4 comprehension checks incorrectly; end with a job function in a different group from screening (IT, data and security count as one group) or a different level; finish in under one third of the median time; or give identical WTP and choices in all four scenarios. WTP above L/4 is set to L/4. No other trimming. We report the number excluded by each rule.

## 7. Sample Size

Target: 200 analysable participants (about 100 per group). We recruit about 250 in batches and continue until 200 pass all exclusion rules, with a hard cap of 300 recruited. No interim hypothesis tests and no outcome-based stopping. If the cap is reached with fewer than 200 analysable participants, we analyse those available and report the shortfall. Power is .80 for d = 0.40 (H2c).

## 8. Other

Pilot (Question 1): 10 participants from the same panel were run in November 2026 only to test the survey; pilot data are not used in any hypothesis test or in the final sample. Changes after the pilot: stated duration from 19 to 22 minutes; consistency-check rule relaxed (IT, data and security as one group). No scenario, number or measure changed. A WTP fallback rule fixed before the pilot (30% or more identical WTP, or 2+ comprehension failures, would make S_choice = P(local | 6%) − P(local | 2%) primary) was not triggered.
Participants: professionals via Prolific with job-role filters where available; no country filter. Compensation: GBP 19.70/hour (about GBP 7.2 for 22 minutes). IRB: Hanyang University, HY-IRB-2026-11-033.
Scenario figures: accuracy and cost per correct answer come from our own measurements of quantized open models on a laptop GPU and a cloud API; B, E, L are fixed design values; the local cost is levelized (USD 1,500 hardware over 3 years at 50% utilization, USD 0.12/kWh). Marginal-cost and break-even analyses go in the appendix.
Limitations: hypothetical stakes, self-reported job role, few organizations under the strictest security rules, limited power for exploratory analyses. Deviations will be reported.

## 9. Name

Incident news and AI sourcing choices

## 10. Type of study

Survey

## 11. Data source

Prolific
