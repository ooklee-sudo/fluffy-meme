# EMSE 투고용 수정 초안 (ISRE-2026-4563 기반)

모든 수치는 원고에 있는 값만 사용했습니다. 새 분석이 필요한 곳은 `[TODO]`로 표시했습니다.

---

## 0. 프레이밍 전환 (먼저 결정할 것)

| ISR 원고 | EMSE 원고 |
|---|---|
| "신호이론 + state/time-dependent 이론 검증" | "LLM 툴링 생태계의 릴리스 행동에 대한 실증 연구" |
| 기여 = 이론 연결 | 기여 = (1) 업스트림 모델 출시 후 며칠 내 릴리스 반응, (2) 효과 크기 상한 (bounded null), (3) 측정·식별 방법 (burst 보정, 일 단위 placebo 설계), (4) replication package |
| Limitations 절 | **Threats to Validity** (construct / internal / external / conclusion) |
| Section 2.1–2.2 (가격 경제학, 교체 모델) | 짧게 줄이고 모델은 "동기" 정도로. 관련 연구는 MSR의 release engineering, rapid release, ML 시스템 유지보수 중심으로 보강 |

---

## 1. Abstract 재작성안

> Release frequency is widely read as a sign that open-source AI tooling is actively maintained, yet it is unclear what actually triggers a release. We study 19 widely used open-source repositories in the LLM tooling ecosystem (inference engines, training libraries, client SDKs, agent frameworks, and evaluation tools; 3,432 repository-weeks, 2,456 releases) together with 38 upstream model launches. **Releases respond to upstream model launches within days:** repositories exposed to a launch release 3.4 days sooner than unexposed repositories (placebo-based p = 0.018), and 17.5 percentage points more of them release within one day (p = 0.008); the effect persists for regular releases once controls exposed to other launches are dropped (4.6 days, p = 0.002). Release notes mention the launched model in 42.8% of exposed repository-launch pairs, which suggests that part of the response is support for the new model. Releases also follow the volume of user issues (0.26 log-odds per SD of bug reports, wild cluster bootstrap p = 0.01) and tend to follow the stock of merged changes. **We find no evidence that release timing tracks accumulating defects, and our intervals bound how large such a link can be:** the pooled slope of bug reports on release age is −0.003 per week (95% CI −0.015 to 0.010) and is equivalent to zero within ±2% per week (TOST p = 0.004). With the post-release burst of attention absorbed, an accumulation of up to about 3.9% per week cannot be excluded. The additional response to bug reports at a given issue volume is positive but not significant (0.19 log-odds per SD; CI −0.05 to 0.43). Release cadence therefore carries information about responsiveness to users, upstream changes, and accumulated work, but public repository data do not let us read it as responsiveness to degradation. We discuss implications for dependency-health metrics and for monitoring practice, and release the weekly panel and analysis scripts.

수정 이유:
- 양성 발견을 첫 번째로 올리고, null은 "효과 크기 상한"으로 썼습니다.
- 일 단위 결과가 사후에 정한 통계량이라는 점은 본문 4.4와 Threats에서 밝혀야 합니다 (6절 참고).

---

## 2. Introduction의 contribution 문단 교체안

원고의 "The paper makes four contributions" 문단을 아래로 바꿉니다.

> This paper makes four contributions.
> **(1) Release response to upstream model launches.** Using 38 model launches (22 open-weights, 16 API) and 277 repository-launch pairs, we show that exposed repositories release 3.4 days sooner than unexposed ones, against 0.9 days at placebo dates (p = 0.018). A weekly indicator misses this response (−0.002, SE 0.018) because the weekly release rate in treated blocks is already about 0.42 and client SDKs often release on the day a model is announced. This is a methodological finding as well: weekly panels, the default in repository-mining studies, are too coarse for event-driven maintenance.
> **(2) Bounded evidence on defect-driven release timing.** Rather than reporting non-significance, we report how large an effect the data can exclude. Bug reports do not rise with release age by more than about 1% per week relative to total issues (specification (b), TOST p = 0.004 for ±2%), and the response of releases to bug reports beyond overall issue volume is positive but imprecise (0.19 log-odds per SD; CI −0.05 to 0.43). We show which specifications are biased toward zero by the post-release burst of issue filing, using synthetic panels with a planted effect.
> **(3) Release timing tracks user activity and accumulated work.** The release hazard rises with the volume of user issues and tends to rise with the stock of merged pull requests (work age 0.182, 95% CI 0.029 to 0.335 when entered jointly with calendar age), though the two ages are correlated (0.74) and the wild cluster bootstrap does not reject at 5%.
> **(4) Practical implications.** Release frequency, as used in CHAOSS, Snyk, and OpenSSF Scorecard, reflects responsiveness to users and to upstream changes, and cannot be read as evidence that defects are being managed. A replication package with weekly aggregates and scripts accompanies the paper.

---

## 3. 저장소 선정 기준과 일반화 한계 (Section 4.1 + Threats)

### 3.1 Section 4.1 "Repository Selection" 교체안

> **Sampling frame and procedure.** We target open-source projects in the LLM tooling layer, meaning software that sits between users and models (inference engines, training and fine-tuning libraries, client SDKs, agent frameworks, evaluation tools) and whose releases are human-made decisions. We selected repositories in three steps, all fixed before collecting issue or release histories for the repositories in steps 2 and 3.
>
> *Step 1: seed candidates.* We tried six prominent projects. Qwen2.5 and DeepSeek-V3 were excluded because they publish weights elsewhere and have few or no GitHub releases; llama.cpp was excluded because it publishes automated builds with no timing decision. vLLM, Hugging Face Transformers, and Ollama were retained.
> *Step 2: pre-specified list.* To avoid relying on three seeds, we fixed a list of 17 further repositories before collecting data on them. The authors chose them from general knowledge of the field, without looking at their issue or release histories.
> *Step 3: eligibility rule.* We required at least 10 non-draft, non-prerelease releases and at least 80 weeks of data since 1 January 2023. One of the 20 collected repositories (mlc-llm) failed this rule, leaving 19.
>
> **What the sample is.** A convenience sample of prominent projects, not a random draw from the ecosystem. Table 1 gives per-repository weeks, releases, and median release cycle. [TODO: add columns for primary language, GitHub stars at collection date, owner type (company-backed / community), and category (inference engine, training library, client SDK, agent framework, evaluation tool) to Table 1.] Seven repositories release at a median cycle of one week, and two of them (anthropic-sdk-python, openai-python) may rely on automated release pipelines. We retain them and report results without them (Section 5.6).
>
> **How the rule shapes the sample.** The eligibility rule keeps projects that release often enough to have a release hazard, so slowly releasing or inactive projects are excluded by construction. Our results describe *actively releasing, prominent* tooling projects.

### 3.2 Threats to Validity — External validity 교체안

> **External validity.** Our 19 repositories are prominent, actively releasing, GitHub-hosted tooling projects selected by the authors' judgment under pre-specified rules. Four limits follow.
> (i) *Not a random sample.* We cannot estimate how typical these projects are of the ecosystem, and the pooled intervals describe variation across these 19 repositories, not a population of repositories. Heterogeneity is real: repository-level bug-rate slopes range from −0.231 (semantic-kernel) to 0.067 (Ollama), and the pooled between-repository variance is τ² = 0.0003.
> (ii) *Conditioning on release frequency.* The eligibility rule (at least 10 releases, 80 weeks) excludes slow or inactive projects, where release timing is more likely to be irregular.
> (iii) *Tooling, not models.* Repositories are software around models; we observe no model weights, and a release is a proxy for a refresh. We make no claim about how commercial operators maintain hosted models.
> (iv) *Platform and period.* All data come from GitHub, from January 2023 to October 2026, a period of rapid change in the field. Projects that track issues elsewhere, or that were created after 2023, are under-represented.
> Results should be read as evidence about this layer of the ecosystem. Whether they hold for other open-source domains, for smaller projects, or for hosted models is an empirical question we leave to replication, and the replication package is designed to make this easy.

---

## 4. Null result의 검정력 / 효과 크기 상한 (Section 4.x + 5.x 교체안)

### 4.1 방법 절 (Equivalence and power)

> **Reporting null results.** Several of our hypotheses predict an effect that the data may not show. For each, we do not interpret p > 0.05 as absence of an effect. We report (a) the 95% confidence interval, which gives the largest effect compatible with the data; (b) a two one-sided test (TOST) against a smallest effect size of interest (SESOI); (c) the smallest equivalence bound at which equivalence holds at the 5% level (|estimate| + 1.645 SE); and (d) the minimum detectable effect (MDE) at 80% power (2.8 SE). SESOIs are: a 2% weekly increase in the bug rate (RQ1); 0.25 log-odds per SD of bug reports, about the size of the response to non-bug issues that the data detect (0.23) (RQ3); and 5 percentage points for upstream launches, about one eighth of the pre-launch release rate. Because these bounds are anchored to the data, we also report (c), so readers can apply their own.

### 4.2 결과 요약 표 (Table 새로 추가 권장)

| Test | Estimate (SE) | 95% CI | SESOI | TOST p | Smallest equivalence bound | MDE (80% power) | Reading |
|---|---|---|---|---|---|---|---|
| RQ1 bug-rate age slope, spec (b) | −0.003 (0.006) | −0.015, 0.010 | ±0.02 | 0.004 | 0.013 | 0.018 | **Equivalent to zero**; rises above ~1%/week excluded |
| RQ1 bug-rate age slope, spec (d) | 0.017 (0.010) | −0.003, 0.038 | ±0.02 | 0.40 | 0.035 | 0.029 | **Inconclusive**; up to ~3.9%/week not excluded |
| RQ3 weekly launch event study | −0.002 (0.018) | −0.037, 0.033 | ±0.05 | 0.004 | 0.032 | 0.050 | **Equivalent to zero at weekly resolution** |
| RQ3 bug reports, total issues fixed | 0.191 (0.123) | −0.05, 0.43 | ±0.25 | 0.32 | 0.39 | n/a | **Inconclusive**; positive extra response possible |
| RQ3 bug reports, non-bug issues fixed | 0.261 (0.095) | n/a | ±0.25 | 0.55 | 0.42 | n/a | Positive, significant (wild cluster p = 0.01) |
| RQ4 receivers: adoption vs cadence (downloads / stars) | −0.008 / 0.047 | n/a | n/a | n/a | n/a | 0.09 / 0.07 | Modest star response not excluded |

표는 원고 5.6, 5.7절의 값으로 채웠습니다. `n/a`는 원고에서 해당 값을 못 찾은 칸입니다. 투고 전에 원고 값과 대조해서 채워 넣으세요.

### 4.3 결과 절 문장 교체 예시

원고 5.1의 "H1 is therefore not supported at conventional levels"를 아래로 바꿉니다.

> The data bound the accumulation of bug reports with release age from above. Under specification (b), the pooled slope is −0.003 per week (95% CI −0.015 to 0.010), statistically equivalent to zero within ±0.02 log points per week (TOST p = 0.004), and the smallest bound at which equivalence holds is 0.013. This specification is biased toward zero if errors rise, but synthetic panels with a planted rise show that the bias is not large enough to hide it. Under specification (d), which absorbs the post-release burst with age indicators, the estimate is 0.017 (95% CI −0.003 to 0.038), and equivalence within ±0.02 is not established (TOST p = 0.40; smallest bound 0.035). We therefore conclude that **any weekly accumulation of bug reports with release age is small: at most about 1% per week under (b) and at most about 3.9% under (d)**. We cannot say it is zero.

원고 5.3의 RQ3 결론 문장 교체안:

> The additional response of releases to bug reports, over and above overall issue volume, is positive but imprecise (0.191 log-odds per SD; 95% CI −0.05 to 0.43; wild cluster bootstrap p = 0.20). The interval is compatible with no additional response and with an increase in the odds of a release of up to about 54% per SD. Equivalence within ±0.25 is not established (TOST p = 0.32). Our data therefore do not identify a defect-specific response, and do not exclude one.

### 4.4 검정력 관련으로 보완하면 좋은 것 `[TODO]`

1. 19개 클러스터에서 wild cluster bootstrap의 검정력은 낮습니다. 원고의 합성 패널(planted effect)을 재활용해서 "γ를 x%로 심었을 때 몇 %를 복구했는가"를 표나 그림으로 추가하세요. 이미 코드가 있습니다.
2. 위 표를 Figure 2처럼 forest plot으로 그리면 한눈에 읽힙니다 (equivalence band ±SESOI 음영).

---

## 5. 양성 발견(업스트림 출시 후 릴리스 반응)을 전면에 두는 구조

EMSE용 RQ 재배열 제안:

| 새 RQ | 내용 | 원고 대응 |
|---|---|---|
| **RQ1** | 업스트림 모델 출시 후 릴리스가 앞당겨지는가? | 5.4 (일 단위) |
| RQ2 | 릴리스 노트는 새 모델 지원을 언급하는가? (대응의 성격) | 5.4 release notes (143/334 pairs = 42.8%; 287 of 1,901 vs 26 of 1,871) |
| RQ3 | 릴리스가 사용자 이슈 / 누적 작업에 반응하는가? | 5.3, 5.5 |
| RQ4 | 릴리스 타이밍이 결함 누적과 연결되는가? (bounded null) | 5.1, 5.2, 5.3 |

양성 발견 절의 문장:

> Exposed repositories release a restricted mean of 3.4 days earlier than unexposed repositories (placebo mean 0.9 days; placebo 95% range −3.0 to 1.2; randomization p = 0.018), and 17.5 percentage points more of them release within one day (placebo 4.8 points; p = 0.008). The response is concentrated in the first days (Figure 4). It is larger when controls exposed to another launch within the window are dropped (5.9 days, p = 0.001) and remains for regular releases once those controls are dropped (4.6 days, p = 0.002). Release notes support the interpretation that part of this response is support for the new model: 143 of 334 exposed repository-launch pairs (42.8%) have a release within eight weeks that mentions the launched model, and the median delay is 10 days.

### 이 부분에서 꼭 정직하게 써야 하는 약점 (리뷰어가 100% 짚습니다)

원고 스스로 인정한 것들이고, EMSE 리뷰어는 이걸 가장 먼저 봅니다.

1. **primary statistic을 추정치를 본 뒤에 정했습니다.** 그래서 이 분석은 *exploratory*로 표시해야 합니다. 해결책 `[TODO]`: 2026-10 이후 새로 나오는 업스트림 출시를 holdout으로 두고 같은 통계량을 사전 등록(OSF 등)해서 확인하는 분석을 추가하면, 이 약점이 가장 크게 줄어듭니다.
2. **핫픽스를 제외하면 primary statistic이 유의하지 않습니다** (2.2일, p = 0.10). 다른 오염된 control을 함께 제거해야 유의해집니다 (4.6일, p = 0.002). 이 의존성은 본문에서 숨기지 말고 한 표로 보여주세요: {all / drop contaminated controls / regular only / regular + drop controls} × {mean days, within 1 day}.
3. **exposure 코딩이 판단에 의존합니다** (11개 레포가 open-weights에, 6/6/5개가 OpenAI/Anthropic/Google API에 노출). `[TODO]`: 코딩 기준을 표로 공개하고 서로 다른 코더 두 명이 독립 코딩해서 Cohen's κ를 보고하세요.
4. **release notes 키워드 매칭은 수동 검증이 없습니다.** `[TODO]`: 무작위 50–100건 수동 검증으로 precision을 보고하세요 (원고는 12건만 확인했고 그마저 fix 분류입니다).
5. open-weights 쪽에는 pre-trend가 있을 수 있습니다 (joint Wald p = 0.07). 일 단위 placebo 설계가 baseline 차이는 흡수하지만 "노출 레포가 어떤 발표에든 더 빨리 반응하는 성향"은 흡수하지 못합니다 (원고 6.3).

---

## 6. 추가 수정 체크리스트 (EMSE 형식)

- [ ] Section 2.1, 2.2 (가격 경제학, 교체 모델)를 1/3로 줄이고, release engineering / rapid release / ML 시스템 기술 부채 문헌을 늘리기
- [ ] Section 3 (Poisson 모델)은 유지하되 "Background and hypotheses"로 이름 바꾸고 분량 줄이기
- [ ] "Implications"를 연구자용 / 실무자용으로 나누고, IS식 정책 논의(EU AI Act)는 짧게
- [ ] Limitations → Threats to Validity (construct: bug 분류 미검증, release = refresh proxy / internal: 동시결정성, burst / external: 3.2 / conclusion: 검정력, 다중비교)
- [ ] bug 분류를 수동 라벨 샘플로 검증해서 precision/recall 보고 (원고가 스스로 한계로 인정한 부분이며 가장 쉽게 막을 수 있는 공격입니다)
- [ ] 데이터와 코드를 Zenodo 등에 DOI로 공개 (EMSE는 open science policy가 있습니다)
- [ ] 저자 가이드에 따라 구조화 abstract 여부와 분량을 확인
