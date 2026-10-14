# McDonald's alone: US comparable sales around the 2026 fuel shock (analysis defined 2026-10-14 at the author's request; exploratory, because McDonald's quarterly figures had already been seen)

**Author's premise.** McDonald's is the lowest-priced fast-food chain, so it should be hit hardest by lower-income households' budget pressure. (Not verified here: relative price positioning of chains is not in the data; the company itself says value-menu execution was weak in 2026Q2.)
**Data.** McDonald's US comparable sales growth (year over year) from SEC 8-K Exhibit 99.1, 2021Q4–2026Q2 (`chains2022/MCD.json`, `chains/MCD.json`; quotes verified); the other 12 chains (`chains2022`, `chains`) for comparison.
**Statistics (all fixed here, none tuned to results).**
- M1 (own history): Δ_t = comps_t − comps_{t−1} for McDonald's. Rank of Δ_2026Q2 among Δ_t, t = 2022Q2..2025Q4 (15 quarters; one-sided, lowest = worst). Same for Δ_2022Q2 (gasoline peak) among 2023Q2..2025Q4.
- M2 (relative to peers): R_t = Δ_t(MCD) − mean over other chains of Δ_t. Rank of R_2026Q2 among R_t, t = 2023Q2..2025Q4 (11 quarters, peers have full coverage), and the z-score using the peer cross-section SD of Δ_{c,2026Q2}.
- M3 (year-ago comparison, base effects): comps_2026Q2 − comps_2025Q2; two-year stack comps_t + comps_{t−4} for 2026Q1 and 2026Q2 (and the change in the stack).
**Limits.** One company, one post quarter, no significance test beyond ranks; comps mix price and traffic (traffic not numerically available); 2025Q1 was depressed by leap-day and weather so 2026Q1 had an easy comparison.
