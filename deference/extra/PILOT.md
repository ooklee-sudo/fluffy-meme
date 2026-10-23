# Pilot for the post-main-run additions (2026-10-23)

Probes (one arithmetic question, `reasoning.enabled` true/false, temperature 1.0, 2,048 tokens):
- Sonnet 5.5, Gemini 3.1 Pro, Gemini 3.5 Flash: "Reasoning is mandatory for this endpoint and cannot be disabled" (400). Not usable for on/off.
- Haiku 4.5, Qwen3.5/3.6/3.7/3.8, GLM-4.7-flash, DeepSeek-V3.2: toggle works (off gives 0 reasoning tokens). Qwen3 (2504-era) and the toggle: off still emits reasoning tokens, rejected.

Pilot calls (extra_run.py run --per-cell N; fixed-shuffle prefix of each condition, so every channel mix is represented), 1,450 calls, US$3.5 billed:

| condition | n | parse fail | truncated | mean reasoning tokens | $/call |
|---|---|---|---|---|---|
| Haiku4.5 off | 150 | 0 | 0 | 0 | 0.0017 |
| Haiku4.5 on | 150 | 0 | 0 | 403 | 0.0034 |
| Gemini3.1-Pro default (reasoning forced) | 150 | 0 | 0 | 665 | 0.0083 |
| Qwen3.5-9B on | 150 | 0.91 | 0.91 | 1798 | 0.0004 |
| Qwen3.5-27B on | 150 | 0.04 | 0.09 | 1696 | 0.0044 |
| Qwen3.6-27B on | 100 | 0.10 | 0.10 | 1142 | 0.0048 |
| Qwen3.8-27B on | 100 | 0.10 | 0.10 | 734 | 0.0018 |
| Qwen3.x-27B off | 100 | 0 | 0 | 0 | ~0.0001 |

Selected: Haiku 4.5 (300-item sample), Qwen3.6-27B and Qwen3.8-27B (600 items). Truncation with reasoning on (about 10%) is
counted as missing in the primary analysis (and as an error in the sensitivity analysis); it is a property of the 2,048-token limit
that the main run also used, and is reported as such.

Projected cost of the full additions at pilot per-call prices: Haiku ~US$17, Qwen3.6 ~US$16, Qwen3.8 ~US$7, Gemini 3.1 Pro ~US$105 (total ~US$145).
