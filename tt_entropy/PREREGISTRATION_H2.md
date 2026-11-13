# Preregistration: Phase 2, tensor-train vs LoRA at matched per-tenant budgets (H2)

Status: written before any Phase 2 data were collected. The learning rates are fixed by the tuning rule in
section 5 and recorded in section 8 in a separate commit before the main run starts. Both commits are the
timestamps. For a formal record, upload this file to OSF (osf.io) before the main run as well.

## 1. Background

Phase 1 (`PREREGISTRATION.md`, `PREREGISTRATION_H1prime.md`, `EXPLORATORY_RESULTS.md`) found that gradient
entanglement entropy predicts the value of personalization beyond four brand traits (H1', supported), but
that the effect is mostly ordinary SVD entropy and adds no practical decision value over response
diversity. Phase 2 asks whether the tensor-network structure pays off in the adapter itself: per-tenant
storage, which grows with the number of tenants. No TT-vs-LoRA comparison has been run on these data.

## 2. Hypothesis

**H2.** At a matched per-tenant parameter budget of about 130,000 trainable parameters, a tensor-train
adapter (bond dimension 5) and LoRA (rank 1) differ in relative gain. No direction is assumed.

**H0.** The median per-brand difference in relative gain between TT r=5 and LoRA r=1 is zero.

## 3. Data and sample

- Data: the converted Customer Support on Twitter file of the earlier preregistrations.
- Test sample: all 31 brands with at least 440 pairs that were not used in Phase 1:
  AdobeCare, AirbnbHelp, AlaskaAir, AmericanAir, AskLyft, AskSeagate, AskTarget, AskTigogh, AsurionCares,
  BofA_Help, BoostCare, British_Airways, CenturyLinkHelp, ChipotleTweets, DellCares, DoorDash_Help, JetBlue,
  Kimpton, LondonMidland, MicrosoftHelps, NortonSupport, O2, PandoraSupport, PearsonSupport, SpotifyCares,
  USCellularCares, VirginAmerica, Walmart, XboxSupport, nationalrailenq, sainsburys.
- Tuning sample (learning rates only): the 10 Phase 1 exploratory brands (`results/phase1`).
- Per brand, data seed 0: 320 training, 40 dev, 80 evaluation pairs, disjoint.

## 4. Methods and measures

Base model Qwen2.5-1.5B (bf16), adapters on every q and v projection (28 layers), 300 steps maximum, batch 4,
max length 256, AdamW with warmup and cosine decay, early stopping on dev every 50 steps (step 0 included),
training seeds 0 and 1. Code: `adapters.py`, `phase2.py` at the commit that adds this file.

| Config | Trainable params per tenant | Role |
| --- | --- | --- |
| TT r=1, r=2 | 7,952; 24,640 | below LoRA's smallest size |
| VeRA r=256, r=1024 | 64,512; 107,520 | sub-LoRA baseline |
| **TT r=5 vs LoRA r=1** | **127,120 vs 136,192** | **primary budget B1** |
| TT r=10 vs LoRA r=4 | 472,640 vs 544,768 | B2 |
| TT r=15 vs LoRA r=8 | 1,036,560 vs 1,089,536 | B3 |

TT always has fewer parameters than its LoRA partner. TT and LoRA both scale the update by 1/sqrt(r).

- **Relative gain (outcome):** (evaluation NLL without adapter - NLL with adapter) / NLL without adapter,
  averaged over the two training seeds.
- **Cost measures:** trainable parameters and fp16 bytes per tenant, training seconds per run, and
  unmerged forward latency (`bench.py`, batch 1 and 8, length 256) on the same laptop GPU.

## 5. Learning-rate tuning rule

For each method, one learning rate is chosen on the tuning sample with mid-size configs (TT r=10, LoRA r=4,
VeRA r=1024) and seed 0, from these grids: TT and LoRA {3e-4, 1e-3, 3e-3}; VeRA {1e-3, 3e-3, 1e-2, 3e-2}.
The choice is the lr with the highest mean dev relative gain (`python analyze_tune.py`). If the choice is at
the edge of its grid, the grid is extended by one step (a factor of about 3) in that direction for that
method and tuning is repeated, at most twice. The chosen lrs are recorded in section 8 and committed before
the main run. The test sample is not used for tuning.

## 6. Analysis

- **Primary test:** Wilcoxon signed-rank test on the 31 per-brand differences in relative gain,
  TT r=5 minus LoRA r=1, two-sided, alpha = 0.05 (`python analyze_h2.py results/phase2_s0 results/phase2_s1`).
  Reported with the median difference, the Hodges-Lehmann estimate and a bootstrap 95% interval.
- **H2 is supported** if p < 0.05. The direction and size are reported either way.
- **Exclusions:** none, except a brand whose run fails for a technical reason; such a brand is reported
  and not replaced. If seed 1 cannot be completed, the seed-0 result is reported as a deviation.
- **Secondary, not used to decide H2:** the same test at B2 and B3 (Holm-adjusted over the two); TT r=2 and
  TT r=1 against VeRA r=256 and r=1024; mean relative gain per config against parameters; the share of runs
  whose best checkpoint is the last step (a sign of undertraining); cost measures.
- **Power (approximate):** with 31 pairs, about 80% power for a standardized paired difference of 0.5.

## 7. Deviations

Any change after the main run starts will be listed here with its reason and date.

## 8. Chosen learning rates

To be filled in from `analyze_tune.py` before the main run.
