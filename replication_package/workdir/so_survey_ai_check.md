# Stack Overflow Developer Survey: tag-level AI usage? (checked 2026-10-30)

Data: StackExchange/Survey, `packages/archive/<year>` (results CSVs are Git LFS; fetched via media.githubusercontent.com). License: ODbL 1.0 (data), DbCL 1.0 (contents). The 2023 file came from the official CDN zip.

| Year | Respondents | AI question | Language question |
|---|---|---|---|
| 2023 | 89,184 | `AISelect` (uses AI tools in dev process?) | `LanguageHaveWorkedWith` |
| 2024 | 65,437 | `AISelect` | `LanguageHaveWorkedWith` |
| 2025 | 49,191 | `AISelect` (daily/weekly/monthly) | `LanguageHaveWorkedWith` |
| 2026 | 30,903 | `LanguagesUsedAI` (languages used AI for) | `LanguagesHaveWorkedWith` |

Computed `pilot/ai_share_by_language.json`: share of respondents working with a language who use AI (2023-2025, general AI use), or used AI for that language (2026).

Caveats:
- 2023-2025 measure AI use among people who work with a language, not AI use for that language. Only 2026 asks per language.
- Language-level only (no frameworks such as pandas). 8 of the top-30 tags map to a language.
- Cross-language SD of the AI share is about 6-7 pp in 2023-2025, 12.5 pp in 2026.
- Correlation of AI share with log tag decline (2022 to 2025) over the 8 matched tags: 2023 -0.65, 2024 -0.87, 2025 -0.79, 2026 -0.39. n = 8, suggestive only.
