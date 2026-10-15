import re, sys
from xml.sax.saxutils import escape
path = sys.argv[1]
x = open(path, encoding='utf-8').read()
x = x.replace('<w:lastRenderedPageBreak/>', '')
import re as _re
x = _re.sub(r'</w:t><w:t(?: xml:space="preserve")?>', '', x)
AUTH, DATE = 'Claude', '2026-10-15T00:00:00Z'
nid = [20000]
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

KV = "Kim and Verrecchia 1991"
# ---- Introduction
replace("Explanations typically invoke attention", "Explanations typically invoke Bayesian updating on public announcements (Kim and Verrecchia 1991), attention")
replace("an information-theoretic account that motivated the study is not supported by its pre-specified tests",
        "a Bayesian account of price reactions to public announcements that motivated the study, first stated in information-theoretic terms, is not supported by its pre-specified tests")
# ---- Scope
replace("We began from an information-theoretic reading in which a post moves prices according to its surprisal, the prior uncertainty about the state it concerns and its redundancy;",
        "We began from a reading, first stated in information-theoretic terms and restated in Appendix F as Bayesian updating on a public signal (Kim and Verrecchia 1991), in which the price response to a post grows with how far it departs from what the market expected, with the prior uncertainty about the state it concerns and with its precision, and shrinks when it repeats earlier information;")
# ---- 4.6
replace("They are reported in full in Appendix F (Table F1).",
        " Appendix F restates the propositions as implications of Bayesian updating on a public signal (Kim and Verrecchia 1991); the restatement changes no result, but it shows why the prior-uncertainty test as specified cannot separate updating from volatility persistence, and which test would.", after=True)
# ---- Appendix F
replace("Information-theoretic motivation and tests", "Motivation from Bayesian updating, and tests")
tail = '<w:r><w:rPr><w:i/><w:iCs/></w:rPr><w:t>size</w:t></w:r><w:r><w:t xml:space="preserve"> of a reaction, not its sign.</w:t></w:r>'
assert x.count(tail) == 1
x = x.replace(tail, del_run('size', '<w:rPr><w:i/><w:iCs/></w:rPr>') + del_run(' of a reaction, not its sign.'))
replace("Information theory offers a vocabulary for this (Shannon 1948; Cover and Thomas 2006). Let S be a state the market cares about (here, whether Hormuz transit is open), with prior π and entropy H(π). A message that changes the belief to π′ conveys KL(π′ ‖ π) (Kullback and Leibler 1951). Three implications follow in expectation. A message that is unlikely under π, and not a repeat of earlier messages, should produce a larger update (surprisal and redundancy). The update should be larger when H(π) is larger (prior uncertainty). And reliability should scale the update. These are statements about the ",
        "The study was first motivated in information-theoretic terms (Shannon 1948; Cover and Thomas 2006): a message that moves the market’s belief about a state from π to π′ conveys KL(π′ ‖ π) (Kullback and Leibler 1951). Those quantities restate Bayesian updating, and the standard model of price reactions to public announcements (Kim and Verrecchia 1991) gives the same implications with its parameters explicit. Let V be the value of the asset implied by the state (here, the oil price that would prevail given the course of the closure), with prior V ~ N(m, σ₀²) held by the market before the post. A post is a public signal y = V + ε, with ε ~ N(0, 1/s) independent of V, where the precision s is how reliably the post reveals the decision. With the price equal to the posterior mean, the price revision at the post is")
insert_after("the price revision at the post is", [
  new_para([("ΔP = w · (y − m),   where w = s σ₀² / (1 + s σ₀²),     (F1)", False)], jc='center'),
  new_para([("and its variance across posts is", False)]),
  new_para([("Var(ΔP) = w · σ₀².     (F2)", False)], jc='center'),
  new_para([("The propositions follow. For a given precision, the size of the reaction increases in the surprise y − m (P1, surprisal). A post that repeats information the market already holds carries a smaller surprise and, when it is correlated with earlier public signals, a smaller incremental precision (P5, redundancy; Holthausen and Verrecchia 1988; Tetlock 2011). For a given surprise the reaction increases in the prior uncertainty σ₀², because w does (P2), and because the surprise is multiplied by w its effect is larger when prior uncertainty is higher (P3, the interaction). The reaction increases in the precision s, which is the reliability channel. The sign of ΔP is the sign of y − m, so a de-escalation post moves oil down only to the extent that the market had not already expected de-escalation; this is the logic of the state-dependent sign (P6). In this Gaussian case the information-theoretic quantity is a function of the same terms, KL(π′ ‖ π) = ½[ΔP²/σ₀² − w − ln(1 − w)], which is large when the standardized revision is large and when w is large. The restatement therefore adds no prediction to the information-theoretic account; it makes the parameters explicit and shows what each proxy has to measure.", False)]),
])
replace("not the entropy of beliefs about the strait", "not the prior variance σ₀² of beliefs about the strait")
replace("not of the vocabulary", "not of the model")
insert_after("we do not claim that the account organizes the evidence.", [
  new_para([("The restatement also shows what the tests could and could not detect. Equation (F2) scales with σ₀², and so does the variance of returns in hours without a post when volatility is persistent. The outcome |z|, scaled by long-run volatility, therefore rises with recent volatility whether or not the market updates on the post, which is the confound noted in Appendix F.2. What the model attributes to the post is w, the share of prior variance that the post resolves; empirically, the ratio of the return variance at posts to that in comparable hours without a post. A test of P2 that is not confounded by volatility persistence would scale the post-window return by the volatility of matched placebo windows (Section 4.5) instead of long-run volatility and ask whether the scaled reaction rises with prior uncertainty. We have not run this test; it is a design implication, not a result. Two further gaps are visible in the model. The novelty measure N_c is computed on the poster’s own text, so it measures the surprise y − m only if the market’s expectation m is formed from the poster’s recent messages. And the precision s, which the model treats as a separate channel, has no proxy in our data.", False)]),
])
# ---- References
J = lambda a, j, b: [(a, False), (j, True), (b, False)]
insert_after("Holm, S. 1979", [new_para(J("Holthausen, R. W., and Verrecchia, R. E. 1988. “The Effect of Sequential Information Releases on the Variance of Price Changes in an Intertemporal Multi-Asset Market,” ", "Journal of Accounting Research", " (26:1), pp. 82–106."))])
insert_after("Kamenica, E.", [new_para(J("Kim, O., and Verrecchia, R. E. 1991. “Trading Volume and Price Reactions to Public Announcements,” ", "Journal of Accounting Research", " (29:2), pp. 302–321."))])
insert_after("Tetlock, P. C. 2007", [new_para(J("Tetlock, P. C. 2011. “All the News That’s Fit to Reprint: Do Investors React to Stale Information?,” ", "Review of Financial Studies", " (24:5), pp. 1481–1512."))])
# ---- Table A1
anc = T("Appendices D and E")
e = x.index('</w:tr>', x.index(anc)) + len('</w:tr>')
def cell(t):
    mark = f'<w:rPr><w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"/></w:rPr>'
    return f'<w:tc><w:tcPr/><w:p><w:pPr><w:pStyle w:val="Compact"/><w:jc w:val="left"/>{mark}</w:pPr>{ins_run(t)}</w:p></w:tc>'
x = x[:e] + f'<w:tr><w:trPr><w:ins w:id="{i()}" w:author="{AUTH}" w:date="{DATE}"/></w:trPr>' + cell("Bayesian restatement of the propositions (Appendix F.1)") + cell("Written after the tests; changes no result; the placebo-scaled test of P2 is proposed, not run") + '</w:tr>' + x[e:]
open(path, 'w', encoding='utf-8').write(x)
print('ok')
