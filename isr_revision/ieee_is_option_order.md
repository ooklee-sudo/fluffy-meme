# 초안: Option Order Matters as Much as Wording

IEEE Intelligent Systems 버전의 다섯 번째 섹션 초안입니다. 목표 분량은 700단어이고, 본문은 약 720단어입니다. 인용은 템플릿 형식(위첨자 번호)에 맞춰 [n]으로 표시했고, 번호는 전체 원고에서 다시 매겨야 합니다.

---

## OPTION ORDER MATTERS AS MUCH AS WORDING

Every prompt in our task lists the same six options; only their order can change. A fixed layout, as is common in such evaluations, would show every decision the options in the same order. We instead rotated the list across episodes, so that each wording of each headline appeared equally often with each option in first place. The facts, the payoffs, and the option descriptions were unchanged.

The layout turned out to matter about as much as the headline did (see Figure 3). Averaged over all six layouts, the fast model skipped tests in 17% of first decisions. With the target added to the headline and "hold" at the top of the list, the model skipped tests in 55% to 69% of first decisions; with "rollback" at the top, in 24% to 48%. When a tested fix headed the list, skipping almost disappeared: the model took the small tested fix in 93% of decisions when it was listed first, and in no such decision did it skip. Three of the six layouts accounted for 96% of all skipping.

Layout also changed what the headline did. The goal effect from the previous section, the rise in skipping when the target sentence is added to a neutral or a loss headline, was large when a non-progress option led the list. With hold first, adding the target raised skipping from 15% to 69% under neutral text and from 10% to 55% under loss text; with rollback first, from 3% to 24% and from 0% to 48%. The effect was near zero when a tested fix led the list. It vanished when the untested wide fix was listed first, a layout in which the model skipped in about one-third of decisions under every headline. Averaged over layouts, adding the target raised skipping by 16 percentage points under both neutral and loss text, in 14 and 13 of 16 wordings, so the goal effect is real. But its size depends on a formatting decision that most prompt designers would not think of as a decision at all.

The effect is not a simple preference for whatever comes first. When the untested wide fix was at the top, the model chose it in only 9% of decisions; it more often took the tested wide fix at the bottom of the list or the untested small fix. Across all layouts, the chosen option was in first place in 29% of decisions, second in 26%, and third in 21%, a mild pull toward the top that does not explain the large swings. What the layout seems to change is which options the model weighs against each other when it is short of time and has been shown a gap to close. Our design identifies the effect of layout, not the process behind it.

Sensitivity to option order is known from multiple-choice benchmarks, where reordering the answers changes how often models pick the correct one [n1], and where much of the bias has been traced to a preference for particular answer labels such as "A" or "B" [n2]. Our setting differs in two ways that matter for practice. The options here are named actions with consequences, not labeled answers, so there is no label to prefer. And the order does not add a constant bias; it interacts with the content of the status message, amplifying the goal effect in some layouts and erasing it in others. A layout chosen once, for convenience, can therefore decide whether an audit finds a problem.

This matters for how fixed-layout evaluations should be read. A natural design, rotating options by turn number, shows every first decision the same layout, with hold at the top, and that layout produces the most skipping. Measured on hold-first decisions alone, adding the target raised skipping by 54 points under neutral text, more than three times the 16-point average over layouts. An evaluation that fixes one layout measures that layout, not the model.

For organizations, the lesson is that option order belongs in the audit. An operator should be tested with the options in several orders, and results should be reported by layout as well as on average. In deployment, the order in which a runbook or tool list presents actions is part of the control signal; listing a tested option first may be the cheapest guard available.

---

## 메모

### 숫자 출처
모두 `skipver/results/study4_bal__haiku45__s4_bal.jsonl`에서 facts line에 target이 있는 조건(2,400회)입니다. Haiku 4.5, 3턴 남음, 16 wordings × 5 frames × 30 episodes, 순서 균형.

| 문장 | 값 |
|---|---|
| 전체 skip | 17.4% |
| hold 맨 위, target을 더한 헤드라인 | neutral+target 68.8%, loss+target 55.0% |
| rollback 맨 위, target을 더한 헤드라인 | neutral+target 23.8%, loss+target 47.5% |
| goal effect (쌍 비교), hold 맨 위 | neutral 15.0 → 68.8 (+53.8), loss 10.0 → 55.0 (+45.0) |
| goal effect (쌍 비교), rollback 맨 위 | neutral 2.5 → 23.8 (+21.2), loss 0.0 → 47.5 (+47.5) |
| goal effect (쌍 비교), 검증 없는 wide fix 맨 위 | neutral +11.2, loss −2.5 (모든 헤드라인에서 약 1/3이 skip) |
| goal effect (쌍 비교), 배치 평균 | neutral +16.2 [+8.8, +24.0], 14/16 wording 양수; loss +16.0 [+7.5, +25.4], 13/16 |
| small tested fix 맨 위 | 그 선택지를 93% 선택, skip 0% |
| hold·rollback·wide-skip 맨 위 세 배치가 전체 skip에서 차지하는 비중 | 96% |
| wide-skip이 맨 위일 때 그걸 고른 비율 | 9% (tested wide fix 54%, untested small fix 26%) |
| 고른 선택지의 위치 | 1번째 29%, 2번째 26%, 3번째 21% |

**대비 정의**: goal effect는 Goals, Not Losses 섹션과 같은 쌍 비교(neutral+target − neutral, loss+target − loss)로 통일했습니다. gain 헤드라인은 target도 말하지만 문장 자체가 달라서, 목표 효과를 분리하는 대비에서는 뺐습니다.

**"our earlier runs" 제거**: ISR 원고가 공개되지 않았으므로 1·6단락에서 이전 실행 언급을 빼고, 고정 배치를 일반적인 설계로 서술했습니다. "as is common in such evaluations"는 근거 인용 없이 쓴 표현이라, 리뷰어가 물으면 [n1], [n2]처럼 고정 순서로 선택지를 제시한 평가 연구를 예로 들 수 있게 준비해 두세요.

### 인용 (확인함)
- [n1] P. Pezeshkpour and E. Hruschka, "Large language models sensitivity to the order of options in multiple-choice questions," *Findings of NAACL 2024*, pp. 2006–2017.
- [n2] C. Zheng, H. Zhou, F. Meng, J. Zhou, and M. Huang, "Large language models are not robust multiple choice selectors," *ICLR 2024*. (저자 목록은 원문에서 다시 확인하세요.)

Zheng et al.은 이 편향이 위치보다 "A/B/C" 같은 선택지 라벨 선호에서 주로 온다고 주장합니다. 이 원고의 선택지에는 라벨이 없다는 점이 둘을 구별하는 논거가 됩니다(넷째 단락).

### 일부러 조심한 표현
- 메커니즘을 주장하지 않았습니다 ("What the layout seems to change…", "Our design identifies the effect of layout, not the process behind it").
- 고정 배치(hold가 맨 위)가 효과를 3배 넘게 부풀린다는 점을 일반적인 경고로 서술했습니다 (여섯째 단락).
- "the goal effect is real"은 배치 평균 +16 pp가 99.6% 구간에서도 0을 벗어나기 때문에 쓸 수 있는 표현입니다.
