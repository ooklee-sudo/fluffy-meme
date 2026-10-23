# 선행연구 정리와 이론적 배경

> **인용 검증 안내**: 아래 문헌은 저자가 기억하는 서지정보에 기반합니다. 논문 투고 전 **각 항목의 저자·연도·저널·권호·쪽수를 원문/DB(Google Scholar, DOI)로 반드시 확인**하세요. 특히 쪽수·권호는 기재하지 않았습니다.

## 1. 연구의 위치

세 갈래 문헌의 교차점에 위치한다.
(A) 온라인 리뷰·콘텐츠의 **반응(helpfulness, 공유, 좋아요)을 설명하는 텍스트 특성** 연구,
(B) 마케팅의 **자동 텍스트 분석 방법론**과 그 LLM으로의 확장,
(C) **count 데이터 계량모형**과 **기계 생성 변수의 측정오차 보정**.

## 2. 문헌 (A): 텍스트 특성과 반응 count

| 문헌 | 핵심 발견 | 본 연구와의 연결 |
|---|---|---|
| Mudambi & Schuff (2010), *MIS Quarterly* — "What Makes a Helpful Online Review?" | 제품 유형(탐색재/경험재)에 따라 극단적 별점·리뷰 길이의 helpfulness 효과가 달라짐. helpful votes를 종속변수로 사용 | H3의 이론적 근거. 본 연구는 별점/길이 대신 **텍스트 내용 특성**을 투입 |
| Cao, Duan & Gan (2011), *Decision Support Systems* | 의미적(semantic) 특성이 helpful votes에 영향, 극단적 의견이 더 많은 표를 받음 | 감성 비선형(H2) |
| Yin, Bond & Zhang (2014), *MIS Quarterly* | 불안(anxiety)과 분노(anger)가 리뷰 helpfulness 인식에 서로 다르게 작용 | `dominant_emotion` 범주 설계 |
| Berger & Milkman (2012), *Journal of Marketing Research* | 각성(arousal)이 높은 감정이 콘텐츠 공유(viral)를 증가시킴 | `emotional_intensity`의 이론 |
| Ghose & Ipeirotis (2011), *IEEE TKDE* | 리뷰의 주관성·가독성 등 텍스트 특성이 유용성·판매에 영향 | 텍스트 특성 → 반응 연구의 선례 |
| Godes & Mayzlin (2004), *Marketing Science*; Chevalier & Mayzlin (2006), *JMR* | eWOM의 양·내용이 판매에 영향 | eWOM 연구의 동기 |

### 이론적 메커니즘 (가설 도출용)
- **진단성(diagnosticity) 이론**: 구체적·정보적 텍스트는 구매 결정의 불확실성을 줄여 유용성 투표를 유도 → **H1**(구체성, 정보성 ↑).
- **각성 이론(arousal)**: 고각성 감정은 공유·반응을 촉진 → 감정 강도·극단 감성 ↑ (**H2**).
- **양면 메시지(two-sided message)와 신뢰성**: 장단점을 모두 서술한 리뷰는 신뢰성 지각이 높아 유용하다고 평가 → `argument_balance` ↑.
- **서사 전이(narrative transportation)**: 경험담은 몰입을 높이나 정보성은 낮을 수 있어 효과 방향이 열려 있음(탐색적 가설).
- **상품 유형 조절**: 경험재는 감정·경험 서술, 탐색재는 사양·정보 서술의 가치가 큼 (Mudambi & Schuff; Nelson의 search/experience goods 구분) → **H3**.

## 3. 문헌 (B): 자동 텍스트 분석과 LLM 코딩

- Humphreys & Wang (2018), *Journal of Consumer Research* — 소비자 연구에서 자동 텍스트 분석의 타당화 절차(사전 기반, 분류기, 토픽모델)를 정리. 본 연구의 **타당화 프로토콜의 틀**.
- Berger, Humphreys, Ludwig, Moe, Netzer & Schweidel (2020), *Journal of Marketing* — "Uniting the Tribes: Using Text for Marketing Insight". 마케팅에서 텍스트 활용의 이론-방법 통합.
- Netzer, Feldman, Goldenberg & Fresko (2012), *Marketing Science* — 텍스트 마이닝으로 시장구조 도출.
- Tirunillai & Tellis (2014), *Journal of Marketing Research* — UGC 토픽모델링으로 품질 차원 추출.
- Gilardi, Alizadeh & Kubli (2023), *PNAS* — ChatGPT가 텍스트 주석 과업에서 크라우드워커보다 정확. Ziems et al. (2024), *Computational Linguistics* — "Can Large Language Models Transform Computational Social Science?": 과업별 편차 큼, 인간 검증 필요.
- 공통 시사점: LLM 코딩은 저비용·고성능이지만 **(i) 모델 버전 의존, (ii) 프롬프트 민감도, (iii) 체계적 편향** 가능성이 있어 인간 대조와 보정이 필수.

**본 연구의 기여 주장(안)**: 기존 연구는 사전/전통 ML 특성 또는 소수 변수를 사용. 본 연구는 (1) 이론 기반 다차원 코드북을 LLM으로 대규모 코딩, (2) 신뢰도·민감도·측정오차 보정까지 포함한 투명한 절차, (3) 전통 방법 대비 예측 개선(held-out deviance) 비교를 제공.

## 4. 문헌 (C): 계량 방법

- **Count 모형**: Cameron & Trivedi (1998), *Regression Analysis of Count Data*; Hilbe, *Negative Binomial Regression*. 과대산포 검정(Cameron & Trivedi 1990의 보조회귀)과 NB2 사용 근거. 노출시간은 offset으로 처리.
- **군집-강건 표준오차**: 같은 업체/제품 리뷰의 상관을 업체 수준 클러스터링으로 보정.
- **기계 생성 변수의 측정오차**: LLM 코딩 변수를 "관측된 공변량"처럼 쓰면 감쇠편향/오분류 편향이 생김.
  - Angelopoulos et al. (2023), *Science* — Prediction-Powered Inference (PPI): 소수 인간 라벨로 기계 예측 기반 추정량의 편향을 보정하고 타당한 신뢰구간 제공.
  - Egami, Hinck, Stewart & Wei (2023), NeurIPS — Design-based Supervised Learning (DSL): 라벨 추출을 확률표집으로 설계하고 하류 회귀계수의 일관추정.
  - **실행안**: 인간 라벨 300–500건(확률표집)을 확보해 (a) 단순 LLM 변수 회귀, (b) PPI/DSL 보정 회귀를 모두 보고하고 계수 차이를 강건성으로 제시.

## 5. 가설 정리

| 가설 | 예측 (IRR 기준) | 근거 이론 |
|---|---|---|
| H1 | `specificity`, `informativeness` ↑ → IRR > 1 | 진단성 |
| H2 | `sentiment_c²` > 0 (U자), `emotional_intensity` ↑ → IRR > 1 | 각성·극단성 |
| H2b | `argument_balance` ↑ → IRR > 1 | 양면 메시지 신뢰성 |
| H3 | 경험재에서 감정 변수, 탐색재에서 정보 변수의 효과가 더 큼 (상호작용) | 상품 유형 조절 |
| H4 | LLM 변수 모형(M2)의 held-out deviance < 사전 기반(M1) < 통제만(M0) | 측정 품질 |

## 6. 식별 한계(논문 한계 절에 명시)
- 관찰 데이터 → 인과가 아닌 **조건부 연관**. 리뷰 노출 순위(정렬 알고리즘)가 count에 영향(선택/노출 편향): 정렬 기준·최초 노출 위치를 통제하거나 제품 고정효과 사용.
- 별점은 텍스트 감성과 상관이 높음(공선성). 별점 포함/제외 두 사양 보고.
- 가능하면 광고 카피 A/B 실험(클릭 수)으로 인과 검증을 보완.
