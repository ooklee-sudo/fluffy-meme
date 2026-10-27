# Pre-registration: Do repositories in the LLM tooling ecosystem release sooner after upstream model launches? (Holdout confirmation)

**Status:** DRAFT. Fill the `[FILL]` fields, then paste into the OSF "Secondary Data Preregistration" template.
**Registered by:** [FILL names] **Registration date:** [FILL; the date of OSF submission] **Analysis code SHA-256:** see `SHA256SUMS`

## 1. Background and what has already been seen

A prior study (manuscript ISRE-2026-4563, under revision) analyzed 19 open-source repositories in the LLM tooling ecosystem and 38 upstream model launches announced between July 2023 and July 2026, with data collected through the week of 5 October 2026. In that data, repositories exposed to a launch released 3.4 days sooner than unexposed repositories (placebo-based p = 0.018).

**Disclosure.** The primary statistic of the prior study was designated *after* its estimates had been seen, and the effect depended on how hot-fix releases and controls exposed to other launches were handled. The prior analysis is therefore treated as exploratory. All 38 of those launches, and any launch announced before the registration date, **are not used for confirmation** (they have been seen). The confirmatory test uses only launches announced **after** the registration date.

## 2. Hypothesis

**H-conf.** For an upstream model launch, repositories exposed to that launch release their next release sooner than repositories not exposed to it. The direction is the one found in the prior study. The test is two-sided (section 3.4); a result in the opposite direction does not confirm.

## 3. Design and analysis

### 3.1 Repositories (fixed)
The same 19 repositories as in the prior study (list in `exposure_coding_template.csv`). No repository is added or removed. A repository whose GitHub repository is archived or deleted during the window is dropped from the launches after that date and the drop is reported.

### 3.2 Launches (frozen before analysis)
Launches are logged as they happen, following `launch_inclusion_criteria.md`, in `launches_log.csv`. The set of launches is frozen at the end of the collection window, **before any release data for the window is downloaded**. No launch is added or removed after freezing.

### 3.3 Exposure (frozen before analysis)
Exposure of each repository to each of four launch types (open_weights, openai, anthropic, google) is coded by two coders working independently, following `exposure_codebook.md`. Cohen's kappa is reported; disagreements are settled by a third person. The consensus table is frozen **before any release data for the window is downloaded**. The same procedure is applied to the 38 prior launches' coding as a sensitivity check.

### 3.4 Primary statistic and inference
Computed by `confirmatory_analysis.py`, unmodified.

- **Unit:** launch × repository, where the repository released at least once in the 90 days before the announcement.
- **Outcome:** days from the announcement date to the next release (non-draft, non-prerelease; hot-fixes included), truncated at 28 days; a release on the announcement day counts as 0; a repository with no release within 28 days counts as 28.
- **Statistic:** per launch, mean(unexposed) − mean(exposed); averaged over launches with equal weight. Positive means exposed repositories release sooner. Launches whose 28-day window is not fully observed, or that have no exposed or no unexposed repository at risk, are not used, and their number is reported.
- **Inference:** randomization. Each launch date is replaced by a date drawn at random from dates at least 14 days from every real launch, keeping the launch type, and the statistic is recomputed; 999 replications, seed 20261101. The p-value is the share of placebo statistics at least as far from the placebo mean as the observed statistic.
- **Confirmation rule:** the hypothesis is confirmed if the observed statistic is positive and p < 0.05.

### 3.5 Secondary analyses (reported; not used to decide confirmation)
1. The same statistic dropping unexposed repositories that are exposed to a different launch within 28 days after the announcement.
2. Regular releases only (hot-fixes excluded), with and without the control exclusion in (1).
3. The difference in the share of repositories releasing within 1 day.
Differences between 1 and 2 are expected, because the prior study found them. They are interpreted as descriptive.

### 3.6 Sample size and stopping
- Collection window: from the registration date until the earlier of (a) 15 launches meeting the criteria and (b) [FILL end date, at most six months after registration].
- If fewer than 15 launches are observed by the end date, the analysis is run on those available and described as underpowered. The number of launches and repository-launch pairs is reported. For reference, the prior study had 38 launches and 277 repository-launch pairs.
- No analysis of release data is run before the window closes. The decision to stop is made only by the rule above.

### 3.7 What would count as failing to confirm
A statistic that is not positive, or p ≥ 0.05, is reported as not confirmed. The estimate and the placebo range are reported either way. If not confirmed, the prior study's daily-resolution result is described as exploratory, as in section 1.

## 4. Data and materials
Release data: GitHub REST API (non-draft, non-prerelease releases), collected after the window closes. Materials: `launch_inclusion_criteria.md`, `launches_log.csv` (template: `launches_template.csv`), `exposure_codebook.md`, `exposure_coding_template.csv`, `confirmatory_analysis.py`, `SHA256SUMS`.

## 5. Known limitations
- Likely lower power than the prior study.
- Exposure coding involves judgment (section 3.3); agreement is reported.
- The estimate in the prior study may be inflated by the selection of the statistic; the holdout estimate is the one to quote.
- The 19 repositories are a convenience sample of prominent projects; confirmation would not extend to other ecosystems or to hosted models.
