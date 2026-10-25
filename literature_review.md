# 문헌 조사 1차: 우리 구조가 이미 알려진 결과인가?

> 한계를 먼저 밝힙니다. 웹 검색으로 한 1차 조사이며 INFORMS PubsOnLine, ISR·Management Science·MISQ·JMIS·Marketing Science·SSRN의 체계적 검색이 아닙니다. 아래 "없었다"는 "이 검색에서 찾지 못했다"는 뜻이지 존재하지 않는다는 증명이 아닙니다. 출처 중 일부는 요약·블로그라서 원문 확인이 필요합니다.

## 1. 조각별 판정

| 우리 구조 | 알려진 문헌 | 판정 |
|---|---|---|
| NHPP 신뢰도 모형 + 비용 기반 최적 테스트·출시 시점 | [Okumoto & Goel (1980)](https://scispace.com/authors/amrit-l-goel-2kuu8o7wna)(학술지 확인 필요), 이후 불완전 디버깅·벌칙 비용 등 확장 다수([리뷰](https://www.mecs-press.org/ijmecs/ijmecs-v6-n2/v6n2-7.html)). **IS 저널에도 있음**: Ji, Mookerjee & Sethi (2005) *ISR* 16(3), "Optimal software development: A control theoretic approach"; Chiang & Mookerjee (2004) *ISR* 15, "A fault threshold policy..." (참고문헌 목록으로 확인, 원문 미확인) | **새롭지 않음.** 우리 기여는 이 틀에 "AI의 속도 대 도달"을 넣은 것뿐 |
| 보증·성과 보장이 품질 신호가 됨 | Spence (1977), [Grossman (1981)](https://people.duke.edu/~qc2/BA532/1981%20JLE%20grossman.pdf) (JLE), Lutz 계열; 가격 신호는 Milgrom & Roberts (1986); [Bagwell & Riordan (1991)](https://ideas.repec.org/a/aea/aecrev/v81y1991i1p224-39.html): 고품질이 완전정보 가격보다 *높은* 가격으로 신호. 정리: [Sobel 정리 노트](https://econweb.ucsd.edu/~jsobel/Papers/Signalling) | **메커니즘은 알려져 있음.** 우리 결과에서 H가 단가를 *낮추는* 방향은 "더 큰 보증 제공"과 같은 논리라 일치하지만, 가격 신호의 "높이는" 방향과는 반대라서 설명이 필요 |
| 성과 기반 계약이 사적 정보의 신호가 됨 | [Bakshi, Kim & Savva (2015), *Management Science*](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2014.2029): 판매자가 신제품 신뢰도를 알 때 성과 기반 계약이 신뢰도 신호로 작동 | **가장 가까운 선행연구.** 우리 모형과의 차이를 명확히 해야 함 |
| IT 아웃소싱에서 벤더의 사적 능력 정보 | Shivendu, Zeng & Gurbaxani ([MISQ 요약](https://misq.umn.edu/pub/skin/frontend/default/misq/pdf/Abstracts/12336_RA_ShivenduZeng.pdf)): 벤더의 능력과 노력이 사적 정보 | IS 독자에게 익숙한 틀. 우리의 "도달"은 벤더 능력의 구체적 차원 |
| 생성형 AI 서비스의 가격 이론 (사용량 대 구독 대 결과 기반) | 학술 이론 논문은 찾지 못함. 산업 자료만: 결과 기반 과금의 실제 사례(Intercom Fin 해결 1건당 $0.99 등, [Stripe 사례](https://stripe.com/customers/fin-ai), [flexprice](https://flexprice.io/glossary/outcome-based-pricing-for-ai)), 코딩 도구의 토큰 과금 이동 ([관련 기사](https://www.okoone.com/spark/leadership-management/gartner-says-ai-coding-agents-could-cost-more-than-software-developers/)). 근처 연구: [생성형 AI 동적 가격 진화 게임](https://www.sciencedirect.com/science/article/abs/pii/S0096300325006034) | **빈 칸일 가능성**이 있으나 검색이 얕음. 가장 중요한 확인 대상 |
| AI 효과의 과업·경험 이질성, 보완성 | 실증: [Kreitmeir & Raschky](https://arxiv.org/pdf/2403.01964), 현장 실험 (Cui et al.), McKinsey 보고서에서 복잡한 과업의 시간 절감 감소 (요약). 이론: [NBER w35275](https://nber.org/papers/w35275) (weak-link, 강한 보완성). 과업 기반 AI 모형(Acemoglu 계열) | 방향은 알려진 사실. 우리 기여는 *도달 임계와 시장 배제*로의 연결 |
| 결과 기반 과금의 정의·검증 문제 | 산업 자료가 이미 지적 (결과 판정이 벤더에 유리할 수 있음, 침묵을 해결로 추정) | 알려진 한계. 우리 모형의 확장 항목과 일치 |

## 2. 우리 구조의 새로움에 대한 평가

**새로울 수 있는 부분 (확인 필요)**
1. 속도(b)와 도달(a)을 분리해 AI 테스트 도구의 가치를 도출한 것, 그리고 도달이 사람 수준 미만이면 *장애 비용이 가장 큰 기업이 이탈*한다는 결과(고위험 이탈).
2. 도달 평행선(A=1)에서 도입 집합이 체제 전환하고 규제(책임 강화)의 효과 부호가 도달에 따라 뒤집힌다는 결과.
3. 사용량 과금은 정의상 도달 정보를 전달하지 못하고(수입이 유형과 무관), 결과 과금은 *벤더의 변동 비용(연산)* 이 있을 때만 신호가 된다는 결과, 그리고 복잡한 과업은 어떤 과금 방식으로도 배제된다는 결과.

**이미 알려진 것에 가까운 부분**
- 보증·성과 계약이 신호가 된다는 기본 논리와 분리 균형의 구조(Spence 계열, Bakshi et al.). 우리 결과의 "변동 비용이 있어야 신호가 된다"는 흉내 비용(단일 교차)의 일반 논리와 일치할 가능성이 큽니다.
- 최적 테스트 중단 시점 모형 전반.

**종합**: 각 조각은 선행연구가 있습니다. 조합(AI 서비스 시장, 도달·속도의 분리, 사용량 대 결과 과금, 복잡도에 따른 배제)이 새로울 *가능성*은 있으나, 이 검색으로는 확정할 수 없습니다.

## 3. ISR 투고 판단에 주는 의미

- **긍정**: IS 저널에 소프트웨어 개발·테스트의 경제학이 실려 온 선례(Ji et al. 2005, Chiang & Mookerjee 2004)가 있어 *독자층 적합성*은 있습니다. 결과 기반 과금과 벤더 사적 정보는 IS의 IT 아웃소싱·벤더 계약 문헌과 닿습니다.
- **부정**: 기초 모형이 고전이고 신호 메커니즘이 표준이어서, 기여는 "AI 서비스 시장이라는 새 맥락에서의 구체적 예측"에 있어야 합니다. 예측이 선행연구의 일반 결과에서 쉽게 따라 나온다면 신규성이 약합니다.
- 가장 가까운 선행연구(Bakshi et al. 2015, *Management Science*)와의 차이를 정면으로 설명해야 합니다. 차이 후보: (i) 도달과 복잡도의 이질성, (ii) 사용량 계약이 신호 불능이라는 대비, (iii) 시장 배제 결과, (iv) AI 서비스 특유의 연산 변동 비용.

## 4. 다음 단계 (체계적 검색 계획)

1. **검색 DB**: INFORMS PubsOnLine (ISR, Management Science, Marketing Science), MISQ, JMIS, Google Scholar, SSRN, arXiv(econ.TH, cs.GT).
2. **검색어 묶음**: (a) "performance-based contract" OR "outcome-based pricing" + "signaling" + "private information"; (b) "usage-based pricing" + "AI" OR "LLM" + "adoption threshold"; (c) "software testing" + "release" + "game" OR "vendor" OR "outsourcing"; (d) "AI capability" + "task complexity" + "adoption" + "model".
3. **읽을 순서**: Bakshi–Kim–Savva (2015) → Ji–Mookerjee–Sethi (2005) → Chiang–Mookerjee (2004) → NBER w35275 → 생성형 AI 가격 이론 논문(있다면).
4. **판정 기준**: 각 논문에 대해 "우리 명제가 이 논문의 일반 결과에서 따라 나오는가"를 표로 확인.
5. 확정 전에는 신규성 주장을 논문에 쓰지 않는다.
