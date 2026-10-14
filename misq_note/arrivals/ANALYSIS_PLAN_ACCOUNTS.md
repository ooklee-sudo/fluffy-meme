# Pre-registration: dispersion and self-excitation in influence-seeking vs. ordinary accounts

Status: written BEFORE any comparison-account data were downloaded or analysed. Date: 2026-10-14.
Dependent code: `compare_models.py` (`daily_models`, NB and NB-INGARCH(1,1) fitters). It is reused unchanged.

## 1. Question
Do accounts whose holders use posts to influence others show more over-dispersed and more self-exciting posting than matched ordinary accounts?
This is NOT a claim that "influence-seeking accounts are Poisson-Gamma". Poisson-Gamma (NB) vs Poisson-lognormal was not separable in prior work (|dAIC| <= 13), so the model-form claim is dropped. The target is the size of dispersion and of self-excitation.

## 2. Hypotheses (directional, confirmatory)
- HA1: NB dispersion alpha (Var = mu + alpha mu^2) is larger in influence accounts than in matched ordinary accounts.
- HA2: In NB-INGARCH(1,1), the persistence a+b is larger in influence accounts than in matched ordinary accounts.
- HA3 (exploratory, not in the Holm family): the share of the dispersion in HA1 that remains after adding weekday and hour-of-day effects to the mean.
Holm correction over HA1 and HA2 (family of 2). Alpha = .05, one-sided in the stated direction; two-sided result also reported.

## 3. Units and groups
Unit: account-period with at least 365 consecutive calendar days and mean >= 0.5 posts/day (days in UTC; local-time robustness in 6).
- Influence group (I): accounts of heads of state or government, legislators with >= 1M followers, and listed-company CEOs/founders, who post under their own name. Own-name posting is checked from the account bio and press coverage. Corporate or staff-run accounts are excluded.
- Control group (C): accounts of ordinary users and of public figures without an influence aim (entertainers, athletes), matched below.
- The classification is fixed in a list file committed BEFORE any dispersion statistic is computed (`accounts_list.csv`, with columns account, group, source, followers, mean_daily). The classification cannot be changed after the first fit.
- Target: >= 30 accounts per group. If the available pool is smaller, the achieved n is reported and the confirmatory conclusion is limited to "estimated difference with interval", with no significance claim.

## 4. Matching
Nearest-neighbour matching without replacement on log(mean daily posts) and log(followers), with caliper 0.25 SD of each. Followers are as of the period end. Unmatched accounts are dropped and counted. Matching is done before outcomes are computed, by a script that reads only the list file.
The activity match is essential: NB alpha depends on the mean, so unmatched mean levels would confound HA1.

## 5. Estimation and tests
- Per account: Poisson, NB, NB-INGARCH(1,1) by ML as in `compare_models.py`. alpha_i from NB; persistence a_i + b_i from INGARCH.
- Accounts whose INGARCH fit does not converge or hits a bound are kept in HA1 and excluded from HA2; the number excluded is reported by group.
- Test: Wilcoxon rank-sum on the matched pair differences (signed-rank on pairs), plus a bootstrap 95% CI of the median pair difference (10,000 resamples of pairs).
- Effect size: median log(alpha_I / alpha_C) and median (a+b)_I - (a+b)_C.

## 6. Robustness (reported, not confirmatory)
1. Local-time days, and 6-hour bins for accounts with exact times.
2. Exclusion of the top 1% of days per account (burst days) to see whether alpha comes from rare bursts.
3. Posts only vs. posts + replies/retweets, where the source gives both.
4. Exclusion of the 5 largest-alpha accounts per group.
5. A mean-level check: alpha regressed on log mean, group indicator, log followers (OLS with HC3 errors).

## 7. Falsification / interpretation rules
- If alpha_I <= alpha_C and persistence_I <= persistence_C: the proposition "influence-seeking accounts differ" is not supported. The result is reported as "over-dispersion and self-excitation are common to accounts in general", and the manuscript will not describe them as features of influence-holders.
- If only one of HA1 and HA2 holds: reported as partial, without a general claim.
- If I > C, the paper says "consistent with" and does not say that the influence aim causes it. Role, audience size, staff-run posting and news-following are not separated, and this is stated as a limit.
- Posting mixed with staff-written posts, deleted posts, and incomplete scraping all bias toward the null or the alternative in unknown directions. Sources are therefore logged with completeness checks (days with zero posts for an account that otherwise posts daily, and gaps longer than 7 days, are flagged).

## 8. Data sources and feasibility
Candidate sources are public archives of tweets (e.g. archived dumps of politicians' and CEOs' tweets; Kaggle/GitHub datasets) and public datasets of ordinary-user samples. Live X/Twitter API access is not assumed.
Step 0 (before any dispersion computation): a feasibility check of how many accounts per group have >= 365 days of timestamped posts and a follower count. This step uses only counts of accounts and days, not dispersion. If n < 15 per group, the study is dropped and the null of feasibility is reported.
The existing Trump (Twitter, Truth Social) and Musk series are placed in group I and are not used to choose other accounts.

## 9. What will not be done
- No change of group labels after outcomes are seen.
- No post-hoc metric (e.g. Fano factor at another window) as a replacement confirmatory outcome.
- Results of Step 0 and of the main test are reported even when negative.
