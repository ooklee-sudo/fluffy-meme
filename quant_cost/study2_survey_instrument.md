# Study 2 서베이 문안 (Prolific 배포용, 영어 원문 + 한국어 구현 메모)

> 응답자에게 보이는 문안은 영어이고 `[구현]`은 연구자용 메모, `[REPLACE]`는 확정값으로 교체한다. 설계는 `study2_design.md`, 규범 값은 `normative_check_study2.py`. 소요 시간 약 19분.
> 선별 문항(S1–S8)과 자격 규칙은 `screening_items.md`, 공변량·일관성·인구통계 블록(§5–§6)은 `survey_instrument.md`와 같다. 아래에는 Study 2에서 달라진 부분만 적는다.

---

## 구조와 흐름

| 순서 | 블록 | 내용 |
| --- | --- | --- |
| 0 | 동의 | 연구 설명 (소요 19분) |
| 1 | 선별 | `screening_items.md` (S8 정책 문항 포함, 무선 배정 전) |
| 2 | 소개 | 역할, 두 선택지 설명, 위험중립 안내 |
| 3 | **H2 조작** | 사고 사례 / 중립 보도 (무선 50:50) → 일반 노출 확률 추정 |
| 4 | 시나리오 4개 | λ(낮음/높음) × 성능 제시(정확도만/병기). 각 시나리오: 본문 → 이해 점검 → 선택 → WTP → 추정 확률 → 지각된 품질 격차 |
| 5 | 공변량 | `survey_instrument.md` §5 (수리능력, AI 경험, 프라이버시 우려, 위험 선호, 주의 점검 A1·A2) + 아래 §5 추가 문항(재량, 요소 순위, 산업, 지식재산 중요도, 기밀 정보) |
| 6 | 일관성·인구통계 | `survey_instrument.md` §6 |
| 7 | 해설 | 아래 추가 문장 포함 |

**[구현] 무선화**
- 응답자 단위로 독립 배정: (1) 사고 사례 노출/비노출(50:50), (2) 라틴 방격 버전 V1–V4(균등). 시나리오 순서는 매번 무선.
- 슬라이더/숫자 입력은 초기값 없음. 선택 문항만 응답 강제.
- 매개 문항(추정 확률, 지각된 품질 격차)은 **선택과 WTP 뒤**에 둔다.
- A1은 시나리오 2와 3 사이.

---

## 0. 동의

You are invited to take part in a research study about how professionals make technology sourcing decisions. The survey takes about 19 minutes. You will read a short news item and four business scenarios and answer questions about the choices you would make. All scenarios and figures are hypothetical.

Your participation is voluntary, and you may stop at any time without penalty (return the study on Prolific). Your answers are anonymous and will be used only for research. We will not ask for your name or employer. This study has been reviewed and approved by the Hanyang University Institutional Review Board (approval no. HY-IRB-2026-11-033). If you have questions about the study, you may contact the researcher at ooklee@hanyang.ac.kr.

☐ I have read the information above and agree to participate.

[구현] IRB 사무국이 Study 2에 별도 승인이 필요 없다고 답변했다(승인 번호 HY-IRB-2026-11-033 유지). 답변 서면을 보관한다.

---

## 2. 소개 (모든 응답자)

In the following scenarios, you will play the role of a **decision-maker at a mid-sized company** (about 500 employees) that processes large volumes of text documents containing customers' personal information. For each scenario you must choose between two options for the coming year:
- a **cloud AI service (API)** from an external vendor, or
- a **local small AI model** that runs on your own servers.

**Please decide as a risk-neutral manager:** assume your company cares only about the **expected total cost over the coming year** and is neither more nor less cautious than that.

All amounts are in US dollars per year. All figures in this survey are **hypothetical**.

---

## 3. H2 조작

### 3-A. 노출 집단 (Incident condition)
Please read the following short news item.

> **Customer records exposed through an AI vendor.** Last year, a mid-sized insurance company discovered that customer names, phone numbers and claim details had been exposed after its external AI vendor suffered a security failure. The company had to notify thousands of customers, faced an investigation, and its customer-service volume rose sharply for months. *(This news item is fictional and written for this study.)*

### 3-B. 비노출 집단 (Control condition)
Please read the following short news item.

> **Companies compare AI deployment options.** Mid-sized companies increasingly evaluate whether to run AI models in the cloud or on their own servers. Analysts describe the choice as depending on cost, accuracy, and operational capacity. *(This news item is fictional and written for this study.)*

(두 문단의 길이를 맞춘다.)

### 3-C. 모든 응답자 — 일반 노출 확률 추정 (사고 사례의 가용성 효과 점검)
Thinking about companies in general, **what do you think is the chance, over the next 12 months, that a mid-sized company's customer data is exposed through an external AI vendor?** (0–100%, numeric entry)

---

## 4. 시나리오 (4개)

### 4-1. 조건
| 셀 | 노출 확률 λ | 성능 제시 |
| --- | --- | --- |
| C1 | 낮음 (2%) | 정확도만 |
| C2 | 낮음 (2%) | 정확도 + 정답당 비용 |
| C3 | 높음 (6%) | 정확도만 |
| C4 | 높음 (6%) | 정확도 + 정답당 비용 |

### 4-2. 사례와 수치 (천 달러/년, 사례 C 기준 B=100, E=180, L=2,000; 나머지는 비례)

| 사례 | 업무 | 운영비 절감 B | 추가 오류 비용 E | 노출 시 손실 L | WTP 슬라이더 범위 (0–L/4) |
| --- | --- | --- | --- | --- | --- |
| A | 고객 문의 분류 | 80 | 144 | 1,600 | $0–$400k |
| B | 인사 기록 정리 | 60 | 108 | 1,200 | $0–$300k |
| C | 계약 문서 핵심 조항 추출 | 100 | 180 | 2,000 | $0–$500k |
| D | 보험 청구 분류(트리아지) | 120 | 216 | 2,400 | $0–$600k |

성능 수치는 `quant_cost` 측정값으로 채운다(예시, `[REPLACE]`):

| 사례 | 로컬/API 정확도 | 정답당 비용 로컬/API |
| --- | --- | --- |
| A | [88]% / [95]% | $[0.0045] / $[0.0126] |
| B | [86]% / [96]% | $[0.0058] / $[0.0135] |
| C | [84]% / [95]% | $[0.0119] / $[0.0295] |
| D | [87]% / [97]% | $[0.0092] / $[0.0227] |

(성능 수치는 맥락일 뿐 B, E 수치는 성능과 무관하게 고정한 설계값이다. 측정값을 넣을 때 B, E, L은 건드리지 않는다.)

정답당 비용의 비용 모형(확정): 장비 $1,500을 3년에 상각, **이용률 50%**, 전기 $0.12/kWh, 에너지와 지연은 측정값. 수치는 `python -m quant_cost.scenario_numbers --local-label <라벨> --sensitivity`로 만들고(기본 이용률이 0.5), 25%·75% 민감도는 부록에 보고한다.

### 4-3. 라틴 방격 (사례 → 셀)
| 버전 | C1 | C2 | C3 | C4 |
| --- | --- | --- | --- | --- |
| V1 | A | B | C | D |
| V2 | B | C | D | A |
| V3 | C | D | A | B |
| V4 | D | A | B | C |

### 4-4. 시나리오 본문 템플릿

**Scenario [n] of 4 — [업무명]**

Your company wants to use AI to **[업무 설명: e.g., classify incoming customer inquiries]**. These documents contain customers' personal information. For the coming year you must choose between the two options below.

**Key numbers (per year, in thousands of dollars)**
- **Running cost.** The local model is cheaper to run than the cloud API by **$[B]k** per year.
- **Errors.** The local model is less accurate. Its extra errors cost **$[E]k** per year.
- **Data exposure with the cloud API.** Your company's risk team estimates a **[λ]% chance per year** that customer data is exposed through the vendor. This estimate is based on industry-wide data covering all reported incidents. If it happens, the loss to your company is **$[L]k** (fines, notification, and lost customers).
- **Data exposure with the local model.** All data stay in-house. There is no exposure risk from a vendor.

The figures above **already take into account** the performance difference shown below.

**[성능 제시 — 정확도만 (C1, C3)]**

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | [88]% | [95]% |

**[성능 제시 — 병기 (C2, C4)]**

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | [88]% | [95]% |
| Cost per 1,000,000 correct answers | $[4.75] | $[29.4] |

### 4-5. 시나리오마다 묻는 문항 (이 순서)

**Q1. (이해 점검, K)** In this scenario, what is the yearly chance of customer data being exposed through the cloud vendor?
○ 2% ○ 6% ○ 10% ○ 20% (선택지 순서 무선, 정답은 그 시나리오의 λ)

**Q2. (DV1 선택)** Which option would you choose for the coming year?
○ The local model ○ The cloud API

**Q3. (DV2 WTP)** **How much would you be willing to pay per year to eliminate the exposure risk of the cloud API altogether** (that is, to be certain that no customer data is exposed through a vendor)?
(slider $0 – $[L/4]k, 값이 숫자로 표시됨)

**Q4. (추정 확률, 매개)** In your own judgment, what is the chance per year that customer data is exposed through the cloud vendor in this scenario? (0–100%, numeric entry)

**Q5. (지각된 품질 격차, 매개)** How large is the local model's quality disadvantage compared with the cloud API in this scenario?
1 = Not large at all … 7 = Extremely large

### 4-6. 규범 키 (연구자용, 응답자에게 보이지 않음)

로컬의 순 이점 = (B − E) + λL (천 달러/년). 규범 WTP = λL.

| 사례 | 낮은 λ(2%): 순 이점 / 최적 / WTP* | 높은 λ(6%): 순 이점 / 최적 / WTP* | ln(WTP* 높음/낮음) |
| --- | --- | --- | --- |
| A | −32 / API / 32 | +32 / 로컬 / 96 | 1.099 |
| B | −24 / API / 24 | +24 / 로컬 / 72 | 1.099 |
| C | −40 / API / 40 | +40 / 로컬 / 120 | 1.099 |
| D | −48 / API / 48 | +48 / 로컬 / 144 | 1.099 |

손익분기 λ* = 4%. 값은 `normative_check_study2.py`로 계산·검증한다.

---

## 5. 공변량 추가 문항 (Study 2, `survey_instrument.md` §5의 문항 뒤에)

(S8 정책 문항은 선별 블록에서 이미 물었다: `screening_items.md`.)

**P2. (재량)** Within your organization's current policy, how much discretion do you (or your team) have in choosing between a local model and a cloud AI service for a use case like those in this survey?
1 = No discretion at all … 7 = Full discretion

**P3. (요소 중요도, 선택·WTP 뒤에 둔다)** Which factors matter most when your organization decides how to source AI for sensitive data? Please select your **top three** and rank them (1 = most important).
- Running cost
- Accuracy and quality of the AI
- Security and privacy policy
- Regulatory and legal compliance
- Dependence on an outside vendor
- In-house expertise needed to operate it
(항목 순서 무선)

**I1. (산업)** Which best describes your organization's industry?
○ Semiconductors / electronics hardware ○ Software / IT services ○ Finance / insurance ○ Healthcare / pharmaceuticals ○ Defense / aerospace / government ○ Manufacturing (other) ○ Retail / consumer ○ Telecom / media ○ Energy / utilities ○ Other

**I2. (지식재산 중요도)** How valuable are trade secrets and intellectual property (for example designs, source code, research data) to your organization's competitive position?
1 = Not at all valuable … 7 = Extremely valuable

**I3. (기밀·통제 정보)** Does your organization handle classified, export-controlled or similarly regulated information?
○ Yes ○ No ○ Not sure

[구현] P3은 처치(사고 사례) 뒤에 묻는 **결과 변수**이기도 하다(사고 사례가 보안·프라이버시 순위를 올리는지, 탐색적). S8, I1–I3은 공변량이다.

---

## 7. 해설 (Study 1과 같고 아래를 추가)

- All figures in this survey, including the risk team's exposure estimates and the loss amounts, were **fictional**.
- The news item you read (about a data exposure or about companies comparing AI options) was written for this study. The conditions differed between participants on purpose; the exposure probabilities shown in the scenarios were the same kind of estimates for everyone.
- If you have questions, please contact ooklee@hanyang.ac.kr. This study was approved by the Hanyang University Institutional Review Board (HY-IRB-2026-11-033).

---

## 구현 체크리스트

1. 성능 수치를 `quant_cost` 측정값으로 교체한다. B, E, L, λ는 건드리지 않는다.
2. 사고 사례/중립 보도의 길이를 맞춘다.
3. 8그룹(V1–V4 × 노출/비노출) 무선 배정이 되는지 테스트 응답으로 확인한다.
4. 모바일에서 슬라이더와 숫자 입력이 되는지 확인한다.
5. 이해 점검 오답률과 WTP 분포를 사전 점검(20명)에서 확인하고, 사전등록의 진행 기준과 대조한다.
6. 영어 원문을 원어민 또는 전문가가 검수한다.
