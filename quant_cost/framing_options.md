# "이 논문이 IS 이론에 더하는 것": 세 가지 후보 프레이밍

> 초안(가설 생성용)이다. "가장 가까운 선행연구" 칸은 제가 기억과 앞선 웹 검색에 의존해 적은 것이라 **원문과 체계적 검색으로 확인하기 전에는 주장에 쓰지 말 것**. 영어 문단은 투고문이 아니라 프레이밍을 비교하기 위한 시험 문안이다. 근거 데이터는 Study 2(`study2_design.md`)를 기준으로 한다.

## 한눈에 비교

| | 프레이밍 1 | 프레이밍 2 | 프레이밍 3 |
| --- | --- | --- | --- |
| 이름 | 속성 현저성 왜곡 | 정보 인공물 설계 | 프라이버시 계산의 경계 조건 |
| 한 줄 주장 | AI 소싱 결정은 정보의 양이 아니라 어떤 속성이 두드러지는지에 따라 움직인다 | 벤더의 성능 보고 형식과 사고 공개 방식이 소싱 결정을 바꾸는 설계 변수다 | 조직의 프라이버시 계산은 위험이 생생할 때 확률에 둔감해진다 |
| 대화할 IS 문헌 | IT 소싱·도입 의사결정, 행동 의사결정 | 정보 제시·의사결정 지원, AI 거버넌스, 투명성 | 프라이버시 계산, 정보보안 행동 |
| 가장 강하게 쓰는 가설 | H2c, H3a, H4 | H3a, H3b | **H2c**, H2a, H2b |
| 필요한 추가 연구 | 다른 속성 쌍으로 일반화 | 실제 벤더 보고서 분석, 실무자 인터뷰 | 다른 위험 크기(L)와 맥락에서 반복 |
| 가장 큰 위험 | 너무 일반적인 심리학 이론의 적용으로 읽힘 | 이론보다 실무 가이드로 읽힘 | 개인 수준 이론을 조직에 옮긴 것이 타당한지 의심받음 |
| 이번 데이터로의 적합도 | 중간 | 중간(H3만 주축) | **높음**(주 검정 H2c가 중심) |

## 프레이밍 1: 속성 현저성 왜곡 (Attribute Salience Distortion in AI Sourcing)

**핵심 주장.** 규범적으로 선택이 같아야 하는 정보 조작(사고 사례 읽기, 성능 제시 형식)이 소싱 결정의 속성별 가중치를 움직인다. 생생한 프라이버시 사고는 프라이버시 속성을, 정확도만 보여주는 형식은 품질 격차 속성을 두드러지게 한다. 두 효과는 주의가 한정되어 서로 경쟁한다(H4).

**IS 이론에 더하는 것.** IT 소싱 결정 문헌이 대개 거래비용과 자원 기반의 합리적 모형을 쓴다는 점에 "정보가 어떻게 제시되는가가 가중치를 바꾼다"는 행동 메커니즘을 더한다.

**시험 문안(영어).** *Sourcing decisions for AI are usually modeled as comparisons of cost, quality, and risk. We show that the weights managers place on these attributes are not fixed but depend on which attribute information makes salient. Vivid incident reports shift weight toward privacy risk, while the format of performance reporting shifts weight between quality and cost, even when the underlying numbers are identical.*

**심사자가 물을 것.** "현저성 이론과 가용성 휴리스틱을 AI 소싱에 적용한 것이 IS 고유의 기여인가?" 일반 심리학 이론의 새 맥락 적용으로 읽힐 위험이 가장 크다.

**가장 가까운 선행연구(미확인).** 현저성 이론(Bordalo, Gennaioli & Shleifer), 가용성 휴리스틱(Tversky & Kahneman), IT 소싱 의사결정 연구.

## 프레이밍 2: 정보 인공물 설계 (Performance Reporting and Incident Disclosure as Decision Infrastructure)

**핵심 주장.** AI 벤더가 쓰는 성능 지표의 형식과 사고를 공개하는 방식은 단순한 정보 전달이 아니라 구매자의 결정을 설계하는 **정보 인공물**이다. 같은 정보라도 통합 지표(정답당 비용)와 단일 지표(정확도)는 선택을 다르게 만든다(H3).

**IS 이론에 더하는 것.** IS의 핵심 관심사인 "정보 시스템과 정보 제시가 결정을 어떻게 바꾸는가"를 AI 구매 맥락에서 보고 지표 설계의 원칙을 제시한다. 규제와 표준(보고 형식 표준화)에 대한 시사점이 크다.

**시험 문안(영어).** *Vendors and regulators increasingly shape AI procurement through the information they publish: benchmark scores, cost metrics, and incident disclosures. We treat these as decision infrastructure and show experimentally that the format of performance reporting and the vividness of incident disclosure change sourcing choices even when the information content is held constant, which yields design principles for reporting standards.*

**심사자가 물을 것.** "이론적 기여가 무엇인가? 실무 가이드나 정책 제언에 가깝다." H2(사고 사례)가 이 프레이밍에서는 부차적이 되어, 가장 강한 검정(H2c)이 활용되지 못한다.

**가장 가까운 선행연구(미확인).** 정보 제시 형식과 인지 적합(cognitive fit) 연구, 의사결정 지원 시스템 연구, AI 거버넌스·투명성 문헌.

## 프레이밍 3: 프라이버시 계산의 경계 조건 (When the Privacy Calculus Breaks: Probability Insensitivity in Organizational AI Sourcing)

**핵심 주장.** 프라이버시 계산 이론은 위험의 확률과 손실을 비용·이익과 저울질한다고 본다. 우리는 **위험이 생생할 때(사고 사례 노출) 조직의 결정이 제시된 확률에 둔감해진다**는 경계 조건을 보인다(H2c). 선택은 확률이 아니라 결과의 끔찍함에 반응하고, 이는 추정 확률의 상승(H2b)과 구별된다.

**IS 이론에 더하는 것.** 프라이버시 계산이 가장 많이 연구된 IS의 중심 이론 중 하나라는 점에서, 개인 정보 공개에서 **조직의 소싱 결정**으로 옮겼을 때 이론이 언제 깨지는지를 규정한다. 확률 둔감(기울기 감소)과 가용성(수준 이동)을 구분하는 검정이 이론적 차별점이다. H3은 "주의 재분배"의 두 번째 증거로 보조한다.

**시험 문안(영어).** *The privacy calculus assumes that decision makers weigh the probability and magnitude of privacy harm against benefits. We show that this calculus has a boundary condition at the organizational level: when harm is made vivid, sourcing decisions become less sensitive to the stated probability of exposure, even though normatively they should respond to it. Distinguishing a shift in perceived probability from a flattening of the response to probability, we clarify when and why organizational privacy calculi fail.*

**심사자가 물을 것.** "개인 수준 이론을 조직 의사결정에 옮겨도 되는가? 응답자는 조직이 아니라 개인이다." 그리고 "정서 부하에 따른 확률 둔감이 실제 조직 결정에서도 나타나는가?" 가상 시나리오와 개인 응답으로 조직 수준을 주장하는 것이 약점이다.

**가장 가까운 선행연구(미확인).** 프라이버시 계산(Culnan & Armstrong, Dinev & Hart), 정서와 확률 둔감(Rottenstreich & Hsee), 정보보안 공포 호소(Johnston & Warkentin).

## 제 평가와 권고

- **이번 데이터와 가장 잘 맞는 것은 프레이밍 3입니다.** 사전등록의 주 검정(H2c)이 바로 이 프레이밍의 핵심 예측이라, 설계와 주장이 일치합니다. 또 ISR이 오래 다뤄 온 프라이버시 계산 이론에 직접 이어져서 독자층이 분명합니다.
- **프레이밍 2의 내용은 논의의 실무적 시사점**으로 쓰고(보고 지표 설계, 사고 공개 방식), **프레이밍 1의 일반화는 한계와 후속 연구**로 두는 조합을 권합니다. 즉 "3을 주축, 2를 시사점, 1을 확장".
- 프레이밍을 고정하기 전에 확인할 것:
  1. 핵심 서지(프라이버시 계산, 확률 둔감, 현저성)를 원문으로 읽고 "가장 가까운 선행연구"가 실제로 같은 가설을 검정했는지 확인한다.
  2. 조직 수준 주장을 어떻게 정당화할지(응답자가 실제 구매 권한을 가진 전문직이라는 점, 시나리오가 회사 단위 비용·손실이라는 점) 정리한다.
  3. 지도교수와 어느 프레이밍이 목표 저널의 독자에게 가장 설득력 있는지 의견을 구한다.
- H2c가 데이터에서 안 나오면(효과가 없거나 반대) 프레이밍 3은 약해진다. 그 경우 프레이밍 1이나 2로 옮길 여지를 남기려면 **사전등록의 보조·탐색 분석을 빠짐없이 보고**해야 한다.
