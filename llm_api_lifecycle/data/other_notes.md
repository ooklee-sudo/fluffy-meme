# Non-OpenAI/Gemini-API lifecycle data: method, definitions, gaps

Retrieved 2026-11-04. Status is relative to 2026-11-04. Build script: `/tmp/claude-0/-home-user-fluffy-meme/7fe68551-a26f-5204-b375-89e5b2ba9817/scratchpad/scripts/build.py`. Raw pages are in `research/raw/{ant,bed,az,vtx}` and `research/raw/bedrock_legacy.md`. Note that `research/raw/` also holds files from other runs.

## Files
- `other_lifecycle.csv`: 486 rows. Anthropic API 36, AWS Bedrock 144, Azure OpenAI 120, Azure AI Foundry (partner and non-OpenAI models) 130, Vertex AI 56.
- `anthropic_prices.csv`: 22 predecessor→successor list-price pairs (USD per 1M tokens, input/output).

## Method
1. **Anthropic API.** Source: `platform.claude.com/docs/en/about-claude/model-deprecations`. `docs.anthropic.com` now redirects there.
   - `announce_date` is the dated "Deprecation history" heading ("On <date>, Anthropic notified developers…").
   - `shutdown_date` is the retirement date.
   - `replacement` is the recommended replacement *as the page lists it today*.
   - Active models carry no shutdown date. Their notes hold the "Not sooner than" commitment.
   - Release dates:
     - Models up to Opus 4.5 use Anthropic launch announcements.
     - Claude 1.0 and Instant 1.0 use the public API launch date, 2023-03-14.
     - 2026 models use the "not sooner than" date minus one year. This matches the Bedrock model-card launch date and endoflife.date in every case.
     - Release is left blank for claude-1.1, 1.2, 1.3, instant-1.1 and claude-mythos-preview, because I could not verify those dates.
2. **AWS Bedrock.**
   - `model-lifecycle.html` now covers only models launched on or after 2026-09-07. The dated tables are on `model-lifecycle-legacy` (fetched as `.md`).
   - `announce_date` is the **Legacy date** and `shutdown_date` is the **EOL date**.
   - `release_date` is the "Model launch date" on each model card. All 138 cards were fetched from `model-cards.md`.
   - Cards with no lifecycle-table entry are included as active rows (status `none`). Their notes give the "EOL no sooner than" date and the Legacy-period length, which gives censoring information.
3. **Azure.** Two Microsoft Learn pages were used:
   - "Model retirement schedule" (current, updated 2026-09-23). It gives model, version, current lifecycle stage, retirement date and replacement.
   - "Retired Foundry Models" (updated 2026-07-28). Its Azure OpenAI table adds a "Deprecation date" column.
   - Rows are de-duplicated on (platform, model, version).
   - For Azure OpenAI and dated partner versions, `release_date` is the version string: the OpenAI snapshot date, so Azure availability may lag. The 4-digit versions 0301/0314/0613 were mapped to 2023-MM-DD.
   - Azure OpenAI rows are platform `Azure OpenAI`. All other publishers are `Azure AI Foundry`. Notes say whether a model is "sold by Azure" or a partner/Marketplace model.
4. **Vertex AI.** Source: "Model versions and lifecycle". The URL now redirects to `docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions`. It gives release date, retirement date and replacement. It has no announcement dates.
5. **Prices.**
   - Current and retired-but-listed prices come from the Anthropic pricing page.
   - Claude 3 / 3.5 / 3.7 / 2.x prices come from their launch announcements: Claude 3 Haiku $0.25/$1.25, Claude 3 Sonnet $3/$15, Claude 3 Opus $15/$75, Claude 3.5 Sonnet $3/$15, Claude 3.7 Sonnet $3/$15, Claude 2.0/2.1 $8/$24. These are well documented, but this session could not re-fetch them (Wayback Machine blocked).
   - Claude 3.5 Haiku used $1/$5 at launch (2024-11-04) and the current $0.80/$4 after the price cut. The notes say which value each row uses.
   - Two pair types (in `notes`):
     - `next_generation_same_tier`: 19 pairs, priced at the successor's launch.
     - `listed_replacement`: 3 pairs. These are deprecation-page replacements that already existed on the notice date, priced at that date.
6. **Tier.** Heuristic, from the model name: large / mid / small / specialized. "Specialized" means embedding, image, video, audio, rerank, OCR, router or safety models. Tier is blank when the name gives no positioning, for example OpenAI "Sol/Terra/Luna/Astra", DeepSeek-V4-Flash and gemini-4-argon. Use it only as a filter. It is not authoritative.

## Platform definitions (verbatim substance)
- **Anthropic.**
  - Lifecycle stages: Active → Legacy (no further updates) → Deprecated (still works; replacement and retirement date assigned) → Retired (requests fail).
  - Policy: "at least 60 days' notice before model retirement for publicly released models."
  - Active models carry a "not sooner than" date one year after release.
  - The dates apply to Anthropic-operated platforms, which include Microsoft Foundry. Bedrock and Google-managed Vertex set their own dates.
- **AWS Bedrock.** Old policy, for models launched before 2026-09-07:
  - **Legacy** = Bedrock notifies customers and announces the EOL date. The model stays in Legacy **at least 6 months** before EOL.
  - New customers are blocked, and existing customers may lose access after 15 days of inactivity. No new Provisioned Throughput.
  - For EOL dates after 2026-02-01, after 3 or more months of Legacy there is a "public extended access" period at **higher provider-set pricing**.
  - **EOL** = removed from all regions.
  - A model stays on Bedrock at least 12 months after launch.
  - New policy, for models launched on or after 2026-09-07: each model card states "EOL no sooner than" and a Legacy period of **6 months or 45 days**. Bedrock-hosted OpenAI GPT-6.1 Sol follows OpenAI's own deprecation terms.
  - Bedrock dates may differ from the provider's dates, and may differ by region.
  - Bedrock "Legacy" is therefore a good proxy for the announcement date. It is **not** the same as Anthropic's "Legacy" stage, which is a pre-deprecation stage.
- **Azure / Microsoft Foundry.**
  - Stages: Preview → GA → Legacy (optional) → Deprecated (blocked for new customers; existing subscriptions keep working) → Retired (HTTP 410).
  - Standard GA lifecycle is 18 months. The retirement date is "set programmatically at launch", and the model becomes Deprecated at 12 months.
  - Anthropic, DeepSeek, Fireworks and Mistral GA models get 12 months. Grok ≥4.7 gets a minimum of 6 months.
  - The replacement is named about 90–120 days before retirement.
  - Notice: at least 60 days for GA, at least 30 days for Preview. Fireworks pay-per-token gets 15 days.
  - Microsoft says GA models have "no separate announcement". In effect, the retirement date is known at release.
  - The API's `lifecycleStatus: "Deprecated"` means retired.
- **Vertex AI.**
  - Stable models are "available for at least 12 months after release". Retirement dates for older Gemini versions were set at exactly release + 12 months (1.5-pro-001: 2024-05-24 → 2025-05-24).
  - A separate "shorter availability periods" class exists, for example gemini-3.6-flash: 2026-07-21 → 2026-11-19.
  - No deprecation-announcement dates are published.

## Key observations (for the article)
- **The same model gets different notice on different platforms.**
  - Claude Sonnet 4: Anthropic API 2026-04-14 → 2026-06-15 (62 d). Bedrock Legacy 2026-04-14 → EOL 2026-10-14 (183 d).
  - Claude 3 Haiku: API 60 d. Bedrock 184 d in the main regions; 34–43 d in straggler regions with EOL 2026-11-13/27.
  - Opus 4.1: API 61 d (retired 2026-08-05). Bedrock 184 d (EOL 2027-01-08).
  - Sonnet 4.5: API 61 d. Bedrock 182 d.
  - Azure Foundry Claude follows Anthropic's dates (sonnet-4-5 on 2026-11-30, opus-4-1 on 2026-08-05).
- **Bedrock notice is a policy floor.** All 48 non-straggler Legacy→EOL intervals are 181–185 days. Batch events: 2026-09-30 put 26 models (Meta, Mistral, Qwen, MiniMax and others) into Legacy at once.
- **Anthropic notice by event.** There are 10 announcement events: 60, 61, 61, 62, 62, 63, 76, 114, 181 and 189 days. The event median is 62.5 d and the row median is 63 d. The longer notices (Claude 2/Sonnet 3, Opus 3, Sonnet 3.7) were in 2025. Every 2026 notice is 60–62 d, at the policy floor.
- **Azure and Vertex use a "retirement date at release" regime.** Notice ≈ lifetime, so they are not directly comparable with notice computed from an announcement.

## Gaps and caveats
- **Wayback Machine is blocked** in this environment (connection reset, and WebFetch refused). Consequences:
  - (a) Bedrock models that reached EOL before about Jan 2026 are missing. The page now keeps only recent EOLs, so Claude v1/v2/Instant, Claude 3 Opus/Sonnet main regions, Claude 3.5 Haiku, Titan Text, Llama 2/3.0, Cohere Command and Jurassic are all absent. The four Claude Sonnet 3.x rows on Bedrock are **regional straggler** rows, flagged `REGIONAL STRAGGLER` in notes. Exclude them from notice statistics.
  - (b) Anthropic replacements are the **current** listing. They were evidently rewritten as new models launched. For example, claude-2.0 → claude-opus-4-8 and claude-3-opus → claude-opus-4-8, although Opus 4.8 was released after those notices. Rows where the listed replacement post-dates the notice are flagged. A search snippet suggests the earlier page named claude-opus-4-1-20250805 for Opus 3. I did not verify that, so it is not used.
  - (c) Pre-2026 price pages could not be re-fetched.
- **Azure announcement dates are almost absent.** Only 29 rows have one:
  - the 27 legacy completion/embedding models, deprecated 2023-07-06 and retired 2024-06-14;
  - gpt-4o-realtime-preview 2024-10-01 (2025-02-25 → 2025-03-26);
  - mistral-small-2503 (deprecated 2026-10-09);
  - the 2023 group counts as one event.
  - Azure's "deprecation date" is when the model became Deprecated (blocked for new customers). That is not necessarily when customers were first told.
  - Most partner-model rows have no release date (version "1").
- **Azure GA retirement dates are scheduled by policy.** They are set at launch, not by a deprecation decision. They are marked `scheduled` with a note. Exclude them if "scheduled" should mean "announced".
- **Bedrock card anomalies.**
  - Mistral Small (ID 2402) gives launch 2025-12-16. That conflicts with the ID, so release is left blank.
  - Some cards give only a month, for example Command R "Aug 2024" and Devstral 2 "Jun 2025". Release is left blank and the month is in notes.
  - Bedrock card launch dates for Claude models are sometimes one day after Anthropic's (Sonnet 4: 2025-05-23 vs 2025-05-22).
- **Duplicate Azure rows (kept on purpose).**
  - gpt-realtime-mini (2025-10-06 and 2025-12-15) each appear twice on the schedule with different dates.
  - Llama-3.3-70B and Llama-4-Maverick appear in both the "sold by Azure" and the partner sections.
- **Vertex.** The Gemini API (AI Studio) data the paper already has is a different platform. These rows are Vertex-specific. Partner models on Vertex (Claude, Llama on Model Garden) were not collected.
- **Not collected:** Mistral La Plateforme, Cohere platform, xAI API, and Google-managed Claude on Vertex. All of them publish deprecation pages and could be added.
