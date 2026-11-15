# Phase 3 pilot: go / no-go rule (fixed before the pilot runs)

Written 2026-11-15, before any Phase 3 pilot result on the laptop GPU. The git commit adding this file is
its timestamp. One pilot only; its result decides whether the tensor-network line continues.

## Pilot

Four task instances, one training seed, learning rates from Phase 2 (TT 1e-3, LoRA 3e-3), adapters on
q, v, up and down projections, configs LoRA r=1 (723,968 params), TT r=7 (646,800), LoRA r=16
(11,583,488), TT r=31 (11,447,184):

```bash
python phase3.py --task facts --n-facts 500 && python phase3.py --task facts --n-facts 2000 && python phase3.py --task facts --n-facts 8000 && python phase3.py --task math --n-math 5000
python analyze_pilot.py
```

## Rule (relative gain on the evaluation set, as printed by analyze_pilot.py)

**Continue to a preregistered H3 study only if both hold:**

1. **The capacity dial works:** for N = 8,000 facts or for math, capacity demand (LoRA r=16 minus
   LoRA r=1) is at least +0.05, and for facts it is larger at N = 8,000 than at N = 500.
2. **TT closes the gap where capacity matters:** for N = 8,000 facts or for math, TT r=31 minus
   LoRA r=16 is at least -0.01 (TT within one point of LoRA, or ahead).

**Otherwise stop the tensor-network line** and write up Phases 1 and 2 with this pilot as supporting
evidence that TT showed no advantage even on high-capacity tasks. If rule 1 fails, the pilot could not
test the question; that is reported as such, and the line still stops (no second pilot).

The threshold of one point (0.01) is about the size of seed-to-seed differences seen in Phase 2.
Exact-match accuracy for facts is reported alongside but does not change the decision.

## Decision (2026-11-15)

Pilot output (relative gain on evaluation; fact accuracy = exact match on unseen wording):

| Instance | Demand: LoRA16 - LoRA1 | TT7 - LoRA1 | TT31 - LoRA16 | Accuracy LoRA1 / LoRA16 / TT7 / TT31 |
| --- | --- | --- | --- | --- |
| Facts N = 500 | +0.006 | -0.084 | -0.001 | 0.960 / 1.000 / 0.422 / 0.998 |
| Facts N = 2,000 | +0.002 | -0.083 | +0.001 | 0.986 / 0.997 / 0.353 / 0.997 |
| Facts N = 8,000 | +0.010 | -0.075 | +0.021 | 0.714 / 0.823 / 0.140 / 0.961 |
| Math (5,000) | -0.079 | -0.047 | -0.107 | - |

**Rule 1 fails** (demand +0.010 at N = 8,000 and -0.079 for math, both below +0.05). Rule 2 holds at
N = 8,000 (+0.021). Both were required, so **the rule says stop.**

**Observations that the rule did not anticipate (exploratory):**

- For 8,000 facts, TT r=31 beat LoRA r=16 clearly: accuracy 0.961 vs 0.823, evaluation NLL 0.041 vs 0.183.
  It is the only setting in the study where TT came out ahead.
- Relative gain saturates near 1 on the fact task (NLL falls from about 6.75 to near 0), so it hides the
  capacity demand that accuracy shows (LoRA r=1 0.714, r=16 0.823 at N = 8,000). The rule's choice of
  relative gain was a poor fit for this task.
- On math, LoRA r=16 and TT r=31 reached their best dev loss at step 125 of 1,250 and then got worse,
  which points to Phase 2 learning rates being too high for math rather than to low capacity demand.
- Single seed; every fact run was still improving at its last step; LoRA's learning rate was not tuned
  for facts; TT took about 2.8 times longer to train.

Whether to stop here or to test the knowledge-injection observation as a new, separately preregistered
hypothesis on new fact sets is the researcher's decision; either way, this pilot and its rule are
reported as written.
