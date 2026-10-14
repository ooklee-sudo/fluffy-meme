# Information-theoretic hypotheses — results (plan: ANALYSIS_PLAN_INFO.md; code: analysis_info.py; output: results_info.json)

Sample: hold-out/pooled hourly signal posts with a standardized impact (oil n = 112, tariffs 74, Fed 47, China 38; total 271). Outcome |z|; OLS with topic fixed effects, standard errors clustered by day. N_c = conditional compression ratio (higher = more novel), U = ln(sd of previous 24 one-bar returns / sd of previous 300).

| Hypothesis | Result | Decision (rule fixed in advance) |
|---|---|---|
| HI1 surprisal: coefficient of N_c on |z| > 0 | +0.77 (SE 0.56), one-sided p = 0.084; same sign in every topic (oil +0.65, tariffs +1.39, Fed +0.27, China +0.96); TF-IDF novelty N_t +0.52 (p = 0.073); 2022–24 replication (n = 49, daily): +0.26 (SE 0.37), p = 0.24 | **Not supported** at α = .05 (pooled p = 0.084); direction consistent, including in the replication |
| HI2 prior uncertainty: coefficient of U on |z| > 0 | +0.29 (SE 0.20), one-sided p = 0.072 | **Not supported** |
| HI3 interaction N_c × U > 0 | −0.08 (SE 1.52), p = 0.52; main effects N_c +0.81 (p = 0.075), U +0.35 (p = 0.35) | **Not supported** |
| HI4 information transfer: I(post class; return sign) larger in war than pre-war and above its permutation null in war | War: 0.00137 bits (null mean 0.00043), permutation p = 0.041 (3,380 bars; 43 DEESC, 33 ESC). Pre-war: 0.00025 bits (null 0.00020), p = 0.28 | **Supported at α = .05 (marginal)**; the quantity is tiny in absolute terms (about 0.001 bit per hour-bar), as expected when posts are rare relative to bars |
| HI5 redundancy (descriptive) | Correlation of N_c with the number of same-topic signal posts in the previous 24 h: −0.10. Only 2 of 272 posts are empty re-posts/links in this sample (N_c = 0 by construction) | Direction as expected; uninformative |

Reading. The information-theoretic variables point in the predicted direction for novelty and uncertainty, consistently across four topics and in a 2022–24 replication, but none of the three coefficients clears the pre-registered threshold. The mutual-information result for the war period is the only supported hypothesis, and its p-value is close to the threshold. The account is therefore organizing rather than confirmed. Power: with 271 posts the standard error of N_c is 0.56 against a coefficient of 0.77; effects smaller than about 1.5 in these units cannot be excluded.
