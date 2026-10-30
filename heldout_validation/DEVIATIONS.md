# Deviations from PREREG.md (all decided after seeing outputs; reported in the manuscript)

1. **Judge verdict classification.** Judge replies were generated with a 4-token limit. SmolLM2-1.7B writes `UNSUPPORT` (the word is split over several tokens), so a literal match for `UNSUPPORTED` classified 99% of its verdicts as supported. The analysis now classifies a reply as unsupported if it starts with `UNSUP` (spaces removed). Qwen2.5-1.5B replies were complete words, so its results did not change.
2. **Judge prompt.** The prompt of the original 300-question evaluation was not preserved; the prompt in `run_heldout.py` was written for this replication. L3 numbers are not comparable with the original.
3. **Exploratory variant.** `analyze_heldout.py <judge> credit` credits verdicts slower than 2 s (the sensitivity analysis of Section 5.4). Not part of PREREG.md.
4. **Second judge.** SmolLM2-1.7B-Instruct: more than 90% of calls exceeded 2 s on this CPU and, when credited, it flagged ~99% of answers. Reported as uninformative; the self-judging limitation remains.
5. **Overlap.** The original 300-question sample (seed 0) cannot be reproduced, so overlap with the new sample cannot be excluded (about 3% expected).
6. **Verdict parsing (second fix).** Some models put newlines or markdown before the verdict (Gemma). A reply is now classified by its first `SUPPORT`/`UNSUPPORT` token; this replaces the prefix rule of item 1. The Qwen2.5-1.5B results did not change.
7. **Large external judges.** After seeing the local-judge results we added Llama-3.3-70B-Instruct and Gemma-3-27B-Instruct through OpenRouter (`judge_api.py`, same prompt, temperature 0, no timeout because network latency is not comparable with the CPU timings). Not part of PREREG.md.
8. **Cost comparison.** `cost_heldout.py` (paired daily-cost effect of adding the routed judge, harm in {0, 100, 1000} USD) was written after the judge results were known.
