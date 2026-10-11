# Preliminary empirical evidence from public data

This is a first test of two propositions that the paper's current design (Section 5, Study 1) would test on archival data. It is a draft for the authors to check, not a finished result.

## Data and design

**Source.** GH Archive, 1–14 September 2025 (336 hourly files). I kept three event types: pull requests closed in the window, pull-request reviews, and inline review comments. I did not use later months because GH Archive payloads from about October 2025 no longer carry PR size or author fields.

**Samples.**
- PRs created and closed in the window: **140,613 agent-authored PRs** and **807,735 human-authored PRs**. Bot accounts other than the coding agents are excluded.
- The within-repository comparison uses the **5,106 repositories** that have both kinds of PR: **45,922 agent PRs and 32,058 human PRs**.
- Agents are identified by account name or branch prefix (Copilot, Jules, Devin, Cursor, Codex) or by the signature in the PR body (Claude Code). Agent PR counts: Codex 102,870; Copilot 16,802; Claude Code 8,929; Cursor 7,982; Jules 3,360; Devin 670.

**Measures.**
- *Review:* whether anyone other than the author and not a bot reviewed or commented, and the number of such inline comments.
- *Net addition:* log((additions+1)/(deletions+1)) per PR.
- *Size:* additions + deletions.

**Estimation.** Linear regressions with repository fixed effects (demeaned within repository). Standard errors are clustered by repository. Size is controlled by log lines changed. Robustness checks add task-type indicators from PR titles, drop Copilot, and split repositories into solo and team.

The same data cannot test P1–P4, P6, P8, or Results 3–8. None of these needs a variable that archive data supplies (static-analysis warnings, defect-fix times, interface settings).

## Results

### P5 — LLM-assisted changes add more relative to what they delete

**Supported, and robust.**

| Specification | Agent effect on log(add/del) | SE |
|---|---|---|
| Within-repo, size control | **+0.633** (×1.88) | 0.035 |
| + task-type controls | +0.533 | 0.037 |
| Excluding refactor-titled PRs | +0.648 | 0.038 |
| Solo repositories (≤1 author) | +0.691 | 0.040 |
| Team repositories (≥3 authors) | +0.432 | 0.073 |

Every individual agent has a positive effect, significant for five of six: Copilot (+1.10), Codex (+0.62), Cursor (+0.70), Claude Code (+0.37) and Jules (+0.23, p = 0.03). Devin is positive but not significant (+0.27, p = 0.29), with only 670 PRs. Median additions/deletions are 50/8 for agent PRs and 37/9 for human PRs.

**Link to Table 2.** The paper says rational acceleration predicts *no* net-addition bias in single-contributor code, while the behavioral theory predicts one. The bias is present, and larger, in solo repositories. This favors the behavioral account over the rebound explanation.

**Caveats.**
- The bias is not unique to a loss-aversion mechanism. The same pattern follows if models simply generate more code per task, which is what Zhu et al. report.
- My solo/team split is a crude proxy, counting distinct authors over two weeks.
- The pooled share of deleted lines goes the *opposite* way (agent 0.544 vs human 0.232), because a few very large deletion PRs dominate the sum. I report the per-PR log ratio, which is not dominated by outliers.

### P7 — LLM-authored PRs receive less review

**Not supported in the pooled data. Partly supported in one subsample.**

| Specification | Agent effect | SE | p |
|---|---|---|---|
| Raw gap in P(any human review): human 11.7% vs agent 3.1% | descriptive | | |
| Within-repo, P(any human review) | **+0.040** | 0.007 | <0.001 |
| …excluding Copilot | +0.001 | 0.009 | 0.93 |
| Team repositories, excluding Copilot | **−0.067** | 0.018 | <0.001 |
| Within-repo, log(1+inline comments) | +0.023 | 0.002 | <0.001 |
| Agent × log size, log(1+inline) | −0.0085 | 0.0009 | <0.001 |
| Team repositories, log(1+inline), agent × size | −0.004 | 0.005 | 0.44 |

How to read this:
- **The raw gap is across repositories, not within them.** In the 50 busiest repositories, human PRs are reviewed 23.5% of the time and agent PRs 0.4%. Within the same repository the sign flips. Agent PRs are concentrated in solo and self-merge settings, where nobody reviews.
- **The positive within-repo effect comes from Copilot.** Copilot's workflow has the human steer the agent through review comments, so those comments measure iteration, not scrutiny. Excluding Copilot removes the effect.
- **Team repositories are where P7 is testable.** There, agent PRs are less likely to be reviewed at all (−6.7 percentage points), which is what P7 predicts. But the number of inline comments does not differ, and the size gradient is not significant.
- The agent × size interaction is negative in the full sample, which is the direction of the paper's "gap widens with size". It is not significant in team repositories, and for large PRs (≥500 lines) the agent effect on comments is positive.

**Net.** The data do not establish P7. They are consistent with it only in repositories where review is feasible, and only for the presence of any review.

## Limits

1. **Not causal.** Within-repo comparison removes repository characteristics, not task difficulty or developer differences.
2. **Measurement.**
   - Agent identification is imperfect. Unlabelled AI-assisted human PRs contaminate the human group, which biases effects toward zero.
   - Archive data supply PR-level size and review counts, not code quality or technical debt.
   - The solo/team split is a proxy.
3. **One two-week window**, September 2025, restricted to PRs that closed within it.
4. **Selection into agent use** is not modelled. Developers who run agents in solo repositories may differ in ways that matter.
5. **What this does and does not show.** P5 is a robust descriptive regularity that the behavioral theory predicts and the rival theory, in its solo-repo form, does not. It is not evidence that the proposed mechanism (loss aversion over a possessed artifact) produces it.

## What would strengthen this for a journal submission

- Run the same pipeline over a longer period and the AIDev dataset (agent PRs with comments and commit details) to check stability.
- Add outcomes the theory needs and archive data lack: static-analysis warnings introduced (P4), self-admitted-debt markers (TODO/FIXME) in added lines, and time to fix defects (P6).
- Treat Copilot separately, since its human-in-the-loop review is part of the product design.
- Report the P5 result against the rebound account explicitly in the text, since solo-repo evidence is where the two theories differ.
