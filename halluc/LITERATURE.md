# 문헌 조사: 환각의 신뢰성 성장 모형 (주제 1)

조사일 2026-10-28. 웹 검색 결과의 요약만 근거로 했고 원문을 끝까지 읽지는 않았습니다. 인용 전에 원문을 확인해야 합니다. "미확인" 표시는 검색 요약이 서로 다르거나 2차 출처뿐인 항목입니다.

## 1. 가장 가까운 선행연구 (공백을 가르는 기준선)

| 논문 | 내용 | 우리와의 관계 |
| --- | --- | --- |
| [Yang et al. 2025, "Hallucinate at the Last in Long Response Generation"](https://arxiv.org/abs/2505.15291) | 긴 문서 요약에서 환각이 응답 후반부에 몰림. 어텐션·디코딩 원인 분석과 완화 시도 | **위치 효과의 선행 증거.** 우리는 이를 λ(t)로 모형화하고 이질성 대 전염을 구분함 |
| [Tu et al. 2025, "Investigating Factuality in Long-Form Text Generation: The Roles of Self-Known and Self-Unknown"](https://arxiv.org/html/2411.15993v2) (EMNLP 2025) | 원자 주장을 상대 위치로 구간화. 뒤 문장일수록 사실성 하락. 검색 보강으로도 완전히 해결되지 않음 | 같은 방법(원자 주장 + 위치 구간)이라 비교 대상. 위치 구간 평균만 보고하고 **분산·군집은 안 봄** |
| [Zhang et al. 2024, "How Language Model Hallucinations Can Snowball"](https://arxiv.org/abs/2305.13534) (ICML 2024) | 앞선 오류에 일관성을 맞추려고 추가 오류를 냄. 모델은 따로 물으면 상당수를 오류로 식별(GPT-3.5 67%, GPT-4 87%, LLaMA2-70B-chat 94%). 온도·빔서치·CoT로도 안 사라짐 | **전염(자기여기)의 직접 증거.** 단, 질의응답형 과제의 사례 연구이고 점과정 모형·추정은 없음 |

## 2. 측정 도구와 데이터

- [Min et al. 2023, FActScore](https://nips.cc/virtual/2023/79626): 원자 사실 정밀도. ChatGPT 58% 보고, 자동 추정치는 사람 점수와 2% 미만 차이. 우리 파일럿의 판정 방식과 개체 집합(HF `dskar/FActScore`)의 원천.
- [Wei et al. 2024, LongFact / SAFE](https://arxiv.org/abs/2403.18802) (NeurIPS 2024): 2,280개 프롬프트, 38개 주제. SAFE는 사람 주석과 72% 일치, 비용은 20배 이상 저렴. 위키 근거가 없는 주제로 확장할 때 쓸 수 있음.
- 희귀 지식: SeSE 논문(arXiv 2511.16275)이 FActScore 개체와 PopQA로 긴 형식 환각 시험 집합을 만듦. 다만 인기·희귀를 나눠 보고하지는 않음(검색 요약 기준). PopQA 인기도 지표를 희귀도 지표로 쓸 수 있는지 확인 필요.
- 긴 문맥: 문서 질의응답 대규모 연구(arXiv 2603.08274)는 문맥 길이에 따라 날조가 늘고(32K 약 7% → 200K 70% 초과라는 2차 요약) **미확인**, 다른 연구는 대화 400턴·7.5만 토큰까지 안정적이라고 보고. 결과가 엇갈리므로 "긴 문맥" 조건은 가설로 두는 것이 안전함.
- 추론 단계 오류 누적(ProcessBench, PRM 계열)은 이번 검색에서 **다루지 못함**. 별도 조사 필요.

## 3. 모형 쪽 문헌

- **NHPP 신뢰성 성장.** [Goel & Okumoto](https://arxiv.org/pdf/0904.2769)가 NHPP로 결함 과정을 모형화하고 신뢰성·비용 기준의 최적 출시 시점 문제를 처음 정식화. Yamada 등은 시험 노력 함수를 추가. [Huang & Lyu 2005](https://webarchive.lib.cuhk.edu.hk/20221209113932mp_/http://www.cse.cuhk.edu.hk/~lyu/paper_pdf/01546566.pdf)는 고정 시험 예산을 모듈 간에 배분(로지스틱 시험 노력). **모듈 = 우리의 생성 구간**으로 대응시키면 배분 모형의 직접 선행 틀이 됨. Musa-Okumoto는 이번 검색에서 확인 못 함.
- **중요한 차이.** 이 문헌은 시험이 진행될수록 결함 강도가 감소하는 성장 모형이다. 환각은 생성이 길어질수록 강도가 증가할 수 있으므로(§1) 이름은 "신뢰성 성장"이지만 실제로는 감쇠 또는 비단조 형태일 수 있음.
- **자기여기 점과정.** [Laub, Lee 등 서베이(arXiv 2405.10527)](https://arxiv.org/abs/2405.10527)와 [Daw & Pender, "Queues Driven by Hawkes Processes"](https://ar5iv.labs.arxiv.org/html/1707.05143)가 기본 참고. IS 저널(ISR, MISQ)에서 Hawkes를 쓴 사례는 이번 검색에서 **찾지 못함**.
- **검증 병목의 경제학.** [Catalini, Hui, Wu 2026, "Some Simple Economics of AGI"](https://arxiv.org/abs/2602.20946)(워킹페이퍼, 미게재): AI 진보를 값싼 자동화와 비싼 인간 검증의 경주로 모형화. 가장 가까운 경제학 틀이지만 환각의 시간 구조(λ(t), 전염)는 다루지 않음(검색 요약 기준).

## 4. 공백과 포지셔닝

1. 위치·전염의 증거는 각각 있다(Yang, Tu / Zhang). 그러나 **강도 함수와 과대산포를 한 틀에서 추정하고, 이질성과 전염을 통계적으로 구분한 연구**는 이번 검색에서 찾지 못했다. 이것이 측정 기여의 자리.
2. 검증 비용을 모형에 넣은 **구간별 검증 배분의 최적 정책**은 AI 쪽에서는 찾지 못했고, 경제학 쪽은 일반론(Catalini 등)만 확인했다. 이것이 모형 기여의 자리.
3. ISR, Management Science에서 이 조합(LLM 환각 + 검증 배분 모형)의 게재 논문은 이번 검색에서 **확인하지 못했다.** 검색 도구가 INFORMS 사이트를 직접 훑지 못한 탓일 수 있으니, 투고 전에 PubsOnline에서 "LLM", "human oversight", "verification", "hallucination"으로 직접 검색해야 한다.

## 5. 다음에 해야 할 조사

- Tu 등과 Yang 등의 원문에서 분산·군집을 이미 보고했는지 확인(새로움 주장의 핵심).
- ProcessBench, PRM800K 등 추론 단계 오류 데이터와 단계별 오류율 보고 여부.
- INFORMS PubsOnline에서 ISR/Management Science의 AI 오류·감사·인간 검토 모형 논문 직접 검색.
- 감사(auditing)·검사 게임, 정보의 가치, 품질 검사 최적화의 고전 문헌(OR/회계) 정리.
