---
title: "E-Companion to \"Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions\""
---

# E-Companion A. Simulation Settings and Assumptions

**Table A.1. Simulation Parameters**

| Parameter | Value | Remarks |
|---|---|---|
| Stimulus scale $\kappa$ | 0.16 | Set manually |
| Stimulus decay $\tau$ | 1 h | Single exponential |
| Stimulus cap $S_{\max}$ | 3.0 | Synthetic saturation |
| Base exposure probability | 0.5 | Multiplied by $(\max\{f,10\}/10)^{-\beta}$ |
| Engagement elasticity $\beta$ | 0 (base); 0–0.5 | Applied to all accounts |
| Comment visibility factor | 0.4 | Multiplies exposure probability |
| Feed capacity | 40 items | Most recent items |
| Recency weight | $\exp(-\text{age}/2\text{ h})$ | For comment and retweet targets |
| Circadian profile | 0.12 + evening Gaussian at chronotype (sd 2.2 h) + 0.45 × midday Gaussian at 12.5 h (sd 1.8 h) | Normalized to mean one |
| Emotion at each urge evaluation | excited / angry / happy / indifferent with p = .20 / .15 / .30 / .35 | Assumption |
| Relevance level | interest < 0.10: 0.25; < 0.30: 0.50; else 0.75 | Assumption |
| Network | 2,000 agents, preferential attachment, 3 follows per new agent | |
| Horizon | 18 h warm-up; 48 h after injection | Injection at 18:00 unless stated |
| Distributed seed pool | Accounts outside the top 5% by followers | Random order until budget is spent |
| Volume-matching factor | 1.77 | Alternative schedulers only |

*Rule-based urge function.* With $h$ the hour of day, $\text{leisure} = 1$ if $h \ge 19$ or $h < 1$, 0.5 if $11 \le h < 14$, and 0 otherwise; $n$ the number of feed items in the last hour on topics with interest weight $\ge 0.10$; $\ell \in \{0, 1, 2\}$ the relevance level of the latest item; $\nu = 1$ for a notification and 0 otherwise; and $e$ an emotion bonus of 0.8 (excited), 0.6 (angry), 0.4 (happy), or $-0.6$ (indifferent), the rating is $I = \text{clip}(1.0 + 1.0\cdot\text{leisure} + 0.4\cdot\min\{n, 3\} + 0.5\cdot\ell + 0.8\cdot\nu + e,\ 0,\ 5)$. For notifications $\ell$ is set to 1.

# E-Companion B. Validation of the Estimation Procedure on Synthetic Data

To check that the procedure in Section 6 recovers known parameters, we generated synthetic campaign data with the structure of an influencer-campaign dataset with timestamps: 400 authors with follower counts drawn log-uniformly between $10^5$ and $10^7$, assigned to six products, 15 posts per author over 60 days, author and product random effects, post-level noise, log-normal reply delays (median 0.8 h, log-sd 1.2), and interaction times thinned by a known daily profile with an evening peak at 21:30. Table B.1 reports the results for two true values of $\beta$.

**Table B.1. Recovery of Known Parameters on Synthetic Data (6,000 Posts)**

| True $\beta$ | PPML $\hat\beta$ [95% CI] | OLS on $\ln(1+y)$ $\hat\beta$ | Fitted evening peak | Held-out TV (flat profile) | Held-out $r$ |
|---|---|---|---|---|---|
| 0 | −0.017 [−0.096, 0.063] | 0.817 | 21.4 h | 0.068 (0.293) | 0.971 |
| 0.35 | 0.283 [0.199, 0.366] | 0.944 | 22.2 h | 0.140 (0.276) | 0.864 |

*Note.* TV = total variation distance between the fitted profile from three calibration products and the observed hourly distribution in three held-out products; the value for a flat profile is shown in parentheses. The fitted reply-delay median was 0.86 h and 0.74 h in the two cases, against a generating value of 0.8 h.

The PPML confidence interval contained the true $\beta$ in both cases, although the point estimate for $\beta = 0.35$ was somewhat low (0.28). OLS on the log-transformed count was far off in both cases (0.82 when the true $\beta$ was 0 and 0.94 when it was 0.35), because adding one to the count distorts the relation between interactions and audience size. The daily profile fitted on calibration products reproduced the held-out profile well when $\beta = 0$ ($r = 0.97$) and less well when $\beta = 0.35$ ($r = 0.86$), but in both cases far more closely than a flat profile. Two features of the real data are not represented here: the synthetic data include posts with no interactions and only accounts with $10^5$ to $10^7$ followers, so this exercise does not test the estimator under the zero truncation and account selection present in SAGraph, which Section 6 of the main text addresses with the zero-truncated model and a discussion of bias. Because the public SAGraph release lacks timestamps, only the elasticity part of the procedure could be applied to real data.
