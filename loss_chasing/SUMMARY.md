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
- Different families and sizes; three models cannot support a claim about scale. SmolLM2 parse-fail is 0.6% (mapped to hold).

## Caveats

- The H2 rule here is post hoc (exploratory). In this state machine rollback has positive EV after a failure, so a rational agent *lowers* its raw risk index; the registered raw-risk H2 cannot separate chasing from rational retreat.
- First free choice only (registered primary sample); the later turns (H4, chase streaks, terminal quality) have not been run.
- One temperature (0.7) for the open models; at temperature 0 the 100 episodes per cell collapse to one effective sample.
