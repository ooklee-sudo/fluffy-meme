# Literature search: robustness of screens for machine-written scholarly text

Search date: 2026-10-26. Searcher: Claude (automated, web tools only). Repository not modified.

## (a) Protocol and query log

**Sources searched.** General web search (Google Scholar-style; the search tool returns arXiv, ACL Anthology, PMLR/ICLR/NeurIPS/AAAI proceedings, publisher pages, PMC, Semantic Scholar-style aggregators), then direct page fetches of arXiv abstract pages, ACL Anthology entries, AAAI OJS, PMC and publisher pages for verification. Window: 2019 to Oct 2026. Mode "standard" for all queries; "extended" used once (query 51, the pre-emption check on artifact-controlled robustness audits). Semantic Scholar and Google Scholar were not queried directly (not reachable as such); their role was covered by the general search tool. Nature portfolio and Cell Press (Patterns, Cell Reports Physical Science) pages: Nature article page redirected to an authentication wall and Cell.com returned 403, so those entries were verified through PMC, arXiv, the author-hosted PDF title page via search display, or search-result display (flagged in the status column).

**Inclusion rule.** Directly relevant to detection robustness, evaluation, benchmarks, attacks, dataset artifacts/shortcuts, scientific-text or peer-review detection, feature-based detection, watermark robustness, LLM-judge self-recognition, or prevalence measurement. Excluded: pure generation-quality papers, vendor blogs and news coverage, items whose author list/venue could not be confirmed.

**Verification rule.** VERIFIED = title, authors, venue and year confirmed on a primary page opened with WebFetch (arXiv abs, ACL Anthology, AAAI OJS, PMC), or, where stated in the notes, venue taken from a proceedings page displayed in a search result. UNVERIFIED = not used for any included entry (see notes where partially verified).

Relevant hits = results that were relevant papers (counted from the result list of each query, including repeats of papers found earlier).

| # | Theme | Query string | Source | Relevant hits |
|---|---|---|---|---|
| 1 | 1 | DetectGPT zero-shot machine-generated text detection probability curvature | web/arXiv/PMLR | 3 |
| 2 | 1 | Fast-DetectGPT conditional probability curvature efficient zero-shot detection | web/arXiv/ICLR | 3 |
| 3 | 1 | Binoculars zero-shot detection of LLM-generated text | web/arXiv/ICML | 3 |
| 4 | 1 | GLTR statistical detection and visualization of generated text | web/ACL Anthology | 3 |
| 5 | 3 | Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense DIPPER | web/arXiv/NeurIPS | 3 |
| 6 | 4 | RAID shared benchmark for robust evaluation of machine-generated text detectors | web/ACL Anthology | 3 |
| 7 | 4 | MAGE Testbed deepfake text detection in the wild | web/ACL Anthology | 3 |
| 8 | 4 | M4 multi-generator multi-domain multi-lingual black-box machine-generated text detection | web/ACL Anthology | 3 |
| 9 | 4 | HC3 How close is ChatGPT to human experts comparison corpus evaluation detection | web/arXiv | 2 |
| 10 | 4 | MGTBench benchmarking machine-generated text detection | web/arXiv | 2 |
| 11 | 4 | DetectRL benchmarking LLM-generated text detection in real-world scenarios | web/arXiv/NeurIPS | 3 |
| 12 | 3 | Can AI-generated text be reliably detected? Sadasivan | web/arXiv/TMLR | 2 |
| 13 | 8 | GPT detectors are biased against non-native English writers | web/arXiv/Patterns | 2 |
| 14 | 9 | A watermark for large language models Kirchenbauer | web/PMLR | 2 |
| 15 | 9 | On the reliability of watermarks for large language models | web/arXiv/ICLR | 2 |
| 16 | 12 | Mapping the increasing use of LLMs in scientific papers Liang | web/arXiv/Nat Hum Behav | 4 |
| 17 | 12 | Monitoring AI-modified content at scale ... peer reviews Liang ICML 2024 | web/PMLR | 2 |
| 18 | 12 | Delving into ChatGPT usage in academic writing through excess vocabulary Kobak | web/arXiv | 2 |
| 19 | 5 | detecting machine-generated scientific abstracts ChatGPT classifier journal | web/PMC/ACL | 3 |
| 20 | 5 | Desaire distinguishing academic science writing from humans or ChatGPT with over 99% accuracy | web/PMC | 1 |
| 21 | 5 | detecting LLM-generated peer reviews benchmark detection | web/arXiv | 3 |
| 22 | 5 | tortured phrases paper mills problematic paper screener detection | web | 0 (only web pages; no primary paper verified) |
| 23 | 5 | machine-generated scientific text detection SCIgen detecting automatically generated papers | web/arXiv | 2 (not included; not verified) |
| 24 | 11 | Release strategies and the social impacts of language models detection GPT-2 Solaiman | web/arXiv | 1 |
| 25 | 7 | shortcut learning artifacts machine-generated text detection datasets spurious features | web/arXiv | 3 |
| 26 | 7 | AI-generated text detectors dataset bias formatting length confound detector exploit superficial cues | web/arXiv | 3 |
| 27 | 6 | stylometric linguistic features detecting ChatGPT generated text explainable detection | web/arXiv | 2 (not included; not verified) |
| 28 | 10 | LLM-as-a-judge detect AI-generated text self-preference bias LLM evaluators recognize own generations | web/NeurIPS | 1 |
| 29 | 11 | A survey on LLM-generated text detection: necessity, methods, and future directions | web/ACL Anthology | 1 |
| 30 | 2 | Automatic detection of generated text is easiest when humans are fooled Ippolito | web/ACL Anthology | 2 |
| 31 | 2 | Defending against neural fake news Grover | web/arXiv/NeurIPS | 1 |
| 32 | 2 | Authorship attribution for neural text generation Uchendu Turing test | web/ACL Anthology | 2 |
| 33 | 6,7 | linguistic feature detectors AI text domain shift formatting text-length SHAP benchmark accuracy not reliable evidence authorship 2026 | web/arXiv | 3 |
| 34 | 7 | reprocessed DetectRL dataset shortcuts spoofing AI-generation patterns cleansing | web | 0 (query too specific) |
| 35 | 7 | contamination in machine-generated text detection datasets syntactic shortcuts punctuation whitespace | web/arXiv | 2 |
| 36 | 3 | adversarial attack against AI text detectors homoglyph typo perturbation evade DetectGPT | web/arXiv/ACL | 1 |
| 37 | 3 | adaptive attacker against machine-generated text detectors reinforcement learning paraphrase evade detector | web/arXiv | 3 |
| 38 | 3 | mixed human-machine text detection boundary detection sentence-level human-AI collaborative | web/ACL | 2 (not included) |
| 39 | 3 | Stumbling blocks: stress testing the robustness of machine-generated text detectors under attacks | web/ACL Anthology | 1 |
| 40 | 3 | Humanizer tools AI text detection evasion study detectors robustness evaluation | web/ACL | 2 |
| 41 | 1,2 | Ghostbuster detecting text ghostwritten by large language models | web/arXiv | 1 |
| 42 | 3 | Red teaming language model detectors with language models Shi | web/TACL | 1 |
| 43 | 2 | On the zero-shot generalization of machine-generated text detectors Pu | web/ACL | 1 |
| 44 | 5 | Comparing scientific abstracts generated by ChatGPT to real abstracts with detectors and blinded human reviewers | web/PMC | 3 |
| 45 | 1 | DNA-GPT divergent N-gram analysis training-free detection | web/arXiv | 1 |
| 46 | 1 | Smaller language models are better black-box machine-generated text detectors | web/ACL | 1 |
| 47 | 1 | Raidar generative AI detection via rewriting | web/arXiv | 1 |
| 48 | 3 | OUTFOX LLM-generated essay detection in-context learning adversarially generated examples | web/AAAI | 1 |
| 49 | 3,6 | robustness of linguistic feature-based AI text detectors adversarial attack sentence mixing noise injection detector score adaptive | web/arXiv | 3 |
| 50 | 5 | machine-generated text detection scientific papers benchmark arXiv abstracts ... detectors fail | web/ACL | 2 |
| 51 | 7,3 | detector robustness audit structural artifacts control corpus-matched human machine text AI detection perturbation (extended mode) | web/arXiv | 4 |
| 52 | 9 | Watermarks in the sand impossibility of strong watermarking generative models | web/arXiv/ICML | 1 |
| 53 | 2 | All that's 'human' is not gold: evaluating human evaluation of generated text Clark | web/ACL Anthology | 1 |
| 54 | 2 | Real or fake? Learning to discriminate machine from human generated text Bakhtin | web/arXiv | 1 (not included; author list not verified) |
| 55 | 4 | TuringBench benchmark environment for Turing test in the age of neural text generation | web/ACL | 1 |
| 56 | 10 | LLMs as zero-shot detectors of AI-generated text GPT-4 prompted to detect | web/arXiv | 2 (not included; not verified) |
| 57 | 9 | Three bricks to consolidate watermarks for large language models | web/arXiv | 1 |
| 58 | 3 | Are AI-generated text detectors robust to adversarial perturbations ACL 2024 | web/ACL | 1 |
| 59 | 3 | Adversarial paraphrasing universal attack humanizing AI-generated text | web/NeurIPS | 1 |
| 60 | 7 | Are AI detectors good enough? A survey on quality of datasets with machine-generated texts | web/arXiv | 1 |
| 61 | 5 | Mosca distinguishing fact from fiction benchmark machine-generated scientific papers | web/ACL | 1 |
| 62 | 5 | ChatGPT-generated peer reviews detection ... hidden prompt injection | web/arXiv | 1 |
| 63 | 12 | Geng Trotta Is ChatGPT transforming academics' writing style | web/arXiv | 1 |
| 64 | 10 | OpenAI text classifier AI-written text evaluation | web (OpenAI blog) | 0 (grey literature, excluded) |
| 65 | 12 | Liang "Quantifying large language model usage in scientific papers" Nature Human Behaviour 2025 | web/Nature | 1 |
| 66 | 5 | Desaire ... Cell Reports Physical Science (author lookup) | web/PMC | 1 |
| 67 | 4 | M4GT-Bench evaluation benchmark ACL 2024 | web/ACL | 1 |
| 68 | 4 | SemEval-2024 Task 8 | web/ACL | 1 |
| 69 | 3 | score-based adaptive attack detector query feedback sentence insertion noise evade Binoculars Fast-DetectGPT | web/arXiv | 3 |
| 70 | 3 | Unveiling effective disturbances for modern AI content detectors | web/ACL | 1 |
| 71 | 3 | Mutation-based adversarial attacks on neural text detectors | web/arXiv | 1 |
| 72 | 3 | Beemo benchmark of expert-edited machine-generated outputs | web/ACL | 1 |
| 73 | 5 | LLM-written scientific abstracts detection robustness Nature Machine Intelligence / Patterns / PNAS | web/arXiv | 1 |

73 distinct queries. No Nature Machine Intelligence, PNAS or Nature-portfolio detection-robustness paper surfaced; the Nature portfolio hit is the prevalence paper in Nature Human Behaviour. In total, about 70 further verification fetches were made on primary pages (not logged as queries).

## (b) Counts

- Identified: about 105 distinct records surfaced in result lists (approximate; counted by eye from result lists, not by script).
- Screened (title/abstract-level, by search snippet): about 90.
- Included: 64 (all VERIFIED, with notes where a venue came from a proceedings page displayed in a search result rather than from an opened page).
- Excluded, in brief: news, blogs and vendor pages (OpenAI classifier blog, press coverage, Substack, rework.com, casrai.org); Problematic Paper Screener / tortured-phrase web pages (no primary paper verified); items seen only in snippets with unverified author lists or venues (Bakhtin et al. 2019; SCIgen detection papers; Dugan et al. boundary-detection papers; TM-TREK SemEval system; StyleDecipher; GradEscape; MASH; WaveDetect; Sci-SpanDet; TADDLE; CoCoNUTS; C-ReD; BAID; GECScore; stylometry studies); pure generation-quality material. Several of these are worth a second pass if space allows.

## (c) Included references

Notes on format: Nature reference style, initials derived from the full given names shown on the primary page. More than five authors are abbreviated with "et al.". "Themes" use the numbering in the task (1 zero-shot, 2 supervised/generalisation, 3 attacks/robustness, 4 benchmarks, 5 scientific/peer review, 6 feature-based/explainable, 7 artifacts/shortcuts, 8 bias, 9 watermarking, 10 LLM judge, 11 survey, 12 prevalence).

| key | citation | themes | relevance to a robustness audit | status | URL |
|---|---|---|---|---|---|
| gehrmann2019 | Gehrmann, S., Strobelt, H. & Rush, A. GLTR: statistical detection and visualization of generated text. In Proc. 57th Annu. Meet. ACL: System Demonstrations 111-116 (ACL, 2019). | 1 | Origin of rank/entropy/probability feature screens that count-based screens descend from. | VERIFIED | https://aclanthology.org/P19-3019/ |
| solaiman2019 | Solaiman, I. et al. Release strategies and the social impacts of language models. Preprint at arXiv:1908.09203 (2019). | 11,2 | Early statement of detector arms race and the GPT-2 RoBERTa detector baseline. | VERIFIED | https://arxiv.org/abs/1908.09203 |
| zellers2019 | Zellers, R. et al. Defending against neural fake news. In Adv. Neural Inf. Process. Syst. 32 (NeurIPS 2019). | 2 | Shows sampling artifacts are exploitable by discriminators and detectors lose power on other generators. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/1905.12616 |
| ippolito2020 | Ippolito, D., Duckworth, D., Callison-Burch, C. & Eck, D. Automatic detection of generated text is easiest when humans are fooled. In Proc. 58th Annu. Meet. ACL 1808-1822 (ACL, 2020). | 2,1 | Detectors exploit statistical abnormalities and generalise poorly to unseen decoding. | VERIFIED | https://aclanthology.org/2020.acl-main.164/ |
| uchendu2020 | Uchendu, A., Le, T., Shu, K. & Lee, D. Authorship attribution for neural text generation. In Proc. 2020 Conf. EMNLP 8384-8395 (ACL, 2020). | 2,6 | Early cross-generator attribution, including linguistic-feature baselines. | VERIFIED | https://aclanthology.org/2020.emnlp-main.673/ |
| clark2021 | Clark, E. et al. All that's 'human' is not gold: evaluating human evaluation of generated text. In Proc. ACL-IJCNLP 7282-7296 (ACL, 2021). | 2 | Human judges near chance on GPT-3, so human labels cannot anchor a screen. | VERIFIED (arXiv page opened; ACL pages and Outstanding Paper status from search result) | https://arxiv.org/abs/2107.00061 |
| uchendu2021 | Uchendu, A., Ma, Z., Le, T., Zhang, R. & Lee, D. TuringBench: a benchmark environment for Turing test in the age of neural text generation. In Findings ACL: EMNLP 2021 2001-2016 (ACL, 2021). | 4,2 | Benchmark showing detection depends on generator; basis for cross-generator transfer tests. | VERIFIED | https://aclanthology.org/2021.findings-emnlp.172/ |
| mitchell2023 | Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D. & Finn, C. DetectGPT: zero-shot machine-generated text detection using probability curvature. In Proc. 40th Int. Conf. Mach. Learn. (PMLR 202, 2023). | 1 | Canonical perturbation-curvature zero-shot detector to attack and benchmark. | VERIFIED (ICML 2023 per arXiv comments; PMLR 202 from search result) | https://arxiv.org/abs/2301.11305 |
| bao2024 | Bao, G., Zhao, Y., Teng, Z., Yang, L. & Zhang, Y. Fast-DetectGPT: efficient zero-shot detection of machine-generated text via conditional probability curvature. In Int. Conf. Learn. Represent. (ICLR 2024). | 1 | Strong, widely used zero-shot baseline for the audit. | VERIFIED | https://arxiv.org/abs/2310.05130 |
| hans2024 | Hans, A. et al. Spotting LLMs with Binoculars: zero-shot detection of machine-generated text. In Proc. 41st Int. Conf. Mach. Learn. (ICML 2024). Preprint at arXiv:2401.12070. | 1 | State-of-the-art zero-shot score (perplexity over cross-perplexity) whose score can be directly attacked. | VERIFIED (arXiv page lists no venue; ICML 2024 from the icml.cc poster page shown in search) | https://arxiv.org/abs/2401.12070 |
| yang2024 | Yang, X. et al. DNA-GPT: divergent n-gram analysis for training-free detection of GPT-generated text. In Int. Conf. Learn. Represent. (ICLR 2024). Preprint at arXiv:2305.17359. | 1 | Regeneration-based zero-shot detector with claimed robustness to revision attacks. | VERIFIED (authors via arXiv; ICLR 2024 from iclr.cc poster page shown in search) | https://arxiv.org/abs/2305.17359 |
| mao2024 | Mao, C., Vondrick, C., Wang, H. & Yang, J. Raidar: generative AI detection via rewriting. In Int. Conf. Learn. Represent. (ICLR 2024). | 1 | Rewrite-based detector evaluated on arXiv papers; another score an author could target. | VERIFIED | https://arxiv.org/abs/2401.12970 |
| mireshghallah2024 | Mireshghallah, N., Mattern, J., Gao, S., Shokri, R. & Berg-Kirkpatrick, T. Smaller language models are better zero-shot machine-generated text detectors. In Proc. 18th Conf. Eur. Chapter ACL (Vol. 2: Short Papers) 278-293 (ACL, 2024). | 1,2 | Shows detector-model choice drives cross-generator transfer. | VERIFIED | https://aclanthology.org/2024.eacl-short.25/ |
| verma2024 | Verma, V., Fleisig, E., Tomlin, N. & Klein, D. Ghostbuster: detecting text ghostwritten by large language models. In NAACL 2024 (ACL, 2024). Preprint at arXiv:2305.15047. | 2,6 | Feature-search supervised detector with OOD tests; non-native bias discussion. | VERIFIED (venue from arXiv comments; ACL Anthology page seen in search) | https://arxiv.org/abs/2305.15047 |
| pu2023 | Pu, X., Zhang, J., Han, X., Tsvetkov, Y. & He, T. On the zero-shot generalization of machine-generated text detectors. In Findings ACL: EMNLP 2023 4799-4808 (ACL, 2023). | 2 | Cross-generator transfer of supervised detectors. | VERIFIED | https://aclanthology.org/2023.findings-emnlp.318/ |
| krishna2023 | Krishna, K., Song, Y., Karpinska, M., Wieting, J. & Iyyer, M. Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. In Adv. Neural Inf. Process. Syst. 36 (NeurIPS 2023). | 3 | DIPPER paraphrase attack; the standard paraphrase condition. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2303.13408 |
| sadasivan2025 | Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W. & Feizi, S. Can AI-generated text be reliably detected? Trans. Mach. Learn. Res. (2025). Preprint at arXiv:2303.11156. | 3 | Recursive paraphrasing and theoretical limits; frames the adaptive-author setting. | VERIFIED | https://arxiv.org/abs/2303.11156 |
| shi2024 | Shi, Z., Wang, Y., Yin, F., Chen, X., Chang, K.-W. & Hsieh, C.-J. Red teaming language model detectors with language models. Trans. Assoc. Comput. Linguist. 12, 174-189 (2024). | 3 | Substitution and instruction-search attacks against detectors with an auxiliary LLM. | VERIFIED | https://aclanthology.org/2024.tacl-1.10/ |
| wang2024stumbling | Wang, Y. et al. Stumbling blocks: stress testing the robustness of machine-generated text detectors under attacks. In Proc. 62nd Annu. Meet. ACL (Vol. 1) 2894-2925 (ACL, 2024). | 3 | Editing, paraphrasing, prompting and co-generation attacks under budgets; closest design template. | VERIFIED | https://aclanthology.org/2024.acl-long.160/ |
| huang2024 | Huang, G. et al. Are AI-generated text detectors robust to adversarial perturbations? In Proc. 62nd Annu. Meet. ACL (Vol. 1) 6005-6024 (ACL, 2024). | 3 | Character and word-level perturbation flips detector decisions; includes mixed-source tests. | VERIFIED | https://aclanthology.org/2024.acl-long.327/ |
| zhou2024 | Zhou, Y., He, B. & Sun, L. Navigating the shadows: unveiling effective disturbances for modern AI content detectors. In Proc. 62nd Annu. Meet. ACL (Vol. 1) 10847-10861 (ACL, 2024). | 3 | Twelve black-box perturbation methods across granularities. | VERIFIED | https://aclanthology.org/2024.acl-long.584/ |
| liang2023mutation | Liang, G., Guerrero, J. & Alsmadi, I. Mutation-based adversarial attacks on neural text detectors. Preprint at arXiv:2302.05794 (2023). | 3 | Character/word mutation attacks (noise-type) on neural detectors; arXiv only (no venue on the page). | VERIFIED (preprint only) | https://arxiv.org/abs/2302.05794 |
| koike2024 | Koike, R., Kaneko, M. & Okazaki, N. OUTFOX: LLM-generated essay detection through in-context learning with adversarially generated examples. Proc. AAAI Conf. Artif. Intell. 38, 21258-21266 (2024). | 3 | Attacker-detector co-adaptation for essays; adaptive author precedent. | VERIFIED | https://ojs.aaai.org/index.php/AAAI/article/view/30120 |
| creo2025 | Creo, A. & Pudasaini, S. SilverSpeak: evading AI-generated text detectors using homoglyphs. In Proc. 1st Workshop GenAI Content Detection 1-46 (2025). | 3 | Homoglyph noise breaks DetectGPT, Binoculars, Fast-DetectGPT and others. | VERIFIED | https://aclanthology.org/2025.genaidetect-1.1/ |
| masrour2025 | Masrour, E., Emi, B. N. & Spero, M. DAMAGE: detecting adversarially modified AI generated text. In Proc. 1st Workshop GenAI Content Detection 120-133 (2025). | 3 | 19 humanizer tools stress-tested; vendor-affiliated, so treat defence claims with care. | VERIFIED | https://aclanthology.org/2025.genaidetect-1.9/ |
| cheng2025 | Cheng, Y., Sadasivan, V. S., Saberi, M., Saha, S. & Feizi, S. Adversarial paraphrasing: a universal attack for humanizing AI-generated text. In Adv. Neural Inf. Process. Syst. 38 (NeurIPS 2025). | 3 | Detector-guided paraphrasing, i.e. an attack aimed at a detector's own score. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2506.07001 |
| david2025 | David, I. & Gervais, A. AuthorMist: evading AI text detectors with reinforcement learning. Preprint at arXiv:2503.08716 (2025). | 3 | RL paraphraser trained with commercial detector scores as reward (adaptive author). | VERIFIED (preprint only) | https://arxiv.org/abs/2503.08716 |
| ranganath2026 | Ranganath, S. & Ramesh, A. StealthRL: reinforcement learning paraphrase attacks for multi-detector evasion of AI-text detectors. Preprint at arXiv:2602.08934 (2026). | 3 | GRPO paraphrase policy against RoBERTa, Fast-DetectGPT, Binoculars and MAGE ensemble; near-zero TPR at 1% FPR. Workshop paper (PlurVA-LLM 2026 at AACL-IJCNLP 2026 per arXiv comments). | VERIFIED (preprint; workshop venue from comments) | https://arxiv.org/abs/2602.08934 |
| tufts2025 | Tufts, B., Zhao, X. & Li, L. A practical examination of AI-generated text detectors for large language models. In Findings ACL: NAACL 2025 4839-4856 (ACL, 2025). | 3,1 | Fast-DetectGPT and Binoculars on unseen domains with prompt-based evasion. | VERIFIED | https://aclanthology.org/2025.findings-naacl.271/ |
| bao2026 | Bao, G. et al. Triospect: a three-dimensional framework for robust statistical AI-generated text detection against diverse attacks. Preprint at arXiv:2606.31074 (2026). | 1,3 | Statistical detector evaluated against 17 attacks on Humanize-16K and adversarial RAID; arXiv comments say "TACL final version". | VERIFIED (arXiv; journal pagination not confirmed) | https://arxiv.org/abs/2606.31074 |
| artemova2025 | Artemova, E. et al. Beemo: benchmark of expert-edited machine-generated outputs. In Proc. 2025 Conf. NAACL (Vol. 1) 6992-7018 (ACL, 2025). | 3,4 | Expert and LLM edits of machine text; edited text evades detection. | VERIFIED | https://aclanthology.org/2025.naacl-long.357/ |
| dugan2024 | Dugan, L. et al. RAID: a shared benchmark for robust evaluation of machine-generated text detectors. In Proc. 62nd Annu. Meet. ACL (Vol. 1) 12463-12492 (ACL, 2024). | 4,3 | 11 attacks, 11 generators, 8 domains, 4 decoding settings; the main attack benchmark. | VERIFIED | https://aclanthology.org/2024.acl-long.674/ |
| li2024mage | Li, Y. et al. MAGE: machine-generated text detection in the wild. In Proc. 62nd Annu. Meet. ACL (Vol. 1) 36-53 (ACL, 2024). | 4,2 | Cross-domain and cross-generator testbeds with paraphrase. | VERIFIED | https://aclanthology.org/2024.acl-long.3/ |
| wang2024m4 | Wang, Y. et al. M4: multi-generator, multi-domain, and multi-lingual black-box machine-generated text detection. In Proc. 18th Conf. Eur. Chapter ACL (Vol. 1) 1369-1407 (ACL, 2024). | 4,2 | Detectors fail on unseen domains and generators. | VERIFIED (ACL Anthology opened; arXiv page itself lists no venue) | https://aclanthology.org/2024.eacl-long.83/ |
| wang2024m4gt | Wang, Y. et al. M4GT-Bench: evaluation benchmark for black-box machine-generated text detection. In Proc. 62nd Annu. Meet. ACL (Vol. 1) 3964-3992 (ACL, 2024). | 4,2 | Adds model attribution and mixed-text boundary tasks. | VERIFIED | https://aclanthology.org/2024.acl-long.218/ |
| wang2024semeval | Wang, Y. et al. SemEval-2024 Task 8: multidomain, multimodel and multilingual machine-generated text detection. In Proc. 18th Int. Workshop Semantic Evaluation 2057-2079 (ACL, 2024). | 4 | Shared-task results showing LLM-based detectors lead; mixed-text subtask hard. | VERIFIED | https://aclanthology.org/2024.semeval-1.279/ |
| guo2023 | Guo, B. et al. How close is ChatGPT to human experts? Comparison corpus, evaluation, and detection. Preprint at arXiv:2301.07597 (2023). | 4,6 | HC3 corpus; question-answer format and length differences are a known structural confound; includes linguistic analysis. | VERIFIED (preprint only) | https://arxiv.org/abs/2301.07597 |
| he2023 | He, X., Shen, X., Chen, Z., Backes, M. & Zhang, Y. MGTBench: benchmarking machine-generated text detection. Preprint at arXiv:2303.14822 (2023). | 4,3 | Unified evaluation of metric-based and model-based detectors with paraphrase, spacing and perturbation attacks. | VERIFIED (preprint; page lists no venue) | https://arxiv.org/abs/2303.14822 |
| wu2024detectrl | Wu, J. et al. DetectRL: benchmarking LLM-generated text detection in real-world scenarios. In Adv. Neural Inf. Process. Syst. 37, Datasets and Benchmarks Track (NeurIPS 2024). | 4,3 | Includes attacks and mixing scenarios; the corpus later audited for artifacts by dingfelder2025. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2410.23746 |
| wu2025survey | Wu, J., Yang, S., Zhan, R., Yuan, Y., Chao, L. S. & Wong, D. F. A survey on LLM-generated text detection: necessity, methods, and future directions. Comput. Linguist. 51, 275-338 (2025). | 11 | Standard survey; names OOD, attacks and evaluation frameworks as open problems. | VERIFIED | https://aclanthology.org/2025.cl-1.8/ |
| gritsai2025 | Gritsai, G., Voznyuk, A., Grabovoy, A. & Chekhovich, Y. Are AI detectors good enough? A survey on quality of datasets with machine-generated texts. Presented at PDLM workshop, AAAI 2025. Preprint at arXiv:2410.14677. | 7,11 | Reviews detection competition datasets and proposes perturbation/shuffling tests for dataset quality. | VERIFIED (workshop venue from arXiv comments) | https://arxiv.org/abs/2410.14677 |
| dingfelder2025 | Dingfelder, P. & Riess, C. Contamination in generated text detection benchmarks. Preprint at arXiv:2511.09200 (2025) (CSCML 2025 per arXiv comments). | 7,3 | Shows 98.5% of DetectRL Claude text carries chatbot residue ("Sure! Here is...") that detectors learn as a shortcut and attackers spoof. Note: some indexes mangle the title with a chatbot preamble; the real title is as given. | VERIFIED | https://arxiv.org/abs/2511.09200 |
| pudasaini2026 | Pudasaini, S., Miralles-Pechuan, L., Lillis, D. & Llorens Salvador, M. Why AI-generated text detection fails: evidence from explainable AI beyond benchmark accuracy. Preprint at arXiv:2603.23146 (2026). | 6,7 | Thirty-feature interpretable detector, F1 0.9734 in-domain, collapse under cross-domain/cross-generator; features most useful in-domain are most vulnerable to formatting and length. | VERIFIED (preprint only) | https://arxiv.org/abs/2603.23146 |
| xia2026 | Xia, Y., Stanczak, K. & Roth, B. Explaining generalization of AI-generated text detectors through linguistic analysis. Preprint at arXiv:2601.07974 (2026). | 6,2 | Links transfer accuracy to shifts in 80 linguistic features (tense, pronouns). Authors' diacritics simplified here. | VERIFIED (preprint only) | https://arxiv.org/abs/2601.07974 |
| mady2026 | Mady, M., Reschke, J. & Schuller, B. Feature-augmented transformers for robust AI-text detection across domains and generators. Preprint at arXiv:2605.03969 (2026). | 6,2 | Linguistic-feature fusion improves transfer; brittle under shift. Submitted to ICML 2026 per comments (not confirmed accepted). | VERIFIED (preprint only) | https://arxiv.org/abs/2605.03969 |
| perrone2026 | Perrone, G. & Romano, S. P. ARB: a matched authorship-rewriting benchmark dataset for AI-text detector evaluation. Preprint at arXiv:2607.29539 (2026). | 3,7 | Matched human/LLM/rewritten variants per source; Fast-DetectGPT and Binoculars catch about 91-94% direct LLM text but far less LLM-rewritten human text (about 31%, 15%). | VERIFIED (preprint only) | https://arxiv.org/abs/2607.29539 |
| creanga2026 | Creanga, C. & Dinu, L. Ontological instability and statistical amplification: the paradox of "humanizing" LLM-generated text. Preprint at arXiv:2610.03110 (2026). | 3,2 | RoBERTa detector on M4 under semantic, structural and tokenizer perturbations; 76.3% false-positive rate on formal human writing. | VERIFIED (preprint only) | https://arxiv.org/abs/2610.03110 |
| liang2023patterns | Liang, W., Yuksekgonul, M., Mao, Y., Wu, E. & Zou, J. GPT detectors are biased against non-native English writers. Patterns 4, 100779 (2023). | 8,1 | Low-perplexity screens flag non-native writing; a fairness check any screening claim needs. | VERIFIED (PMC) | https://doi.org/10.1016/j.patter.2023.100779 |
| kirchenbauer2023 | Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I. & Goldstein, T. A watermark for large language models. In Proc. 40th Int. Conf. Mach. Learn. (PMLR 202, 2023). | 9 | Reference watermark; contrast case where the author does not control the generator. | VERIFIED | https://arxiv.org/abs/2301.10226 |
| kirchenbauer2024 | Kirchenbauer, J. et al. On the reliability of watermarks for large language models. In Int. Conf. Learn. Represent. (ICLR 2024). | 9,3 | Watermark survival under human and machine paraphrase, depends on length. | VERIFIED | https://arxiv.org/abs/2306.04634 |
| zhang2024 | Zhang, H. et al. Watermarks in the sand: impossibility of strong watermarking for generative models. In Proc. 41st Int. Conf. Mach. Learn. (ICML 2024). Preprint at arXiv:2311.04378. | 9,3 | Generic removal attack argues watermarks cannot be strongly robust. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2311.04378 |
| fernandez2023 | Fernandez, P., Chaffin, A., Tit, K., Chappelier, V. & Furon, T. Three bricks to consolidate watermarks for large language models. In Proc. IEEE Int. Workshop Inf. Forensics Secur. (WIFS 2023). Preprint at arXiv:2308.00113. | 9 | Low-FPR statistical tests for watermarks. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2308.00113 |
| panickssery2024 | Panickssery, A., Bowman, S. R. & Feng, S. LLM evaluators recognize and favor their own generations. In Adv. Neural Inf. Process. Syst. 37 (NeurIPS 2024). Preprint at arXiv:2404.13076. | 10 | LLM judges can recognise their own output; supports caution on LLM-judge screens and self-preference. | VERIFIED (arXiv page lists no venue; NeurIPS 2024 from papers.nips.cc page shown in search) | https://arxiv.org/abs/2404.13076 |
| mosca2023 | Mosca, E., Abdalla, M. H. I., Basso, P., Musumeci, M. & Groh, G. Distinguishing fact from fiction: a benchmark dataset for identifying machine-generated scientific papers in the LLM era. In Proc. 3rd Workshop Trustworthy NLP 190-207 (ACL, 2023). | 5,4 | Scientific-paper benchmark with SCIgen, GPT-2/3, ChatGPT, Galactica and co-written papers. | VERIFIED | https://aclanthology.org/2023.trustnlp-1.17/ |
| gao2023 | Gao, C. A. et al. Comparing scientific abstracts generated by ChatGPT to real abstracts with detectors and blinded human reviewers. npj Digit. Med. 6, 75 (2023). | 5 | Early scientific-abstract detector study (GPT-2 output detector, plagiarism checker, reviewers). | VERIFIED (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC10133283/ |
| desaire2023 | Desaire, H., Chua, A. E., Isom, M., Jarosova, R. & Hua, D. Distinguishing academic science writing from humans or ChatGPT with over 99% accuracy using off-the-shelf machine learning tools. Cell Rep. Phys. Sci. 4, 101426 (2023). | 5,6 | Feature-based (paragraph and sentence structure, word choice) detector for scientific writing; proof of concept with 64 human articles. | VERIFIED (PMC) | https://doi.org/10.1016/j.xcrp.2023.101426 |
| dou2024 | Dou, Z., Guo, Y., Chang, C.-C., Nguyen, H. H. & Echizen, I. Enhancing robustness of LLM-synthetic text detectors for academic writing: a comprehensive analysis. Preprint at arXiv:2401.08046 (2024). | 5,3 | Prompt-robustness of detectors for academic text and a Siamese reference-based detector. | VERIFIED (preprint only) | https://arxiv.org/abs/2401.08046 |
| yu2026 | Yu, S., Luo, M., Madasu, A., Lal, V. & Howard, P. Is your paper being reviewed by an LLM? Benchmarking AI text detection in peer review. In Int. Conf. Learn. Represent. (ICLR 2026). Preprint at arXiv:2502.19614. | 5,4 | About 790k human/LLM reviews; 18 detectors struggle at low FPR; also tests LLM-edited human reviews. | VERIFIED (venue from arXiv comments) | https://arxiv.org/abs/2502.19614 |
| rao2025 | Rao, V., Kumar, A., Lakkaraju, H. & Shah, N. B. Detecting LLM-generated peer reviews. Preprint at arXiv:2503.15772 (2025). | 5,9 | Hidden-prompt watermark for reviews, robust to paraphrase; an alternative to content-based screens. | VERIFIED (preprint only) | https://arxiv.org/abs/2503.15772 |
| liang2024monitoring | Liang, W. et al. Monitoring AI-modified content at scale: a case study on the impact of ChatGPT on AI conference peer reviews. In Proc. 41st Int. Conf. Mach. Learn. (PMLR 235, 29575-29620, 2024). | 12,5 | Corpus-level estimate (6.5-16.9% of review text) without per-document classification. | VERIFIED (ICML 2024 per arXiv comments; PMLR pages from search result) | https://arxiv.org/abs/2403.07183 |
| liang2024mapping | Liang, W. et al. Mapping the increasing use of LLMs in scientific papers. Preprint at arXiv:2404.01268 (2024) (COLM 2024 per search result; arXiv page lists no venue). | 12,5 | Population-level prevalence in arXiv, bioRxiv and Nature-portfolio papers. | VERIFIED (preprint; venue only from search result) | https://arxiv.org/abs/2404.01268 |
| liang2025nhb | Liang, W. et al. Quantifying large language model usage in scientific papers. Nat. Hum. Behav. https://doi.org/10.1038/s41562-025-02273-8 (2025). | 12,5 | Published version of the above (1.12 million papers to Sept 2024; up to 22% in computer science). | VERIFIED for title, journal, DOI, year via search result display; Nature page blocked, volume/pages and full author list not opened | https://doi.org/10.1038/s41562-025-02273-8 |
| kobak2025 | Kobak, D., Gonzalez-Marquez, R., Horvat, E.-A. & Lause, J. Delving into LLM-assisted writing in biomedical publications through excess vocabulary. Sci. Adv. 11 (27) (2025). | 12,5 | Vocabulary-shift prevalence in PubMed abstracts (at least 10% in 2024). Diacritics dropped in names. | VERIFIED (arXiv page lists Science Advances 11, 27) | https://arxiv.org/abs/2406.07016 |
| geng2024 | Geng, M. & Trotta, R. Is ChatGPT transforming academics' writing style? Preprint at arXiv:2404.08627 (2024). | 12,5 | Word-frequency prevalence estimates in arXiv abstracts; depends on baseline prompt. | VERIFIED (preprint only) | https://arxiv.org/abs/2404.08627 |

Count check: 64 rows.

## (d) Eight papers the paper must discuss

1. dugan2024 (RAID): the reference attack and generator-shift benchmark; any new audit must position itself against its 11 attacks.
2. krishna2023 and sadasivan2025 (DIPPER; recursive paraphrasing and impossibility): the canonical adaptive-author attacks.
3. wang2024stumbling and huang2024 (and zhou2024): attack-budget and perturbation-granularity robustness studies, nearest in design to an attack-on-the-score audit.
4. dingfelder2025: demonstrates the structural-artifact problem (chatbot residue) in a detector benchmark and its link to spoofing; the central citation for the artifact control.
5. pudasaini2026: shows feature-based detectors learn dataset-specific, format- and length-sensitive cues; directly motivates count-based screens plus artifact control.
6. mitchell2023, bao2024 and hans2024 (DetectGPT, Fast-DetectGPT, Binoculars): the zero-shot detectors under test.
7. liang2023patterns: non-native-writer bias; any screening recommendation must address fairness.
8. liang2025nhb with liang2024monitoring: why scholarly text matters (prevalence), plus yu2026 as the closest peer-review detection benchmark.

Close runners-up: cheng2025, ranganath2026, david2025 (score-guided attacks); creo2025 (noise/homoglyph); artemova2025 and perrone2026 (edited/rewritten text); gritsai2025 (dataset quality).

## (e) Does prior work pre-empt "no prior audit combines attacks aimed at a detector's own score (sentence mixing, noise) with a control for structural artifacts in the corpora"?

Short answer: I found no single paper that combines both, but the claim as worded is exposed on both halves, so it should be narrowed and hedged ("to our knowledge", with the nearest works cited).

What exists, in decreasing closeness:

- Attacks aimed at a detector's own score already exist and are plentiful: Cheng et al. 2025 (detector-guided paraphrasing), AuthorMist (detector scores as RL reward), StealthRL (reward from a Fast-DetectGPT/Binoculars/RoBERTa ensemble), OUTFOX (attacker/detector co-adaptation), Shi et al. 2024, and Stumbling Blocks (budgeted attacks). None of these controls for structural artifacts in the corpora. So "attacks aimed at the score" cannot be presented as new; what may be new is the specific sentence-mixing and noise operators applied to the score of count-based screens.
- Noise and mixing attacks are covered: DetectRL has perturbation and data-mixing scenarios, RAID has 11 attacks (including character-level), SilverSpeak, Liang et al. mutation, Huang et al. 2024 and Zhou et al. 2024 all use noise-type perturbations. The sentence-mixing operator specifically is close to DetectRL's data mixing and Beemo/M4GT mixed-text tasks.
- Artifact control exists without attacks on the score: Dingfelder and Riess 2025 (cleansing of chatbot residue in DetectRL and showing spoofing exploits it) and Pudasaini et al. 2026 (feature-based detector, formatting and length sensitivity, SHAP). Dingfelder and Riess is the nearest overlap because it links artifacts to attackability, but its attack is a direct spoof of the artifact, not a sentence-mixing or noise attack, and it covers abstracts only as part of DetectRL.
- Partial combinations: Perrone and Romano 2026 (ARB) uses matched human/LLM/rewritten variants per source, controlling content origin, and finds zero-shot detectors miss LLM-rewritten human text; it does not describe a structural-artifact control or score-targeted attacks (abstract only; I did not read the full text). Creanga and Dinu 2026 test a RoBERTa detector under structural and tokenizer perturbations on M4 (and a control detector), and report calibration problems; again no corpus-level artifact control from the abstract.
- Scholarly text: no paper found that does the combination on scientific papers or peer reviews. Yu et al. 2026 and Mosca et al. 2023 are benchmarks without artifact-controlled attack audits; Desaire et al. 2023 is a feature-based scientific-text detector with no attack or artifact control.

Caveats: (1) I read abstracts, search snippets and primary-page metadata, not full texts, so a full-text overlap (e.g. in ARB, Creanga and Dinu, Triospect, RAID follow-ups) cannot be excluded. (2) Semantic Scholar and Google Scholar citation graphs were not queried; a forward-citation check on dingfelder2025 and pudasaini2026 is recommended before submission. (3) arXiv IDs from mid-2026 (2606-2610) are very recent and unreviewed.
