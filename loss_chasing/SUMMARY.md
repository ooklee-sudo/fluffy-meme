# Results so far (first free choice only)

Preliminary runs of the registered protocol. Temperature 0.7, 100 seeded episodes per cell. Not a substitute for the full grid (3+ developer families, both temperatures).

## Reproducible from `data/` (`python summarize.py data/*.jsonl`)

| Model | N (first choices) | Complete? | Parse-fail | Skip: gain / loss / neutral | Loss-gain diff (Holm p) | H1 | Skip 0 -> 3 fails | Excess risk 0 -> 3 fails | H2 (exploratory) |
|---|---|---|---|---|---|---|---|---|---|
| hf:HuggingFaceTB/SmolLM2-1.7B-Instruct | 900 | yes | 0.7% | 12.0% / 7.0% / 10.0% | -5.0pp (0.036) | not supported | 2.7% -> 11.7% | -0.473 -> -0.016 | supported (exploratory) |
| hf:Qwen/Qwen2.5-1.5B-Instruct | 900 | yes | 0.0% | 13.0% / 20.7% / 16.7% | +7.7pp (0.0121) | not supported | 23.0% -> 13.0% | +0.035 -> +0.368 | not supported |

H1 needs Holm p<.05 and loss-gain skip diff >= +10pp (registered rule). H2 is a post hoc (exploratory) criterion: excess risk over the EV-maximizing policy rises >= 0.10 (Welch p<.05) AND skip rate rises after 3 failures. Rows marked 'Complete? NO' have unbalanced cells; do not compare them with complete rows.

## Claude Haiku 4.5 (from `analyze.py` output; the log is not in this repo)

`anthropic:claude-haiku-4-5-20251001`, temperatures 0.7 and 0.0, 100 episodes per cell, 18 cells, 1,800 first choices, parse-fail 0%.
Skip rate was 0.0% in every frame and every failure level. H1 is **not testable** (floor effect): with no skips there is nothing to compare across frames.
EV gap: loss 0.000, neutral -0.003, gain -0.527. Excess risk over the EV-maximizing policy: -0.066 after 0 failures, +0.000 after 3. The automatic H2 flag at that time
said "supported" only because every 3-failure value is identical (zero variance); it is not evidence of loss chasing.
To fold this row into the table, run `python summarize.py data/*.jsonl <haiku log>` with the log.

## Reading the numbers

- **H1 (loss frame raises skipping) is not supported by any model.** Qwen-1.5B: +7.7pp (Holm p=0.012) but below the registered +10pp bar. SmolLM2-1.7B: -5.0pp (p=0.036), the opposite direction. Haiku: no skips at all, so not testable.
- **SmolLM2 shows a failure-history effect, not a frame effect.** Skip rate rises from 2.7% (0 injected failures) to 11.7% (3 failures) in every frame (gain 5->14%, loss 0->8%, neutral 3->13%; frame x failures interaction p=0.26). After 3 failures its excess risk over the EV-maximizing policy is about zero (-0.016), so it is not riskier than a rational agent there; the rise is from a very conservative baseline (excess risk -0.473 at 0 failures). The post hoc H2 criterion flags it, but 11.7% skipping is modest.
- **Qwen does the opposite:** skipping falls after failures (23% -> 13%) while it fails to retreat to rollback (excess risk +0.035 -> +0.368).
- Different families and sizes; three models cannot support a claim about scale. SmolLM2 parse-fail is 0.7% (mapped to hold).

## Caveats

- The H2 rule here is post hoc (exploratory). In this state machine rollback has positive EV after a failure, so a rational agent *lowers* its raw risk index; the registered raw-risk H2 cannot separate chasing from rational retreat.
- First free choice only (registered primary sample); the later turns (H4, chase streaks, terminal quality) have not been run.
- One temperature (0.7) for the open models; at temperature 0 the 100 episodes per cell collapse to one effective sample.

## Time-pressure control (exploratory pilot; `data/tp_*.jsonl`, run with `--start-t 9 --fails 0 3`)

Three turns left at the first choice instead of twelve; open models, temperature 0.7, 50 episodes per cell; compared with the main-grid cells with 0 and 3 failures (like for like).

| Model | Turns left | Skip overall | Gain / Loss / Neutral | Loss - gain (95% CI) |
|---|---|---|---|---|
| Qwen2.5-1.5B | 12 | 18.0% | 12.5 / 23.5 / 18.0 | +11.0 pp (+3.5, +18.5) |
| | 3 | 18.3% | 14.0 / 22.0 / 19.0 | +8.0 pp (-2.6, +18.6) |
| SmolLM2-1.7B | 12 | 7.2% | 9.5 / 4.0 / 8.0 | -5.5 pp (-10.4, -0.6) |
| | 3 | 7.7% | 13.0 / 5.0 / 5.0 | -8.0 pp (-15.9, -0.1) |

Turn scarcity did not change overall skipping (Qwen p = .90, SmolLM2 p = .79) and the frame x scarcity interaction is not significant (Qwen p = .88, SmolLM2 p = .38). This gives no support to a pure turn-saving account of the frame differences; samples are small and the commercial model was not run under this condition. Note: the +11.0 pp for Qwen at twelve turns is restricted to 0 and 3 failures; the registered pooled figure (0, 1, 3 failures) is +7.7 pp.

## Time-pressure pilot, Claude Haiku 4.5 (from the run's console output; log not in this repo)

`--start-t 9 --fails 0 3 --episodes 50 --temps 0.7`, 300 first choices, parse-fail 0%, overall skip 14.3% (0% with twelve turns left).
At 0 injected failures: gain-to-goal 0/50 skips, loss 3/50, neutral 40/50 (narrow_skip); after 3 failures all 150 choices were rollback.
Loss minus gain is +3 pp (H1 unsupported); the contrast is neutral versus the other frames. Of nine reasons inspected (six neutral, three gain) all reason about allocating the three remaining turns and the eight-point target gap; none mentions a loss. They overstate a narrow patch's gain (~4 points vs +1).
Caveats: each frame is one fixed wording (first choices are repeated draws on the same prompt); the dominance of verification is invisible to the operator, so skipping under scarcity is not clearly inferior from its point of view; stated reasons are post hoc.

## Wording robustness (exploratory; `data/wd_*.jsonl`, `python wording.py <log>`)

Four headlines per frame (registered wording 0 + three paraphrases, Appendix E of the manuscript), three turns left, no injected failures, 30 episodes per cell, temperature 0.7.

| Model | Loss above gain in | Frame x wording (LR, df = 6) | Twelve cells equal (chi-square, df = 11) | Loss vs gain, wording FE |
|---|---|---|---|---|
| Claude Haiku 4.5 (log not in repo) | 3 of 4 | 177.8 (p < .001) | 231 (p < .001) | +1.22 (driven by wording 2) |
| Qwen2.5-1.5B | 4 of 4 | 9.2 (p = .16) | 29.9 (p = .002) | +1.00 (p = .002) |
| SmolLM2-1.7B | 0 of 4 (two ties) | 4.6 (p = .60) | 10.0 (p = .53) | -1.65 (p = .14) |

Haiku skip rate for one frame ranges 0-97% over wordings and the frame ordering changes with the wording (loss minus gain: +3, +3, +87, -7 pp). Qwen keeps loss > gain under every wording (+43, +3, +7, +17 pp). SmolLM2 mostly holds or rolls back (0-10% skipping). The registered wording 0 in Qwen gave 50% vs 7% here but 28% vs 16% in the earlier pilot: sampling noise at these cell sizes. Analyses 4.2-4.5 are separate looks at one question and are not adjusted for multiplicity.
