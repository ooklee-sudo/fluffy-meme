# Wayback check of Gemini pages (run 2026-11-04 on the author's computer)

Source: `wayback_timeline_gemini.csv` (deduplicated output of `wayback_check_standalone.py gemini`): 70 distinct snapshots of the deprecations page (from 2025-11-05), 208 of the changelog (from 2024-05-21), and 575 of the pricing page (from 2024).

## Confirmed
- Gemini 2.0 Flash and 2.0 Flash-Lite shutdown date was revised: "Earliest February 2026" (2025-11-05, 2026-01-16) → March 31, 2026 (2026-02-09) → June 1, 2026 (2026-03-11; changelog entry dated 2026-02-18). Shut down June 1, 2026 (changelog).
- Gemini 2.5 Pro and 2.5 Flash: "Earliest June 2026" (2026-01-16) → June 17, 2026 (2026-02-09) → October 16, 2026 (2026-05-18) → "No shutdown date announced" (2026-10-07). 2.5 Flash-Lite: July 22, 2026 → October 16, 2026 → no date.
- Gemini 3.5 Flash and 3.7 Flash: the deprecations page still read "No shutdown date announced" on 2026-10-07, the day before both were redirected (no advance notice).
- Gemini 3.1 Flash-Lite shutdown May 7, 2027 listed from the first snapshot after release (2026-05-18).
- Gemini 3.6 Flash introductory input price ($0.75 "through December") was in effect on 2026-09-12 and 2026-10-10 snapshots.
- Gemini 2.0 Flash input price $0.10 and 2.0 Flash-Lite $0.075/$0.30 appear on the official pricing page (2025-10-12 to 2026-06-09 snapshots).

## Changed in the data
- `gemini-2.0-flash(-001)` announce date: 2025-12-03 → 2026-02-07 (first day-level shutdown date; bracket 2026-01-16 to 2026-02-07). Notice 180 → 114 days. Gemini stable median notice unchanged (84 days); simulation results unchanged.

## Not checked
- Gemini 2.0 Flash output price ($0.40): the saved context was cut before it. Run `price_check.py` to print it from the 2026-03-11 snapshot.
- Gemini 1.0/1.5 notices (sent by email; no lifecycle page existed before mid-2025).
- OpenAI, Anthropic and Bedrock pages (not run).
