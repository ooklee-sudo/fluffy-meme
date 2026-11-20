# AsPredicted 제출본 (영어, 항목별 복사·붙여넣기용)

> **제출 전 확인 (한국어 메모, 제출본에는 넣지 않는다)**
> 1. 시나리오 수치를 `quant_cost` 측정값으로 확정했고 설문(`survey_instrument.md`)을 **동결**했다. 동결 후에는 고치지 않는다.
> 2. 전문직 20명 사전 점검을 마쳤다. 점검 후 문항이 바뀌었다면 아래 본문이 바뀐 설문과 일치하는지 대조했다.
> 3. 아래 `[ ... ]`가 남아 있지 않다(날짜, 점검 결과 한 줄).
> 4. 사전 점검을 **하지 않고** 제출한다면 1번 항목 답을 "No."로만 바꾼다.
> 5. AsPredicted의 현재 입력 항목과 글자 수 제한은 제가 확인하지 못했다. 항목 이름이 조금 다르면 의미가 맞는 칸에 붙여 넣고, 제한을 넘으면 문장을 줄인다. 작성자 이메일 입력과 공저자 확인 절차는 사이트에서 직접 진행한다.
> 6. 투고 전까지 비공개로 둘 수 있는지는 제출 화면의 공개 옵션에서 확인한다.

---

## 1. Data collection. Have any data been collected for this study already?

No data relevant to the hypotheses have been collected. A pilot of 20 participants from the same panel was run only to test the survey (completion time, comprehension and attention-check failure rates, recruitment speed, technical errors). Pilot responses are not used in any hypothesis test and are not part of the final sample. [Pilot completed on YYYY-MM-DD. Survey changes made after the pilot: none / list.]

## 2. Hypothesis. What's the main question being asked or hypothesis being tested in this study?

Main question: Do professionals who decide between a cloud AI service (API) and building a local small language model weigh the option value of waiting (under uncertainty and an irreversible investment) as a real-options model prescribes, and does the way performance information is presented change their choices?

Normative benchmark. A firm can pay a one-time, irreversible cost F to build a local model whose savings have present value V that follows a geometric Brownian motion (volatility σ, drift 0, discount rate r = 8%). It should invest now only if V ≥ [β/(β−1)]·F, where β is the positive root of ½σ²β(β−1) − r = 0. With V/F fixed at 1.8: for σ = 0.10 the threshold ratio is 1.28, so building now is optimal; for σ = 0.50 it is 3.26, so waiting is optimal. The maximum cost F_max at which investing now is still optimal is V/1.28 = 0.78V at low volatility and V/3.26 = 0.31V at high volatility; the ratio is 0.394 (log difference = −0.93). Participants are not given σ, r, or this formula; the benchmark is a model-implied reference.

Confirmatory hypotheses:
- H1a. In high-volatility scenarios, the share of "build the local model now" choices exceeds 10% (the benchmark is 0%; 10% allows for noise and inattention).
- H1b. Increasing volatility lowers participants' F_max by less than the normative benchmark: the mean within-person difference in log F_max (high minus low volatility) is greater than −0.93.
- H3. Presenting accuracy alone, rather than accuracy plus cost per correct answer, lowers the probability of choosing "build the local model now".

Exploratory only (not tested confirmatorily): H2. Reading a (fictional) data-exposure incident report raises preference for the local model and the estimated probability of a vendor data exposure, with the estimated probability mediating the effect. We expect to be underpowered for H2.

## 3. Dependent variable. Describe the key dependent variable(s) specifying how they will be measured.

In each of four scenarios, a participant (a) chooses one of: build the local model now / wait 12 months and decide again / keep using the cloud API (DV1; the binary indicator "build now" is the primary choice variable); (b) states the highest one-time cost F_max they would still pay to build the local model now, on a slider from $0 to 1.2V (DV2; analysed as log F_max, with 0 replaced by $1); (c) states how many months they would prefer to wait before committing money, 0–24 (DV3, secondary).
Secondary measures: estimated 12-month probability of customer data exposure through an external AI vendor (0–100%, measured before the scenarios); perceived change in API prices and small-model performance (1–7, after each scenario). Covariates: job function, seniority, decision authority, budget authority, AI experience, numeracy, privacy concern, risk attitude.

## 4. Conditions. How many and which conditions will participants be assigned to?

Within-subject 2×2: volatility (low vs. high) × performance presentation (accuracy only vs. accuracy plus cost per correct answer). Each participant sees all four scenarios. Four business cases (customer inquiry classification, HR records, contract documents, insurance claims) are assigned to the four cells with a Latin square (four versions, equally likely); scenario order is randomized. All scenarios fix V/F = 1.8. Volatility is manipulated in text: low = prices and small-model performance "expected to stay very stable", analysts' forecasts "agree closely"; high = "could change a great deal, up or down", forecasts "disagree widely".
Between-subject (exploratory, H2): participants are randomly assigned (50:50) to read either a short fictional data-exposure incident report or a neutral report of equal length before the scenarios. A background annual exposure probability is stated identically to everyone.
All amounts are in USD and no country-specific rules are mentioned.

## 5. Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

- H1a: For each participant, compute the proportion of "build now" choices across the two high-volatility scenarios (0, 0.5, 1). Test whether the mean proportion exceeds 0.10 with a one-sided participant-level bootstrap (5,000 resamples, α = .05). Sensitivity analysis: exact binomial test of H0: p ≤ 0.10 on all high-volatility responses.
- H1b: For each participant, D = mean log F_max (two high-volatility scenarios) − mean log F_max (two low-volatility scenarios). One-sided one-sample t-test of H0: E[D] ≤ −0.93 (α = .05); bootstrap confidence interval as a robustness check.
- H3: Mixed-effects logistic regression: build-now indicator ~ performance presentation + volatility + scenario position + business case + (1 | participant). The performance-presentation coefficient is tested two-sided. A linear mixed model on log F_max with the same terms is a robustness check.
- Multiplicity: Holm correction across H1a, H1b and H3.
- Effect sizes with 95% confidence intervals are reported for all tests. Models are reported with and without covariates.
- Exploratory (H2): Welch t-test and logistic regression for group differences; mediation through estimated exposure probability by bootstrap (5,000). Interpreted as exploratory.

## 6. Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

Exclusions are applied automatically before looking at the dependent variables. A participant is not eligible (and is screened out before the scenarios) unless: current job function is one of the listed IT/data/security/procurement/finance/general-management categories; their role in technology or vendor decisions is "final decision", "my recommendation effectively decides", or "member of the deciding group"; at least one of (level ≥ manager, can approve ≥ USD 10k of technology budget alone, or final/decisive role) holds; they have taken part in at least a discussion about adopting an AI/LLM service in the past two years; and their organization has at least 10 employees.
Among eligible respondents we exclude those who: fail either of two attention checks; answer incorrectly at least 2 of the 4 scenario comprehension checks; give job function or level at the end that differs from the screening answers; finish in less than one third of the median completion time; or give identical F_max and identical choices in all four scenarios. F_max values are bounded by the slider, so no outlier trimming is applied. We report the number excluded by each rule.

## 7. Sample Size. How many observations will be collected or what will determine sample size?

Target: 90 analysable participants. We start by recruiting about 113 eligible-panel participants (assuming ~20% exclusions) and recruit additional batches until 90 participants pass all exclusion rules, with a hard cap of 140 recruited participants. No interim analyses of hypotheses are run and no data-dependent stopping is used. If the cap is reached with fewer than 90 analysable participants, we analyse those available and report the shortfall. Justification: a paired comparison with dz = 0.30, α = .05, power = .80 requires about 90 participants; we acknowledge lower power for smaller effects.

## 8. Anything else you would like to pre-register?

- Participants: professionals recruited through Prolific with employment/job-role filters where available; the screening items above are used to verify eligibility because filters are self-reported. No country filter is applied.
- Compensation: hourly-equivalent rate of about USD 20 (about 15 minutes). The study is approved by the Hanyang University IRB (HY-IRB-2026-11-033).
- The normative benchmark is model-implied under the stated assumptions (r = 8%, drift 0, V/F = 1.8) and under our mapping of the qualitative volatility descriptions to σ = 0.10 and σ = 0.50. Results for H1a and H1b are interpreted as deviations from this benchmark only to that extent; we also report whether volatility lowers F_max at all (D < 0).
- Scenario numbers (accuracy and cost of the local model and the API) come from our own measurements of quantized open models on a laptop GPU and a cloud API. Anonymized data, scenario text and analysis code will be shared.
- Limitations stated in advance: hypothetical stakes, self-reported job role, country-neutral scenarios, and limited power for exploratory analyses.
- Any deviation from this plan will be reported and labelled.

## 9. Name. Give a title for this AsPredicted pre-registration

Professionals' sourcing decisions between cloud AI services and local small language models: a behavioral real-options study
