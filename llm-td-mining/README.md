# Within-developer comparison of AI-labeled commits

Supports Table 2 of "Choosing Versus Accepting: Why Cheaper Code Is Producing Costlier Debt" (IEEE Software submission).

Projects: PrefectHQ/prefect, calcom/cal.com, n8n-io/n8n, grafana/grafana, home-assistant/core, getsentry/sentry.
Window: non-merge commits from 2025-04-01 to the clone date (early November 2026).

A commit is AI-labeled when its message has a `Co-authored-by` trailer naming Claude/Anthropic, Codex/OpenAI,
Cursor, Copilot, Devin, Gemini or Aider, or a "Generated with Claude Code" footer. Bot accounts, non-source
files, generated paths and commits adding more than 5,000 lines are excluded.

Each developer is compared with themselves: AI-labeled commits vs. their unlabeled commits made after their
first AI-labeled one, keeping developers with at least 5 of each.

```bash
# one bare clone per project, history since March 2025
git clone --bare --shallow-since=2025-03-01 https://github.com/PrefectHQ/prefect PrefectHQ_prefect.git
python mine.py PrefectHQ_prefect.git out/PrefectHQ_prefect.jsonl   # repeat per project
python analyze.py out/*.jsonl > results.json                        # Wilcoxon tests per project and pooled
python sign_tests.py                                                 # sign tests and pooled rates (run from the folder holding out/)
```

Per-commit outputs (`out/*.jsonl`) contain author emails and are not committed.
