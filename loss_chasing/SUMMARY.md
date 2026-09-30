# Results so far (first free choice only)

Preliminary runs of the registered protocol. Temperature 0.7, 100 seeded episodes per cell unless marked. Not a substitute for the full grid (3+ developer families, both temperatures).

## Reproducible from `data/` (`python summarize.py data/*.jsonl`)

| Model | N (first choices) | Complete? | Parse-fail | Skip: gain / loss / neutral | Loss-gain diff (Holm p) | H1 | Skip 0 -> 3 fails | Excess risk 0 -> 3 fails | H2 (exploratory) |
|---|---|---|---|---|---|---|---|---|---|
| hf:HuggingFaceTB/SmolLM2-1.7B-Instruct | 742 | NO (42-100/cell, 8 cells) | 0.4% | 12.0% / 7.0% / 8.5% | -5.0pp (0.0356) | not supported | 2.7% -> 11.0% | -0.473 -> -0.022 | supported (exploratory) |
| hf:Qwen/Qwen2.5-1.5B-Instruct | 900 | yes | 0.0% | 13.0% / 20.7% / 16.7% | +7.7pp (0.0121) | not supported | 23.0% -> 13.0% | +0.035 -> +0.368 | not supported |

H1 needs Holm p<.05 and loss-gain skip diff >= +10pp (registered rule). H2 is a post hoc (exploratory) criterion: excess risk over the EV-maximizing policy rises >= 0.10 (Welch p<.05) AND skip rate rises after 3 failures. Rows marked 'Complete? NO' have unbalanced cells; do not compare them with complete rows.

## Claude Haiku 4.5 (from `analyze.py` output; the log is not in this repo)

`anthropic:claude-haiku-4-5-20251001`, temperatures 0.7 and 0.0, 100 episodes per cell, 18 cells, 1,800 first choices, parse-fail 0%.
Skip rate was 0.0% in every frame and every failure level. H1 is **not testable** (floor effect): with no skips there is nothing to compare across frames.
EV gap: loss 0.000, neutral -0.003, gain -0.527. Excess risk over the EV-maximizing policy: -0.066 after 0 failures, +0.000 after 3. The automatic H2 flag at that time
said "supported" only because every 3-failure value is identical (zero variance); it is not evidence of loss chasing.
To fold this row into the table, run `python summarize.py data/*.jsonl <haiku log>` with the log.

## Caveats

- The SmolLM2 log is **incomplete** (742 of 900): the neutral frame is missing the 3-failure cell and part of the 1-failure cell. Its H2 flag compares unbalanced cells.
- SmolLM2 and Qwen point in opposite directions on H1 (loss frame -5pp vs +7.7pp, neither reaches the +10pp rule), so there is no consistent frame effect.
- The H2 rule here is post hoc (exploratory). In this state machine rollback has positive EV after a failure, so a rational agent *lowers* its raw risk index; the registered raw-risk H2 therefore cannot separate chasing from rational retreat.
- Three models of different families and sizes cannot support a claim about scale.
