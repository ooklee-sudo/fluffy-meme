# ISRE-2026-4499 수정안: goal-setting 중심 리프레이밍

데스크 리젝 이후 세 가지 방향으로 고친 원고 텍스트입니다. 원고에 들어갈 부분은 영어로, 설명과 주의사항은 한국어로 썼습니다.

1. 중심 이론을 goal-setting / multitask agency로 바꾸고, loss-chasing은 사전등록한 경쟁 설명으로 내림
2. 큰 모델 문제를 정면으로 다룸: (a) 추가 실험 설계안, (b) 작은 모델이 운영 에이전트로 쓰인다는 근거
3. "principal의 통제 신호로서의 status text"를 서론의 핵심 주장으로 올림

---

## 0. 먼저 지켜야 할 점: 순서를 감추지 않기

리프레이밍할 때 가장 위험한 부분입니다. 원고는 H5–H7(goal visibility, valence, reasoning)이 **Study 1 이후에** 세워졌다고 분명히 밝히고 있습니다. 새 버전에서 goal-setting을 주인공으로 내세우더라도 **처음부터 이 가설을 세운 것처럼 읽히면 안 됩니다** (HARKing). 리뷰어가 사전등록 문서를 열어보면 바로 드러납니다.

해결책은 순서를 오히려 서사로 쓰는 겁니다. "유력한 설명(loss chasing)을 사전등록해서 검증했고, 지지되지 않았다. 데이터가 가리킨 다른 설명(goal visibility)을 세우고, 미리 커밋한 분석 스크립트로 이 둘을 분리하는 2×2 설계(Study 4)로 검증했다." 이 구조라면 goal-setting이 주인공이 되면서도 순서는 정직하게 남습니다. 아래 텍스트는 모두 이 원칙에 맞춰 썼습니다.

---

## 1. 제목 후보

1. **When the Target Is Visible: Goal Signals and Verification Skipping in LLM Operators** (추천)
2. Goals Gone Wild in the Machine: How Principals' Status Text Drives AI Agents to Skip Verification
3. The Prompt as a Control Signal: Goal Visibility, Reasoning, and Shortcut Taking in Delegated AI Maintenance

1번은 핵심 결과를 담고 있고 차분합니다. 2번은 Ordóñez et al. (2009)을 직접 가리켜서 눈에 띄지만, 에디터에 따라 가볍게 볼 수 있습니다.

---

## 2. Abstract (새 버전)

> Organizations increasingly delegate operational decisions to agents built on large language models (LLMs), and the status text the principal writes is the main channel through which goals reach the agent. Drawing on goal-setting and multitask agency theory, we examine whether that text induces an LLM operator to skip verification, a shortcut that is dominated in expected value and invisible to the principal. In a rule-scored maintenance environment, we first report a registered test of a prominent alternative account, that describing a failed update as a loss induces loss chasing; it is not supported. We then show, with every message written in 16 independently generated wordings so that wording is the unit of replication, that what moves the operator is the goal. In a fast commercial model (Claude Haiku 4.5) with three turns left, stating the target in the status line raised verification skipping by 30 to 54 percentage points whatever the valence of the sentence, whereas loss text lowered it; when the target was visible nowhere in the prompt, skipping in non-goal frames fell to zero. Time pressure was necessary (27.2% skipping with three turns left, 0.5% with six, none with twelve), extended reasoning cut skipping from 27.2% to 9.7%, and stating each option's expected value reduced but did not remove it. A small model from a second vendor (Gemini 2.5 Flash-Lite) showed the same pattern, while three larger reasoning tiers (Sonnet 5.5, Opus 5.5, Fable 5.1) did not skip, which marks model capability and reasoning budget as boundary conditions that the principal also controls. We contribute (i) evidence that goal specificity, a known driver of shortcut taking in human agents, carries over to AI agents through the text that delegates the task, (ii) a conceptualization of status text as a configurable control signal in AI delegation, and (iii) an audit design, with wording as the unit of replication, that organizations can run before delegating to a candidate model.

**설명**: 숫자는 모두 원고에서 가져왔습니다 (Study 2, 3, 4, 6). "30 to 54"는 Study 4에서 facts line에 target이 있을 때의 goal effect 범위(loss text +30.2, neutral text +54.2)입니다. (a) 실험을 실제로 돌리면 마지막에서 두 번째 문장을 그 결과에 맞게 바꿔야 합니다.

---

## 3. Introduction (전면 재작성)

> **1. Introduction**
>
> Organizations increasingly delegate operational work to agents built on large language models (LLMs): triaging incidents, applying patches, and maintaining the very models they run on. Delegation of this kind recreates a classic agency problem. The principal cannot watch every step the agent takes, and verification, the step that protects the principal from hidden failures, is precisely the kind of effort that goes unobserved (Jensen and Meckling 1976; Eisenhardt 1989). Skipped verification leaves hidden technical debt that surfaces later and elsewhere (Sculley et al. 2015).
>
> With human agents, organizations manage this problem with incentives, monitoring, and goals. With an LLM agent, most of these levers collapse into a single artifact: the text the principal writes to describe the task and its status. A dashboard line such as "6 points remain to the target of 108" is not a neutral report; it is a control signal through which the principal directs the agent (Kellogg et al. 2020). Research on algorithmic control has asked how systems monitor and direct human workers, and research on automation has asked when humans rely on machines (Raisch and Krakowski 2021). Much less is known about the reverse direction: how the signals a principal sends shape the behavior of an AI agent, and which of them induce shortcuts.
>
> Goal-setting theory gives a reason to expect that some will. Specific, visible goals raise effort and performance (Locke and Latham 2002), but the same specificity leads agents to take shortcuts, take risks, and bend rules when the goal is hard to reach (Schweitzer et al. 2004; Ordóñez et al. 2009; Larrick et al. 2009). Multitask agency theory sharpens the prediction: when the principal measures one dimension of performance and not another, agents shift effort toward the measured dimension (Holmström and Milgrom 1991; Kerr 1975). A target stated in quality points measures the outcome and says nothing about verification. If an LLM agent responds to goals as human agents do, then stating the target, especially when little time remains, should make it more willing to trade verification for speed, even when skipping verification is worse in expected value.
>
> A prominent alternative locates the risk elsewhere. Prospect theory predicts that a decision maker below a reference point becomes risk seeking (Kahneman and Tversky 1979; Tversky and Kahneman 1981), and in sequences of gambles this appears as loss chasing (Thaler and Johnson 1990). On this account, the dangerous status line is the one that says "the last update cost us two points," not the one that names the target. Prior work on LLMs as decision makers has asked mainly whether models reproduce such human biases in one-shot choices (Horton 2023; Ross et al. 2024). Because the two accounts make opposite predictions about which message is risky, telling them apart matters for anyone who writes the messages an AI agent reads.
>
> We place an LLM in the role of an on-call lead for a deployed model and vary the status text it reads, holding the facts constant. Every option that skips verification is strictly worse in expected value than its verified counterpart, all outcomes are scored by rule, and no human participants are involved. We registered the loss-chasing account in advance as our hypothesis (Study 1). It was not supported, and the model that skipped did so only under time pressure and least of all under loss text (Study 2). We then stated a goal-visibility account and tested it against loss chasing in a 2 × 2 design that separates the valence of the sentence from whether it names the target, with analysis scripts committed before the runs (Study 4). Because a single sentence per condition confounds the condition with the sentence, every frame in Studies 2 to 6 is written in 16 independently generated wordings, and wording is the unit of replication.
>
> The results favor the goal account. In a fast commercial model (Claude Haiku 4.5) with three turns left, stating the target raised verification skipping by 30 to 54 percentage points, whether the sentence was neutral or described a loss, while loss text lowered skipping. When the target appeared nowhere in the prompt, the operator did not skip in non-goal frames at all. Extended reasoning removed most of the effect (Study 3), and stating each option's expected value reduced it without removing it (Study 5). A small model from a second vendor showed the same pattern (Study 6). Three larger commercial tiers that reason by default did not skip in any condition; we treat this not as a failure to replicate but as a boundary condition, because model tier and reasoning budget are themselves configuration choices that the principal makes, often under cost pressure that favors small, fast models (Section 2.4; Study 7).
>
> The paper makes three contributions. First, it extends goal-setting and multitask agency theory to AI agents: the specificity that induces shortcuts in human agents induces them in LLM agents too, through the text that delegates the task, and the effect does not run through loss accounting. Second, it conceptualizes status text as a control signal in AI delegation, with four configurable dimensions (goal specification, valence, time budget, and deliberation allowance) and identifies which of them govern verification. Third, it offers a method: a human-subject-free audit in which wording is the unit of replication and behavior is benchmarked against the expected-value-maximizing action, which organizations can run on a candidate operator before delegating to it.

**설명**
- 첫 단락부터 "에이전시 문제 + 검증은 관찰 불가능한 노력"으로 시작해서 IS 독자에게 왜 중요한지를 먼저 보여줍니다.
- 둘째 단락이 원래 11.2절 3번째 단락에 있던 "통제 신호" 개념을 서론으로 끌어올린 부분입니다.
- loss chasing은 넷째 단락에서 "유력한 경쟁 설명"으로만 등장합니다.
- 기여를 넷에서 셋으로 줄였습니다. 원래의 둘째 기여(사전등록 검증)와 넷째 기여(floor 효과)는 독립된 기여가 아니라 첫째 기여의 근거와 경계 조건으로 흡수했습니다.
- **새 인용 3개는 반드시 원문을 확인하세요**: Holmström & Milgrom (1991, *JLEO*), Kerr (1975, *AMJ*), Larrick, Heath & Wu (2009, *Social Cognition*, "Goal-induced risk taking in negotiation and decision making"). 특히 Larrick et al. (2009)은 "목표가 위험 감수를 유발한다"는 주장에 가장 직접적인 근거라서 꼭 넣을 가치가 있지만, 서지 정보는 제가 기억에 의존한 것이라 확인이 필요합니다.

---

## 4. Section 2 재구성

### 새 구조

| 새 절 | 내용 | 원래 위치 |
|---|---|---|
| 2.1 Goals, specificity, and shortcut taking | Locke & Latham, Schweitzer et al., Ordóñez et al., Larrick et al., Heath et al. 1999, Kivetz et al. 2006 | 2.5 앞부분 (확장) |
| 2.2 Status text as a control signal in AI delegation | 에이전시, multitask, 알고리즘 통제, 네 가지 차원 정의 | 서론 + 11.2 (확장) |
| 2.3 A rival account: reference dependence and loss chasing | prospect theory, 사전등록 가설 H1–H4, 세 조건 정의 | 2.1 + 2.4 (축소) |
| 2.4 LLM agents as decision makers, and the boundary set by capability | LLM 의사결정 문헌 + 작은 모델이 운영에 쓰인다는 근거 | 2.2 + 신규 |
| 2.5 Hypotheses and conceptual model | Box 1 개정 | 2.5 + 2.6 |

2.3(maintenance as repeated risky choice)의 status quo bias 부분은 2.3 안의 한 단락으로 합치면 됩니다.

### 2.2 본문 (새로 쓴 핵심 절)

> **2.2 Status text as a control signal in AI delegation**
>
> In delegation to a human agent, a principal steers behavior through several channels at once: contracts, incentives, monitoring, socialization, and goals. In delegation to an LLM agent, these channels narrow. The agent has no stake in a bonus, cannot be socialized over time within a single episode, and acts on what its context contains. The text that describes the task and its current status therefore carries most of the control that the principal can exercise at run time. We call this text the delegation interface, and we treat it as a control signal in the sense of the algorithmic-control literature (Kellogg et al. 2020), with the direction reversed: the principal is human and the controlled worker is the algorithm.
>
> We distinguish four dimensions of the delegation interface that a principal sets, often without treating them as choices. *Goal specification* is whether, and how prominently, the text states a target and the gap to it. *Valence* is whether the same facts are described as a loss, a gain, or neutral status. *Time budget* is how much of the allotted effort remains, as stated in the text. *Deliberation allowance* is whether the agent is configured to reason before acting, and with what budget; together with the choice of model tier, it determines how much computation the agent spends on each decision. A fifth element, the *information about options* (whether expected consequences are stated), is also under the principal's control and serves here as a check on whether a shortcut is chosen despite visible dominance.
>
> Multitask agency theory predicts how these dimensions bear on verification. When a principal rewards or emphasizes one dimension of performance that it can measure, an agent shifts effort away from dimensions it cannot (Holmström and Milgrom 1991); organizations that reward A while hoping for B get A (Kerr 1975). A status line that states a quality target makes quality the measured dimension and leaves verification unmentioned. The prediction is that goal specification raises the willingness to skip verification, most of all when the time budget is short and closing the gap requires speed. Valence, on this account, should matter little, because a loss description changes the reference point that is described but not the goal that is measured. Deliberation allowance should work in the opposite direction: an agent that reasons before acting has more opportunity to notice that a shortcut is inferior.

### Box 1 개정안

| 제안 | 내용 | 가설 | 사전등록 여부 | Study |
|---|---|---|---|---|
| P1 Goal specification | target이 보이면 skipping이 증가한다 (valence와 무관하게) | H5 | Study 1 이후 설정, 스크립트 사전 커밋 | 4 (핵심), 2, 5, 6 |
| P2 Time budget | P1의 효과는 남은 턴이 적을 때 나타난다 | 설계 요인 | Study 1 이후 | 2, 6 |
| P3 Deliberation | reasoning이 skipping을 줄인다 | H7 | Study 1 이후 | 3 |
| P4 Capability boundary | 기본으로 reasoning하는 큰 모델은 skip하지 않는다 (경계 조건) | H7 | Study 1 이후 | 2, 7 |
| R1 Rival: loss chasing | loss text가 skipping을 늘린다 → **기각** | H1–H4, H6 | **사전등록** | 1, 2, 4 |
| C1 Visible dominance check | 기대값을 보여줘도 goal frame에서 skipping이 남는가 | – | Study 1 이후 | 5 |

표 아래에 원래 note처럼 등록 여부를 명시하세요. 이 표 자체가 "순서를 정직하게 밝히는" 장치가 됩니다.

### Study 순서

Study 번호는 실행 순서대로 그대로 두되, 본문 서술의 무게중심을 Study 4로 옮기는 게 좋습니다. 구체적으로:
- Study 1은 "Registered test of the rival account"로 제목을 바꾸고 분량을 줄입니다 (Table 4의 H2 논의는 measurement argument로 Online Appendix에 보내도 됩니다).
- Study 4 제목을 "Separating goal specification from valence"로 하고 Figure 2를 논문의 대표 그림으로 씁니다.
- 서론과 결론에서 Study 4를 가장 먼저 인용합니다.

---

## 5. 큰 모델 문제

리뷰어의 질문은 "능력이 오르면 사라지는 현상을 왜 연구하나"입니다. 답은 두 갈래이고, **둘 다 하는 게 가장 강합니다**.

### (a) Study 7: 큰 모델에서 skip이 생기는 조건 찾기 (설계안)

> **업데이트 (파일럿 결과)**: `skipver/` 코드로 셀당 5회씩 파일럿을 돌렸더니 L0(Haiku 5.5), L1(Sonnet 5.5 minimal effort, reasoning 토큰 0), L2(1–2턴), L3(SLA 문구) **모두 0/240**이었습니다. 그리고 Sonnet 5.5는 OpenRouter에서 reasoning을 아예 끌 수 없습니다. 이 결과가 본 실험에서도 유지되면 (a)로는 큰 모델 문제를 풀기 어렵고, 아래 (b) 논리도 약해집니다(현재 세대 fast tier도 skip하지 않으므로). 그 경우 범위를 "이전 세대 / 저가 모델"로 분명히 좁히고, audit 방법론의 가치를 강조하는 쪽이 정직합니다. 자세한 내용은 `skipver/README.md`.

> 이 레포에는 이 논문의 실험 코드가 없어서 직접 돌리지 못했습니다. 아래는 기존 환경(Table 2 payoff, 16 wordings, 사전 커밋된 스크립트)을 그대로 확장하는 설계안입니다.

**원칙**: 한 번에 하나씩 압력을 올리는 사다리(ladder) 설계로, Sonnet 5.5부터 시작합니다 (Opus/Fable 대비 비용이 낮고 floor가 같음). 각 단계에서 skip이 5%를 넘으면 그 단계에서 Study 4의 2×2(valence × target)를 돌립니다. Study 6의 screening rule과 같은 논리라서 리뷰어에게 설명하기 쉽습니다. **screening rule과 단계 순서를 실행 전에 커밋하세요.**

| 단계 | 조작 | 근거 | 예상 비용 (Sonnet, 셀당 30회) |
|---|---|---|---|
| L0 | 현재 설계, 3턴 (기준선, 이미 0%) | – | 0 |
| L1 | **Deliberation 낮추기**: 기본 reasoning을 끄거나 최소 budget으로 | Study 3의 거울상. Haiku에서 thinking이 skip을 줄였으므로, 큰 모델에서 thinking을 줄이면 skip이 생기는지 보는 게 가장 직접적인 검증. 실무에서도 지연시간 때문에 reasoning을 끄는 경우가 많음 | 1,440 |
| L2 | **더 강한 deadline**: 1턴 남음 + verified 옵션은 1턴 초과로 마감 넘김 | 현재는 3턴 남아도 narrow_patch(2턴)가 가능해서 큰 모델에겐 trade-off가 약함. verified 경로로는 마감 내 target 도달이 불가능하도록 | 1,440 |
| L3 | **Goal stakes 올리기**: system role에 "target 미달 시 서비스 SLA 위반"을 추가 | goal-setting 문헌에서 shortcut은 목표가 어렵고 중요할 때 증가 (Ordóñez et al. 2009). 단, 이는 payoff를 바꾸므로 EV 지배 관계를 다시 계산해서 skip이 여전히 지배되도록 유지 | 1,440 |
| L4 | **Agentic 형식**: 6개 선택지 대신 tool call(`run_tests`, `deploy`, `rollback`)로 다회 에피소드, 테스트 실행이 실제로 턴을 소모 | 선택지 목록에 "skip regression tests"라고 써 있으면 큰 모델이 바로 알아봄. tool 형식에서는 검증을 "안 부르는 것"이 shortcut이 되어 생략이 덜 눈에 띔. Chen et al. (2026), Saebo et al. (2026)이 보고한 장기 과제 압력과 연결 | 설계 비용 큼, 1,440+ |

**해석 규칙도 미리 정하세요**:
- 어떤 단계에서 skip이 생기고 goal effect가 같은 방향이면 → "능력은 효과를 없애는 게 아니라 문턱을 올린다"는 주장이 가능 (가장 좋은 결과).
- L1에서만 생기면 → P3/P4를 "deliberation allowance가 핵심 통제 변수"로 강화.
- 어디서도 안 생기면 → 그것도 보고하고, (b)의 실무적 관련성으로 방어. L4까지 0%면 "이 문제는 작은 모델과 reasoning을 끈 설정의 문제"라고 범위를 분명히 하면 됩니다.

**주의**: L3과 L4는 환경을 바꾸므로 "같은 환경에서의 비교"가 아니게 됩니다. 본문은 L1, L2로 하고 L3, L4는 확장 분석으로 두는 게 안전합니다. 비용이 제한적이면 **L1 하나만으로도** 큰 모델 문제에 대한 답이 크게 강해집니다.

### (b) 실무 관련성 단락 (2.4절 또는 Discussion에 삽입)

> The larger tiers in our study did not skip, and a reader may ask whether the phenomenon will disappear as models improve. Three considerations suggest that it remains relevant. First, operational agents are often not frontier models. Because agents call a model many times per task, cost and latency push designers toward small, fast models for routine steps: model cascades and routers are built specifically to send most calls to cheaper models (Chen et al. 2023; Ong et al. 2025), and a position paper from NVIDIA researchers argues that small language models are sufficient and more economical for many agentic invocations (Belcak et al. 2025). Providers market their fast tiers for exactly this role; Anthropic positions Claude Haiku 4.5, the model in which we observe skipping, as a sub-agent that carries out targeted actions under the direction of a larger orchestrating model (Anthropic 2025). Second, reasoning is a configurable setting, not a fixed property, and it is often reduced in production to save latency and cost; our Study 3 shows that the same model skipped in 27% of first choices without reasoning and 10% with it. Third, each new release of a fast tier is a new operator whose sensitivity to goal signals is unknown until measured; one of the two small Gemini models in Study 6 skipped and the other did not. The boundary we observe in larger tiers is therefore a boundary on the operator a principal chooses, not on the problem.

**인용 확인 결과**

| 인용 | 확인 | 서지 |
|---|---|---|
| Belcak et al. 2025 | ✅ | Belcak, P., Heinrich, G., Diao, S., Fu, Y., Dong, X., Muralidharan, S., Lin, Y. C., Molchanov, P. "Small Language Models are the Future of Agentic AI." arXiv:2506.02153 (position paper) |
| Ong et al. 2025 | ✅ | Ong, I. et al. "RouteLLM: Learning to Route LLMs from Preference Data." ICLR 2025. arXiv:2406.18665. 품질 손실 없이 비용 2배 이상 절감 보고 |
| Chen et al. 2023 | ✅ (게재지 확인 필요) | Chen, L., Zaharia, M., Zou, J. "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance." arXiv:2305.05176. TMLR 게재본이 있는지는 확인하지 못했으니 OpenReview에서 확인 후 인용 |
| Anthropic 2025 | ⚠️ 1차 출처 확인 필요 | Haiku 4.5 출시 발표 (2025년 10월). 2차 보도는 Sonnet이 계획하고 여러 Haiku 4.5가 하위 작업을 병렬 수행하는 구조를 Anthropic이 직접 설명했다고 전함. Anthropic 공식 발표문을 열어 문구를 확인하고 인용하세요 |
| Aubakirova et al. 2026 (선택) | ⚠️ | "State of AI: An Empirical 100 Trillion Token Study with OpenRouter" (a16z × OpenRouter), arXiv:2601.10088. 실제 사용 데이터라 "작은 모델이 많이 쓰인다"는 근거로 강력할 수 있지만, 저는 2차 보도만 확인했고 roleplay 비중이 크다는 비판도 있습니다. 원문에서 작은/빠른 모델의 토큰 비중을 직접 확인한 뒤에만 쓰세요 |

---

## 6. Discussion 11.2 개정 (Theoretical contributions)

> **11.2 Theoretical contributions**
>
> *Goal setting in AI agents.* Our central contribution is to show that goal specificity, a known driver of shortcut taking in human agents (Schweitzer et al. 2004; Ordóñez et al. 2009), drives it in LLM agents as well, and that it does so through the text that delegates the task. In the fast commercial model, stating the target raised verification skipping by tens of percentage points whatever the valence, and removing the target from the prompt removed skipping in the frames that did not state it. The pattern fits the multitask prediction that a measured outcome draws effort away from an unmeasured one (Holmström and Milgrom 1991): the status line measured quality, and the operator traded away verification, which it did not mention. We do not claim that a language model has motives or identify a mechanism inside the model; the claim is about the mapping from the principal's signal to the agent's behavior, which is what a principal can configure.
>
> *Ruling out loss chasing.* The registered test and the 2 × 2 design separate two accounts that framing studies of LLMs often leave confounded, because a "gain-to-goal" frame both changes valence and names the goal. Loss text did not raise skipping in any model with variation; it lowered it. A prospect-theoretic reading survives only if the target is treated as a future reference point, in which case the data say that the future reference point, not the past one, moves the choice (Heath et al. 1999). Either way, the practical warning that loss-worded alerts make AI operators reckless is not supported here.
>
> *Status text as a control signal.* For information systems research, the results add a third element to the study of control in human–algorithm work. Research on algorithmic control examines how systems direct human workers (Kellogg et al. 2020), and research on automation examines when humans rely on machines (Raisch and Krakowski 2021). Here the direction is reversed: the principal controls an algorithm, and the control signal is text the principal may not regard as a design choice. We identify which dimensions of that signal govern a hidden action: goal specification and time budget raise verification skipping, deliberation allowance lowers it, and valence does not raise it.
>
> *Capability as a boundary condition.* Three larger tiers that reason by default did not skip. We read this as a boundary on the phenomenon that is itself set by the principal, through the choice of model and reasoning budget, and not as evidence that the phenomenon is transient. [Study 7 결과에 따라 한 문장 추가.]
>
> *Method.* [원래의 measurement argument (i)–(vi)를 그대로 두되 한 단락으로 압축.]

---

## 7. 남은 체크리스트

- [ ] 새 인용 3개 원문 확인: Holmström & Milgrom 1991, Kerr 1975, Larrick, Heath & Wu 2009
- [ ] Anthropic Haiku 4.5 발표문 1차 출처 확인, FrugalGPT 게재지 확인
- [ ] Study 7 screening rule과 단계 순서를 실행 전에 커밋 (최소 L1)
- [ ] 결론(11.5)과 키워드를 goal 중심으로 수정 (예: goal setting; multitask agency; delegation to AI; LLM agents; algorithmic control; verification; behavioral audit). "prospect theory"는 키워드에서 빼도 됩니다
- [ ] Limitations 첫 문단을 "capability boundary"와 연결해서 다시 쓰기
- [ ] cover letter에서 ISR 리젝을 언급할지 결정 (저널에 따라 이전 리젝 이력을 묻기도 함)
