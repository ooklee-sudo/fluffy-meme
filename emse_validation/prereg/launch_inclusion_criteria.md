# Launch inclusion criteria (freeze before collecting release data)

**Why no list is attached:** the confirmatory launches are those announced after the registration date, so the list does not exist yet. The prior study's 38 launches are not in this repository and are not used for confirmation. Log launches as they happen in `launches_log.csv` (columns in `launches_template.csv`).

## What counts as a launch
A launch is the **first public announcement of a new model** by one of the providers below, with an announcement date and a primary-source URL.

| `launch_type` | Provider | Counts |
|---|---|---|
| `openai` | OpenAI | New model available through the OpenAI API |
| `anthropic` | Anthropic | New model available through the Anthropic API |
| `google` | Google | New model available through the Gemini API |
| `open_weights` | Any | New model whose weights are publicly downloadable (any provider) |

The prior study's counts were 22 open-weights and 16 API launches (6 OpenAI, 6 Anthropic, 4 Google). Match this granularity: a new model, not a point update.

## Rules
1. **Date:** the date of the provider's public announcement (blog post, model card, or API changelog entry), in UTC. Day 0 is that date.
2. **Source:** a primary-source URL in the `source_url` column. Third-party news is not enough.
3. **Newness:** a new model or a new model version. Not counted: price changes, rate-limit changes, new endpoints for an existing model, fine-tuning features, and re-releases of the same weights in a new quantization.
4. **Open-weights threshold:** downloadable weights from the provider's official page or the Hugging Face organization page, announced on one date. A preview with gated access that is not downloadable does not count until weights are downloadable.
5. **Dates not shared:** when two launches fall within 14 days of each other, both are kept. The analysis handles this through placebo-date rules and the secondary "drop contaminated controls" analysis.
6. **Logging time:** each launch is logged within 7 days of announcement, with `logged_date`, by someone who has **not** looked at release data for the window.
7. **Freezing:** at the end of the window, copy `launches_log.csv` to `launches_frozen.csv`, record its SHA-256, and do not edit it.
8. **Disputes:** if a launch is disputed, the decision is made by a person who has not seen release data, is written in the `notes` column, and is made before freezing.
