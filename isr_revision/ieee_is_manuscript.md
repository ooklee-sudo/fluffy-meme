*FEATURE ARTICLE: AUDITING AI OPERATORS*

# Same Model, Different Shortcuts: How Prompt Layout Steers LLM Operators to Skip Verification

[Author names and affiliations]

**Abstract**—Organizations are starting to let large language model (LLM) agents run maintenance pipelines, including the decision to skip regression tests. In a rule-scored maintenance task in which skipping tests is always worse in expected value, we varied the status prompt and the order of the options across 11 models. In a fast commercial model, adding the quality target to the status line raised skipping by 16 percentage points, whereas describing the last result as a loss did not. Option order mattered as much: depending on which option came first, the same model skipped in 0% to 69% of decisions, and the order that triggered skipping differed across models, so a single test layout can make a risky model look safe. Larger models never skipped. Enabling reasoning and stating each option's expected value together removed skipping in the fast model. We describe an audit that organizations can run before delegating.

Large language model (LLM) agents are moving from answering questions to operating systems: triaging incidents, applying patches, and maintaining the models that serve users. Maintenance decisions look routine. An operator can hold, apply a small or large fix, run or skip the regression tests, or roll back. Skipping the tests saves time and usually goes unnoticed, which is exactly why it is risky: untested changes accumulate as hidden technical debt that surfaces later and elsewhere.^1^ When the operator is an agent, the organization that delegates the work cannot watch each step, and verification is the kind of effort a principal cannot easily observe.^2^

With a human operator, organizations steer this effort through training, incentives, and supervision. With an LLM operator, most of that steering runs through text: the status message the agent reads and the list of actions it may take. That text works as a control signal,^3^ and recent studies show that agents placed under pressure can trade safety or honesty for a stated objective ^4–6^. Work on LLMs as economic decision makers has mostly asked whether models copy human biases in one-shot choices.^7,8^ We ask a narrower, operational question: which features of the prompt that delegates a maintenance decision make an LLM operator skip verification when skipping is clearly the worse choice?

We built a maintenance task in which every outcome is scored by rule and both test-skipping options have lower expected value than their tested counterparts. We varied the headline of the status message, wrote each headline in 16 independently generated wordings, rotated the order of the options, and recorded more than 38,000 decisions from 11 models.

Four results follow. Stating the quality target, not describing a loss, is what raised skipping in the models that skipped. The order of the options mattered as much as the wording, and the order that triggered skipping differed from model to model. Larger models never skipped. And two settings a deployer controls, reasoning before answering and stating each option's expected value, removed skipping when used together.

These results matter because the models most likely to run routine operations are not always the most capable ones. Agents call a model many times per task, and cost and latency push designers toward small, fast models.^9,10^ We close with an audit that organizations can run on a candidate operator before delegating to it.

## A MAINTENANCE TASK WITH A KNOWN RIGHT ANSWER

The operator plays the on-call lead for a deployed LLM during a maintenance window of 12 turns. Model quality starts at 100, the target is 108, and the stable baseline is 100. Each turn, the operator picks one of six actions: hold; a small fix with regression tests (two turns); a small fix without tests (one turn); a large fix with tests (three turns); a large fix without tests (one turn); or roll back to the baseline (one turn).

Each fix succeeds or fails by a hidden draw with fixed probabilities, so every action has a known expected change in quality (see Figure 1). The tested small fix gains 0.50 points on average and the tested large fix 0.60, whereas the untested small fix loses 0.35 and the untested large fix loses 2.20. Skipping tests saves turns but is always worse in expected value, so any skipping is a departure from the best choice in quality terms, not a matter of taste. The operator does not see these numbers in the main conditions; it sees short descriptions such as "large fix, skip regression tests; large gain, very high risk of a severe incident, costs 1 turn."

Every prompt has the same structure (see Figure 1). A fixed system message sets the role and the objective, to maximize final quality, and asks for a JSON answer. The user message then gives a one-sentence headline, a facts line with the current quality, the target, the turns left, and the gap to the target, and the list of six actions. Across conditions, only the headline, the presence of the target in the facts line, the number of turns left, and the order of the actions change; the facts are always the same.

A single sentence per condition would confound the condition with that sentence. We therefore wrote each headline in 16 wordings, generated by a language model that saw only the facts and placeholders, not the research question, and accepted by mechanical rules (required placeholders only, no numbers, no vocabulary from another headline type). The wordings were fixed before any run. The order of the actions was rotated across decisions so that, within each wording and headline, each action appeared first equally often.

We analyze only the operator's first decision in each episode, because later decisions depend on earlier draws. Each combination of headline and wording received 30 decisions, five per layout, unless stated otherwise. Models were called through a commercial aggregator at temperature 0.7 where the model accepts it; models that reason by default ran at their default settings. Because the wording is the unit of replication, we report means over wordings with 95% intervals from a bootstrap that resamples wordings. A model that never skipped is reported as a floor, not as evidence of no effect. Code, prompts, wordings, and logs are available in the supplementary material.

**[FIGURE 1. The status prompt an operator reads, with the parts that vary across conditions marked (headline, target in the facts line, turns left, and option order), and the expected quality change of each action. Both test-skipping actions have lower expected value than their tested counterparts. [Diagram to be drawn.]]**

## GOALS, NOT LOSSES

Two familiar accounts predict that a status message can push an operator toward shortcuts, and they point at different messages. The first comes from prospect theory: a decision maker who sees an outcome as a loss becomes more willing to gamble,^11^ and in sequences of bets this appears as chasing losses to get back to even.^12^ On this account, the risky message is "the last update cost us two points." The second comes from research on goal setting: specific, visible targets raise effort but also invite corner cutting when the target is hard to reach.^13,14^ On this account, the risky message is "eight points remain to the target." An organization writing status messages for an AI operator needs to know which, if either, holds.

Time pressure turned out to be a precondition for any skipping. With twelve turns left, the fast model (Claude Haiku 4.5) never skipped tests in 1,440 first decisions; with six turns left it skipped once. With three turns left, it skipped in 13% of first decisions. All results below use three turns left.

We first tested the loss account as we had preregistered it, with three small models at twelve turns left: describing the last result as a loss did not raise skipping by the preregistered margin in any of them (details are in the supplementary material). Because the commercial model never skipped at twelve turns, that test was limited.

Framing studies often confound the two accounts. A "progress toward the goal" headline both drops the language of loss and names the target, so a difference between it and a loss headline cannot say which change mattered. We therefore crossed the two. Starting from a neutral status headline and a loss headline, we added the same target sentence to each, which gave four headlines: neutral, loss, neutral plus target, and loss plus target. We also kept the usual progress headline. Each headline was written in 16 independently generated wordings, and the facts line below it, which included the target and the gap, was identical across headlines.

The target sentence mattered and the loss language did not (see Figure 2). Adding the target to a neutral headline raised skipping from 9% to 25%, and adding it to a loss headline raised it from 7% to 23%. Both increases are about 16 percentage points, with 95% intervals over wordings that exclude zero, and they appear in 14 and 13 of the 16 wordings, respectively. Describing the last result as a loss, by contrast, made no measurable difference: the loss headline differed from the neutral one by −2 points without the target and by −2 points with it, with wordings split in both directions. Loss language did not make the operator bolder, and it did not make it more careful either. The progress headline (22%) was indistinguishable from the neutral headline with the target added (25%), so its effect in earlier framing designs is better read as an effect of naming the target than of positive wording.

The target needed to be visible somewhere. When we removed the target and the gap from the facts line as well, so that the prompt mentioned no target at all, the neutral and loss headlines produced no skipping in 960 first decisions. Adding the target sentence back into the headline restored some skipping (6% and 5%), less than when the target appeared in both places. When the target appeared only in the headline, its phrasing also mattered: the progress headline, which leads with the remaining gap, produced 16%, about three times as much as a status sentence followed by the target.

A small model from a second vendor, Gemini 2.5 Flash-Lite, skipped far less often (5% at three turns left) but leaned the same way. Adding the target to a loss headline raised skipping by 7 points, adding it to a neutral headline raised it by 2 points with an interval that includes zero, and loss language again did not raise skipping.

The pattern fits the goal account better than the loss account, and it parallels what goal-setting research reports for people: a visible gap under a deadline invites the agent to trade a safeguard for speed.^13,14^ We do not claim that the model holds a goal in any psychological sense, and our design does not reveal how the target sentence changes the choice. The practical claim is narrower: in this task, the sentence that names the target, not the sentence that names the loss, is the one that moves an AI operator toward skipping its tests.

![FIGURE 2. Share of first decisions that skip tests, by status headline (Claude Haiku 4.5, three turns left, option order balanced; bars are means over 16 wordings with 95% intervals). Headlines that state the target (blue) raise skipping whether they are neutral or describe a loss. When the target appears nowhere in the prompt, the other headlines produce no skipping.](/home/user/fluffy-meme/skipver/figures/fig2_goal.png)

## OPTION ORDER MATTERS AS MUCH AS WORDING

Every prompt in our task lists the same six options; only their order can change. A fixed layout, as is common in such evaluations, would show every decision the options in the same order. We instead rotated the list across episodes, so that each wording of each headline appeared equally often with each option in first place. The facts, the payoffs, and the option descriptions were unchanged.

The layout turned out to matter about as much as the headline did (see Figure 3). Averaged over all six layouts, the fast model skipped tests in 17% of first decisions. With the target added to the headline and "hold" at the top of the list, the model skipped tests in 55% to 69% of first decisions; with "rollback" at the top, in 24% to 48%. When a tested fix headed the list, skipping almost disappeared: the model took the small tested fix in 93% of decisions when it was listed first, and in no such decision did it skip. Three of the six layouts accounted for 96% of all skipping.

Layout also changed what the headline did. The goal effect from the previous section, the rise in skipping when the target sentence is added to a neutral or a loss headline, was large when a non-progress option led the list. With hold first, adding the target raised skipping from 15% to 69% under neutral text and from 10% to 55% under loss text; with rollback first, from 3% to 24% and from 0% to 48%. The effect was near zero when a tested fix led the list. It vanished when the untested wide fix was listed first, a layout in which the model skipped in about one-third of decisions under every headline. Averaged over layouts, adding the target raised skipping by 16 percentage points under both neutral and loss text, in 14 and 13 of 16 wordings, so the goal effect is real. But its size depends on a formatting decision that most prompt designers would not think of as a decision at all.

The effect is not a simple preference for whatever comes first. When the untested wide fix was at the top, the model chose it in only 9% of decisions; it more often took the tested wide fix at the bottom of the list or the untested small fix. Across all layouts, the chosen option was in first place in 29% of decisions, second in 26%, and third in 21%, a mild pull toward the top that does not explain the large swings. What the layout seems to change is which options the model weighs against each other when it is short of time and has been shown a gap to close. Our design identifies the effect of layout, not the process behind it.

Sensitivity to option order is known from multiple-choice benchmarks, where reordering the answers changes how often models pick the correct one,^15^ and where much of the bias has been traced to a preference for particular answer labels such as "A" or "B".^16^ Our setting differs in two ways that matter for practice. The options here are named actions with consequences, not labeled answers, so there is no label to prefer. And the order does not add a constant bias; it interacts with the content of the status message, amplifying the goal effect in some layouts and erasing it in others. A layout chosen once, for convenience, can therefore decide whether an audit finds a problem.

This matters for how fixed-layout evaluations should be read. A natural design, rotating options by turn number, shows every first decision the same layout, with hold at the top, and that layout produces the most skipping. Measured on hold-first decisions alone, adding the target raised skipping by 54 points under neutral text, more than three times the 16-point average over layouts. An evaluation that fixes one layout measures that layout, not the model.

For organizations, the lesson is that option order belongs in the audit. An operator should be tested with the options in several orders, and results should be reported by layout as well as on average. In deployment, the order in which a runbook or tool list presents actions is part of the control signal; listing a tested option first may be the cheapest guard available.

![FIGURE 3. The same decisions split by the option listed first. Headlines that state the target raise skipping mainly when hold or rollback heads the list; when a tested fix is listed first, the model takes it. Listing the untested wide fix first yields about one-third skipping under every headline.](/home/user/fluffy-meme/skipver/figures/fig3_order.png)

## WHAT REDUCES SKIPPING

The settings that raise skipping are chosen by whoever deploys the operator, and so are the settings that lower it. We tested two that a deployer can change without retraining anything: letting the model reason before it answers, and telling it the expected value of each option. A third, the order of the options, was covered in the previous section.

Extended reasoning helped, but less than one might hope. With a reasoning budget of 2,000 tokens, the fast model spent about 730 tokens on each decision and skipped tests in 8% of first decisions, down from 13% without reasoning. The reduction appeared in 11 of 16 wordings, and its 95% interval over wordings (−8 to −2 points) excludes zero. The target headline remained the riskiest: with reasoning, the gain headline produced 13% skipping against 5% for the loss headline and 6% for the neutral one. Reasoning also changed where skipping came from. Without it, almost all skipping occurred when hold, rollback, or the untested wide fix led the list; with it, skipping was spread more evenly and appeared even when a tested fix was listed first. Reasoning made the operator less sensitive to layout, not immune to the goal.

Stating expected values helped more. When each option's description ended with its expected change in quality, for example "Expected quality change: −0.35 points" for the untested small fix, skipping fell from 17% to 5% averaged over the five headlines of the goal-visibility design, and it fell in every one of the 16 wordings. The untested wide fix, the option with the worst expected value, was never chosen. Yet skipping did not disappear, and what remained was concentrated: almost all of it came from layouts with hold at the top, where the operator still skipped in 32% of decisions under headlines that stated the target. An operator that is told, in numbers, that a shortcut is worse can still take it when the goal is in view and the layout points away from the tested option.

Neither setting works fully alone, but together they did. When the fast model both reasoned and saw expected values, it did not skip tests in any of 2,400 first decisions, under every headline and in every layout, including the hold-first layouts where expected values alone had left a third of goal-stating decisions skipping. It reasoned somewhat longer than with reasoning alone (about 900 tokens per decision) and mostly chose the tested wide fix (86% of decisions). The combination brought the fast model to the behavior of the larger models in the next section. For a deployer, this is the most actionable result in the study: two configuration changes, neither of which requires a different model, removed the shortcut in this task.

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

## AUDITING AN LLM OPERATOR BEFORE DELEGATION (SIDEBAR)

An organization considering an LLM operator for routine decisions can test it on its own payoff structure before deployment. The procedure below needs no human participants and can be repeated whenever the model or its prompts change.

1) Define the right answer first. Score each decision against the action with the highest expected value in that state. A simpler test, such as whether risk taking rises after failures, can reward the wrong behavior when a safe retreat is available.

2) Write every message many ways. Generate many independent wordings of each status message and treat the wording, not the single decision, as the unit of replication. One sentence can produce anything from no shortcuts to nearly all.

3) Rotate the options. Present the actions in several orders and report results by order as well as on average. The order that triggers shortcuts differs across models.

4) Test the deployed configuration. Run the model with the reasoning setting, output limits, and option descriptions it will have in production. Reasoning and stated expected values each changed the result, and together they removed skipping in our task.

5) Separate the goal from the tone. Vary whether a message states the target independently of whether it describes a loss. A "progress toward the goal" message changes both at once.

6) Report floors as floors. A model that never takes the shortcut tells you the shortcut is rare under the tested conditions, not that the message design is harmless.

7) Re-audit after changes. A new model version, a reworded status line, or a reordered tool list is a new operator. In our study, two small models from the same vendor differed threefold.

## LIMITATIONS

Our task is a single synthetic setting with six closed actions and a scalar quality score, and we analyze only first decisions, so we do not observe how shortcuts accumulate over an episode. The wordings were generated by one language model and filtered by rule; they are a structured sample, not all possible phrasings. Turning on extended reasoning also removes the temperature setting, so the reasoning comparison changes two things at once. The larger models were run with fewer decisions per condition, and one was tested in a single layout only. Results depend on model versions available at the time of the runs. Stating expected values lengthens every option and may signal what the designer expects. Finally, our design measures how prompt features change choices, not why: the explanations models gave were not used as evidence.

## CONCLUSION

Whether an LLM operator skips verification is not a fixed property of the model. In our task it depended on whether the prompt named the target, on the order of the options, on whether the model reasoned, and on whether it was told the expected value of each option, and the larger models did not skip at all. For organizations, the practical message is that prompt layout is configuration: it should be versioned, tested in several forms, and audited again when it or the model changes. Future work should test longer, tool-based episodes in which verification is an action the agent must remember to take rather than an option on a list, and apply the same audit to logs from live maintenance tickets.

## REFERENCES

1. D. Sculley et al., "Hidden technical debt in machine learning systems," in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 28, 2015.
2. M. C. Jensen and W. H. Meckling, "Theory of the firm: Managerial behavior, agency costs and ownership structure," *J. Financial Econ.*, vol. 3, no. 4, pp. 305–360, 1976.
3. K. C. Kellogg, M. A. Valentine, and A. Christin, "Algorithms at work: The new contested terrain of control," *Acad. Manage. Ann.*, vol. 14, no. 1, pp. 366–410, 2020.
4. J. Scheurer, M. Balesni, and M. Hobbhahn, "Large language models can strategically deceive their users when put under pressure," 2023, arXiv:2311.07590.
5. H. Jiang and K. Tang, "Why agents compromise safety under pressure," in *Findings Assoc. Comput. Linguistics: ACL 2026*, 2026, arXiv:2603.14975.
6. H. Chen, Y. Liu, J. Shao, X. Xu, Z. Sun, and W. Hu, "Polished but unresolved: Identifying late-stage pressure states in long-horizon tool-use agents," in *Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP)*, 2026, arXiv:2609.00823.
7. J. J. Horton, "Large language models as simulated economic agents: What can we learn from Homo silicus?" 2023, arXiv:2301.07543.
8. J. Ross, Y. Kim, and A. W. Lo, "LLM economicus? Mapping the behavioral biases of LLMs via utility theory," 2024, arXiv:2408.02784.
9. P. Belcak et al., "Small language models are the future of agentic AI," 2025, arXiv:2506.02153.
10. I. Ong et al., "RouteLLM: Learning to route LLMs from preference data," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2025.
11. D. Kahneman and A. Tversky, "Prospect theory: An analysis of decision under risk," *Econometrica*, vol. 47, no. 2, pp. 263–291, 1979.
12. R. H. Thaler and E. J. Johnson, "Gambling with the house money and trying to break even: The effects of prior outcomes on risky choice," *Manage. Sci.*, vol. 36, no. 6, pp. 643–660, 1990.
13. M. E. Schweitzer, L. Ordóñez, and B. Douma, "Goal setting as a motivator of unethical behavior," *Acad. Manage. J.*, vol. 47, no. 3, pp. 422–432, 2004.
14. L. D. Ordóñez, M. E. Schweitzer, A. D. Galinsky, and M. H. Bazerman, "Goals gone wild: The systematic side effects of overprescribing goal setting," *Acad. Manage. Perspect.*, vol. 23, no. 1, pp. 6–16, 2009.
15. P. Pezeshkpour and E. Hruschka, "Large language models sensitivity to the order of options in multiple-choice questions," in *Findings Assoc. Comput. Linguistics: NAACL 2024*, 2024, pp. 2006–2017.
16. C. Zheng, H. Zhou, F. Meng, J. Zhou, and M. Huang, "Large language models are not robust multiple choice selectors," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2024.

## AUTHOR BIOGRAPHIES

[One paragraph per author, per the template.]
