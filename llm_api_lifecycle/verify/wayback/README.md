# Wayback check (run on your own computer)

The Internet Archive could not be reached from the cloud sessions used to build this dataset (see `ACCESS_FAILED.md`). Run the check from a computer that can open https://web.archive.org.

```bash
cd llm_api_lifecycle/verify/wayback
python wayback_check.py
```

The script needs Python 3.9+ and no extra packages. Expect it to run for a long time (hours): it waits 3 seconds between requests, and longer when the archive asks it to slow down. Rerunning appends to the output, so delete `wayback_timeline.csv` first for a clean run. To check one source at a time, pass a prefix: `python wayback_check.py gemini`.

Output: `wayback_timeline.csv`, one row each time the text around a model ID changes on an archived page. Columns: page, snapshot date, snapshot URL, model ID, and the surrounding text.

What to check, in order of importance for the manuscript:

1. Gemini text models: the first snapshot in which each shutdown date appears (the announcement date), whether it was later revised, and the replacement named at the time. Compare with `announce_date`, `shutdown_date` and `replacement` in `data/gemini_lifecycle.csv`.
2. Gemini pricing around 2026-10-02: whether the 3.6–3.8 Flash introductory price was in effect, and the 2.0 Flash output price (USD 0.40 per million tokens in our data, from third-party trackers).
3. Anthropic and OpenAI deprecation pages: the replacement named at the time of each announcement.

Results already verified against live official pages are in `../live/`.
