# M&SOM 초안: 그림과 캡션

그림 생성: `python sim/make_figures.py` (numpy, matplotlib 필요). 출력은 `figures/`에 PNG(200dpi)와 PDF(벡터). 팔레트는 dataviz 스킬의 기준 팔레트이고 검증 스크립트를 통과했다 (범주 2색 통과, 범주 3색 전 쌍 통과, 순서형 파랑 램프 통과). 검증에서 aqua는 밝은 표면 대비 대비가 3:1 미만이라는 경고가 있어 그림 2에서는 칸마다 글자 레이블을 붙였다 (색만으로 구분하지 않음). 그림 2의 빗금은 색과 별개의 보조 부호화다.

비용 파라미터는 모두 **예시 값**이다: 걸음 비용 k=1, 오류 비용 c=5, 완료 확률 q=0.06, 오류율 μ=0.054, 인계 비용 H=40 (그림 1), 검토자 작업 비용 h=20, 지연 비용 ω=10 (그림 3). 일반 결과가 아니라 구조를 보여 주는 그림으로 쓸 것.

---

## Figure 1. The firm's count threshold falls as errors become more harmful
파일: `figures/fig1_threshold.{png,pdf}`

**Caption.** *Optimal number of errors after which the firm hands the task to a person (Proposition 1), as a function of the probability θ_w that an error leads to a wrong output, for two costs of a wrong output (F = 60, 100). Hand-off cost H = 40; other costs are illustrative. Horizontal bars mark the estimated θ_w of each agent after a misleading message in customer service; the ends of each bar are the additive and the model-consistent estimates (Section 5). For GPT-6.1-terra θ_w is indistinguishable from zero and no count rule is warranted. N\* is capped at 12 in the plot.*

상태: 명제 1의 닫힌 형식에서 계산 (가치 반복과 일치, `sim/table4_two_component.py`). 에이전트 구간은 두 추정기의 양 끝점이고 신뢰구간이 아님.

## Figure 2. Which control portfolio is best as the cost of reaching a person varies
파일: `figures/fig2_portfolio.{png,pdf}`

**Caption.** *Best portfolio as the cost H of handing a task to a person and the fixed cost K of verifying outputs vary (Proposition 3). Colors give the escalation policy (E: always hand off; C: count rule; N: never hand off); hatching marks that output verification is adopted. Verification detects a derailed output with probability 0.8 and turns the cost of an undetected wrong output (100) into a repair cost (30). Probability that an error derails the task θ_w = 0.12 (the estimate for Claude Sonnet 5.5). Illustrative costs.*

상태: 수치 (명제 3의 방향과 일치). 직접 조작 실험으로 검증하지 않았음을 본문에 명시. 이 그림은 자기 인계가 없는 사슬로 계산했다 (θ_h의 영향은 2차 효과이므로 지도는 거의 바뀌지 않는다고 판단했으나, 두 성분 모형으로 다시 계산해 확인할 것).

## Figure 3. A rule based on the observed wait hands off too many tasks
파일: `figures/fig3_average_wait.{png,pdf}`

**Caption.** *(a) Share of tasks handed to a person under the system optimum and under a rule that treats the average observed wait as the price of a hand-off, as the arrival rate of tasks grows; one reviewer with service rate 1 and delay cost 10 per unit time (Proposition 4). (b) Cost of the average-wait rule relative to the system optimum when the same total capacity is split across 1, 2, 5, or 10 reviewers (Allen–Cunneen approximation for arrival variability equal to 1, queueing delay only). The curves are not smooth because the number of errors at which the rule hands off is an integer. In this example pooling raises the loss in most but not all cases: averaged over arrival rates of 2 or more the loss is 11.9%, 13.7%, 16.7%, and 19.2% for 1, 2, 5, and 10 reviewers, and the loss exceeds the one-reviewer loss at 94% of the arrival rates tried. θ_w = 0.29, F = 100, reviewer working cost h = 20; illustrative.*

상태: 명제 4는 증명 (큐 볼록성 가정, `msom_reframing.md` §8). 손실 크기와 풀링 효과는 **수치 예시**. 응용이지 새 원리가 아님 (Naor 1969, Wang & Rachev 2026). θ_w=0.29는 앞선 모형의 DeepSeek 유형 값이므로 새 θ_w 추정과 맞춰 다시 그릴지 결정할 것.

## Figure 4. What a misleading tool message does
파일: `figures/fig4_two_channels.{png,pdf}`

**Caption.** *Customer service (τ²-bench), misleading message versus no injected error. (a) Share of runs in which the agent transfers the task to a person. (b) Probability that a misleading message leads to a self-transfer (θ_h) or to a wrong output (θ_w). Dots and lines: model-consistent split with 95% task-clustered bootstrap intervals; open diamonds: additive split (Section 5.3). For GPT-6.1-terra almost all of the fall in success is self-transfer; for Claude Sonnet 5.5 it is wrong output; for DeepSeek-V3.1 the split of the wrong-output channel depends on the estimator. Llama agents are omitted because their control success is too low to separate the channels.*

상태: 기존 런 로그의 사후 탐색 분석 (`sim/table4_two_component.py`). 한 에이전트의 인계율 증가를 일반화하지 말 것.

---

## 남은 그림 작업
1. 그림 3을 두 성분 모형의 θ_w 추정과 맞춘 파라미터로 다시 그릴지 결정 (현재는 θ_w=0.29).
2. 그림 2를 θ_h가 있는 모형으로 다시 계산해 지도가 바뀌지 않는지 확인.
3. 비용 파라미터를 실제 콜센터 수치나 산업 보고서에서 근거를 찾아 고정.
4. 저널 양식(흑백 인쇄)에서 읽히는지 점검: 그림 1은 선 두께와 직접 레이블로 구분, 그림 4는 색에 더해 위치(행)로 구분, 그림 2는 글자 레이블과 빗금으로 구분됨.
