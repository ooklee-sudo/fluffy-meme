# Data

The data files are **not included in this package yet**. Place them here before running `code/analysis.py`.

## Files that `analysis.py` reads

### `posts.csv` (191 rows, one per war-period post)

| column | description |
|---|---|
| `post_id` | identifier from the post archive |
| `human` | final human label (two coders, disagreements resolved by the third coder) |
| `model1` | first-stage label (claude-sonnet-5-5, no codebook, run 1) |
| `v2_opus`, `v2_sonnet`, `v2_haiku`, `v2_sonnet_repeat` | codebook-v2 labels |
| `v2_majority` | modal v2 label; ties broken by `v2_opus` |

Labels take the values `escalation`, `deescalation`, `mixed`, `other`.

### `events.csv` (95 rows, one per event in the common frame)

All columns of `posts.csv`, plus:

| column | description |
|---|---|
| `day` | trading day of the post (bootstrap cluster) |
| `ret30` | log return of the WTI CFD mid quote, in percent, from the last tick before the post to 30 minutes after it (unsigned; the code signs it by class: oil up for escalation, oil down for de-escalation) |

## Source material to deposit

| item | notes |
|---|---|
| Post texts | CNN archive of the president's posts; deposit post IDs and texts, or IDs plus retrieval code, per the archive's terms |
| Tick data | Dukascopy WTI CFD quotes. **Check Dukascopy's redistribution terms**; if raw ticks cannot be shared, deposit the derived `ret30` values and the download code |
| Model prompts and raw outputs | first-stage runs and the four codebook-v2 runs |
| Coder sheets | two original coders, third coder (with control items marked), codebooks v1 and v2 |
| Investigator-adjudicated labels | earlier analysis reported in the SI |
| Analysis plans | the plan files listed in SI Table S9, with commit dates |
