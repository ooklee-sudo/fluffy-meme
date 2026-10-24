# Package results vs. the numbers currently in the manuscript (internal note; delete before submission)

The simulation code in this package is an implementation written from the manuscript's specification. The manuscript's
Tables 2-6 and Figures 1-2 were produced by earlier code that is not available, so the numbers differ. Table 7 (SAGraph) and the
structure of the findings agree. Before submission, either replace the manuscript's simulation numbers by the ones in
`results/tables_simulation.md` (and rewrite the statements that depend on them) or locate the original code.

| Quantity | Manuscript | This package |
|---|---|---|
| beta = 0: final adopters C / D | 299 / 144 | 152 / 50 |
| Difference C - D [95% CI] | 155 [115, 201] | 102 [90, 114] |
| Seeds in distributed plan | about 430 | about 620 |
| t50 C / D (h) | 2.72 / 1.59 | 2.39 / 1.70 |
| Plans nearly tied after 1 h | yes (56 vs 50) | no (37 vs 17) |
| Distributed ahead after 1 h | 40% of runs | 0% |
| Concentrated dominates (stochastic dominance, every hour) | yes | yes |
| Alternative schedulers: absolute difference | 286-340 (about 2x) | 199-248 (about 2x) |
| Ranking reversal, discounted reach and CVaR | near 0.1 | between 0.25 and 0.5 (Delta V < 0 first at 0.30, CI includes 0) |
| Ranking reversal, final reach | 0.2-0.3 | about 0.5 (18 [4, 33] at 0.30; -19 [-33, -1] at 0.50) |
| Eq. (2) prediction for final reach | 0.23 | 0.32 |
| beta at the SAGraph estimate (0.66) | not run | Delta V = -14 [-16, -13]; final adopters -13 [-36, 12] |
| SAGraph pooled beta (PPML) | 0.66 [0.63, 0.68] | 0.656 [0.631, 0.680]; all Table 7 rows agree to two decimals |
| Table B.1 PPML beta (true 0 / 0.35) | -0.017 / 0.283 | -0.064 / 0.346 (our random-effect scales differ) |
| Table B.1 OLS on ln(1+y) (true 0 / 0.35) | 0.82 / 0.94 | -0.00 / 0.83 |

What holds: concentration dominates under constant attention; the apparent scale-versus-speed trade-off in t50 is an artifact;
alternative schedulers roughly double absolute gaps; the ranking reverses at a moderate elasticity, and the estimated elasticity
(0.66) lies above the reversal points for discounted reach and downside risk.
What does not hold in this implementation: thresholds as low as 0.1; a near-tie after one hour; the 40% early lead of distributed seeding.
At beta = 0.66 the final-reach difference is imprecise (15 replications).
