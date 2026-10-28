# Audit of published exposure and adoption studies against the detectability bound

Inputs: `examples/published_estimates.csv` (each row has its source: table, figure or text, and page). Code: `audit_published.py`. Output: `results/published_audit.csv`.
Six studies were read from their working-paper or published PDFs. This is a small, non-systematic selection, not a literature census.

**Metric.** For exposure-gradient designs, `MDE = 2.8 SE` per SD of exposure. The smallest effect per assimilating employer that complete assimilation could produce and the design could detect is
`|beta_min| = MDE / (A * sigma_s)` (R = 1; A = share of assimilating employers; sigma_s = SD of the true task share). We set sigma_s = 0.19 (the manuscript's favourable case, k = 5.3) and compare with the
platform effect |beta| = 0.19. For adoption-observed designs the coefficient is already an effect of adoption or of firm-level AI use, so we report the MDE and compare it with 0.19.

## Exposure-gradient designs
| Study (outcome) | Estimate per SD (SE) | MDE | beta_min, A = 0.10 | beta_min, A = 0.40 | Detects platform-sized assimilation at A = 0.40? |
|---|---|---|---|---|---|
| Acemoglu et al. 2022, occupation employment 2010-18 (Felten) | +0.041 (0.028) | 0.078 | 4.1 | 1.0 | no |
| same (Webb) | -0.014 (0.023) | 0.065 | 3.4 | 0.86 | no |
| same (SML) | -0.030 (0.020) | 0.056 | 2.9 | 0.74 | no |
| same, industry-by-CZ employment 2010-16 (Felten) | -0.003 (0.005) | 0.013 | 0.71 | 0.18 | borderline (yes) |
| Brynjolfsson et al. 2026, ages 22-25, ADP, quintile 5 vs 1 | -0.064 (0.013) | 0.036 | 1.9 | 0.47 | no |
| same, ages 26-30 | -0.017 (0.012) | 0.033 | 1.7 | 0.43 | no |
| Gathmann et al. 2024, worker-level log days employed (figure-read) | -0.0045 (0.0018) | 0.005 | 0.27 | 0.07 | yes |

## Adoption-observed designs
| Study (outcome) | Estimate (SE) | MDE | MDE below 0.19? |
|---|---|---|---|
| Hampole et al. 2025, occupation-firm employment growth per SD, OLS | -0.057 (0.006) | 0.016 | yes |
| same, IV | -0.104 (0.010) | 0.027 | yes |
| Humlum & Vestergaard 2025, adopters' earnings (SE derived from the stated bound) | 0 (0.005) | 0.014 | yes |
| same, occupation level (derived) | 0 (0.031) | 0.086 | yes |
| same, workplace wage bill per full adoption (derived) | 0 (0.026) | 0.071 | yes |
| Hosseini & Lichtinger 2026, junior employment at adopters (figure-read) | -0.062 (0.020) | 0.056 | yes |

## What the audit shows
1. **The manuscript's claim holds for the design it is about.** Occupation-level exposure gradients on aggregate employment, as in Acemoglu et al. (2022), cannot detect platform-sized assimilation unless adoption is very high and exposure is almost a pure measure of the task share.
   This matches their own conclusion that aggregate effects "are too small to detect".
2. **It does not hold for all exposure designs.** Designs with microdata (worker-level German registers, Gathmann et al.) or firm-by-occupation panels with observed AI use (Hampole et al.) have MDEs of 0.5 to 3 percent and could detect effects far smaller than the platform estimate.
   The statement in Section 10.1 that exposure-based hiring designs "cannot detect plausible assimilation effects" should therefore be limited to occupation- or industry-level outcomes with a small number of units, or be rephrased as a rule to check with the bound.
3. **Adoption-observed designs rule out platform-sized effects.** Humlum and Vestergaard find precise zeros for adopters' earnings (bounds of about 1 percent), far below the 17 percent platform effect, and report average time savings of about 3 percent. This is consistent with the manuscript's theory that acquisition
   (and even use) does not imply reassignment of tasks, and it is the closest existing evidence to the firm-level design of Section 9 (adoption, employer policies, task-level survey, administrative outcomes). It is not open data.
4. **Large observed effects are not explained by platform-sized assimilation.** Brynjolfsson et al.'s per-SD estimate for ages 22-25 (-0.064) is about four times the coefficient that complete assimilation at A = 0.40 and beta = -0.19 would produce (-0.014); it is detectable (z about 5) but exceeds what the manuscript's rule (iii) treats as plausible
   only if sigma_s is as large as 0.19. Under a smaller sigma_s the gap widens. Either entry-level effects are much larger than platform effects, or confounders (interest rates, other shocks, composition) matter; the authors present the results as descriptive.

## Caveats (read before using any number)
* **Extraction.** Values were read by the assistant from PDFs: tables as printed, minus signs checked against the text. Two rows are read from figures (Gathmann et al. Figure 7; Hosseini and Lichtinger Figure 6) and three Humlum and Vestergaard rows derive SE from stated confidence bounds (SE = bound / 1.96). Verify each against the paper before citing.
* **Versions.** Brynjolfsson et al. is the August 2026 version (downloaded from a URL labelled Nov25); Hosseini and Lichtinger is the May 2026 version; results change between versions. Hampole et al. is NBER WP 33509 (rev. September 2025); Gathmann et al. is IZA DP 17554; Humlum and Vestergaard is BFI WP 2025-56-3.
* **Not comparable by construction.** Outcomes (employment, earnings, hours, growth rates), horizons (5 to 8 years) and exposure measures differ. The per-SD conversion for quintile contrasts assumes a normal exposure distribution (top minus bottom quintile = 2.8 SD).
* **Scenario parameters.** A is a scenario (0.10, 0.40), not an estimated assimilation share; sigma_s = 0.19 assumes the most exposed occupation does only exposed work and is the most favourable case for detection. With sigma_s = 0.10 every beta_min doubles (see the CSV).
* **Not independently verified.** The audit has not been checked by the studies' authors.
