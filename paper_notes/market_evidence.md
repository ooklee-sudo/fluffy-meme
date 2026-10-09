# Market evidence on LLM API pricing and public traces (from a web-search subagent, accessed 2026-10-09)

Status: gathered by a subagent that opened the pages listed; I have not re-opened them. List prices are snapshots.

## Observed price structures (relative to Standard = 1.0)
| Mechanism | Examples | Ratio |
|---|---|---|
| Time-of-day peak/off-peak | DeepSeek 2026: off-peak = half of peak, peak 01-04 and 06-10 UTC Mon-Fri (api-docs.deepseek.com/quick_start/pricing); Feb 2025: up to 50% (V3) / 75% (R1) off, 16:30-00:30 GMT (secondary source only) | 2x-4x peak/off-peak |
| Delay-tolerant (Batch, Flex) | OpenAI, Gemini, Bedrock, Anthropic, Together, Fireworks | 0.5x |
| Priority / fast | OpenAI 2x, Gemini 1.8x, Bedrock 1.75x, Anthropic fast mode (Opus) 2x | 1.75x-2x |
| Priority vs Flex | OpenAI 4x, Gemini 3.6x, Bedrock 3.5x | 3.5x-4x |
| Reserved / provisioned | Bedrock Reserved, Azure PTU, OpenAI Reserved/Scale | fixed fee per capacity |
| Rate and ramp limits, 429/503 | Anthropic, OpenAI, DeepSeek (concurrency limit) | quantity rationing, no price |

## What it supports / does not
- Supports: flat per-token pricing is not the only structure; capacity is treated as scarce and time-varying
  (Azure docs: capacity "changes throughout the day based on customer demand"); one provider prices by time of day.
- Does not support: any peak price "much higher" than off-peak (largest observed spread 3.5x-4x); no real-time surge
  pricing; priority/flex are latency classes, not clearing prices; providers lean on quantity limits.
- Unverified: DeepSeek's own 2025 announcement, Bloomberg/SCMP motive, Anthropic Priority Tier price, Azure PTU discount.

## Public traces (timestamp + token counts; none carries prices or willingness to pay)
| Dataset | Span | Size |
|---|---|---|
| Azure LLM Inference 2023 (used here) | 1 day collected | 0.3 and 0.7 MB |
| Azure LLM Inference 2024 | 10-19 May 2024 | code 692 MB, conv 1.14 GB |
| BurstGPT v2.0 | 121 and 110 days | 51 / 145 / 232 MB |
| Mooncake (Kimi) conversation | ~1 hour | 3 MB |
| Alibaba Bailian usage traces | 2 hours | 28-132 MB |
| Chutes one-year trace (arXiv 2608.13573) | 1 year, 6.1B rows | 91 GB parquet |


## Re-verified by me on 2026-10-09 (pages opened directly)
- DeepSeek pricing page: "Off-peak rates are half of the peak rates." Peak hours 01:00-04:00 and 06:00-10:00 UTC, Mon-Fri, excluding Chinese
  public holidays; weekends and holidays fully off-peak. deepseek-flash: output $1.20 peak / $0.60 off-peak; deepseek-v4-pro: $3.96 / $1.98.
  Concurrency limits 2500 / 500. No effective date on the page. In China time (UTC+8) the peak is 09:00-12:00 and 14:00-18:00: working
  hours excluding lunch - a demand-profile-based schedule.
- OpenAI pricing page: Standard 1x, Batch 0.5x, Flex 0.5x (subset), Fast (formerly priority processing, renamed 30 Jul 2026) 2x (about 1.8x for
  gpt-5-mini), and **Ultrafast 6x** for gpt-6-astra and gpt-6.1-sol only. So the Ultrafast-to-Flex spread is 12x, larger than the 3.5-4x
  I reported earlier from the subagent.
- AWS Bedrock service-tier page: Reserved / Priority / Standard / Flex; "Priority tier requests are prioritized over Standard and Flex tier requests";
  Reserved overflows to Standard; on-demand quota shared across priority/default/flex. Percent premium/discount is NOT on this page (the
  75% / 50% figures from the subagent came from the pricing page and are unverified by me).
