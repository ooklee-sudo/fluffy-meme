# Preregistration: confirmatory test of H1' (gradient entropy and the value of personalization)

Status: written before any H1' confirmatory data were collected. The git commit that adds this file is its
timestamp. For a formal record, upload this file to OSF (osf.io) before the run as well.

## 1. Background: what has already been seen

- The preregistered H1 test (`PREREGISTRATION.md`, 30 brands) did not support H1: gradient entropy did not
  predict capacity need beyond response length (partial rho = -0.334, p = 0.076).
- Exploring those same 30 brands afterwards (`explore.py`), gradient entropy correlated with how much a
  brand gains from personalization. With relative gain as the outcome and four controls (type-token
  ratio, distinct-response share, mean response length, NLL without adapter), partial rho = +0.528
  (p = 0.006). Without controls, rho = +0.631.
- In the earlier 10 exploratory brands, the same relation was absent (no controls +0.188; four controls
  -0.403; n = 10, single seed).
- Entropy correlated with response diversity (type-token ratio rho = -0.506), and controlling for it
  weakened the relation most (best gain: +0.586 to +0.370).

The hypothesis was found in data that now cannot test it, and one small independent sample did not show
it. This preregistration tests it on 30 brands never used before. The test is two-sided.

## 2. Hypothesis

**H1'.** Holding four simple brand traits fixed (response type-token ratio, distinct-response share, mean
response length, NLL without adapter), the entanglement entropy of a brand's loss gradient predicts the
brand's relative gain from personalization. No direction is assumed.

**H0.** The partial rank correlation between gradient entropy and relative gain, given the four traits,
is zero.

## 3. Data and sample

- Data: the same converted Customer Support on Twitter file as `PREREGISTRATION.md` (1,259,128 pairs,
  106 brands; 101 with at least 440 pairs).
- Eligible brands: at least 440 pairs, and not among the 40 brands already used (`results/phase1`,
  `results/phase1_confirm`). 61 brands are eligible.
- Sample: 30 brands chosen evenly across the eligible brands' ranking by number of pairs
  (`--select spread`), listed in section 8.
- Per brand, with data seed 0: 320 training, 40 dev and 80 evaluation pairs, disjoint.

## 4. Measures

All measures and settings are those of `PREREGISTRATION.md` section 4 and the `phase1.py` defaults at the
commit that adds this file, with training seeds 0 and 1.

- **Relative gain (outcome):** the largest seed-averaged gain over bond dimensions 1, 2, 4, 8 and 16
  (evaluation NLL without adapter minus NLL with it), divided by the evaluation NLL without adapter.
- **Gradient entropy (predictor):** `grad_probe.summary.mean_norm_entropy`, on a 4,000-response-token
  budget.
- **Controls:** `features.response_type_token_ratio` (distinct tokens among the first 5,000 response
  tokens), `features.distinct_response_share`, `features.mean_response_tokens`, and `nll_none`, all from
  the 320 training pairs except `nll_none` (evaluation pairs).

## 5. Analysis

- **Primary test:** partial Spearman correlation of gradient entropy with relative gain, controlling for
  the four traits (ranks, least-squares residuals, df = n - 6), two-sided, alpha = 0.05
  (`python analyze_value.py results/phase1_value`).
- **H1' is supported** if p < 0.05. The sign and size are reported either way.
- **Exclusions, fixed in advance:** a brand is left out if its best gain is not positive or its training
  pairs hold fewer than 4,000 response tokens. Left-out brands are not replaced. Fewer than 25 remaining
  brands: reported as underpowered.
- **Secondary, not used to decide H1':** relative gain without controls; best gain with and without
  controls; the H1 test (capacity need given response length) repeated on this sample.
- **Power (approximate):** with n = 30 and four controls, a two-sided test at 0.05 has about 70% power
  for a partial correlation of 0.5, and little power for 0.3.

## 6. Commands

```bash
python phase1.py --exclude-dir results/phase1,results/phase1_confirm --n-tenants 30 --list-only
python phase1.py --exclude-dir results/phase1,results/phase1_confirm --n-tenants 30 --seeds 0,1 --out results/phase1_value
python analyze_value.py results/phase1_value
```

## 7. Deviations

Any change after the run starts will be listed here with its reason and date.

## 8. Selected brands

ATT, AWSSupport, ArgosHelpers, AskCiti, AskRBC, Ask_Spectrum, Ask_WellsFargo, AzureSupport, GWRHelp,
GloCare, GoDaddyHelp, GooglePlayMusic, GreggsOfficial, MOO, McDonalds, Morrisons, NikeSupport, SCsupport,
Tesco, Uber_Support, VMUcare, VerizonSupport, YahooCare, airtel_care, askpanera, askvisa, comcastcares,
hulu_support, idea_cares, marksandspencer

All 30 hold at least 4,000 response tokens in their 320 training pairs with the Qwen2.5 tokenizer
(minimum 4,157, GreggsOfficial).

## 9. Results (added after the run, 2026-11-13)

The run followed sections 3 to 6 with no deviations. All 30 brands were used (none failed the gain or
token-budget rules).

**Primary test.** Partial Spearman correlation of gradient entropy with relative gain, controlling for
type-token ratio, distinct-response share, mean response length and NLL without adapter:
rho = +0.616, p = 0.0008, n = 30, two-sided. **H1' is supported at alpha = 0.05.** The approximate 95%
interval (Fisher z, four covariates) is +0.30 to +0.81. Brands whose gradient has higher entanglement
entropy gained more from personalization, relative to their loss without an adapter.

**Secondary results (do not bear on H1'):**

- Relative gain, no controls: rho = +0.655 (p < 0.001). Best gain, four controls: +0.553 (p = 0.003);
  no controls: +0.509 (p = 0.004).
- The H1 test repeated on this sample: partial rho(entropy, log2 capacity need | response length) =
  -0.046 (p = 0.81). Entropy again did not predict capacity need.

**Limits.** One dataset, one base model (Qwen2.5-1.5B), one probe setting. Entropy spans a narrow range
(0.861 to 0.891), so the practical meaning of a given difference is not yet known. Gain is measured as
response NLL, not a business outcome. The mechanism is not known. In the earlier 10 exploratory brands
the relation was absent (n = 10, single seed); that inconsistency should be reported alongside this
result.
