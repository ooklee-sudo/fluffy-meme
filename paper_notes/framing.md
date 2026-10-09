# Framing draft: congestion wedge and the productivity paradox (English draft text for the manuscript)

Numbers refer to results/congestion_wedge.md (quasi-static model, Azure 2023 traces, assumptions as in the other result
files). Literature named below is from memory and must be checked: Solow (1987); Brynjolfsson (1993, CACM);
Brynjolfsson & Hitt (1996, Management Science); Brynjolfsson, Rock & Syverson (2021, AEJ: Macro, "The Productivity J-Curve").

## 1. Introduction paragraph (motivation)
Generative-AI usage is growing quickly, yet measured productivity gains remain hard to see - the latest instance of
the IT productivity paradox. The literature offers mismeasurement, lags from complementary investments, and
redistribution as explanations. We study a different and complementary channel that is specific to shared AI
infrastructure: congestion. Waiting time is borne by users, so it appears in neither the provider's revenue nor in
output or input statistics; and when demand is bursty, a capacity plan and a flat per-token price that look adequate
on average leave a persistent share of created value dissipated in queues. We call that unmeasured share the
*congestion wedge*. We do not claim that congestion explains the aggregate paradox; we show, in a calibrated
queueing model, when and how much of the value of AI usage is lost to it, and which pricing structures remove it.

## 2. Definition and results
Per unit time: Q = served requests (what usage statistics record); V = gross user value; Dc = time lost waiting;
W = V - Dc; wedge share = Dc / V.

Findings (quasi-static model, c = 45 for the conversation trace, c = 7 for the code trace):
- **Usage rises while welfare falls when access is unpriced.** Conversation trace, bursty demand, no price: as
  adoption (mean demand potential / capacity) goes from 1.0 to 2.4, throughput per unit capacity rises 0.88 -> 1.00
  but welfare per unit capacity falls 7.76 -> 4.35 and the wedge share grows 21% -> 72%. With the best flat price,
  welfare keeps rising with adoption (8.46 -> 12.96) and the wedge share stays near 10-12%.
- **This is already true under Poisson arrivals** (no price: welfare per capacity 8.82 at a = 1.0, 4.15 at a = 2.4), so
  the paradox-like pattern is a property of unpriced congestion, not of burstiness alone.
- **Burstiness shifts the onset earlier and keeps a wedge even with a flat price.** Code trace at low adoption
  (a = 0.5): wedge share 31% (bursty, no price) vs 10% (Poisson). At a = 1.4 with the best flat price the wedge share
  rises with demand dispersion: 11.7% (Poisson) -> 19.2% (fitted trace) for the code trace and 9.1% -> 11.4% for the
  conversation trace; phase-dependent (Pigouvian) prices bring it back to about 10%.
- **Caveat on a tempting hypothesis.** With *no price* at high adoption the wedge share is not monotone in dispersion
  (code trace at a = 1.4: 46.7% at zero dispersion, 21.3% at the trace's dispersion), because saturation dominates and
  the quasi-static model lets the off-peak phase absorb part of the load. "Burstier means a larger wedge" holds in the
  priced regime, not in general.

## 3. Policy implications and conclusion paragraph
Throughput and revenue are poor guides to the value of AI services when capacity is shared: they keep rising while the
user-borne waiting cost rises faster. The relevant diagnostic is the waiting cost per unit of value, and the remedy is
to price the congestion externality where it arises - phase-dependent prices in a bursty environment - or to ration it
by quantity, as providers do with rate limits. Observed list prices already contain delay-tolerant discounts (about
0.5x), priority premia (1.75-2x) and, at one provider, a 2x time-of-day ratio; these are far smaller than the peak/off-peak
ratio our calibrated model prescribes, which should be read as a limit of the model (no marginal-cost base price,
static price lists, no strategic response) rather than as evidence in its favour. Limits: simulations on two one-hour
traces, assumed service-time and demand parameters, no firm-level productivity data; the link to measured aggregate
productivity is a hypothesis for empirical work.
