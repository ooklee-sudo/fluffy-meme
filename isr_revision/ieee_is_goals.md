# 초안: Goals, Not Losses

IEEE Intelligent Systems 버전의 네 번째 섹션 초안입니다. 목표 분량은 750단어입니다. 바로 다음 섹션(Option Order Matters)이 "the goal effect from the previous section"으로 이어받으므로, goal effect의 정의(쌍 비교)를 여기서 처음 세웁니다. 숫자는 모두 순서 균형 데이터이고, 인용은 [n]으로 표시했습니다.

---

## GOALS, NOT LOSSES

Two familiar accounts predict that a status message can push an operator toward shortcuts, and they point at different messages. The first comes from prospect theory: a decision maker who sees an outcome as a loss becomes more willing to gamble [n3], and in sequences of bets this appears as chasing losses to get back to even [n4]. On this account, the risky message is "the last update cost us two points." The second comes from research on goal setting: specific, visible targets raise effort but also invite corner cutting when the target is hard to reach [n5], [n6]. On this account, the risky message is "eight points remain to the target." An organization writing status messages for an AI operator needs to know which, if either, holds.

Time pressure turned out to be a precondition for both. With twelve turns left, the fast model (Claude Haiku 4.5) never skipped tests in 1,440 first decisions; with six turns left it skipped once. With three turns left, it skipped in 13% of first decisions. All results below use three turns left.

We first tested the loss account as we had preregistered it, with three small models at twelve turns left: describing the last result as a loss did not raise skipping by the preregistered margin in any of them (details are in the supplementary material). Because the commercial model never skipped at twelve turns, that test was limited.

Earlier framing studies often confound them. A "progress toward the goal" headline both drops the language of loss and names the target, so a difference between it and a loss headline cannot say which change mattered. We therefore crossed the two. Starting from a neutral status headline and a loss headline, we added the same target sentence to each, which gave four headlines: neutral, loss, neutral plus target, and loss plus target. We also kept the original progress headline. Each headline was written in 16 independently generated wordings, and the facts line below it, which included the target and the gap, was identical across headlines.

The target sentence mattered and the loss language did not (see Figure 2). Adding the target to a neutral headline raised skipping from 9% to 25%, and adding it to a loss headline raised it from 7% to 23%. Both increases are about 16 percentage points, with 95% intervals over wordings that exclude zero, and they appear in 14 and 13 of the 16 wordings, respectively. Describing the last result as a loss, by contrast, made no measurable difference: the loss headline differed from the neutral one by −2 points without the target and by −2 points with it, with wordings split in both directions. Loss language did not make the operator bolder, and it did not make it more careful either. The original progress headline (22%) was indistinguishable from the neutral headline with the target added (25%), so its effect in earlier framing designs is better read as an effect of naming the target than of positive wording.

The target needed to be visible somewhere. When we removed the target and the gap from the facts line as well, so that the prompt mentioned no target at all, the neutral and loss headlines produced no skipping in 960 first decisions. Adding the target sentence back into the headline restored some skipping (6% and 5%), less than when the target appeared in both places. When the target appeared only in the headline, its phrasing also mattered: the progress headline, which leads with the remaining gap, produced 16%, about three times as much as a status sentence followed by the target.

A small model from a second vendor, Gemini 2.5 Flash-Lite, skipped far less often (5% at three turns left) but leaned the same way. Adding the target to a loss headline raised skipping by 7 points, adding it to a neutral headline raised it by 2 points with an interval that includes zero, and loss language again did not raise skipping.

The pattern fits the goal account better than the loss account, and it parallels what goal-setting research reports for people: a visible gap under a deadline invites the agent to trade a safeguard for speed [n5], [n6]. We do not claim that the model holds a goal in any psychological sense, and our design does not reveal how the target sentence changes the choice. The practical claim is narrower: in this task, the sentence that names the target, not the sentence that names the loss, is the one that moves an AI operator toward skipping its tests.

---

## 메모

### 숫자 출처 (Haiku 4.5, 3턴 남음, 순서 균형, 16 wordings × 30 episodes)

| 문장 | 값 | 파일 |
|---|---|---|
| 12턴 / 6턴 / 3턴 skip | 0/1,440 · 1/1,440 · 184/1,440 (12.8%) | `study2_bal__haiku45__bal.jsonl` |
| neutral → neutral+target | 9.2% → 25.4%, +16.2 [+8.8, +24.0], 14/16 | `study4_bal__haiku45__s4_bal.jsonl`, facts에 target 있음 |
| loss → loss+target | 7.3% → 23.3%, +16.0 [+7.5, +25.4], 13/16 | 같음 |
| loss − neutral (target 없음) | −1.9 [−7.5, +3.3], wording 6개 양수 / 5개 음수 | 같음 |
| loss+target − neutral+target | −2.1 [−9.6, +4.6], 5 / 7 | 같음 |
| gain vs neutral+target | 21.7% vs 25.4%, −3.8 [−11.2, +4.0] | 같음 |
| prompt 어디에도 target 없음 | neutral 0%, loss 0% (각 480회, 합 960회) | facts에서 target 제거 |
| target이 헤드라인에만 | neutral+target 6.0%, loss+target 4.8%, gain 16.2% | 같음 |
| gain − neutral+target (헤드라인에만) | +10.2 [+4.6, +16.2], 13/16 | 같음 |
| Flash-Lite | 3턴 skip 4.2–4.6%; loss+target − loss +7.1 [+3.5, +10.6]; neutral+target − neutral +2.3 [−1.9, +6.9]; loss − neutral −1.7 [−4.2, 0.0] | `study6_bal__gemini25fl__*.jsonl` |

### Study 1 서술에 관해
셋째 단락은 사전등록 검증을 두 문장으로 줄인 것입니다. Study 1은 원래 순서(hold가 맨 위)로 돌렸고 순서 균형 재실행을 하지 않았습니다. 12턴에서 Haiku가 0%였고 Qwen과 SmolLM의 결과는 순서와 무관하게 사전등록 기준(10 pp 이상, Holm 보정 후 유의)을 넘지 못했으므로, "did not raise skipping by the preregistered margin in any of them"은 순서를 섞어도 바뀌지 않을 가능성이 높습니다. 그래도 보충자료에 "Study 1 used a fixed layout"을 명시하세요. 사전등록을 공개하지 않았거나 익명 심사에서 링크를 줄 수 없다면 "preregistered"라는 단어를 쓸지 편집 정책을 확인하세요.

### 인용
- [n3] Kahneman & Tversky 1979 (또는 Tversky & Kahneman 1981 중 하나만, 참고문헌 20개 제한)
- [n4] Thaler & Johnson 1990
- [n5] Schweitzer, Ordóñez & Douma 2004
- [n6] Ordóñez et al. 2009

### 다음 섹션과의 연결
Option Order 섹션 첫 문장 "The goal effect from the previous section, the rise in skipping when the target sentence is added to a neutral or a loss headline"과 정의가 맞습니다. 두 섹션 모두 "16 percentage points … in 14 and 13 of 16 wordings"를 같은 값으로 씁니다.

### 생략한 것
- 99.6% 구간과 분산 분해: 보충자료로.
- Study 5(기대값 표시)는 What Reduces Skipping 섹션에서.
- Flash-Lite의 target을 헤드라인에만 둔 조건: 효과가 작아(+2–3 pp) 본문에서 뺐습니다.
