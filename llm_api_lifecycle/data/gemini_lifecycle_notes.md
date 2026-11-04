# Gemini API model lifecycle dataset: method, gaps and caveats

File: `gemini_lifecycle.csv` (103 rows, compiled 2026-11-04). Builder script: `../build_gemini.py`.

## Scope
- These are model IDs served on the Gemini Developer API (ai.google.dev, which now redirects to aistudio.google.com/docs). Vertex AI-only versions are excluded.
- The dataset is a union of three sources: (a) every row on the live deprecations page, (b) every model release or shutdown in the release-notes changelog (Dec 2023 to Nov 2026), and (c) models already dropped from the page (1.0 Pro, 1.0 Pro Vision, 1.5 Pro/Flash -001/-002, Flash-8B-001, 2.0 experimental and thinking models, 2.5-pro-exp, 2.5-flash-preview-04-17, 2.5-flash-lite-preview-06-17, the native-audio-dialog models and 2.0-flash-exp-image-generation).
- The `tier` column lets you filter rows:
  - Text LLMs are `pro`, `flash`, `flash-lite` and `flash-8b`: 40 rows, or 37 after removing aliases.
  - The other tiers are `live-audio`, `tts`, `image` (native Gemini image models), `image-gen` (Imagen), `video` (Veo/Omni), `music` (Lyria), `embedding`, `robotics`, `computer-use`, `transcribe` and `agent` (managed agents, which are not models; 5 rows).
- `notes` holds machine-parseable tags:
  - `ALIAS_OF=` marks an alias row. Drop these rows for version-level counts.
  - `ORIG_SHUTDOWN=` records the first shutdown date, where the date was later changed.
  - `FINAL_ANNOUNCE=` records the date of the binding final announcement, where it differs from the earliest documented one.
  - `REDIRECT` means the ID was rerouted to another model instead of returning 404.
  - `DEPRECATED_NO_DATE` means the model is deprecated but has no shutdown date.
- Excluded:
  - Gemma open models and `aqa`.
  - The 1.5 and 2.0 `-exp-MMDD` and `gemini-exp-11xx/1206` experimental models, whose shutdown dates were never documented.
  - The `gemini-1.5-flash-001-tuning` base model.
  - `gemini-2.5-flash-native-audio-preview-09-2025`, which is absent from all current pages and whose shutdown date is undocumented.
  - `gemini-3.1-pro-preview-customtools`.

## Method
1. **Release dates.** I used the changelog entry where one exists, because it is the first public availability on the API. Otherwise I used the deprecations page's "Release date" column. Where the two disagree, the conflict is noted in `release_source`. The page is wrong in at least these cases: 2.5-pro-preview-03-25, 2.5-flash-image-preview, 3.1-flash-tts-preview, 3.1-flash-live-preview, Imagen 4 GA and veo-3.0-generate-preview.
2. **Shutdown dates.** I used the final date on the live deprecations page, or the changelog "shut down" entry for models no longer on the page. For 1.0 and 1.5, I used Google's email dates; the changelog confirms the actual cutoff 3 to 5 days later. When a date changed, `notes` gives the original date and the final one.
3. **Announcement dates.** The earliest documented date is coded in `announce_source` with one of these prefixes:
   - `official:` means a dated Gemini API changelog entry or a developers.googleblog.com post. These rows have exact dates.
   - `email(user-reported):` means a Google deprecation email whose receipt date a developer quoted on discuss.ai.google.dev. These dates are close to exact.
   - `UPPER-BOUND third-party:` means the earliest dated third-party mention I found (forum posts that cite the deprecations page, a news article, or the hidekazu-konishi.com lifecycle calendar). The real announcement may be earlier, so notice periods computed from these rows are **lower bounds**.
   - A blank value means no documented announcement was found. The shutdown date is still known.

## Major gap: the Wayback Machine was not reachable
web.archive.org (both CDX and snapshots) is blocked by this environment's egress policy, and WebFetch cannot reach it either. As a result:
- **`announce_date_lower` is blank in every row.** I could not reconstruct any snapshot brackets.
- I did not route around the block.
- The changelog does make deprecation announcements explicit and dated from mid-2025 onward ("Deprecation announcement: … will be shut down on …"). That covers most retirements since Oct 2025 with exact official dates, so Wayback is mostly needed for the 12 rows marked UPPER-BOUND.
- To finish the job, run the CDX procedure from a machine with archive.org access, focusing on these rows:
  - 2.0-flash/-lite (when "Earliest February 2026" and then 2026-03-31 first appeared)
  - 2.5-pro/flash/flash-lite (when 2026-06-17 and 2026-07-22 first appeared, and when 2026-10-16 appeared)
  - the 2026-11-17 TTS/Live batch
  - 2.5-flash-image, gemini-embedding-001 and gemini-3.1-flash-lite (2027-05-07)
  - veo-3.1 previews, computer-use-preview and gemini-embedding-2-preview
  - when the deprecations page itself was created (some time between 2025-05-26 and 2025-11-24)

## Key substantive findings for the article
- **Before mid-2025 the Gemini API had no lifecycle page.** A forum post on 2025-05-26 states that lifecycle information "isn't currently available in the Gemini API docs". Notice for 1.0 and 1.5 came by email; Vertex AI published 1.5 retirement dates at launch, but that was Vertex-only.
- **Notice periods are short.**
  - Across all 41 official-dated announcements, the median notice is **28 days** (range 0 to 184).
  - Across 56 non-alias, non-agent models that have any announce date, the median is 35 days.
  - For text-LLM versions, the median is 114 days for stable models (n=13, several of them upper-bound) and **28 days for preview/experimental models** (n=15).
- **Redirects are retirements without a 404.**
  - 2.5-pro-preview-03-25 was silently repointed on 2025-05-06.
  - gemini-3-pro-preview was repointed to 3.1-pro-preview on 2026-03-09.
  - gemini-3.5-flash and gemini-3.7-flash were rerouted on 2026-10-08 with zero notice (3.7 Flash lived 56 days).
  - 2.5-pro and 2.5-flash will auto-route to 3.8-flash and 3.5-flash-lite on 2026-12-01, announced 2026-11-02 (29 days' notice).
- **Dates move in both directions.**
  - 2.0-flash went from "Earliest Feb 2026" to 2026-03-31 to 2026-06-01.
  - embedding-001 and gemini-embedding-exp went from 2025-08-14 to "October 2025" to 2025-10-30.
  - 2.5-flash-lite-preview-06-17 went from 2025-08-25 to 2025-11-18.
  - 2.5-pro-preview-05-06 was set for 2025-06-19, then redirected from 2025-06-26, then shut down 2025-12-02.
  - gemini-omni-flash-preview went from 2026-09-30 to 2026-10-22.
  - Several dates passed with no shutdown: 2.5-flash-lite (2026-07-22), 2.5-flash-image (2026-10-02) and gemini-embedding-001 (2026-07-14). 2.5-pro/flash were "un-deprecated" on 2026-09-18 before the December routing was set.
  - The page itself warns that listed dates are "earliest possible" dates.
- **Replacement names are rewritten after the fact.** The live page now names models that did not exist at shutdown time; for example, gemini-2.0-flash-live-001 (shut down 2025-12-09) now lists gemini-3.8-live. The CSV records the replacement named at the time (changelog or blog) where one is known, and otherwise the page's current value.

## Uncertain items
- The 1.0 Pro announcement date (2024-11-15) is the date of a news article about the email. The email's send date is unknown.
- The 1.5 email date (2025-03-13) is one developer's receipt date, posted 2025-03-19. A second user corroborates the email on 2025-03-17.
- Dates for 2.5-flash-image (orig. 2026-10-02), gemini-embedding-001 (orig. 2026-07-14) and 2.5-pro/flash (2026-10-16) come from a third-party calendar as read by a summarising fetch tool. Treat them as indicative only.
- embedding-gecko-001 has no release date (it is a PaLM-era model). gemini-3.5-live-translate-preview has only "June 2026".
- Changelog dates are the dates Google posted them. Google sometimes edits old entries; for example, the 2025-02-05 entries were once mis-dated 2024 (forum topic 64668).
