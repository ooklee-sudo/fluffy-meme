# P4 pilot test on Aider-AI/aider (exploratory)

Proposition P4: for a given amount of statically detected debt introduced by a change, LLM-assisted
changes carry fewer self-admitted technical debt (SATD) markers. Rational acceleration predicts no difference.

## Data and measures
- Repo: Aider-AI/aider, full history (13,138 commits, to 2026-05-22). Non-merge commits touching *.py: 7,965.
- LLM-authored = commit **author** name contains "(aider)" (the committer field is NOT usable: aider tags the
  committer on human-authored commits too). Tag exists only from 2024-06-18, so the window starts there; no
  "(aider)" commits appear after 2025-Q2.
- Sample: 4,936 commits with >=1 added .py line (2,135 human-authored, 2,801 LLM-authored); Paul Gauthier authors
  4,707 of them, so most contrasts are within one developer.
- SATD: added comment lines matching TODO|FIXME|HACK|XXX|KLUDGE|WORKAROUND (strict, 30 events) or a broader list
  adding "for now", "temporary", "quick fix", "ugly", "refactor later", etc. (broad, 121 events).
- Detected debt introduced: increase in ruff warnings (C901, PLR0911/12/13/15, PLR2004, SIM, ERA001, B; noqa
  ignored; mccabe max 10) between parent and commit versions of changed files, positive part, summed per commit.

## Results (Poisson, controls: debt, log added lines, quarter FE; SE clustered by month)
| Spec | Strict SATD IRR (LLM vs human) | Broad SATD IRR |
|---|---|---|
| All authors | 0.02 [0.00, 0.13] | 0.28 [0.14, 0.56] |
| Paul Gauthier only | 0.02 [0.00, 0.12] | 0.27 [0.14, 0.52] |
| + control for added comment lines | 0.02 [0.00, 0.12] | 0.32 [0.17, 0.60] |
| Excluding test/benchmark-only commits | 0.03 [0.01, 0.19] | 0.33 [0.16, 0.68] |

Crude rate per 1,000 added lines: strict 1.24 (human) vs 0.03 (LLM); broad 4.02 vs 0.78.
Added comment lines per added line: 0.069 (human) vs 0.088 (LLM), so the gap is not due to fewer comments.
Share of commits introducing new warnings is similar (7.6% vs 7.5%).

## Caveats
Single repository and a single dominant maintainer; the tool's own prompts/conventions may discourage TODO
comments; selection of tasks into LLM edits is not random; ruff warnings are a proxy; strict SATD events are few;
not preregistered. An earlier version classified LLM commits using the committer field and was wrong; corrected.

## Reproduce
bare-clone Aider-AI/aider to /home/user/aider-ai/aider.git, run extract3.py (commits3.json), lint.py (blobs), run
ruff over blobs/ (see command in the report) to build blobcounts.json, then analyze3.py.
