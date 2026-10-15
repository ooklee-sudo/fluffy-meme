import re, sys
from xml.sax.saxutils import escape
path = sys.argv[1]
x = open(path, encoding='utf-8').read()
AUTH, DATE = 'Claude', '2026-10-15T00:00:00Z'
nid = [9000]
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
    return x.rfind('<w:p>', 0, x.index(eo))
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

# ---- Abstract
replace("the model-labelled escalation estimates are smaller (0.17% to 0.35%) because the models add events that humans call de-escalation or other.",
        "the model-labelled escalation estimates are smaller (0.17% to 0.35%). Treating the model label as a misclassified categorical variable, we write each model-label estimate as an exact mixture of human-class means; the shortfall comes from posts that humans call de-escalation or other, not from a weaker response among posts that both call escalation.")
# ---- Introduction
replace("unless they are corrected with a validated subsample (Egami et al. 2023; Angelopoulos et al. 2023).",
        " Econometrics has a longer theory of the same problem. When a categorical variable is misclassified, the error is necessarily correlated with the true category, so it does not shrink an effect by a constant factor as classical measurement error does; the bias of a class mean depends on which classes the misclassified units come from and on how their outcomes differ (Aigner 1973; Bollinger 1996; Bound et al. 2001; Mahajan 2006; Lewbel 2007).", after=True)
replace("The attenuation comes from the events the models add to the escalation class, not from noise shrinking the same effect.",
        "Using the econometrics of misclassified categorical variables, we write the model-label estimate as an exact mixture of the human-class means and decompose its gap from the human estimate: the posts that humans call de-escalation or other account for the gap, and the posts that both call escalation move oil by about as much as the human class as a whole.")
# ---- Scope
replace("They do not bear on the labelling question and no theory is claimed here.",
        "They do not bear on the labelling question, and no theory of how posts move prices is claimed here. The one theoretical frame the paper uses concerns measurement: the econometrics of misclassified categorical variables (Section 4.4) states what an estimate built on model labels measures, and we use it to account for the differences between label sets, not to explain prices.")
# ---- Section 4.4
replace("Why the models’ estimate is smaller.", "Why the models’ estimate is smaller: a misclassification account.")
old44 = " The decomposition in Table 3b shows that the attenuation is event selection. Under the v2 majority, 30 events are labelled escalation: 14 are also escalation for humans (mean directional return +0.53%), 8 are mixed (+0.71%), and 8 are de-escalation or other (−0.84% and −0.30%). The model sets add events that humans do not call escalation, and the ones humans call de-escalation or other have returns of the wrong sign for the escalation class. This is not classical noise shrinking the same effect: misclassified events enter with their own signs."
replace(old44, " Let H be the human label of an event, M a model label, and r_e the 30-minute return signed in the direction of class e. The model-label estimate of the response to class e is the mean of r_e over the events with M = e, which is identically")
insert_after("which is identically", [
  new_para([("μ_M(e) = Σ_h π(h | e) · μ(h, e),     (1)", False)], jc='center'),
  new_para([("where π(h | e) is the share of the model’s e events whose human label is h (π(e | e) is the precision on these events) and μ(h, e) is the mean of r_e over those events. Subtracting the human estimate μ_H(e) gives", False)]),
  new_para([("μ_M(e) − μ_H(e) = π(e | e) · [μ(e, e) − μ_H(e)] + Σ_{h≠e} π(h | e) · [μ(h, e) − μ_H(e)].     (2)", False)], jc='center'),
  new_para([("The first term is selection within the class: the model finds a different subset of the human escalation events. The second is contamination by the other classes. Equation (1) is an accounting identity and needs no assumption about the errors. It makes explicit a result from the econometrics of misclassified discrete variables. Misclassification of a category is necessarily correlated with the true category (Aigner 1973; Bound et al. 2001), so it does not act like classical measurement error, which would shrink the effect by a constant factor. The bias is a weighted sum of the gaps between the outcome means of the classes the errors come from and that of the target class, and it can take either sign (Mahajan 2006; Lewbel 2007). A human de-escalation post placed in the escalation class moves oil in the de-escalation direction, which is negative when signed as escalation, so it contributes a negative term where an unrelated post would contribute about zero.", False)]),
  new_para([("Table 3b supplies every term. For the original labels (24 escalation events: 10 human escalation, +0.45%; 4 human de-escalation, −0.43%; 5 mixed, +0.71%; 5 other, −0.44%), equation (1) returns +0.17%, the estimate in Table 3, and equation (2) divides the gap of −0.31 points into −0.01 from selection within the class, −0.15 from human de-escalation posts, −0.19 from human other posts and +0.05 from mixed posts. For the v2 majority (30 events: 14 escalation, +0.53%; 2 de-escalation, −0.84%; 8 mixed, +0.71%; 6 other, −0.30%) it returns +0.32% and divides the gap of −0.16 points into +0.02, −0.09, −0.16 and +0.06 (components are computed from the rounded means of Table 3b and need not sum exactly). In both label sets the posts that humans and models both call escalation move oil by about as much as the human class as a whole (0.45% and 0.53% against 0.48%), so the shortfall is contamination, not a weaker response among correctly labelled posts; the mixed posts, in which humans also see a threat, partly offset it. The same identity explains why the de-escalation estimate barely changes across label sets: the precision on its events is higher (23 of 34 and 24 of 33), and its contaminants are mostly mixed and other posts whose signed returns are positive (Table 3b).", False)]),
  new_para([("The identity accounts for the gap; it does not correct the estimate. It takes the human labels as the reference, and they are themselves measured with error (κ 0.61 to 0.69 between coders). With two human coders and several model runs per post, the true class is identified under conditions on how the raters’ errors relate to one another (Hu 2008), which is the formal basis for the latent-class analysis proposed in Section 5.4. The decomposition was written after Table 3b was known and is classified as post hoc in Table A1.", False)]),
])
# ---- Discussion, limitations, future, conclusion
replace("and decompose the difference by the events the label sets disagree on;",
        "and decompose the difference with the misclassification identity of Section 4.4, which shows whether it comes from contamination by other classes or from a different response among correctly labelled events;")
replace("so human labels are a benchmark, not truth.",
        " For the same reason the decomposition of Section 4.4 is an accounting relative to that benchmark, not a corrected estimate.", after=True)
replace("a latent-class analysis of all raters;",
        "a latent-class analysis of all raters, for which the econometrics of misclassification supplies identification conditions (Hu 2008);")
replace("because they added events that humans do not call escalation;",
        "because they added events that humans do not call escalation, and an exact decomposition attributes nearly all of the shortfall to those events;")
# ---- References
J = lambda a, j, b: [(a, False), (j, True), (b, False)]
insert_before("Angelopoulos, A. N., Bates", [new_para(J("Aigner, D. J. 1973. “Regression with a Binary Independent Variable Subject to Errors of Observation,” ", "Journal of Econometrics", " (1:1), pp. 49–59."))])
insert_after("Bollen, J., Mao, H.", [new_para(J("Bollinger, C. R. 1996. “Bounding Mean Regressions When a Binary Regressor Is Mismeasured,” ", "Journal of Econometrics", " (73:2), pp. 387–399."))])
insert_after("Born, J. A., Myers", [new_para(J("Bound, J., Brown, C., and Mathiowetz, N. 2001. “Measurement Error in Survey Data,” in ", "Handbook of Econometrics", " (Vol. 5), J. J. Heckman and E. Leamer (eds.), Amsterdam: North-Holland, pp. 3705–3843."))])
insert_after("Houweling, H. W.", [new_para(J("Hu, Y. 2008. “Identification and Estimation of Nonlinear Models with Misclassification Error Using Instrumental Variables: A General Solution,” ", "Journal of Econometrics", " (144:1), pp. 27–61."))])
insert_before("Lewis, E., Mohler", [new_para(J("Lewbel, A. 2007. “Estimation of Average Treatment Effects with Misclassification,” ", "Econometrica", " (75:2), pp. 537–551."))])
insert_after("Lewis, E., Mohler", [new_para(J("Mahajan, A. 2006. “Identification and Estimation of Regression Models with Misclassification,” ", "Econometrica", " (74:3), pp. 631–665."))])
# ---- Table A1 row
anc = T("Model re-labelling under codebook v2 and label-set comparison (4.4)")
assert x.count(anc) == 1
e = x.index('</w:tr>', x.index(anc)) + len('</w:tr>')
def cell(t):
    mark = f'<w:rPr><w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"/></w:rPr>'
    return f'<w:tc><w:tcPr/><w:p><w:pPr><w:pStyle w:val="Compact"/><w:jc w:val="left"/>{mark}</w:pPr>{ins_run(t)}</w:p></w:tc>'
row = f'<w:tr><w:trPr><w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"/></w:trPr>' + cell("Misclassification decomposition of the label-set difference (4.4)") + cell("Post hoc; accounting identity applied to Table 3b after it was known") + '</w:tr>'
x = x[:e] + row + x[e:]
open(path, 'w', encoding='utf-8').write(x)
print('ok')
