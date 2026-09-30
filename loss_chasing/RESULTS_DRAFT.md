# Draft: Results section (preliminary)

> Status: draft for the authors. All numbers come from runs of the code in this directory (`data/*.jsonl`, `analyze.py`, `summarize.py`). The Claude Haiku log is not in the repository; its figures are copied from the `analyze.py` output of that run. This is a **partial** execution of the registered grid, and it is reported as such.

## 7. Results

### 7.1 What was run, and where it departs from the registered protocol

| Item | Registered (§5) | Executed |
|---|---|---|
| Models | 3+ developer families, small and large in each | Qwen2.5-1.5B-Instruct, SmolLM2-1.7B-Instruct (open, local CPU), Claude Haiku 4.5 (API). No large model in the open families; one closed-family model |
| Temperatures | 0.0 and 0.7 | Open models: 0.7 only. Haiku: 0.0 and 0.7 |
| Design | 3 frames x injected failures {0,1,3} | as registered |
| Episodes | 100 per cell | 100 per cell (open models: 900 first choices each; Haiku: 1,800) |
| Sample | First free choice after injection (primary) | as registered; later turns **not run**, so H4, chase streak and terminal quality are unreported |
| Output format | JSON only | as registered. For the two open models the string `{"action": "` was pre-filled in the assistant turn, because a 0.5B pilot answered with a bare action name and every response failed to parse. This forces the format and may itself shape the choice |
| Parse failures | mapped to `hold`, flagged | as registered (rates below) |
| H2 | Mean risk index after 3 failures exceeds 0 failures | Reported as registered **and** as an exploratory criterion (below) |

One earlier Haiku attempt was discarded. Every API call in it raised an error that the retry loop swallowed, so all 180 rows were `hold` with 100% parse failure; the analysis was run only to diagnose this. The cause was a client library without a `temperature` argument (the code now passes it in the request body and stops on programming errors instead of hiding them). That log was deleted and is excluded from every result reported here.

### 7.2 H1: loss frame versus gain-to-goal frame

First-choice skip rate (share of `narrow_skip` or `wide_skip`), N = 100 per cell.

| Model | Failures | Gain-to-goal | Loss | Neutral |
|---|---|---|---|---|
| Qwen2.5-1.5B | 0 | 17% | 31% | 21% |
| | 1 | 14% | 15% | 14% |
| | 3 | 8% | 16% | 15% |
| SmolLM2-1.7B | 0 | 5% | 0% | 3% |
| | 1 | 17% | 13% | 14% |
| | 3 | 14% | 8% | 13% |
| Claude Haiku 4.5 | all | 0% | 0% | 0% |

Pooled over failure levels, the loss-minus-gain difference is **+7.7 pp** for Qwen (Holm-adjusted p = 0.012), **-5.0 pp** for SmolLM2 (Holm p = 0.036), and exactly zero for Haiku.

**H1 is not supported for any model.** Qwen's difference has the predicted sign but is below the registered +10 pp threshold; it is reported as a small effect in the operational role. SmolLM2's difference has the opposite sign. For Haiku the test is **not informative**: nobody skips in any condition, so there is no variation to compare (a floor effect). Equal rates of zero are not evidence that framing is irrelevant for the model in general, only that this task elicits no skipping from it.

Qwen's loss-frame excess is concentrated where there is no failure history (31% with zero injected failures, where the headline reads "unrealized cumulative loss is 0"); with failures present the gap is +1 to +8 pp. The zero-failure cell therefore may reflect the wording format rather than loss accounting. The frame x failures interaction is not significant for either open model (Qwen p = 0.56, SmolLM2 p = 0.26).

### 7.3 H2: behaviour after consecutive failures

In this state machine a rollback has a positive expected value after a failure (EV = 2n for n injected failures), so the EV-maximizing policy *lowers* its risk index after failures. The registered H2 (risk index rises) therefore rewards departures from rationality in the wrong direction: a rational agent "fails" it. We report it as registered, then add a **post hoc, exploratory** criterion that measures *excess* risk over the EV-maximizing action in the same state and additionally requires that test-skipping rises after failures (condition 2 of the definition of loss chasing in §3.2).

| Model | Raw risk index, 0 -> 3 failures | Registered H2 | Excess risk over EV-max, 0 -> 3 | Skip rate, 0 -> 3 | Exploratory H2 |
|---|---|---|---|---|---|
| Qwen2.5-1.5B | 0.635 -> 0.568 | not met | +0.035 -> +0.368 | 23.0% -> 13.0% | not supported |
| SmolLM2-1.7B | 0.127 -> 0.184 | met | -0.473 -> -0.016 | 2.7% -> 11.7% | supported |
| Claude Haiku 4.5 | 0.534 -> 0.200 | not met | -0.066 -> 0.000 | 0% -> 0% | not testable |

- **Qwen** does not retreat to rollback after failures (excess risk rises) but skips *less* (logit coefficient for 3 versus 0 failures -0.70, Holm p = 0.003). Its behaviour is an under-response to failure, not test-skipping chase.
- **SmolLM2** skips more after failures (2.7% -> 11.7%; logit +1.58, Holm p = 0.0002), in all three frames (gain 5 -> 14%, loss 0 -> 8%, neutral 3 -> 13%). This is a failure-history effect independent of framing. After three failures its excess risk is about zero (-0.016), i.e. it is not riskier than a rational agent there: the rise starts from a very conservative baseline, and 11.7% is a modest level of skipping. The exploratory criterion is met, but we do not read this as loss chasing without replication.
- **Haiku** behaves like the EV-maximizing policy: it gets an EV gap of 0.000 in the loss frame and -0.003 in the neutral frame (-0.527 in the gain-to-goal frame, where it makes some lower-EV choice that is not riskier, excess risk +0.006). After failures it rolls back as the benchmark does. The automatic H2 flag of an early version of the analysis read "supported" only because all three-failure values were identical (zero variance); this is an artifact, not an effect.

### 7.4 Which interpretive pattern (§9) fits

- **Pattern A** (H1 and H2 both supported): not observed. No model satisfies both.
- **Pattern B** (conservative response, holding or rolling back): Haiku retreats rationally; Qwen does not retreat.
- **Pattern C** (frame effect without failure-count effect): partly, for Qwen's sub-threshold frame effect, but its failure-count effect exists and runs in the opposite direction.
- **Pattern D** (effect vanishes in larger models): Haiku shows no effect, consistent with D. The three models differ in family, size and training, so this **cannot** be attributed to scale.

### 7.5 Limitations specific to these runs

1. Three models, each from a different family; no within-family size comparison.
2. Only the first free choice was analysed; path-dependent outcomes (H4, chase streak, terminal quality, rollback latency) were not run.
3. Open models at temperature 0.7 only; at temperature 0 the 100 episodes per cell would collapse to one effective sample (prompt identical, sampling off).
4. The response prefill for the open models is a format intervention not in the registered protocol.
5. The exploratory H2 criterion, the 0.10 effect-size threshold and the "skip must rise" requirement were specified after seeing pilot output. They are labeled exploratory and should not be treated as confirmatory.
6. The sensitivity grid (p and delta +-20%, early stop on/off, hold imputation versus episode drop) in Appendix A has not been run (`--p-scale`, `--d-scale`, `--early-stop` and `analyze.py --drop-parse-fail` exist for it). Parse failure is 0% for Qwen and Haiku and 0.7% for SmolLM2.
7. The Haiku numbers were taken from the analysis output of a run whose log was kept outside this repository.

### 7.6 Summary sentence for the abstract (if the section is kept short)

> In a preliminary, partial execution of the protocol with three models, we found no support for H1: the loss frame raised test-skipping by 7.7 pp in one model (below the registered 10 pp threshold), lowered it by 5.0 pp in another, and a third model never skipped tests in any condition. Behaviour after consecutive failures differed across models and, for the EV-maximizing benchmark, runs opposite to the registered H2 because rollback dominates after a failure.
