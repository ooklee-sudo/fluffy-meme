# 초안: Abstract, 도입, 과제 설계, Audit sidebar, 한계, 결론

IEEE Intelligent Systems 버전의 나머지 섹션입니다. 인용은 {이름} 형태로 표시했고, `ieee_is_manuscript.md`로 합칠 때 등장 순서대로 번호를 매깁니다.

---

## ABSTRACT

Organizations are starting to let large language model (LLM) agents run maintenance pipelines, including the decision to skip regression tests. In a rule-scored maintenance task in which skipping tests is always worse in expected value, we varied the status prompt and the order of the options across 11 models. In a fast commercial model, adding the quality target to the status line raised skipping by 16 percentage points, whereas describing the last result as a loss did not. Option order mattered as much: depending on which option came first, the same model skipped in 0% to 69% of decisions, and the order that triggered skipping differed across models, so a single test layout can make a risky model look safe. Larger models never skipped. Enabling reasoning and stating each option's expected value together removed skipping in the fast model. We describe an audit that organizations can run before delegating.

---

## (INTRODUCTION, no heading)

Large language model (LLM) agents are moving from answering questions to operating systems: triaging incidents, applying patches, and maintaining the models that serve users. Maintenance decisions look routine. An operator can hold, apply a small or large fix, run or skip the regression tests, or roll back. Skipping the tests saves time and usually goes unnoticed, which is exactly why it is risky: untested changes accumulate as hidden technical debt that surfaces later and elsewhere {Sculley}. When the operator is an agent, the organization that delegates the work cannot watch each step, and verification is the kind of effort a principal cannot easily observe {Jensen}.

With a human operator, organizations steer this effort through training, incentives, and supervision. With an LLM operator, most of that steering runs through text: the status message the agent reads and the list of actions it may take. That text works as a control signal {Kellogg}, and recent studies show that agents placed under pressure can trade safety or honesty for a stated objective {Scheurer}, {Jiang}, {Chen}. Work on LLMs as economic decision makers has mostly asked whether models copy human biases in one-shot choices {Horton}, {Ross}. We ask a narrower, operational question: which features of the prompt that delegates a maintenance decision make an LLM operator skip verification when skipping is clearly the worse choice?

We built a maintenance task in which every outcome is scored by rule and both test-skipping options have lower expected value than their tested counterparts. We varied the headline of the status message, wrote each headline in 16 independently generated wordings, rotated the order of the options, and recorded more than 38,000 decisions from 11 models.

Four results follow. Stating the quality target, not describing a loss, is what raised skipping in the models that skipped. The order of the options mattered as much as the wording, and the order that triggered skipping differed from model to model. Larger models never skipped. And two settings a deployer controls, reasoning before answering and stating each option's expected value, removed skipping when used together.

These results matter because the models most likely to run routine operations are not always the most capable ones. Agents call a model many times per task, and cost and latency push designers toward small, fast models {Belcak}, {Ong}. We close with an audit that organizations can run on a candidate operator before delegating to it.

---

## A MAINTENANCE TASK WITH A KNOWN RIGHT ANSWER

The operator plays the on-call lead for a deployed LLM during a maintenance window of 12 turns. Model quality starts at 100, the target is 108, and the stable baseline is 100. Each turn, the operator picks one of six actions: hold; a small fix with regression tests (two turns); a small fix without tests (one turn); a large fix with tests (three turns); a large fix without tests (one turn); or roll back to the baseline (one turn).

Each fix succeeds or fails by a hidden draw with fixed probabilities, so every action has a known expected change in quality (see Figure 1). The tested small fix gains 0.50 points on average and the tested large fix 0.60, whereas the untested small fix loses 0.35 and the untested large fix loses 2.20. Skipping tests saves turns but is always worse in expected value, so any skipping is a departure from the best choice in quality terms, not a matter of taste. The operator does not see these numbers in the main conditions; it sees short descriptions such as "large fix, skip regression tests; large gain, very high risk of a severe incident, costs 1 turn."

Every prompt has the same structure (see Figure 1). A fixed system message sets the role and the objective, to maximize final quality, and asks for a JSON answer. The user message then gives a one-sentence headline, a facts line with the current quality, the target, the turns left, and the gap to the target, and the list of six actions. Across conditions, only the headline, the presence of the target in the facts line, the number of turns left, and the order of the actions change; the facts are always the same.

A single sentence per condition would confound the condition with that sentence. We therefore wrote each headline in 16 wordings, generated by a language model that saw only the facts and placeholders, not the research question, and accepted by mechanical rules (required placeholders only, no numbers, no vocabulary from another headline type). The wordings were fixed before any run. The order of the actions was rotated across decisions so that, within each wording and headline, each action appeared first equally often.

We analyze only the operator's first decision in each episode, because later decisions depend on earlier draws. Each combination of headline and wording received 30 decisions, five per layout, unless stated otherwise. Models were called through a commercial aggregator at temperature 0.7 where the model accepts it; models that reason by default ran at their default settings. Because the wording is the unit of replication, we report means over wordings with 95% intervals from a bootstrap that resamples wordings. A model that never skipped is reported as a floor, not as evidence of no effect. Code, prompts, wordings, and logs are available in the supplementary material.

---

## SIDEBAR: AUDITING AN LLM OPERATOR BEFORE DELEGATION

An organization considering an LLM operator for routine decisions can test it on its own payoff structure before deployment. The procedure below needs no human participants and can be repeated whenever the model or its prompts change.

1) Define the right answer first. Score each decision against the action with the highest expected value in that state. A simpler test, such as whether risk taking rises after failures, can reward the wrong behavior when a safe retreat is available.

2) Write every message many ways. Generate many independent wordings of each status message and treat the wording, not the single decision, as the unit of replication. One sentence can produce anything from no shortcuts to nearly all.

3) Rotate the options. Present the actions in several orders and report results by order as well as on average. The order that triggers shortcuts differs across models.

4) Test the deployed configuration. Run the model with the reasoning setting, output limits, and option descriptions it will have in production. Reasoning and stated expected values each changed the result, and together they removed skipping in our task.

5) Separate the goal from the tone. Vary whether a message states the target independently of whether it describes a loss. A "progress toward the goal" message changes both at once.

6) Report floors as floors. A model that never takes the shortcut tells you the shortcut is rare under the tested conditions, not that the message design is harmless.

7) Re-audit after changes. A new model version, a reworded status line, or a reordered tool list is a new operator. In our study, two small models from the same vendor differed threefold.

---

## LIMITATIONS

Our task is a single synthetic setting with six closed actions and a scalar quality score, and we analyze only first decisions, so we do not observe how shortcuts accumulate over an episode. The wordings were generated by one language model and filtered by rule; they are a structured sample, not all possible phrasings. Turning on extended reasoning also removes the temperature setting, so the reasoning comparison changes two things at once. The larger models were run with fewer decisions per condition, and one was tested in a single layout only. Results depend on model versions available at the time of the runs. Stating expected values lengthens every option and may signal what the designer expects. Finally, our design measures how prompt features change choices, not why: the explanations models gave were not used as evidence.

---

## CONCLUSION

Whether an LLM operator skips verification is not a fixed property of the model. In our task it depended on whether the prompt named the target, on the order of the options, on whether the model reasoned, and on whether it was told the expected value of each option, and the larger models did not skip at all. For organizations, the practical message is that prompt layout is configuration: it should be versioned, tested in several forms, and audited again when it or the model changes. Future work should test longer, tool-based episodes in which verification is an action the agent must remember to take rather than an option on a list, and apply the same audit to logs from live maintenance tickets.

---

## 메모

- **Abstract 단어 수**: 합본 스크립트에서 자동으로 셉니다 (150 이하 확인).
- **"more than 38,000 decisions from 11 models"**: 순서 균형 실행의 첫 결정 38,496회, 모델 11개 (Fable 5.1은 고정 배치라 제외).
- **도입의 "two small models from the same vendor differed threefold"** (sidebar 7번): Gemini 3.1 Flash-Lite 12.9% vs Gemini 2.5 Flash-Lite 4.2%.
- **"models were called through a commercial aggregator"**: OpenRouter. 원 원고는 Anthropic API를 직접 썼습니다. 익명 심사라면 "a commercial aggregator"로 두고, 최종본에서 이름을 밝히세요.
- **사전등록**: Goals 섹션에서만 언급합니다. 과제 설계 섹션에는 넣지 않았습니다.
- **그림 1**: 과제 설계 섹션이 두 번 참조합니다(기대값, 프롬프트 구조). 다이어그램은 직접 그려야 합니다.
