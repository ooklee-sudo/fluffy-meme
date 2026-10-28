# Pilot: are LLM agent tool errors self-exciting? (SWE-agent trajectories)

Data: nebius/SWE-agent-trajectories (Hugging Face, CC-BY-4.0), shards 0-1: 13,340 trajectories, 12,375 with >= 6 steps
(Llama-70B 11,321; Llama-8B 814; Llama-405B 240). Event = agent-side tool error in the observation after an action
(edit rejected for syntax errors, command not found, missing file/directory, usage error, interface error, timeout);
file-viewer output excluded. 22% of steps are errors; 84% of trajectories do not resolve the issue.

| Question | Result | Verdict |
|---|---|---|
| Errors cluster? | P(error after error) 0.657 vs P(error after success) 0.102; difference 0.555 against 0.434 (95% upper 0.435) when errors are permuted within each trajectory (heterogeneity only) | clustering beyond heterogeneity |
| Contagion with trajectory fixed effects | conditional logit of error on decayed past errors: beta 0.25-0.31 (SE 0.01-0.02) across decay 0.3-0.8; placebo on permuted sequences -0.33 (fixed-effect bias is negative, so the test is conservative) | supported |
| Not only edit-retry loops | non-edit errors: beta 0.32 (placebo -0.40); edit errors: 0.44 (placebo -0.39) | supported |
| Branching ratio (pooled discrete Hawkes, no heterogeneity) | 8B 2.10, 70B 1.59, 405B 1.97 | upper bounds only: heterogeneity not removed; not monotone in size |
| Early warning of final failure from first 8 steps | AUC 0.55 (error count), 0.53 (excitation) | not supported here |
| Escalation rules | count >= 3: catches 40% of failures, hands off 17% of successes; excitation >= 1.5: 37% / 18% | no advantage here |

Caveats: errors are tool-misuse events, not task failure; final failure (84%) is dominated by other causes; step index used as time;
cross-excitation model between edit and non-edit errors did not converge cleanly. Next: heterogeneity-adjusted Hawkes
(random baseline per trajectory), fault-injection experiment for causal excitation, tau-bench outcome where failures matter.

## Step 2: heterogeneity-adjusted Hawkes (`hawkes_re.py`, results in `hawkes_re_results.json`)
lambda_t = mu_i (1+t)^gamma + alpha S_t, mu_i ~ Gamma integrated out; first 60 steps; up to 1,200 trajectories per model.

| Model | Trajectories | Branching, Hawkes only | Branching, Hawkes + heterogeneity | LR test of excitation given heterogeneity (df 2) |
|---|---|---|---|---|
| Llama-8B | 814 | 1.96 | 0.49 | 568.8 |
| Llama-70B | 1,200 | 1.49 | 0.35 (bootstrap 0.29-0.48, 12 reps of 1,000) | 330.8 |
| Llama-405B | 240 | 2.12 | 0.62 | 132.8 |

Reading: ignoring heterogeneity overstates the branching ratio about fourfold; after controlling for it, excitation remains
highly significant but subcritical (an error triggers on average 0.35-0.62 further errors), so cascades die out rather than run away.
The ordering across model sizes is not monotone and the 405B sample is small. Optimisation by L-BFGS-B from one start;
for Llama-70B the full model barely improves on Hawkes-only, so local optima should be checked with multiple starts.

## Step 3: all 12 shards, multi-start estimation (`hawkes_re_results_all.json`)
80,036 trajectories (Llama-70B 74,792; 8B 4,053; 405B 1,191). Up to 3,000 trajectories per model (>= 6 steps), five starting
points per fit plus warm starts from the nested models; bootstrap: 15 resamples, warm-started at the point estimate
(this may understate the spread).

| Model | Trajectories | Branching, Hawkes only | Branching, Hawkes + heterogeneity | 95% bootstrap | LR excitation given heterogeneity | LR heterogeneity given excitation |
|---|---|---|---|---|---|---|
| Llama-8B | 3,000 | 1.85 | 0.50 | 0.44-0.56 | 2,077 | 595 |
| Llama-70B | 3,000 | 1.48 | 0.38 | 0.31-0.42 | 1,130 | 219 |
| Llama-405B | 1,140 | 2.08 | 0.56 | 0.49-0.62 | 659 | 357 |

Both contagion and heterogeneity are needed; ignoring heterogeneity overstates the branching ratio about four-fold;
all three models are subcritical; 70B is lower than 8B and 405B, so excitation is not monotone in model size.
