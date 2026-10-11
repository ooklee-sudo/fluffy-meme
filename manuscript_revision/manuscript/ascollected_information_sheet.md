---
title: "Information for the AsCollected project page"
---

*This sheet collects the facts you will need to enter on the AsCollected project page for the manuscript. It is based on the work done in this project. I have not seen the AsCollected form, so check each item against its fields and instructions (AsCollected.org author instructions and the replication-package checklist linked from the journal's Code and Data Disclosure Policy). Items in brackets are for you to complete or confirm.*

# 1. Summary of what was collected

**No data were collected from human participants.** No survey, experiment, interview, or scraping of private data was carried out. The experiment in Section 5.5 of the manuscript and Online Appendix OA9 has not been run. All data in the paper are secondary data from three public sources, plus simulated data from the author's own programs (power analyses and numerical checks of the model).

# 2. Data sources

| Source | What was used | Retrieved | Terms |
|---|---|---|---|
| GH Archive (gharchive.org, hourly files `data.gharchive.org/YYYY-MM-DD-H.json.gz`) | Events of type PullRequestEvent (action closed), PullRequestReviewEvent, and PullRequestReviewCommentEvent | 11 October 2026 | Public GitHub activity logs |
| AIDev (Hugging Face `hao-li/AIDev`, tags v3 and v4/main) | v3: `pull_request`, `pr_commit_details`. v4: `pull_request`, `repository` | 11 October 2026 | CC BY 4.0 |
| CommitPackFT (Hugging Face `bigcode/commitpackft`) | Language files for Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, PHP, Kotlin, Swift, Scala, Ruby, shell | 11 October 2026 | MIT |

**GH Archive hours used.** 1 to 14 August 2025, 1 to 14 September 2025, and 15 to 28 September 2025 (336 hourly files each), and the first seven days of each month from February to July 2025 (1,008 files) for the event study; the first seven days of August and September came from the files already retrieved. Total 2,016 hourly files. Raw files were streamed and filtered on the fly; only the filtered events were stored (not redistributed).

**Downloaded or inspected but not used in any reported result.** AIDev v4 tables `pr_reviews`, `pr_review_comments`, `pr_comments`, `pr_commits`, `user`; AIDev v3 tables `human_pull_request`, `human_pr_task_type`, `pr_task_type`, `pr_reviews`, `pr_review_comments_v2`, `pr_comments`, `pr_commits`, `repository`, `user`. The v3 human pull requests carry no reviews, comments, or commits, which is why a human baseline for review was taken from GH Archive instead. One extra GH Archive file (15 September 2025, hour 14) was retrieved to test the extraction and is excluded from the analysis.

**Attempted and not possible.** Retrieving human pull-request details through the GitHub REST API was refused for repositories not attached to the working environment, so no data came from that route. An extraction of September 2026 GH Archive files was started and stopped after finding that, from about October 2025, the pull-request payload no longer contains size or author fields; the windows were therefore restricted to 2025.

# 3. Processing steps, in order

1. **Extraction** (`hour.sh`, `hour2.sh`, `hour3.sh`, `extract.py`, `extract_f.py`): each hourly file is streamed, filtered to the three event types (for the event study, to repositories in AIDev), and reduced to the fields used (repository, pull-request identifiers, author login and type, branch name, size fields, review and comment counts, timestamps, a title and the first 300 characters of the description, flags for the Claude Code signature).
2. **Classification and variables** (`analysis.py`, `panel.py`): agent-authored pull requests are identified by author account, branch prefix, or description signature; other bot accounts are dropped; variables are built as defined in Online Appendix OA5.
3. **Pull-request comparisons** (`analysis.py`, `analysis2.py`, `analysis3.py`): within-repository regressions, robustness checks, replication across windows.
4. **Self-admitted debt markers** (`satd/count_agent.py`, `satd/count_human.py`, `satd/metrics.py`, `satd/size_strat.py`, `satd/boot_fast.py`, `satd/analyze.py`): counts of marker patterns in added lines of code, from AIDev patches and from line-level diffs rebuilt from CommitPackFT file contents.
5. **Event study** (`event_study/panel.py`, `event_study/event_study.py`).
6. **Simulations and numerical checks** (no external data): `verify_model.py`, `verify_appendix.py`, `study2/power_simulation.py`, `study2/power_one_session.py`.

# 4. Analysis decisions you should disclose

These choices were made while the analysis was being developed, some after results from earlier steps had been seen. The study was **not preregistered**.

- Two observation windows were analysed first (August and early September); a third window (late September) was added to check that results replicate, and the three are reported together.
- The comparison of agent and human pull requests was run within repositories, with a size control, after a first look at raw differences (which showed large between-repository gaps).
- The "team" and "solo" repository split (three or more authors, or at most one, in a two-week window) was defined to separate repositories where review is feasible; it is a rough proxy.
- Copilot was reported separately for review outcomes after its within-repository coefficient was found to be positive, because its workflow has a human steer the agent through review comments.
- One individual user supplying 34 percent of the Codex file changes in AIDev was excluded from the comparison with the human baseline.
- The smell score (long lines, repeated lines, broad exception handlers, warning suppressions) was defined after the first marker counts had been produced; it is the author's own construction.
- The human baseline is restricted to the 14 languages and to the language and patch-size cells that both datasets contain (60.6 percent of the agent's added lines).
- The event-study outcomes (net addition, human review, refactor-titled share, merge rate, pull-request count) were all reported; no outcome was dropped. Only the first seven days of each month were sampled.
- Estimates for event times far from adoption are very imprecise and are described as such.
- Results that did not support the theory (review at the repository level, refactoring share) are reported in the paper.

# 5. Who did what

*[To complete.]* The author set the research design and directed the work. **The extraction, analysis, simulation, and checking programs were written and run by an AI assistant (Claude, from Anthropic) in a cloud coding session, at the author's direction, and the assistant also drafted the manuscript text, the Online Appendix, the cover letter, and this sheet.** Say plainly on the AsCollected page, and in the journal's AI-use statement, what the assistant did and what you reviewed and verified yourself; the journal's policy decides how this must be worded. A reader who tries to reproduce the results should be able to tell which steps you checked.

# 6. Replication package

**Contents.** The Markdown and Word sources of the manuscript and Online Appendix; all programs named in section 3; the saved outputs (`results_*.txt`) and figure files; the lists of GH Archive hours used (`hours*.txt`) and the AIDev and CommitPackFT file names.

**To add before deposit.** The exact software versions (run `pip freeze` in the environment used); a short `README` with the order of the steps and the paths the programs expect (several paths in the programs are hard-coded to a temporary directory and should be edited or parameterized); a statement of which raw files must be downloaded again from the sources above and from which dates; and the repository location and DOI [to be added]. GitHub usernames appear in the public logs but are not needed in the replication package beyond what the programs aggregate; check the journal's policy on personal data.

# 7. Points to settle before you complete the page

1. Whether the form asks about secondary data differently from primary data, and whether it expects a statement about the use of AI tools.
2. Where the AsCollected link must appear (the cover letter, the title page, and the manuscript each carry a placeholder).
3. Whether the replication package has to be uploaded at submission or can wait for acceptance.
