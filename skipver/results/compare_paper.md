# Manuscript vs balanced action order (Haiku 4.5)

## Study 2: time pressure

| Turns left | Skip, manuscript | Skip, balanced | Loss − gain, manuscript | Loss − gain, balanced | Neutral − gain, manuscript | Neutral − gain, balanced |
|---|---|---|---|---|---|---|
| 12 | 0.0% | 0.0% | – | floor | – | floor |
| 6 | 0.5% | 0.1% | -1.5 | -0.2 [-0.6, +0.0] | -1.5 | -0.2 [-0.6, +0.0] |
| 3 | 27.2% | 12.8% | -62.9 | -15.4 [-22.1, -8.3] | -50.4 | -13.1 [-20.8, -4.2] |

## Study 3: extended thinking (3 turns left)

| | Manuscript | Balanced |
|---|---|---|
| Skip, no thinking | 27.2% | 12.8% |
| Skip, thinking | 9.7% | 8.0% |
| Loss − gain, thinking | -5.2 | -7.5 [-12.1, -2.7] |
| Neutral − gain, thinking | -6.2 | -6.7 [-10.4, -2.9] |

## Study 4: goal visibility and valence

### Facts line with the target

Skip rate by frame (%):

| Frame | Manuscript | Balanced |
|---|---|---|
| neutral | 15.0 | 9.2 |
| loss | 1.9 | 7.3 |
| gain | 62.3 | 21.7 |
| neutral_goal | 69.2 | 25.4 |
| loss_goal | 32.1 | 23.3 |

| Contrast, pp | Manuscript | Balanced [95% CI] | Excludes 0 at 99.6% |
|---|---|---|---|
| Goal effect, neutral text | +54.2 | +16.2 [+8.5, +24.0] | yes |
| Goal effect, loss text | +30.2 | +16.0 [+7.5, +25.0] | yes |
| Valence without target (loss − neutral) | -13.1 | -1.9 [-7.7, +3.3] | no |
| Valence with target (loss_goal − neutral_goal) | -37.1 | -2.1 [-9.8, +5.0] | no |
| Registered contrast (loss − gain) | -60.4 | -14.4 [-22.5, -5.4] | yes |
| Gain − neutral_goal | -6.9 | -3.8 [-11.7, +3.8] | no |

### Facts line without the target

Skip rate by frame (%):

| Frame | Manuscript | Balanced |
|---|---|---|
| neutral | 0.0 | 0.0 |
| loss | 0.0 | 0.0 |
| gain | 56.0 | 16.2 |
| neutral_goal | 31.7 | 6.0 |
| loss_goal | 23.8 | 4.8 |

| Contrast, pp | Manuscript | Balanced [95% CI] | Excludes 0 at 99.6% |
|---|---|---|---|
| Goal effect, neutral text | +31.7 | +6.0 [+1.9, +11.0] | yes |
| Goal effect, loss text | +23.8 | +4.8 [+0.2, +11.2] | no |
| Valence without target (loss − neutral) | +0.0 | +0.0 [+0.0, +0.0] | no |
| Valence with target (loss_goal − neutral_goal) | -7.9 | -1.3 [-4.4, +1.7] | no |
| Registered contrast (loss − gain) | -56.0 | -16.2 [-22.1, -10.6] | yes |
| Gain − neutral_goal | +24.4 | +10.2 [+4.4, +16.5] | yes |

## Study 5: expected values shown

### Expected values shown (target in the facts line)

Skip rate by frame (%):

| Frame | Manuscript | Balanced |
|---|---|---|
| neutral | 10.2 | 6.0 |
| loss | 0.0 | 0.0 |
| gain | 25.0 | 5.8 |
| neutral_goal | 17.3 | 5.8 |
| loss_goal | 21.5 | 7.1 |

| Contrast, pp | Manuscript | Balanced [95% CI] | Excludes 0 at 99.6% |
|---|---|---|---|
| Goal effect, neutral text | +7.1 | -0.2 [-4.2, +3.8] | no |
| Goal effect, loss text | +21.5 | +7.1 [+4.0, +10.2] | yes |
| Valence without target (loss − neutral) | -10.2 | -6.0 [-9.2, -3.1] | yes |
| Valence with target (loss_goal − neutral_goal) | – | +1.3 [-2.5, +4.8] | no |
| Registered contrast (loss − gain) | -25.0 | -5.8 [-8.8, -3.1] | yes |
| Gain − neutral_goal | – | -0.0 [-3.3, +3.1] | no |

## Floor checks under balanced order (3 turns left)

- floor_bal__haiku55__bal: skip 0.0% of 1440 first choices; by first-listed action: hold 0.0%, narrow_patch 0.0%, narrow_skip 0.0%, rollback 0.0%, wide_patch 0.0%, wide_skip 0.0%
- floor_bal__sonnet55__bal: skip 0.0% of 288 first choices; by first-listed action: hold 0.0%, narrow_patch 0.0%, narrow_skip 0.0%, rollback 0.0%, wide_patch 0.0%, wide_skip 0.0%