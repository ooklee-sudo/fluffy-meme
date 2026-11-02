# OpenRouter weekly snapshots

Weekly snapshots of OpenRouter model prices (catalogue and per-provider endpoints) and token usage,
collected for research on demand and pricing of large language models.

- `collect.py` writes `snapshots/YYYY-MM-DD/` with `models.json`, `endpoints.json`, `usage_week.json`, `usage_day.json`, `meta.json`.
- `history/rankings_weekly_2025-2026.json`: weekly usage back to January 2025 from the OpenRouter Data API (initial backfill).

Data source and licence: "Source: OpenRouter (openrouter.ai/rankings), as of {as_of}." Licensed under CC BY 4.0.
Prices are list prices at collection time; past prices before the first snapshot are not available.
