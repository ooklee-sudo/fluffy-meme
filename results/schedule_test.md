# Schedules with real list-price ratios (Azure 2024 hour-of-day profile, c=77, quasi-static)

Loss (% of welfare) relative to hour-by-hour first-best prices; 'h' = number of peak hours chosen.

| c0 | no price | best flat | free 2-level | ratio 1.5x | ratio 2x | ratio 4x | ratio 6x | 2x with 7 peak h (DeepSeek-like) |
|---|---|---|---|---|---|---|---|---|
| 0.0 | 44.1% | 14.7% | 4.6% | 6.9% (8h) | 5.2% (8h) | 4.7% (10h) | 4.7% (10h) | 6.3% |
| 4.0 | 43.6% | 14.4% | 4.5% | 5.0% (8h) | 4.6% (10h) | 28.2% (8h) | - | 7.1% |
| 8.0 | 42.8% | 14.0% | 4.2% | 4.3% (10h) | 19.0% (9h) | - | - | 20.9% |

Reading (c0 = serving cost per request in the same units as user delay cost; its value is not observed):
- With c0 = 0-4 a 2x schedule with 8-10 peak hours loses 4.6-5.2% against hourly first-best prices, versus 14.4-14.7% for a flat price
  (captures about 65-70% of the gain) and about the same as the best free two-level schedule (4.5-4.6%). A DeepSeek-like 7 peak hours loses 6.3-7.1%.
- With c0 = 8 the model's optimal ratio is about 1.5x (4.3% loss); a 2x schedule overshoots and is worse than flat (19.0% vs 14.0%; 20.9% with 7 peak hours).
  Ratios of 4x-6x are infeasible or harmful once c0 >= 4 in this model.
- Caveats: Azure's hour-of-day profile is not DeepSeek's demand profile; DeepSeek's weekday/weekend structure is not modelled; c0 unknown.
