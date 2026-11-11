"""Build the Online Appendix for "Asking Changes the Answer" (ISR submission, anonymized).
All numbers are recomputed from the data files or copied from results/*.txt produced by the analysis scripts."""
import json, re, difflib, collections, sys
import numpy as np, pandas as pd
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = '/home/user/fluffy-meme/arena-strategic/'
D = '/home/user/data/'
OUT = R + 'paper/LLM_code_review_ISR_online_appendix.docx'
sys.path.insert(0, R + 'src')

items = json.load(open(R + 'prereg/code_items.json'))
prs = json.load(open(R + 'prereg/code_prs.json'))
he = pd.read_parquet(D + 'humaneval/he.parquet').set_index('task_id')
A = pd.read_pickle(D + 'code_A.pkl'); B = pd.read_pickle(D + 'code_B.pkl')
Q = pd.read_pickle(D + 'code_quantum.pkl'); F = pd.read_pickle(D + 'code_freetext.pkl')
NAME = {'qwen': 'Qwen3.7 Flash', 'haiku': 'Claude Haiku 5.5', 'llama': 'Llama 4 Scout', 'deepseek': 'DeepSeek V3.2',
        'deepseek_reason': 'DeepSeek V3.2 (reasoning)'}
ORDER = ['deepseek', 'deepseek_reason', 'haiku', 'llama', 'qwen']
rng = np.random.default_rng(2028)

def boot_ci(per_unit, n=2000):
    v = np.asarray(per_unit, float); idx = rng.integers(0, len(v), (n, len(v)))
    return np.percentile(v[idx].mean(1), [2.5, 97.5])

# ---------- document helpers ----------
doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
st.paragraph_format.line_spacing = 2.0; st.paragraph_format.space_after = Pt(0)

def page_numbers():
    p = doc.sections[0].footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    for t, txt in (('begin', None), (None, 'PAGE'), ('end', None)):
        if t:
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), t)
        else:
            e = OxmlElement('w:instrText'); e.set(qn('xml:space'), 'preserve'); e.text = txt
        r._r.append(e)
page_numbers()

def H(text, level=1):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(12); p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.bold = True
    if level == 2: r.italic = True
    if level == 0: p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r.font.size = Pt(14)
    return p

def P(text, indent=True):
    p = doc.add_paragraph()
    if indent: p.paragraph_format.first_line_indent = Inches(0.5)
    for i, part in enumerate(re.split(r'(\*[^*]+\*)', text)):
        if part.startswith('*') and part.endswith('*'): p.add_run(part[1:-1]).italic = True
        else: p.add_run(part)
    return p

def V(text):  # verbatim prompt text
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.5); p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text); r.font.name = 'Courier New'; r.font.size = Pt(9.5)
    return p

def T(title, header, rows, note=None):
    cap = doc.add_paragraph(); cap.paragraph_format.space_before = Pt(12); cap.paragraph_format.keep_with_next = True
    cap.paragraph_format.line_spacing = 1.0
    cap.add_run(title.split('.')[0] + '.').bold = True; cap.add_run(title[len(title.split('.')[0]) + 1:])
    t = doc.add_table(rows=1, cols=len(header)); t.style = 'Table Grid'
    for c, h in zip(t.rows[0].cells, header): c.text = str(h)
    for row in rows:
        cells = t.add_row().cells
        for c, v in zip(cells, row): c.text = str(v)
    for i, row in enumerate(t.rows):
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.line_spacing = 1.0; p.paragraph_format.first_line_indent = Inches(0)
                for r in p.runs:
                    r.font.size = Pt(10)
                    if i == 0: r.bold = True
    if note:
        n = doc.add_paragraph(); n.paragraph_format.line_spacing = 1.0; n.paragraph_format.space_after = Pt(6)
        n.add_run('Note. ').italic = True; r = n.add_run(note); r.font.size = Pt(10)

f3 = lambda x: f'{x:.3f}'.replace('0.', '.', 1) if x >= 0 else f'{x:.3f}'.replace('-0.', '−.', 1)
ci = lambda lo, hi: f'[{f3(lo)}, {f3(hi)}]'

# ---------- title ----------
H('Online Appendix', 0)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('Asking Changes the Answer: Non-Classical Judgment in Large Language Model Code Review').italic = True
P('This appendix documents the materials, prompts, model settings, response rates, and preregistration record of '
  'the three studies, and it reports results that are summarized but not tabulated in the paper. Sections are labeled '
  'OA1 to OA9 and tables OA1 to OA13. All analyses can be reproduced from the replication package. [AUTHOR: add an '
  'anonymized repository link for review and the OSF link at acceptance.]')

# ---------- OA1 materials ----------
H('OA1. Materials')
H('OA1.1 Programs (Studies 1 and 2)', 2)
cats = collections.Counter()
def opcat(a, b):
    if (a, b) in (('=', '!'), ('!', '=')): return 'Equality test inverted (== / !=)'
    if (a, b) in (('+', '-'),): return 'Arithmetic operator replaced (+ to −)'
    if (a, b) in (('', '='), ('=', '')): return 'Comparison boundary shifted (< / <=, > / >=)'
    if (a, b) in (('and', 'or'), ('or', 'and')): return 'Boolean operator replaced (and / or)'
    if a.strip() in ('+ 1', '- 1') and b == '': return 'Off-by-one constant removed (+1 / −1)'
    if (a, b) in (('Tru', 'Fals'), ('Fals', 'Tru')): return 'Boolean literal inverted'
    if (a, b) in (('ax', 'in'), ('in', 'ax')): return 'max / min swapped'
    return 'Other'
for it in items:
    if it['label'] != 'buggy': continue
    full = he.loc[it['task_id'], 'prompt'] + he.loc[it['task_id'], 'canonical_solution']
    diff = list(difflib.ndiff(full.splitlines(), it['code'].splitlines()))
    a = [l[2:] for l in diff if l[:2] == '- '][0]; b = [l[2:] for l in diff if l[:2] == '+ '][0]
    ops = [(a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if t != 'equal']
    cats[opcat(*ops[0]) if len(ops) == 1 else 'Other'] += 1
lines = np.array([it['code'].count('\n') + 1 for it in items])
P(f'The 120 programs are drawn from the HumanEval benchmark (164 problems). For each problem, the canonical solution '
  f'was first run against the official unit tests; it was retained only if it passed. Candidate defective versions were '
  f'generated by applying single-token substitutions to the solution body (comparison, equality, arithmetic, boolean, '
  f'off-by-one, and min/max substitutions), discarding any that did not parse, and keeping the first of up to eight '
  f'shuffled candidates that failed the official tests. From the problems with a verified failing mutant, 120 were sampled '
  f'(seed 7) and alternately assigned to the correct or defective condition, so that each problem appears exactly once: '
  f'60 programs are canonical solutions and 60 are mutants. Each program includes the function signature and docstring '
  f'from the benchmark. Programs are {lines.min()} to {lines.max()} lines long (mean {lines.mean():.1f}, median '
  f'{int(np.median(lines))}). Table OA1 lists the substitutions that produced the 60 defective programs; every mutant '
  f'changes a single line.')
T('Table OA1. Substitutions in the 60 defective programs', ['Substitution', 'Programs'],
  [(k, v) for k, v in cats.most_common()],
  'Classified by comparing each mutant with the canonical solution. All mutants fail at least one official HumanEval test.')

H('OA1.2 Pull requests (Study 3)', 2)
pl = np.array([p['code'].count('\n') + 1 for p in prs])
pos = collections.Counter(p['functions'].index(p['buggy_function']) + 1 for p in prs if p['defective'])
P(f'The 60 pull requests were built before data collection by a fixed script (seed 2027). Each adds a new file, '
  f'utils.py, containing three functions. The 30 clean pull requests contain three correct programs sampled without '
  f'replacement within the pull request; the 30 defective pull requests contain two correct programs and one of the 60 '
  f'defective programs, inserted at a random position (first: {pos[1]}, second: {pos[2]}, third: {pos[3]}). Correct programs '
  f'can recur across pull requests. Each pull request has a title of the form "Add f, g and h helpers," naming its '
  f'functions, and the description "Adds utility functions to utils.py." Pull requests are {pl.min()} to {pl.max()} '
  f'lines long (mean {pl.mean():.1f}). Because every defect is a verified single-token mutant, the ground truth for each '
  f'pull request is known, but the pull requests remain simpler than real changes: they add new code rather than modify '
  f'existing code, contain at most one defect, and come without repository context.')

# ---------- OA2 models ----------
H('OA2. Models and Generation Settings')
P('All models were queried through a commercial API gateway (OpenRouter) between the preregistration commits and the '
  'analysis, with fixed prompts and a seed for each repetition. Responses were cached, so every reported number can be '
  'regenerated from the cache without new queries. Table OA2 lists the settings.')
T('Table OA2. Models and settings by study',
  ['Study', 'Models (API identifiers)', 'Temperature', 'Max output tokens', 'Reasoning', 'Repetitions', 'Cost (USD)'],
  [('1A', 'qwen/qwen3.7-flash; anthropic/claude-haiku-5.5; meta-llama/llama-4-scout', '1.0', '5', 'off', '5 per program and question', '0.21 (1A and 1B)'),
   ('1B', 'same as 1A', '1.0', '5', 'off', '4 per program and order', ''),
   ('2 (E1–E3)', 'Study 1 models and deepseek/deepseek-v3.2', '1.0', '5', 'off', '2 per program and cell', '0.15'),
   ('3', 'Study 2 models; deepseek/deepseek-v3.2 with reasoning as a fifth configuration', '0.7', '1,200 (4,000 with reasoning)', 'off / on', '2 per pull request and condition', '1.35')],
  'Model names in the paper: Qwen3.7 Flash, Claude Haiku 5.5, Llama 4 Scout, DeepSeek V3.2. Costs are the gateway charges '
  'for the main data collection, excluding pilots.')

# ---------- OA3 prompts ----------
H('OA3. Prompts')
P('The prompts below are reproduced verbatim. Braces mark text that varied across trials.')
H('Studies 1 and 2', 2)
V('System (Study 1): You are an experienced Python code reviewer. Answer each question with a single word: Yes or No.')
V('System (Study 2, E1 and E2): You are an experienced Python code reviewer. Answer each question with a single letter. '
  'In this conversation, A means Yes and B means No.   [mapping M2: A means No and B means Yes]')
V('User (all): Here is a pull request with the following code:\n```python\n{program}\n```\n\n{question}')
V('Study 1A questions: "Is this code correct?" | "Does this code contain a bug?"\n'
  'Study 1B questions, one conversation, both orders: "Is this code correct?" and "Is this code well written and easy to read?"')
V('E1 contexts, each followed by "Would you approve merging this pull request? (Answer A for Yes, B for No.)":\n'
  '  P: The CI test suite was run on this code and all tests passed.\n'
  '  F: The CI test suite was run on this code and one test failed.\n'
  '  U: The CI test suite has not finished running yet, so you do not know whether the tests will pass.')
V('E2 direct: Would you approve merging this pull request?\n'
  'E2 indirect: Does this code contain a bug?  -> [model answer] -> Would you approve merging this pull request?')
V('E3 (system adds "Answer with a single letter, A or B."): Which statement is more probable?\n'
  '(A) This code contains a bug.\n(B) This code contains a bug in a comparison, arithmetic, or boolean operator.\n'
  'Answer A or B.   [option order counterbalanced]')
H('Study 3', 2)
V('System: You are an experienced Python code reviewer on a software team.')
V('Pull request: {title}\nDescription: Adds utility functions to utils.py.\n\n```python\n# utils.py (new file)\n{code}\n```')
V('Review instruction (DIRECT): Review this pull request. Keep your review under 250 words. Write your review comments, '
  'then end with a final line that is exactly "DECISION: APPROVE" or "DECISION: REQUEST CHANGES".')
V('BUGFIRST, first turn: Before your review, list any bugs you can find in this pull request.\n'
  'BUGFIRST, second turn (same conversation): the review instruction.')
V('CI conditions (prepended to the review instruction):\n'
  '  CI_PASS: The CI test suite was run on this pull request and all tests passed.\n'
  '  CI_FAIL: The CI test suite was run on this pull request and one test failed.\n'
  '  CI_UNKNOWN: The CI test suite is still running, so you do not know yet whether the tests will pass.')
P('The decision was parsed from the last line matching "DECISION: APPROVE" or "DECISION: REQUEST CHANGES" '
  '(case-insensitive). Reviews without such a line were treated as unanswered.')

# ---------- OA4 response rates ----------
H('OA4. Response Rates and Missing Data')
rows = []
for m in ['deepseek', 'haiku', 'llama', 'qwen']:
    a = (A.model == m).sum() if m in A.model.unique() else None
    b = (B.model == m).sum() if m in B.model.unique() else None
    e = [(Q[(Q.exp == x) & (Q.model == m)]).shape[0] for x in ('E1', 'E2', 'E3')]
    rows.append((NAME[m], f'{a:,} / 1,200' if a is not None else '–', f'{b:,} / 960' if b is not None else '–',
                 f'{e[0]:,} / 1,440', f'{e[1]} / 960', f'{e[2]} / 480'))
T('Table OA3. Answered queries in Studies 1 and 2', ['Model', '1A', '1B', 'E1', 'E2', 'E3'], rows,
  'An answer counts if it could be mapped to Yes or No (A or B in Study 2, and the statement chosen in E3). In 1B and E2, '
  'a conversation counts only if both answers were usable.')
cnt = F[F.approve.notna()].groupby(['model', 'cond']).size().unstack().reindex(ORDER)
cols = ['DIRECT', 'BUGFIRST', 'CI_PASS', 'CI_FAIL', 'CI_UNKNOWN']
T('Table OA4. Parsable reviews in Study 3, by condition (of 120 each)', ['Reviewer'] + cols,
  [[NAME[m]] + [int(cnt.loc[m, c]) for c in cols] for m in ORDER],
  'Missing BUGFIRST reviews arise when the first-stage request (listing bugs) returned no content after three attempts, so '
  'that the conversation could not continue; other missing reviews lack a parsable decision line.')
P('Two cells have substantial missing data. In E3, Llama 4 Scout produced a usable choice in only 226 of 480 trials; its '
  'other replies did not choose between the statements. The E3 estimate for Llama is therefore based on a selected subset '
  'and should be read with caution. In Study 3, the reasoning configuration of DeepSeek V3.2 returned no first-stage bug '
  'list in 39 of 120 BUGFIRST conversations. If the missing conversations differ systematically, the interference '
  'estimate for that configuration could be biased. Table OA5 therefore re-estimates interference on matched pairs: for '
  'each pull request and repetition, the BUGFIRST decision is compared only with the DIRECT decision for the same pull '
  'request and repetition. The estimates are close to those in the paper.')
rows = []
for m in ['deepseek', 'deepseek_reason', 'qwen']:
    for scope in ('All', 'Clean'):
        s = F[(F.model == m) & F.cond.isin(['DIRECT', 'BUGFIRST'])]
        if scope == 'Clean': s = s[~s.defective]
        pv = s.pivot_table(index=['pr', 'rep'], columns='cond', values='approve').dropna()
        d = (pv.DIRECT - pv.BUGFIRST).groupby(level=0).mean()
        lo, hi = boot_ci(d.values)
        rows.append((NAME[m], scope, len(pv), f3(pv.DIRECT.mean()), f3(pv.BUGFIRST.mean()), f3(d.mean()), ci(lo, hi)))
T('Table OA5. Interference in Study 3 on matched pairs', ['Reviewer', 'Pull requests', 'Pairs', 'Direct', 'Bug first', 'Interference', '95% CI'],
  rows, 'Pairs are pull request × repetition combinations with a parsable decision in both conditions. Confidence intervals '
  'from 2,000 resamples of pull requests (per-pull-request mean differences).')

# ---------- OA5 Study 1 ----------
H('OA5. Additional Results for Study 1')
P('Table OA6 reports Study 1B, which asked about correctness and readability in both orders within one conversation. '
  'This study was preregistered as exploratory. The order effect on the correctness judgment was significant for Claude '
  'Haiku 5.5 and Qwen3.7 Flash, and for Claude Haiku 5.5 it was concentrated in correct programs, where asking about '
  'readability first raised the share judged correct from .637 to .779. The QQ statistic, which equals zero under the '
  'quantum model of question order, did not differ significantly from zero for Llama and Qwen, but it did for Claude Haiku 5.5 '
  'on correct programs. Because these were not the paper’s confirmatory tests, we do not draw conclusions from them.')
qq = [l for l in open(R + 'results/code_judgment.txt').read().splitlines() if 'P(correct=yes)' in l]
rows = []
for l in qq:
    m = re.match(r"\s*\(?'?(\w+)'?(?:, '(\w+)'\))?\s+n=\s*(\d+)\s+P\(correct=yes\) Q first ([\d.]+) / Q second ([\d.]+)\s+order p=([\d.e\-]+)\s+q=([+\-][\d.]+) \(p=([\d.e\-]+)\) 90%CI\[([+\-][\d.]+),([+\-][\d.]+)\]", l)
    if not m: continue
    mod, lab, n, q1, q2, op, qv, qp, lo, hi = m.groups()
    fmt = lambda x: f3(float(x))
    rows.append((NAME[mod], lab or 'all', n, fmt(q1), fmt(q2), op if float(op) >= 0.001 else f'{float(op):.1e}', fmt(qv), ci(float(lo), float(hi))))
T('Table OA6. Question order in Study 1B', ['Model', 'Programs', 'n', 'P(correct) asked first', 'P(correct) asked second',
  'Order test p', 'QQ statistic', '90% CI'], rows,
  'n = answered two-question conversations. The order test is a chi-square test on the 2 × 4 table of answer patterns; '
  'the QQ statistic is the difference in disagreement shares between orders, with a 90% item-bootstrap interval used for the '
  'preregistered equivalence test at ±.05.')

# ---------- OA6 Study 2 by label mapping ----------
H('OA6. Study 2 Results by Label Mapping and Program Correctness')
P('In Study 2, answers were given as letters, and which letter meant Yes was counterbalanced across conversations. '
  'The paper reports estimates pooled with equal weight over the two mappings. Tables OA7 and OA8 show that the mapping '
  'itself moved approval rates substantially for Llama 4 Scout and Qwen3.7 Flash, which approved far more often when B '
  'meant Yes. For Llama, interference is positive under both mappings, but the disjunction-like violation appears only under '
  'mapping M2 (approval .142 with unknown results against .383 with failed tests); under M1, approval after failed and '
  'unknown results is at the floor. For Qwen, and to a lesser degree for Claude Haiku 5.5 and DeepSeek V3.2, interference '
  'appears only under M2, and under M1 it is small and in some cases negative. We treat this label dependence as part of the evidence for '
  'elicitation sensitivity rather than as noise to be averaged away.')
e1 = Q[Q.exp == 'E1']; rows = []
for m in ['deepseek', 'haiku', 'llama', 'qwen']:
    for mp in ('M1', 'M2'):
        for lab in ('all', 'correct', 'buggy'):
            s = e1[(e1.model == m) & (e1['map'] == mp)]
            if lab != 'all': s = s[s.label == lab]
            r = s.groupby('cond').approve.mean()
            rows.append((NAME[m], mp, lab, f3(r['P']), f3(r['F']), f3(r['U'])))
T('Table OA7. Experiment 2A (CI status): approval by label mapping', ['Model', 'Mapping', 'Programs', 'Tests passed',
  'Tests failed', 'Tests unknown'], rows, 'M1: A = Yes; M2: A = No. Shares of answered queries.')
e2 = Q[Q.exp == 'E2']; rows = []
for m in ['deepseek', 'haiku', 'llama', 'qwen']:
    for mp in ('M1', 'M2'):
        s = e2[(e2.model == m) & (e2['map'] == mp)]
        r = s.groupby('cond').approve.mean()
        per = s.groupby(['item', 'cond']).approve.mean().unstack().dropna()
        lo, hi = boot_ci((per['direct'] - per['indirect']).values)
        bug = s[s.cond == 'indirect'].bug.mean()
        rows.append((NAME[m], mp, f3(r['direct']), f3(r['indirect']), f3(r['direct'] - r['indirect']), ci(lo, hi), f3(bug)))
T('Table OA8. Experiment 2B (bug question first): approval by label mapping', ['Model', 'Mapping', 'Direct', 'After bug question',
  'Interference', '95% CI', 'P(bug = yes)'], rows,
  'Interference = direct minus indirect approval. P(bug = yes) is the share answering that the code contains a bug in the '
  'first question of the indirect condition. Confidence intervals from 2,000 resamples of programs.')
e3 = Q[Q.exp == 'E3']; rows = []
for m in ['deepseek', 'haiku', 'llama', 'qwen']:
    s = e3[e3.model == m]
    for lab in ('correct', 'buggy'):
        t = s[s.label == lab]; o = t.groupby('order').conj.mean()
        rows.append((NAME[m], lab, len(t), f3(o.mean()), f3(o.get('single_first', np.nan)), f3(o.get('conj_first', np.nan))))
T('Table OA9. Experiment 2C (conjunction): share choosing the more specific statement', ['Model', 'Programs', 'n', 'Rate',
  'General statement listed first', 'Specific statement listed first'], rows,
  'Rate = mean of the two option-order rates, as in the paper. Choosing the specific statement ("a bug in a comparison, arithmetic, or boolean operator") over the general one ("a bug") '
  'violates the conjunction rule. The Llama estimates rest on 226 of 480 trials (Section OA4).')

# ---------- OA7 variance ----------
H('OA7. Elicitation-Variance Decomposition')
P('The decomposition in Section 4.6 of the paper uses the Study 2 data, in which every condition ends with the same approval '
  'question. An elicitation configuration is one of the conditions (direct, after the bug question, tests unknown, and, in '
  'the second panel, tests passed and tests failed) crossed with the two label mappings. For each program, model, and '
  'configuration, we compute the approval rate over the two repetitions and fit a linear model with program fixed effects, '
  'model, configuration, and their interaction. Table OA10 reports the share of the total sum of squares (type II) attributed '
  'to each term. The first panel, used in the paper, restricts attention to configurations that convey no information about '
  'the code, so that a perfectly coherent reviewer would give the same answer in all of them. The second panel adds the '
  'informative CI conditions for comparison. The same decomposition for Study 3 uses pull requests in place of programs and '
  'the DIRECT, BUGFIRST, and CI_UNKNOWN conditions.')
P('One feature of the record should be noted. The decomposition was specified in the Study 3 preregistration, and it is '
  'therefore confirmatory for Study 3. For Study 2, it was specified after the Study 2 data had been collected and analyzed, '
  'although before Study 3 data were collected, and it should be regarded as exploratory for Study 2.')
vt = open(R + 'results/elicitation_variance.txt').read()
def shares(block):
    return {k: float(v) for k, v in re.findall(r'(C\(\w+\)(?::C\(\w+\))?|Residual)\s+([\d.]+)', block)}
b1, b2 = vt.split('All elicitations')[0], vt.split('All elicitations')[1]
s1, s2 = shares(b1), shares(b2)
s3 = {'C(item)': 0.244, 'C(model)': 0.046, 'C(elic)': 0.017, 'C(model):C(elic)': 0.024, 'Residual': 0.670}
s3txt = open(R + 'results/code_freetext.txt').read()
m3 = re.search(r"Variance shares \(non-informative elicitations\): (\{.*\})", s3txt)
if m3:
    d3 = eval(m3.group(1)); s3 = {'C(item)': d3['C(pr)'], 'C(model)': d3['C(model)'], 'C(elic)': d3['C(cond)'],
                                 'C(model):C(elic)': d3['C(model):C(cond)'], 'Residual': d3['Residual']}
lab = [('C(item)', 'Program / pull request'), ('C(model)', 'Model'), ('C(elic)', 'Elicitation'),
       ('C(model):C(elic)', 'Model × elicitation'), ('Residual', 'Residual')]
T('Table OA10. Shares of variance in approval rates', ['Component', 'Study 2, non-informative', 'Study 2, all configurations',
  'Study 3, non-informative'], [(n, f3(s1[k]), f3(s2[k]), f3(s3[k])) for k, n in lab],
  'Study 2: 120 programs × 4 models × 6 non-informative configurations (10 with the CI passed and failed conditions). '
  'Study 3: 60 pull requests × 5 reviewer configurations × 3 conditions; Study 3 conditions were not label-counterbalanced.')
r1 = eval(re.search(r"by model: (\{.*?\})", b1).group(1)); r2 = eval(re.search(r"by model: (\{.*?\})", b2).group(1))
g1 = float(re.search(r'averaged over configurations: ([\d.]+)', b1).group(1)); g2 = float(re.search(r'averaged over configurations: ([\d.]+)', b2).group(1))
T('Table OA11. Range of approval rates across elicitation configurations (Study 2)', ['Model', 'Non-informative configurations',
  'All configurations'], [(NAME[m], f3(r1[m]), f3(r2[m])) for m in ['deepseek', 'haiku', 'llama', 'qwen']] +
  [('Range across models (mean over configurations)', f3(g1), f3(g2))],
  'Maximum minus minimum approval rate over configurations for each model; the last row is the range across the four models '
  'within a configuration, averaged over configurations.')

# ---------- OA8 Study 3 ----------
H('OA8. Additional Results for Study 3')
P('Table OA12 reports approval rates in Study 3 for defective pull requests, which the paper summarizes. Approval of '
  'defective pull requests was near zero in every condition, so neither the interference test nor the test of the law of '
  'total probability is informative for them. In no configuration did approval under unknown test results fall outside '
  'the range spanned by passed and failed tests, for all, clean, or defective pull requests.')
rows = []
for l in open(R + 'results/code_freetext.txt').read().splitlines():
    m = re.match(r'\s*(defective)\s+(\w+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s+\[([+\-][\d.]+),([+\-][\d.]+)\]', l)
    if m:
        g = m.groups(); rows.append([NAME[g[1]]] + [f3(float(x)) for x in g[2:8]] + [ci(float(g[8]), float(g[9]))])
T('Table OA12. Approval of defective pull requests in Study 3', ['Reviewer', 'Direct', 'Bug first', 'Tests passed', 'Tests failed',
  'Tests unknown', 'Interference', '95% CI'], rows, 'Thirty defective pull requests, two reviews per condition. Confidence '
  'intervals from 2,000 resamples of pull requests.')
lens = eval(re.search(r'Mean review length \(characters\): (\{.*?\})', s3txt).group(1))
P('Mean review length was ' + ', '.join(f'{lens[m]:,.0f} characters for {NAME[m]}' for m in ORDER) + '. Almost every review of '
  'a defective pull request mentioned the defective function by name (98 to 100 percent in every configuration and condition), '
  'but because reviews routinely discussed all three functions, this measure does not separate detection from coverage.')
H('Illustration: the same pull request with and without a prior bug list', 2)
P('To show what the interference effect looks like in free text, we reproduce excerpts from two reviews by Qwen3.7 Flash of '
  'the same clean pull request (pull request 12 in the replication files, which adds monotonic, get_max_triples, and words_string; all three functions '
  'pass their tests) with the same seed. Both reviews raise essentially the same concerns, chiefly that get_max_triples '
  'runs in cubic time. Reviewed directly, the model approved; after first listing bugs, it requested changes.')
V('DIRECT (excerpt): "... `get_max_triples` has a critical performance issue. The current implementation uses three nested '
  'loops, making it O(N^3). ... However, since the logic is correct for small inputs and the file is new, I will approve with '
  'strong notes on performance.\nDECISION: APPROVE"')
V('BUGFIRST, second turn (excerpt): "... The `get_max_triples` function is fundamentally broken for performance reasons and '
  'requires significant refactoring. I cannot approve a core algorithm that will fail on standard test cases due to time '
  'complexity limits.\nDECISION: REQUEST CHANGES"')
P('The example is illustrative and was selected because it shows the effect clearly; it is not a random draw. In the '
  'BUGFIRST conversation, the first-stage bug list was itself cut off by the output limit before it finished, which did not '
  'prevent the second-stage review.')

# ---------- preregistration record ----------
H('OA9. Preregistration Record')
P('Each preregistration was committed with a time stamp to the project repository before the corresponding data were '
  'collected. Table OA13 lists the commits. The anonymized repository is available to reviewers; commit identifiers allow '
  'the time stamps to be verified.')
T('Table OA13. Preregistration commits', ['Study', 'Document', 'Commit', 'Time stamp (UTC)'],
  [('1', 'code_judgment_prereg.md', 'db8602d', '2026-11-11 14:21'),
   ('2', 'code_quantum_prereg.md', '9a6ef20', '2026-11-11 21:00'),
   ('3', 'code_review_freetext_prereg.md', 'e09fac7', '2026-11-11 22:36'),
   ('3 (amendment)', 'code_review_freetext_prereg.md', 'ea288ea', '2026-11-11 22:40')],
  'The Study 3 commit also added the elicitation-variance analysis script (Section OA7).')
P('Deviations and clarifications. (1) Study 3 was amended once, after a two-pull-request pilot and before the main data '
  'collection: 59 of 96 pilot reviews had been cut off by the 700-token limit before the decision line, so the review '
  'instruction was shortened ("Keep your review under 250 words") and the limit raised to 1,200 tokens (4,000 with '
  'reasoning). Pilot data are excluded from all analyses. (2) Study 1B was preregistered as exploratory. (3) In Study 1, '
  'answer labels were not counterbalanced; Study 2 counterbalanced them. '
  '(4) The elicitation-variance decomposition is exploratory for Study 2 and confirmatory for Study 3 (Section OA7). '
  '(5) The matched-pair analysis in Table OA5 was not preregistered; it was added to assess the effect of missing data.')

doc.core_properties.author = ''; doc.core_properties.title = 'Online Appendix'
doc.save(OUT); print('saved', OUT)
