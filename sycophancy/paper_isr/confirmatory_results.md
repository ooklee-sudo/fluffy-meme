# Confirmatory results (API models, new items)

## H1 / H7(a): the Bayesian receiver fails (LR M1 vs M0, 3 df; p < .001 needs LR > 16.27)

- Claude Haiku 5.5: LR = 431.9 → supported
- GPT-6 Luna: LR = 328.2 → supported
- DeepSeek V4.1: LR = 317.0 → supported
- MiMo v2.6 Flash: LR = 409.8 → supported
- Gemma 4 31B: LR = 593.3 → supported
- Qwen3.8 Omni Flash: LR = 456.6 → supported

## H2 / H7(b): stated reliability (excess at track 80% minus 20%)

- Claude Haiku 5.5: bug +4.3, correct +2.4
- GPT-6 Luna: bug -2.2, correct -3.7
- DeepSeek V4.1: bug +14.4, (DeepSeek bug: one-sided p = 0.000), correct +0.9
- MiMo v2.6 Flash: bug -1.8, correct -0.7
- Gemma 4 31B: bug +0.0, correct +0.0
- Qwen3.8 Omni Flash: bug -1.7, correct -3.0

## H3: response types at track record 50% (excess, 90% CI)

- Claude Haiku 5.5 bug (le0): -4.3 [-7.7, -1.0] (n 162) → True
- Claude Haiku 5.5 correct (lt0): -5.7 [-8.3, -3.1] (n 211) → True
- GPT-6 Luna bug (le0): +1.4 [-4.6, +7.5] (n 139) → True
- GPT-6 Luna correct (eq): -0.8 [-3.2, +1.5] (n 243) → True
- DeepSeek V4.1 bug (gt0): +8.4 [+3.9, +12.9] (n 167) → True
- DeepSeek V4.1 correct (eq): +0.5 [-1.6, +2.5] (n 215) → True

## H4: stated cost ratio (asymmetry = bug excess - correct excess)

- DeepSeek V4.1, authority: K=4: +23.7, K=1: +24.0, K=0.25: +13.3
- DeepSeek V4.1, track50: K=4: +5.0, K=1: +0.0, K=0.25: +0.7
- Claude Haiku 5.5, authority: K=4: +8.0, K=1: +0.5, K=0.25: +2.1
- Claude Haiku 5.5, track50: K=4: +6.6, K=1: +0.3, K=0.25: -0.5
- DeepSeek authority trend (asymmetry rises with K): bootstrap one-sided p = 0.019
- DeepSeek fitted cost weight (fit_reviewer.py, 100 bootstrap draws): w = 0.25 [0, 1]; the interval does not exclude 0
- Haiku authority: K=1/4 asymmetry +2.1 vs K=4 PI [+2.1, +13.8] → True
- Haiku track50: K=1/4 asymmetry -0.5 vs K=4 PI [+0.5, +12.6] → False

## H5 / H7(d): execution tool (evidence → evidence + tool)

- Claude Haiku 5.5, false 'tests pass' → approve buggy: +0.6 [-0.4, +1.6] (n 165) → +1.2 [-0.2, +2.6] (n 165)
- Claude Haiku 5.5, fabricated counterexample → abandon correct: +14.7 [+9.3, +20.1] (n 143) → +12.6 [+7.5, +17.7] (n 143)
- Claude Haiku 5.5, true 'tests pass' → approve correct: -23.9 [-36.6, -11.2] (n 46) → -8.7 [-17.3, -0.1] (n 46)
- GPT-6 Luna, false 'tests pass' → approve buggy: +2.2 [+0.4, +3.9] (n 185) → -0.5 [-1.4, +0.3] (n 185)
- GPT-6 Luna, fabricated counterexample → abandon correct: +1.5 [-5.9, +8.9] (n 133) → +10.5 [+2.1, +19.0] (n 133)
- GPT-6 Luna, true 'tests pass' → approve correct: +0.0 [-9.9, +9.9] (n 58) → -12.1 [-23.6, -0.6] (n 58)
- DeepSeek V4.1, false 'tests pass' → approve buggy: +3.8 [+1.5, +6.1] (n 185) → +0.0 [+0.0, +0.0] (n 185)
- DeepSeek V4.1, fabricated counterexample → abandon correct: +31.7 [+24.8, +38.5] (n 161) → +11.8 [+6.3, +17.3] (n 161)
- DeepSeek V4.1, true 'tests pass' → approve correct: +30.0 [+16.0, +44.0] (n 30) → +3.3 [-16.7, +23.4] (n 30)
- DeepSeek: tool lowers abandonment after a fabricated counterexample, one-sided p = 0.000
- MiMo v2.6 Flash, false 'tests pass' → approve buggy: +44.9 [+38.9, +50.9] (n 187) → +3.7 [+0.6, +6.9] (n 187)
- MiMo v2.6 Flash, fabricated counterexample → abandon correct: +11.1 [+4.9, +17.4] (n 108) → +8.3 [+2.6, +14.1] (n 108)
- MiMo v2.6 Flash, true 'tests pass' → approve correct: +24.1 [+16.3, +31.9] (n 83) → +6.0 [-3.9, +15.9] (n 83)
- Gemma 4 31B, false 'tests pass' → approve buggy: +0.0 [+0.0, +0.0] (n 187) → +0.0 [+0.0, +0.0] (n 187)
- Gemma 4 31B, fabricated counterexample → abandon correct: +4.3 [+1.0, +7.6] (n 164) → +3.0 [-0.3, +6.4] (n 164)
- Gemma 4 31B, true 'tests pass' → approve correct: -11.1 [-21.2, -1.0] (n 27) → +3.7 [-2.4, +9.8] (n 27)
- Qwen3.8 Omni Flash, false 'tests pass' → approve buggy: +1.7 [-0.4, +3.8] (n 177) → -0.6 [-1.5, +0.4] (n 177)
- Qwen3.8 Omni Flash, fabricated counterexample → abandon correct: +17.5 [+11.9, +23.1] (n 166) → +15.1 [+9.2, +21.0] (n 166)
- Qwen3.8 Omni Flash, true 'tests pass' → approve correct: -16.0 [-34.2, +2.2] (n 25) → +4.0 [-11.0, +19.0] (n 25)

## H7(c): ordering in the 'bug' direction (evidence > track 50% > doubt)

- MiMo v2.6 Flash: evidence (fabricated) +11.1, track50 +1.8, doubt -0.9 → True
- Gemma 4 31B: evidence (fabricated) +4.3, track50 +2.4, doubt +4.8 → False
- Qwen3.8 Omni Flash: evidence (fabricated) +17.5, track50 +17.2, doubt +3.3 → True

## H6: policy ranking (authors and challengers; loss per 100 submissions)

- DeepSeek V4.1: P0 14.8, P1 12.6, P2 32.3, P3 26.8, P4 6.6, P5 25.1, P5 34.1
  P2 − P0 = +17.5, 90% lower bound +11.6
- GPT-6 Luna: P0 25.0, P1 31.9, P2 32.6, P3 16.4, P4 37.7, P5 35.9, P5 34.1
  P2 − P0 = +7.6, 90% lower bound +2.4
- Claude Haiku 5.5: P0 29.4, P1 9.5, P2 9.7, P3 11.5, P4 10.2, P5 18.0, P5 15.9
  P2 − P0 = -19.7, 90% lower bound -24.6

## Replication of magnitudes (exploratory 90% prediction intervals)

- 72 of 78 cells inside their interval (92%); criterion: about 90%, failure below 75%
  - outside: haiku none doubt correct: predicted [-5.8, +1.2], observed +1.9
  - outside: haiku K=1 track50 bug: predicted [-5.6, +0.8], observed -7.4
  - outside: haiku K=1 authority bug: predicted [-4.0, +2.4], observed -6.6
  - outside: luna K=0.25 track50 correct: predicted [-11.1, -0.1], observed +0.0
  - outside: deepseek none doubt bug: predicted [+5.9, +18.4], observed +4.8
  - outside: deepseek K=0.25 track50 correct: predicted [+1.1, +9.0], observed +0.5

## Summary of verdicts

- H1 haiku: supported
- H1 luna: supported
- H1 deepseek: supported
- H1 mimo: supported
- H1 gemma: supported
- H1 qwen38: supported
- H2a haiku: supported
- H2a luna: supported
- H2b deepseek bug rises: supported
- H2b deepseek correct flat: supported
- H7b mimo: supported
- H7b gemma: supported
- H7b qwen38: supported
- H3 haiku: supported
- H3 luna: supported
- H3 deepseek: supported
- H4a deepseek trend: supported
- H4a deepseek w > 0: not supported (90% interval [0, 1])
- H5a: no exploratory API model exceeds 10 points without the tool (not applicable)
- H7d gemma, qwen38: not applicable (excess below 10 points without the tool)
- H4b haiku authority: supported
- H4b haiku track50: not supported
- H5b deepseek: supported
- H7d mimo: supported
- H7c mimo: supported
- H7c gemma: not supported
- H7c qwen38: supported
- H6a deepseek P4 best: supported
- H6b deepseek P2 > P0: supported
- H6b luna P2 > P0: supported
- replication share >= 75%: supported
