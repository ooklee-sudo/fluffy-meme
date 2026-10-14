# Pre-registration: an information-theoretic account of platform-mediated executive speech (committed before computing the measures, 2026-10-14)

Why: simulated peer review found that the manuscript has no IS theory and that the three earlier mechanisms were ad hoc. This plan fixes the theory's measurable implications. Already seen: all hourly reactions and standardized impacts (`estd`) of the signal posts, the n24 habituation coefficient (−0.24 pooled, exploratory) and the revision results. Not yet seen: any text-novelty or uncertainty-state measure, and any mutual-information estimate.

## Theory (summary; full text in the manuscript)
A market holds a belief distribution over the state of the world (e.g., strait open/closed, tariff schedule). A post is a message; the market's belief update is KL(posterior ‖ prior). Expected update size increases with (i) the message's surprisal under the market's prior (novelty), (ii) prior uncertainty (entropy), and their interaction; redundant messages (repeats, re-posts, links) carry ~0 bits; message credibility acts as channel reliability. Impact is therefore predicted in **magnitude**, not necessarily in the sign assigned by a classifier.

## Measures (computed by `analysis_info.py`)
- **Novelty N_c (primary):** conditional compression ratio. For post x and the preceding context c (the last 30,000 characters of the account's original posts in the prior 7 days, all topics): N_c = (|zlib₉(c ⊕ x)| − |zlib₉(c)|) / |zlib₉(x)|. Higher = more novel (lower redundancy). Secondary N_t = 1 − maximum TF-IDF cosine similarity to any post in the prior 7 days.
- **Prior-uncertainty state U:** ln(sd of the previous 24 one-bar returns / sd of the previous 300 one-bar returns) in the post's primary asset (CL for oil, ES for tariffs, ZN for Fed, CNH for China). Higher = market currently more uncertain than usual.
- **Outcome:** |z| = |two-hour reaction| / sd of two-hour changes over the previous 300 bars (= |estd| from the earlier files).
- **Mutual information:** I(post class; sign of two-hour return), in bits, over all war-period bars (class ∈ {DEESC, ESC, none}; sign ∈ {up, down}); permutation p (10,000 shuffles of class labels); also over the pre-war bars of 2024-10-15 to 2026-02-27 using coded posts in that window.

## Hypotheses and decision rules (fixed now)
- **HI1 (surprisal):** coefficient of N_c on |z| > 0. Sample: pooled hold-out set `holdout_signal_posts.csv` (oil, tariffs, Fed, China; those with `estd`), OLS with topic fixed effects, SEs clustered by day, one-sided α = .05. Replication: 2022–2024 posts in `oot_signal_posts.csv` (daily reaction) with the same specification. **Supported only if** the pooled one-sided p < .05 **and** the OOT coefficient has the same sign.
- **HI2 (prior uncertainty):** coefficient of U on |z| > 0 (same sample).
- **HI3 (interaction):** coefficient of N_c × U > 0 in the model with both main effects.
- **HI4 (information transfer):** MI(post class; return sign) is larger in the war period than in pre-war bars and exceeds its permutation null in the war period (p < .05).
- **HI5 (redundancy, descriptive):** correlation between N_c and the number of same-topic signal posts in the previous 24 hours (expected negative); and mean N_c of re-posts/links versus original posts (expected lower).
Failure of a hypothesis is reported as such; the TF-IDF novelty is a robustness check, not a substitute.

## Limits stated in advance
N_c measures redundancy relative to the account's own recent posts, not relative to the market's information set; U is a volatility-based proxy for uncertainty. A positive result would not establish causality.

## Amendments
(none)
