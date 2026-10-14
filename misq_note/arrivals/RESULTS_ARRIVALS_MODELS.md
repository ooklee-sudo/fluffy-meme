# Alternative models for the arrival of posts; a second account (Elon Musk, 2012–2017) (code: compare_models.py; output: results_model_comparison.json)

Descriptive comparison; no pre-registered hypothesis. Daily counts compared by AIC (Poisson; negative binomial = Poisson–Gamma; Poisson–lognormal; Poisson and NB INGARCH(1,1), a discrete self-exciting model in which today's mean depends on yesterday's count and mean). Inter-arrival times compared by AIC (exponential, gamma, Weibull, lognormal, Pareto). ΔAIC = AIC minus the best model's AIC (0 = best).

Data: Trump, original tweets 2017-01-21 to 2021-01-07 (public archive; exact times from tweet ids) and the oil/Iran and tariff/trade subsets; Trump Truth Social, original posts 2026-03-01 to 2026-10-13 (CNN archive); Musk, a public Kaggle-derived file (`musk_2017_tweets.csv`, 3,218 tweets 2012-11-16 to 2017-09-29, described by its source repository as all of his tweets in that span; completeness and time zone not verified by us), originals only (2,693).

## Daily counts (ΔAIC)
| Series | n / days | Poisson | NB (Poisson–Gamma) | Poisson–lognormal | Poisson INGARCH | NB INGARCH |
|---|---|---|---|---|---|---|
| Trump Twitter, all original | 15,530 / 1,448 | 3,662 | 626 | 639 | 1,261 | **0** |
| Trump Twitter, oil/Iran | 341 / 1,448 | 150 | 57 | 62 | 56 | **0** |
| Trump Twitter, tariff/trade/China | 937 / 1,448 | 543 | 137 | 129 | 280 | **0** |
| Trump Truth Social 2026, all original | 4,838 / 227 | 1,272 | **0** | 1 | 1,248 | 0 (collapses to NB) |
| Musk Twitter 2012–17, original | 2,693 / 1,779 | 3,700 | 238 | 249 | 2,484 | **0** |
| Musk Twitter 2016–17, original | 1,707 / 638 | 1,828 | 59 | 66 | 1,463 | **0** |

## Inter-arrival times (ΔAIC; CV in last column)
| Series | Exponential | Gamma | Weibull | Lognormal | Pareto | Best | CV |
|---|---|---|---|---|---|---|---|
| Trump Twitter, all | 19,245 | 251 | **0** | 3,837 | 40,772 | Weibull | 1.84 |
| Trump Twitter, oil/Iran | 446 | **0** | 48 | 248 | 786 | Gamma | 1.68 |
| Trump Twitter, tariff | 1,521 | **0** | 122 | 555 | 1,868 | Gamma | 1.83 |
| Trump Truth Social | 12,625 | 1,400 | 642 | **0** | 6,484 | Lognormal | 2.35 |
| Musk 2012–17 | 7,198 | 663 | 281 | **0** | 1,845 | Lognormal | 2.39 |
| Musk 2016–17 | 4,441 | 512 | 227 | **0** | 1,051 | Lognormal | 2.50 |

## Reading
1. A homogeneous Poisson process is rejected by a wide margin for every account and period, for counts and for waiting times.
2. The negative binomial (Poisson–Gamma) is far better than Poisson, but the Poisson–lognormal mixture fits as well (ΔAIC differences within about ±13 of each other); gamma versus lognormal mixing is not distinguishable with these data.
3. For the multi-year Twitter series a dynamic model, in which the current rate depends on the recent past, is far better than any static mixture (ΔAIC 57 to 626). The 2026 series is short (227 days) and the static NB suffices there. Clustering over days is a real feature, not only a rate that varies independently across days.
4. A power-law waiting-time distribution is clearly worse than gamma, Weibull or lognormal in every series; the waiting times are heavy-tailed but not of the power-law form. Lognormal is the best waiting-time model for Truth Social and for Musk; gamma or Weibull for the Trump Twitter series.
5. Musk's account shows the same qualitative pattern as Trump's (overdispersion, dynamic dependence, lognormal-type waiting times, CV 2.4–2.5), which fits the general finding that human posting is bursty. It does not show that the pattern is specific to people whose words carry weight: there is no comparison with ordinary accounts, and one further account is one further account.
Limits: the Musk file is a third-party extract of unknown completeness and time zone, covers only 2012–2017, and is the same API-era dataset for a person who tweeted far less than later; no ordinary-user comparison; counts by calendar day in UTC; all fits are by maximum likelihood without goodness-of-fit tests beyond AIC.
