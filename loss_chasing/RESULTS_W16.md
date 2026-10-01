# 16-wording study: results received from the laptop runs (Claude models, first choice, 0 injected failures, 30 episodes per cell)

Wordings: 16 independently generated per frame (wordings.json, content hash 4d25f0374b8f). Skip = narrow_skip or wide_skip.
Intervals resample wordings. Logs are on the researcher's laptop (results\w16_*.jsonl); only the printed tables are recorded here.

## Skip rate by model and turns left (all frames pooled)

| Model | 12 left | 6 left | 3 left | Notes |
|---|---|---|---|---|
| Haiku 4.5 (T=0.7, no thinking) | 0% | 0.5% (0-13.3%) | 27.2% (0-100%) | loss-gain -62.9 [-82.5,-41.9]; neutral-gain -50.4 [-74.2,-22.9]; frame/wording/interaction 52.4/9.7/37.9% |
| Haiku 4.5 + extended thinking (2,000 tokens; default sampling) | - | - | 9.7% (0-23.3%) | loss-gain -5.2 [-9.6,-1.0]; neutral-gain -6.2 [-9.8,-2.7]; 4 of 16 wordings loss>gain, 10 below; 21.6/26.5/51.9% |
| Sonnet 5.5 (default sampling, always reasons) | 0% | 0% | 0% | floor; 4,320 rows, parse failure 0.09% or 0%, 0 refusals; actions only patch / wide_patch / hold |
| Opus 5.5 (default sampling, always reasons) | 0% | 0% | 0% | floor; 4,320 rows, 0 refusals |

Action counts for the two floor logs (one file each, labelled by the researcher as the two logs pasted): only narrow_patch, wide_patch and hold ever chosen;
wide_patch rises with time pressure (up to 40 of 1,440 at 6 turns left in one, 25 of 1,440 at 3 turns left in the other).

## Goal-salience 2x2 (Haiku 4.5, 3 turns left, T=0.7, 16 wordings x 30 episodes)

Frames: neutral (quality, last result); loss (drop, unrealized loss); gain (distance to target); neutral_goal (neutral + target headline);
loss_goal (loss + target headline). "Facts line" = the line of facts below the headline; with / without the target and gap.

| Skip rate | neutral | loss | gain | neutral_goal | loss_goal |
|---|---|---|---|---|---|
| Facts line WITH target | 15.0% | 1.9% | 62.3% | 69.2% | 32.1% |
| Facts line WITHOUT target | 0.0% | 0.0% | 56.0% | 31.7% | 23.8% |

| Contrast (pp, 95% CI over wordings; wordings positive/negative) | with target | without target |
|---|---|---|
| Goal effect, neutral wording | +54.2 [+36.0,+70.2]; 13/2 | +31.7 [+14.4,+50.8]; 12/0 |
| Goal effect, loss wording | +30.2 [+13.8,+48.5]; 13/2 | +23.8 [+6.0,+46.2]; 4/0 |
| Valence without goal (loss - neutral) | -13.1 [-23.8,-4.4]; 2/11 | 0.0 |
| Valence with goal (loss_goal - neutral_goal) | -37.1 [-56.5,-15.6]; 3/12 | -7.9 [-29.0,+12.9]; 3/9 |
| Interaction | -24.0 [-44.6,-4.2]; 5/11 | -7.9 [-29.0,+12.9]; 3/9 |
| Registered contrast (loss - gain) | -60.4 [-80.8,-38.8]; 2/14 | -56.0 [-73.8,-38.7]; 0/15 |
| gain - neutral_goal | -6.9 [-27.3,+12.7]; 8/7 | +24.4 [+6.5,+41.9]; 12/4 |

Notes: neutral_goal and loss_goal contain the gain headline of the same index, so the 2x2 varies valence text, not the presence of the gain sentence.
The 2x2 and the thinking control are follow-ups run after the registered grid and are exploratory.
