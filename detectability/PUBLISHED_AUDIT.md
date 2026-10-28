# Audit of published exposure and adoption studies against the detectability bound

Inputs: `examples/published_estimates.csv` (each row has its source: table, figure or text, and page). Code: `audit_published.py`. Output: `results/published_audit.csv`.
Nine studies were read from their working-paper or published PDFs (open copies only). This is a small, non-systematic selection, not a literature census. Three further candidates could not be audited because the full text was not obtainable without bypassing an access barrier: Demirci, Hannane & Zhu (2025), Kim, Jin & Lee (2026) and Zhou & Lee (2024).

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
| Albanesi et al. 2025, 16 European countries, employment share, AI (Webb); relative units derived | +0.075 (0.025) | 0.071 | 3.7 | 0.93 | no |
| same, AI (Felten et al.) | +0.191 (0.048) | 0.136 | 7.1 | 1.8 | no |
| Georgieff & Hyee 2022, 23 OECD countries, employment growth, high-computer-use occupations | +0.057 (0.025) | 0.069 | 3.6 | 0.90 | no |

## Adoption-observed designs
| Study (outcome) | Estimate (SE) | MDE | MDE below 0.19? |
|---|---|---|---|
| Hampole et al. 2025, occupation-firm employment growth per SD, OLS | -0.057 (0.006) | 0.016 | yes |
| same, IV | -0.104 (0.010) | 0.027 | yes |
| Humlum & Vestergaard 2025, adopters' earnings (SE derived from the stated bound) | 0 (0.005) | 0.014 | yes |
| same, occupation level (derived) | 0 (0.031) | 0.086 | yes |
| same, workplace wage bill per full adoption (derived) | 0 (0.026) | 0.071 | yes |
| Hosseini & Lichtinger 2026, junior employment at adopters (figure-read) | -0.062 (0.020) | 0.056 | yes |
| Hui, Reshef & Zhou 2024, platform DiD, monthly jobs | -0.020 (0.004) | 0.011 | yes |
| same, monthly income | -0.052 (0.016) | 0.045 | yes |

## What the audit shows
1. **Occupation- or industry-level exposure gradients on aggregate employment cannot detect platform-sized assimilation.** Acemoglu et al. (2022), Albanesi et al. (2025) for 16 European countries, and Georgieff and Hyee (2022) for 23 OECD countries have minimum detectable effects of about 6 to 14 log points per SD of exposure,
   which requires a per-assimilator effect of 0.7 to 1.8 log points even at 40 percent adoption. This is the class that the manuscript's European and Canadian estimates belong to, and Acemoglu et al. reach the same conclusion that aggregate effects "are too small to detect".
2. **Designs with microdata or observed adoption are much more precise.** Worker-level registers (Gathmann et al.), firm-by-occupation panels with observed AI use (Hampole et al.), and adoption-observed designs (Humlum and Vestergaard; Hosseini and Lichtinger) have MDEs of 0.5 to 8.6 percent, well below the platform effect.
   The manuscript's methodological claim (Section 10.1) is therefore limited to the first class, and the bound is a way of telling the two classes apart.
3. **Adoption-observed designs rule out platform-sized effects.** Humlum and Vestergaard find precise zeros for adopters' earnings (bounds of about 1 percent) and average time savings of about 3 percent. This is consistent with the manuscript's theory that acquisition, and even use, does not imply reassignment of tasks,
   and it is the closest existing evidence to the firm-level design of Section 9 (adoption, employer policies, task-level survey, administrative outcomes). It is not open data.
4. **Platform effect sizes differ by an order of magnitude.** Hui et al. (2024) estimate 2 percent fewer jobs and 5.2 percent lower earnings for affected freelancers, against the 17 percent fall in posts of Demirci et al. (2025). The manuscript's reference value (-0.19) is therefore on the high side and favours detection; a smaller reference value strengthens the conclusion that occupation-level designs cannot detect assimilation.
5. **Large observed effects are not explained by platform-sized assimilation.** Brynjolfsson et al.'s per-SD estimate for ages 22-25 (-0.064) is about four times the coefficient that complete assimilation at A = 0.40 and beta = -0.19 would produce (-0.014). It is detectable (z about 5), and the authors present it as descriptive.

## Caveats (read before using any number)
* **Extraction.** Values were read by the assistant from PDFs: tables as printed, minus signs checked against the text. Two rows are read from figures (Gathmann et al. Figure 7; Hosseini and Lichtinger Figure 6), three Humlum and Vestergaard rows derive SE from stated confidence bounds (SE = bound / 1.96), and three rows are converted to relative units (Albanesi et al. by dividing by an assumed mean cell share of 0.236 percentage points; Georgieff and Hyee by the authors' own SD of 0.067). Verify each against the paper before citing.
* **Versions.** Brynjolfsson et al. is the August 2026 version (downloaded from a URL labelled Nov25); Hosseini and Lichtinger is the May 2026 version; results change between versions. Hampole et al. is NBER WP 33509 (rev. September 2025); Gathmann et al. is IZA DP 17554; Humlum and Vestergaard is BFI WP 2025-56-3 (May 2025); Albanesi et al. is ECB WP 2831; Georgieff and Hyee is the Frontiers in AI version; Hui et al. is CESifo WP 10601 (August 2023).
* **Not comparable by construction.** Outcomes (employment, earnings, hours, growth rates), horizons (5 to 8 years) and exposure measures differ. The per-SD conversion for quintile contrasts assumes a normal exposure distribution (top minus bottom quintile = 2.8 SD).
* **Scenario parameters.** A is a scenario (0.10, 0.40), not an estimated assimilation share; sigma_s = 0.19 assumes the most exposed occupation does only exposed work and is the most favourable case for detection. With sigma_s = 0.10 every beta_min doubles (see the CSV).
* **Not independently verified.** The audit has not been checked by the studies' authors.
