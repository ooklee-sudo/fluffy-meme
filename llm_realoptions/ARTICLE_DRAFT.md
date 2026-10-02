> **Superseded.** The numbers below come from a first version of the simulation whose price-gap module was flawed (see research_program/THEORY.md). Current results: results.md, breakeven.md and IEEE_Computer_manuscript.docx. Earlier output is kept in results_v1_flawed_timing.md.

# Managing Enterprise LLM Maintenance Uncertainties: A Real Options Framework for Cloud API Lifecycles

Target: IEEE IT Professional. Draft prepared 2026-10-02. Check the journal's current author guidelines for length and format before writing the full text.

## 1. Revised abstract (about 150 words)

Cloud large language model (LLM) APIs shorten the planning horizon of enterprise IT: model versions are retired roughly a year after release and their successors are repriced. Public records show a median lifetime of 13.8 months for retired Gemini API models (n = 9) and a median notice of 183 days for OpenAI retirements (n = 96). We treat maintenance as a set of real options, the option to choose among vendors at retirement and the option to switch early, and simulate a 36-month enterprise chatbot with inputs taken from these records. Against a hard-wired, reactive deployment, a flexible architecture lowered discounted lifecycle cost by 24% when successor prices were unchanged and by 3% to 77% when they changed, depending on how closely vendors' price changes move together. A volatility-based switching threshold did not outperform a simple net-present-value rule. We derive governance guidelines for CIOs and name the data they should collect.

Changes from the original draft: the single "up to 24%" claim is replaced by a range, because the size of the saving depends on assumptions that open data cannot fix (Section 5). "Novel" is dropped. The claim that the framework supplies a quantitative migration threshold is replaced by what the simulation showed.

## 2. Suggested outline

1. Introduction: the retirement cycle as a recurring cost for LLM-based services (about 400 words). Use the OpenAI table (96 retirements announced 2022–2026) and the Gemini table.
2. Background: real options in IT investment, and how API retirement differs from classical vendor lock-in (400).
3. Framework: three options, mapped to observable triggers (700). Option to choose at retirement (vendor or tier switch). Option to switch early when the price gap exceeds a threshold. Option to defer the flexibility investment. Define the premium (abstraction layer, evaluation harness) and the effort reduction it buys.
4. Evidence from open data (600). Lifetimes, notice periods, generation-to-generation price ratios, wages (Section 4 below).
5. Simulation and results (800). Strategies, parameters, base case, sensitivity (Section 5 below).
6. Governance guidelines for CIOs (500). See Section 6.
7. Limitations and what to measure next (300).

## 3. Strategies in the simulation (`sim.py`)

- **Rigid:** hard-wired, migrates only when the retirement date arrives, to the vendor's successor.
- **Flex:** pays a premium of 6 person-weeks up front, cuts migration effort to half, and at retirement takes the cheaper of the successor and an alternative vendor.
- **Flex + NPV switching:** flex plus an early switch whenever the present value of the savings from the lower price exceeds the switching cost.
- **Flex + real-options threshold:** flex plus an early switch only when savings exceed theta times the switching cost, where theta = b/(b-1) is the McDonald–Siegel multiple (2.1 at 10% monthly volatility of the price gap).

Cost is the present value over 36 months at 10% per year of token spend, migration labor, flexibility premium, emergency premium (x1.5) and outage cost (USD 2,000 per day) when notice is shorter than the time needed. It is a variable lifecycle cost; fixed operating costs of the chatbot are excluded.

## 4. Open data inputs

| Input | Value | Source |
|---|---|---|
| Version lifetime, release to retirement | median 13.8 months, range 5.7–21.2 (n = 9 retired Gemini API models) | ai.google.dev/gemini-api/docs/deprecations |
| Notice before retirement | median 183 days, quartiles 97 and 184, 3 of 96 under 90 days (OpenAI) | developers.openai.com/api/docs/deprecations |
| Successor price ratio (blended 5:1 input:output list price) | 4.4, 4.1, 0.45 (Flash tier); 1.3, 3.1, 1.5 (Flash-Lite tier) | ai.google.dev/gemini-api/docs/pricing; 2.0 prices from third-party aggregators |
| Labor cost | USD 91.5 per hour (BLS median developer pay USD 135,980 in May 2025, x1.4 for overhead) | bls.gov; the 1.4 is an assumption |

Google also announced that Gemini 3.6/3.7/3.8 Flash list prices rise on 2027-01-01, which is direct evidence of in-version price changes.

Not open data and therefore assumptions: migration effort (triangular 2–4–10 person-weeks), flexibility premium (6 weeks), effort reduction (halved), outage cost, token volume (1B tokens per month in the base case), and the price relationship between vendors.

## 5. Results (20,000 simulated lifecycles per scenario, paired comparison with the rigid strategy; 95% intervals for the mean saving)

Saving relative to the rigid strategy, in percent of its discounted cost.

| Scenario | Flex | Flex + NPV switching | Flex + threshold |
|---|---|---|---|
| Base (1B tokens/month, price correlation 0.5) | 54.1 [49.9, 58.3] | 65.2 [60.4, 70.0] | 62.9 [58.3, 67.4] |
| 100M tokens/month | 44.3 [42.0, 46.6] | 46.4 | 45.9 |
| 10B tokens/month | 56.1 | 73.6 | 72.9 |
| Alternative vendor price independent | 77.4 | 80.2 | 79.4 |
| Alternative vendor price perfectly correlated | 3.3 [3.3, 3.4] | 32.4 | 27.9 |
| No price shock at retirement | 23.7 [23.2, 24.2] | 24.0 | 23.8 |
| Short notice (x0.1) | 56.8 | 64.4 | 62.8 |
| Effort reduction only 20% | 51.2 | 60.6 | 58.5 |
| Premium 12 weeks | 51.8 | 62.9 | 60.6 |
| Effort 4–8–20 weeks | 59.6 | 66.4 | 64.8 |
| Price-gap volatility 0.36 per month | 54.1 | 80.1 | 69.2 |

Full output with all intervals: `results.md`. Reproduce with `python sim.py --n 20000`.

What the numbers say, and what they do not:

- The size of the saving is set mostly by how retirement prices of competing vendors co-move (3% if they move together, 77% if independent). The data cannot tell us which holds; it is the first quantity to estimate.
- Where successor prices are unchanged, the saving is about 24% and comes from lower migration effort net of the premium. This value coincides with the number in the earlier draft by chance and was not tuned.
- A volatility-based threshold did not beat the simple NPV rule in any scenario here. We therefore cannot claim that the option-theoretic threshold improves timing. The zero-drift price-gap process favors frequent switching and is probably too generous; a process with switching frictions (quality differences, re-evaluation cost) is needed before a timing claim can be made.
- At low token volume labor dominates and price risk matters little; the flexibility argument is strongest for high-volume deployments.

## 6. Governance guidelines supported by the evidence

1. Plan for a model replacement at least once per year; median lifetime is under 14 months.
2. Notice has usually been long enough (median about six months), so the cost of rigidity is mostly effort and price exposure, not outages; short-notice cases (3% of OpenAI records) deserve a runbook.
3. Invest in an abstraction layer and an evaluation harness only if expected migrations times the effort saved exceeds the premium; the break-even depends on volume and on how correlated vendor prices are.
4. Track list-price changes of your own tier and of at least one alternative vendor; the correlation between them decides how valuable the vendor-switch option is.
5. Do not set a switching trigger from a volatility formula alone; use a net-present-value check with an explicit switching cost until a better-calibrated process is available.

## 7. Limitations to state in the article

- Eleven Gemini and 96 OpenAI records; Google publishes no announcement dates in the table, so notice comes from OpenAI.
- Price ratios (n = 6) mix price and capability changes; they are not like-for-like price quotes.
- Effort, premium, outage cost and volume are assumptions; the paper should present a break-even analysis, not a point estimate.
- The data tables were extracted with an automated page reader and the 2.0-generation prices come from third-party aggregators. Verify each row against the live page or an archived copy before submission.
