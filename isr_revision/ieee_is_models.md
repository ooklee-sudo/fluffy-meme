# 초안: Which Models Skip

IEEE Intelligent Systems 버전의 일곱 번째 섹션 초안입니다. 목표 분량은 350단어 + 표 1(300단어로 계산)입니다. 앞 섹션 마지막 문장("The combination brought the fast model to the behavior of the larger models in the next section")을 이어받습니다. 숫자는 모두 3턴 남음, 헤드라인 3개(loss, gain, neutral) × 16 wordings 설계입니다.

---

## WHICH MODELS SKIP

We ran the same three-turn task, with the options in all six layouts, on 11 models: four tiers of one commercial family and seven small models from five other vendors (see Table 1). Two findings stand out.

First, the larger and newer models in the commercial family did not skip tests under any headline or layout. Neither did the newest small model of that family. These models chose a tested fix in 92% to 100% of decisions and otherwise held. For them, our question has no answer to estimate: they show a floor, not evidence that wording or layout is harmless.

Second, most small models skipped some of the time, and the layout that set them off differed by model. The fast model from our main analyses skipped most when hold led the list. A small model from a second vendor skipped at the same overall rate, 13%, but never with hold first; it skipped in 65% of decisions when the untested wide fix led the list. Another skipped only when the untested small fix came first. An evaluation that fixed one layout, the hold-first layout for instance, would have ranked these models in nearly the opposite order from the one the balanced design gives. Size and recency were no reliable guide either: the newer of the two models from the second vendor skipped about three times as often as the older one.

Where small models skipped, the direction of the headline effect usually held. In six of the seven small models that skipped at all, the progress headline, which names the target, produced more skipping than the loss headline. The differences were often small, and one model showed none.

For an organization choosing an operator, the table carries two lessons. A capable model can remove the problem in this task, but the cheaper models that cost pressure favors do not behave alike, and a single test layout can make a risky model look safe.

### TABLE 1. Share of first decisions that skip tests, three turns left.

| Model | Balanced layouts | Hold listed first | Range across the six layouts | Progress vs. loss headline |
|---|---|---|---|---|
| Claude Haiku 4.5 | 12.8% | 31.2% | 0–31% | 22.3% vs. 6.9% |
| Gemini 3.1 Flash-Lite | 12.9% | 0.0% | 0–65% | 22.7% vs. 3.5% |
| Ministral-8B | 5.4% | 1.2% | 0–28% | 7.9% vs. 4.4% |
| Llama-3.1-8B | 4.7% | 3.8% | 1–8% | 4.2% vs. 5.2% |
| Gemini 2.5 Flash-Lite | 4.2% | 6.2% | 0–15% | 10.0% vs. 0.8% |
| Gemma-3-12B | 2.2% | 0.0% | 0–13% | 3.8% vs. 2.3% |
| Qwen3-14B | 1.7% | 0.4% | 0–8% | 4.0% vs. 0.4% |
| GPT-5-nano | 0.2% | 0.4% | 0–0.4% | 0.6% vs. 0.0% |
| Claude Haiku 5.5 | 0 of 1,440 | 0 | – | – |
| Claude Sonnet 5.5 | 0 of 288 | 0 | – | – |
| Claude Opus 5.5 | 0 of 288 | 0 | – | – |
| Claude Fable 5.1ᵃ | 0 of 4,320 | 0 | – | – |

Note: 1,440 first decisions per model (16 wordings × 3 headlines × 30) unless shown; Sonnet 5.5 and Opus 5.5 were run with 6 decisions per cell. Options were rotated so that each appears first equally often. ᵃRun with hold listed first only.

---

## 메모

### 원 논문(고정 배치)과의 비교

| 모델 | 원 논문, 고정 배치 | 순서 균형 | 바뀐 판정 |
|---|---|---|---|
| Claude Haiku 4.5 | 27.2% | 12.8% | skip, 크기 절반 |
| **Gemini 3.1 Flash-Lite** | **0.0% (floor)** | **12.9%** | **floor → Haiku와 같은 수준** |
| Ministral-8B | 4.0% (screen 미통과) | 5.4% | screen 기준(5%) 통과 |
| Llama-3.1-8B | 2.4% | 4.7% | 비슷 |
| Gemini 2.5 Flash-Lite | 17.2% (유일하게 통과) | 4.2% | 크기 1/4 |
| **Gemma-3-12B** | **0.0% (floor)** | **2.2%** | floor → 드물게 skip |
| Qwen3-14B | 무효 (출력 비어 있음) | 1.7% | 이번에는 유효 (출력 한도 4,000토큰) |
| GPT-5-nano | 무효 (출력 비어 있음) | 0.2% | 이번에는 유효 |
| Claude Sonnet 5.5, Opus 5.5 | 0% | 0% | 동일 |

원 논문 Study 6의 결론("7개 소형 모델 중 1개만 skip")은 순서 균형 하에서는 "8개 소형 모델 중 7개가 가끔 skip하고, 모델마다 skip을 유발하는 배치가 다르다"로 바뀝니다.

### 숫자 출처
- Haiku 4.5: `study2_bal__haiku45__bal.jsonl` (3턴)
- Gemini 2.5 Flash-Lite: `study6_bal__gemini25fl__bal.jsonl`
- Haiku 5.5, Sonnet 5.5: `floor_bal__*.jsonl`
- 나머지: `screen_bal__*__bal.jsonl`
- Fable 5.1: 원 논문 Study 2 (고정 배치만, 순서 균형 재실행 안 함, 약 $7)

### 본문 문장 근거
- "13%, but never with hold first; 65% when the untested wide fix led": Gemini 3.1 Flash-Lite, hold 0.0%, wide_skip 65.0% (gain 100%, neutral 73.8%, loss 21.2%).
- "Another skipped only when the untested small fix came first": Gemma-3-12B, narrow_skip 맨 위 12.9%, 나머지 배치 0–0.4%.
- "nearly the opposite order": hold 맨 위 기준 순위는 Haiku 4.5(31%) > Gemini 2.5 FL(6%) > Llama(4%) > … > Gemini 3.1 FL(0%) = Gemma(0%). 순서 균형 순위는 Gemini 3.1 FL ≈ Haiku 4.5 > Ministral > Llama > Gemini 2.5 FL > Gemma. 특히 Gemini 3.1 FL이 꼴찌에서 1위가 됩니다. "nearly the opposite"가 과하다고 느끼면 "a very different order"로 바꾸세요.
- "about three times as often": Gemini 3.1 FL 12.9% vs 2.5 FL 4.2%.
- "six of the seven small models that skipped at all": GPT-5-nano(0.2%, 3회)는 사실상 skip하지 않는 것으로 보고 제외. 나머지 7개 중 Llama만 progress < loss (4.2 vs 5.2).

### 조심할 점
- **이 섹션은 헤드라인 3개 설계라 goal effect(쌍 비교)를 직접 보여주지 못합니다.** 그래서 "progress vs. loss"만 비교했고, 이 대비가 target과 표현 차이를 섞는다는 점은 Goals 섹션에서 이미 설명했습니다.
- **Sonnet 5.5와 Opus 5.5는 셀당 6회(288회)만 돌렸습니다.** 0/288의 95% 상한은 약 1%입니다. 표 주석에 명시하거나, 필요하면 셀당 30회로 늘리세요(Sonnet 약 $7, Opus 약 $14).
- **Fable 5.1만 고정 배치입니다.** 표 주석(ᵃ)으로 표시했습니다. 다른 큰 모델이 순서와 무관하게 0%였으니 결론이 바뀔 가능성은 낮지만, 통일하려면 셀당 6회로 약 $7입니다.
- 큰 모델 4개의 선택: Haiku 5.5는 tested fix 92.5%·hold 7.5%, Sonnet 5.5는 tested fix 99.7%, Opus 5.5는 100%.
- 모델명이 한 회사(Claude)에 몰려 있어서 "the commercial family"로 썼습니다. 저자 소속과 이해관계 공개 규정이 있으면 확인하세요.
