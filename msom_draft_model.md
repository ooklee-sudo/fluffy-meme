> **SUPERSEDED** by manuscript/03_model.md, 04_analysis.md. This file is kept for its status notes and claims ledger; edit the manuscript files, not this one.

# M&SOM 초안: 3절 Model, 4절 Analysis

> 상태 표기: **[증명]** = 증명 완료 (위치 병기), **[수치]** = 수치 검증만, **[스케치]** = 증명 스케치. 기호는 ISR 원고와 맞췄다 (k: 걸음당 비용, c: 오류당 비용, q: 걸음당 완료 확률, μ: 걸음당 오류율, H: 인계 비용, F: 틀린 출력의 탐지·복구 비용). 오류 유형 색인은 원고의 k와 충돌하지 않도록 j를 쓰고, 대기비용은 ω, 검증 품질은 d로 쓴다.
> 읽기 쉽게 쓰는 규칙(§4 문체 규칙): 각 결과 뒤에 **"In words"** 한 문장, 증명은 부록.

---

## 3. Model

**Setting.** A firm sends a stream of tasks to an AI agent. A task is carried out in steps; a step is one action of the agent, such as a tool call. A step costs k, and each error made in it costs a further c. After each step the task is completed with probability q, independently of everything else. At the start of each step the firm may instead hand the task to a human reviewer, which ends the agent's involvement and costs H. The cost H includes the reviewer's time to take over and finish the task.

**Errors and what they cause.** An error is a tool call that the environment rejects. Errors are of types j = 1, …, J, and the number of type-j errors in a step is Poisson with mean μ_j. An error of type j has two possible consequences, which we keep apart because the data separate them (Section 5).

- *Derailment.* With probability θ_wj the error derails the task. A derailed task still runs on and may be completed, but its output is wrong, and the firm then pays F to detect and repair it. The firm does not observe derailment directly.
- *Self-transfer.* With probability θ_hj the error leads the agent to transfer the task to a human on its own. The task ends and costs H, exactly as if the firm had handed it off, but the firm did not choose the timing.

Errors are independent across steps and types. (We write θ̃_j = θ_wj + θ_hj − θ_wj θ_hj for the probability that an error has at least one consequence.)

**What the firm observes and controls.** The firm sees every error and its type, but not derailment. It chooses when to hand off, as a function of the history of errors. In Section 4.2 it also chooses the quality d ∈ [0,1] of an output check: after the agent finishes, a derailed output is caught with probability d, in which case repair costs F_d; otherwise the wrong output reaches the customer and costs F_u > F_d. The expected cost of a derailed completion is therefore F(d) = F_u − d(F_u − F_d), at a cost v(d) of the check, with v convex and increasing. In Section 4.3 hand-offs queue for a limited number of reviewers.

**Timing.** At the start of step t the firm hands off or lets the agent act. If the agent acts, the step cost is incurred, errors arrive, the agent may self-transfer, and otherwise the task is completed with probability q. If it completes, the firm pays F(d) times the probability that the task has been derailed. The firm minimizes expected total cost.

**Assumptions.** (A1) Errors and their types are observed. (A2) Parameters are known and constant. (A3) Completion occurs with probability q regardless of the error history; errors affect the correctness of the output only through derailment.

---

## 4. Analysis

### 4.1 Count errors by what they cause

Write N_j for the number of type-j errors so far, w_j = −ln(1 − θ_wj) for the weight of a type-j error, and ρ = exp(−Σ_j μ_j θ_hj) for the probability that no self-transfer occurs in a step (given the agent has not transferred so far).

**Proposition 1 (count rule).** The optimal policy hands the task to a human at the first step at which the weighted count Σ_j w_j N_j reaches the threshold −ln R, where

R = exp(Σ_j μ_j θ̃_j) · [ (k + c Σ_j μ_j) / (qF) − ρ (H − F) / F ].

If R ≥ 1 the firm should always hand off; if R ≤ 0 or all θ_wj = 0 it should never intervene on account of errors.

*In words.* The firm should count each error by how likely it is to lead to a wrong output, and hand off when the total gets large enough. An error type that never produces a wrong output should not be counted at all, however often it occurs.

[Status. **[증명]** for the monotone structure (the stopping set is absorbing because counts never fall and self-transfer does not change how counts evolve, so the one-step-lookahead rule is optimal; Chow, Robbins, and Siegmund 1971), and the formula follows by comparing H with the cost of one more step followed by a hand-off (derivation in `msom_reframing.md` §12.1). **[수치]** closed form vs value iteration: 0 mismatches in 150 random single-type parameter sets (`sim/table4_two_component.py`) and 0 of 3,025 states in 25 random two-type models (`sim/check_multitype.py`). Without self-transfer (all θ_hj = 0) R reduces to the manuscript's Equation (3).]

**Remark (what self-transfer does and does not change).** The agent's own transfers affect the threshold only through the second-order terms in μ (the factors exp(μθ̃) and ρ); in numerical examples the optimal count is unchanged when θ_h is varied from 0 to 0.8 at fixed θ_w. The threshold is set by θ_w. Self-transfer matters for how much work reaches the reviewers (Section 4.3), not for when the firm should step in. [수치, `msom_reframing.md` §12.1]

**Calibration.** The weights w_j and the threshold require only θ_wj, which a firm can estimate with a small injection experiment (Section 5), together with H, F, k, c, q, and μ. In our data, for example, Sonnet 5.5's misleading-message errors have θ_w ≈ 0.12, giving a threshold of two to four errors, while GPT-6.1-terra's have θ_w indistinguishable from zero, so no count rule is warranted even though its misleading errors are very costly in another way (they send work to reviewers). **[Numbers from §12.2; DeepSeek's value depends on how θ_w and θ_h are separated, so report a range.]**

### 4.2 Escalation and verification are substitutes

Let G(H, F) = min over policies of expected cost, so that G is the value of the best count rule for a given hand-off cost H and wrong-output cost F. Define the *value of monitoring* as the saving relative to the better of the two static choices (always hand off, never hand off), and the *value of verification at quality d* as V(H; d) = G(H, F_u) − G(H, F(d)).

**Proposition 2 (monitoring pays at the margin).** The value of monitoring is largest when the hand-off cost equals the expected cost of never intervening: it is zero for very cheap hand-offs, rises up to H = C̄ and falls beyond.

*In words.* Monitoring is worth building for tasks where taking the work back costs about as much as letting the agent finish. Cheap-to-reassign tasks can simply be reassigned; tasks that are very costly to reassign will stay with the agent whatever the monitor says. [**[증명]** manuscript Proposition 8: the optimal cost is a lower envelope of affine functions of H and hence concave.]

**Proposition 3 (verification substitutes for escalation).**
(a) The optimal count threshold is nondecreasing in the quality d of the output check, and the optimal check quality is nondecreasing in the threshold: tighter escalation lowers the value of checking.
(b) The optimal threshold is nondecreasing in the hand-off cost H.
(c) The value of verification V(H; d) is nondecreasing in H. It is zero when hand-offs are so cheap that the firm always hands off, and it reaches the constant d(F_u − F_d) z_∞ when the firm never hands off, where z_∞ is the probability that a task finishes derailed under no intervention. With v(d) = κd² the net gain at its upper end is [(F_u − F_d) z_∞]² / (4κ), attained at d = (F_u − F_d) z_∞ / (2κ).

*In words.* Checking outputs and stepping in during the run do the same job, so more of one means less of the other. Escalation is worth most at the margin of delegation; verification is worth most when people are hardest to reach. [**[증명]** (a), (b) by decreasing differences and the monotone-comparative-statics theorem of Topkis, using that the probability of finishing derailed z_n strictly increases with the threshold n and the hand-off probability P_n strictly decreases (Lemma in `msom_reframing.md` §8); (c) by the envelope theorem. **[수치]** `sim/check_proofs.py`: 0 violations in 40 random parameter sets for each claim; the closed forms in (c) match the numerical optimum d* = 0.29, gain 2.13.]

**Figure 2 (to be drawn).** The portfolio the firm should choose as the hand-off cost H and the fixed cost of verification vary: always hand off; count rule; count rule with verification; verify and let the agent run. [**[수치]** `msom_reframing.md` §7.3; parameter values are illustrative.] Our experiments are consistent with this ordering across domains, since the coding agent can run tests, which checks its own work, and has smaller effects than the customer-service agent; we did not manipulate verification directly.

### 4.3 Reviewer capacity (extension)

So far hand-off costs H as a constant. With a limited number of reviewers, each hand-off also delays the others, and H depends on how many tasks are handed off. Suppose tasks arrive at rate Λ and a hand-off waits in a queue with mean delay W(λ) at hand-off rate λ = Λ · P, where P is the probability that a task is handed off under the firm's rule, and delay costs ω per unit of time. The hand-off cost becomes H_eff = h + ω W(λ), with h the reviewer's working cost.

**Proposition 4 (do not set the rule from the observed wait).** Suppose λ W(λ) is convex and W is increasing, as in the M/M/1 and M/G/1 queues and, by Grassmann (1983), in the M/M/c queue. A firm that sets its rule against the average wait it observes hands off at least as often as the system optimum, which accounts for the delay each hand-off imposes on the others. The wedge between the marginal and the average delay cost per hand-off is ωΛ P W′ (positive whenever waits rise with load), which is what the average-wait rule ignores; the two rules coincide only where the policy frontier has a kink or at a corner.

*In words.* A rule that looks at how busy the reviewers seem now ignores the delay the new case causes for everyone behind it, so it escalates too much. [**[증명]** `msom_reframing.md` §8 (contradiction argument using the subgradients of the convex frontier). **[수치]** M/M/1 and M/M/c with Allen–Cunneen arrival variability; in the examples the cost of the average-wait rule is 0–16% (M/M/1) and 8–33% (M/M/c, pooled), tends to be larger when the same capacity is pooled across more reviewers, and is smaller under bursty arrivals in most but not all cases; parameters are illustrative. Allen–Cunneen is an approximation. **Positioning.** This applies Naor's (1969) congestion externality to hand-off rules; capacity-dependent thresholds and a shadow price of capacity are in Wang and Rachev (2026), so we present this as a supporting result and not as a main contribution.]

**Link to Sections 4.1 and 5.** In this extension the arrival rate of work at the reviewers is not a primitive. It is Λ P, where P depends on the agent's self-transfer probability θ_h as well as on the firm's rule. In our data a misleading tool message changed GPT-6.1-terra's transfer rate from 0.40 to 0.74, which would nearly double the load on the reviewers, while changing the firm's threshold hardly at all (Remark in 4.1). The accuracy of the tools the agent relies on therefore enters the staffing decision directly.

---

## 부록 연결표 (증명 위치)

| 본문 | 증명·검증 위치 |
|---|---|
| Proposition 1 | `msom_reframing.md` §12.1 (일보 전망 유도), `sim/table4_two_component.py`, `sim/check_multitype.py` |
| Remark (θ_h의 영향) | `msom_reframing.md` §12.1 하단 수치 |
| Proposition 2 | 원고 Prop 8, 증명 한 줄 (아핀 함수의 아래 포락선은 오목) |
| Proposition 3 | `msom_reframing.md` §8 보조정리 1, B1, B2, `sim/check_proofs.py` |
| Proposition 4 | `msom_reframing.md` §8 명제 A, 보조정리 3, `sim/sim_capacity3.py` |

## 다음에 정할 것

1. 원고의 Prop 1–5 (전염, 이질성)를 본문에서 완전히 뺄지, 한 문단과 부록으로 줄일지. 실험이 전염을 약하게 지지하므로 후자를 권한다.
2. 명제 번호와 개수: 본문 4개로 줄였다 (기존 8개 + 따름정리 1). 나머지는 부록.
3. Figure 1 (임계 대 θ_w, F), Figure 2 (포트폴리오 지도), Figure 3 (평균 대기 대 계획자) 그리기 및 파라미터 현실화.
4. 5절(증거)의 서술: 두 경로 분해를 표 하나로, 관측 코퍼스는 한 문단으로.
