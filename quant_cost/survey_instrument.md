# 서베이 문안 (Prolific 배포용, 영어 원문 + 한국어 구현 메모)

> 응답자에게 보이는 문안은 영어이고, `[구현]` 표시는 연구자용 메모다. `[REPLACE]`는 `quant_cost` 측정값이나 확정값으로 교체한다. 설문 도구(Qualtrics 등)의 무선화 기능으로 구현한다. 소요 시간 약 15분.
> 선별 문항 S1–S7과 자격 규칙은 `screening_items.md`를 그대로 쓴다(이 문서의 Part 1 위치). 가설과 분석은 `experiment_design.md`, `preregistration_draft.md` 참조.

---

## 구조와 흐름

| 순서 | 블록 | 내용 |
| --- | --- | --- |
| 0 | 동의 | 연구 설명, 자발적 참여 |
| 1 | 선별 | S1–S7 (`screening_items.md`), 부적격 시 종료 |
| 2 | 소개와 기저율 | 모든 응답자에게 같은 문안 |
| 3 | **H2 조작** | 사고 사례 노출 / 비노출 (무선 배정), 추정 유출확률 측정 |
| 4 | 시나리오 4개 | 각 시나리오: 본문 → 이해 점검 → 선택 → F_max → 대기 개월 → 변동성 지각 |
| 5 | 공변량 | 수리능력, AI 경험, 프라이버시 우려, 위험 선호 (주의 점검 A1, A2 포함) |
| 6 | 일관성·인구통계 | C1(S1·S2 재확인), 인구통계 |
| 7 | 해설(debrief) | 시나리오·사고 사례가 가상임을 알림, 완료 코드 |

**[구현] 무선화**
- 응답자 단위로 두 가지를 독립 무선 배정: (1) 사고 사례 **노출/비노출**(50:50), (2) **라틴 방격 버전 V1–V4**(균등).
- 시나리오 제시 순서는 매번 무선.
- 슬라이더는 **초기 위치 없음**(클릭해야 값이 생김), 응답 강제(forced response)는 선택 문항에만 적용.

---

## 0. 동의

**Study information**
You are invited to take part in a research study about how professionals make technology sourcing decisions. The survey takes about 15 minutes. You will read four short business scenarios and answer questions about the choices you would make. All scenarios are hypothetical.

Your participation is voluntary, and you may stop at any time without penalty (return the study on Prolific). Your answers are anonymous and will be used only for research. We will not ask for your name or employer. [IRB 승인 번호/연락처: REPLACE]

☐ I have read the information above and agree to participate.

---

## 1. 선별
`screening_items.md`의 S1–S7을 그대로 사용. 자격 규칙 불충족 시:
> Thank you. Based on your answers, you are not eligible for this study. [Prolific 스크린아웃 절차에 따라 처리 — 보상 규칙은 `experiment_design.md` §9 확인 후 확정]

---

## 2. 소개와 기저율 (모든 응답자)

In the following scenarios, you will play the role of a **decision-maker at a mid-sized company** (about 500 employees) that processes large volumes of text documents containing customers' personal information. The company currently uses a **cloud AI service (API)** from an external vendor. A **local small AI model**, run on the company's own servers, is an alternative. It is cheaper to run but somewhat less accurate, and it keeps all data inside the company.

All amounts are in US dollars. All figures in this survey are **hypothetical**.

**Background figure (shown to everyone):** In this hypothetical industry, a company that sends customer data to an external AI vendor has about a **[3]% chance per year** of a data exposure incident involving that vendor. [REPLACE: 값을 정하고 출처가 없으면 "hypothetical"로만 표기]

---

## 3. H2 조작 + 추정 유출확률

### 3-A. 노출 집단에게만 (Incident condition)
Please read the following short report.

> **Customer records exposed through an AI vendor.** Last year, a mid-sized insurance company discovered that customer names, phone numbers and claim details had been exposed after its external AI vendor suffered a security failure. The company had to notify thousands of customers, faced an investigation, and its customer-service volume rose sharply for months. *(The report is fictional and written for this study.)*

### 3-B. 비노출 집단에게만 (Control condition)
Please read the following short report.

> **Companies compare AI deployment options.** Mid-sized companies increasingly evaluate whether to run AI models in the cloud or on their own servers. Analysts describe the choice as depending on cost, accuracy, and operational capacity. *(The report is fictional and written for this study.)*

(두 문단의 길이를 맞춘다. [구현] 노출 집단 문단에도 "fictional" 표기를 넣어 윤리적 해설과 일치시킨다.)

### 3-C. 모든 응답자 — 추정 유출확률 (H2 매개)
Thinking about a company like the one described, **what do you think is the chance, over the next 12 months, that customer data is exposed through an external AI vendor?**
(slider 0–100%)

---

## 4. 시나리오 (4개 × 반복 구조)

### 4-1. 조건 정의
4개 조건(셀)은 변동성 × 성능 제시의 2×2.

| 셀 | 변동성 | 성능 제시 |
| --- | --- | --- |
| C1 | 저 | 정확도만 |
| C2 | 저 | 정확도 + 정답당 비용 |
| C3 | 고 | 정확도만 |
| C4 | 고 | 정확도 + 정답당 비용 |

### 4-2. 사례와 수치 (V = 1.8·F로 고정, 모두 `[REPLACE]`)

| 사례 | 업무 | F (일회성 구축비) | V (3년 절감 현재가치) | F_max 슬라이더 범위 (0–1.2V) | 로컬/API 정확도 | 로컬/API 요청당 비용 | 정답당 비용 로컬/API |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 고객 문의 분류 | $400,000 | $720,000 | $0–$864,000 | 88% / 95% | $0.004 / $0.012 | $0.0045 / $0.0126 |
| B | 인사 기록 정리 | $300,000 | $540,000 | $0–$648,000 | 86% / 96% | $0.005 / $0.013 | $0.0058 / $0.0135 |
| C | 계약 문서 요약 | $500,000 | $900,000 | $0–$1,080,000 | 84% / 95% | $0.010 / $0.028 | $0.0119 / $0.0295 |
| D | 보험 청구 심사 보조 | $600,000 | $1,080,000 | $0–$1,296,000 | 87% / 97% | $0.008 / $0.022 | $0.0092 / $0.0227 |

(정답당 비용 = 요청당 비용 ÷ 정확도. 위 값은 형식 예시이며 실제 측정값으로 반드시 교체하고 계산을 다시 한다.)

### 4-3. 라틴 방격 (사례 → 셀)

| 버전 | C1 | C2 | C3 | C4 |
| --- | --- | --- | --- | --- |
| V1 | A | B | C | D |
| V2 | B | C | D | A |
| V3 | C | D | A | B |
| V4 | D | A | B | C |

### 4-4. 시나리오 본문 템플릿

**Scenario [n] of 4 — [업무명]**

Your company wants to use AI to **[업무 설명: e.g., classify incoming customer inquiries]**. These documents contain customers' personal information. The company currently uses the cloud API.

**Option to build a local model.** You could build a local small AI model that runs on your own servers.
- One-time cost to build it: **$[F]**
- The estimated present value of the savings it would generate over the next three years: **$[V]**

**[변동성 문구 — 저]**
Over the next 12 months, API prices and the performance of small AI models are expected to stay **very stable**. Analysts' forecasts agree closely with each other.

**[변동성 문구 — 고]**
Over the next 12 months, API prices and the performance of small AI models could **change a great deal, up or down**. Analysts' forecasts disagree widely.

**[성능 제시 — 정확도만 (C1, C3)]**

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | [88]% | [95]% |

**[성능 제시 — 병기 (C2, C4)]**

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | [88]% | [95]% |
| Cost per correct answer | $[0.0045] | $[0.0126] |

**Your options**
- **(a) Build the local model now.**
- **(b) Wait 12 months, then decide again.** You keep using the cloud API in the meantime. Later you could still build the local model, but the cost and the expected savings will have changed.
- **(c) Keep using the cloud API.** You do not build a local model.

### 4-5. 시나리오마다 묻는 문항 (이 순서)

**Q1. (이해 점검, K)** In this scenario, what is the one-time cost of building the local model?
- $[F] (정답)
- $[V]
- $[F의 절반]
- $[F의 2배]
(선택지 순서 무선)

**Q2. (DV1 선택)** Which option would you choose?
○ (a) Build the local model now ○ (b) Wait 12 months, then decide again ○ (c) Keep using the cloud API

**Q3. (DV2 F_max)** Suppose the quoted cost of $[F] could be different. **What is the highest one-time cost you would still be willing to pay to build the local model now?**
(slider $0 – $[1.2V], 값이 숫자로 표시됨)

**Q4. (DV3 대기)** Ignoring your answer above, **how many months would you prefer to wait before committing money to a local build?** (0 = commit now, 24 = wait two years)
(slider 0–24)

**Q5. (변동성 지각 점검)** How much do you expect API prices and small-model performance to change over the next 12 months in this scenario?
1 = Almost no change … 7 = Very large changes

(시나리오 2와 3 사이에 주의 점검 A1을 넣는다. 5-A 참조.)

---

## 5. 공변량 블록

**5-A. 주의 점검 (시나리오 2와 3 사이)**
**A1.** To show you are reading carefully, please select "Somewhat agree" for this item.
1 Strongly disagree – 7 Strongly agree (정답 5)

**5-B. 수리능력 (직접 작성한 3문항 — 검증 척도로 대체 가능)**
**N1.** A product costs $200. It is discounted by 25%. What is the new price? ($150)
**N2.** A project has a 20% chance of success. Out of 500 similar projects, about how many would you expect to succeed? (100)
**N3.** A firm's cost rises from $80 to $100. By what percentage did it rise? (25%)
(주관식, 숫자 입력. 검증된 수리능력 척도를 쓰려면 사용 허락과 출처를 확인해 교체한다.)

**5-C. AI 경험**
**E1.** How familiar are you with large language models (LLMs)? 1 Not at all – 5 Extremely
**E2.** How often do you use LLM-based tools at work? Never / Rarely / Monthly / Weekly / Daily
**E3.** Has your organization built or run its own AI model on its own servers? Yes / No / Not sure

**5-D. 프라이버시 우려 (직접 작성한 4문항 — 검증 척도로 대체 가능)** 1 Strongly disagree – 7 Strongly agree
**P1.** I worry about the safety of personal data held by external vendors.
**P2.** Keeping data inside the company is worth extra cost.
**P3.** Data breaches at vendors are a serious business risk.
**P4.** My organization takes data-handling rules very seriously.
(원문 척도를 쓰려면 사용 허락과 출처를 확인해 교체한다.)

**5-E. 위험 선호**
**R1.** How willing are you to take risks in business decisions, in general? 0 = Not at all willing … 10 = Very willing

**5-F. 주의 점검 2 (공변량 블록 끝)**
**A2.** For this question, please select the second option from the left: ○ Never ○ Rarely ○ Sometimes ○ Often ○ Always (정답 Rarely)

---

## 6. 일관성 점검과 인구통계

**C1-a.** What is your current main job function? (S1과 같은 선택지) → S1과 불일치 시 제외
**C1-b.** What is your current level? (S2와 같은 선택지) → S2와 불일치 시 제외

**Demographics (선택 응답, 보고용)**
- Age: 18–24 / 25–34 / 35–44 / 45–54 / 55+
- Gender: Woman / Man / Another / Prefer not to say
- Highest education: High school / Bachelor's / Master's / Doctorate / Other
- Years of work experience: <3 / 3–5 / 6–10 / 11–20 / >20
- Country of residence (Prolific 정보와 대조해 보고용으로만 사용)

---

## 7. 해설 (Debrief)

Thank you for taking part. We want to be transparent about what this study involved:
- All companies, figures, and reports in this survey were **fictional**, including the customer-data exposure report (if you saw one) and the background figure for incident probability.
- The study examines how professionals weigh uncertainty, data-risk information, and the way performance information is presented when choosing between cloud and local AI. Some conditions differed between participants on purpose.
- Your answers do not reflect any real decision at your employer, and nothing here is advice about a real purchase.
- If you have questions, please contact [연구자 이메일, REPLACE]. [IRB 문구 REPLACE]

Your completion code is [Prolific 완료 URL/코드: REPLACE].

---

## 구현 체크리스트

1. 모든 `[REPLACE]` 수치를 `quant_cost` 측정값으로 교체하고 정답당 비용을 재계산한다. V = 1.8F를 유지한다.
2. 사고 사례/비노출 문단의 길이를 맞추고, 기저율 문구는 두 집단에 **동일하게** 표시한다(H2의 핵심 통제).
3. 라틴 방격 V1–V4와 사고 사례 노출(2) = 8 그룹에 무선 배정되는지 테스트 응답으로 확인한다.
4. 슬라이더는 초기 위치가 없고, 값이 숫자로 보이는지 확인한다. 휴대폰에서도 조작되는지 본다.
5. 자격 규칙·점검 문항·제외 규칙이 사전등록 문서와 정확히 일치하는지 대조한다.
6. 사전 점검 20명에서 소요 시간, 이해 점검 오답률, 어색한 문구를 확인하고 본 수집 전에 수정한다(수정 기록 보관).
7. 영어 원문을 원어민 또는 전문가가 검수하고, 한국어 대조본을 보관한다.
