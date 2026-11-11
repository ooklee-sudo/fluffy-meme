"""Claude Docs HTML export (tool-result JSON) -> Word via LibreOffice, then format the display equations."""
import sys, json, base64, subprocess, os, re, zipfile
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
src, out = sys.argv[1], sys.argv[2]
scratch = '/tmp/claude-0/-home-user-fluffy-meme/53200c0a-fa05-56f3-aa27-bbd149828e06/scratchpad'
d = json.load(open(src))['data']; html = base64.b64decode(d['bytes_b64']).decode()
h = os.path.join(scratch, 'conv.html'); open(h, 'w').write(html)
subprocess.run(['soffice', '--headless', '--convert-to', 'docx:MS Word 2007 XML', h, '--outdir', scratch], capture_output=True)
doc = Document(os.path.join(scratch, 'conv.docx'))
EQS = {
 '\\big[p(A_y': [('[ ', ''), ('p', 'i'), ('(', ''), ('A', 'i'), ('y', 'si'), (' ', ''), ('B', 'i'), ('n', 'si'), (') + ', ''), ('p', 'i'), ('(', ''), ('A', 'i'), ('n', 'si'), (' ', ''), ('B', 'i'), ('y', 'si'),
                 (') ]', ''), ('A→B', 's'), ('  =  [ ', ''), ('p', 'i'), ('(', ''), ('B', 'i'), ('n', 'si'), (' ', ''), ('A', 'i'), ('y', 'si'), (') + ', ''), ('p', 'i'), ('(', ''), ('B', 'i'), ('y', 'si'),
                 (' ', ''), ('A', 'i'), ('n', 'si'), (') ]', ''), ('B→A', 's')],
 '\\mathrm{SE}': [('SE(', ''), ('q', 'i'), (') = √[ ', ''), ('d', 'i'), ('AB', 'si'), ('(1 − ', ''), ('d', 'i'), ('AB', 'si'), (') / ', ''), ('n', 'i'), ('AB', 'si'),
                  ('  +  ', ''), ('d', 'i'), ('BA', 'si'), ('(1 − ', ''), ('d', 'i'), ('BA', 'si'), (') / ', ''), ('n', 'i'), ('BA', 'si'), (' ]', '')],
}
k = 0
for para in doc.paragraphs:
    t = para.text.strip(); eq = next((v for kk, v in EQS.items() if t.startswith(kk)), None)
    if not eq: continue
    for r in list(para.runs): r._element.getparent().remove(r._element)
    for txt, st in eq:
        run = para.add_run(txt); run.font.name = 'Cambria Math'; run.italic = 'i' in st; run.font.subscript = 's' in st
    k += 1; n = para.add_run('\t(%d)' % k); n.font.name = 'Cambria Math'; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.save(out)
x = zipfile.ZipFile(out).read('word/document.xml').decode(); t = re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', x))
print('saved', out, '| equations', k, '| tables', x.count('<w:tbl>'), '| words', len(t.split()), '| raw latex', t.count('\\big') + t.count('\\mathrm'), '| Kang cited', 'Kang' in t, '| has 9. Robustness', 'Robustness to Answer Labels' in t)
