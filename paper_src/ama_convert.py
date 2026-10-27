"""Convert the JIM manuscript content to AMA journal format (AMA/JIM submission guidelines): unnumbered headings, no 'Section N',
AMA in-text citations (no comma, up to three authors listed), no leading zero before decimals, third-person abstract,
AMA reference style with full first names, takeaway table titles, generative-AI disclosure. Usage: python3 ama_convert.py in.json out.json"""
import sys, json, re
c = json.load(open(sys.argv[1], encoding='utf-8'))
SMALL = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'of', 'on', 'or', 'the', 'to', 'with', 'vs'}
def tcase(t):
    out = []; words = t.split(' ')
    for i, w in enumerate(words):
        def cap(x): return x if (re.search(r'\d', x) or re.search(r'[A-Z].*[A-Z]', x)) else x[:1].upper() + x[1:]
        if '-' in w and not re.search(r'\d', w): w = '-'.join(cap(p) if (i == 0 or p.lower() not in SMALL) else p for p in w.split('-'))
        elif i > 0 and i < len(words) - 1 and w.lower() in SMALL: w = w.lower()
        else: w = cap(w)
        out.append(w)
    r = ' '.join(out)
    return re.sub(r'(: )([a-z])', lambda m: m.group(1) + m.group(2).upper(), r)
# ---- citations
FULL = {'Aher et al.': 'Aher, Arriaga, and Kalai', 'Brand et al.': 'Brand, Israeli, and Ngwe', 'Güth et al.': 'Güth, Schmittberger, and Schwarze', 'Horton et al.': 'Horton, Filippas, and Manning',
        'Huber et al.': 'Huber, Payne, and Puto', 'Persson et al.': 'Persson, Schultzberg, and Ankargren', 'Benjamini & Hochberg': 'Benjamini and Hochberg', 'Kahneman & Tversky': 'Kahneman and Tversky',
        'Lieder & Griffiths': 'Lieder and Griffiths', 'Tversky & Kahneman': 'Tversky and Kahneman'}
def cite(s):
    for k, v in FULL.items(): s = s.replace(k, v)
    s = re.sub(r'(?<=[A-Za-zÀ-ÿ.]), (?=(?:19|20)\d{2}\b)', ' ', s)   # "al., 2023" -> "al. 2023"
    return s
def nolead(s): return re.sub(r'(?<![\d.])0\.(\d)', r'.\1', s)
def pre(s): return s.replace('pre-registrations', 'preregistrations').replace('pre-registration', 'preregistration').replace('Pre-registration', 'Preregistration').replace('pre-registered', 'preregistered').replace('Pre-registered', 'Preregistered').replace('Pre-registrations', 'Preregistrations')
def fix(s): return nolead(pre(cite(s)))
# ---- body
body = []
for b in c['body']:
    if 'h1' in b or 'h2' in b:
        k = 'h1' if 'h1' in b else 'h2'; t = re.sub(r'^\d+(\.\d+)?\.?\s+', '', b[k]); t = pre(t)
        if t == 'Conclusion': k = 'h1'
        body.append({k: tcase(t)})
    elif 'p' in b:
        p = fix(b['p'])
        p = p.replace('Section 2 develops the account, Section 3 describes the studies, Section 4 reports results, Section 5 draws managerial implications, and Section 6 discusses theory, research practice, and limitations.',
                      'The next section develops the account and propositions, the research design section describes the studies, the results section reports the findings, the managerial implications section derives the protocol, and the discussion considers theory, research practice, and limitations.')
        p = p.replace('and Sections 4.2 to 4.4 report their confirmatory tests','and the confirmatory studies report their tests')
        p = p.replace('did not replicate (Section 4.2)','did not replicate in the confirmatory twin study')
        body.append({'p': p})
    else:
        body.append(dict(b, **({'caption': fix(b['caption'])} if 'caption' in b else {})))
# AI disclosure subsection after 'Measures and Analysis Rules' paragraphs (end of Research Design)
i = max(j for j, b in enumerate(body) if b.get('h2') == tcase('Measures and analysis rules')) + 1
while 'h1' not in body[i] and 'h2' not in body[i]: i += 1
body[i:i] = [{'h2': 'Use of Generative AI'}, {'p': 'An AI model (Claude, Anthropic) wrote most of the simulation and analysis code, executed the analyses, and drafted the text under the authors’ direction. The AI model is not an author, and the authors are responsible for the content. The simulated respondents in all studies are outputs of large language models and not people, and no new human-subject data were collected.'}]
for b in body:
    if 'figure' in b:
        b['caption'] = 'Twin Effects Diverge Widely from Human Benchmarks in the Confirmatory Twin Study. Notes: Each panel is one effect. Points are twin estimates and bars are 95% respondent-bootstrap intervals (600 simulated respondents per model and architecture). The shaded band is the 95% interval of the human effect and the vertical line is the human estimate. Estimates beyond the axis range appear as triangles at the panel edge with their value.'
# ---- tables: takeaway titles, units, p and SE columns
T = c['tables']
cap = {'props': 'Registered Propositions Receive Mixed Confirmation', 'studies': 'Three Confirmatory and Three Exploratory Studies Test the Account', 'human': 'Public Human Benchmarks for Seven Consumer Decision Effects',
       'c1': 'Twins Overstate the Canonical Default and Understate the Novel Default', 'c1models': 'Model Estimates Differ Widely from Human Benchmarks (Persona-Summary Twins)',
       'h6': 'More Reasoning Lowers Factual Errors but Raises Bias', 'c2': 'Headline Predictions Beat Chance Only Without Personas and Are Compressed', 'map': 'Direction Is Usually Valid, Magnitude Rarely, and Defaults Almost Never'}
for k, v in cap.items(): T[k]['caption'] = v
T['c1'].update(widths=[3000, 1000, 1500, 1100, 800, 1960], head=['Test', 'Pooled D', '95% CI', 'Models (n of 5)', 'p', 'Verdict'])
T['c1']['rows'] = [r[:4] + ['≤ .001', r[4]] for r in T['c1']['rows']]
T['h6'].update(widths=[2900, 1150, 750, 1550, 1000, 2010], head=['Test', 'Coefficient', 'SE', '95% CI', 'Models (n of 4)', 'Verdict'])
se = {'P4 reasoning level → bias index (predicted negative)': '.097', 'P4 reasoning level → framing effect (predicted negative)': '.156', 'P4 reasoning level → attraction effect (predicted negative)': '.098',
      'P4 reasoning level → factual error (predicted negative)': '.007', 'P4 reasoning level → fabrication, with / without nudge': '—', 'P5 within-model correlation of bias and error (predicted positive)': '—'}
T['h6']['rows'] = [[r[0], r[1], se[r[0]], r[2], r[3], r[4]] for r in T['h6']['rows']]
T['c2'].update(widths=[3100, 900, 1600, 1100, 800, 1860], head=['Test', 'Pooled value', '95% CI', 'Models (n of 5)', 'p', 'Verdict'])
pv = ['.660', '≤ .001', '≤ .001', '≤ .001']; T['c2']['rows'] = [r[:4] + [pv[i], r[4]] for i, r in enumerate(T['c2']['rows'])]
T['human']['head'] = ['Effect', 'Human estimate (units as noted)', '95% interval', 'Source (n)']
T['map']['head'] = ['Effect', 'Direction valid (% of configurations)', 'Magnitude valid (% of configurations)', 'Decision rule']
for k in T:
    T[k]['head'] = [fix(h) for h in T[k]['head']]; T[k]['rows'] = [[fix(x) for x in r] for r in T[k]['rows']]; T[k]['caption'] = fix(T[k]['caption'])
# ---- abstract (third person, <= 200 words)
abstract = ('Marketers increasingly consider LLM-based synthetic consumers to pre-screen digital experiments and to run market research, yet when such agents can be trusted is unknown. '
 'The authors propose a validity-region account: a synthetic agent is informative about a treatment effect only if the effect operates through textual cues, does not depend on effort costs, lies outside memorized paradigms, and the agent’s reasoning regime matches the human one. '
 'In preregistered tests with new simulated respondents, a reasoning-by-temperature grid, and 999 public headline A/B tests, plus a stability study over 13 model versions, default effects reverse with paradigm familiarity in all five model families, naming the theory inflates canonical effects, reasoning reduces factual errors but raises bias, and click predictions beat chance by nine points only without personas and are compressed. '
 'Errors are specific to model versions. The authors derive a version-specific validation protocol that tells managers when synthetic evidence can screen designs and when human tests are required.')
assert len(abstract.split()) <= 200, len(abstract.split())
# ---- references (AMA style, full first names; italics with *...*)
refs = [
"Aher, Gati V., Rosa I. Arriaga, and Adam Tauman Kalai (2023), “Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies,” in *Proceedings of the 40th International Conference on Machine Learning*, PMLR 202, 337–71.",
"Argyle, Lisa P., Ethan C. Busby, Nancy Fulda, Joshua R. Gubler, Christopher Rytting, and David Wingate (2023), “Out of One, Many: Using Language Models to Simulate Human Samples,” *Political Analysis*, 31 (3), 337–51.",
"Benjamini, Yoav and Yosef Hochberg (1995), “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing,” *Journal of the Royal Statistical Society: Series B*, 57 (1), 289–300.",
"Binz, Marcel, Elif Akata, Matthias Bethge, Franziska Brändle, Fred Callaway, Julian Coda-Forno, Peter Dayan, Can Demircan, Maria K. Eckstein, Noémi Éltető, Thomas L. Griffiths, Susanne Haridi, Akshay K. Jagadish, Li Ji-An, Alexander Kipnis, Sreejan Kumar, Tobias Ludwig, Marvin Mathony, Marcelo Mattar, Alireza Modirshanechi, et al. (2025), “A Foundation Model to Predict and Capture Human Cognition,” *Nature*, 644 (8078), 1002–9, https://doi.org/10.1038/s41586-025-09215-4.",
"Brand, James, Ayelet Israeli, and Donald Ngwe (2024), “Using GPT for Market Research,” in *Proceedings of the 25th ACM Conference on Economics and Computation*, https://doi.org/10.1145/3670865.3673479.",
"Carlini, Nicholas, Daphne Ippolito, Matthew Jagielski, Katherine Lee, Florian Tramèr, and Chiyuan Zhang (2023), “Quantifying Memorization Across Neural Language Models,” in *International Conference on Learning Representations*.",
"Carlini, Nicholas, Florian Tramèr, Eric Wallace, Matthew Jagielski, Ariel Herbert-Voss, Katherine Lee, Adam Roberts, Tom Brown, Dawn Song, Úlfar Erlingsson, Alina Oprea, and Colin Raffel (2021), “Extracting Training Data from Large Language Models,” in *30th USENIX Security Symposium*. USENIX Association, 2633–50.",
"Güth, Werner, Rolf Schmittberger, and Bernd Schwarze (1982), “An Experimental Analysis of Ultimatum Bargaining,” *Journal of Economic Behavior & Organization*, 3 (4), 367–88.",
"Horton, John J., Apostolos Filippas, and Benjamin S. Manning (2023), “Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?” NBER Working Paper No. 31122, National Bureau of Economic Research.",
"Huber, Joel, John W. Payne, and Christopher Puto (1982), “Adding Asymmetrically Dominated Alternatives: Violations of Regularity and the Similarity Hypothesis,” *Journal of Consumer Research*, 9 (1), 90–98.",
"Hullman, Jessica, David Broska, Huaman Sun, and Aaron Shaw (2026), “This Human Study Did Not Involve Human Subjects: Validating LLM Simulations as Behavioral Evidence,” arXiv preprint (arXiv:2602.15785), https://arxiv.org/abs/2602.15785.",
"Jachimowicz, Jon M., Shannon Duncan, Elke U. Weber, and Eric J. Johnson (2019), “When and Why Defaults Influence Decisions: A Meta-Analysis of Default Effects,” *Behavioural Public Policy*, 3 (2), 159–86.",
"Kahneman, Daniel and Amos Tversky (1979), “Prospect Theory: An Analysis of Decision Under Risk,” *Econometrica*, 47 (2), 263–91.",
"Lieder, Falk and Thomas L. Griffiths (2020), “Resource-Rational Analysis: Understanding Human Cognition as the Optimal Use of Limited Computational Resources,” *Behavioral and Brain Sciences*, 43, e1.",
"Maiorano, Alexandre Cristovão (2026), “Do Synthetic Personas Predict Real Audience Response? A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based Copy Simulation,” arXiv preprint (arXiv:2609.25010), https://arxiv.org/abs/2609.25010.",
"Matias, J. Nathan, Kevin Munger, Marianne Aubin Le Quere, and Charles Ebersole (2021), “The Upworthy Research Archive, a Time Series of 32,487 Experiments in U.S. Media,” *Scientific Data*, 8, Article 195.",
"Peng, Tianyi, George Gui, Melanie Brucks, Daniel J. Merlau, Grace Jiarui Fan, Malek Ben Sliman, Eric J. Johnson, Abdullah Althenayyan, Silvia Bellezza, Dante Donati, Hortense Fong, Elizabeth Friedman, Ariana Guevara, Mohamed Hussein, Kinshuk Jerath, Bruce Kogut, Akshit Kumar, Kristen Lane, Hannah Li, Vicki Morwitz, et al. (2026), “Digital Twins Are Funhouse Mirrors: Five Systematic Distortions,” arXiv preprint (arXiv:2509.19088), https://arxiv.org/abs/2509.19088.",
"Persson, Joel, Mårten Schultzberg, and Sebastian Ankargren (2026), “Statistical Foundations of LLM-Based A/B Testing: A Surrogacy Framework for Human Causal Inference,” arXiv preprint (arXiv:2606.17165), https://arxiv.org/abs/2606.17165.",
"Sarstedt, Marko, Susanne J. Adler, Lea Rau, and Bernd Schmitz (2024), “Using Large Language Models to Generate Silicon Samples in Consumer and Marketing Research: Challenges, Opportunities, and Guidelines,” *Psychology & Marketing*, 41 (6), 1254–70, https://doi.org/10.1002/mar.21982.",
"Stromberg, Malik, Wendy W. Moe, Thomas Reutterer, and David A. Schweidel (2025), “Blind Spots in Broad Strokes: Caveats for the Use of LLMs in Marketing Research,” SSRN, https://doi.org/10.2139/ssrn.5145114.",
"Toubia, Olivier, George Z. Gui, Tianyi Peng, Daniel J. Merlau, Ang Li, and Haozhe Chen (2025), “Twin-2K-500: A Data Set for Building Digital Twins of over 2,000 People Based on Their Answers to over 500 Questions,” *Marketing Science*, 44 (6), 1446–55, https://doi.org/10.1287/mksc.2025.0262.",
"Tversky, Amos and Daniel Kahneman (1974), “Judgment Under Uncertainty: Heuristics and Biases,” *Science*, 185 (4157), 1124–31.",
"Wang, Steven, Kyle Hunt, Shaojie Tang, and Kenneth Joseph (2026), “When Can LLM Digital Twins Reduce Human Measurement? From Behavioral Fidelity to Statistical Substitutability,” arXiv preprint (arXiv:2609.07987), https://arxiv.org/abs/2609.07987."]
appendix = [{'h1': 'Appendix A: Deviations from the Preregistrations and Corrections'},
 {'p': fix([a for a in c['appendix'] if a.get('p', '').startswith('All registered predictions')][0]['p'])}]
out = dict(title=c['title'], abstract=abstract, keywords=c['keywords'], body=body, tables=T, refs=refs, appendix=appendix)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('ok', len(abstract.split()), 'abstract words')
