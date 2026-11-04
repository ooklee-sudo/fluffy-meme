# IEEE Intelligent Systems 투고용 원고 구조

ISRE-2026-4499를 IEEE Intelligent Systems의 Feature Article로 다시 쓰기 위한 설계도입니다. 숫자는 모두 순서 균형(balanced action order) 재실행 결과(`skipver/results/compare_paper.md`)에서 가져왔습니다.

---

## 0. 투고 전에 확인할 것

올려주신 CS 매거진 템플릿(`CS_Mag_7_22_2.docx`)은 분량 제한을 각 매거진의 *Write for Us > Author Information* 페이지로 미룹니다. 저는 그 페이지를 확인하지 못했습니다. 아래 배분은 다음 **가정**에 맞춘 것이니 투고 전에 꼭 확인하세요.

| 항목 | 가정 | 근거 |
|---|---|---|
| 본문 | 약 6,000단어 이하 (그림·표 1개당 250단어로 계산) | Computer Society 피처 아티클의 일반 관행 |
| 참고문헌 | 20개 이하 | 비공식 템플릿 사이트(SciSpace) 기준, 미확인 |
| Abstract | 150단어 내외, 인용 없음 | 템플릿: 한 단락, 인용 금지 |
| 헤더 | "Feature Article" + 3–4단어 주제 문구 | 템플릿 1쪽 안내 |

템플릿 규칙 중 원고에 영향이 큰 것: 제목 4줄 이하, 소제목 번호 없음, 인용은 위첨자 번호(등장 순서), 본문에서 언급하지 않는 부록은 보충자료로 이동하고 언급하는 부록은 sidebar로, "general technical reader" 대상이라 전문용어 최소화, 결론에서 그림·표 언급 자제.

---

## 1. 이 버전의 핵심 메시지

ISR 원고와 메시지가 다릅니다. 순서 균형 재실행 결과가 메시지를 바꿨습니다.

> **LLM 운영 에이전트가 검증을 건너뛰는지는 모델만의 성질이 아니라 모델과 프롬프트 배치(목표를 보여주는지, 선택지를 어떤 순서로 나열하는지)가 함께 정한다. 같은 모델이 배치에 따라 0%에서 60%까지 오간다. 그러니 위임 전에 배치를 무작위화해서 audit해야 한다.**

ISR 원고와 비교:

| | ISR 원고 | IEEE IS 버전 |
|---|---|---|
| 주인공 | loss chasing 검증 → goal visibility | 프롬프트 배치가 에이전트 행동을 좌우한다 |
| 순서 의존성 | (몰랐음) | **핵심 결과 중 하나** |
| 효과 크기 | goal effect +54 pp | +16 pp (순서 균형), 순서별로 0–62% |
| loss 문장 | skip을 줄인다 | 늘리지도 줄이지도 않는다 (차이 없음) |
| reasoning | 대부분 없앤다 (27→10%) | 일부 줄인다 (13→8%) |
| 큰 모델 | floor | Sonnet 5.5·Haiku 5.5는 순서를 섞어도 0% |
| 기여 | 이론 + 방법 + 실무 | 방법(audit 설계) + 실무 가이드 |

---

## 2. 제목과 Abstract

**제목 후보** (4줄 이하)
1. **Same Model, Different Shortcuts: How Prompt Layout Steers LLM Operators to Skip Verification** (추천)
2. Auditing LLM Operators Before Delegation: Goals, Option Order, and Skipped Tests
3. When AI Operators Cut Corners: Goal Visibility and Option Order in Automated Maintenance

**헤더 문구**: Feature Article: Auditing AI Operators

**Abstract 초안 (약 150단어)**

> Organizations are beginning to let large language model (LLM) agents run maintenance pipelines, including the decision to skip regression tests. We built a rule-scored maintenance task in which skipping tests is always worse in expected value, and varied only the wording and layout of the status prompt. In a fast commercial model, skipping appeared only under time pressure. Stating the quality target in the status line raised it by about 16 percentage points, whereas describing the last result as a loss did not. The order in which options were listed mattered as much: the same model skipped in 62% of goal-stating prompts when "hold" was listed first and almost never when a tested fix was listed first. Larger and newer models did not skip under any layout. Shortcut taking is therefore a property of a model and its prompt layout together, and we describe an audit that organizations can run before delegating.

---

## 3. 섹션별 분량 배분 (총 약 6,000단어 기준)

| 섹션 (번호 없음) | 단어 | 내용 | 원 원고에서 가져올 것 |
|---|---|---|---|
| Abstract | 150 | 위 초안 | – |
| (도입, 제목 없음) | 600 | 에이전트에게 운영을 맡기는 흐름, 검증은 관찰하기 어려운 노력, 질문: 무엇이 shortcut을 유발하나 | 서론 1–2단락, 11.2 "통제 신호" |
| **A Maintenance Task With a Known Right Answer** | 800 | 환경, payoff (skip은 항상 기대값 열위), 1회 선택만 분석하는 이유, 16개 wording과 순서 균형 설계 | 4.1–4.5 (대폭 압축) |
| **Goals, Not Losses** | 900 | 시간 압박(12→6→3턴: 0%, 0.1%, 12.8%), goal effect +16 pp, loss 차이 없음, target이 어디에도 없으면 0% | Study 2, 4 (등록 검증 Study 1은 두 문장으로) |
| **Option Order Matters as Much as Wording** | 800 | 순서별 skip 0–62%, wide_skip이 맨 위면 frame과 무관하게 약 35%, 원래 결과가 가장 유리한 순서에서 나왔다는 점을 직접 밝힘 | **신규** (order_check) |
| **What Reduces Skipping** | 600 | thinking 13→8%, 기대값을 보여주면 약 5%로, 선택지 순서 균형 | Study 3, 5 |
| **Which Models Skip** | 500 | 표 1: 모델별 결과. Haiku 4.5와 Flash-Lite만 skip, Sonnet 5.5·Haiku 5.5는 순서를 섞어도 0% | Study 2, 6, 7 파일럿 |
| **Auditing an Operator Before Delegation** (sidebar 겸용) | 600 | 체크리스트 6개 | 11.2 measurement argument + 11.3 실무 함의 |
| **Limitations** | 300 | 1회 선택, 단일 과제, 모델 버전 의존, 메커니즘 미규명 | 11.4 압축 |
| Conclusion | 250 | 미래 방향 (agentic tool-use 과제, 실제 티켓 데이터), 그림 언급 없이 | 11.5 |
| 그림 3개 + 표 1개 | (1,000) | 250 × 4 | |
| **합계** | **약 6,500** | 한도가 6,000이면 Limitations와 Which Models를 줄이세요 | |

### 빼거나 보충자료로 보낼 것
- Study 1 전체 (사전등록 loss-chasing 검증): 본문 두 문장 + 보충자료. 이 저널 독자에게는 "유력한 설명을 미리 등록해서 검증했고 지지되지 않았다"면 충분합니다.
- H2 escalation과 excess risk 논의 (Table 4): 보충자료.
- Prospect theory 이론 배경: 한 단락으로.
- Goal-setting과 에이전시 이론: 도입에서 한두 문장 (Schweitzer, Ordóñez, Kellogg).
- 분산 분해(frame/wording/interaction), 99.6% 구간: 보충자료. 본문은 95% 구간만.
- Online Appendix A–F: 보충자료.

---

## 4. 그림과 표

### 그림 1. 프롬프트 구조와 조작한 차원 (다이어그램, 직접 그려야 함)

에이전트가 받는 프롬프트를 실물처럼 보여주고, 조작한 부분을 표시하는 그림입니다.

```
┌──────────────────────────────────────────────────────┐
│ [헤드라인]  "8 points remain to the target. ..."      │ ← ① 목표 노출  ② valence
│ [Facts]    quality=100; target=108; remaining=3 ...   │ ← ③ 남은 턴   ④ facts에 target 유무
│ [Options]  - hold: ...                               │ ← ⑤ 나열 순서 (6가지 회전)
│            - narrow_patch: ... costs 2 turns          │
│            - narrow_skip: ... costs 1 turn            │ ← 기대값 −0.35 (항상 열위)
│            ...                                        │
└──────────────────────────────────────────────────────┘
          오른쪽: 6개 행동의 기대값 막대 (skip 2개만 음수)
```

- 왼쪽: 프롬프트 박스에 번호 표시. 오른쪽: Table 2의 기대값을 작은 막대로 (skip 두 개만 음수).
- 캡션 예: "FIGURE 1. The status prompt an operator reads. Only the marked parts vary across conditions; the facts are identical. Both test-skipping options have lower expected value than their tested counterparts."

### 그림 2. 목표를 보여주면 skip이 늘고, loss 문장은 영향이 없다 ✅ 생성됨

`skipver/figures/fig2_goal.png` / `.pdf`. Haiku 4.5, 3턴 남음, 순서 균형, 16개 wording, 95% CI는 wording 단위 bootstrap.

- 왼쪽 패널 (facts에도 target 있음): Neutral 9%, Loss 7% vs Gain 22%, Neutral+target 25%, Loss+target 23%.
- 오른쪽 패널 (target이 헤드라인에만): target을 말하지 않는 frame은 0%.
- 캡션 예: "FIGURE 2. Share of first choices that skip tests, by status headline (Claude Haiku 4.5, three turns left; option order balanced; bars are means over 16 wordings with 95% intervals). Headlines that state the target (blue) raise skipping whether they are neutral or describe a loss. When the target appears nowhere in the prompt, the other headlines produce no skipping."

### 그림 3. 맨 위에 나열된 선택지가 결과를 바꾼다 ✅ 생성됨

`skipver/figures/fig3_order.png` / `.pdf`. 같은 데이터(facts에 target 있는 조건)를 맨 위 선택지별로 나눔.

- target을 말하는 헤드라인: hold가 맨 위면 62%, rollback 38%, 검증 없는 wide fix 34%, 검증된 fix가 맨 위면 0–3%.
- target을 말하지 않는 헤드라인: 검증 없는 wide fix가 맨 위일 때만 35%.
- 캡션 예: "FIGURE 3. The same data split by the option listed first. Goal-stating headlines raise skipping mainly when a non-progress option (hold or rollback) heads the list; when a tested fix is listed first the model takes it. Listing the untested wide fix first yields about one-third skipping regardless of the headline."
- **본문에서 직접 밝힐 문장**: "Our earlier analyses listed 'hold' first in every first choice, the layout that produces the largest effect; the estimates reported here average over all six layouts."

### 표 1. 어떤 모델이 skip하나

| 모델 | 3턴 남음, skip | 순서 | Gain이 가장 높은가 |
|---|---|---|---|
| Claude Haiku 4.5 | 12.8% | 균형 | 예 |
| Claude Haiku 4.5, extended thinking | 8.0% | 균형 | 예 |
| Gemini 2.5 Flash-Lite | 4.2% | 균형 | 예 |
| Claude Haiku 5.5 | 0.0% (0/1,440) | 균형 | – |
| Claude Sonnet 5.5 | 0.0% (0/288) | 균형 | – |
| Claude Opus 5.5, Fable 5.1 | 0.0% (0/4,320 each) | 원 순서만 | – |
| Ministral-8B, Llama-3.1-8B, Gemini 3.1 Flash-Lite, Gemma-3-12B | 0–4% | 원 순서만 | – |

(Opus·Fable과 다른 소형 모델은 순서 균형으로 재실행하지 않았습니다. 필요하면 Opus는 약 $5, 소형 모델은 $1 이하로 돌릴 수 있습니다.)

### Sidebar. Auditing an LLM Operator Before Delegation

템플릿이 "본문에서 언급하는 부록은 sidebar로"라고 하므로, 실무 체크리스트를 sidebar로 두면 좋습니다.

1. Score each decision against the expected-value-maximizing action, not against "risk goes up after failures."
2. Write every status message in many independent wordings and treat the wording as the unit of replication.
3. Randomize or rotate the order of options; report results by layout.
4. Run the model with the reasoning setting it will have in deployment.
5. Report a model that never takes the shortcut as a floor, not as evidence of no effect.
6. Vary goal statement and valence separately; a "progress to goal" message changes both.

---

## 5. 참고문헌 (20개 이내 후보)

원 원고에서 고른 것 + 앞서 확인한 것. ⚠️ 표시는 서지 정보 확인이 필요한 것.

1. Kahneman & Tversky 1979, prospect theory
2. Tversky & Kahneman 1981, framing
3. Thaler & Johnson 1990, loss chasing
4. Locke & Latham 2002, goal setting
5. Schweitzer, Ordóñez & Douma 2004, goals and unethical behavior
6. Ordóñez et al. 2009, "Goals gone wild"
7. Heath, Larrick & Wu 1999, goals as reference points
8. Jensen & Meckling 1976 *또는* Holmström & Milgrom 1991 (하나만) ⚠️
9. Kellogg, Valentine & Christin 2020, algorithmic control
10. Sculley et al. 2015, hidden technical debt in ML
11. Horton 2023, LLMs as simulated economic agents
12. Ross et al. 2024, LLM economic rationality
13. Scheurer et al. 2023, deceptive trading agent under pressure
14. Jiang & Tang 2026, safety-utility trade-off under pressure
15. Chen et al. 2026, long-horizon agents rushing to finish
16. **선택지 순서 효과에 관한 LLM 문헌** ⚠️ 새로 필요: 객관식 문제에서 LLM의 선택지 위치 편향을 보인 연구가 여럿 있습니다(예: 선택지 순서를 바꾸면 정답률이 바뀐다는 연구). 그림 3을 해석할 때 꼭 하나는 인용해야 리뷰어가 "알려진 position bias를 재발견한 것 아니냐"고 물을 때 답할 수 있습니다. 서지를 확인한 뒤 넣으세요.
17. Belcak et al. 2025, small language models for agentic AI
18. Ong et al. 2025, RouteLLM

---

## 6. 진행 순서 제안

1. Author Information 페이지에서 단어·참고문헌·그림 제한 확인 → 3절 배분 조정.
2. 그림 1 다이어그램 제작.
3. "Option Order Matters" 섹션부터 쓰기 (새 내용이고 논문의 차별점).
4. 선택지 순서 편향 문헌 찾아서 인용 16 확정.
5. (선택) Opus 5.5와 Study 6 소형 모델을 순서 균형으로 재실행해서 표 1을 모두 균형 버전으로 통일.
6. 보충자료: 원 원고의 Online Appendix + `skipver` 코드와 로그 링크 (double-blind 여부 확인).
