const { P, H1, H2, BUL, run } = require('./lib');
const { d } = require('./lib');
const discussion = [
  H1('6. Discussion'),
  H2('6.1 Implications for IS practice and research'),
  BUL('**Size capacity from a quantile, and fit the dispersion first.** The mean-load rule fails on roughly 40-50% of days in every configuration we measured. The Poisson quantile fixes this when daily counts are Poisson, but Proposition 2 and the burst experiment show that a modest day-to-day variation in demand (CV 0.3) multiplies the miss rate several-fold. Dispersion should be estimated from incident logs before the plan is fixed.'),
  BUL('**Guardrail value is an empirical, per-deployment quantity.** The layers\' standalone clearance, their dependence, their false-block cost and their latency vary strongly by layer and model, and the best cascade changes with the SLA and the cost ratio. A fixed "three layers" prescription is not supported; the method here selects the stack from measurements.'),
  BUL('**Routing is a first-order design choice.** Sending only low-entailment answers to the expensive judge cuts judge calls by roughly an order of magnitude, but it also forgoes catches among answers the classifier rated as fully supported; the measured cost of routing is shown in Section 5.1.'),
  BUL('**Governance.** Because k* converts a detector\'s precision/recall into headcount, the framework gives IT governance a common unit (units of triage capacity or dollars per day) in which to compare detectors, set the SLA and justify standing on-call capacity.'),
  H2('6.2 Limitations'),
  BUL('**Simulated arrivals.** Outcomes are measured on real model outputs, but arrival times are simulated and each arrival replays a bootstrapped example. Real users\' queries are correlated (trending topics, incidents), so real streams are likely *more* over-dispersed than the pure replay. The burst experiment bounds this effect but does not replace production data; validation on proprietary logs is the main follow-up.'),
  BUL('**Small open models and one task.** We study 0.4-1.5B-parameter models on extractive QA with unanswerable questions. Absolute hallucination rates are much higher than for frontier models, and the layers are CPU-bound; latencies on GPU or hosted APIs differ. The *method* transfers, the *numbers* do not.'),
  BUL('**Label noise.** Ground truth uses string and token-F1 matching against SQuAD gold answers, which can mark valid paraphrases as hallucinations; this affects all configurations alike but inflates the base rate.'),
  BUL('**Cost parameters are assumptions.** Only labour-to-compute ratios and the sensitivity grid are informative; dollar levels are illustrative.'),
  BUL('**Single judge and classifier.** Layer dependence and clearance were measured for one NLI model and one judge model; other choices may be more or less correlated.'),
  BUL('**Independent days.** The model treats days as exchangeable; weekly seasonality and trends are not modelled.'),
];
const conclusion = [
  H1('7. Conclusion'),
  P('Treating critical hallucinations as a counting process turns guardrail performance into a staffing and cost decision. The analysis yields three results that differ from the common practice the earlier draft followed: capacity must be sized from an over-dispersion-aware quantile; the multiplicative guardrail formula is an optimistic bound whose gap must be measured; and the cost-minimising number of layers is not fixed at three but depends on integer capacity effects, the floor on standing staff, latency and the labour-to-compute ratio. On real outputs of three open models, a classifier-plus-routed-judge cascade reduces the required capacity by an order of magnitude relative to no guardrails and by a further large margin relative to a single layer, but only at a false-block and latency cost that the earlier framework ignored. Validating the counting-process assumptions on production incident logs is the key next step.'),
];
const refs = [
  'Allal, L. B., et al. (2025). SmolLM2: When Smol goes big, data-centric training of a small language model. arXiv:2502.02737.',
  'Brown, L., Gans, N., Mandelbaum, A., Sakov, A., Shen, H., Zeltyn, S., & Zhao, L. (2005). Statistical analysis of a telephone call center: A queueing-science perspective. Journal of the American Statistical Association, 100(469), 36-50.',
  'Cameron, A. C., & Trivedi, P. K. (1998). Regression Analysis of Count Data. Cambridge University Press.',
  'Cox, D. R. (1955). Some statistical methods connected with series of events. Journal of the Royal Statistical Society, Series B, 17(2), 129-164.',
  'Esary, J. D., Proschan, F., & Walkup, D. W. (1967). Association of random variables, with applications. Annals of Mathematical Statistics, 38(5), 1466-1474.',
  'Green, L. V., Kolesar, P. J., & Whitt, W. (2007). Coping with time-varying demand when setting staffing requirements for a service system. Production and Operations Management, 16(1), 13-39.',
  'Gregor, S., & Hevner, A. R. (2013). Positioning and presenting design science research for maximum impact. MIS Quarterly, 37(2), 337-355.',
  'He, P., Gao, J., & Chen, W. (2021). DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing. arXiv:2111.09543.',
  'Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. MIS Quarterly, 28(1), 75-105.',
  'Inan, H., et al. (2023). Llama Guard: LLM-based input-output safeguard for human-AI conversations. arXiv:2312.06674.',
  'Ji, Z., et al. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), Article 248.',
  'Kingman, J. F. C. (1993). Poisson Processes. Oxford University Press.',
  'Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33.',
  'Manakul, P., Liusie, A., & Gales, M. J. F. (2023). SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models. Proceedings of EMNLP 2023.',
  'Qwen Team. (2024). Qwen2.5 technical report. arXiv:2412.15115.',
  'Rajpurkar, P., Jia, R., & Liang, P. (2018). Know what you don\'t know: Unanswerable questions for SQuAD. Proceedings of ACL 2018, 784-789.',
  'Topkis, D. M. (1978). Minimizing a submodular function on a lattice. Operations Research, 26(2), 305-321.',
  'Whitt, W. (2007). What you should know about queueing models to set staffing requirements in service systems. Naval Research Logistics, 54(5), 476-484.',
  'Zheng, L., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. Advances in Neural Information Processing Systems, 36.',
];
const references = [H1('References'), ...refs.map(r => new d.Paragraph({ children: [run(r, { size: 20 })], spacing: { after: 70 }, indent: { left: 360, hanging: 360 } }))];
module.exports = { discussion, conclusion, references };
