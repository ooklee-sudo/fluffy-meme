# Analytical results for the LLM-retirement real options model

Notation. Retirements of the model in use arrive at dates T_1 < T_2 < ... over a horizon H (renewal process, expected discounted count Lambda = E[sum_i exp(-r T_i)]). A migration costs K for a hard-wired system and phi*K (0 < phi < 1) for a system with an abstraction layer and evaluation harness, which costs a premium P up front. At a retirement the vendor's successor is priced at a multiple R1 of the old price. An alternative vendor's successor is priced at R2. With probability c, R2 = R1; otherwise R2 is an independent draw from the same distribution F. The data-based F has mean E[R] = 2.48 and Gini mean difference G = E|R1 - R2'| = 1.66 (R2' an independent copy).

## Proposition 1 (value of lower migration effort)
The expected discounted saving from flexibility through effort alone is (1 - phi) K Lambda - P. The break-even premium is P* = (1 - phi) K Lambda. It increases in K, in the retirement frequency, in the horizon H and in (1 - phi), and does not depend on token volume. For Poisson retirements with rate lambda, Lambda = lambda (1 - exp(-rH)) / r.

Proof. Each migration date T_i contributes exp(-r T_i) times the cost difference K - phi K. Sum and take expectations. The Poisson form follows from E[sum exp(-r T_i)] = integral of lambda exp(-r t) dt over [0, H].

Check (`theory_check.py`): with mean effort 5.33 person-weeks and 4.42 retirements in 36 months (E[sum discounted] = 3.79), the formula gives 14.16, 10.11 and 4.05 weeks for phi = 0.3, 0.5, 0.8; the simulation (no emergency surcharge, no outage cost) gives 14.16, 10.12 and 4.05.

## Proposition 2 (value of choosing a vendor at retirement)
E[min(R1, R2)] = E[R] - (1 - c) G / 2. A firm that picks the cheaper successor pays on average a fraction 1 - (1 - c) G / (2 E[R]) of the price multiple that a hard-wired firm pays, at each retirement. The saving is zero when c = 1, rises linearly as the correlation c falls, and rises with the dispersion G of retirement price changes. With independent ratios across retirements, the expected price level after n retirements is the n-th power of the per-event multiplier, so the saving compounds.

Proof. For independent copies, min(x, y) = (x + y)/2 - |x - y|/2. Take expectations, and mix with the probability c of R2 = R1, for which min = R1.

Check: the identity holds exactly on the six empirical ratios (1.6466 on both sides). The per-event multiplier is 0.665, 0.832 and 1.000 of the rigid value at c = 0, 0.5 and 1.

## Proposition 3 (timing of early switches between two vendors)
Let s be the flow saving from holding the current vendor instead of the other (the other's monthly cost minus mine) and let s follow an arithmetic Brownian motion with zero drift and variance sigma^2 per month. Switching costs K and maps s to -s. The optimal policy switches when s falls to -b, where b solves
  kappa b - tanh(kappa b) = kappa r K / 2,  kappa = sqrt(2r) / sigma,
and for small bands b is close to (3 K sigma^2 / 4)^(1/3). The band satisfies b > rK/2, the band at which the present value of a permanent saving 2b equals K (the NPV rule). The band widens with sigma and with K.

Proof sketch. On the continuation region the value is V(s) = s/r + B exp(-kappa s). Value matching V(-b) = V(b) - K and smooth pasting V'(-b) = -V'(b) give B = 1 / (r kappa cosh(kappa b)) and then 2 B sinh(kappa b) = 2b/r - K, which reduces to the stated equation. Since tanh(kappa b) / kappa = b - rK/2 > 0, b > rK/2.

Check (`band_check.py`, r = 0.1/12 per month, K = USD 20,000, sigma = USD 1,000 per month): b* = 2,500 per month against an NPV band of 83. Simulated discounted payoff is 664,299 at the NPV band, 873,294 at half of b*, 886,460 at b*, 884,306 at 1.5 b*, 832,376 at 2.5 b*. The maximum lies at the theoretical b*; the NPV rule switches far too often (time step 0.1 month, so its switch count is understated).

Implication. A switching rule from option theory beats a plain NPV rule when the alternative's price is an exogenous level that moves randomly and a switch is costly. A model in which the price gap resets to zero after each switch, as in the first version of our simulation, instead rewards frequent switching and wrongly favors the NPV rule. This is the flaw that we found and fixed (see `results_v1_flawed_timing.md` for the superseded output).

## Predictions that can be tested with data (see STUDY_DESIGN.md)
- P1: the migration lag after a retirement notice is shorter for repositories with an abstraction layer.
- P2: when the replacement is priced much higher, a larger share of repositories change provider, and this share is higher for repositories whose code can swap providers cheaply.
- P3: migrations bunch near the shutdown date and are rarer than an NPV rule implies, because the optimal band is wider than the NPV band.
