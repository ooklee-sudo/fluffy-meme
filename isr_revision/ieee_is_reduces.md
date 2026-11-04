# 초안: What Reduces Skipping

IEEE Intelligent Systems 버전의 여섯 번째 섹션 초안입니다. 목표 분량은 450단어입니다. 앞의 두 섹션(Goals, Not Losses와 Option Order Matters)에 이어서, principal이 바꿀 수 있는 설정 중 무엇이 skip을 줄이는지를 다룹니다. 숫자는 모두 Haiku 4.5, 3턴 남음, 순서 균형 데이터입니다.

---

## WHAT REDUCES SKIPPING

The settings that raise skipping are chosen by whoever deploys the operator, and so are the settings that lower it. We tested two that a deployer can change without retraining anything: letting the model reason before it answers, and telling it the expected value of each option. A third, the order of the options, was covered in the previous section.

Extended reasoning helped, but less than one might hope. With a reasoning budget of 2,000 tokens, the fast model spent about 730 tokens on each decision and skipped tests in 8% of first decisions, down from 13% without reasoning. The reduction appeared in 11 of 16 wordings, and its 95% interval over wordings (−8 to −2 points) excludes zero. The target headline remained the riskiest: with reasoning, the gain headline produced 13% skipping against 5% for the loss headline and 6% for the neutral one. Reasoning also changed where skipping came from. Without it, almost all skipping occurred when hold, rollback, or the untested wide fix led the list; with it, skipping was spread more evenly and appeared even when a tested fix was listed first. Reasoning made the operator less sensitive to layout, not immune to the goal.

Stating expected values helped more. When each option's description ended with its expected change in quality, for example "Expected quality change: −0.35 points" for the untested small fix, skipping fell from 17% to 5% averaged over the five headlines of the goal-visibility design, and it fell in every one of the 16 wordings. The untested wide fix, the option with the worst expected value, was never chosen. Yet skipping did not disappear, and what remained was concentrated: almost all of it came from layouts with hold at the top, where the operator still skipped in 32% of decisions under headlines that stated the target. An operator that is told, in numbers, that a shortcut is worse can still take it when the goal is in view and the layout points away from the tested option.

Neither setting works fully alone, but together they did. When the fast model both reasoned and saw expected values, it did not skip tests in any of 2,400 first decisions, under every headline and in every layout, including the hold-first layouts where expected values alone had left a third of goal-stating decisions skipping. It reasoned somewhat longer than with reasoning alone (about 900 tokens per decision) and mostly chose the tested wide fix (86% of decisions). The combination brought the fast model to the behavior of the larger models in the next section. For a deployer, this is the most actionable result in the study: two configuration changes, neither of which requires a different model, removed the shortcut in this task.

---

## 메모

### 숫자 출처

| 문장 | 값 | 파일 |
|---|---|---|
| thinking 없음 / 있음 | 12.8% / 8.0% | `study2_bal__haiku45__bal.jsonl` (3턴), `study3_bal__haiku45_think__bal.jsonl` |
| reasoning 토큰 평균 | 733 (thinking), 0 (없음) | 같음 |
| thinking의 효과 (wording별) | −4.8 pp [−7.8, −1.9], 16개 중 11개에서 감소, 4개에서 증가 | 같음 |
| thinking 하의 frame별 skip | gain 12.7%, loss 5.2%, neutral 6.0% | 같음 |
| 맨 위 선택지별 skip, thinking 없음 | hold 31.2, rollback 16.2, wide_skip 29.2, 나머지 0 | 같음 |
| 맨 위 선택지별 skip, thinking 있음 | hold 15.8, rollback 15.4, narrow_patch 7.9, wide_skip 4.2, narrow_skip 2.5, wide_patch 2.1 | 같음 |
| 기대값 없음 / 있음 | 17.4% / 5.0% (5 frames, facts에 target 있음) | `study4_bal__haiku45__s4_bal.jsonl`, `study5_bal__haiku45__s5_bal.jsonl` |
| 기대값 효과 (wording별) | −12.4 pp [−15.1, −9.6], 16개 wording 모두 감소 | 같음 |
| 기대값 표시 후 wide_skip 선택 | 0% (선택은 narrow_patch 52%, wide_patch 43%, narrow_skip 5%) | 같음 |
| 기대값 표시 후 맨 위 선택지별 skip | hold 26.2%, wide_skip 3.5%, 나머지 0% | 같음 |
| 기대값 표시, target 헤드라인, hold 맨 위 | 31.7% | 같음 |
| **thinking + 기대값 + 순서 균형** | **0/2,400 (0.0%)**, 모든 헤드라인·배치에서 0 | `combo_bal__haiku45_think__combo.jsonl` |
| 위 조건의 reasoning 토큰 평균 | 902 | 같음 |
| 위 조건의 선택 | wide_patch 86.1%, narrow_patch 13.3%, hold 0.6% | 같음 |
| 기대값만 대비 감소 (wording별) | −5.0 pp [−6.8, −3.4], 16개 모두 감소 | 같음 |

### 해석에서 조심한 점
- **비교 조건이 다릅니다.** thinking 비교는 3개 헤드라인(Study 2·3 설계), 기대값 비교는 5개 헤드라인(Study 4·5 설계)이라 기준선이 13%와 17%로 다릅니다. 본문에서 각각의 기준선을 밝혔습니다.
- **thinking과 temperature가 같이 바뀝니다.** thinking을 켜면 temperature를 지정할 수 없어 기본값으로 돌아갑니다(원고 Study 3과 같은 한계). 보충자료나 Limitations에 한 줄 넣으세요.
- **세 설정을 함께 켠 조건을 돌렸습니다** (thinking + 기대값, 순서 균형). skip이 0/2,400이라 배치를 따로 고정할 필요가 없었습니다. 마지막 단락을 이 관찰 결과로 바꿨습니다. 0%는 floor라서 이 조건에서 frame 효과는 "측정 불가"이지 "없음"이 아닙니다.
- **0/2,400의 의미**: 진짜 skip 비율의 95% 상한은 약 0.15%입니다(3/n 규칙).
- **기대값 문구가 단서 역할을 할 수 있습니다.** 선택지 설명이 길어지면서 설계자의 의도를 드러낼 수 있다는 점은 원고 Study 5의 주의사항 그대로 Limitations로.
