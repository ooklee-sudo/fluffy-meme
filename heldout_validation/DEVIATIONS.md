# Deviations from PREREG.md (all decided after seeing outputs; reported in the manuscript)

1. **Judge verdict classification.** Judge replies were generated with a 4-token limit. SmolLM2-1.7B writes `UNSUPPORT` (the word is split over several tokens), so a literal match for `UNSUPPORTED` classified 99% of its verdicts as supported. The analysis now classifies a reply as unsupported if it starts with `UNSUP` (spaces removed). Qwen2.5-1.5B replies were complete words, so its results did not change.
2. **Judge prompt.** The prompt of the original 300-question evaluation was not preserved; the prompt in `run_heldout.py` was written for this replication. L3 numbers are not comparable with the original.
3. **Exploratory variant.** `analyze_heldout.py <judge> credit` credits verdicts slower than 2 s (the sensitivity analysis of Section 5.4). Not part of PREREG.md.
4. **Second judge.** SmolLM2-1.7B-Instruct: more than 90% of calls exceeded 2 s on this CPU and, when credited, it flagged ~99% of answers. Reported as uninformative; the self-judging limitation remains.
5. **Overlap.** The original 300-question sample (seed 0) cannot be reproduced, so overlap with the new sample cannot be excluded (about 3% expected).
