"""Decode a Claude Docs docx export and format the two display equations."""
import sys, json, base64
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
src, out = sys.argv[1], sys.argv[2]
j = json.loads(open(src).read())
def find(o):
    if isinstance(o, dict):
        for v in o.values():
            if isinstance(v, str) and len(v) > 10000: return v
            r = find(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = find(v)
            if r: return r
open(out, 'wb').write(base64.b64decode(find(j)))
doc = Document(out)
EQ1 = [('Y', 'i'), ('ij', 'si'), (' = β · Disclose', ''), ('ij', 'si'), (' + γ′', ''), ('X', 'i'), ('ij', 'si'), (' + μ', ''), ('m(j), o(j)', 'si'),
       (' + θ', ''), ('c(i)', 'si'), (' + λ', ''), ('l(i)', 'si'), (' + ε', ''), ('ij', 'si')]
EQ2 = [('[ ', ''), ('p', 'i'), ('(', ''), ('Q', 'i'), ('y', 'si'), (' ', ''), ('B', 'i'), ('n', 'si'), (') + ', ''), ('p', 'i'), ('(', ''), ('Q', 'i'), ('n', 'si'), (' ', ''), ('B', 'i'), ('y', 'si'),
       (') ]', ''), ('Q→B', 's'), ('  =  [ ', ''), ('p', 'i'), ('(', ''), ('B', 'i'), ('n', 'si'), (' ', ''), ('Q', 'i'), ('y', 'si'), (') + ', ''), ('p', 'i'), ('(', ''), ('B', 'i'), ('y', 'si'),
       (' ', ''), ('Q', 'i'), ('n', 'si'), (') ]', ''), ('B→Q', 's')]
k = 0
for para in doc.paragraphs:
    t = para.text.strip()
    eq = EQ1 if t.startswith('Y_{ij}') else EQ2 if t.startswith('\\big[p(Q_y') else None
    if not eq: continue
    for r in list(para.runs): r._element.getparent().remove(r._element)
    for txt, st in eq:
        run = para.add_run(txt); run.font.name = 'Cambria Math'; run.italic = 'i' in st; run.font.subscript = 's' in st
    k += 1; n = para.add_run('\t(%d)' % k); n.font.name = 'Cambria Math'
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = para._p.get_or_add_pPr()
    for shd in pPr.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd'): pPr.remove(shd)
doc.save(out); print('saved', out, 'equations', k)
