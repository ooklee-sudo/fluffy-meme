# Related-work map (from a web-search subagent; NOT independently verified by me)

Status: every entry was returned by a search or a fetched page, but the subagent read abstracts and snippets only,
never full texts. Authors, years and venues must be checked against the primary source before citing. Items in
section F were not found and must not be cited.

## A. Queueing pricing and peak-load pricing
- Naor (1969), Econometrica 37(1) - regulation of queue size by tolls
- Mendelson (1985), CACM 28(3) - pricing computer services, queueing effects
- Dewan & Mendelson (1990), Management Science 36(12) - user delay costs and internal pricing
- Mendelson & Whang (1990), Operations Research 38(5) - incentive-compatible priority pricing, M/M/1
- Dewan (1996), Information Systems Research 7(3) - pricing computer services under alternative control structures (an ISR anchor)
- Afeche & Mendelson (2004), Management Science 50(7); Afeche (2013), M&SOM 15(3)
- Hassin & Haviv (2003), To Queue or Not to Queue (imprint/year disagree across sources); Stidham (2009), Optimal Design of Queueing Systems
- Steiner (1957), QJE 71(4); Boiteux (1960), Journal of Business 33(2) - peak-load pricing, deterministic periods, no queueing

## B. Dynamic vs static pricing; Markov-modulated demand
- Paschalidis & Tsitsiklis (2000), IEEE/ACM ToN 8(2); Ata & Shneorson (2006), Management Science 52(11)
- Afeche & Ata (2013), M&SOM 15(2); Kim & Randhawa (2018), Operations Research 66(2) (two prices capture most of the dynamic value)
- Bergquist & Elmachtoub (2025), Stochastic Systems 16(1), arXiv 2305.09168 - static pricing guarantees (Poisson)
- Unconfirmed details: Hemachandra & Narahari (MMPP/GI/1 profit), Ormeci & van der Wal (2006), arXiv 1307.2601, Yoon & Lewis
- Gap noted by the subagent: no paper found comparing static vs phase-dependent prices for an MMPP queue with a
  closed-form "kappa-weighted average of phase tolls" condition (limited search; check Google Scholar and INFORMS).

## C. Cloud / API pricing
- No ISR/MISQ/JMIS/Management Science paper on cloud or LLM pricing under congestion found (verify directly).
- POM (2024) capacity reservation for cloud demand surges (DOI 10.1177/10591478241251614, authors missing);
  Dierks & Seuken (2020) cloud pricing working paper; Song & Guerin spot-instance pricing; Kash, "Pricing the cloud" (venue unconfirmed).

## D. LLM inference economics and queueing (2023-2026, mostly arXiv)
- McDougall & Sankaralingam (2026), "Pricing time, not just tokens", arXiv 2609.40098, stated as accepted to EC'26 (opened)
- Bergemann, Bonatti & Smolin (2025/26), "Menu pricing of large language models", arXiv 2502.07736 (opened)
- Lin, Ding, Han & Zhang (2026), prefill-decode contention, asymptotically optimal control, arXiv 2602.02987 (opened)
- Dai, Deng, Li & Peng (2025/26), throughput-optimal scheduling for LLM inference, arXiv 2504.07347 (opened)
- Ramani & Tantawi (2026), approximate queueing model for SLO-driven autoscaling, arXiv 2609.20957 (opened)
- Katageria, Rani & Sengupta (2026), LLM inference under bursty workloads (MMPP, scheduling, no pricing), arXiv 2608.06135 (opened)
- Chen et al. (2026), token economics survey, arXiv 2605.09104 (opened)
- Search-only titles (authors missing): arXiv 2506.04645, 2603.28576, 2606.11690, 2608.23986, 2601.10274, 2606.15555, 2605.04595, 2604.11001, 2512.12928, 2406.03243, 2512.03416

## E. Burstiness evidence
- Wang et al. (2024/25), BurstGPT, arXiv 2401.17644 (10.31M traces, 213 days, Azure OpenAI; opened)
- Patel et al. (2024), Splitwise, ISCA 2024 (Azure traces, Nov 2023); Stojkovic et al. (2025), DynamoLLM, HPCA 2025 (2024 Azure trace)
- Secondary: DualScale (arXiv 2602.18755) variance-time analysis of the Azure trace

## F. Not found / from memory - do not cite until checked
Lippman & Stidham (1977); Low (1974); Chen & Frank (2001); Stidham (1985); Maglaras & Zeevi (2003); Gans & Savin (2007);
Heffes & Lucantoni (1986); Fischer & Meier-Hellstern (1993); Harchol-Balter (2013); any ISR/MISQ/JMIS cloud-pricing papers.

## G. Closest papers (threats to novelty) and how to differ
1. McDougall & Sankaralingam (EC'26): flat per-token prices optimal in a static screening model; show phase-dependent congestion externalities break this.
2. Lin et al. (2602.02987): fluid-limit optimum with steady rates misses burst-induced loss.
3. Kim & Randhawa (2018) / Bergquist & Elmachtoub (2025): our gap comes from exogenous demand modulation, not queue-length information.
4. Bergemann, Bonatti & Smolin: marginal-cost linear pricing; show what changes when marginal cost is a phase-dependent congestion toll.
5. Paschalidis & Tsitsiklis (2000), Ata & Shneorson (2006): decomposition into a capacity-misjudgment term and a price-misallocation term; phase prices need no real-time queue observation.
Also cite and do not overlap: Dai et al., Katageria et al., Ramani & Tantawi.
