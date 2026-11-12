# Preregistration: Phase 1 confirmatory test of H1

Status: written before any confirmatory data were collected. The git commit that adds this file is its
timestamp. For a formal record, upload this file to OSF (osf.io) before the run as well.

## 1. Background: what has already been seen

An exploratory run on 10 brands from Customer Support on Twitter (results in `results/phase1/`) found:

- The TT-probe entropy was nearly constant across brands (0.921 to 0.925). An untrained adapter scores
  0.91 to 0.98, so this signal mostly reflects the adapter's random initialization. It is dropped as a
  test signal.
- The gradient-probe entropy (all training data) correlated with capacity need at Spearman rho = -0.66
  (p = 0.038; Holm-adjusted p = 0.23).
- Mean response length correlated with capacity need at rho = +0.75 (p = 0.013) and with the gradient
  entropy at rho = -0.61. Controlling for response length, the entropy correlation fell to partial
  rho = -0.46 (p = 0.21).
- Suspected mechanism: brands with longer responses contribute more tokens to the summed gradient, which
  averages out noise and lowers its entropy. The confirmatory probe therefore uses an equal token budget.

Because the direction was seen in these data, the confirmatory test is two-sided.

## 2. Hypothesis

**H1.** Holding a tenant's mean response length fixed, the entanglement entropy of the tenant's loss
gradient predicts how much adapter capacity the tenant needs. No direction is assumed.

**H0.** The partial rank correlation between gradient entropy and capacity need, controlling for mean
response length, is zero.

## 3. Data and sample

- Data: Customer Support on Twitter (`twcs.csv`), converted with `python data.py twcs data/twcs.csv
  data/twcs_pairs.jsonl 200`. A tenant is a brand account; a pair is a customer tweet and the brand's
  direct reply. The run uses a Hugging Face copy of the file; the paper will verify it against the
  Kaggle original (`thoughtvector/customer-support-on-twitter`).
- Eligible brands: at least 440 pairs, and not among the 10 exploratory brands.
- Sample: 30 brands, chosen evenly across the eligible brands' ranking by number of pairs
  (`--select spread`). The exact list is printed by the `--list-only` command in section 6 and is
  recorded in section 8 before the run.
- Per brand, with data seed 0: 320 training, 40 dev (early stopping) and 80 evaluation pairs, disjoint.

## 4. Measures

- **Capacity need (outcome):** for bond dimensions 1, 2, 4, 8 and 16, fine-tune a TT adapter on the
  q and v projections of Qwen2.5-1.5B (300 steps maximum, early stopping on dev). Gain = evaluation NLL
  without an adapter minus NLL with it, averaged over training seeds 0 and 1. Capacity need is the bond
  dimension where the mean gain first reaches 90% of the best mean gain, interpolated in log2(rank).
  The analysis uses log2(capacity need).
- **Gradient entropy (predictor):** the loss gradient with respect to each frozen q and v weight, summed
  over the first 4,000 response tokens of the training pairs. For each of the 56 matrices, the
  entanglement entropy at each of its 3 MPO bonds is divided by log of that bond's maximum rank; the
  predictor is the mean over all bonds and matrices (`grad_probe.summary.mean_norm_entropy`).
- **Covariate:** mean response length in tokens over the 320 training pairs
  (`features.mean_response_tokens`).

All other settings are the defaults of `phase1.py` at the commit that adds this file.

## 5. Analysis

- **Primary test:** partial Spearman correlation between gradient entropy and log2(capacity need),
  controlling for mean response length (rank residuals, df = n - 3), two-sided, alpha = 0.05.
- **H1 is supported** if p < 0.05. The sign and size of the partial correlation are reported either way.
- **Exclusions, fixed in advance:** a brand is left out if its best mean gain is not positive, or if its
  training pairs hold fewer than 4,000 response tokens. Left-out brands are not replaced. If fewer than 25
  brands remain, the result is reported as underpowered.
- **Secondary, not used to decide H1:** zero-order correlations of every probe signal and trait;
  the partial correlation of response length given entropy; seed reliability (Spearman correlation of
  capacity need between seeds 0 and 1); the 10 exploratory brands re-probed with the same 4,000-token
  budget.
- **Power (approximate):** with n = 30, a two-sided test at 0.05 has about 80% power for a partial
  correlation of about 0.5, and much less for correlations near 0.3.

## 6. Commands

```bash
python phase1.py --exclude-dir results/phase1 --n-tenants 30 --list-only
python phase1.py --exclude-dir results/phase1 --n-tenants 30 --seeds 0,1 --out results/phase1_confirm
python analyze.py results/phase1_confirm
```

## 7. Deviations

Any change after the run starts (settings, exclusions, analysis) will be listed here with its reason and
date, and reported in the paper.

## 8. Selected brands

From the `--list-only` command in section 6, on the converted file (1,259,128 pairs, 106 brands;
101 brands have at least 440 pairs, 91 after removing the exploratory 10):

AirAsiaSupport, AppleSupport, ArbysCares, AskAmex, AskPapaJohns, AskPlayStation, AskVirginMoney,
AskeBay, ChaseSupport, CoxHelp, Delta, DropboxSupport, HPSupport, HiltonHelp, IHGService, KFC_UKI_Help,
MTNC_Care, NeweggService, Postmates_Help, SW_Help, Safaricom_Care, SouthwestAir, TMobileHelp,
TwitterSupport, UPSHelp, VirginAtlantic, ask_progressive, asksalesforce, sizehelpteam, sprintcare

All 30 hold at least 4,000 response tokens in their 320 training pairs with the Qwen2.5 tokenizer
(minimum 5,682, Postmates_Help), so the token-budget exclusion is not expected to remove any brand.

## 9. Results (added after the run, 2026-11-12)

The run followed sections 3 to 6 with no deviations. All 30 brands were used (none failed the gain or
token-budget rules).

**Primary test.** Partial Spearman correlation of gradient entropy and log2(capacity need), controlling
for mean response length: rho = -0.334, p = 0.076, n = 30, two-sided. **H1 is not supported at
alpha = 0.05.** The approximate 95% interval (Fisher z, df adjusted for one covariate) is -0.62 to +0.04,
so a moderate negative effect is not ruled out, but an effect of the size the study was powered for
(|rho| about 0.5) is less likely.

**Secondary results (do not bear on H1):**

- Zero-order correlation of gradient entropy with capacity need: rho = -0.236 (p = 0.21).
- Response length given gradient entropy: partial rho = +0.416 (p = 0.025). Longer responses went with
  larger capacity need in both the exploratory and the confirmatory sample.
- Seed reliability of capacity need (Spearman, seed 0 vs seed 1): 0.782.
- TwitterSupport reached an evaluation NLL near 0.07, which suggests templated replies. It met the
  preregistered rules and stays in the primary test; any analysis without it is a post hoc sensitivity
  check.

**Exploratory finding, not preregistered:** gradient entropy correlated with the best gain over the
sweep (how much a brand benefits from personalization at all): rho = +0.586 (p = 0.001). Response
diversity also correlated with best gain (type-token ratio rho = -0.719, distinct-response share
rho = -0.583), so this may reflect templated versus varied replies. It is a hypothesis for a new
preregistered test on unused brands, not a result.
