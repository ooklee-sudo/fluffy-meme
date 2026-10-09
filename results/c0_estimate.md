# Implied serving-cost share c0/P from observed peak/off-peak ratios

Azure 2024 hour-of-day profile, quasi-static model. Entry = c0/P at which the model's best two-level schedule has the stated price ratio (number of peak hours in parentheses). First ratio column = ratio at c0 = 0.

| P (choke value) | unpriced demand / capacity | c | ratio at c0=0 | c0/P for 2x (DeepSeek) | c0/P for 1.5x | c0/P for 4x |
|---|---|---|---|---|---|---|
| 20 | 1.4 | 77 | 4.8x (10h) | 0.25 (10h) | 0.43 (10h) | 0.03 (10h) |
| 10 | 1.4 | 77 | 5.6x (10h) | 0.18 (10h) | 0.29 (8h) | 0.05 (10h) |
| 40 | 1.4 | 77 | 4.4x (10h) | 0.25 (10h) | 0.43 (10h) | 0.02 (10h) |
| 20 | 1.2 | 77 | 2.7x (8h) | 0.10 (8h) | 0.30 (8h) | - |
| 20 | 2.0 | 77 | 2.3x (10h) | 0.08 (10h) | 0.31 (10h) | - |
| 20 | 1.4 | 108 | 4.8x (10h) | 0.25 (10h) | 0.43 (10h) | 0.03 (10h) |
| 20 | 1.4 | 64 | 4.8x (10h) | 0.25 (10h) | 0.42 (10h) | 0.03 (10h) |


Reading: DeepSeek's 2x ratio implies c0/P of about 0.25 at 1.4x unpriced demand (insensitive to c = 64-108 and to P = 20 vs 40; 0.18 at P = 10), and 0.10 / 0.08 at
1.2x / 2.0x unpriced demand. So the estimate is c0/P in roughly 0.08-0.25, driven mainly by how far unpriced demand exceeds capacity, which is not observed.
The model's best schedule has 8-10 peak hours; DeepSeek's is 7 weekday hours (and the demand profile is Azure's, not DeepSeek's), so this is a loose consistency
check, not a test. The price level cannot identify c0 (units of user time vs dollars).