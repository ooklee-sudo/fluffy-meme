# OpenAI API model lifecycle dataset: method and gaps (compiled 2026-11-04)

## Files
- `openai_lifecycle.csv`: 150 rows. 132 deprecated model ids (98 retired by 2026-11-04, 34 scheduled) and 18 active GA chat/text and embedding models (`shutdown_status=none`, right-censored).
- `openai_prices.csv`: 60 predecessor-to-successor list-price pairs (USD per 1M tokens, standard tier).
- Build scripts: `/tmp/claude-0/-home-user-fluffy-meme/7fe68551-a26f-5204-b375-89e5b2ba9817/scratchpad/scripts_oa/build.py` and `prices.py`.

## Sources
1. **Deprecations.** `https://developers.openai.com/api/docs/deprecations.md`, re-retrieved 2026-11-04.
   - Since the 2 Oct snapshot, the page has a new section, "2026-10-14 GPT-4 series".
   - `announce_date` is the date in the section heading. Notice is `shutdown_date - announce_date`.
2. **Release dates.** Searched in this order:
   - (a) the API changelog, `developers.openai.com/api/docs/changelog.md`, which covers Oct 2023 to Oct 2026;
   - (b) OpenAI launch blog posts, for pre-changelog models;
   - (c) dated snapshot names;
   - (d) secondary sources, used only where flagged.
   - `release_source` names the basis of each date. "changelog X + snapshot name" means the two agree. "snapshot name only" means the date is unverified.
3. **Active models.** Taken from the models catalogue (`/api/docs/models/all.md`) and dated from the changelog.
4. **Prices.** Taken from:
   - the current pricing page (`/api/docs/pricing.md`);
   - prices printed on the deprecations page;
   - the changelog's price announcements;
   - historical launch list prices that are well documented.
   - The Wayback Machine could not be reached from this environment, so no historical pricing-page snapshots were used.

## Coding rules
- **One row per model id.**
  - When a row names both an alias and a snapshot (for example `gpt-5 | gpt-5-2025-08-07`), the row uses the snapshot id and puts the alias in `notes`.
  - Fine-tuning-only items are excluded: training shutdowns, `/v1/fine-tunes`, and the self-serve fine-tuning wind-down.
  - Endpoints and products are excluded: Assistants, Realtime beta, Evals, Agent Builder, prompts, `/v1/edits`, `/v1/engines`, and the Videos API. These are the main reason this count differs from the earlier 96-record count.
- **Category** is the `cat=` prefix in `notes`, for example chat-text, text-completion, embedding, audio, image, video or moderation.
  - Chat variants such as `*-chat-latest`, Codex, deep-research, search and computer-use models are tagged chat-text with tier=other.
- **Duplicates were resolved as follows:**
  - `gpt-4-0314`: the announce date is 2025-09-26. It had been marked "legacy" on 2023-06-13; use that date in a sensitivity analysis.
  - `gpt-4-32k-0314`: the announce date is 2023-06-13. It was re-listed on 2024-06-06.
  - `code-davinci-002`: uses the 2023-03-20 notice (3-day shutdown). It also appears under the 2023-07-06 notice with a 2024-01-04 shutdown.
- **Four "family" rows** from the 2026-07-20 notice (`gpt-4o-audio`, `gpt-4o-realtime`, `gpt-4o-mini-audio`, `gpt-4o-mini-realtime`) are labels, not model ids. Their snapshots already shut down on 2026-05-07. Release date is left blank, and they should be excluded from survival analysis.

## Headline figures
These cover retired rows that have a release date.

| Group | n | Median lifetime (release to shutdown) | Notes |
|---|---|---|---|
| All retired rows | 95 | 590 days | IQR 392–709; range 137–1302 |
| Chat/text, excluding ChatGPT/Codex/restricted variants | 41 | 707 days | |
| All chat/text and completion | 54 | 560 days | |

Median notice is 182 days across all 132 deprecated rows, and also 182 days for retired rows only.

## Caveats and gaps
- **Replacements were revised after the fact.**
  - The deprecations page is edited retroactively. Many replacements did not exist when the deprecation was announced:
    - GPT-5.6 replacements are shown for the 2025-09-26, 2026-04-22, 2026-05-08 and 2026-06-11 notices, but GPT-5.6 launched on 2026-07-09.
    - `text-embedding-3-small` is shown for 2023 embeddings, but it launched in Jan 2024.
    - `gpt-4o` is shown for the 2023 edit and Codex models.
    - `gpt-realtime-1.5` is shown for models that shut down in 2025.
  - An OpenAI staff forum post of 2026-04-22 confirms that notice's date and model list, but it named no replacements.
  - `replacement` should therefore be read as "current recommended replacement", not the contemporaneous one.
- **Release-date uncertainty.**
  - Snapshot names can predate actual release:
    - `gpt-4o-audio-preview-2024-10-01` was released 2024-10-17.
    - `gpt-3.5-turbo-0125` was released 2024-02-01.
    - The deep-research `-2025-06-26` snapshots have a changelog entry dated Jun 24.
  - These dates are approximate:
    - `gpt-3.5-turbo-instruct` (2023-09-18, from secondary sources);
    - `gpt-4o-transcribe-diarize` (2025-10-16, from the SDK release);
    - the InstructGPT `*-001` models (2022-01-27 is when they became the default; beta access was earlier);
    - moderation aliases (the 2022-08-10 endpoint launch);
    - `gpt-5.4-cyber` (2026-04-14, press reports; restricted access, not GA).
  - `gpt-4-1106-vision-preview` is dated from its snapshot name only.
  - Missing release dates: `text-moderation-007`, `code-davinci-002`, `code-cushman-002`, and the four family rows.
- **Early "release" means limited availability.** This applies to GPT-3 base models (private beta 2020), Codex (beta 2021), `gpt-4-0314` and `-32k` (waitlist), `o1` and `o1-preview` (tier 5). See `stage_at_release`.
- **Conflicts with the page.**
  - A forum user reported that `gpt-4-1106-preview` was already unavailable on 2026-03-26. The page says 2026-10-23.
  - `gpt-4o-mini-tts-2025-03-20` was briefly slated for 2026-07-23, then reinstated. It is now scheduled for 2027-01-06.
  - The Daybreak Red/Blue aliases are marked "Deprecated" in the model catalogue but do not appear on the deprecations page. They are not included.
- **Notice periods are as published.** They do not account for access restrictions placed before shutdown, for example "only existing users from 2024-06-17".
- **Active list scope.** It covers GA chat/text models and embeddings. Restricted models (`gpt-5.6-cyber`, `gpt-5.5-cyber`, Rosalind) are excluded, as are `chat-latest` (a ChatGPT pointer), `gpt-5-search-api`, `omni-moderation`, gpt-oss (open weights) and audio/image models.

## Prices
- There are 60 pairs, covering text/chat models only.
- **Price date.** Predecessor prices are list prices at announcement. Successor prices are at announcement, or at the successor's launch when the successor came later.
- **GPT-5.6 launch prices** (Sol $5/$30, Terra $2.50/$15, Luna $1/$6) are back-calculated. The changelog gives the cut percentages (Luna −80% and Terra −20% on 2026-07-30; Sol to $4/$20 on 2026-08-21), and the results match a community-forum price table. Each row's notes give the price in effect at shutdown.
- **Excluded pairs:**
  - the 2025-09-26 batch, where the GPT-5.6 replacement was named more than 9 months later;
  - embeddings, where the named replacement postdates the shutdown;
  - pro-mode successors, which have no separate list price;
  - audio, image and video models.
- **`gpt-3.5-turbo-0301`:** the page shows $15/$20, which conflicts with the historical $2/$2. The CSV uses the historical price.
- **Successor cost.** The median successor/predecessor ratio is 0.78 for input price and 1.0 for output price. In 26 of 60 pairs the successor is dearer on input or output; most of these are 2026 moves to GPT-5.6 Sol/Terra at launch prices.
