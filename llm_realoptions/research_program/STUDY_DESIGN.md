# Study design for a field test (target: JMIS, Decision Support Systems, then ISR or MISQ if results are strong)

## Question
Do firms and projects that invest in flexibility migrate faster and cheaper when an LLM version is retired, and do they respond to price changes the way the real options model predicts?

## Data
1. **Retirement records**: the vendor deprecation tables used in `data/` (OpenAI: announcement date, shutdown date, replacement; Google: release and shutdown dates). Extend to Anthropic, Azure OpenAI, AWS Bedrock and Vertex AI model lifecycle pages.
2. **Repository histories** (public GitHub), collected with `research_program/mine_migrations.py`. For each retired model identifier, files that contain it are located by code search, and the first commit after the announcement that removes it defines the migration date. Files that still contain it are right-censored.
3. **Flexibility proxy**: whether the repository, at the announcement date, imports a provider-agnostic layer (for example LiteLLM, LangChain, an internal gateway) or calls the vendor SDK directly, plus the share of calls that use model aliases instead of dated identifiers (the pinned share from `exposure_index.py`).
4. **Controls**: repository age, number of contributors, commit frequency, language, test presence, stars.
The code runs on your own machine with your own token. It was not run in the session that wrote it, and the GitHub search interface has rate limits, so a sample of a few thousand files is realistic.

## Measures
- **Migration lag**: days from announcement to the removal commit; censored if absent.
- **Notice share**: lag divided by notice length (announcement to shutdown).
- **Retirement Exposure Index** (`exposure_index.py`): share of model-identifier occurrences weighted by how near the shutdown is. It gives firms and researchers a simple exposure score and can be computed for any code base.
- **Provider switch**: the identifier replaced is from a different vendor.

- **Effort proxies** (from `mine_migrations.py`, pull-request and commit data of the migration change): lines added and deleted, files changed, hours from pull-request creation to merge, review comments, and whether the change touched prompt files or tests. They measure the size of public migration work. They are not person-weeks.

## Hypotheses
- **H1 (effort).** Lag is shorter for repositories with a provider-agnostic layer. Test: survival model (Cox, with censoring) of lag on the flexibility proxy and controls, clustering by repository owner. Model prediction: hazard ratio above 1 (Proposition 1).
- **H2 (choice).** The probability of a provider switch rises with the price multiple of the named replacement, and the rise is steeper for repositories with the flexibility proxy. Test: logit of provider switch on replacement price ratio, the proxy and their interaction (Proposition 2). Price ratios come from the vendor pricing pages.
- **H3 (timing).** Migrations bunch in the final third of the notice window, and bunching is stronger when the price gap between alternatives is more volatile or the migration cost is higher. Test: distribution of the notice share and its dependence on a repository-level proxy for migration cost (size, number of call sites). Model prediction: a wide switching band, not an NPV rule (Proposition 3).
- **H5 (effort).** Migrations in repositories with the flexibility proxy are smaller (fewer lines and files, faster merge) than in repositories without it. Test: regression of log lines changed and log hours to merge on the proxy and controls, with repository clustering (Proposition 1).
- **H4 (notice).** Longer notice does not shorten the lag proportionally (deadline effect): lag grows less than one-for-one with notice length.

## Identification and threats
- Selection: teams that adopt abstraction layers differ. Use within-repository comparison across several retirements, repository fixed effects, and a placebo using retirements of models that the repository does not use.
- Measurement: code search finds only identifiers in text files; configuration in environment variables or secrets is invisible. State this and treat it as classical measurement error.
- Public repositories are not enterprises. Complement with 5 to 10 firm interviews that give person-weeks, premium paid for the abstraction layer and outage experience; these replace the assumed parameters in the simulation.
- Ethics and terms: public data only, no personal e-mail addresses, aggregate reporting, check the GitHub terms of service and the target journal's data policy; ask your institutional review board whether review is needed.

## Contribution framing
Analytical result (Propositions 1 to 3), parameters calibrated from firm interviews and vendor records, and a field test of three testable predictions. The earlier practitioner article reports the simulation that motivates this work; the field study cites it.
