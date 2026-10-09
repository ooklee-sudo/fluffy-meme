# Draft manuscript (working title): When Is a Flat Price Wrong? Pricing Shared LLM Inference Capacity under Phase-Varying Demand

Status: structured draft for the authors. All numbers are taken from files in results/ (named in brackets). Literature statements are
unverified (see paper_notes/related_work.md); claims of novelty are provisional. Not ready for submission.

## Abstract (draft)
Providers of large-language-model (LLM) inference sell capacity that users share, so one user's request delays others. Industry practice
is mostly a time-invariant per-token price, and capacity is planned with Poisson-arrival models. We study pricing when demand switches between
phases (hours of the day, bursts). In a quasi-static queueing model with equilibrium demand we show (i) the welfare-optimal price in a
phase equals the congestion toll and rises strictly with the phase's demand, so no flat price is first best unless phases are alike;
(ii) the best flat price is a weighted average of the phase tolls and its exact loss has an integral form; (iii) when phases switch
fast relative to queue dynamics a flat price becomes first best, and in between the loss is largest for bursts lasting a few service times.
Calibrated on Azure LLM inference traces and BurstGPT, a flat price forgoes about 14-15% of welfare relative to hour-by-hour prices on a
trace with a strong daily cycle, while a two-level peak/off-peak schedule removes roughly 70% of that loss; Poisson-based sizing
understates the servers needed to meet a delay target by 20% (conversation trace) to more than 80% (code trace). A peak/off-peak ratio of 2, as
a provider (DeepSeek) now posts, is consistent with a serving-cost share of 8-25% of the marginal user's value.

## 1. Introduction
(1) Motivation: growth of LLM usage, shared capacity, observed non-flat price structures: a documented 2x peak/off-peak ratio (DeepSeek), 0.5x
delay-tolerant tiers (Batch, Flex) and 2x-6x low-latency tiers (OpenAI Fast, Ultrafast) [paper_notes/market_evidence.md].
(2) Question: when is a time-invariant price wrong, by how much, and how much of the loss does a simple schedule recover?
(3) Approach and contributions, in order of strength: exact first-order and integral characterisation of flat-price loss (Section 3);
a fast-switching limit and numerical map between limits (Section 3.3); calibration on public traces and list prices (Section 4).
(4) Secondary, flagged as extensions: a congestion wedge between measured throughput and welfare (relation to the IT productivity paradox),
and a duopoly illustration.

## 2. Related work (to be verified before use)
Queueing pricing (Naor 1969; Mendelson 1985; Mendelson and Whang 1990; Afeche and Mendelson 2004), peak-load pricing (Steiner 1957; Boiteux 1960),
dynamic vs static pricing in queues (Paschalidis and Tsitsiklis 2000; Ata and Shneorson 2006; Kim and Randhawa 2018; Bergquist and Elmachtoub 2025),
LLM pricing (Bergemann, Bonatti and Smolin 2025; McDougall and Sankaralingam 2026), LLM serving queueing/scheduling (Lin et al. 2026; Dai et al. 2025),
traces (Patel et al. 2024; Wang et al. 2024). Position relative to McDougall and Sankaralingam: they abstract from queueing and state that stochastic demand
would connect their framework to congestion externalities; their "volume-independent price" is about linearity in volume, ours about constancy over time
[paper_notes/theory.md, Section 3]. Gap claim ("no paper found combining Markov-modulated demand, welfare-optimal pricing and an LLM service model")
rests on a limited search and must be re-checked in Google Scholar and the INFORMS/MISQ/JMIS archives.

## 3. Model and results
### 3.1 Model (paper_notes/theory.md, Section 1)
Phases k with probabilities pi_k; users observe the phase and price; linear inverse demand; delay d(lambda) increasing and convex; quasi-static
queue; welfare = user value minus waiting cost; serving cost c0 per request.
### 3.2 Results (paper_notes/theory.md, Section 2; numerical checks in results/theory_props.md and results/theory_verify.md)
P1 tolls rise with demand; P2 flat price is a convex combination of phase tolls, never first best unless phases are alike, FOC
sum pi kappa (p - t) = 0; P3 exact integral loss (checked to four decimals: 4.8265 vs 4.8264 and 31.8094 vs 31.8093); P4 local formula,
accurate for small dispersion and not beyond. A negative result is reported: the direction of the error from pricing at the mean demand
depends on curvature (above the optimal flat price for the code trace, below for the conversation trace).
### 3.3 Switching speed (paper_notes/theory.md, Section 5; results/switching_scaling.md)
Theorem 5 (fast switching: flat is first best in the limit; proof by finite-state perturbation). Numerical map for the code-trace MMPP:
loss 0.28% (burst 0.02 service times) rising roughly linearly to 19.0% at 4.1 service times and about 17% for slow switching.
The rate (quadratic conjectured) is not supported and left open.

## 4. Evidence
### 4.1 Traces
- Azure 2023 (19,366 conversation and 8,819 code requests, ~1 hour each) [results/trace_calibration.md, trace_models.md]: inter-arrival CV^2 1.20 (conversation)
  and 173 (code). Servers needed for P(wait > mean service) <= 5%: conversation real 43, block bootstrap 53, rate-chain 52, Poisson 41, 2-state MMPP 72;
  code real 38, bootstrap 42, 2-state MMPP 45, Poisson 7. Matching IDC with a 2-state MMPP overstates delay on the conversation trace.
- Azure 2024 code (16.8 million requests, 7 days) [results/longtrace_azure.md]: hour-of-day peak 2.15x mean, trough 0.24x; large residual burstiness;
  replay delays far exceed Poisson and exceed the daily-cycle NHPP at moderate load.
- BurstGPT file 1 (1.43 million requests, 61 days) [results/longtrace_burst.md]: daily counts range 1,576-149,520, so multi-day swings dominate; hourly
  phases: flat loses 14.5%, an hour-of-day schedule 14.2% (no gain), no price 48.3%.
### 4.2 Pricing (Azure 2024 hour-of-day phases; results/longtrace_azure.md, schedule_test.md, robustness.md)
Relative to hour-by-hour first best: no price 44.1%, best flat 14.7%, best two-level 4.6%; a posted 2x schedule with 8-10 peak hours 4.6-5.2% when
c0/P is low and worse than flat when c0/P is large (19.0% vs 14.0% at c0 = 8, P = 20). Equilibrium demand with posted prices, exact CTMC and
simulation with non-exponential service (cs2 0.5-16) [results/trace_equilibrium.md, trace_service_pricing.md]: flat price loses 6% (conversation) and
17-19% (code) of phase-dependent welfare; no price 38-71%; results hardly depend on cs2 for the code trace and shrink with cs2 for the conversation trace.
### 4.3 List prices and c0 (results/c0_estimate.md; paper_notes/market_evidence.md)
Directly verified: DeepSeek peak = 2x off-peak, 7 weekday peak hours (China working hours excluding lunch); OpenAI Fast 2x, Batch/Flex 0.5x,
Ultrafast 6x; Bedrock Reserved/Priority/Standard/Flex tiers. A 2x ratio implies c0/P of 0.08-0.25 depending mainly on how far unpriced demand
exceeds capacity. This is one parameter fitted to one ratio: it is a consistency check, not a test.

## 5. Extensions (labelled as such)
- Heterogeneous delay costs: flat-price loss persists (10.2% code, 5.8% conversation) [results/theory_props.md].
- Duopoly (logit): phase prices raise profit per firm (code 11.78 -> 14.38; conversation 209.06 -> 276.96) while welfare is slightly lower (94.36 -> 92.67;
  972.04 -> 968.99); welfare excludes differentiation surplus; illustration only.
- Congestion wedge (paper_notes/framing.md, results/congestion_wedge.md): unpriced access makes throughput rise while welfare falls; same pattern under Poisson.

## 6. Limitations (to state in the paper)
Quasi-static theory covers slow switching only; the quadratic fast-switching rate is unproved; service times are built from tokens with assumed coefficients
(0.5 ms per prompt token, 30 ms per generated token); demand is linear with assumed choke value and unpriced-demand ratio; traces are one hour (2023), seven days
(2024) and 61 days (BurstGPT) and the last is dominated by multi-day swings that no phase model here captures; no firm-level productivity data;
c0 is identified only through one price ratio; list prices are static; providers also ration by rate limits and 429/503 errors; the duopoly welfare measure is incomplete.

## 7. What would still be needed for a top-tier submission
A sharper single theorem with consequences beyond the exact flat-price characterisation (for example, conditions under which a two-level schedule is
near optimal, with a bound); a properly specified competition model; an over-identified empirical test (several posted price structures explained by one
parameter set); verified literature positioning.
