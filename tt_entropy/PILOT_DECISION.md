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

## Decision

To be filled in from the pilot output.
