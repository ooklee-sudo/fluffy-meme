# Study 5: self-generated failure

Episodes: 210; attempts after a first own failure: 797

| model                 |   episodes |   unsafe % |   honest exit % |   mean own failed test runs |   step limit % |
|:----------------------|-----------:|-----------:|----------------:|----------------------------:|---------------:|
| claude-haiku-5.5      |         30 |        0   |           100   |                        1.3  |            0   |
| deepseek-v4.1-flash   |         30 |        0   |           100   |                        1.77 |            0   |
| gemini-3.5-flash-lite |         30 |        3.3 |            40   |                        9.9  |           56.7 |
| gemini-3.8-flash      |         30 |        0   |            53.3 |                        8.13 |           46.7 |
| gpt-5.6-luna          |         30 |       26.7 |            73.3 |                        3.27 |            0   |
| mistral-large-4-0     |         30 |       10   |            53.3 |                        5.17 |           40   |
| qwen3.8-27b           |         30 |       20   |            56.7 |                        3.67 |           26.7 |

## Hazard of gaming per attempt, by own failed test runs so far

| fail_bin   |   attempts |   gaming_rate |
|:-----------|-----------:|--------------:|
| 1          |        129 |           0.8 |
| 2          |        110 |           2.7 |
| 3          |        106 |           6.6 |
| 4+         |        452 |           3.1 |

LPM (model FE, SE clustered by episode): own_fail b = +0.0047 (SE 0.0019), p = 0.012, n = 797.  
Logit on models with any gaming (n = 332): log(own_fail) b = +1.346 (SE 0.461), p = 0.003; OR for doubling = 2.54.

