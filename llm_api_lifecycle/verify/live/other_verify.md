# Independent verification: Anthropic / Bedrock / OpenAI lifecycle and price data (2026-11-04)

Row-level results: `other_verify.csv` (423 checks). Primary sources were fetched on 2026-11-04. Later in the session, docs.aws.amazon.com, developers.openai.com and openai.com began refusing curl through the proxy; the Bedrock legacy table and the OpenAI changelog were read with WebFetch instead.

| dataset | match | mismatch | unverifiable |
|---|---|---|---|
| anthropic_lifecycle (36 rows x 3 fields) | 103 | 1 | 4 |
| anthropic_prices (22 pairs x 4 prices) | 84 | 0 | 4 |
| bedrock (8 Claude + 10 sampled rows x 2 dates) | 36 | 0 | 0 |
| openai (83 rows x announce/shutdown + 25 release dates) | 183 | 0 | 8 |

## Mismatches
- `claude-mythos-preview` release_date: the dataset leaves it blank. The release notes (2026-04-07) give 2026-04-07, the date it was announced as a gated, invitation-only research preview. This is a missing value, not a wrong one.

## Unverifiable
- Release dates for `claude-1.1`, `claude-1.2`, `claude-1.3` and `claude-instant-1.1` are blank in the dataset, and no primary source gives them.
- Claude 2.0 and Claude 2.1 prices ($8/$24): the Claude 2.1 post says "we are also updating our pricing" but gives no figures, and archive.org is blocked. Secondary sources say Claude 2.0 cost $11.02/$32.68 before 2023-11-21. If so, the 2.0→2.1 pair was a price cut applied at the successor's launch, not an unchanged price.
- 8 sampled OpenAI release dates (gpt-3.5-turbo-instruct, text-davinci-003, text-ada/curie/davinci-001, gpt-3.5-turbo-0301, gpt-5-chat-latest, gpt-5.4-cyber): these models are not in the changelog, or they predate it, and openai.com returns 403. Secondary sources mostly agree with the dataset. The exception is gpt-3.5-turbo-instruct, where secondary sources give either 2023-09-18/19 or 2023-09-28.

## Manuscript claims
- **"13 of 19 same-tier successors launched at an unchanged price"**: reproduces from the data. Every price except the Claude 2.x prices checks out against primary sources. The count depends on three classification choices:
  - Claude 2.0→2.1 (unverifiable, and possibly a simultaneous cut).
  - Sonnet 4.6→Sonnet 5. Sonnet 5 launched at an *introductory* $2/$10, with $3/$15 named as the standard price. Counting the standard price makes this pair unchanged, giving 14/19.
  - Haiku 4.5→5.5, whose price is tiered.
  
  The pair list also leaves out same-tier successors with unchanged prices: Fable 5→5.1 and Mythos 5→5.1, both $10/$50 per the release notes. Including both gives 15/21. The manuscript should define the pair set and state the Sonnet 5 introductory-price rule.
- **"Claude Sonnet 4: 62 days' notice on Anthropic's API vs 183 on Bedrock, both announced the same day"**: CONFIRMED. API: 2026-04-14 → 2026-06-15 (62 d). Bedrock Legacy: 2026-04-14 → EOL 2026-10-14 (183 d).
- **"Bedrock guarantees at least 6 months between Legacy and EOL for most models"**: CONFIRMED, with caveats.
  - The legacy-policy page says "at least 6 months", and the new policy says "Most models have a 6-month Legacy period" (some have 45 days).
  - 48 of the 52 Legacy rows run 181–185 days.
  - The exceptions are regional straggler rows for Claude 3 Sonnet, 3.5 Sonnet, 3.5 Sonnet v2, 3.7 Sonnet and some Claude 3 Haiku regions, at 34–43 d. These contradict the "at least 6 months" wording.
- **OpenAI median notice of about 182 days**: CONFIRMED. All 68 announce/shutdown pairs match the deprecations page. Median 182 d by row and 182 d by event (20 events).
- **"Only 2 of 68 notices under 90 days"**: CONFIRMED: gpt-5.4-cyber (20 d) and codex-mini-latest (87 d). Another 22 notices fall at 91–94 d.
- Caveat: gpt-4-0314 and gpt-4-32k-0314 also appear in the 2023-06-13 section. The dataset uses 2025-09-26 for gpt-4-0314 but 2023-06-13 for gpt-4-32k-0314, which is inconsistent. Neither choice changes the median or the under-90 count.
