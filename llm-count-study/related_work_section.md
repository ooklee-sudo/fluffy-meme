**2. Related Work and Research Gap**

Large language models (LLMs) are increasingly proposed as inexpensive stand-ins for consumer panels. Early work suggested that GPT-based respondents can produce plausible willingness-to-pay estimates and conjoint results (Brand, Israeli, & Ngwe, 2023), and that simulated agents reproduce the qualitative pattern of classic behavioral experiments (Horton, 2023). Related studies report that LLM-generated data can track the direction of experimental treatment effects, although the magnitudes tend to be overstated (Hewitt et al., 2024). Direct elicitation of numerical ratings, however, yields response distributions that are unrealistically narrow, and recent methods address this by mapping free-text answers to rating scales through embedding similarity (Maier et al., 2025).

The narrowness of simulated responses is now well documented. Silicon samples drift toward the modal answer within demographic subgroups (Li, Li, & Qiu, 2025), and instruction-tuned models appear unable to draw independent samples from the distribution they can otherwise describe (Jang, Lee, & Kim, 2026; see also Gu et al., 2024). Prompting a model to list several candidate answers together with their probabilities partly restores diversity (Zhang et al., 2025). In operations management, LLMs often reproduce the outcome of a hypothesis test while diverging from human data in the full response distribution, with mismatched dispersion playing a central role (Zhang, Zhang, & Zhao, 2025).

Nearly all of this evidence concerns bounded, ordinal, or continuous responses such as ratings, choices, and prices. Purchase and visit counts differ in an important way. They are nonnegative integers whose variance is tied to their mean, and in marketing practice they are modeled as a Poisson process whose rate varies across customers, giving a negative binomial distribution in aggregate (Ehrenberg, 1959; Schmittlein, Morrison, & Colombo, 1987; Fader, Hardie, & Lee, 2005). For this reason, overdispersion relative to the Poisson is the empirical signature of customer heterogeneity (Cameron & Trivedi, 1990), and a simulator that compresses heterogeneity should show up first as underdispersion. These distributions also feed customer lifetime value, repeat-purchase forecasts, and budget allocation, so errors in their shape propagate directly into downstream decisions.

The studies closest to ours stop short of this question. Huang and Wang (2026) model aggregate demand as a mixture of persona-level purchase probabilities, but within a single period and without repeat counts. Sashihara et al. (2025) use the distribution of purchases per buyer as a validation metric for a simulated marketplace, without testing it against Poisson or negative binomial benchmarks. Chen (2026) compares LLM user simulators with verified payment outcomes and finds that they overstate purchase propensity among customers who ultimately do not buy, but the outcome there is a binary conversion rather than a count. Calibration frameworks such as SYN-DIGITS (Fan, Huang, & Peng, 2026) align simulated responses with human ground truth at the individual and distributional level, yet, to our reading, they do not exploit the Poisson-gamma structure that governs count data. To our knowledge, and within the scope of our search, no prior study evaluates whether LLM-generated per-customer purchase counts reproduce the dispersion, zero proportion, and tail behavior of observed count data, or examines how the way heterogeneity is injected affects that fidelity. We address this gap by comparing four elicitation designs against two public transaction datasets and by assessing whether the resulting distributions support valid inference about promotion effects.

**References**

Brand, J., Israeli, A., & Ngwe, D. (2023). *Using GPT for market research* (Harvard Business School Working Paper No. 23-062).

Cameron, A. C., & Trivedi, P. K. (1990). Regression-based tests for overdispersion in the Poisson model. *Journal of Econometrics, 46*(3), 347–364.

Chen, L. (2026). Simulated customers never walk away: Decision fidelity of LLM user simulators measured against real purchase outcomes. *arXiv:2606.20708*.

Ehrenberg, A. S. C. (1959). The pattern of consumer purchases. *Journal of the Royal Statistical Society: Series C, 8*(1), 26–41.

Fader, P. S., Hardie, B. G. S., & Lee, K. L. (2005). "Counting your customers" the easy way: An alternative to the Pareto/NBD model. *Marketing Science, 24*(2), 275–284.

Fan, G. J., Huang, C., & Peng, T. (2026). SYN-DIGITS: A synthetic control framework for calibrated digital twin simulation. *arXiv:2604.07513*.

Gu, J., Pang, L., Shen, H., & Cheng, X. (2024). Do LLMs play dice? Exploring probability distribution sampling in large language models for behavioral simulation. *arXiv:2404.09043*.

Hewitt, L., Ashokkumar, A., Ghezae, I., & Willer, R. (2024). Predicting results of social science experiments using large language models. Working paper, Stanford University.

Horton, J. J. (2023). Large language models as simulated economic agents: What can we learn from Homo silicus? *arXiv:2301.07543*.

Huang, C., & Wang, K. (2026). LLM-powered virtual population for demand simulation and pricing. *arXiv:2606.16183*.

Jang, C., Lee, D., & Kim, J. (2026). Instruction-tuned language models cannot sample from distributions they can describe. *arXiv:2607.25292*.

Li, D., Li, L., & Qiu, H. S. (2025). ChatGPT is not a man but Das Man: Representativeness and structural consistency of silicon samples generated by large language models. *arXiv:2507.02919*.

Maier, B. F., Aslak, U., Fiaschi, L., et al. (2025). LLMs reproduce human purchase intent via semantic similarity elicitation of Likert ratings. *arXiv:2510.08338*.

Sashihara, J., Fujita, Y., Nakamura, K., et al. (2025). LLM-based multi-agent system for simulating strategic and goal-oriented data marketplaces. *arXiv:2511.13233*.

Schmittlein, D. C., Morrison, D. G., & Colombo, R. (1987). Counting your customers: Who are they and what will they do next? *Management Science, 33*(1), 1–24.

Zhang, J., Yu, S., Chong, D., et al. (2025). Verbalized sampling: How to mitigate mode collapse and unlock LLM diversity. *arXiv:2510.01171*.

Zhang, R., Zhang, X., & Zhao, M. (2025). Predicting effects, missing distributions: Evaluating LLMs as human behavior simulators in operations management. *arXiv:2510.03310*.
