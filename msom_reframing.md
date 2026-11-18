# M&SOM 재투고용 재구성안 (초안)

> 상태 표시: **[기존]** = 원고에 이미 있는 결과, **[신규-추측]** = 제가 스케치한 결과로 증명/수치검증 전. 투고문에 쓰기 전에 반드시 직접 도출·검증해야 함.

---

## 1. 프레이밍 전환

| 현재 (ISR) | M&SOM |
|---|---|
| agent error dynamics, contagion/heterogeneity/derailment | human-in-the-loop 에스컬레이션 정책과 감독 자원(검토자 용량) 배분 |
| "오류의 통계적 구조" | "누구를, 언제, 어떤 신호로 사람에게 넘기나 + 사람을 몇 명 두나" |
| H = 개입 비용(상수) | H = 검토자 시간의 기회비용 → **혼잡에 따라 내생** |
| 세 채널을 대등하게 나열 | derailment를 중심 모형으로, 나머지 두 채널은 강건성/부록 |

### 제목 후보
1. *Escalating to the Human: Staffing and Policy Design for Oversight of Autonomous AI Agents*
2. *When to Escalate? Capacity-Constrained Human Oversight of AI Agents*
3. *Count What the Error Says: Escalation Rules for AI Agents Under Scarce Human Review*

추천: 2번 (짧고 운영 쪽 독자에게 질문이 바로 보임).

### 초록 초안 (영문, 약 150단어)
Firms deploy autonomous AI agents on streams of multistep tasks and rely on a limited pool of human reviewers to take over when an agent goes wrong. We study the joint design of the escalation policy and the reviewer capacity. In our model an agent's errors may derail a task silently, so that it completes with a wrong output; the firm observes errors but not derailment, and escalated tasks queue for reviewers. We show that the optimal policy escalates when a type-weighted error count reaches a threshold, that the threshold rises with reviewer load, and that **[신규-추측: a rule that sets thresholds from the observed average wait over-escalates relative to the system optimum]**. **[신규-추측: Outcome verification and in-flight escalation are substitutes: better verification raises the optimal threshold.]** Using 80,036 public agent trajectories and two randomized fault-injection experiments (11,352 runs, five agents), we find that transient failures rarely harm recent models, whereas errors that misreport the environment derail tasks, lowering success by up to 30 percentage points. Counting errors by type, and staffing for the load this creates, matters more than counting errors.

---

## 2. 이론 보강 (핵심 작업)

AE의 "rudimentary / simple extension" 비판에 대한 답: 현재 결과(Prop 6, Cor 1)는 가정 A3(독립 derailment)에서 거의 바로 나온다. 아래 두 확장은 **가정만으로는 자명하지 않은 결과**를 만들고, 운영 문헌의 익숙한 도구(큐잉, 정보가치)와 연결된다.

### 확장 A: 용량 제한 인간 검토자 (혼잡과 외부효과)

**설정.** 과제가 도착률 Λ로 들어오고, 정책 N(임계 횟수)에서 에스컬레이션 확률을 P_N이라 하면 에스컬레이션률 λ = Λ·P_N. 검토자는 서비스율 s의 M/M/1(또는 M/M/c). 대기 비용률 d. 유효 hand-off 비용:

- 평균 기준: H_avg(λ) = h + d/(s − λ)
- 한계 기준: H_mar(λ) = h + d·s/(s − λ)²   ← d/dλ[ d·λ/(s−λ) ] (Little 법칙으로 시스템 내 인원 L = λ/(s−λ))

H_mar > H_avg 이다 (한계 기준이 항상 큼).

**후보 결과 [신규-추측]**
1. 시스템 최적 임계는 Prop 6의 식 (3)에서 H를 H_mar로 바꾼 값의 고정점이다. 부하가 커질수록 N*는 올라간다 (전략적 보완성: 임계를 낮춤 → λ↑ → H_eff↑ → 임계↑).
2. 관측된 평균 대기시간으로 H를 잡는 분권적 규칙은 **과잉 에스컬레이션**한다 (Naor 유형의 외부효과). 실무 시사점: "검토자가 한가해 보인다고 임계를 낮추면 안 된다".
3. Prop 8과 결합: 마진(H_eff ≈ C̄)이 **스태핑 s에 따라 이동**하므로 모니터링의 가치는 s에 대해 단봉이거나 비단조일 수 있다. 검토자를 늘리면 모니터링 가치가 오를 수도, 내릴 수도 있다. (**증명 필요; 수치로 먼저 확인할 것**)
4. 유형별 가중치 w_k = −ln(1−θ_k)는 그대로 유지되고, 용량 제약은 임계에만 그림자가격으로 들어온다 (라그랑지 완화). Cor 1이 확장에서도 살아남는지 확인.

**확인할 사항:** P_N의 닫힌 형태 (N번째 오류 전에 완료할 확률), 정상상태 가정, 정책 간 비교에서 이탈(abandon) 처리.

### 확장 B: 불완전한 검증 신호 (결과 통제 vs 행동 통제)

**설정.** 완료 시점에 비용 v로 최종 출력을 검증하면 오답을 확률 d로 잡는다. 잡히면 복구비용 F_d, 못 잡으면 하류 손실 F_u (F_d < F_u).

**후보 결과 [신규-추측]**
1. 유효 오답 비용 F_eff(d) = d·F_d + (1−d)·F_u 는 d에 대해 감소한다. 식 (3)의 임계는 F_eff가 낮을수록 올라가므로 **N*는 d에 대해 증가**한다. 즉 결과 검증과 에스컬레이션은 한계에서 대체재다 (Kirsch의 통제 포트폴리오와 연결).
2. 검증 투자(v)의 가치도 H, F와의 상대위치에 따라 단봉일 수 있음 (Prop 8과 같은 구조).
3. 비행 중 노이즈 신호 s_t를 추가하면 posterior 로그오즈가 가법이므로 충분통계는 "가중 오류 수 + 가중 신호"이다. Cor 1의 자연스러운 일반화.

**실증 연결 (이미 가진 데이터).** 코드 수리는 에이전트가 테스트를 돌려 스스로 검증할 수 있고(d 큼), 고객 서비스는 그렇지 못하다(d 작음). Table 4에서 N*가 코드 수리 4–7, 고객 서비스 1–2로 갈리는 패턴이 확장 B의 비교정태와 정확히 같은 방향이다. 지금은 "한 가지 추정"이지만 새 모형에서는 **예측과 검증**이 된다.

### 추가 실험 (선택, 비용 작음)
- 고객 서비스에 검증 단계(DB 재조회 또는 LLM 검사)를 붙여 d를 조작하고, 상황별로 θ와 N*가 예측대로 이동하는지 확인. 이전 실험이 약 US$330였으므로 소규모로 가능.
- misleading 오류의 "거짓 진술" 요소와 "내 실수처럼 보임" 요소를 분리하는 두 번째 arm. (원고의 한계 항목)
- agent가 거짓 보고를 받아들였는지 코딩 (메커니즘 검증).

---

## 3. 구성안

**본문**
1. Introduction: 운영 질문으로 시작 (검토자가 10명뿐인데 에이전트 수천 개). 한 문장 발견 → 기여 3개.
2. Literature: 인간–알고리즘 협업·override 정책 / 큐잉과 외부효과 / 최적정지 / 에이전트 신뢰성 평가
3. Model: derailment + 용량 (단일 핵심 모형)
4. Analysis: Prop 6/Cor 1 [기존] → 확장 A → 확장 B → 마진 결과(Prop 8)
5. Evidence: 관측 코퍼스(이질성 때문에 전염이 과대추정됨) → 실험 → 보정
6. Managerial implications: 스태핑 + 임계 + 검증 투자를 함께 설계하는 표
7. Conclusion

**부록으로 이동:** 전염(Hawkes) 분석 Prop 1–4, 이질성 학습 Prop 5, 결합 Prop 7. 본문에는 "왜 전염을 주 모형에서 뺐는지"를 실험 결과 한 단락으로 설명.

## 4. 문체 (AE의 가독성 비판 대응)
- 서론 첫 문단은 구체적 장면 하나 (예: 항공 예약이 "찾을 수 없음"으로 응답).
- 본문의 명제 수를 8개 → 3–4개로. 나머지는 부록.
- 각 명제 뒤 한 문장짜리 평이한 해석.
- "X, but Y, which Z" 구조 반복 줄이기. 문장 길이를 섞기.

## 5. 투고 전 체크리스트
- [ ] 확장 A/B 증명 또는 수치 시뮬레이션 (특히 A-3 비단조성)
- [ ] 비슷한 arXiv 논문과 차별점 정리 ("Oversight Has a Capacity", 에스컬레이션 모델별 특성 논문)
- [ ] M&SOM AI in Operations 담당 에디터와 최근 게재 논문 확인, 필요하면 사전 문의
- [ ] 최신 JCR/IF 확인
- [ ] 비용 파라미터(k, c, H, F, s, d) 현실화: 실제 사례 또는 산업 보고서 인용

---

## 6. 시뮬레이션 검증 결과 (`sim/sim_capacity.py`, `sim/sim_capacity2.py`)

설정: k=1, c=5, μ=0.054, q=0.06, h=20, d=10, s=1. 마르코프 체인으로 임계 n별 (A_n, P_n)을 정확히 계산.

| 점검 | 결과 | 판정 |
|---|---|---|
| 체인 최적 임계 vs Prop 6 닫힌 형태 (θ 5개 × F 2개) | 10/10 일치 | 기존 결과 확인 |
| 시스템 최적 임계가 부하 Λ에 대해 비감소 | 성립 (Λ 0.3→8에서 1→4) | 지지 |
| 분권적 규칙(평균 대기로 H 설정)이 과잉 에스컬레이션 | 36개 중 34개에서 P_dec ≥ P_sys. 1개는 반례 성격(P_dec 0.126 < P_sys 0.139, 격자 거칠기 영향 가능), 1개는 수치 실패(고정점 탐색이 불안정 영역에 걸림) | **대체로 지지, 미완** |
| 분권적 손실 | 대부분 0~6%, 최대 약 14% | 크기는 중간 |
| 모니터링 가치가 스태핑 s에 대해 단봉 | 48/48 설정에서 내부 최대 (s=3에서 17.8 → s≥10에서 0) | 지지, 단 아래 주의 |
| 확장 B: 검증 품질 d↑ → 최적 임계↑ | 1→1→1→2→3, 닫힌 형태와 일치 | 성립, 단 아래 주의 |

### 정직한 해석
- **A의 과잉 에스컬레이션**은 이산 임계에서는 순수전략 균형이 자주 없어서, 무작위 혼합 임계로 완화해야 했다. 이 완화에서만 깔끔하게 나온다. 논문에서는 연속 완화를 명시하거나 균형 개념을 정의해야 한다.
- **스태핑에 대한 단봉성**은 Prop 8(마진에서 최대)에 H_eff가 s의 함수라는 사실을 합친 것이라 새로운 깊이는 작다. 다만 "검토자가 충분하면 모니터링은 필요 없고, 너무 적으면 소용이 없다"는 관리적 해석은 쓸 만하다.
- **B**는 Prop 6이 F에 대해 단조라는 사실에서 거의 기계적으로 나온다. 진짜 새로운 결과가 되려면 노이즈 있는 비행 중 신호나, 검증 투자 v의 내생적 선택(가치가 단봉인지)을 넣어야 한다.
- 모든 비용 파라미터(h, d, s, Λ)는 임의 값이다. 정성적 패턴만 믿을 것.
- 다음 단계: (1) 균형 개념을 명확히 하고 위 두 예외 셀을 해결, (2) M/M/c와 도착의 변동성 추가, (3) B에 v를 내생화.
