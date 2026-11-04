# Action-order robustness

## order_check__haiku45__balanced

Skip rate (%) by the action listed first:

| first_listed   |   gain |   loss |   neutral |   all |   n |
|:---------------|-------:|-------:|----------:|------:|----:|
| hold           |   61.3 |    8.8 |      15   |  28.3 | 240 |
| narrow_patch   |    0   |    0   |       0   |   0   | 240 |
| narrow_skip    |    1.2 |    0   |       0   |   0.4 | 240 |
| rollback       |   38.8 |    0   |       3.8 |  14.2 | 240 |
| wide_patch     |    0   |    0   |       0   |   0   | 240 |
| wide_skip      |   28.7 |   25   |      33.8 |  29.2 | 240 |

Contrasts pooled over the six orders (within wording, bootstrap over wordings):

| Contrast | Mean, pp | 95% CI | 99.6% CI | Wordings + / − | SD (excess) |
|---|---|---|---|---|---|
| loss minus gain | -16.0 | [-24.0, -7.5] | [-26.7, -3.3] | 3 / 13 | 16.9 (14.8) |
| neutral minus gain | -12.9 | [-21.7, -3.7] | [-24.8, +1.2] | 4 / 12 | 18.4 (16.3) |

Main contrast within each order (mean over wordings, pp):

| First listed | loss minus gain | 95% CI |
|---|---|---|
| hold | -52.5 | [-76.2, -26.2] |
| narrow_patch | floor | – |
| narrow_skip | -1.2 | [-3.8, +0.0] |
| rollback | -38.8 | [-58.8, -18.8] |
| wide_patch | floor | – |
| wide_skip | -3.7 | [-30.0, +22.5] |

## order_check__haiku45__s4_balanced

Skip rate (%) by the action listed first:

| first_listed   |   gain |   loss |   loss_goal |   neutral |   neutral_goal |   all |   n |
|:---------------|-------:|-------:|------------:|----------:|---------------:|------:|----:|
| hold           |   63.7 |    6.2 |        55   |      17.5 |           68.8 |  42.2 | 400 |
| narrow_patch   |    0   |    0   |         0   |       0   |            0   |   0   | 400 |
| narrow_skip    |    1.2 |    0   |         0   |       0   |            6.2 |   1.5 | 400 |
| rollback       |   45   |    0   |        46.2 |       2.5 |           36.2 |  26   | 400 |
| wide_patch     |    0   |    0   |         6.2 |       0   |            1.2 |   1.5 | 400 |
| wide_skip      |   31.2 |   26.2 |        30   |      25   |           43.8 |  31.2 | 400 |

Contrasts pooled over the six orders (within wording, bootstrap over wordings):

| Contrast | Mean, pp | 95% CI | 99.6% CI | Wordings + / − | SD (excess) |
|---|---|---|---|---|---|
| goal effect, neutral text (neutral_goal - neutral) | +18.5 | [+10.4, +26.7] | [+7.1, +29.8] | 13 / 2 | 17.0 (14.4) |
| goal effect, loss text (loss_goal - loss) | +17.5 | [+8.1, +28.1] | [+4.2, +32.7] | 12 / 3 | 21.1 (19.5) |
| valence without target (loss - neutral) | -2.1 | [-6.2, +1.7] | [-8.1, +3.3] | 3 / 7 | 8.3 (5.8) |
| valence with target (loss_goal - neutral_goal) | -3.1 | [-12.3, +5.6] | [-17.1, +10.6] | 8 / 7 | 19.1 (16.1) |
| registered contrast (loss - gain) | -18.1 | [-26.5, -9.2] | [-29.6, -5.0] | 3 / 13 | 18.3 (16.3) |
| gain - neutral_goal (both state the target) | -2.5 | [-9.6, +4.6] | [-13.1, +8.3] | 5 / 7 | 14.7 (10.2) |

Main contrast within each order (mean over wordings, pp):

| First listed | goal effect, neutral text (neutral_goal - neutral) | 95% CI |
|---|---|---|
| hold | +51.2 | [+26.2, +72.5] |
| narrow_patch | floor | – |
| narrow_skip | +6.2 | [+0.0, +17.5] |
| rollback | +33.8 | [+15.0, +52.5] |
| wide_patch | +1.2 | [+0.0, +3.8] |
| wide_skip | +18.8 | [-6.2, +42.5] |
