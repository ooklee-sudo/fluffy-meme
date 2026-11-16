# Preregistration: quality of adapter vs retrieval replies (H5), selection by observable traits (H10) and
asymmetric obsolescence (H7)

Status: written before any H5, H7 or H10 data were collected. The git commit that adds this file, together
with the code it names (`gen_replies.py`, `judge.py`, `analyze_h5.py`, `drift.py`, `analyze_h7.py`) and the
brand lists (`h5_brands.txt`, `h7_brands.txt`), is its timestamp. For a formal record, upload it to OSF
(osf.io) before the runs as well.

## 1. Background and theory

The revision plan (`수정 계획: 이론 프레이밍과 논문 재구성`) frames personalization as an IT asset that trades
fixed for variable cost and becomes obsolete. These hypotheses test three of its propositions on data not used
for the corresponding exploratory analyses:

- P2 (sufficiency of minimal assets): exploratory E1 found LoRA r=1 above RAG-8 in NLL relative gain for 31 of
  31 brands. NLL may not reflect reply quality, so H5 compares generated replies with an LLM judge.
- P5 (sufficiency of observable signals): exploratory decision simulations found that ranking brands by
  response type-token ratio captures nearly the oracle's share of personalization gain (H10).
- P3 (asymmetric obsolescence): exploratory E4 (30 brands) found a stale adapter losing 0.016 relative gain per
  week against 0.003 for refreshed RAG (H7).

## 2. Hypotheses (all two-sided)

- **H5.** Replies generated with a LoRA r=1 adapter and with RAG-8 differ in the primary judge's overall
  preference. H0: the per-brand win rate of LoRA r=1 has median 0.5.
- **H10.** Personalizing the third of brands with the lowest response type-token ratio captures a different
  share of the total LoRA r=1 relative gain than a random third. H0: the captured share equals that of a random
  selection.
- **H7.** The within-brand weekly slope of relative gain differs between a stale LoRA r=1 adapter and RAG-8 with
  a weekly refreshed index. H0: the per-brand difference of slopes has median 0.

## 3. Samples

- H5 and H10: the 50 brands in `h5_brands.txt`: all TWCS brands with at least 440 pairs that were not used in
  E1 (31 brands) or E4 (30 brands).
- H7: the 35 brands in `h7_brands.txt`: all brands that meet the time-split rule of `drift.py` (enough pairs in
  weeks 0-1 and in each of weeks 2-8) and were not used in E4.
- Per brand, the split of all earlier studies (data seed 0; 320 train, 40 dev, 80 evaluation pairs).

## 4. Procedures

- **Generation (H5, H10):** `python gen_replies.py --tenants-file h5_brands.txt --out results/h5_gen`. Qwen2.5-1.5B
  (bf16); LoRA r=1 (lr 3e-3) and VeRA r=256 (lr 3e-2) on q and v projections, 300 steps with early stopping on
  dev; RAG-8 = the 8 most similar training pairs by TF-IDF. Greedy replies of up to 64 tokens to the first 40
  evaluation messages from: no personalization, RAG-8, LoRA r=1, VeRA r=256. NLL relative gains on all 80
  evaluation pairs. Five style examples per brand drawn from its training replies with a fixed seed.
- **Judging (H5):** `python judge.py results/h5_gen --out results/h5_judge.jsonl --max-cost 10`. Primary judge
  `anthropic/claude-haiku-5.5` via OpenRouter, temperature 0, low reasoning effort, the prompt in `judge.py`
  at this commit; the brand's actual reply is not shown; the two replies appear in a random order fixed by the
  seed. Pairs: LoRA r=1 vs RAG-8 (primary), VeRA r=256 vs RAG-8, LoRA r=1 vs no personalization. Second judge
  `openai/gpt-5-mini` on a fixed 20% sample of the primary pairs. Spending cap US$10.
- **Drift (H7):** `python drift.py --tenants <the 35 brands> --out results/h7_drift`, with the defaults used in
  E4 (LoRA r=1 trained on weeks 0-1, evaluated on weeks 2-8; RAG-8 with a stale and a refreshed index).

## 5. Analysis

- **H5 primary:** per brand, the win rate of LoRA r=1 over RAG-8 on the primary judge's "overall" answer (tie =
  one half); Wilcoxon signed-rank test of (win rate - 0.5) across the 50 brands, two-sided, alpha 0.05
  (`python analyze_h5.py results/h5_gen results/h5_judge.jsonl`).
- **H10 primary:** rank the 50 brands by type-token ratio of their training replies, lowest first (the direction
  of the exploratory relation); take the top 17; share of the total LoRA r=1 NLL relative gain they hold;
  two-sided permutation p-value against 20,000 random draws of 17 brands (`analyze_h5.py`).
- **H7 primary:** per brand, OLS slopes over weeks 2-8 of the stale adapter's and the fresh-index RAG's relative
  gain; Wilcoxon signed-rank test of the difference, two-sided, alpha 0.05 (`python analyze_h7.py
  results/h7_drift`).
- **Secondary, not used to decide the hypotheses:** the "voice" and "helpfulness" criteria; send-as-is and
  unsupported-claim rates by method; the two other pairs; agreement and Cohen's kappa between the two judges;
  NLL relative gains; for H7, retention, recovery R, the share of brands where the stale adapter stays ahead of
  fresh-index RAG in week 8, and the implied horizon.
- **Exclusions:** none, except a brand whose run fails for a technical reason or a judgment that cannot be
  obtained after four attempts; these are reported and not replaced. If the spending cap stops judging early,
  the primary test uses the brands with complete primary-pair judgments and the shortfall is reported.

## 6. Planned but separate

- **H6** (agreement of the LLM judge with human raters) and the estimate of lambda (value of quality) from
  human send-as-is judgments need ethics approval and are registered separately.
- **H8 and H9** (large-model serving and replication) run on cloud GPUs and are registered separately.

## 7. Deviations

Any change after the runs start will be listed here with its reason and date.
