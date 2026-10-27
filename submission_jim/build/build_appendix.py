"""Builds the online appendix (Word) from the repository results and code. Usage: python3 build_appendix.py <data_dir> <out.docx>
<data_dir> must hold the three mega-study parquet files (for the stimulus texts); results are read from ../../results."""
import sys, os, re, json, datetime
import pandas as pd, requests
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); D, OUT = sys.argv[1], sys.argv[2]
R = lambda *p: os.path.join(ROOT, 'results', *p)
doc = Document(); sec = doc.sections[0]; sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(11)
for h in ('Heading 1', 'Heading 2', 'Heading 3'): doc.styles[h].font.name = 'Times New Roman'; doc.styles[h].font.color.rgb = None
def H(t, l=1): doc.add_heading(t, level=l)
def P(t, bold=False, italic=False, size=None):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    return p
def MONO(t):
    p = doc.add_paragraph(); r = p.add_run(t); r.font.name = 'Courier New'; r.font.size = Pt(8.5); p.paragraph_format.left_indent = Inches(0.2); return p
def TAB(df, widths=None, size=8.5, caption=None):
    if caption: P(caption, bold=True)
    t = doc.add_table(rows=1, cols=len(df.columns)); t.style = 'Table Grid'
    for i, c in enumerate(df.columns):
        cell = t.rows[0].cells[i]; cell.text = ''; r = cell.paragraphs[0].add_run(str(c)); r.bold = True; r.font.size = Pt(size)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''; r = cells[i].paragraphs[0].add_run('' if (isinstance(v, float) and pd.isna(v)) else str(v)); r.font.size = Pt(size)
    doc.add_paragraph()
def fmt(x, d=2): return '' if pd.isna(x) else f'{x:.{d}f}'
def md_text(path):
    s = open(path).read(); s = re.sub(r'^#+\s*', '', s, flags=re.M); return s.strip()

t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Online Appendix\nWhen Can Marketers Trust Synthetic Consumers? Validity Regions and a Validation Protocol for LLM Digital Twins in Digital Experimentation'); r.bold = True; r.font.size = Pt(14)
P('This appendix accompanies the manuscript. Section A inventories the studies. Section B documents all materials (prompts, stimuli, factual battery, personas, models). Section C reproduces the pre-registrations and the deviation log. Section D reports complete results. Section E documents data quality and exclusions. Section F covers code, data, and disclosure statements.', italic=True)

# ---------------- A
H('A. Study inventory and compute')
costs = {}
for nm, rel in [('E1', 'full2'), ('E2', 'h6'), ('C1', 'c1'), ('H6c', 'h6c'), ('C2', 'c2conf'), ('S', 'gen')]: pass
inv = pd.DataFrame([
 ['E1', 'Exploratory twin simulations', '772 mega-study respondents; defaults, attraction, targeting fairness', '5 models × 3 persona architectures; template A', '36,009 of 36,450 planned', '83.89', 'None'],
 ['E2', 'Exploratory reasoning × temperature pilot', '100 respondents per task + 100 for factual battery', '4 models × 9 cells', '14,400', '45.55', 'None'],
 ['C1', 'Confirmatory twin study', '600 new respondents; 9 items', '5 models × 3 architectures; template B', '9,000', '19.00', 'AsPredicted #320110'],
 ['H6c', 'Confirmatory reasoning grid', '100 new respondents; booklet + 2 batteries', '4 models × 3 effort × 3 temperature', '10,800', '32.60', 'AsPredicted #320110'],
 ['C2', 'Confirmatory field test', '999 Upworthy tests (confirmatory package)', '5 models × persona / no-persona × 5 draws', '50,000', '35.07', 'AsPredicted #320124'],
 ['S', 'Stability across templates and generations', '200 new respondents', '13 model versions × 2 templates; persona summary', '5,200', '84.86', 'None (exploratory)'],
 ['dev', 'C2 development (exploratory package, 150 tests)', '150 Upworthy tests', '5 models × 2 arms × 5 draws', '7,499', '5.23', 'None']],
 columns=['Study', 'Purpose', 'Units', 'Configuration', 'API calls', 'Cost (USD)', 'Registration'])
TAB(inv, caption='Table A1. Studies, calls, and API cost (all runs executed on 26 October 2026; total about 306 USD).')
P('E1 is 441 calls short of plan because some Llama 4 Maverick calls failed repeatedly under upstream rate limits; the missing calls are concentrated in Llama cells (Section E). All other studies completed all planned calls.')

# ---------------- B
H('B. Materials')
H('B1. Prompts and templates', 2)
code = open(os.path.join(ROOT, 'pilot', 'run_c1.py')).read(); gen = open(os.path.join(ROOT, 'pilot', 'run_gen.py')).read(); full = open(os.path.join(ROOT, 'pilot', 'run_full.py')).read(); c2 = open(os.path.join(ROOT, 'pilot', 'run_c2.py')).read()
def grab(src, name):
    m = re.search(name + r"\s*=\s*\(?((?:'(?:[^'\\]|\\.)*'\s*)+)\)?", src); return eval('(' + m.group(1) + ')') if m else ''
P('Template B (confirmatory; system prompt, persona block follows):', bold=True); MONO(grab(code, 'HEAD'))
P('Theory-explicit research note appended to the demographic profile:', bold=True); MONO(grab(code, 'NOTE').strip())
P('Template A (exploratory and stability study; system prompt):', bold=True); MONO(grab(gen, 'HEAD_A'))
P('Template B user message (header; the questions follow as "Q1. ..." with numbered options):', bold=True)
MONO('Please complete the following short survey as the person described. For every question reply with the number of the option you would choose, or with the number you would enter for numeric questions. Reply with only a JSON object whose keys are the question labels, for example {"Q1": 2, "Q2": 35}.')
P('Template A user message (survey-text format with a JSON answer template; example for one single-choice question):', bold=True)
MONO('Q1:\n<question text>\nQuestion Type: Single Choice\nOptions:\n  1 - <option>\n  2 - <option>\nAnswer: [Masked]\n\n### Format Instructions:\nGenerate a JSON object filling in the Masked values for N questions. For single-choice questions give the option position and text; for numeric questions give one number.\n{ "Q1": {"Question Type": "Single Choice", "Answers": {"SelectedByPosition": "Masked", "SelectedText": "Masked"}}, ... }')
P('C2 field test: system prompts and task.', bold=True)
MONO('Persona arm: ' + grab(c2, 'HEAD') + '<14 demographic attributes>\nNo-persona arm: ' + grab(c2, 'NOPERSONA'))
MONO('User message: You are scrolling through your social media news feed and see the following versions of the same article promoted by a media site. Each version would be shown to different readers. For each version, estimate the probability (0 to 100) that YOU would click on it if it appeared in your feed. Reply with only a JSON object mapping each letter to a number, for example {"A": 12, "B": 30}.\nA. <headline> (<excerpt>)\nB. ...   (variant order shuffled per call)')
P('Common call settings: temperature 0.7 unless a study varies it; reasoning effort "low" unless varied; one draw per respondent (five draws per test in C2); maximum output tokens 1,500 to 6,000 depending on the study; JSON object parsed from the first brace to the last.')

H('B2. Stimuli (confirmatory booklet, nine items)', 2)
os.environ['C1_DRY'] = '1'; sys.argv = ['run_c1', D, os.path.join('/tmp', '_c1unused_app'), '600']
ns = {'__name__': 'c1lib', '__file__': os.path.join(ROOT, 'pilot', 'run_c1.py')}; exec(open(ns['__file__']).read(), ns); STIM = ns['STIM']
P('Each respondent saw all nine items in random order, each in one randomly assigned condition. Human benchmark conditions were identical in wording. Text below is the question as shown, with options in order.')
for (item, cond), qs in sorted(STIM.items()):
    for qi, (txt, opts) in enumerate(qs):
        P(f'{item} / {cond}' + (f' / question {qi + 1}' if len(qs) > 1 else ''), bold=True, size=9.5)
        MONO(txt + ('\n' + '\n'.join(f'  ({i}) {o}' for i, o in enumerate(opts, 1)) if opts else '\n  (numeric entry)'))
H('B3. Persona architectures', 2)
P('Demographics only: the 14 attributes region, sex assigned at birth, age group, education, race or origin, US citizenship, marital status, religion, religious-service attendance, party identification, family income, political views, household size, and employment status, as answered in wave 1 of Twin-2K-500. Persona summary: the text description of the participant released with Twin-2K-500 ("persona_summary", about 13,000 characters, generated from wave 1 to 3 answers). Theory-explicit: the demographic profile plus the research note in B1. No-persona (C2 only): no individual attributes.')
H('B4. Factual battery', 2)
sys.path.insert(0, os.path.join(ROOT, 'pilot')); from h6_battery import ANSWERABLE, INVENTED, INVENTED2, ABSTAIN
P('Battery A (26 items, abstain option "' + ABSTAIN + '" last, instruction to choose it if unsure): 16 answerable items with keyed answers and 10 invented-entity items for which the abstain option is the only correct answer. Battery B (10 further invented items): same options, no abstention instruction.')
TAB(pd.DataFrame([[q, ' | '.join(o), k] for q, o, k in ANSWERABLE], columns=['Answerable item', 'Options', 'Key']), caption='Table B1. Answerable items.')
TAB(pd.DataFrame([[q, ' | '.join(o), 'Battery A'] for q, o in INVENTED] + [[q, ' | '.join(o), 'Battery B'] for q, o in INVENTED2], columns=['Invented-entity item', 'Options', 'Battery']), caption='Table B2. Invented-entity items (correct answer: abstain).')
H('B5. Models', 2)
ms = {m['id']: m for m in requests.get('https://openrouter.ai/api/v1/models', timeout=30).json()['data']}
use = [('anthropic/claude-haiku-4.5', 'S'), ('anthropic/claude-haiku-5.5', 'E1 E2 C1 H6c C2 S'), ('anthropic/claude-sonnet-5', 'S'), ('anthropic/claude-sonnet-5.5', 'S'), ('openai/gpt-5.2', 'S'), ('openai/gpt-5.4', 'S'), ('openai/gpt-5.5', 'S'),
       ('openai/gpt-5.6-luna', 'E1 E2 C1 H6c C2 S'), ('google/gemini-3.5-flash', 'S'), ('google/gemini-3.6-flash', 'S'), ('google/gemini-3.7-flash', 'E1 E2 C1 H6c C2 S'), ('x-ai/grok-4.3', 'E1 E2 C1 H6c C2 S'), ('x-ai/grok-4.5', 'S'), ('x-ai/grok-4.7', 'S'), ('meta-llama/llama-4-maverick', 'E1 C1 C2 S')]
rows = [[k, datetime.datetime.fromtimestamp(ms[k]['created'], datetime.timezone.utc).date().isoformat(), f"{float(ms[k]['pricing']['prompt']) * 1e6:.2f} / {float(ms[k]['pricing']['completion']) * 1e6:.2f}", u] for k, u in use]
TAB(pd.DataFrame(rows, columns=['Model identifier (API aggregator)', 'Listed release date', 'USD per million tokens (in / out)', 'Studies']), caption='Table B3. Models. All calls were made on 26 October 2026 through one API aggregator; the underlying provider was selected by the aggregator and not recorded per call.')
P('Reasoning effort was passed as the aggregator\'s unified "reasoning effort" parameter. Claude Haiku 5.5, GPT-5.6 luna, and Grok 4.3 accepted none, low, and high. Gemini 3.7 Flash rejected "none" (reasoning cannot be disabled); its levels in H6c are low, medium, high. Llama 4 Maverick has no reasoning mode and was excluded from the reasoning grid.')

# ---------------- C
H('C. Pre-registrations and deviation log')
for title, f in [('C1. AsPredicted #320110 (answers as submitted)', os.path.join(ROOT, 'prereg', 'ASPREDICTED_ANSWERS.md')), ('C2. AsPredicted #320124 (answers as submitted; overlapping with #320110)', os.path.join(ROOT, 'prereg', 'ASPREDICTED_2_ANSWERS.md'))]:
    H(title, 2)
    for para in md_text(f).split('\n'):
        if para.strip(): MONO(para) if False else P(para, size=9.5)
H('C3. Amendment note and pre-run clarifications', 2)
for f in ['AMENDMENT_1.md']:
    for para in md_text(os.path.join(ROOT, 'prereg', f)).split('\n'):
        if para.strip(): P(para, size=9.5)
H('C4. Longer working version of the registration', 2)
for para in md_text(os.path.join(ROOT, 'prereg', 'PREREGISTRATION_DRAFT.md')).split('\n'):
    if para.strip(): P(para, size=9.5)

# ---------------- D
H('D. Complete results')
H('D1. Study C1: twin effects, human benchmarks, discrepancies', 2)
c1 = pd.read_csv(R('c1', 'final_effects.csv')); c1 = c1.sort_values(['arch', 'item', 'model'])
TAB(pd.DataFrame({'Architecture': c1.arch, 'Effect': c1['item'], 'Model': c1.model.str.split('/').str[1], 'Twin': c1.twin.map(fmt), 'Human': c1.human.map(fmt), 'D': c1.D.map(fmt), 'D 95% CI': [f'{fmt(a)} to {fmt(b)}' for a, b in zip(c1.D_lo, c1.D_hi)]}), size=8,
    caption='Table D1. C1 effects (default effects in percentage points; attraction in log odds; other effects in standardized units of Table 3 of the manuscript). D = twin minus human; interval from 1,000 respondent bootstrap resamples.')
pr = pd.read_csv(R('c1', 'final_propositions.csv'))
TAB(pd.DataFrame({'Test': pr.test, 'Pooled': pr.pooled.map(lambda x: fmt(x, 3)), '95% CI': [f'{fmt(a, 3)} to {fmt(b, 3)}' for a, b in zip(pr.ci_lo, pr.ci_hi)], 'Models in direction': pr.models_in_predicted_direction, 'p (boot)': pr.p_boot.map(lambda x: fmt(x, 3)), 'q (BH)': pr.q_BH.map(lambda x: fmt(x, 4)), 'Verdict': pr.verdict_unadjusted}), size=8, caption='Table D2. C1 registered propositions and robustness checks.')
H('D2. Study H6c: reasoning grid cells', 2)
hc = pd.read_csv(R('h6c', 'final_cells.csv')).sort_values(['model', 'level', 'temp'])
TAB(pd.DataFrame({'Model': hc.model.str.split('/').str[1], 'Effort': hc.effort, 'Temp': hc.temp, 'n': hc.n_book, 'Framing d': hc.frame.map(fmt), 'Attraction': hc.attraction.map(fmt), 'Anch. Africa': hc.anch_africa.map(fmt), 'Anch. redwood': hc.anch_redwood.map(fmt), 'Bias index': hc.bias_idx.map(fmt), 'Error': hc.err.map(lambda x: fmt(x, 3)), 'Fabr. A': hc.fabA.map(lambda x: fmt(x, 3)), 'Fabr. B': hc.fabB.map(lambda x: fmt(x, 3))}), size=7.5, caption='Table D3. H6c cell estimates (100 respondents per cell).')
hp = pd.read_csv(R('h6c', 'final_propositions.csv'))
TAB(pd.DataFrame({'Test': hp.test, 'Coefficient': hp.coef.map(lambda x: fmt(x, 3)), '95% interval': [f'{fmt(a, 3)} to {fmt(b, 3)}' for a, b in zip(hp.ci_lo, hp.ci_hi)], 'Models in direction': hp.models_negative, 'Verdict': hp.verdict}), size=8, caption='Table D4. H6c registered tests.')
H('D3. Study C2: field test', 2)
c2s = pd.read_csv(R('c2', 'final2_summary.csv')).sort_values(['model', 'arm', 'cue'])
TAB(pd.DataFrame({'Model': c2s.model.str.split('/').str[1], 'Arm': c2s.arm, 'Cue-contrast': c2s.cue, 'Tests': c2s.tests, 'Significant tests': c2s.sig_tests, 'Agreement': c2s.agreement.map(lambda x: fmt(x, 3)), 'Chance': c2s.chance_sig.map(lambda x: fmt(x, 3)), 'Mean rho': c2s.mean_rho.map(lambda x: fmt(x, 3)), 'Raw slope': c2s.slope_pred_on_obs.map(lambda x: fmt(x, 3)), 'Disatt. slope': c2s.slope_disattenuated.map(lambda x: fmt(x, 3))}), size=7.5, caption='Table D5. C2 per-model summaries by arm and test class.')
cv = pd.read_csv(R('c2', 'final_verdicts.csv')); mc = [c for c in cv.columns if c.startswith('m_')]
TAB(pd.DataFrame({'Test': cv.test, 'Pooled': cv.pooled.map(lambda x: fmt(x, 3)), '95% CI': [f'{fmt(a, 3)} to {fmt(b, 3)}' for a, b in zip(cv.ci_lo, cv.ci_hi)], 'Models': cv.models_above_null, 'q (BH)': cv.q_BH.map(lambda x: fmt(x, 4)), 'Verdict': cv.verdict_unadjusted, **{c[2:]: cv[c].map(lambda x: fmt(x, 3)) for c in mc}}), size=7, caption='Table D6. C2 registered verdicts with per-model values.')
P('Cue-contrast rule: digit present; question mark; word from the lexicon {worst, terrible, horrible, tragic, shocking, disgusting, awful, scary, never, stop, dangerous, fail(s/ed), lose/lost/losing, dead, death, kill(s), hate, angry, outrage, crisis, nightmare, ruin(ed)}; second-person pronoun (you, your, yours). A test is cue-contrast if the headline arms disagree on at least one of the four features.')
H('D4. Study S: validity levels and stability', 2)
s = pd.read_csv(R('s', 'res_cells.csv')); lv = s.pivot_table(index=['model', 'template'], columns='item', values='level').reset_index()
TAB(pd.DataFrame({'Model': lv.model.str.split('/').str[1], 'Template': lv.template, **{c: lv[c].map(lambda x: '' if pd.isna(x) else int(x)) for c in lv.columns[2:]}}), size=7.5, caption='Table D7. Validity level per model, template, and effect (2 = magnitude-valid, 1 = direction-valid, 0 = invalid).')
tw = s.pivot_table(index=['model', 'template'], columns='item', values='twin').reset_index()
TAB(pd.DataFrame({'Model': tw.model.str.split('/').str[1], 'Template': tw.template, **{c: tw[c].map(lambda x: fmt(x)) for c in tw.columns[2:]}}), size=7.5, caption='Table D8. Twin effect estimates in Study S (human benchmarks in Table 3).')
P(open(R('s', 'analysis.txt')).read().split('Validity level by effect')[0].strip() + '\n' + 'Stability statistics: ' + '\n'.join(l for l in open(R('s', 'analysis.txt')).read().splitlines() if l.startswith(('Template stability', '  model', '  effect', '  template', '  residual', '  model main'))), size=8.5)
H('D5. Exploratory studies E1 and E2', 2)
e1 = pd.read_csv(R('e1', 'res_final.csv'))
TAB(e1.round(2).fillna(''), size=8, caption='Table D9. E1 twin effects by model and architecture (template A; defaults in points, attraction in log odds, fairness d). Human row first.')
P(open(R('e2', 'analysis_final.txt')).read().split('OLS with model fixed effects')[1][:900].strip(), size=8.5)
P('The exploratory H6 pilot pointed to a positive relation between reasoning level and bias and a negative within-cell correlation of bias with error; the confirmatory grid H6c replicates the first and the second at smaller size (Section 4.3 of the manuscript).', italic=True)

# ---------------- E
H('E. Data quality, exclusions, and known issues')
for t_ in [
 'Invalid responses (not parseable JSON or out-of-range option) are excluded and counted. In C1, the Llama 4 Maverick persona-summary cell excluded 85 of 600 responses (14%), above the registered 10% flag; two Llama theory-explicit and four GPT-5.6 luna persona-summary responses were also excluded; all other C1 cells had no exclusions. In Study S, Claude Haiku 4.5 with template A excluded 97 of 200 responses (49%) and with template B 13 of 200; its template A estimates should not be interpreted.',
 'E1 lacks 441 planned calls because of repeated upstream rate-limit failures for Llama 4 Maverick. Retries were attempted up to five times per call and a second pass filled most failed calls.',
 'The raw condition tag (EmbeddedData "target") in the targeting-fairness mega-study file is inverted relative to the survey text shown to participants. All analyses code conditions from the displayed text.',
 'An indexing error in our Benjamini–Hochberg routine was found after the C2 evaluation (a p-value of 0.66 received q = 0.001). It was corrected and C1 and C2 were recomputed; no verdict changed. The corrected code and results are in the repository, and the history documents the sequence.',
 'The Upworthy archive version used (December 2020 files) has no randomization-risk flag; tests created from 2013-06-25 to 2014-01-10 were excluded by date. The archive is public and could be partly present in model training data.',
 'The aggregator selects the serving provider; provider identity, quantization, and routing were not controlled or recorded. Reasoning-effort semantics differ across providers.',
 'Human benchmark intervals for loss framing and the two anchoring items come from the Twin-2K-500 repeat wave (wave 4); the interval for targeting fairness is an approximate Cohen\'s d interval computed from the group sizes.']:
    P('• ' + t_, size=10)

# ---------------- F
H('F. Code, data, and disclosures')
P('Repository contents (see README in the code package): pilot/ (runners and analysis scripts), benchmarks/ (human-benchmark computation), prereg/ (registrations, amendment, working document), results/ (summary tables), paper_src/ (manuscript source). Raw model outputs (JSON lines, about 300 MB uncompressed, 18 MB compressed) are provided as a separate archive. Human data are public and are not redistributed: Twin-2K-500 (CC BY 4.0, huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500), the Twin-2K-500 mega-study (Apache-2.0, huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500-Mega-Study), and the Upworthy Research Archive (OSF project jd64p).')
P('Reproduction: (1) download the public datasets; (2) python3 benchmarks/compute_human_benchmarks.py <data_dir> <data_dir> to recompute human benchmarks; (3) run the study runners in pilot/ (they need an API key for an LLM aggregator and write JSON-lines files); (4) run the matching analyze_*.py scripts; (5) node paper_src/make.js to rebuild the manuscript. Analysis scripts for confirmatory studies were committed before their outputs were analyzed (see commit history).')
P('Software: Python 3.13 (pandas, numpy, scipy, requests, pyarrow, python-docx), Node.js with docx. Random seeds: 2026 (respondent draws, C2 test draw, bootstrap), 11 (C2 development draw), 2027 (Study S respondent draw).')
P('Human subjects: no new human-subject data were collected; all human data are public secondary data. Institutional determination of exemption: [to be completed by the authors].')
P('Disclosure of AI assistance: an AI model (Anthropic Claude) assisted with study design discussion, writing the simulation and analysis code, running analyses, and drafting the manuscript and this appendix. The authors are responsible for the content and should verify every number against the repository before submission: [to be confirmed by the authors in line with journal policy].')
doc.save(OUT); print('saved', OUT)
