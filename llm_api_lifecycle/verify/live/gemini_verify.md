# Gemini dataset verification (2026-11-04)

Detail: `gemini_verify.csv` (246 checks). **231 match · 8 mismatch · 7 unverifiable.**

## Scope and sources
- **Lifecycle checks:** 40 text-LLM rows × 5 fields = 200 checks.
- **Sources fetched independently on 2026-11-04:**
  - aistudio.google.com/docs/{deprecations, changelog, pricing}
  - aistudio.google.com/docs/whats-new-gemini-{3.5, 3.6, 3.7, 3.8}
  - Vertex pricing and model-versions pages
  - The developers.googleblog.com and blog.google launch posts
  - The discuss.ai.google.dev topics the dataset cites
- **Arena:**
  - I checked the local `text_style_control/full-00000-of-00001.parquet` against Hugging Face's LFS oid. The sha256 `669e6c2a…4aaf` is identical.
  - I queried category `overall`, snapshot 2026-10-02, which is an exact snapshot date.
- **Not reachable:**
  - web.archive.org is blocked; one availability-API call succeeded, but snapshot fetches did not.
  - Partway through, direct curl to aistudio.google.com, HF and the forum was denied. I used WebFetch instead.

## Lifecycle: 200 checks, 194 match
Every release date and every shutdown date matches the deprecations page or the changelog. The mismatches are below.

| Model | Field | Dataset | Verified | Source |
|---|---|---|---|---|
| gemini-2.5-pro-preview-05-06 | announce_date | 2025-06-12 (forum email) | **2025-06-05**: official changelog entry says 05-06 "will be redirected to gemini-2.5-pro on June 26, 2025" | changelog |
| gemini-2.5-pro | announce_date | 2026-01-16 | **2026-11-02**: the earlier June 2026 date was withdrawn, and changelog 2026-09-18 says "not deprecated". Forum 115760 also mentions only 2.5 Flash. | changelog |
| gemini-2.5-flash | announce_date | 2026-01-16 | **2026-11-02** (same reason) | changelog |
| gemini-2.5-flash-lite | announce_date | 2026-02-07 | **blank**: the deprecations page says "not deprecated … until further notice" | deprecations |
| gemini-3.5-flash, gemini-3.7-flash | shutdown_status | retired | **redirected**: Google says the endpoint "is not shutting down" and gives shutdown as "N/A" | deprecations |

**Unverifiable:** the gemini-3.1-flash-lite announce date. The page shows 2027-05-07, but nothing dates when that first appeared.

**Third-party announce dates confirmed as cited:**
- 1.0 Pro: 2024-11-15 article.
- 1.5: email received 2025-03-13.
- 2.0 Flash: forum, 2025-12-03.
- 2.0 Flash-Lite: forum, 2026-02-07.

No official dated source exists before these, except for 2.0 Flash and 2.0 Flash-Lite. For both, the earliest official announcement is changelog 2026-02-18.

## Prices
These all match the official pages:
- 2.5 Flash, 2.5 Flash-Lite, 3.1 Flash-Lite and 3.5 Flash-Lite.
- 3.5 Flash at $1.50/$9.00, from the 3.6 guide and Vertex.
- 3.6 Flash and 3.8 Flash at $0.75/$3.75 introductory and $1.50/$7.50 from 1 Jan 2027.

The 2.0 Flash $0.10 input price is confirmed by Google's blog.

**Unverifiable:**
- 2.0 Flash output ($0.40).
- 2.0 Flash-Lite input and output ($0.075/$0.30). Official Vertex pricing shows the same $0.075/$0.30, but that is a different platform.

The official start date of the 3.6 Flash introductory price is undocumented. It launched at $1.50/$7.50, and third parties date the cut to 2026-08-13.

## Arena and quality-matched ratios
- All 15 Arena scores match the 2026-10-02 snapshot.
- All six ratios reproduce: 1.00, 1.33, 0.69, 0.45, 1.00, 1.45.
- Caveats:
  - The 1.00 and 1.33 ratios rest on the unverified 2.0 prices.
  - 0.45 needs the 3.6 Flash promo price; at list price it is 0.91.
  - The 3.7 → 3.8 result depends on 3.1 Pro Preview missing by 0.7 points, which is a statistical tie.

## Manuscript claims
1. **"Silently redirected with no notice" (3.5 and 3.7 Flash): partly refuted.**
   - Zero *advance* notice is confirmed.
   - But the redirect was not silent: Google announced it the same day (2026-10-08) in the changelog and on the deprecations page.
   - Suggested wording: "redirected without advance notice."
2. **2.0 Flash dates (Feb 2026 → 2026-03-31 → 2026-06-01): the first two steps are unverifiable from official sources.**
   - Only the final step is official (changelog 2026-02-18). The earlier two come only from forum posts.
   - The general claim that dates were revised repeatedly *is* confirmed by official sources:
     - 2.5-flash-lite-preview-06-17: Aug 25 → Nov 18.
     - embedding-exp: Aug 14 → "October 2025" → Oct 30.
     - omni-flash-preview: Sep 30 → Oct 22.
     - 2.5 Pro/Flash: "not deprecated" → routed from Dec 1.
3. **"3.6–3.8 Flash list prices will rise on 1 Jan 2027": refuted as worded.**
   - Google calls the current price *introductory* and says *standard* pricing ($1.50/$7.50, the launch list price) applies from 2027-01-01. Effective prices double, but list prices do not change.
   - 3.7 Flash is no longer offered on the Gemini API.
