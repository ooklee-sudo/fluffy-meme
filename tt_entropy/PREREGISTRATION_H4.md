# Preregistration: knowledge injection, tensor-train vs LoRA (H4)

Status: written before any H4 data were collected. The learning rates are fixed by the tuning rule in
section 5 and recorded in section 8 in a later commit, before the main run. Both commits are timestamps.
For a formal record, upload this file to OSF (osf.io) before the main run as well.

## 1. Background, and a stated override

- Phases 1 and 2 (`PREREGISTRATION*.md`) found no practical benefit of tensor-network methods for
  brand-style personalization; LoRA r=1 and VeRA already saturate that task, and TT lost at every budget.
- The Phase 3 pilot (`PILOT_DECISION.md`) had a go/no-go rule fixed in advance. **The rule said stop**,
  because capacity demand measured by relative gain stayed below its threshold. The researcher decided to
  continue anyway, for a reason stated here: relative gain saturates near 1 on fact injection, while
  exact-match accuracy showed both a capacity demand and a large TT advantage at 8,000 facts (TT r=31 0.961
  vs LoRA r=16 0.823; single fact set, single seed, untuned learning rates). This override is reported in
  the paper. The pilot's fact set (task seed 0) is not used again.

## 2. Hypothesis

**H4.** When 8,000 new facts are injected through adapters on the q, v, up and down projections of
Qwen2.5-1.5B, a TT adapter with bond dimension 31 (11,447,184 parameters) and LoRA rank 16 (11,583,488)
reach different exact-match accuracy on questions worded differently from training. No direction is
assumed.

**H0.** The mean per-fact-set accuracy difference (TT r=31 minus LoRA r=16) is zero.

## 3. Tasks

- Fact sets from `data_tasks.py` (`facts_task(8000, seed)`): 8,000 fictional people, one fictional
  attribute each (department, home town or instrument; 120 values per relation). Training uses question
  templates 0 and 1; dev uses template 2 on 200 facts; evaluation uses template 3 on 1,000 facts.
- Tuning: task seed 100. Test: task seeds 1, 2, 3, 4, 5, 6 (six independent fact sets).

## 4. Methods and measures

Base model Qwen2.5-1.5B (bf16, gradient checkpointing), adapters on q, v, up and down projections
(112 modules), batch 32, max length 64, AdamW with warmup and cosine decay, early stopping on dev loss
every 10% of training (step 0 included), training seed 0. Code: `adapters.py`, `phase3.py` at the commit
that adds this file.

- Configs: **TT r=31** and **LoRA r=16** (primary); LoRA r=32 (23,166,976 parameters, about twice TT's;
  secondary, at LoRA's tuned learning rate).
- Steps: 6,000 per run (12 epochs over the 16,000 training examples) on test sets; 2,000 on the tuning set.
- **Outcome:** exact-match accuracy on the evaluation set (every answer token is the model's top
  prediction under teacher forcing).
- Also recorded: evaluation NLL, dev accuracy, best step, training time, and the effective rank
  (exp of the entropy of normalized squared singular values) of each learned update.

## 5. Learning-rate tuning rule

On the tuning set (task seed 100, 2,000 steps), grids: LoRA {1e-3, 3e-3, 1e-2}; TT {3e-4, 1e-3, 3e-3}.
For each method, the lr with the highest dev exact-match accuracy is chosen (`python analyze_h4.py tune
results/h4_tune`). If a choice is at the edge of its grid, the grid is extended by one step (a factor of
about 3) in that direction for that method and tuning is repeated, at most twice. Chosen lrs are recorded
in section 8 and committed before the main run. Test sets are not used for tuning.

## 6. Analysis

- **Primary test:** paired t-test, two-sided, alpha = 0.05, on the six per-fact-set differences in
  evaluation accuracy, TT r=31 minus LoRA r=16 (`python analyze_h4.py test results/h4`). Reported with the
  mean difference and its 95% confidence interval.
- **H4 is supported** if p < 0.05. Direction and size are reported either way.
- **Exclusions:** none, except a fact set whose run fails for a technical reason; it is reported and not
  replaced.
- **Secondary, not used to decide H4:** Wilcoxon signed-rank on the same differences; evaluation NLL
  difference; TT r=31 vs LoRA r=32 accuracy (does LoRA need about twice the parameters to match TT?);
  training time; effective rank of the learned updates by module type.
- **Power:** the pilot difference was 0.14 in accuracy on one fact set. With six sets, a paired t-test has
  high power for a difference of that size if the between-set standard deviation is below about 0.05, and
  little power for differences of a few points.

## 7. Deviations

Any change after the main run starts will be listed here with its reason and date.

## 8. Chosen learning rates

To be filled in from `analyze_h4.py tune` before the main run.
