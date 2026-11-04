# Gemini API successor pricing: quality-adjusted comparison

All data accessed **2026-11-04** unless stated otherwise. Blended price = (5×input + 1×output)/6, USD per 1M tokens, standard paid tier, text, ≤200k context (≤128k for 1.5). Raw downloads: `research/raw/`. Scripts: `research/scripts/`.

## Sources (short keys)

| Key | URL | Notes |
|---|---|---|
| DEP | https://ai.google.dev/gemini-api/docs/deprecations (301 → https://aistudio.google.com/docs/deprecations) | Current version. **The 2 Oct 2026 version could not be retrieved** (web.archive.org blocked from this environment). |
| PRC | https://ai.google.dev/gemini-api/docs/pricing (301 → https://aistudio.google.com/docs/pricing) | Current version. |
| CHG | https://aistudio.google.com/docs/changelog | Release notes, dated entries. |
| W35 / W36 / W37 / W38 | https://aistudio.google.com/docs/whats-new-gemini-3.5, …-3.6, …-3.7, …-3.8 | Model guides. W36 gives 3.5 Flash's price ($1.50/$9.00). |
| VTX | https://cloud.google.com/vertex-ai/generative-ai/pricing?hl=en | Vertex pricing, used to check promo prices and 3.5 Flash. |
| BLOG | https://developers.googleblog.com/en/start-building-with-the-gemini-2-0-flash-family/ | Official: 2.0 Flash "$0.10 per 1 million input tokens". |
| LLT | https://raw.githubusercontent.com/BerriAI/litellm/v1.74.0-stable/model_prices_and_context_window.json | Third-party aggregator (LiteLLM, mid-2025 tag). Prices for 2.0 Flash, 2.0 Flash-Lite and 1.5 Flash; cites ai.google.dev/pricing. |
| SW | https://simonwillison.net/2025/Feb/25/gemini-20-flash-and-flash-lite/ | Third party: 2.0 Flash-Lite $0.075 input, "same price as Gemini 1.5 Flash". Its output figure "$0.030" is a typo for $0.30. |
| OR | https://openrouter.ai/api/v1/models | Aggregator: checks the 2.5/3.x prices. 2.0 is no longer listed. |
| ARENA | https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset (`text_style_control`, `full` split, category `overall`, **snapshot 2026-10-02**) | Official Arena (LMArena) historical snapshots. Style control is the default leaderboard. |
| AA | https://artificialanalysis.ai/leaderboards/models and https://artificialanalysis.ai/models/<slug> (embedded page data) | Intelligence Index **v5.0.1** and per-benchmark scores (GPQA Diamond, HLE). |

## 1. Model list

Prices are per 1M tokens. "promo" means the introductory price valid through 31 Dec 2026, and "list" means the price from 1 Jan 2027 (PRC, W38, VTX).

| Model ID | Release (DEP/CHG) | Shutdown (DEP) | Named replacement, current DEP | Input $ | Output $ | Blended 5:1 | Price source |
|---|---|---|---|---|---|---|---|
| gemini-1.5-flash(-002) | 2024-05 (001); 2024-09-24 (002; AA date) | 2025-09-24 (LLT `deprecation_date`; no longer on DEP) | not on DEP | 0.075 | 0.30 | 0.1125 | LLT (third party), ≤128k |
| gemini-2.0-flash / -001 | 2025-02-05 | 2026-06-01 | gemini-3.6-flash (CHG of 1 Jun 2026 said "Use gemini-3.5-flash") | 0.10 | 0.40 | 0.1500 | input: BLOG (official); output: LLT (third party) |
| gemini-2.0-flash-lite / -001 | 2025-02-25 | 2026-06-01 | gemini-3.1-flash-lite | 0.075 | 0.30 | 0.1125 | LLT + SW (third party) |
| gemini-2.5-flash | 2025-06-17 | 2026-12-01 (auto-routed) | gemini-3.5-flash-lite (announced 2026-11-02, CHG) | 0.30 | 2.50 | 0.6667 | PRC |
| gemini-2.5-flash-lite | 2025-07-22 | none announced | none | 0.10 | 0.40 | 0.1500 | PRC |
| gemini-3-flash-preview | 2025-12-17 | none announced | gemini-3.6-flash | 0.50 | 3.00 | 0.9167 | PRC |
| gemini-3.1-flash-lite | 2026-05-07 | 2027-05-07 | gemini-3.5-flash-lite | 0.25 | 1.50 | 0.4583 | PRC, VTX, OR |
| gemini-3.5-flash | 2026-05-19 | N/A: deprecated 2026-10-08, endpoint auto-routes | gemini-3.6-flash | 1.50 | 9.00 | 2.7500 | W36 ("$7.50/1M versus $9.00/1M for 3.5 Flash. Input tokens remain at $1.50/1M"), VTX, OR |
| gemini-3.6-flash | 2026-07-21 | none announced | none | 0.75 promo / 1.50 list | 3.75 promo / 7.50 list | 1.25 promo / 2.50 list | PRC, VTX. At launch W36 gave 1.50/7.50. |
| gemini-3.5-flash-lite | 2026-07-21 | none announced | none | 0.30 | 2.50 | 0.6667 | PRC |
| gemini-3.7-flash | 2026-08-13 | N/A: deprecated 2026-10-08, auto-routes | gemini-3.8-flash | 0.75 promo / 1.50 list | 3.75 promo / 7.50 list | 1.25 / 2.50 | VTX, OR (removed from PRC) |
| gemini-3.8-flash | 2026-09-02 | none announced | none | 0.75 promo / 1.50 list | 3.75 promo / 7.50 list | 1.25 / 2.50 | PRC, W38 |
| *Pro (context only)* | | | | | | | |
| gemini-2.5-pro | 2025-06-17 | 2026-12-01 (auto-routed) | gemini-3.8-flash (a cross-tier replacement) | 1.25 | 10.00 | 2.7083 | PRC |
| gemini-3.1-pro-preview | 2026-02-19 | none announced | none | 2.00 | 12.00 | 3.6667 | PRC |
| gemini-4-argon | 2026-10-13 GA | none | none | 2.00 promo (to 30 Nov 2026) / 4.00 | 10.00 / 20.00 | 3.33 / 6.67 | PRC |

I left out 1.5 Pro: the only aggregator price I found (LLT: $3.50/$10.50) looks stale, because Google cut it in Oct 2024, and I could not confirm the price in effect.

## 2. Reconstructing the manuscript ratios

Script: `scripts/calc.py`.

| Manuscript ratio | Pair that reproduces it | Computed |
|---|---|---|
| 4.4 (Flash) | 2.0 Flash (0.150) → 2.5 Flash (0.667) | **4.44** |
| 4.1 (Flash) | 2.5 Flash (0.667) → 3.5 Flash (2.75) | **4.13** |
| 0.45 (Flash) | 3.5 Flash (2.75) → 3.6 Flash at **promo** price (1.25) | **0.455**. At the 2027 list price (2.50) it is 0.91. |
| 1.3 (Flash-Lite) | 2.0 Flash-Lite (0.1125) → 2.5 Flash-Lite (0.150) | **1.33**. 1.5 Flash → 2.0 Flash also gives 1.33. |
| 3.1 (Flash-Lite) | 2.5 Flash-Lite (0.150) → 3.1 Flash-Lite (0.458) | **3.06** |
| 1.5 (Flash-Lite) | 3.1 Flash-Lite (0.458) → 3.5 Flash-Lite (0.667) | **1.45** |

The table skips 3 Flash Preview (2.5F→3FP would be 1.38 and 3FP→3.5F 3.00). It also skips 3.7 and 3.8 Flash.

### The 8.3× and 4.1× claims

These are **named-replacement** ratios, not generation-to-generation ratios, so they do not contradict the table. The text should say so explicitly.

- **2.0 Flash → named replacement gemini-3.6-flash (current DEP):** 1.25 / 0.15 = **8.33×**. This uses the 3.6 Flash introductory price. At the list price that applies from 1 Jan 2027 it is **16.7×**. On the shutdown date (CHG, 1 Jun 2026) Google pointed users to gemini-3.5-flash, which gives 2.75 / 0.15 = **18.3×**. The named replacement therefore changed over time: 3.5 Flash in June, 3.6 Flash after 3.5 Flash was deprecated on 2026-10-08. I could not verify what DEP showed on 2 Oct 2026. Because the manuscript's 8.3 reproduces exactly with 3.6 Flash at the promo price, the manuscript data most likely already reflected that.
- **2.0 Flash-Lite → named gemini-3.1-flash-lite:** 0.4583 / 0.1125 = **4.07×**. This matches 4.1, and it equals the product of 1.33 × 3.06 (skipping 2.5 Flash-Lite).
- Note that the Flash-tier "4.1" in the table (2.5F→3.5F = 4.125) is a different number from the Flash-Lite named-replacement "4.1" (4.07). They round to the same value by coincidence.

### Other named replacements, for completeness

| Retiring model | Named replacement | Price ratio |
|---|---|---|
| 2.5 Flash | 3.5 Flash-Lite (cross-tier) | **1.00×** |
| 3.5 Flash | 3.6 Flash | 0.45× promo / 0.91× list |
| 3.7 Flash | 3.8 Flash | 1.00× |
| 3.1 Flash-Lite | 3.5 Flash-Lite | 1.45× |
| 3 Flash Preview | 3.6 Flash | 1.36× promo / 2.73× list |
| 2.5 Pro | 3.8 Flash (cross-tier) | 0.46× promo / 0.92× list |

## 3. Quality scores

**Artificial Analysis Intelligence Index.** The current version is **v5.0.1**: "incorporates 9 evaluations: AA-Briefcase v1.1, AutomationBench-AA, Terminal-Bench 4.0, FrontierCode 2.0, AA-Omniscience v1.1, GDP.pdf, HLE-Diamond, CritPt v2 (Hard Subset), and Terminal-Bench-Science 0.1". AA publishes the index **only for non-deprecated models**: `intelligenceIndex` is null for every model AA marks deprecated. The v5.0.1 values available are:

| Model | Variant | v5.0.1 index |
|---|---|---|
| 3.5 Flash-Lite | High | **11.66** |
| 3.8 Flash | High | **30.85** |
| 3.8 Flash | Medium | **30.08** |
| 3.8 Flash | Low | **22.55** |
| 4 Argon | High | **50.41** |
| 4 Carbon | High | 60.03 (not on the Gemini API pricing page) |

No v5.0.1 value exists for 1.5, 2.0, 2.5, 3, 3.1, 3.5, 3.6 or 3.7 models. I could not retrieve older index versions (v2–v4) consistently, so I did not use any. **The AA index cannot support this comparison.**

**Primary consistent metric used instead: Arena text score** (style control, overall, snapshot 2026-10-02, Bradley–Terry scale). It covers all generations on one scale. A difference of Δ points means the successor wins with probability 1/(1+10^(−Δ/400)). The scale is an interval scale, so "price per point" is not meaningful for it.

**Secondary metric: AA-measured GPQA Diamond accuracy** (and HLE). AA still shows these per-benchmark scores for deprecated models. They are a ratio-scale metric, so I used them for price per point.

| Model | Arena name (2026-10-02) | Arena score | Arena variant / proxy | AA GPQA Diamond (variant) | AA HLE |
|---|---|---|---|---|---|
| 1.5 Flash-002 | gemini-1.5-flash-002 | 1309.2 | – | 0.463 (Sep '24, non-reasoning) | 0.032 |
| 2.0 Flash-001 | gemini-2.0-flash-001 | 1359.9 | non-thinking | 0.623 (non-reasoning) | 0.043 |
| 2.0 Flash-Lite | gemini-2.0-flash-lite-preview-02-05 | 1353.5 | **proxy: preview**, GA -001 not listed | 0.535 (GA -001) | 0.034 |
| 2.5 Flash | gemini-2.5-flash | 1409.4 | API default (dynamic thinking) | 0.790 reasoning / 0.683 non-reasoning | 0.121 / 0.047 |
| 2.5 Flash-Lite | gemini-2.5-flash-lite-preview-06-17-thinking | 1374.9 | **proxy: preview with thinking ON**. GA default is thinking off. The 09-2025 no-thinking preview scores 1379.4. | 0.474 non-reasoning / 0.625 reasoning | 0.037 / 0.068 |
| 3 Flash Preview | gemini-3-flash | 1472.7 | default; minimal = 1458.2 | 0.898 (reasoning) | 0.366 |
| 3.1 Flash-Lite | gemini-3.1-flash-lite-preview | 1432.7 | **proxy: preview** | 0.822 (AA's "3.1 Flash-Lite" entry = preview, reasoning) | 0.172 |
| 3.5 Flash | gemini-3.5-flash-medium | 1476.1 | medium = API default; high = 1477.4 | 0.921 (Medium) | 0.413 |
| 3.6 Flash | gemini-3.6-flash-high | 1483.0 | **High only** (API default is medium) | 0.928 (High only) | 0.408 |
| 3.5 Flash-Lite | gemini-3.5-flash-lite | 1455.0 | – | 0.838 (AA "High") | 0.188 |
| 3.7 Flash | gemini-3.7-flash-high | 1487.7 | High only | 0.921 (Medium) | 0.390 |
| 3.8 Flash | gemini-3.8-flash-high | 1494.8 | High only | 0.935 (Medium) | 0.421 |
| 2.5 Pro | gemini-2.5-pro | 1445.6 | – | 0.844 | 0.225 |
| 3.1 Pro Preview | gemini-3.1-pro-preview | 1487.0 | – | 0.941 | 0.470 |
| 4 Argon | gemini-4-argon-high | 1525.2 | High | n/a | 0.571 |

## 4. Quality-adjusted pair table

- **Δ Arena** = successor score − predecessor score.
- **P(win)** = Bradley–Terry probability that the successor wins.
- **GPQA ratio** = successor GPQA / predecessor GPQA.
- **Price/GPQA-pt ratio** = price ratio ÷ GPQA ratio.
- GPQA variants: 2.0 Flash non-reasoning, 2.5 Flash reasoning, 2.5 Flash-Lite non-reasoning (its API default), 3.x Medium where available.

| Pair | Price ratio | Arena pred → succ (Δ, P(win)) | GPQA pred → succ (ratio) | Price/GPQA-pt ratio |
|---|---|---|---|---|
| 2.0 F → 2.5 F | 4.44 | 1359.9 → 1409.4 (+49, 0.57) | 0.623 → 0.790 (1.27) | **3.51** (4.06 if 2.5F non-reasoning) |
| 2.5 F → 3.5 F | 4.13 | 1409.4 → 1476.1 (+67, 0.60) | 0.790 → 0.921 (1.17) | **3.54** |
| 3.5 F → 3.6 F | 0.45 promo / 0.91 list | 1476.1 → 1483.0 (+7, 0.51) | 0.921 → 0.928 (1.01) | **0.45** promo / 0.90 list |
| 2.0 FL → 2.5 FL | 1.33 | 1353.5 → 1374.9 (+21, 0.53) | 0.535 → 0.474 (0.89) | **1.51** (1.14 if 2.5FL with thinking) |
| 2.5 FL → 3.1 FL | 3.06 | 1374.9 → 1432.7 (+58, 0.58) | 0.474 → 0.822 (1.74) | **1.76** (2.32 vs 2.5FL with thinking) |
| 3.1 FL → 3.5 FL | 1.45 | 1432.7 → 1455.0 (+22, 0.53) | 0.822 → 0.838 (1.02) | **1.43** |

### Quality-matched replacement price

At the predecessor's retirement date, this is the cheapest Gemini text model **still available** whose score is at least the predecessor's score, and its blended price relative to the predecessor's.

| Retiring model (date) | Named replacement (price ratio) | Cheapest model with Arena score ≥ predecessor | Ratio | Cheapest model with GPQA ≥ predecessor | Ratio |
|---|---|---|---|---|---|
| 2.0 Flash (2026-06-01) | 3.6 F: 8.33 promo / 16.7 list. 3.5 F per CHG on that date: 18.3 | 2.5 Flash-Lite (1374.9 ≥ 1359.9; proxy) | **1.00** | 2.5 FL with thinking (0.625 ≥ 0.623): **1.00**. At default thinking-off (0.474), the cheapest is 3.1 FL. | **3.06** |
| 2.0 Flash-Lite (2026-06-01) | 3.1 FL: 4.07 | 2.5 Flash-Lite (1374.9 ≥ 1353.5) | **1.33** | 2.5 FL with thinking (0.625 ≥ 0.535): **1.33**. Without thinking, the cheapest is 3.1 FL. | **4.07** |
| 2.5 Flash (2026-12-01) | 3.5 FL: 1.00 | 3.1 Flash-Lite (1432.7 ≥ 1409.4) | **0.69** | 3.1 FL (0.822 ≥ 0.790) | **0.69** |
| 3.5 Flash (2026-10-08) | 3.6 F: 0.45 / 0.91 | 3.6 F or 3.8 F, same price (3 Flash Preview 1472.7 < 1476.1 fails) | **0.45 promo / 0.91 list** | 3.6 F (0.928 ≥ 0.921); 3FP 0.898 fails | **0.45 / 0.91** |
| 3.7 Flash (2026-10-08) | 3.8 F: 1.00 | 3.8 F (1494.8); 3.6 F 1483.0 and 3.1 Pro Preview 1487.0 fall short of 1487.7 | **1.00** | 3.6 F (0.928 ≥ 0.921) | **1.00** |
| 3.1 Flash-Lite (2027-05-07) | 3.5 FL: 1.45 | 3.5 FL (2.5 FL fails) | **1.45** | 3.5 FL | **1.45** |
| 2.5 Pro (2026-12-01; cross-tier) | 3.8 F: 0.46 / 0.92 | 3.5 FL (1455.0 ≥ 1445.6); 3.1 FL at 1432.7 falls short | **0.25** | 3.6 / 3.8 Flash (0.928 / 0.935 ≥ 0.844); 3.5 FL is 0.838 and fails | **0.46** promo / 0.92 list |

The key takeaway: the eye-catching named-replacement ratios for 2.0 Flash (8.3× to 18.3×) and 2.0 Flash-Lite (4.1×) fall to about 1.0–1.3× when the user moves to the cheapest model that is at least as good on Arena. That model is 2.5 Flash-Lite, which was still available and has no shutdown date. On GPQA with default (non-thinking) settings, the quality-matched ratios are about 3.1× and 4.1×. The Flash-tier generational jumps (4.4×, 4.1×) are still about 3.5× per GPQA point.

## 5. Uncertainties and gaps

1. **2 Oct 2026 page state not verified.** web.archive.org is unreachable from this environment, so I could only read the current (4 Nov 2026) DEP and PRC. DEP's named replacement for 2.0 Flash changed from 3.5 Flash (CHG, 1 Jun 2026) to 3.6 Flash (current). I could not date the edit. The 3.6 Flash introductory price ($0.75/$3.75) did not exist at its 21 Jul launch (W36 lists $1.50/$7.50); its start date is undocumented. The manuscript's 0.45 and 8.3 figures both require the promo price to have been in effect on 2 Oct 2026.
2. **Promo vs list.** The 3.6, 3.7 and 3.8 Flash promo ends 31 Dec 2026. After that, 3.5F→3.6F becomes 0.91 and 2.0F→named 3.6F becomes 16.7×. The manuscript should state which one it uses.
3. **2.0 prices** come from official retired pages that I could not retrieve. 2.0 Flash input $0.10 is confirmed by the official Google blog (BLOG). 2.0 Flash output $0.40 and 2.0 Flash-Lite $0.075/$0.30 come only from third parties (LLT; SW for Flash-Lite input). I did not use Vertex prices: Vertex lists 2.0 Flash at $0.15/$0.60, which is higher than the Gemini API price.
4. **1.5 Flash** price ($0.075/$0.30, ≤128k) and shutdown date (2025-09-24) are from LLT only. 1.5 models are no longer on DEP. 1.5 Pro was omitted (no reliable price).
5. **AA Intelligence Index** v5.0.1 is unavailable for all deprecated models. It cannot be used consistently, and no number was substituted. AA's own "deprecated" flags differ from Google's: AA marks 3.6 Flash and 3.1 Flash-Lite as deprecated, although Google has not.
6. **Arena proxies.** GA 2.0 Flash-Lite, GA 2.5 Flash-Lite and GA 3.1 Flash-Lite are not on Arena, so preview checkpoints stand in for them. For 2.5 Flash-Lite, the proxy is the thinking-enabled 06-17 preview, while the GA API default is thinking off. 3.6, 3.7 and 3.8 Flash appear only as "High", while the API default is medium. Arena CIs are roughly ±4 points, so the 3.7 F vs 3.1 Pro Preview comparison (1487.7 vs 1487.0) is a tie.
7. **Thinking variants and cost.** Reasoning variants consume more output tokens. Blended list prices ignore token volume, so per-task cost differs from the list-price ratio. This matters most for 2.5 Flash-Lite with thinking, used as a "quality match".
8. **3.7 Flash** pricing comes from VTX and OR only; it has been removed from PRC.
9. **Cross-tier routing.** The 2.5 Flash → 3.5 Flash-Lite and 2.5 Pro → 3.8 Flash replacements (announced 2026-11-02) post-date the manuscript's 2 Oct data.
10. The 1.3 Flash-Lite ratio is also reproduced by 1.5 Flash → 2.0 Flash (1.33). The tier label decides which pair is meant.


## Verification note (2026-11-04)
The Gemini 2.0 Flash output price ($0.40) and 2.0 Flash-Lite prices ($0.075/$0.30) were confirmed on Google's official pricing page in the Internet Archive snapshot of 2026-03-11 (https://web.archive.org/web/20260311202101/https://ai.google.dev/gemini-api/docs/pricing).
