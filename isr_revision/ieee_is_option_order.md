# 초안: Option Order Matters as Much as Wording

IEEE Intelligent Systems 버전의 다섯 번째 섹션 초안입니다. 목표 분량은 700단어이고, 본문은 약 710단어입니다. 인용은 템플릿 형식(위첨자 번호)에 맞춰 [n]으로 표시했고, 번호는 전체 원고에서 다시 매겨야 합니다.

---

## OPTION ORDER MATTERS AS MUCH AS WORDING

Every prompt in our task lists the same six options, and only their order changes. Our earlier runs rotated the list by turn number, so every first decision saw the same layout, with "hold" at the top. We reran the goal-visibility design with the list rotated across episodes, so that each wording of each headline appeared equally often with each option in first place. The facts, the payoffs, and the option descriptions were unchanged.

The layout turned out to matter about as much as the headline did (see Figure 3). Averaged over all six layouts, the fast model skipped tests in 17% of first decisions. With a headline that stated the target and "hold" at the top of the list, the model skipped tests in 62% of first decisions. With "rollback" at the top, it skipped in 38%. When a tested fix headed the list, skipping almost disappeared: the model took the small tested fix in 93% of decisions when it was listed first, and in no such decision did it skip. Three of the six layouts accounted for 96% of all skipping.

Layout also changed what the headline did. The goal effect from the previous section was large when a non-progress option (hold or rollback) led the list: 62% against 13% with hold first, and 38% against 1% with rollback first. It was near zero when a tested fix led the list. And it vanished when the untested wide fix was listed first, a layout in which the model skipped in about one-third of decisions whether or not the headline stated the target. Averaged over layouts, stating the target still raised skipping by 16 percentage points, in 13 of 16 wordings, so the goal effect is real. But its size depends on a formatting decision that most prompt designers would not think of as a decision at all.

The effect is not a simple preference for whatever comes first. When the untested wide fix was at the top, the model chose it in only 9% of decisions; it more often took the tested wide fix at the bottom of the list or the untested small fix. Across all layouts, the chosen option was in first place in 29% of decisions, second in 26%, and third in 21%, a mild pull toward the top that does not explain the large swings. What the layout seems to change is which options the model weighs against each other when it is short of time and has been shown a gap to close. Our design identifies the effect of layout, not the process behind it.

Sensitivity to option order is known from multiple-choice benchmarks, where reordering the answers changes how often models pick the correct one [n1], and where much of the bias has been traced to a preference for particular answer labels such as "A" or "B" [n2]. Our setting differs in two ways that matter for practice. The options here are named actions with consequences, not labeled answers, so there is no label to prefer. And the order does not add a constant bias; it interacts with the content of the status message, amplifying the goal effect in some layouts and erasing it in others. A layout chosen once, for convenience, can therefore decide whether an audit finds a problem.

This changes how our earlier results should be read. The layout we used in every earlier first decision, with hold at the top, is the one that produces the most skipping. Taken alone, the hold-first decisions in the balanced run reproduce our earlier estimates closely (62.5% against 62.3% for the gain headline, and 68.8% against 69.2% for the neutral headline with the target added). The estimates in this article average over all six layouts and are smaller. We report both because the difference is itself a finding: an evaluation that fixes one layout measures that layout, not the model.

For organizations, the lesson is that option order belongs in the audit. An operator should be tested with the options in several orders, and results should be reported by layout as well as on average. In deployment, the order in which a runbook or tool list presents actions is part of the control signal; listing a tested option first may be the cheapest guard available.

---

## 메모

### 숫자 출처
모두 `skipver/results/study4_bal__haiku45__s4_bal.jsonl`에서 facts line에 target이 있는 조건(2,400회)입니다. Haiku 4.5, 3턴 남음, 16 wordings × 5 frames × 30 episodes, 순서 균형.

| 문장 | 값 |
|---|---|
| 전체 skip | 17.4% |
| target 헤드라인, hold 맨 위 | 62.1% (target 없는 헤드라인 12.5%) |
| target 헤드라인, rollback 맨 위 | 37.9% (target 없는 헤드라인 1.2%) |
| 검증 없는 wide fix 맨 위 | target 33.8% / target 없음 35.6% |
| small tested fix 맨 위 | 그 선택지를 93% 선택, skip 0% |
| hold·rollback·wide-skip 맨 위 세 배치가 전체 skip에서 차지하는 비중 | 96% |
| wide-skip이 맨 위일 때 그걸 고른 비율 | 9% (tested wide fix 54%, untested small fix 26%) |
| 고른 선택지의 위치 | 1번째 29%, 2번째 26%, 3번째 21% |
| goal effect, 배치 평균 | +16 pp, 16개 wording 중 13개에서 양수 |
| hold 맨 위 조건 vs 원 논문 | gain 62.5 vs 62.3, neutral+target 68.8 vs 69.2 |

"+16 pp"는 Goals, Not Losses 섹션의 대비(neutral+target − neutral = +16.2, loss+target − loss = +16.0)와 같은 값입니다. 이 섹션의 "13 of 16 wordings"는 target 헤드라인 3개를 합친 평균과 target 없는 헤드라인 2개를 합친 평균을 wording별로 비교한 것이라, 앞 섹션과 정의가 조금 다릅니다. 원고에서는 한 가지 정의로 통일하세요.

### 인용 (확인함)
- [n1] P. Pezeshkpour and E. Hruschka, "Large language models sensitivity to the order of options in multiple-choice questions," *Findings of NAACL 2024*, pp. 2006–2017.
- [n2] C. Zheng, H. Zhou, F. Meng, J. Zhou, and M. Huang, "Large language models are not robust multiple choice selectors," *ICLR 2024*. (저자 목록은 원문에서 다시 확인하세요.)

Zheng et al.은 이 편향이 위치보다 "A/B/C" 같은 선택지 라벨 선호에서 주로 온다고 주장합니다. 이 원고의 선택지에는 라벨이 없다는 점이 둘을 구별하는 논거가 됩니다(넷째 단락).

### 일부러 조심한 표현
- 메커니즘을 주장하지 않았습니다 ("What the layout seems to change…", "Our design identifies the effect of layout, not the process behind it").
- 원래 결과가 가장 유리한 배치에서 나왔다는 사실을 리뷰어가 찾기 전에 직접 밝혔습니다 (여섯째 단락).
- "the goal effect is real"은 배치 평균 +16 pp가 99.6% 구간에서도 0을 벗어나기 때문에 쓸 수 있는 표현입니다.
