# M&SOM 투고용 abstract / introduction 초안

> 상태: 초안. 대괄호 `[...]`는 아직 증명·검증·확정이 필요한 항목이다. 문서 끝의 "주장 대장"에서 각 문장의 근거와 상태를 확인할 것. 근거 파일은 `msom_reframing.md`(절 번호)와 `sim/`.

---

## Title

**When to Escalate? Reviewer Capacity and the Design of Human Oversight for AI Agents**

(대안: *Who Calls the Human? Escalation, Verification, and Reviewer Capacity for Autonomous AI Agents*)

## Abstract (약 190 words)

Firms deploy AI agents on streams of multistep tasks and rely on a limited pool of human reviewers to take over when an agent goes wrong. Escalation can come from two places: the firm, through a rule such as "hand off after N errors," and the agent itself, which may transfer a task to a person. We study how these are best combined with reviewer capacity and with verification of outputs. In our model an error can lead to a wrong output, which is costly to repair, or to an agent-initiated transfer, which loads the reviewers. We show that the optimal firm rule counts errors by the probability that each type leads to a wrong output; that verification and escalation are substitutes, with verification most valuable when reviewers are hardest to reach; and that rules set from the observed average wait escalate too much, because each escalation also delays others. Using 80,036 public agent trajectories and fault-injection experiments with five agents (11,352 runs), we find that transient failures rarely hurt recent models, while a misleading tool message raises GPT-6.1-terra's rate of transferring to a human from 0.40 to 0.74 without increasing wrong outcomes. **[Sonnet 5.5: wrong-output derailment of about 0.12; DeepSeek: estimator-dependent.]** Tool-output accuracy therefore determines escalation volume, and volume determines the reviewers a firm needs.

## 1. Introduction

**[Opening scene]** A customer asks an airline's AI agent to change a flight. The agent looks up the reservation, and the booking system answers: *reservation not found*. The agent now has three options. It can accept the message and tell the customer there is no booking; it can look again by another route; or it can hand the case to a human agent. In our experiments, one commercial model (GPT-6.1-terra) chose the third option far more often when the "not found" message was false: it transferred the case in 74% of runs, against 39% when nothing was wrong. Every such transfer joins a queue of cases waiting for a person.

This paper is about the decision behind that queue: when should a task be taken back from an AI agent, who should make that call, and how many people does the answer require?

**[Why this question, and not "fix the agent"]** One response is that firms should retrain or redesign agents so that they make fewer errors. We agree that they should, but it does not remove the problem. Agents are often bought rather than built, tool outputs are produced by systems the firm does not control, and even a very reliable agent meets an occasional wrong answer from a database or an API. What a firm controls is the rest of the system: when it intervenes, whether it verifies results, and how many reviewers it staffs. These choices interact, and a firm that tunes one while ignoring the others misjudges the cost.

**[What we do]** We model a firm that sends tasks to an AI agent. At each step the agent may err, a task may finish, and the firm may hand the task to a human reviewer. We give errors two consequences, based on what we see in the data. An error can *derail* the task, so that it ends with a wrong output that costs more to detect and repair; or it can lead the agent to *transfer* the task itself, which costs the reviewer's time. Reviewers are a scarce resource: tasks that reach them wait. The firm chooses its hand-off rule, whether to pay for verification of finished outputs, and (in an extension) how many reviewers to employ.

**[What we find: theory]**
1. *Count errors by what they cause.* The firm's optimal rule hands off when a weighted count of errors reaches a threshold. Each error type is weighted by the probability that it leads to a wrong output; a type that never does should not be counted, however often it occurs. An agent's own transfers change the threshold only slightly, but they change the load on reviewers a great deal.
2. *Do not set the rule from the average wait (a supporting result: the congestion externality is classical, and capacity-dependent thresholds appear in Wang and Rachev 2026).* When each escalation is decided against the observed average waiting time, the firm escalates too much, because a new case also delays everyone behind it. **[Proposition: escalation rate under average-wait rules is at least the system optimum, with equality only at kinks of the policy frontier; in numerical examples the excess costs 0–30%, and the loss tends to be larger when the same capacity is pooled across more reviewers.]**
3. *Verification substitutes for escalation.* Better verification raises the optimal threshold; the value of verification does not fall as hand-off becomes more expensive, whereas the value of monitoring peaks where handing off and letting the agent finish cost about the same. **[Regime map: always escalate → count rule → count rule with verification → verify and let the agent run.]**

**[What we find: evidence]** We use two kinds of evidence. A public corpus of 80,036 trajectories of an open-source software-engineering agent shows strong clustering of errors, but most of it disappears once tasks are allowed to differ in difficulty. We then ran two randomized fault-injection experiments, in customer service and in code repair, with five agents and 11,352 runs, in which we inserted either a transient failure or a misleading "not found" message at a random point. Transient failures rarely hurt the recent models. A misleading message is different: it raises GPT-6.1-terra's rate of transferring the case to a human from 0.40 to 0.74, and its success rate falls from 0.77 to 0.46, but the additional failures are almost all transfers and not wrong outputs. **[Claude Sonnet 5.5, in contrast, shows genuine wrong-output derailment (about 0.12); for DeepSeek-V3.1 the split depends on how the two channels are separated.]** In code repair, where the agent can run tests, the effects are smaller.

**[Contributions]**
- *For capacity models of oversight:* existing models take the demand for review as given, as a function of an exogenous risk score (Wang and Rachev 2026) or of exogenous reviewer error rates (Lin and Zhang 2026). With randomized fault injection we show that the volume of escalations from a multistep agent depends on the accuracy of its tool outputs: a misleading message raised one agent's transfer rate from 0.40 to 0.74. **[Generalize only after more agents or domains; this is one agent.]**
- *For research on human–AI delegation:* we move from the question of whether to delegate to the question of when and by whom a delegation should be reversed. Operations research already studies capacity-dependent deferral from classifiers and screening judges (Lykouris and Weng; Wang and Rachev; Lin and Zhang); we add the error structure of multistep agents and evidence on what agents actually do after an error.
- *For research on IS control:* we separate behavior control (monitoring and escalation) from outcome control (verification) and show that they substitute, with a clear boundary in the hand-off cost.
- *For practice:* we show that the quality of tool outputs drives escalation volume, so that data governance and staffing are the same decision; we show how to calibrate the rule and the staffing from a modest injection experiment of the kind we run; and we flag a common mistake, setting escalation thresholds from the observed queue.

**[A caution about our own results]** The first version of this work interpreted the drop in success after a misleading message as wrong outputs. A closer look at the transcripts shows that for two of the three agents most of it is the agent's own transfer. We report both channels and show where the conclusions depend on how they are separated.

**[Roadmap]** Section 2 reviews related work. Section 3 presents the model and Section 4 the results on thresholds, capacity, and verification. Section 5 reports the observational and experimental evidence, separates the two channels, and calibrates the model. Section 6 discusses implications and limits.

---

## 2. Related Literature (초안, 검색으로 확인한 문헌 포함)

> 확인 수준: Grassmann(1983)과 Naor(1969)는 서지를 확인했다. **Wang & Rachev와 Lin & Zhang는 PDF 텍스트를 추출해 본문을 읽었다.** Lykouris & Weng, Turan, DeCCaF는 초록과 메타데이터만 읽었다. 본문 읽기에서 "개별 최적 대 계획자" 비교를 찾지 못했다는 판단은 키워드 검색(Naor, toll, decentral, individual, self-interest: 0건)과 정독한 부분에 근거한다.

**Delegation to and from AI agents (IS).** Baird and Maruping (2021) treat delegation to agentic IS artifacts as an ongoing allocation of rights and responsibilities; Fügener et al. (2022) show that people delegate poorly to AI; Berente et al. (2021) frame AI management as a balance of autonomy, learning, and inscrutability. These papers ask whether to delegate. We ask when and by whom a delegation should be reversed once the agent acts over many steps.

**Deferral and escalation under congestion (operations, ML).** The closest work studies when to send cases to scarce human reviewers.
- Lykouris and Weng (2024, arXiv:2402.12237, v4 2025), *Learning to Defer in Congested Systems: The AI–Human Interplay*: an AI classifies items and sends uncertain ones to a congested human queue, with delayed and selectively sampled feedback; they give a near-optimal online-learning algorithm. Their object is a classifier on independent items.
- Wang and Rachev (2026, arXiv:2601.22295), *Operating Imperfect AI: Reliability Drift and Human Congestion* **(본문 확인)**: Poisson task arrivals, each task has an i.i.d. observable risk score, the controller decides per task whether to automate or escalate to a finite-capacity human queue, and the reliability regime drifts as a Markov chain. Results: a threshold policy (Theorem 1), convexity of the value function in the queue length (Proposition 1), "congestion shedding" (threshold rises with backlog), "safety buffering" (threshold falls under drift), and a capacity phase transition. The introduction states the congestion externality ("every task added to the queue increases the delay for all subsequent tasks") and a planner's shadow price of capacity. **Overlaps with our capacity analysis (threshold rising in load; shadow price).** They do not (in the text we extracted) compare an individually rational rule using the observed average wait with the planner's rule, and they have no multistep agents, no error accumulation within a run, no agent-initiated transfers, no verification, and only a synthetic simulation. Their stated limitations are reviewer fatigue and an endogenous learning loop.
- Lin and Zhang (2026, arXiv:2603.13870 v2; v1 title *When to Screen, When to Bypass*), now titled *When Should AI Review Precede Human Approval of Agent-Generated Code?* **(본문 확인)**: language-model agents draft pull requests, a human maintainer must approve each one, and an optional AI reviewer can filter first, but its false rejections send merge-ready work back for another agent run. A queueing network with rework yields a staffing map: the optimal review fraction passes through four phases as maintainer capacity grows (including one in which an informative reviewer is left idle because its rework displaces new work), and a "Quota Tracking" rule attains the fluid bound; reviewer error rates (from SWE-Review) are taken as inputs and calibrated on SWE-bench Verified. **Closest to our verification margin and to the claim that the value of oversight is non-monotone in staffing.** Differences: their object is the finished pull request, reviewer error rates are exogenous, and nothing happens inside the run (no error dynamics, no injected faults, no agent-initiated escalation).
- Turan (2026, arXiv:2606.08919), *Oversight Has a Capacity*: agent action gates with a fatiguing reviewer; safety peaks at an intermediate escalation rate. A systems and measurement paper that does not claim novel mechanisms; useful as practical motivation.
- Alves et al. (DeCCaF, arXiv:2403.06906): cost-sensitive learning to defer with workload constraints.

**Queues and individual versus social optimization.** Naor (1969, *Econometrica* 37(1):15–24) shows that joining decisions made against the observed queue exceed the social optimum; our over-escalation result applies this externality to hand-off rules (we claim an application, not a new principle). For convexity of the mean queue size in the M/M/c queue we rely on Grassmann (1983, *J. Appl. Probab.* 20:916–919); Lee and Cohen (1983, same volume, pp. 920–923) cover related performance measures.

**Optimal stopping and monitoring.** Wald (1947); Shiryaev (1963); Chow, Robbins, and Siegmund (1971) for the monotone case; Holmström (1979) and Blackwell (1953) for informativeness; Kirsch (1997) for control portfolios.

**Reliability and failure of LLM agents.** Benchmarks (SWE-agent, τ-bench) report success rates and not within-run error dynamics; we add randomized fault injection and separate error types.

---

## 주장 대장 (각 문장의 근거와 상태)

| 주장 | 근거 | 상태 |
|---|---|---|
| 최적 규칙은 오류를 유형별 가중 횟수로 센다 (w = −ln(1−θ_w)) | Cor 1, 보조정리 1 (`msom_reframing.md` §8) | 증명 완료 (θ_w 기준으로 재서술 필요, §12) |
| 자기 인계는 임계를 거의 바꾸지 않고 부하를 바꾼다 | 명제 6′, 가치 반복 150개 파라미터 일치 (§12.1) | 닫힌 형식은 증명 스케치, 수치 검증 완료 |
| 평균 대기 기반 에스컬레이션이 과잉 | 명제 A, 보조정리 3 (§8) | 증명 완료, M/M/1·M/G/1. M/M/c는 인용 + 수치, 근사에 의존 |
| 손실 0~30%, 풀링할수록 커짐 | `sim/sim_capacity3.py` (§7.1, 7.2) | 수치 예시 (파라미터는 임의 값). 일반 결과로 쓰지 말 것 |
| 검증은 에스컬레이션의 대체재 | 명제 B1 (§8) | 증명 완료 |
| 검증의 가치는 H에 대해 비감소, 모니터링은 H = C̄에서 단봉 | 명제 B2, Prop 8 (§8) | 증명 완료 |
| 레짐 지도 (E → C → C+V → N+V) | §7.3 | 수치 (고정비 검증, 임의 파라미터) |
| GPT 인계율 0.40 → 0.74, 성공률 0.77 → 0.46 | 기존 런 로그 재분석 (§11.2) | 확인됨, 사후 탐색 분석 |
| 추가 실패는 거의 전부 인계, 오답은 늘지 않음 (GPT) | §11.2, §12.2 | 두 추정기 모두에서 견고 |
| Sonnet θ_w ≈ 0.12 | §12.2 | 두 추정기 모두 양수 (0.11, 0.13) |
| DeepSeek 오도 오류의 θ_w | §12.2 | **추정기 의존** (0.00 대 0.17), 구간 보고 |
| 코드 수리는 효과가 작다 | 원고 Table 2, 4 | 원고 값 그대로, 분해는 못 함 |
| 관측 코퍼스: 이질성 반영 후 분기비 0.38–0.56 | 원고 Table 1 | 원고 값 그대로 |
| 용량 의존 임계·그림자 가격은 기존 연구와 겹침 | Wang & Rachev (2026) 본문: Theorem 1, Proposition 1, 서론의 외부효과 서술 | **기여로 내세우지 말 것.** 개별 최적 대 계획자 비교는 본문에서 찾지 못했으나 개념은 서론에 있음 |
| 검토자 용량에 대한 정책·가치의 비단조성은 기존 연구와 겹침 | Lin & Zhang (2026) 본문: 4단계 검토 비율 | **새로움 주장 금지.** 우리 결과(스태핑에 대한 단봉)는 지지 증거로만 |
| "도구 출력 정확성이 검토자 부하를 정한다" | GPT에서 ΔP(transfer) = +0.34 [0.28, 0.41] (§12.5) | 한 에이전트의 증거. 일반화 금지 |

## 아직 비어 있는 것

1. **검증 직접 실험 없음.** 레짐 지도와 대체성은 이론과 기존 데이터의 일관성으로만 뒷받침된다 (§9~10은 실험 설계). 본문에 "직접 조작하지 않았다"고 명시.
2. **자기 인계의 이유.** 로그에 에이전트 발화가 없어 "왜 넘겼는가"는 모른다. 과제가 transfer를 정답으로 기대하는 경우도 분리하지 못했다.
3. **파라미터 현실화.** h, d, s, Λ, F, H는 예시 값이다. 실제 콜센터 수치나 산업 보고서에서 근거를 찾아 그림에 고정할 것.
4. ~~M/M/c의 볼록성 인용~~ **확인 완료**: Grassmann (1983), *J. Appl. Probab.* 20:916–919. Allen–Cunneen 근사의 한계는 여전히 본문에 명시할 것.
5. **관련 문헌**: 위 §2. Wang & Rachev와 Lin & Zhang는 본문 확인 완료 (§13 of `msom_reframing.md`). 남은 것: Lykouris & Weng, Turan, DeCCaF 본문, 그리고 이 둘이 투고 중인 저널(동시 심사 가능성) 확인.
6. ~~원고 숫자 재확인~~ **대부분 확인 완료** (원고 PDF 1–25쪽 기준): 80,036과 11,352, 5개 에이전트, 분기비 0.50/0.38/0.56 (Table 1), 성공률 GPT 0.77→0.46과 Sonnet 0.84→0.69, Table 4의 θ 0.40/0.29/0.18과 N* 1·1 / 2·1 / 2·2가 재계산과 일치. 부록(26–31쪽)은 읽지 않았다.
