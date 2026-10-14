# 2026 Iran war: consolidated findings and research-direction assessment (2026-10-14)

All analyses were fixed in plan files before estimation (disclosures of what had been seen are in each plan); exploratory additions are marked. Folders: `oil_income/`, `oi_tracker/`, `travel/`, `snap/`, `tobacco/`, `bofa/`, `stocks/`, `bigtech/`, `korea/`, `semis/`, `airlines/`, `poisson_posts/`, `hf/`. War onset 28 Feb 2026 (first U.S. trading day 2 March). WTI: $67 (27 Feb) → $114.6 (7 Apr) → $96 (6 Oct).

## A. Real-economy and consumption (monthly/quarterly data; nominal unless stated)
| Area | Result | Strength |
|---|---|---|
| Restaurants (Census, Mar–Jul vs trend) | +0.3% (all), limited-service −0.5%, full-service +1.8% (all within placebo range) | null |
| Fast-food chains comps (13 chains, SEC) | Δ2026Q2 +0.6 pp vs placebo quarters (p = 0.92); year-ago comparison not significant; McDonald's −3.1 pp (rank 2–3 of 12–16; base effect) | null |
| Discretionary vs essential retail | ratio +6.5% (highest of 10 years); health/personal care −6.5% (unexplained) | opposite to hypothesis |
| Grocery | −1.1% nominal, −1.8% real (p = 0.10 low tail) | null |
| Liquor stores | +2.7% (top of range, fragile) | weak |
| Cigarette shipments (TTB) | −1.0% vs trend (decline predates war) | null |
| White goods | retail not below trend; major-appliance output −3.7% (p = 0.5) | null |
| SNAP | participants −12% YoY (already −10% in Feb; work-requirement law) | policy, not war |
| Texas sales tax, OI card data (2022 episode), state employment (2022) | restaurants +0.7%; no gasoline effect on spending; employment effect fragile | null / fragile |
| U.S. citizens' trips abroad (NTTO) | Middle East −37% (largest of 10 years); other regions n.s.; Mexico air −12.6% | **supported (direct war effect)** |
| Lower-income households (BofA, published text) | March–April: gasoline share of spending 8–10%, discretionary spending down; June–Sept: lower-income growth highest, income gaps closed | supports a transitory squeeze |
Net: no durable aggregate consumption decline attributable to the oil shock through July–August; the identified effects are direct (Middle East travel) and transitory (lower-income discretionary, March–April).

## B. Financial markets (daily data; closing prices)
| Area | Result |
|---|---|
| 48 U.S. industries, first week | energy +3.6% (20-day +20.4%), defense +3.8%; gold −12.9%, mines −11.9%, tobacco −8.2%, soda −6.9%; transport −1.9% and restaurants −1.6% (n.s.); market −2.0% (week), −7.7% (month), recovered by August |
| Semiconductors | week 1: Samsung −23%, SK hynix −25%, TSMC (Taiwan) −5%, Nikkei −5%, SOX −4.2%, Nvidia +3.6%; since 27 Feb SOX +51% (peak +81% on 22 Jun, −29% to 29 Jul), Nvidia +29% and stable, Micron/Intel/Broadcom swings; Korean chips lead the late-June and late-July drawdowns |
| Korea | KOSPI −19% at the 31 Mar trough, −1.8% now; sensitivity to the previous U.S. session tripled (0.58 → 1.77, p = 0.001); daily |return| 1.1% → 3.0% |
| Airlines | Korean Air −21.5% in week 1 (p < 0.01), +6.9% since; T'way −62%; oil sensitivity −0.1 per 1% WTI with chip controls (p = 0.06), already present before the war |
| Oil and chips | daily correlation ≈ 0; chips (AI cycle) independent of oil shocks; OPEC+ and IEA/SPR announcement days did not move oil more than ordinary days (weak instruments) |

## C. Trump's Truth Social posts as information arrivals
- **Arrival process:** Iran-threat posts (n = 108) are overdispersed relative to a homogeneous Poisson (dispersion index 350 on 226 df; inter-arrival CV 1.9); a Poisson process with weekly varying intensity fits (Pearson dispersion 0.89), i.e., Poisson–Gamma/negative-binomial counts.
- **Daily/weekly markets:** no association of weekly threat counts with oil or equities; big-tech event study (14 news-selected events) shows no excess reaction beyond the market (p = 0.79).
- **High-frequency (hourly futures, blind-coded post classes, exploratory):** de-escalation posts (hold-off, ceasefire, deal; n = 33) are followed by **WTI −1.29%, Brent −1.21%, USD/KRW −0.14%, S&P +0.23%** within about two hours (p ≤ 0.006; WTI still −0.67%, p = 0.002, without the two largest events); **escalation posts (n = 28) show no oil or equity reaction** (WTI −0.02%, p = 0.92). The asymmetry is the cleanest new result.
- **Instrument use:** at daily frequency the posts are a weak instrument for oil (F = 2.8); Korean-airline reduced form null.

## D. Methodological lessons / errors fixed along the way
Fiscal-to-calendar quarter misalignment (Starbucks, Jack in the Box) fixed; return computation across one-market holidays fixed (Korea); OI tracker daily file switches to weekly in June 2022 (first run discarded); keyword classification of 'threat' posts included peace announcements (first high-frequency run reversed signs; fixed by blind coding); FRED/EDGAR access problems; quotes verified against SEC exhibits for 251 chain observations.

## E. What could be a research project, and how strong it is
1. **Asymmetric intraday market reaction to presidential social-media posts (strongest and most original here).** Information-arrival (Poisson–Gamma) → asymmetric price reaction (de-escalation moves oil, threats do not). Links to the earlier user-generated-content/Poisson theme (information arrival and its distribution; LLM coding). Needs: more events (2025 posts, other issues), human validation of the coding (currently one model instance), proper high-frequency data (Yahoo hourly is thin; ideally minute data), multiple-testing control, and a theory (e.g., signalling/credibility; cheap talk vs. announcements).
2. **Korean market's amplification of U.S./global shocks and semiconductors' independence from oil** — descriptive finance paper; exposed to AI-cycle confounding.
3. **Direct war effects on travel (Middle East −37%)** — straightforward, strong, but a small contribution.
4. **Consumption nulls (low-income restaurant spending)** — useful as robustness section, hard to publish alone (low power, nominal data).
For MISQ/ISR fit, only (1) has an information-systems angle (social media as information channel for markets, LLM-based content coding), and it is still preliminary (small n, endogenous posting times, single-coder). Assessment of publication readiness: low for MISQ now; moderate potential after extending the sample, human validation and a theory.

## F. Open items
Human coding of the Amazon/Yelp validation sheets (150 reviews each, two coders) still pending; chain-comps 2026Q3 (re-run when ≥ 10 chains report, mid-November); BofA/Circana originals for citations; verification of McDonald's call quotes against transcripts; extending the high-frequency analysis to minute data and to other posts (non-Iran).
