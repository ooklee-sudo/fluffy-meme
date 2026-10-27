"""Builds the title page (Word) and the raw-outputs zip. Cover letter: build_cover_letter.py. Replication package: build_replication.py. Usage: python3 build_front.py <scratch_dir_with_raw_outputs>"""
import sys, os, zipfile, gzip, shutil
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); SUB = os.path.abspath(os.path.join(HERE, '..')); SCR = sys.argv[1]
TITLE = 'When Can Marketers Trust Synthetic Consumers? Validity Regions and a Validation Protocol for LLM Digital Twins in Digital Experimentation'
def newdoc(size=12):
    d = Document(); s = d.sections[0]; s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    d.styles['Normal'].font.name = 'Times New Roman'; d.styles['Normal'].font.size = Pt(size); return d
def para(d, text, bold=False, italic=False, align=None, after=6):
    p = d.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic; p.paragraph_format.space_after = Pt(after)
    if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p
def bullets(d, items):
    for t in items: p = d.add_paragraph(style='List Bullet'); p.add_run(t)

# ---------------- title page (AMA format: FILE 1)
d = newdoc(); para(d, TITLE, bold=True, align='c', after=14)
para(d, 'Author(s): name, title, institution, address, telephone number, and email address', bold=True)
para(d, '[Author 1: full name, present position, department/school, university, postal address, telephone, email, ORCID]\n[Author 2: full name, present position, department/school, university, postal address, telephone, email, ORCID]')
para(d, 'Author\'s note', bold=True); para(d, '[Corresponding author and any author note, e.g., prior presentations or relation to dissertations.]')
para(d, 'Acknowledgments', bold=True)
para(d, 'Generative AI use: an AI model (Claude, Anthropic) wrote most of the simulation and analysis code, executed the analyses, and drafted the manuscript text under the authors\' direction. The AI model is not an author, and the authors are responsible for the content. This use is also identified in the main document. [Other acknowledgments to be added by the authors.]')
para(d, 'Statements and declarations', bold=True)
para(d, 'Ethical considerations: No new human-subject data were collected. All human data are public secondary data (Twin-2K-500 and its mega-study; Upworthy Research Archive). [Institutional determination of exemption to be added by the authors.]')
para(d, 'Consent to participate: Not applicable; no new participants were recruited. The simulated respondents are outputs of large language models.')
para(d, 'Declaration of conflicting interest: [The authors declared no potential conflicts of interest with respect to the research, authorship, and/or publication of this article. Authors to confirm or revise.]')
para(d, 'Funding statement: [The authors received no financial support / list funders.] Application-programming-interface compute for the simulations (about US$306) was paid by [the authors / institution].')
para(d, 'Data availability statement: The model outputs, prompts, and code that support the findings of this article are publicly available in [repository name] ([URL/DOI link; to be added when deposited]). The human benchmark data are publicly available from the Twin-2K-500 repositories on Hugging Face (CC BY 4.0; Apache-2.0 for the mega-study) and from the Upworthy Research Archive on the Open Science Framework (project jd64p).')
para(d, 'Preregistration: AsPredicted #320110 (twin study and reasoning grid) and AsPredicted #320124 (field test; overlapping amendment to #320110). Analysis code for the confirmatory studies was committed before the confirmatory outputs were analyzed.')
d.save(os.path.join(SUB, '01_Title_Page.docx'))


# ---------------- raw outputs zip
RAWREAD = '''Raw model outputs (JSON lines, gzip). One line per API call.
Fields: study-specific. Common: pid (Twin-2K-500 participant id, "pid_<n>"), model, effort/temp/arch/template/arm (where applicable), content (model response text), cost (USD), qs/conds (questions shown and condition assignment).
Files: E1 (E1_full_runs.jsonl.gz), E2 (E2_reasoning_pilot.jsonl.gz), C1, H6c, C2 (C2_field_confirmatory), C2dev (development run on the exploratory package), S (stability study). tests.json is the selected Upworthy tests (headlines, impressions, clicks) for C2 and C2dev.
Persona text is not included (Twin-2K-500 CC BY 4.0 data are available from the original source).
'''
rp = os.path.join(SUB, '06_Raw_Model_Outputs.zip')
with zipfile.ZipFile(rp, 'w', zipfile.ZIP_STORED) as z:
    z.writestr('README_RAW.txt', RAWREAD)
    for name, rel in [('E1_full_runs', 'full2'), ('E2_reasoning_pilot', 'h6'), ('C1_confirmatory_twin', 'c1'), ('H6c_reasoning_grid', 'h6c'), ('C2_field_confirmatory', 'c2conf'), ('C2dev_development', 'c2dev'), ('S_stability', 'gen')]:
        src = os.path.join(SCR, rel, 'raw.jsonl'); tmp = os.path.join('/tmp', name + '.jsonl.gz')
        with open(src, 'rb') as fi, gzip.open(tmp, 'wb', 9) as fo: shutil.copyfileobj(fi, fo)
        z.write(tmp, name + '.jsonl.gz'); os.remove(tmp)
        tj = os.path.join(SCR, rel, 'tests.json')
        if os.path.exists(tj): z.write(tj, name + '_tests.json')
print('built', [f for f in os.listdir(SUB) if not f.startswith('build')])
