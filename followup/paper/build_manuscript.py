import json, statistics as st, collections
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

R = "results/"
auto7 = json.load(open(R + "autoscope_qwen7b.json"))
rip7 = json.load(open(R + "ripple_qwen7b.json")) + json.load(open(R + "ripple_qwen7b_s23.json"))
ripr7 = json.load(open(R + "ripple_rule_qwen7b.json")) + json.load(open(R + "ripple_rule_qwen7b_s23.json"))
real = json.load(open(R + "reallaw_qwen7b.json")) + json.load(open(R + "reallaw_sweep_qwen7b.json"))
reg7 = json.load(open(R + "regulatory_qwen7b.json"))
ed = [r for f in ("editors_qwen7b_seed1_ike.json", "editors_qwen7b_seed1_edit.json", "editors_qwen7b_s23.json") for r in json.load(open(R + f)) if "error" not in r]
q15 = json.load(open(R + "qwen15_full.json"))
amend = json.load(open("real_law/real_amendments_v1.json"))
res70 = [r for f in ("resA.json", "resB.json", "resC.json") for r in json.load(open(f))]

mean = lambda xs: st.mean(xs)
def ms(xs, rng=False):
    xs = [x for x in xs if x == x]
    return f"{mean(xs):.2f}" + (f" [{min(xs):.2f}–{max(xs):.2f}]" if rng else "")

d = Document()
sec = d.sections[0]; sec.left_margin = sec.right_margin = Inches(1.0); sec.top_margin = sec.bottom_margin = Inches(1.0)
base = d.styles["Normal"]; base.font.name = "Times New Roman"; base.font.size = Pt(12)
base.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
base.paragraph_format.line_spacing = 1.5; base.paragraph_format.space_after = Pt(6)
for lvl, size in ((1, 14), (2, 12), (3, 12)):
    h = d.styles[f"Heading {lvl}"]; h.font.name = "Times New Roman"; h.font.size = Pt(size); h.font.bold = True; h.font.italic = (lvl == 3)
    h.font.color.rgb = None
    rf = h.element.rPr.rFonts
    for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(att)) is not None: del rf.attrib[qn(att)]
    for att in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(att), "Times New Roman")
    h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(6); h.paragraph_format.line_spacing = 1.15
nfig = [0]; ntab = [0]

def H(t, l=1): d.add_heading(t, level=l)
def P(t, italic=False, bold=False, align=None):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = italic; r.bold = bold
    if align is not None: p.alignment = align
    return p
def BL(items):
    for x in items:
        p = d.add_paragraph(style="List Bullet"); p.add_run(x); p.paragraph_format.line_spacing = 1.5
def Tab(caption, rows, widths=None, note=None):
    ntab[0] += 1
    cp = d.add_paragraph(); r = cp.add_run(f"Table {ntab[0]}"); r.bold = True; cp.add_run("  " + caption); cp.paragraph_format.keep_with_next = True; cp.paragraph_format.line_spacing = 1.15
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, c in enumerate(row):
            cell = t.cell(i, j); cell.text = str(c)
            for pp in cell.paragraphs:
                pp.paragraph_format.line_spacing = 1.0; pp.paragraph_format.space_after = Pt(0)
                for run in pp.runs:
                    run.font.size = Pt(9); run.bold = (i == 0)
    if note:
        n = d.add_paragraph(); rr = n.add_run(note); rr.font.size = Pt(9); n.paragraph_format.line_spacing = 1.0
    else: d.add_paragraph().paragraph_format.line_spacing = 1.0
def Fig(path, caption, width=5.6):
    nfig[0] += 1
    d.add_picture(path, width=Inches(width)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp = d.add_paragraph(); r = cp.add_run(f"Fig. {nfig[0]}"); r.bold = True; cp.add_run("  " + caption); cp.paragraph_format.line_spacing = 1.15

# ------------------------------------------------------------------ title and abstract
t = d.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Consequential amendments for language models: how update procedures treat revised and related statutory provisions"); r.bold = True; r.font.size = Pt(16)
P("[Author names, affiliations and corresponding-author details are given on the title page]", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)

H("Abstract")
P("Statutes are amended continually, and a legal question-answering system has to follow them. When one provision changes, drafting practice does not stop there: drafters list the consequential amendments that other provisions need and add transitional or saving rules for what must stay as it was. We ask how far common procedures for updating a language model reproduce this practice. An amendment is formalised as a change to a share of a bank of provisions, and we measure whether amended provisions take the new value, whether untouched ones keep theirs, and whether dependent ones follow. Experiments use synthetic fact banks on models from 70 million to 7 billion parameters and 27 real amendments to the Employment Rights Act 1996 and the Companies Act 2006 that took effect in 2025 and 2026, compared with MEMIT, ROME and in-context editing. Retaining everything the update does not mention helps only when updates can be matched to stored provisions accurately, with a break-even at a matching accuracy of about 0.7 to 0.8. Provisions whose values follow arithmetically from an amended value, such as gross thresholds set at 1.2 times the net ones, never followed on their own in any procedure, but listing them restored them completely. In real statutes, provisions that share wording followed an amendment stated in only a few of them, and holding such provisions at their old value was harmful. The evidence covers 27 provisions, two Acts and one model family, and we state what it does not show.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
P("Keywords: Statutory amendment; Consequential amendment; Knowledge editing; Language models; Legal information systems; Continual learning", italic=True)

# ------------------------------------------------------------------ 1 Introduction
H("1 Introduction")
P("A language model that answers questions about the law keeps what it knows in its weights. When a rule changes, someone has to change the model, or the system will go on stating the old rule with the same confidence as before. The consequences are not hypothetical. In Moffatt v. Air Canada (2024 BCCRT 149), a Canadian tribunal held a company to the statement its chatbot had made about a policy, and rejected the argument that the chatbot was a separate entity. Organisations that put models in front of the public will increasingly be asked to show that what the model says matches the rules currently in force.")
P("Keeping a model current is more than replacing one answer. Legislative drafters have long dealt with the same difficulty on paper. When a provision is amended, other provisions may refer to it, repeat its wording or depend on a value it fixes, and the amending instrument usually has to deal with those too. Drafting guidance describes these as consequential amendments, that is, additional amendments required as a result of the main changes, and it advises drafters to search systematically for every cross-reference to the provision being changed (Office of Parliamentary Counsel 2025a). A separate set of rules, transitional and saving provisions, governs the move from the old law to the new one and protects what is meant to stay as it was (Office of Parliamentary Counsel 2025b). A model update that ignores this practice can leave the model in a state that no legislature intended: the amended provision is new, its dependents are old, and nothing in the system records the difference.")
P("The model-editing literature has measured this problem under another name. Editing one fact can imply changes to related facts, and editors that change the target fact often fail to change what follows from it (Cohen et al. 2024; Zhong et al. 2023). That work uses encyclopaedic facts, mostly edited one at a time. A body of statute differs in ways that matter for the question. Amendments arrive in groups. The same sentence is often repeated across many provisions, so that an amendment to a few of them changes the evidence for the rest. Some provisions contain values that are computed from others. And the conservative instinct of editing research, to leave everything else alone, collides with the fact that some of the ‘everything else’ is exactly what the amendment was meant to change.")
P("This paper asks how far familiar update procedures reproduce the discipline of consequential and saving provisions. We treat an amendment as a change to a share of a bank of provisions, apply several update procedures to a model that has learned the earlier text, and measure what happens to the amended provisions, to the provisions that were not amended, and to provisions that depend on the amended ones. We make four contributions.")
BL(["We formalise the update of a model after an amendment in terms of drafting practice, and separate three outcomes that are often run together: currency (amended provisions take the new value), continuity (untouched provisions keep theirs) and ripple (dependent provisions follow).",
    "In synthetic fact banks on models from 70 million to 7 billion parameters, we show that the best strength of a retention constraint depends on the share of provisions that were superseded, and that retaining everything the update does not mention reaches the attainable ceiling only to the extent that updates can be matched to stored provisions. A simple expression predicts the outcome in the settings we tested.",
    "We show that provisions whose values follow arithmetically from an amended value did not follow on their own in any procedure or at any model size we tested, and that listing them, as a consequential amendment would, restored them completely.",
    "We assemble 27 real amendments to two United Kingdom Acts from the legislation.gov.uk record, together with 90 unchanged provisions as controls. In this material, provisions that share wording followed an amendment stated in only a few of them, and the retention strategy that works best on synthetic data harmed them. We compare these results with MEMIT, ROME and in-context editing."])
P("The evidence is small and we say so throughout. It consists of one model family, 27 amended provisions from two Acts and a forced-choice evaluation. Section 8 sets out what it does and does not support.")
P("The remainder of the paper is organised as follows. Section 2 reviews related work. Section 3 formalises the problem and Section 4 describes the update procedures. Section 5 describes the data and experiments, Section 6 reports the results, and Section 7 discusses their implications for legal information systems. Section 8 sets out limitations and Section 9 concludes.")

# ------------------------------------------------------------------ 2 Related work
H("2 Background and related work")
H("2.1 Consequential, transitional and saving provisions", 2)
P("Drafting offices distinguish the change a bill is meant to make from the changes needed to keep the statute book coherent once it is made. Australian drafting guidance, for example, defines a consequential amendment as an additional amendment required as a result of the main changes in a legislative project, and notes that it can be purely technical, such as correcting a cross-reference, or substantive, such as reworking a concept (Office of Parliamentary Counsel 2025a). The practical advice is to search the legislation for every form of reference to the provision being amended, including references to the wider part or division, and to consider structural effects such as an orphaned heading. Transitional and saving provisions form the second part of the discipline. Because laws generally operate prospectively, an amending instrument often says what is to happen to cases and rights that arose under the old text (Office of Parliamentary Counsel 2025b). These are the practices to which we compare update procedures for models: the first corresponds to deciding which other provisions must change, and the second to deciding what is to be protected.")
P("Computational work on legislation has long treated versions and amendments as structured data. Standards for legal documents represent a provision as a sequence of versions with dates (Palmirani and Vitali 2011), which is the structure that makes it possible to retrieve the text in force immediately before an amendment, as we do in Section 5. In the logic of theory change, revising a belief set minimally while preserving its consistency is a central problem (Alchórron et al. 1985). A consequential amendment can be read as an instance of the same problem in a setting where the constraints are the dependencies between provisions. We use this reading as motivation only and make no formal claim.")
H("2.2 Knowledge editing and ripple effects", 2)
P("Methods for changing a single fact in a language model without retraining include locating and rewriting the relevant weights (Meng et al. 2022; Meng et al. 2023), training an auxiliary editor (De Cao et al. 2021; Mitchell et al. 2022) and supplying the new fact in the prompt (Zheng et al. 2023); see Yao et al. (2023) for a survey. Evaluations that go beyond the edited fact find that related facts frequently fail to change. Cohen et al. (2024) build a benchmark of about 5,000 edits with test queries for their logical consequences and report that existing editors often change the target fact without keeping related knowledge consistent, and that a simple in-context baseline did best. Zhong et al. (2023) show that edited models answer paraphrases of the edited fact but fail on multi-hop questions that depend on it. Our experiments differ in three respects: the facts are provisions of statutes, the amendments come in groups with shared wording, and we compare editors with a fine-tuning procedure whose retention constraint can be varied.")
H("2.3 Continual learning and temporal misalignment", 2)
P("Fine-tuning a model on new text can erase earlier competence (French 1999; Kirkpatrick et al. 2017), and standard remedies include replaying earlier data (Rolnick et al. 2019) and constraining the updated model to stay close to the earlier one. Language models also fall out of date as the world changes, which has been studied as temporal generalisation (Lazaridou et al. 2021; Dhingra et al. 2022). The constraint to stay close to an earlier model is exactly what an amendment must not apply to the amended provision, a tension that has received less attention than forgetting itself and that we examine directly.")

# ------------------------------------------------------------------ 3 Problem formulation
H("3 Problem formulation")
P("A fact is a pair (p, v) in which p is a prompt that identifies a provision, for example the statutory text up to the point where a value is stated, and v is the value that completes it. A launch model has learned a bank of N facts with values v₀. An amendment changes the authorised value of a subset of the bank. We write ρ for the share of facts in the bank whose value is superseded. A fact is a dependent of another if its authorised value is determined by the value of the other. In the synthetic banks this is a fixed mapping between two sets of values, and in the real data it is the relation between a net threshold and the corresponding gross threshold.")
P("An update procedure receives an update stream, a set of statements of amended provisions with their new values, and may in addition use a retention constraint that keeps selected facts at their launch behaviour. We say that a fact is listed if its amended statement appears in the stream. The share of listed facts among those that are amended is written k. For some experiments we also vary the coverage c, the share of superseded facts that the stream mentions at all, and the matching accuracy m, the probability that a fact mentioned in the stream is recognised as the stored fact it amends, so that its retention can be released.")
P("After the update we measure the following outcomes, each as a share of the relevant facts.")
BL(["Currency: amended provisions for which the model prefers the new value to the old one.",
    "Continuity: provisions that were not amended and for which the model still prefers the launch value. One minus continuity is the collateral damage.",
    "Ripple: dependent provisions of amended provisions that are answered with the new derived value, reported separately for dependents that were and were not listed.",
    "Acquisition: new facts that appear in the stream and are learned."])
P("Preference is judged by forced choice: we compare the log-probability that the model assigns to the authorised value with that of a competitor, which is the old value for an amended provision and a distractor number for an unamended one. This avoids the problem that many of the real values are several tokens long and share their first token (for example ‘£10.2 million’ and ‘£15 million’). It measures a preference between two answers and does not show that the model would produce the correct answer unprompted.")
P("A simple model helps to interpret the results. If a procedure retains everything the update does not mention and releases only those facts that are matched to a listed amendment, then, provided the unamended facts are retained, currency should be approximately (1 − ρ) + ρcm, where the first term is the share of facts that are not amended and the second the share of amended facts that the update both mentions and releases. The expression was written down after the first experiments on a smaller model and was then checked against data from a larger one (Section 6.2). We treat it as a description of the settings we ran and not as a law.")

# ------------------------------------------------------------------ 4 Update procedures
H("4 Update procedures and their drafting counterparts")
P("We compare the procedures in Table 1. The first five rows are variants of one fine-tuning procedure that differ only in the retention constraint or in what the update stream contains. The last two rows are established editors applied to the same launch model.")
Tab("Update procedures and the drafting practice each is closest to", [
    ["Procedure", "What it does", "Closest drafting practice"],
    ["Amend only", "Fine-tune on the statements of listed amendments; no constraint", "The amending text replaces the old text; nothing else is said"],
    ["Retain all", "Add a KL penalty to the launch model on every launch fact (weight λ)", "A blanket saving clause for the whole statute"],
    ["Stream-scoped retention", "KL penalty on launch facts that the update does not mention", "Saving provision for everything not expressly amended"],
    ["Dependency-scoped retention", "As stream-scoped, but facts that belong to the amendment (siblings, dependents) are also released", "Saving provision with an exception for provisions affected by the amendment"],
    ["Consequential listing", "Dependents are also stated in the update stream (completeness k_dep)", "Consequential amendments listed in the amending instrument"],
    ["MEMIT, ROME", "Rank-one weight edits located in the model (EasyEdit implementation)", "None; external baselines"],
    ["In-context editing (IKE)", "Amended statements placed in the prompt; weights unchanged", "None; external baseline"]],
    note="KL, Kullback–Leibler divergence on the distribution over the answer tokens.")

# ------------------------------------------------------------------ 5 Experimental design
H("5 Data and experimental design")
H("5.1 Synthetic fact banks", 2)
P("To control the structure of an amendment we first use synthetic banks. In the first, a provision is identified by a rule code and its value is a two-digit number or a category word, with 200 launch facts and 50 further facts that appear only in the update. In the second, the facts are provisions of fictional statutes (‘Under Article 14 of the Housing Subsidy Act, an application must be filed within’, completed by a spelled-out number), each stated in three paraphrases, so that an amendment given in one wording has to be recognised in the others. In the third, each base provision is paired with a dependent whose text refers to it and whose value is a fixed function of the base value (a filing deadline determines a fee tier). An amendment replaces a share ρ of base values and the authorised value of each dependent changes accordingly. In a fourth variant the launch data also contain explicit statements of the mapping.")
H("5.2 Real amendments", 2)
P("The real data come from legislation.gov.uk, which publishes the text of an Act as it stood on a given date together with editorial notes on each amendment. We scanned sections 1 to 235 of the Employment Rights Act 1996 and sections 380 to 480 of the Companies Act 2006, and also sections 1 to 45 of the Housing Act 1988 and 1 to 130 of the Insolvency Act 1986, which yielded only renumbering changes. We compared the text in force immediately before each amendment came into force with the latest revised text and kept changes of periods and amounts. Each change was matched to the site’s own amendment note, which names the amending instrument and the date of commencement. The result is 27 amended provisions in three groups (Table 2), listed in Appendix A.")
Tab("Real amendments used in the experiments", [
    ["Group", "Provisions", "Change", "In force", "Instrument"],
    ["A. Time limits", "Employment Rights Act 1996, ss. 11, 23, 34, 48, 51, 54, 57, 60, 63, 70, 111, 188 (12)", "period for presenting a complaint: three to six months", "1 Oct 2026", "Employment Rights Act 2025 (c. 36), s. 159(3), Sch. 12; SI 2026/954"],
    ["B. Amounts", "Employment Rights Act 1996, ss. 31, 186, 227 (3)", "£39 to £41 (s. 31); £719 to £751 (ss. 186, 227)", "6 Apr 2026", "Employment Rights (Increase of Limits) Order 2026, SI 2026/310"],
    ["C. Thresholds", "Companies Act 2006, ss. 382, 383, 465, 466 (12 values)", "size thresholds, e.g. turnover £10.2m to £15m; gross values about 1.2 times net", "6 Apr 2025", "SI 2024/1303"]],
    note="Values were taken from the text in force the day before commencement. SI, statutory instrument.")
P("Two features of this material matter for the questions we ask. The twelve time limits in group A were changed by a single amending schedule and are worded almost identically, so they are siblings in the sense of Section 3. In group C each ‘gross’ threshold in sections 383 and 466 is about 1.2 times the corresponding ‘net’ threshold, both before the amendment (10.2 and 12.2, 5.1 and 6.1, 36 and 43.2, 18 and 21.6) and after it (15 and 18, 7.5 and 9, 54 and 64, 27 and 32, the new gross values being rounded). The gross values are therefore dependents whose values follow arithmetically from the net ones. This is an observation about the text and not a rule stated in the Act.")
P("As controls we took 90 phrases from the same Acts that state a period (for example a number of days or weeks) and whose wording and value are identical in the enacted and the current text. Together with the 27 amended provisions they make a bank of 117 facts. Each fact is presented as the Act, section number and heading followed by the statutory words up to the value. The extracted passages were not proofread exhaustively, and some control prompts begin in the middle of a sentence.")
H("5.3 Models, training and evaluation", 2)
P("All procedures start from a launch model obtained by fine-tuning a pretrained model with LoRA (Hu et al. 2022; rank 16, learning rate 2 × 10⁻⁴) on the pre-amendment value of every fact until the token accuracy on the training facts reached 0.995, which happened in every run. The main model is Qwen2.5-7B (Yang et al. 2024); smaller models (Qwen2.5-1.5B and -3B, and a 70-million-parameter model fine-tuned in full) were used for the synthetic experiments. The update is a fresh LoRA adapter trained for 20 to 25 epochs at a learning rate of 10⁻⁴. Retention is implemented as a KL penalty, computed over the distribution of the answer tokens, between the updated model and the launch model on a set of anchor facts, with weight λ = 10 unless stated otherwise (1 and 10 for retention of all facts). The three established editors were applied to the same launch model through the EasyEdit library (Wang et al. 2024) with the library’s configuration for this model family. For MEMIT and ROME we estimated the covariance statistics from 3,000 wikitext-103 samples and not from the 100,000 Wikipedia samples of the original setting, and we did not tune hyperparameters.")
P("A random draw determines which amended provisions are listed. For each setting it was the same across procedures, so that procedures are compared on identical updates. Seeds 1 to 3 change that draw, the distractor numbers, the order of training examples and the initialisation of the adapters. We report means and the range over the three seeds and do not compute significance tests, because three seeds are too few for them. Code, fact banks and results are available in the repository named in the Declarations.")

# ------------------------------------------------------------------ 6 Results
H("6 Results")
H("6.1 The strength of retention and the share of superseded facts", 2)
P("In the first synthetic bank, the best strength of the retention penalty depends on how much of the bank was superseded (Fig. 1; Table 3). With no penalty, fine-tuning on the amended facts forgets many of the untouched ones, so currency is low when few facts were amended. A moderate penalty (λ = 1) protects the untouched facts and gives the best currency up to ρ = 0.5. When most of the bank was superseded, however, the same penalty holds back facts that should change, and the unconstrained update is best from ρ = 0.7. A strong penalty (λ = 10) retains almost all launch behaviour, so its currency is close to 1 − ρ at every value of ρ. The pattern is the same in the 70-million-parameter model with three seeds and in the 1.5-billion-parameter model with one seed.")
def e1(rows, kind):
    out = {}
    for r in rows:
        if kind == "70m" and r["q"] is not None: continue
        if kind == "15b" and r["q"] is not None: continue
        out.setdefault((r["rho"], r["lam"]), []).append(r["currency"])
    return out
a70 = e1(res70, "70m"); a15 = e1(q15, "15b")
rows = [["ρ", "1.5B, λ = 0", "λ = 1", "λ = 10", "70M, λ = 0", "λ = 1", "λ = 10"]]
for rho in (0.1, 0.3, 0.5, 0.7, 0.9):
    rows.append([rho] + [ms(a15[(rho, l)]) if (rho, l) in a15 else "n/a" for l in (0, 1, 10)] + [ms(a70[(rho, l)]) if (rho, l) in a70 else "n/a" for l in (0, 1, 10)])
Tab("Currency by share of superseded facts (ρ) and strength of retention (λ), independent facts", rows,
    note="1.5B: Qwen2.5-1.5B, one seed. 70M: 70-million-parameter model, mean over two or three seeds depending on the cell.")
Fig("paper/fig1_retention.png", "Currency against the share of superseded facts for three strengths of retention (70-million-parameter model, mean over seeds). The grey line is 1 − ρ.", 4.2)
H("6.2 Retaining what the update does not mention, and the cost of mismatching", 2)
P("The stream-scoped procedure retains every fact that the update does not mention. When updates are matched to stored facts without error it reaches the ceiling: in the 1.5-billion-parameter model currency was 1.00 for ρ = 0.3 and ρ = 0.7, against 0.89 and 0.82 for the best unscoped setting. The more realistic question is what happens when matching is imperfect, because an update stated in new words may not be recognised as an amendment of a stored fact. We therefore released each mentioned fact from retention only with probability m. A fact that is not released stays at its old value and an amended fact that is held in this way is lost.")
rows = [["ρ", "m", "Stream-scoped, mean [range]", "(1 − ρ) + ρm", "Best unscoped (mean)", "Difference per seed"]]
for rho in (0.3, 0.7):
    un = {}
    for r in auto7:
        if r["rho"] == rho and r["method"] in ("none", "unscoped"): un.setdefault((r["method"], r["lam"]), []).append(r["currency"])
    best = max(mean(v) for v in un.values())
    for m in (1.0, 0.8, 0.6):
        ss = {x["seed"]: x["currency"] for x in auto7 if x["rho"] == rho and x["method"] == "ss" and x.get("match", 1.0) == m}
        diffs = []
        for s in sorted(ss):
            b = max(x["currency"] for x in auto7 if x["seed"] == s and x["rho"] == rho and x["method"] in ("none", "unscoped"))
            diffs.append(ss[s] - b)
        rows.append([rho, m, ms(list(ss.values()), True), f"{(1 - rho) + rho * m:.2f}", f"{best:.2f}", ", ".join(f"{x:+.2f}" for x in diffs)])
Tab("Stream-scoped retention with imperfect matching, Qwen2.5-7B, three seeds", rows,
    note="Currency of amended provisions. Difference per seed: stream-scoped currency minus the best of the unscoped settings within the same seed.")
Fig("paper/fig2_matching.png", "Currency of stream-scoped retention against matching accuracy m (Qwen2.5-7B; points are means over three seeds, bars the range). The dashed line is (1 − ρ) + ρm and the dotted line is the best unscoped procedure.", 5.8)
P("Table 4 and Fig. 2 show two things. The expression (1 − ρ) + ρm describes the 7B results to within 0.015 in all six settings. It had been written down after seeing 1.5B results, so the 7B data are an independent check, although only within the range of ρ and m that we ran. And the advantage over the best unscoped procedure is clear when matching is exact (+0.09 to +0.23 across seeds), positive but small at m = 0.8 (+0.04 to +0.11), and negative or mixed at m = 0.6 (−0.08 to +0.04). With ill-matched updates a scoped procedure is no better than choosing the retention strength well, and for ρ = 0.7 it is worse. We also varied the accuracy of a record that says which provisions are still valid. Errors of the two kinds were not symmetric in the 1.5B model (one seed): wrongly releasing valid facts cost little, because retaining a subset of them protected the rest, whereas wrongly retaining superseded facts lowered currency in proportion.")
H("6.3 Dependent provisions do not follow, but listing them restores them", 2)
P("In the synthetic banks with dependent provisions, the share of dependents that followed an amendment without being listed was zero in all procedures and at all three model sizes, with one exception that is within chance (0.01). This holds when the dependent’s text explicitly refers to the base provision, when the mapping between their values is learned from many pairs, and when the mapping is also stated explicitly as text in the launch data (Table 5). Releasing the dependents from retention did not help: when dependents are free to change but the stream does not mention them, they stay as they were. In contrast, when a fraction k_dep of the dependents was added to the stream, the share of dependents that followed equalled k_dep (0.60 for k_dep = 0.6 and 1.00 for k_dep = 1), and with the complete list currency reached the ceiling.")
rows = [["Procedure", "ρ", "Ripple", "Unamended base facts kept", "Currency", "Ceiling"]]
def rip(rows_, rho, meth, kappa, lam=None):
    v = [r for r in rows_ if r["rho"] == rho and r["method"] == meth and r["kappa"] == kappa and (lam is None or r["lam"] == lam)]
    return v
for label, meth, kappa, lam in (("Amend only", "none", 0.0, None), ("Retain all (λ = 10)", "unscoped", 0.0, 10.0), ("Stream-scoped", "ss", 0.0, None),
                                ("Dependency-scoped", "dep", 0.0, None), ("Stream-scoped + 60% of dependents listed", "ss", 0.6, None), ("Stream-scoped + all dependents listed", "ss", 1.0, None)):
    for rho in (0.3, 0.7):
        v = rip(rip7, rho, meth, kappa, lam)
        rows.append([label, rho, ms([x["ripple"] for x in v], True), ms([x["keep_base"] for x in v]), ms([x["currency"] for x in v]), ms([x["ceiling"] for x in v])])
Tab("Dependent provisions in the synthetic bank, Qwen2.5-7B, three seeds", rows,
    note="Ripple: share of dependents of amended provisions that take the new derived value (mean [range]). Ceiling: currency attainable given the dependents that are listed.")
P("Two further procedures for propagating an amendment to a dependent without listing it did not work either. In the bank in which the mapping between values was stated as text in the launch data, the model had learned the statements (launch accuracy 0.996) yet still did not apply them to a revised base value: without listing, ripple was 0.00 to 0.01 in the 7B model over three seeds. Placing the amended statement of the base provision before the dependent question raised the share of correct answers only to a mean of 0.04 to 0.08 without listing (individual runs 0.00 to 0.17) and to 0.38 to 0.47 when the dependents had also been trained, far less than the strong showing of a simple in-context baseline reported by Cohen et al. (2024). The same pattern appeared at 1.5B and 3B in the runs we made (one seed each).")
H("6.4 Real amendments", 2)
P("The real amendments behave differently from the synthetic ones in one respect (Table 6). Amending only half of the time limits and amounts (k = 0.5) and fine-tuning on those statements was enough for most of the unlisted time limits to follow: 0.90 of the unlisted provisions in groups A and B took the new value, against 0.00 in the synthetic banks. The twelve time limits share their wording, so a model that has learned the new value in some of them applies it to the others. The gross thresholds, which depend on the net ones arithmetically, did not follow in any procedure (0.00), as in the synthetic banks.")
def rl(meth, lam, kA, kdep):
    return [r for r in real if r["method"] == meth and r["lam"] == lam and r["kA"] == kA and r["kdep"] == kdep]
rows = [["Procedure", "Listed", "Unlisted time limits and amounts", "Unlisted gross thresholds", "Controls kept", "All amended"]]
for label, meth, lam, kdep in (("Amend only", "none", 0.0, 0.0), ("Retain all (λ = 1)", "unscoped", 1.0, 0.0), ("Retain all (λ = 10)", "unscoped", 10.0, 0.0),
                               ("Stream-scoped retention", "ss", 10.0, 0.0), ("Dependency-scoped retention", "dep", 10.0, 0.0), ("Stream-scoped, all dependents listed", "ss", 10.0, 1.0)):
    v = rl(meth, lam, 0.5 if kdep == 0 else 1.0, kdep)
    rows.append([label] + [ms([x[k] for x in v], True) if any(x[k] == x[k] for x in v) else "n/a" for k in ("listed", "unlisted_AB", "ripple_dep", "keep_control", "currency_all")])
Tab("Real amendments, Qwen2.5-7B, three seeds, half of the time limits and amounts listed", rows,
    note="Shares of facts answered with the authorised value (new value for amended provisions); mean [range] over three seeds.")
P("The consequence for retention is the opposite of what the synthetic experiments suggested. Holding the unlisted amended provisions at their old value, which is what stream-scoped retention does, kept them from following the amendment (0.00) and lowered the listed provisions too (0.75 against 1.00), because the retained siblings share wording with the listed ones and pull in the other direction. Overall currency was 0.44 against 0.83 for amending only. Releasing the provisions that belong to the amendment while retaining everything else (dependency-scoped retention) matched amending only on currency (0.81 against 0.83) and kept every control provision (1.00, against 0.98 with a range down to 0.94).")
rows = [["Share listed (k)", "Unlisted: amend only", "Dependency-scoped", "Stream-scoped", "Controls: amend only", "All amended: amend only", "Dependency-scoped", "Stream-scoped"]]
def sw(meth, lam, kA):
    return [r for r in real if r["method"] == meth and r["lam"] == lam and r["kA"] == kA and r["kdep"] == 0]
for kA in (0.1, 0.25, 0.5, 0.75):
    a, b, c = sw("none", 0.0, kA), sw("dep", 10.0, kA), sw("ss", 10.0, kA)
    rows.append([kA, ms([x["unlisted_AB"] for x in a]), ms([x["unlisted_AB"] for x in b]), ms([x["unlisted_AB"] for x in c]), ms([x["keep_control"] for x in a]),
                 ms([x["currency_all"] for x in a]), ms([x["currency_all"] for x in b]), ms([x["currency_all"] for x in c])])
Tab("Share of time limits and amounts listed in the update, Qwen2.5-7B, mean of three seeds", rows,
    note="Unlisted: share of time-limit and amount provisions that are not in the update and still take the new value. With k = 0.75 only three provisions are unlisted, so each is worth 0.33 within a seed.")
Fig("paper/fig3_reallaw.png", "Real amendments: effect of the share of time-limit and amount provisions placed in the update (Qwen2.5-7B, mean over three seeds).", 5.8)
P("Table 7 and Fig. 3 show that a single listed time limit or two (k = 0.1) were enough for 0.77 of the unlisted provisions to follow when the update was fine-tuned without constraint, and that it stayed near 0.9 between k = 0.25 and k = 0.5. We do not know why the proportion falls at k = 0.75. Only three provisions remain unlisted at that point, and the same three may be the hardest in every seed, so the figure should not be over-read. Dependency-scoped retention followed the unconstrained update closely at every k, while stream-scoped retention failed to carry the amendment to any unlisted provision.")
H("6.5 Comparison with established editors", 2)
P("Table 8 compares the procedures with MEMIT, ROME and in-context editing on the same listed amendments (k = 0.5). Placing the amended statement in the prompt changed the preferred value for half of the listed provisions and for almost none of the others. MEMIT and ROME changed the unlisted time limits and amounts to the same degree as fine-tuning did (0.76), which is consistent with an effect of shared wording and not of the fine-tuning procedure alone. ROME changed more of the listed provisions than MEMIT but damaged more control provisions (0.86 retained, down to 0.76). No procedure moved the gross thresholds. Fine-tuning on the amended statements gave the highest currency (0.83), and dependency-scoped retention gave a currency of 0.81 while retaining all controls. This comparison should not be read as a ranking of editing methods: our fine-tuning procedure is trained on the same launch model by the same route, the editors were run with default configurations and with reduced covariance statistics, and the benchmark is small.")
ordr = [("Launch model, no update", "launch"), ("In-context editing, own statement", "ike_own"), ("In-context editing, all statements", "ike_all"), ("MEMIT", "memit"), ("ROME", "rome")]
rows = [["Procedure", "Listed", "Unlisted time limits and amounts", "Unlisted gross thresholds", "Controls kept", "All amended"]]
for label, key in ordr:
    v = [x for x in ed if x["editor"] == key]
    rows.append([label] + [ms([x[k] for x in v], True) for k in ("listed", "unlisted_AB", "ripple_dep", "keep_control", "currency_all")])
for label, meth, lam in (("Fine-tuning on the amendments", "none", 0.0), ("Fine-tuning + dependency-scoped retention", "dep", 10.0), ("Fine-tuning + stream-scoped retention", "ss", 10.0)):
    v = rl(meth, lam, 0.5, 0.0)
    rows.append([label] + [ms([x[k] for x in v], True) for k in ("listed", "unlisted_AB", "ripple_dep", "keep_control", "currency_all")])
Tab("Comparison with established editors on the same amendments, Qwen2.5-7B, three seeds", rows,
    note="Half of the time limits and amounts listed; mean [range] over three seeds.")
H("6.6 Paraphrases", 2)
P("In the synthetic bank with three paraphrases per provision, retaining all facts prevented an amendment that was stated in one wording from being applied to the others (0.00 to 0.01 of the amended provisions in the other wordings, 7B), because the penalty anchored every wording of the provision to its old value. Stream-scoped retention, with exact matching, carried the amendment across wordings (0.94 at ρ = 0.3 and 0.96 at ρ = 0.7) and gave currencies of 0.99 and 0.98, against 0.77 and 0.52 for amending only. Retaining the answers of unmentioned facts by replaying them, instead of a KL penalty, was equally good at ρ = 0.3 (0.98) and a little worse at ρ = 0.7 (0.95).")

# ------------------------------------------------------------------ 7 Discussion
H("7 Discussion")
H("7.1 Two kinds of propagation", 2)
P("The results separate two ways in which an amendment can reach a provision that was not amended in the update. Provisions that share wording with an amended provision followed it without being listed, to a degree that depended little on how many were listed. Provisions whose values are computed from an amended value did not follow at all. A plausible reading is that the first kind of propagation is a by-product of learning a repeated pattern, so that changing the value in a few sentences changes it in the others, whereas the second requires the model to carry out a calculation or a lookup that fine-tuning on the amended statements does not teach. We did not test this explanation, and it is compatible with the failures of the editors on the same provisions. For legal information systems the practical difference is large. The first kind of propagation is useful but uncontrolled, since it also reaches provisions that should not have followed. The second never happens unless somebody has listed the dependent provisions.")
H("7.2 Implications for update practice", 2)
P("Three recommendations follow, each of which should be treated as a hypothesis to test on larger and more varied material. First, an update pipeline should ingest the consequential amendments that the amending instrument already contains, and where dependencies are computed rather than copied it should generate the dependent statements explicitly, as our listing procedure does. Second, blanket retention should be avoided. A penalty that holds everything not mentioned in the update at its old value is harmful when amended provisions share wording with listed ones, and any retention should be scoped to exclude the provisions that belong to the amendment. Third, evaluation after an update should probe three groups separately: the amended provisions, siblings and dependents that were not listed, and a set of unrelated controls. A single aggregate accuracy would have hidden each of the effects reported here. Our results also bear on the choice between updating weights and supplying the current text at question time. In-context editing performed poorly in our implementation, but a retrieval system faces the same dependency problem, since it has to retrieve the dependents as well as the amended provision.")
H("7.3 Relation to drafting practice", 2)
P("The comparison with drafting practice should not be pressed too far. Drafters work with a known set of provisions and an authoritative cross-reference structure, and the consequential amendments they write are judged by lawyers. A model has no such structure, and what we call a list is something the update procedure has to be given. What the experiments do support is a narrower claim. The discipline of listing consequential changes and protecting the rest does not come for free from standard update procedures, and for dependencies that are computed it has to be supplied from outside the model.")

# ------------------------------------------------------------------ 8 Limitations
H("8 Limitations")
P("The study has clear limits. The real amendments are 27 provisions from two United Kingdom Acts, found by scanning four Acts, and they are not a sample of legislation. Only one model family was used and almost all of the real-data results come from one model size with LoRA fine-tuning, so the results may not hold for other families, for full fine-tuning or for systems that retrieve text. The old values were learned by fine-tuning at launch and were not part of what the model knew from pretraining, which makes the experiments controlled but unlike a deployed system. Evaluation is by forced choice between two values and does not show what a model would generate. The synthetic dependency is a one-step mapping, and the real dependency is one arithmetic relation. The expression for currency was written down after the first experiments and has been checked only at the settings reported. The established editors were not tuned, their statistics were estimated from a smaller sample than in their original setting, and our fine-tuning procedure had the advantage of the same training route as the launch model. Finally, the extracted passages were not proofread exhaustively, extent and territorial variants of the Acts were not examined, and nothing in the paper is legal advice.")

# ------------------------------------------------------------------ 9 Conclusion
H("9 Conclusion")
P("When a statute is amended, drafting practice supplies rules for what the amendment does to other provisions. We compared update procedures for language models against that practice on synthetic fact banks and on 27 real amendments. Retaining what the update does not mention is useful only as far as updates can be matched to stored provisions, and it can be harmful when unmentioned provisions share wording with the amended ones. Dependent provisions whose values are computed from an amended value do not follow unless they are listed, which is the role that a list of consequential amendments plays in drafting. The evidence is small, and its main use is to indicate what a larger study should measure: amended provisions, unlisted siblings and dependents, and controls, for each update procedure.")

# ------------------------------------------------------------------ Declarations
H("Declarations")
P("Funding. [To be completed by the authors.]")
P("Competing interests. [To be completed by the authors.]")
P("Data and code availability. The fact banks, scripts and results are available at [repository and DOI to be inserted; the existing deposit covers only the first experiment and must be updated]. Statutory text quoted in the fact banks was retrieved from legislation.gov.uk and is Crown copyright, reproduced under the Open Government Licence v3.0. Its terms should be checked before redistribution.")
P("Author contributions. [To be completed by the authors.]")
P("Use of large language models. [Draft statement, to be confirmed and completed by the authors in line with the journal’s policy: a large language model was used to assist with drafting and editing the text and with writing and running the experiment code. The authors checked the content and the results and take full responsibility for the paper.]")

# ------------------------------------------------------------------ References
H("References")
refs = [
 "Alchourrón CE, Gärdenfors P, Makinson D (1985) On the logic of theory change: partial meet contraction and revision functions. J Symb Log 50(2):510–530",
 "Cohen R, Biran E, Yoran O, Globerson A, Geva M (2024) Evaluating the ripple effects of knowledge editing in language models. Trans Assoc Comput Linguist 12:283–298",
 "De Cao N, Aziz W, Titov I (2021) Editing factual knowledge in language models. In: Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, pp 6491–6506",
 "Dhingra B, Cole JR, Eisenschlos JM, Gillick D, Eisenstein J, Cohen WW (2022) Time-aware language models as temporal knowledge bases. Trans Assoc Comput Linguist 10:257–273",
 "French RM (1999) Catastrophic forgetting in connectionist networks. Trends Cogn Sci 3(4):128–135",
 "Hu EJ, Shen Y, Wallis P, Allen-Zhu Z, Li Y, Wang S, Wang L, Chen W (2022) LoRA: low-rank adaptation of large language models. In: International Conference on Learning Representations",
 "Kirkpatrick J, Pascanu R, Rabinowitz N, Veness J, Desjardins G, Rusu AA, Milan K, Quan J, Ramalho T, Grabska-Barwinska A, Hassabis D, Clopath C, Kumaran D, Hadsell R (2017) Overcoming catastrophic forgetting in neural networks. Proc Natl Acad Sci USA 114(13):3521–3526",
 "Lazaridou A, Kuncoro A, Gribovskaya E, Agrawal D, Liska A, Terzi T, Gimenez M, de Masson d’Autume C, Kocisky T, Ruder S, Yogatama D, Cao K, Young S, Blunsom P (2021) Mind the gap: assessing temporal generalization in neural language models. In: Advances in Neural Information Processing Systems 34",
 "Meng K, Bau D, Andonian A, Belinkov Y (2022) Locating and editing factual associations in GPT. In: Advances in Neural Information Processing Systems 35",
 "Meng K, Sharma AS, Andonian A, Belinkov Y, Bau D (2023) Mass-editing memory in a transformer. In: International Conference on Learning Representations",
 "Mitchell E, Lin C, Bosselut A, Finn C, Manning CD (2022) Fast model editing at scale. In: International Conference on Learning Representations",
 "Moffatt v. Air Canada, 2024 BCCRT 149 (Civil Resolution Tribunal of British Columbia)",
 "Office of Parliamentary Counsel (2025a) Instructor guidance note: consequential amendments. Australian Government. https://www.opc.gov.au/sites/default/files/2025-10/Instructor%20Guidance%20Note%20-%20Consequential%20amendments.pdf. Accessed 3 Nov 2026",
 "Office of Parliamentary Counsel (2025b) Instructor guidance note: application, saving and transitional provisions. Australian Government. https://www.opc.gov.au/sites/default/files/2025-10/Instructor%20Guidance%20Note%20-%20Application%2C%20saving%20and%20transitional%20provisions.pdf. Accessed 3 Nov 2026",
 "Palmirani M, Vitali F (2011) Akoma-Ntoso for legal documents. In: Sartor G, Palmirani M, Francesconi E, Biasiotti MA (eds) Legislative XML for the Semantic Web. Springer, Dordrecht, pp 75–100",
 "Rolnick D, Ahuja A, Schwarz J, Lillicrap T, Wayne G (2019) Experience replay for continual learning. In: Advances in Neural Information Processing Systems 32",
 "Wang P, Zhang N, Tian B, Xi Z, Yao Y, Xu Z, Wang M, Mao S, Wang X, Cheng S, Liu K, Ni Y, Zheng G, Chen H (2024) EasyEdit: an easy-to-use knowledge editing framework for large language models. arXiv:2308.07269",
 "Yang A, Yang B, Zhang B, et al. (2024) Qwen2.5 technical report. arXiv:2412.15115",
 "Yao Y, Wang P, Tian B, Cheng S, Li Z, Deng S, Chen H, Zhang N (2023) Editing large language models: problems, methods, and opportunities. In: Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, pp 10222–10240",
 "Zheng C, Li L, Dong Q, Fan Y, Wu Z, Xu J, Chang B (2023) Can we edit factual knowledge by in-context learning? In: Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, pp 4862–4876",
 "Zhong Z, Wu Z, Manning CD, Potts C, Chen D (2023) MQuAKE: assessing knowledge editing in language models via multi-hop questions. In: Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, pp 15686–15702",
 "Companies Act 2006 (c. 46) and Employment Rights Act 1996 (c. 18), as published on legislation.gov.uk (text retrieved 3 Nov 2026); Employment Rights Act 2025 (c. 36); The Employment Rights (Increase of Limits) Order 2026, SI 2026/310; SI 2026/954; The Companies (Accounts and Reports) (Amendment and Transitional Provision) Regulations 2024, SI 2024/1303. https://www.legislation.gov.uk"]
for x in refs:
    p = d.add_paragraph(x); p.paragraph_format.left_indent = Inches(0.4); p.paragraph_format.first_line_indent = Inches(-0.4); p.paragraph_format.line_spacing = 1.15
    for run in p.runs: run.font.size = Pt(10.5)

# ------------------------------------------------------------------ Appendix
H("Appendix A. Amended provisions")
rows = [["Act", "Section", "Heading", "Group", "Before", "After"]]
for a in amend:
    rows.append([a["act_name"].replace(" Act", ""), a["section"], a["title"], {"time_limit": "A", "amount": "B", "threshold": "C"}[a["kind"]], a["old"], a["new"]])
Tab("The 27 amended provisions used in the real-data experiments (values as in the text in force the day before commencement and in the current text)", rows,
    note="Group C values are in £ million. In ss. 383 and 466, the second value of each pair is a gross threshold.")
H("Appendix B. Training and evaluation settings")
BL(["Launch training: LoRA on all linear layers, rank 16, learning rate 2 × 10⁻⁴, batch size 16, up to 100 epochs (synthetic banks up to 80), stopping when token accuracy on the training facts reached 0.995; bfloat16.",
    "Update: new LoRA adapter, rank 16, learning rate 10⁻⁴, 20 epochs (25 in the synthetic banks), batch size 16; anchors sampled at random in each step.",
    "Retention: KL(launch || updated) over the distribution of each answer token, averaged over answer positions, weight 1 or 10.",
    "Synthetic banks: 200 launch facts and 50 facts introduced by the update; real bank: 117 facts (27 amended, 90 controls); ρ = 0.3 and 0.7 in most synthetic experiments.",
    "Forced choice: sum of log-probabilities of the answer tokens given the prompt, authorised value against the competitor; controls compared with a distractor number drawn at random.",
    "MEMIT and ROME: EasyEdit default configuration for Qwen2.5-7B, layers 4 to 8, subject set to the full prompt, covariance statistics from 3,000 wikitext-103 samples; in-context editing: amended statements placed before the question.",
    "Seeds 1 to 3. Hardware: one rented 80 GB GPU for the 7B runs; a laptop GPU with 8 GB for runs up to 3B."])
d.save("paper/AI_and_Law_manuscript.docx")
txt = " ".join(p.text for p in d.paragraphs)
print("words (paragraphs only):", len(txt.split()), "tables:", ntab[0], "figures:", nfig[0])
abs_ = [p.text for p in d.paragraphs if p.text.startswith("Statutes are amended")][0]
print("abstract words:", len(abs_.split()))
