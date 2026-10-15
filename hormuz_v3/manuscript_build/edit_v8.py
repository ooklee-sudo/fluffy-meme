import re, sys
from xml.sax.saxutils import escape
path = sys.argv[1]
x = open(path, encoding='utf-8').read()
x = x.replace('<w:lastRenderedPageBreak/>', '')
import re as _re
x = _re.sub(r'</w:t><w:t(?: xml:space="preserve")?>', '', x)
AUTH, DATE = 'Claude', '2026-10-15T00:00:00Z'
nid = [30000]
def i():
    nid[0] += 1; return nid[0]
def T(t): return escape(t)
def ins_run(t, italic=False):
    rpr = '<w:rPr><w:iCs/><w:i/></w:rPr>' if italic else ''
    return f'<w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"><w:r>{rpr}<w:t xml:space="preserve">{T(t)}</w:t></w:r></w:ins>'
def del_run(t, rpr=''):
    return f'<w:del w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"><w:r>{rpr}<w:delText xml:space="preserve">{T(t)}</w:delText></w:r></w:del>'

def replace(old, new, after=False):
    """Tracked replacement of `old` (must sit inside one run). after=True: keep old, insert new after it."""
    global x
    old = old if x.count(T(old)) else old.replace('al. ', 'al.\u00a0')
    new = new.replace('et al. ', 'et al.\u00a0')
    eo = T(old)
    assert x.count(eo) == 1, (x.count(eo), old[:60])
    pos = x.index(eo)
    rs = x.rfind('<w:r>', 0, pos); rs2 = x.rfind('<w:r ', 0, pos); rs = max(rs, rs2)
    re_ = x.index('</w:r>', pos) + len('</w:r>')
    run = x[rs:re_]
    m = re.match(r'(<w:r[^>]*>)(<w:rPr>.*?</w:rPr>)?<w:t[^>]*>(.*)</w:t></w:r>$', run, re.S)
    assert m, run[:200]
    rpr = m.group(2) or ''
    txt = m.group(3)
    a, b = txt.split(eo, 1)
    def r(t): return f'<w:r>{rpr}<w:t xml:space="preserve">{t}</w:t></w:r>' if t else ''
    italic = 'w:i/' in rpr
    mid = (r(eo) + ins_run(new, italic)) if after else (del_run(old, rpr) + (ins_run(new, italic) if new else ''))
    x = x[:rs] + r(a) + mid + r(b) + x[re_:]

def para_end(anchor):
    eo = T(anchor); assert x.count(eo) == 1, anchor
    return x.index('</w:p>', x.index(eo)) + len('</w:p>')
def para_start(anchor):
    eo = T(anchor); assert x.count(eo) == 1, anchor
    k = x.index(eo); return max(x.rfind('<w:p>', 0, k), x.rfind('<w:p ', 0, k))
def new_para(runs, style='BodyText', jc=None):
    j = f'<w:jc w:val="{jc}"/>' if jc else ''
    mark = f'<w:rPr><w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"/></w:rPr>'
    body = ''.join(ins_run(t, it) for t, it in runs)
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{j}{mark}</w:pPr>{body}</w:p>'
def insert_after(anchor, paras):
    global x
    p = para_end(anchor); x = x[:p] + ''.join(paras) + x[p:]
def insert_before(anchor, paras):
    global x
    p = para_start(anchor); x = x[:p] + ''.join(paras) + x[p:]

CC = "sub-agents of the Claude Code agent (version 2.1.300)"
replace("one model [record model name, version and temperature]", f"one model (claude-sonnet-5-5, run as {CC} on 14 October 2026; sampling parameters were the agent’s defaults, and temperature was not set by us)")
replace("(three model sizes and a repeat of one)", "(claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5 and a repeat of claude-sonnet-5-5)")
replace("no better than model 1 (Table 2).", " The two sonnet runs use the same model as model 1 (claude-sonnet-5-5), so for them only the prompt differs.", after=True)
replace("The model versions behind the runs are to be recorded [versions].", "Model 1: claude-sonnet-5-5; v2 runs: opus = claude-opus-5-5, sonnet and sonnet repeat = claude-sonnet-5-5, haiku = claude-haiku-5-5.")
replace("the first-stage model is not documented to the level of version and temperature, and", "all runs used default sampling settings that we did not control (temperature was not set), and")
replace("The runs are copies of the same model.", f"The runs are copies of the same model (claude-sonnet-5-5), run as {CC} on 14 October 2026 with default sampling settings.")
replace("[Record model names and versions.]", f"Run 1 used claude-opus-5-5, runs 2 and 4 claude-sonnet-5-5, and run 3 claude-haiku-5-5, all run as {CC} on 14 October 2026 with default sampling settings.")
open(path, 'w', encoding='utf-8').write(x)
print('ok')
