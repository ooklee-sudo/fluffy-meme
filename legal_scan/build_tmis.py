import json, re, os, glob, math, statistics as st, collections
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
mean = st.mean
SD = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/"
A = json.load(open(SD + "final/analysis.json"))
BANK = json.load(open(SD + "v3/real_law/real_fact_bank_v3.json"))
MODELS = ["Qwen2.5-7B", "Qwen3-8B-Base", "Olmo-3-7B"]
TAGS = {"Qwen2.5-7B": "v3qwen25", "Qwen3-8B-Base": "v3qwen3", "Olmo-3-7B": "v3olmo3"}
def f2(x): return f"{x:.2f}"

# ------------------------------------------------------------------ document from the ACM template
doc = docx.Document(SD + "tmpl/acm.docx")
body = doc.element.body
for el in list(body):
    if el.tag != qn("w:sectPr"): body.remove(el)
cp = doc.core_properties
for a in ("author", "last_modified_by", "title", "subject", "comments", "keywords", "category"): setattr(cp, a, "")
cp.title = "Blinded manuscript"; cp.author = "Anonymous"; cp.last_modified_by = "Anonymous"

# ------------------------------------------------------------------ references, numbered by first citation
REFS = {
 "Moffatt": "Moffatt v. Air Canada, 2024 BCCRT 149 (Civil Resolution Tribunal of British Columbia).",
 "Koopman2025": "Saskia Koopman. 2025. Thousands face fines after HMRC misses CGT update. City AM, 29 August 2025. https://www.cityam.com/thousands-face-fines-after-hmrc-misses-cgt-update/. Accessed 16 Nov 2026.",
 "Codd1970": "E. F. Codd. 1970. A relational model of data for large shared data banks. Commun. ACM 13, 6 (1970), 377–387.",
 "Codd1972": "E. F. Codd. 1972. Further normalization of the data base relational model. In Data Base Systems, R. Rustin (Ed.). Prentice-Hall, Englewood Cliffs, NJ, 33–64.",
 "Haney1972": "F. M. Haney. 1972. Module connection analysis: a tool for scheduling software debugging activities. In Proceedings of the AFIPS Fall Joint Computer Conference 41 (1972), 173–179.",
 "Swanson1976": "E. B. Swanson. 1976. The dimensions of maintenance. In Proceedings of the 2nd International Conference on Software Engineering. IEEE Computer Society Press, 492–497.",
 "Lehman1980": "M. M. Lehman. 1980. Programs, life cycles, and laws of software evolution. Proc. IEEE 68, 9 (1980), 1060–1076.",
 "WangStrong1996": "R. Y. Wang and D. M. Strong. 1996. Beyond accuracy: what data quality means to data consumers. J. Manag. Inf. Syst. 12, 4 (1996), 5–33.",
 "Pipino2002": "L. L. Pipino, Y. W. Lee, and R. Y. Wang. 2002. Data quality assessment. Commun. ACM 45, 4 (2002), 211–218.",
 "Ballou1985": "D. P. Ballou and H. L. Pazer. 1985. Modeling data and process quality in multi-input, multi-output information systems. Manag. Sci. 31, 2 (1985), 150–162.",
 "MaloneCrowston1994": "T. W. Malone and K. Crowston. 1994. The interdisciplinary study of coordination. ACM Comput. Surv. 26, 1 (1994), 87–119.",
 "OPC2025a": "Office of Parliamentary Counsel. 2025. Instructor guidance note: consequential amendments. Australian Government. https://www.opc.gov.au/sites/default/files/2025-10/Instructor%20Guidance%20Note%20-%20Consequential%20amendments.pdf. Accessed 3 Nov 2026.",
 "OPC2025b": "Office of Parliamentary Counsel. 2025. Instructor guidance note: application, saving and transitional provisions. Australian Government. https://www.opc.gov.au/sites/default/files/2025-10/Instructor%20Guidance%20Note%20-%20Application%2C%20saving%20and%20transitional%20provisions.pdf. Accessed 3 Nov 2026.",
 "PalmiraniVitali2011": "M. Palmirani and F. Vitali. 2011. Akoma-Ntoso for legal documents. In Legislative XML for the Semantic Web, G. Sartor, M. Palmirani, E. Francesconi, and M. A. Biasiotti (Eds.). Springer, Dordrecht, 75–100.",
 "PalmiraniBrighi2006": "M. Palmirani and R. Brighi. 2006. Time model for managing the dynamic of normative system. In Electronic Government, EGOV 2006. LNCS 4084. Springer, Berlin, Heidelberg.",
 "Governatori2005": "G. Governatori, M. Palmirani, R. Riveret, A. Rotolo, and G. Sartor. 2005. Norm modifications in defeasible logic. In Legal Knowledge and Information Systems, JURIX 2005. IOS Press, Amsterdam, 13–22.",
 "Alchourron1985": "C. E. Alchourrón, P. Gärdenfors, and D. Makinson. 1985. On the logic of theory change: partial meet contraction and revision functions. J. Symb. Log. 50, 2 (1985), 510–530.",
 "Meng2022": "K. Meng, D. Bau, A. Andonian, and Y. Belinkov. 2022. Locating and editing factual associations in GPT. In Advances in Neural Information Processing Systems 35.",
 "Meng2023": "K. Meng, A. S. Sharma, A. Andonian, Y. Belinkov, and D. Bau. 2023. Mass-editing memory in a transformer. In International Conference on Learning Representations.",
 "DeCao2021": "N. De Cao, W. Aziz, and I. Titov. 2021. Editing factual knowledge in language models. In Proceedings of EMNLP 2021. ACL, 6491–6506.",
 "Mitchell2022": "E. Mitchell, C. Lin, A. Bosselut, C. Finn, and C. D. Manning. 2022. Fast model editing at scale. In International Conference on Learning Representations.",
 "Zheng2023": "C. Zheng, L. Li, Q. Dong, Y. Fan, Z. Wu, J. Xu, and B. Chang. 2023. Can we edit factual knowledge by in-context learning? In Proceedings of EMNLP 2023. ACL, 4862–4876.",
 "Yao2023": "Y. Yao, P. Wang, B. Tian, S. Cheng, Z. Li, S. Deng, H. Chen, and N. Zhang. 2023. Editing large language models: problems, methods, and opportunities. In Proceedings of EMNLP 2023. ACL, 10222–10240.",
 "Cohen2024": "R. Cohen, E. Biran, O. Yoran, A. Globerson, and M. Geva. 2024. Evaluating the ripple effects of knowledge editing in language models. Trans. Assoc. Comput. Linguist. 12 (2024), 283–298.",
 "Zhong2023": "Z. Zhong, Z. Wu, C. D. Manning, C. Potts, and D. Chen. 2023. MQuAKE: assessing knowledge editing in language models via multi-hop questions. In Proceedings of EMNLP 2023. ACL, 15686–15702.",
 "French1999": "R. M. French. 1999. Catastrophic forgetting in connectionist networks. Trends Cogn. Sci. 3, 4 (1999), 128–135.",
 "Kirkpatrick2017": "J. Kirkpatrick, R. Pascanu, N. Rabinowitz, et al. 2017. Overcoming catastrophic forgetting in neural networks. Proc. Natl. Acad. Sci. USA 114, 13 (2017), 3521–3526.",
 "Rolnick2019": "D. Rolnick, A. Ahuja, J. Schwarz, T. Lillicrap, and G. Wayne. 2019. Experience replay for continual learning. In Advances in Neural Information Processing Systems 32.",
 "Lazaridou2021": "A. Lazaridou, A. Kuncoro, E. Gribovskaya, et al. 2021. Mind the gap: assessing temporal generalization in neural language models. In Advances in Neural Information Processing Systems 34.",
 "Dhingra2022": "B. Dhingra, J. R. Cole, J. M. Eisenschlos, D. Gillick, J. Eisenstein, and W. W. Cohen. 2022. Time-aware language models as temporal knowledge bases. Trans. Assoc. Comput. Linguist. 10 (2022), 257–273.",
 "Lewis2020": "P. Lewis, E. Perez, A. Piktus, et al. 2020. Retrieval-augmented generation for knowledge-intensive NLP tasks. In Advances in Neural Information Processing Systems 33, 9459–9474.",
 "Dahl2024": "M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho. 2024. Large legal fictions: profiling legal hallucinations in large language models. J. Leg. Anal. 16, 1 (2024), 64–93.",
 "Magesh2025": "V. Magesh, F. Surani, M. Dahl, M. Suzgun, C. D. Manning, and D. E. Ho. 2025. Hallucination-free? Assessing the reliability of leading AI legal research tools. J. Empir. Leg. Stud. 22 (2025), 216.",
 "Hevner2004": "A. R. Hevner, S. T. March, J. Park, and S. Ram. 2004. Design science in information systems research. MIS Q. 28, 1 (2004), 75–105.",
 "Venable2016": "J. Venable, J. Pries-Heje, and R. Baskerville. 2016. FEDS: a framework for evaluation in design science research. Eur. J. Inf. Syst. 25, 1 (2016), 77–89.",
 "Hu2022": "E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang, and W. Chen. 2022. LoRA: low-rank adaptation of large language models. In International Conference on Learning Representations.",
 "Qwen25": "A. Yang, B. Yang, B. Zhang, et al. 2024. Qwen2.5 technical report. arXiv:2412.15115.",
 "Qwen3card": "Qwen Team. 2025. Qwen3-8B-Base (model card). https://huggingface.co/Qwen/Qwen3-8B-Base. Accessed 16 Nov 2026.",
 "Olmo3card": "Allen Institute for AI. 2025. Olmo-3-1025-7B (model card). https://huggingface.co/allenai/Olmo-3-1025-7B. Accessed 16 Nov 2026.",
 "Legislation": "The National Archives. 2026. legislation.gov.uk: revised and point-in-time versions of Acts of the UK Parliament. https://www.legislation.gov.uk. Retrieved 3 and 16 Nov 2026. Contains public sector information licensed under the Open Government Licence v3.0.",
}
CITED = []
def cite(m):
    keys = [k.strip() for k in m.group(1).split(",")]; nums = []
    for k in keys:
        if k not in REFS: raise KeyError(k)
        if k not in CITED: CITED.append(k)
        nums.append(CITED.index(k) + 1)
    return "[" + ", ".join(str(n) for n in sorted(nums)) + "]"
def R(t): return re.sub(r"\{([A-Za-z0-9_, ]+)\}", cite, t)

# ------------------------------------------------------------------ writers
def para(text, style, align=None):
    p = doc.add_paragraph(style=style); p.add_run(R(text))
    if align is not None: p.alignment = align
    return p
def H1(t): return para(t, "Head1")
def H2(t): return para(t, "Head2")
def H3(t): return para(t, "Head3")
def P(t, first=False): return para(t, "PostHeadPara" if first else "Para")
def BUL(items):
    for t in items:
        p = doc.add_paragraph(style="Para"); p.add_run("• " + R(t)); p.paragraph_format.left_indent = Inches(0.2); p.paragraph_format.first_line_indent = Inches(-0.15)
NT = [0]; NF = [0]
def TAB(caption, rows, note=None, size=7, widths=None):
    NT[0] += 1
    para(f"Table {NT[0]}: {caption}", "TableCaption")
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = ""; pp = c.paragraphs[0]; pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.space_before = Pt(0)
            pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = pp.add_run(str(v)); r.font.size = Pt(size); r.bold = (i == 0)
            if widths: c.width = Inches(widths[j])
    if note: para(note, "TableFootnote")
    else: doc.add_paragraph(style="Para")
def FIG(path, caption, alt, width=4.9):
    NF[0] += 1
    p = doc.add_paragraph(style="Image"); run = p.add_run(); run.add_picture(SD + "final/figs/" + path, width=Inches(width))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dp = run._r.xpath(".//wp:docPr")[0]; dp.set("descr", alt); dp.set("title", f"Figure {NF[0]}")
    para(f"Figure {NF[0]}: {caption}", "FigureCaption")

# ------------------------------------------------------------------ front matter
para("Keeping Language-Model Legal Assistants Current After Statutory Amendments: Update Anomalies, Pattern Listing and the Economics of Maintenance", "Title_document")
para("Update Anomalies in Language-Model Legal Systems", "Short Title")
para("Anonymous Author(s)", "Authors")
para("Anonymous Institution", "Affiliation")
P_ABS = ("Organizations that deploy language-model assistants for legal and compliance questions must keep them current when statutes change, yet the models hold no record of which provisions depend on which. "
 "We study what an amendment does to a model that has learned the earlier text. Using 171 real amendments to 15 United Kingdom Acts, 166 unchanged control provisions, and three open models from two families (Qwen2.5-7B, Qwen3-8B-Base, Olmo-3-7B), "
 "we compare fine-tuning with several retention constraints. Updating only the listed amendments left collateral damage on unrelated provisions that an easy control test understated three to six times. "
 "Unlisted amended provisions followed the update almost entirely when a listed provision carried the same change (0.95 to 0.96) and hardly at all otherwise (0.08 to 0.11); provisions whose values are computed from an amended value did not follow (0.00 to 0.03). "
 "Maintenance effort therefore depends on the number of distinct change patterns rather than on the number of amended provisions. "
 "Pattern listing, which adds one representative per uncovered pattern and every derived dependent, raised the share of amended provisions answered correctly to 0.96 to 0.97 with 35 additional statements, against 85 for full listing, without collateral damage. "
 "We embed these measurements in a cost model with stock accumulation and periodic consolidation, derive thresholds for choosing among policies, and discuss what drafting practice and audit design imply for operators. "
 "The evidence covers UK statute and forced-choice evaluation, and cost parameters are not estimated.")
para(P_ABS, "Abstract")
para("CCS CONCEPTS • Information systems → Information systems applications; • Computing methodologies → Natural language processing; • Applied computing → Law.", "CCSDescription")
para("Additional Keywords and Phrases: statutory amendment, update anomaly, knowledge editing, legal information systems, maintenance economics, large language models", "KeyWords")
para("ACM Reference Format:", "ACMRefHead")
para("Anonymous Author(s). 2026. Keeping Language-Model Legal Assistants Current After Statutory Amendments: Update Anomalies, Pattern Listing and the Economics of Maintenance. ACM Trans. Manag. Inf. Syst. (2026). Manuscript submitted for review.", "ACMRef")

# ------------------------------------------------------------------ 1 Introduction
bank = A["bank"]
H1("Introduction")
P("When a statute changes, an information system that applies it must change with it, and the change rarely stays where it is made. In October 2024 the main United Kingdom capital gains tax rates rose from 10% to 18% for basic-rate taxpayers and from 20% to 24% for higher-rate taxpayers, with effect from 30 October {Koopman2025}. The tax authority’s online filing service was reported not to reflect the change correctly, the update having been finalized after the digital return service had been locked for the tax year, and tax advisers warned that tens of thousands of filers might underpay and face interest and penalties of up to 30% of the unpaid tax {Koopman2025}. The rate provision had been amended; what depended on it had not. The same structure appears when a language model answers questions about the law. In Moffatt v. Air Canada (2024 BCCRT 149), a tribunal held a company to the statement its chatbot had made about a policy and rejected the argument that the chatbot was a separate entity {Moffatt}. The two cases differ, since the first concerns a conventional filing service and the second a conversational one, but they share the feature that motivates this paper: the party that operates the system bears the cost when a change to one rule is not carried through to the statements and values that depend on it.", first=True)
P("Information systems research has long treated this as a problem of maintenance. Adaptive changes keep a deployed system aligned with its environment {Swanson1976, Lehman1980}, and a change to one part of a system can spread to others through dependencies the modifier did not anticipate, the ripple effect {Haney1972}. Conventional systems manage the problem through structure: a relational schema declares keys and dependencies, and normalization exists to avoid the modification anomalies that arise when a fact is stored in several places or a derived value is stored separately {Codd1970, Codd1972}. Legislation has an institutionalized practice of this kind. When a provision is amended, others may refer to it, repeat its wording or depend on a value it fixes, and the amending instrument usually has to deal with those too; drafting guidance calls these consequential amendments and advises a systematic search for every reference to the provision being changed {OPC2025a}. A language model that has learned statutory text has no such structure. Its dependencies are implicit, and the usual interfaces for changing it take statements and not a dependency structure.")
P("Research on model editing has measured part of the problem. Editing one fact can imply changes to related facts, and editors that change the target fact often fail to change what follows from it {Zhong2023, Cohen2024}. That work uses encyclopedic facts, mostly edited one at a time. Statute differs in ways that matter to operators. Amendments arrive in groups, the same sentence is repeated across many provisions, some provisions contain values computed from others, and the conservative instinct of editing research, to leave everything else alone, collides with the fact that some of the “everything else” is what the amendment was meant to change.")
P("We ask three questions. First, how do common update procedures treat the amended provisions, the provisions that were not amended, and the provisions that depend on the amended ones? Second, what determines which unlisted provisions follow an amendment? Third, can an operator choose a policy that is cheap, current and safe, and under what costs does each policy win? We answer them with " + f"{bank['changed']} real amendments to {bank['acts_changed']} United Kingdom Acts, {bank['controls']} unchanged controls, and three open models from two families. We make four contributions.")
BUL(["Measurement. We separate three outcomes that are often run together, currency, continuity and ripple, and show that an easy control test understates collateral damage three to six times (Section 6.2).",
     "Mechanism. We show that unlisted amended provisions follow an update when a listed provision carries the same change, and hardly at all otherwise, whatever their textual similarity to listed provisions; provisions computed from an amended value did not follow (Section 6.3).",
     "Policy. We propose pattern listing and show in a direct test that one representative per uncovered change pattern plus every derived dependent raises correctness from 0.75–0.81 to 0.96–0.97 at 35 additional statements instead of 85, with no collateral damage (Section 6.4).",
     "Economics. We embed the measurements in a cost model with accumulating errors and periodic consolidation, derive thresholds for choosing among policies, and show that maintenance effort scales with the number of distinct change patterns, so that uniform drafting is a public good for operators (Section 7)."])
P("The evidence is limited to United Kingdom statute, forced-choice evaluation, and three open models of 7 to 8 billion parameters. Cost parameters are not estimated. Section 8 sets out what the results do and do not support.")

# ------------------------------------------------------------------ 2 Background
H1("Background and Related Work")
H2("Maintenance, update anomalies and consequential amendments")
P("Information quality research treats timeliness and consistency among related items as properties that users value {WangStrong1996, Pipino2002} and shows that errors propagate through chains of processing {Ballou1985}. Coordination theory states the general case: dependencies between items must be identified and managed by some mechanism {MaloneCrowston1994}. A relational store avoids anomalies by representing dependencies; if the same fact is held in several places, an update to one copy leaves the others stale, and if a value is derived from another and stored as well, an update to the source leaves the derived value inconsistent {Codd1970, Codd1972}. Drafting offices distinguish the change a bill is meant to make from the changes needed to keep the statute book coherent. Australian guidance defines a consequential amendment as an additional amendment required as a result of the main changes and notes that it can be technical, such as correcting a cross-reference, or substantive {OPC2025a}. Transitional and saving provisions do something different: they preserve the old law for cases that arose before commencement {OPC2025b}. The retention constraints used in training have no counterpart in this practice, and we do not claim that they implement a saving clause.")
P("Computational work on legislation has long treated versions and amendments as structured data, representing a provision as a sequence of dated versions {PalmiraniVitali2011}, distinguishing the time a text is in force from the time a norm is applied {PalmiraniBrighi2006}, and analyzing norm change as revision and derogation {Governatori2005} and as theory change {Alchourron1985}. We use these as motivation only. Our setting has a single current version and no dates on the queries.")
H2("Language models: editing, continual learning and retrieval")
P("Methods for changing a fact in a language model without retraining include locating and rewriting weights {Meng2022, Meng2023}, training an editor {DeCao2021, Mitchell2022} and supplying the fact in the prompt {Zheng2023}; see {Yao2023} for a survey. Evaluations that go beyond the edited fact find that related facts often fail to change. A benchmark of about 5,000 edits with logical-consequence queries reports that editors often change the target without keeping related knowledge consistent and that a simple in-context baseline did best {Cohen2024}, and edited models answer paraphrases but fail on multi-hop questions that depend on the edit {Zhong2023}. Fine-tuning on new text can erase earlier competence {French1999, Kirkpatrick2017}, with replay {Rolnick2019} and closeness to the earlier model as standard remedies, and models fall out of date as the world changes {Lazaridou2021, Dhingra2022}. The constraint to stay close to an earlier model is exactly what an amendment must not apply to the amended provision. Retrieval-augmented generation supplies passages from a store at question time {Lewis2020}, and legal question answering is a main application, with documented rates of hallucination, including errors about the current status of authorities {Dahl2024, Magesh2025}. Retrieval moves the dependency question from the weights to the store: a store that contains the old text of a dependent provision returns the old text.")
P("Our design is an artificial evaluation of design alternatives in the sense of design science {Hevner2004, Venable2016}: it controls the structure of the amendment and the launch model, and involves no users or organization.")

# ------------------------------------------------------------------ 3 Problem formulation
H1("Problem Formulation")
P("A fact is a pair (p, v) in which p is a prompt that identifies a provision, for example the statutory text up to the point where a value is stated, and v is the value that completes it. A launch model has learned a bank of N facts. An amendment changes the authorized value of a subset. A fact is a dependent of another if its authorized value is determined by the value of the other; in the real data this is the relation between a net and a gross threshold, or the equality of an upper earnings limit with the sum of a personal allowance and a basic-rate limit. An update procedure receives an update stream, a set of statements of amended provisions with their new values, and may use a retention constraint that keeps selected facts at their launch behavior. A fact is listed if its amended statement is in the stream. We call two amended provisions twins if they carry the same change, that is, the same old and new value (for example, a time limit of three months replaced by six).", first=True)
P("After the update we measure, each as a share of the relevant facts, currency (amended provisions for which the model prefers the new value), continuity (provisions not amended for which the model still prefers the launch value; one minus continuity is collateral damage), and ripple (dependents of amended provisions answered with the new derived value, reported for listed and unlisted dependents separately). These correspond to timeliness, stability of correct output, and consistency among related items. Preference is judged by forced choice between the authorized value and a competitor, the old value for an amended provision. For a control we use two competitors: a random number of the same kind, an easy test, and a different period of the kind that occurs in the Acts (for example “six” for “three”), a hard test. Forced choice shows a preference between two answers and not that the model would produce the correct answer unprompted. The authorized value is the value in force today; queries about earlier dates are not modeled.")
P("A simple identity helps with interpretation. Suppose a procedure retains every fact the update does not mention and releases only those matched to a listed amendment, that unamended facts are retained perfectly, and that matched and released facts take the new value. With ρ the share of facts superseded, c the share of superseded facts the stream mentions, and m the probability that a mentioned fact is matched to the stored fact it amends, currency is (1 − ρ) + ρcm. The identity is an accounting statement, not a prediction about model behavior; the experiments test whether its assumptions hold.")

# ------------------------------------------------------------------ 4 Policies
H1("Update Policies")
P("Table 1 lists the policies. The first four are variants of one fine-tuning procedure that differ in the retention constraint or in what the update stream contains. Pattern listing is the policy we propose. It starts from the listed amendments as in dependency-scoped retention and then adds, for every change pattern in which no provision is listed, one representative provision, and adds every derived dependent. Full listing states every affected provision. Retrieval and in-context editing are baselines.", first=True)
TAB("Update policies and the practice each is closest to", [
 ["Policy", "What it does", "Closest practice in information systems or drafting"],
 ["Amend only", "Fine-tune on the statements of listed amendments; no constraint", "Point update without cascade"],
 ["Retain all", "KL penalty to the launch model on every launch fact (weight λ)", "Write protection of the whole store"],
 ["Stream-scoped retention", "KL penalty on launch facts the update does not mention", "Protection of everything not named in the transaction"],
 ["Dependency-scoped retention", "As stream-scoped, but provisions that belong to the amendment (twins, dependents) are released", "Protection scoped by the dependency graph"],
 ["Pattern listing (proposed)", "Dependency-scoped retention, plus one listed representative of each uncovered change pattern and every derived dependent", "Cascading update of one representative per pattern; consequential amendments for dependents"],
 ["Full listing", "Every affected provision stated in the update", "Consequential amendments listed in the amending instrument"],
 ["In-context editing", "Amended statements placed in the prompt; weights unchanged", "Query-time override"],
 ["Retrieval", "Top three statements retrieved by TF-IDF; store refreshed for listed amendments only (incremental) or for all (full)", "Incremental or full refresh of an index"]],
 note="KL, Kullback–Leibler divergence on the distribution over the answer tokens.", size=7)

# ------------------------------------------------------------------ 5 Data and design
H1("Data and Experimental Design")
H2("Synthetic fact banks")
P("To control the structure of an amendment we first use synthetic banks. In the first, a provision is identified by a rule code and its value is a two-digit number or a category word, with 200 launch facts and 50 further facts that appear only in the update. In the second, the facts are provisions of fictional statutes, each stated in three paraphrases. In the third, each base provision is paired with a dependent whose value is a fixed function of the base value, and an amendment replaces a share ρ of base values. These banks were run on Qwen2.5-7B (and, for the first, on a 70-million-parameter model and Qwen2.5-1.5B).", first=True)
H2("Real amendments")
P(f"The real data come from the United Kingdom legislation database, which publishes the text of an Act as it stood on a given date together with editorial notes on amendments {{Legislation}}. We scanned 24 Acts chosen in advance, without reference to results (employment, company, tax, social security, pension, consumer, insolvency, housing, data protection and financial services law; Appendix B). For 22 of them we compared the text in force on 1 January 2021 with the current text and kept replacements of periods, amounts and percentages, excluding cross-reference renumbering, formatting-only changes and changes whose value also occurs in the preceding context; for the other two the 2021 version could not be retrieved. Fifteen of the 22 Acts contained such changes. The bank also includes 27 amendments from an earlier, hand-directed scan of two of these Acts, and contains {bank['changed']} amended provisions in {bank['acts_changed']} Acts, and {bank['controls']} control provisions: numeric periods that are identical in the 2021 and current text, in sections without any change (66 from the earlier scan after manual curation, 100 added by rule). Each fact is the Act, location, heading and the 16 words that precede the value.")
P(f"The amended provisions fall into {bank['patterns']} distinct change patterns (old and new value), of which {bank['singletons']} contain a single provision; the largest patterns contain {bank['largest'][0]}, {bank['largest'][1]}, {bank['largest'][2]} and {bank['largest'][3]} provisions. They include time limits changed from three to six months, tax thresholds and rates, and the size thresholds of the Companies Act. Eight provisions are derived dependents whose value follows from another amended value: gross thresholds that are about 1.2 times the net thresholds both before and after the amendment (four provisions), and the upper earnings limit of £50,270, which equals the personal allowance (£12,570) plus the basic-rate limit (£37,700) and, before the amendment, £50,000 = £12,500 + £37,500 (four provisions in two Acts). These relations are observations about the text and not rules stated in the Acts. In the upper-earnings-limit cases the dependent provision does not mention the personal allowance or the basic-rate limit.")
H2("Models, training and evaluation")
P("All policies start from a launch model obtained by fine-tuning a pretrained model with LoRA {Hu2022} (rank 16, learning rate 2 × 10⁻⁴) on the pre-amendment value of every fact until token accuracy on the training facts reached 0.995, which happened in every run. The models are Qwen2.5-7B {Qwen25}, Qwen3-8B-Base {Qwen3card} and Olmo-3-7B {Olmo3card}; the last is from a different family and fully open. The update is a fresh LoRA adapter trained for 20 epochs at learning rate 10⁻⁴. Retention is a KL penalty, over the distribution of the answer tokens, between the updated and launch models on a set of anchor facts, with weight 10 unless stated (1 and 10 for retention of all facts). A random draw determines which amended provisions are listed; it is the same across policies for a given seed and share k of amended provisions listed. We report means and ranges over three seeds and no significance tests, since so few seeds do not allow them. Code and data are described in the Declarations.")

# ------------------------------------------------------------------ 6 Results
H1("Results")
H2("Synthetic banks: retention strength and matching")
P("In the first synthetic bank the best strength of retention depends on the share of superseded facts. With no penalty, fine-tuning on the amended facts forgets many untouched ones, so currency is low when few facts were amended. A moderate penalty (λ = 1) gives the best currency up to ρ = 0.5. When most of the bank was superseded, the same penalty holds back facts that should change and the unconstrained update is best from ρ = 0.7. A strong penalty (λ = 10) retains almost all launch behavior, so its currency is close to 1 − ρ (Table 2). The pattern holds in the 70-million-parameter model (two or three seeds per cell) and in the 1.5-billion-parameter model (one seed).", first=True)
TAB("Currency by share of superseded facts ρ and retention strength λ, independent facts", [
 ["ρ", "1.5B, λ = 0", "λ = 1", "λ = 10", "70M, λ = 0", "λ = 1", "λ = 10"],
 ["0.1", "0.72", "0.96", "0.91", "0.53", "0.97", "0.91"], ["0.3", "0.50", "0.91", "0.71", "0.63", "0.89", "0.73"], ["0.5", "0.55", "0.83", "0.53", "0.69", "0.81", "0.53"],
 ["0.7", "0.73", "0.64", "0.31", "0.82", "0.67", "0.32"], ["0.9", "0.90", "0.45", "0.10", "0.92", "0.51", "0.12"]],
 note="1.5B: Qwen2.5-1.5B, one seed. 70M: mean over two or three seeds depending on the cell.")
P("Retaining everything the update does not mention (stream-scoped retention) reaches the ceiling when updates are matched to stored facts without error. With imperfect matching it does not (Table 3). In Qwen2.5-7B, currency matched (1 − ρ) + ρm to within 0.015 in all six settings, which shows that the identity’s assumptions held; its advantage over the best unscoped setting was +0.09 to +0.23 across seeds at exact matching, +0.04 to +0.11 at m = 0.8, and −0.08 to +0.04 at m = 0.6. A break-even therefore lies near a matching accuracy of 0.7 to 0.8.")
TAB("Stream-scoped retention with imperfect matching, Qwen2.5-7B, three seeds", [
 ["ρ", "m", "Stream-scoped, mean [range]", "(1 − ρ) + ρm", "Best unscoped (mean)", "Difference per seed"],
 ["0.3", "1.0", "1.00 [1.00–1.00]", "1.00", "0.88", "+0.09, +0.11, +0.15"], ["0.3", "0.8", "0.95 [0.94–0.96]", "0.94", "0.88", "+0.04, +0.06, +0.11"], ["0.3", "0.6", "0.87 [0.85–0.89]", "0.88", "0.88", "−0.03, −0.04, +0.04"],
 ["0.7", "1.0", "1.00 [1.00–1.00]", "1.00", "0.79", "+0.20, +0.22, +0.23"], ["0.7", "0.8", "0.86 [0.84–0.89]", "0.86", "0.79", "+0.05, +0.11, +0.07"], ["0.7", "0.6", "0.73 [0.69–0.76]", "0.72", "0.79", "−0.03, −0.04, −0.08"]],
 note="Currency of amended provisions. Difference per seed: stream-scoped minus the best unscoped setting in the same seed.")
P("In the banks with dependent provisions, the share of dependents that followed without being listed was zero in all policies and at all three model sizes, with one exception within chance (0.01), whether the dependent’s text referred to the base provision, the mapping was learned from many pairs, or the mapping was stated as text in the launch data. When a fraction of dependents was listed, the share that followed equaled that fraction, and with the complete list currency reached its ceiling. Releasing dependents from retention did not help. This agrees with what multi-hop and arithmetic evaluations found for edits {Zhong2023, Cohen2024}.")

H2("Real amendments: comparing policies across models")
pol = A["policy"]; labs = ["Amend only", "Retain all (λ = 1)", "Stream-scoped retention", "Dependency-scoped retention", "Stream-scoped, all affected provisions listed"]
rows = [["Policy"] + [f"{m}: currency" for m in MODELS] + [f"{m}: controls kept (hard)" for m in MODELS]]
for lab in labs:
    rows.append([lab if "all affected" not in lab else "Full listing (stream-scoped, all affected provisions listed)"] + [f2(pol[m][lab]["currency_mean"]) for m in MODELS] + [f2(pol[m][lab]["hard_mean"]) for m in MODELS])
P(f"Table 4 compares the policies on the {bank['changed']} amended provisions and {bank['controls']} controls when half of the amended provisions are listed (k = 0.5). Across the three models, amending only gave a currency of {f2(pol['Qwen3-8B-Base']['Amend only']['currency_mean'])} to {f2(pol['Qwen2.5-7B']['Amend only']['currency_mean'])} but kept only {f2(pol['Olmo-3-7B']['Amend only']['hard_mean'])} to {f2(pol['Qwen3-8B-Base']['Amend only']['hard_mean'])} of the controls against a hard alternative, that is, collateral damage of 0.10 to 0.12. Against a random number the same update kept 0.97 to 0.98, so the easy test shows collateral damage of 0.02 to 0.03 and understates it by a factor of three to six. Dependency-scoped and stream-scoped retention left the controls unchanged. Blanket retention was harmful: stream-scoped retention lowered currency to 0.42–0.46, because the retained twins pull the listed provisions back towards the old value (listed provisions kept 0.83–0.90) and hold unlisted ones at the old value (0.01–0.02 followed). Dependency-scoped retention, which releases the provisions that belong to the amendment, gave a currency of 0.76 in all three models, close to amending only, and kept all controls.")
TAB("Real amendments, k = 0.5, three seeds: mean currency over all amended provisions, and controls kept against a hard alternative", rows,
    note="Currency: share of the amended provisions that prefer the new value. Controls kept (hard): share of controls for which the true value is preferred to a different period. Full listing states every affected provision.", size=7)
P("The gross and upper-earnings-limit dependents, which follow arithmetically from other amended values, did not follow in any policy except when listed (0.00 to 0.04 when unlisted). The next subsection explains why the other unlisted provisions behave differently.")

H2("Which unlisted provisions follow? Change patterns, not text similarity")
tw = A["twin"]
a_ = {m: tw[m]["Amend only"] for m in MODELS}
P(f"Among amended provisions that were not listed, the share that took the new value depended on whether a twin was listed. Under amend-only fine-tuning, {f2(a_['Qwen3-8B-Base']['with_twin'][0])} to {f2(a_['Olmo-3-7B']['with_twin'][0])} of unlisted provisions followed when a listed provision carried the same change, against {f2(a_['Qwen3-8B-Base']['no_twin'][0])} to {f2(a_['Qwen2.5-7B']['no_twin'][0])} when none did (Figure 1; {a_['Qwen3-8B-Base']['with_twin'][1]} and {a_['Qwen3-8B-Base']['no_twin'][1]} observations per model, pooled over seeds and values of k). Derived dependents followed at 0.00 to 0.03 ({a_['Qwen3-8B-Base']['dependent'][1]} observations, {a_['Qwen3-8B-Base']['dependent'][2]} distinct provisions).", first=True)
FIG("fig_twin.jpg", "Share of unlisted amended provisions answered with the new value under amend-only fine-tuning, by whether a twin (a listed provision with the same change) exists and for derived dependents. Hatching distinguishes the three groups.",
    "Grouped bar chart for three models. Unlisted provisions with a listed twin follow at about 0.95, those without a twin at about 0.1, and derived dependents at about 0.0.", width=4.6)
def tert(m, tw_): return A["twin"][m]["Amend only"][f"tercile_twin{tw_}"]
P(f"Textual similarity to the listed provisions, measured by TF-IDF cosine similarity to the closest listed provision, also predicted following, but mostly through the twin relation. In a logistic regression of following on similarity and on a twin indicator, with standard errors clustered by provision, the coefficient on the twin indicator was {a_['Qwen2.5-7B']['logit']['twin'][0]:.1f}, {a_['Qwen3-8B-Base']['logit']['twin'][0]:.1f} and {a_['Olmo-3-7B']['logit']['twin'][0]:.1f} (p < 0.001) for the three models and on similarity {a_['Qwen2.5-7B']['logit']['sim'][0]:.1f}, {a_['Qwen3-8B-Base']['logit']['sim'][0]:.1f} and {a_['Olmo-3-7B']['logit']['sim'][0]:.1f} (p < 0.001). Within the group without a listed twin, following stayed low even in the most similar third of provisions ({f2(tert('Qwen2.5-7B', 0)[2])}, {f2(tert('Qwen3-8B-Base', 0)[2])} and {f2(tert('Olmo-3-7B', 0)[2])}); within the group with a twin it was high in every third ({f2(tert('Qwen2.5-7B', 1)[0])} to 1.00 in the least and most similar thirds for Qwen2.5-7B). A model that has learned a new value in some provisions applies it to provisions with the same change, and does not otherwise carry it to similar ones. This is the uncontrolled propagation among redundant copies that normalization is meant to prevent, and it is reliable only for twins.")
P("The finding bears on how operators search for provisions to update. The usual heuristics, a search for references and for repeated wording {OPC2025a}, find provisions with shared text. Those are the provisions that need listing least when a twin has been listed. The provisions that need listing most are those with no listed twin and, above all, derived dependents, which in four of our eight cases do not mention the provisions on which they depend.")

H2("Pattern listing")
pt = A["pat"]
def prow(m, lab, k): return pt[m][f"{lab}|{k}"]
rows = [["Model", "Policy", "k", "Extra statements", "Unlisted amended followed", "Controls kept (hard)", "Currency"]]
for m in MODELS:
    for lab, k in (("Amend only", 0.5), ("Dependency-scoped", 0.5), ("Pattern listing", 0.1), ("Pattern listing", 0.25), ("Pattern listing", 0.5), ("Pattern listing", 0.75)):
        v = prow(m, lab, k); rows.append([m, lab, k, f"{v['extra']:.0f}", f2(v["unl_m"]), f2(v["hard_m"]), f2(v["cur_m"])])
P("If twins follow, a single representative per change pattern should be enough. We tested this directly. For each seed and share k of amended provisions already listed, pattern listing adds one randomly chosen provision for every change pattern in which no provision is listed, and adds every derived dependent, with the same retention as dependency-scoped retention. At k = 0.5 it adds 35 statements; stating every affected provision (full listing) would add 85. The additional statements fall as k rises (63, 52, 35 and 20 for k = 0.1, 0.25, 0.5 and 0.75), because fewer patterns are uncovered.", first=True)
P(f"Table 5 and Figure 2 show the result. At k = 0.5, unlisted amended provisions, all of which now have a listed twin, followed at {f2(prow('Qwen3-8B-Base','Pattern listing',0.5)['unl_m'])} to {f2(prow('Olmo-3-7B','Pattern listing',0.5)['unl_m'])} across the three models, correctness over all amended provisions rose from {f2(prow('Qwen3-8B-Base','Dependency-scoped',0.5)['cur_m'])}–{f2(prow('Qwen2.5-7B','Amend only',0.5)['cur_m'])} to {f2(prow('Qwen3-8B-Base','Pattern listing',0.5)['cur_m'])}–{f2(prow('Qwen2.5-7B','Pattern listing',0.5)['cur_m'])}, and no control was lost (1.00 against the hard alternative). The share of unlisted provisions that followed was 0.70 to 0.81 at k = 0.1, where few provisions are listed and each pattern has fewer listed members. The measured follow rate of about 0.9 is the parameter that the cost model of Section 7 needs.")
TAB("Pattern listing compared with amend-only and dependency-scoped updates, three seeds", rows, note="Extra statements: statements added to the update beyond the randomly listed ones. Unlisted amended followed: share of amended provisions not in the update that took the new value. Currency: share of all amended provisions that took the new value (listed and added provisions are trained on and count).", size=7)
FIG("fig_pat.jpg", "Share of amended provisions answered correctly against additional statements listed. Lines connect pattern listing at k = 0.1, 0.25, 0.5 and 0.75; open markers show dependency-scoped retention without extra listing; filled markers show full listing.",
    "Line chart with three models. Correctness rises from about 0.75 with no extra statements to 0.96 to 0.98 for pattern listing with 20 to 35 extra statements, against 1.00 for full listing with 85.", width=4.6)

H2("In-context editing and retrieval")
RAGP = {m: SD + f"res/{TAGS[m]}_rag_{TAGS[m]}.json" for m in MODELS}
RAGS = {}
for m in MODELS:
    p = RAGP[m] if os.path.exists(RAGP[m]) else SD + f"part/rag_{TAGS[m]}.json"
    RAGS[m] = json.load(open(p)) if os.path.exists(p) else []
def rg(m, var, fmt, key):
    v = [r[key] for r in RAGS[m] if r["variant"] == var and r["format"] == fmt and r[key] == r[key]]
    return mean(v) if v else float("nan")
fmts = [("ike_own", "In-context editing, own statement"), ("ike_all", "In-context editing, all statements"), ("rag_incremental", "Retrieval, incremental store"), ("rag_full", "Retrieval, fully refreshed store")]
rows = [["Format", "Model", "Listed", "Unlisted amended", "Unlisted dependents", "Currency"]]
for fm, lab in fmts:
    for m in MODELS:
        rows.append([lab, m] + [("n/a" if math.isnan(rg(m, "launch", fm, k)) else f2(rg(m, "launch", fm, k))) for k in ("listed", "unlisted_AB", "ripple_dep", "currency_all")])
P("We also ran in-context editing and retrieval over a store, with the launch model and with the pretrained model before launch fine-tuning (Table 6 gives the launch model). Placing the amended statement of the question’s own provision in the prompt moved only part of the listed provisions to the new value on the launch model, and none of the unlisted ones. This weakness is a property of the fine-tuned launch model, which has been trained to complete exactly these sentences with exactly one value; on the pretrained model the same prompt preferred the new value for every listed provision. Retrieval over an incrementally refreshed store, in which only listed amendments carry the new text, left unlisted amended provisions and dependents at their old values, as the weight updates did, because the store held the old text of every provision that had not been listed. Retrieval over a fully refreshed store restored the dependents. Whatever the architecture, something has to determine which other provisions are affected by an amendment.", first=True)
TAB("In-context editing and retrieval, launch model, k = 0.5, three seeds (where complete)", rows, note="ike_own: the amended statement of the question’s own provision is placed before the question. ike_all: all listed statements are placed before every question. Incremental store: only listed provisions carry the new text. Full store: the new text for every amended provision. n/a: not yet available.", size=7)

# ------------------------------------------------------------------ 7 Economics
H1("Economics of Maintenance")
H2("A cost model with accumulating errors")
E = A["econ"]; th = A["th"]
P("The measurements suggest that the cost of keeping a system current is governed by what each policy leaves wrong and by the labor it needs. We model an operator facing amendment events at rate α per year. Each event is processed by a policy j that requires m_j additional statements, each costing c, and leaves r_j provisions wrong, counting amended provisions that did not take the new value and controls whose answers were damaged. Wrong provisions remain wrong until the operator performs a full consolidation, which costs F and resets the stock of errors; each wrong provision costs ℓ per year. Wrong provisions accumulate at rate αr_j, so the average stock between consolidations at interval T is αr_jT/2. The average cost per year is αcm_j + F/T + ℓαr_jT/2, minimized at T* = √(2F/(ℓαr_j)) with cost", first=True)
P("Φ_j = α c m_j + √(2 F ℓ α r_j).     (1)")
P("Only the ratios c/ℓ and F/ℓ matter, so we state results as functions of these. We take r_j and m_j from the measurements at k = 0.5: r_j is the mean number of amended provisions answered wrongly plus the number of controls answered wrongly against the hard alternative, and m_j is the number of statements added to the update relative to amend-only (Table 7).")
rows = [["Model", "Policy", "Wrong provisions per event r", "Extra statements m"]]
for m in MODELS:
    for j, nm in (("A", "Amend only"), ("S", "Stream-scoped"), ("D", "Dependency-scoped"), ("P", "Pattern listing"), ("F", "Full listing")):
        rows.append([m, nm, f"{th[m]['r'][j]:.1f}", f"{th[m]['lab'][j]:.0f}"])
TAB("Measured inputs of the cost model per amendment event (k = 0.5)", rows, note="r: amended provisions answered wrongly plus controls answered wrongly (hard alternative; 166 controls). m: statements added beyond amend-only.", size=7)
H2("Propositions")
P("The following statements hold for the model in Eq. 1 under the stated assumptions; each is followed by the measured quantity it uses.", first=True)
c2 = lambda m: th[m]["cstar_alpha2_F300"]
P(f"Proposition 1 (listing replaces consolidation only when cheap). Pattern listing beats dependency-scoped retention if and only if c < c*(α, F) = √(2Fℓ/α)(√r_D − √r_P)/m_P. This threshold falls with the event rate as α^(−1/2): the more often the law changes, the lower the labor cost at which listing at every event pays, compared with periodic consolidation. Evaluated at α = 2, F = 300ℓ, c* is {c2('Qwen2.5-7B'):.1f}ℓ, {c2('Qwen3-8B-Base'):.1f}ℓ and {c2('Olmo-3-7B'):.1f}ℓ for the three models: listing a statement must cost less than about two wrong provision-years. Proof: compare Φ_P and Φ_D in Eq. 1.")
astar = lambda m: th[m]["alpha_star_c2_F300"]; astar1 = lambda m: th[m]["alpha_star_c1_F300"]
P(f"Proposition 2 (churn). For given c and F, pattern listing beats dependency-scoped retention only for event rates below α* = 2Fℓ(√r_D − √r_P)²/(c m_P)². At c = 2ℓ and F = 300ℓ, α* is {astar('Qwen2.5-7B'):.1f}, {astar('Qwen3-8B-Base'):.1f} and {astar('Olmo-3-7B'):.1f} events per year; at c = ℓ it is {astar1('Qwen2.5-7B'):.1f}, {astar1('Qwen3-8B-Base'):.1f} and {astar1('Olmo-3-7B'):.1f}. Because listing labor grows in proportion to α while the cost of periodic consolidation grows with √α, higher churn favors consolidation over listing at every event. The result assumes that F does not itself grow with α.")
nc = lambda m: th[m]["nc_star"]
P(f"Proposition 3 (scope). Dependency-scoped retention beats amend-only if the number of unrelated provisions N exceeds N* = N₀(w_D − w_A)/(κ_A − κ_D), where w_j is the number of amended provisions answered wrongly, κ_j the number of controls damaged among N₀ = 166, and the stock of errors is held fixed. N* is {nc('Qwen2.5-7B'):.0f}, {nc('Qwen3-8B-Base'):.0f} and {nc('Olmo-3-7B'):.0f} provisions for the three models. Real statute books have thousands of unrelated provisions, so scoped retention dominates amend-only for any realistic corpus. Judged by an easy control test, N* would be four to five times larger, because the test understates collateral damage.")
P("Proposition 4 (patterns, not provisions). Under pattern replication with follow rate p_T for twins, the labor of pattern listing is the number of uncovered patterns plus the number of derived dependents, while full listing needs every affected provision. The labor ratio is therefore bounded by the ratio of patterns to provisions: in our bank 74 patterns cover 163 non-dependent amended provisions. Reducing the number of distinct changes by drafting uniformly, so that amendments of the same kind use the same change, lowers maintenance labor by the same proportion for all operators.")
H2("Decision map and thresholds")
FIG("fig_map.jpg", "Cost-minimizing policy as a function of labor cost per statement c and consolidation cost F, in units of the yearly loss ℓ per wrong provision, for three event rates (Qwen3-8B-Base measurements, 166 unrelated provisions). Shading from white to dark: amend only, stream-scoped, dependency-scoped, pattern listing, full listing.",
    "Three panels of shaded regions on a log-log grid. Full listing is optimal when c is small, dependency-scoped retention when c is large, and pattern listing in a band between them that widens when the consolidation cost F is high and shrinks when the event rate rises.", width=5.6)
P("Figure 3 shows the optimal policy over c and F for three event rates. Amend-only and stream-scoped retention were never optimal in the region shown. Full listing is optimal when listing is cheap, dependency-scoped retention (no listing beyond the stream) when listing is dear, and pattern listing in an intermediate band that is wider when consolidation is expensive and narrower when events are frequent. Figure 4 shows total cost as a function of the event rate for a fixed c and F: costs of policies that list grow in proportion to α, those that rely on consolidation grow with its square root.")
FIG("fig_alpha.jpg", "Yearly cost of four policies as a function of the amendment event rate α, with c = 2ℓ and F = 300ℓ (Qwen3-8B-Base measurements). Line styles and markers distinguish the policies.",
    "Log-log line chart. Amend only is the most costly at every event rate, listing policies grow in proportion to the event rate and the consolidation-based policies grow more slowly.", width=3.6)
P("These thresholds depend on c, F and ℓ, which we did not estimate. They describe how the preferred policy changes with these ratios and what ranges of the ratios the measured quantities make relevant; they are not a forecast for any organization. Estimating c and F for real maintenance teams is a matter for field work.")

# ------------------------------------------------------------------ 8 Discussion
H1("Discussion")
H2("Implications for operators, auditors and drafters")
P("For operators, the results suggest four practices, each to be tested on larger and more varied material. First, avoid blanket retention, which was harmful when amended provisions share wording. Second, scope retention to the complement of the amendment’s own provisions, which prevented collateral damage in all three models. Third, ensure that every change pattern in the amending instrument has at least one listed provision and that every derived dependent is listed, which pattern listing does at a fraction of the labor of listing everything. Fourth, check the freshness scope of any retrieval store: an index refreshed only for the amendments someone listed has the same gap as a weight update.", first=True)
P("For auditors, an update should be evaluated in strata: amended provisions, unlisted twins, unlisted dependents and unrelated controls, with controls compared against a plausible alternative and not a random one. An easy control test would have shown collateral damage of 0.02 to 0.03 where the hard one showed 0.10 to 0.12. For drafters and for those who publish consolidated texts, the cost of keeping automated systems current depends on the number of distinct change patterns. A single change applied uniformly to many provisions costs an operator one statement; heterogeneous changes cost one each. The explicit listing of derived values, such as an earnings limit that equals the sum of two other amended values, would help operators because such values do not follow on their own.")
H2("Limitations")
P("The study has clear limits. The amendments are from United Kingdom statute found by scanning 24 pre-selected Acts for changes since 2021; they are not a sample of legislation, the scan keeps only replacements of numeric values, and its candidates were filtered by rules and not all proofread. Only eight provisions are derived dependents, so conclusions about computed values rest on few provisions, although they agree with the synthetic banks and with earlier work. Three models of 7 to 8 billion parameters were used, all with LoRA fine-tuning, which may not represent larger models, full fine-tuning or production retrieval systems; our retrieval is a simple TF-IDF index. The old values were learned by fine-tuning at launch and were not in the model’s pretraining, which makes the experiments controlled but unlike a deployed system. Evaluation is forced choice between two values and does not show what the model would generate. The twin follow rate was measured on randomly chosen representatives; a representative that is atypical could behave differently. The cost model is stylized, assumes errors accumulate linearly and that a consolidation resets them, and takes c, F and ℓ as free parameters; the thresholds are conditional on them. Validity at a point in time is not modeled: overwriting weights erases the old law, which matters for questions about earlier dates, for which versioned retrieval is the more natural design. No users, maintainers or organization were studied, so claims about practice are implications to be tested. Nothing in the paper is legal advice.")

# ------------------------------------------------------------------ 9 Conclusion
H1("Conclusion")
P("When a statute is amended, drafting practice lists the consequential amendments. We asked what the same dependency problem looks like for a language model that has learned statutory text. In 171 real amendments and three models, an update that states only some amended provisions left unrelated provisions damaged, a harm an easy test understates, and left unlisted provisions mostly at the old value unless a listed provision carried the same change. Provisions computed from an amended value did not follow. Maintenance effort therefore depends on the number of distinct change patterns, and pattern listing, one representative per uncovered pattern plus every derived dependent, achieved a correctness of 0.96 to 0.97 with 35 statements instead of 85 and no collateral damage. A cost model with accumulating errors gives thresholds for when to list, when to consolidate and when to scope retention, and shows why uniform drafting benefits operators. The evidence is limited to UK statute and three open models; its main use is to indicate what a larger study with real maintenance teams should measure.")

# ------------------------------------------------------------------ Declarations, references, appendices
para("DECLARATIONS", "AckHead")
para("Funding: none. Competing interests: none. Use of large language models: a large language model was used to assist with drafting and editing the text and with writing and running the experiment code. The authors checked the content and the results and take full responsibility for the paper. Data and code availability: the fact banks, scripts and results are withheld from this blinded version and can be provided to the editor and reviewers on request. Statutory text quoted in the fact banks was retrieved from legislation.gov.uk and is Crown copyright, reproduced under the Open Government Licence v3.0; its terms should be checked before redistribution. Nothing in the paper is legal advice.", "AckPara")
para("REFERENCES", "ReferenceHead")
REF_IDX = len(doc.paragraphs)  # references are inserted at the end after all text is written (numbers fixed by first citation)

# Appendix A: summary of the real bank by Act
H_ = lambda t: para(t, "AppendixH1")
chg = [f for f in BANK if f["kind"] == "changed"]
byact = collections.defaultdict(list)
for f in chg: byact[f["act_name"]].append(f)
rows = [["Act", "Amended provisions", "Most frequent change in the bank"]]
for act, fs in sorted(byact.items(), key=lambda kv: -len(kv[1])):
    c = collections.Counter((f["old"].strip(), f["new"].strip()) for f in fs).most_common(1)[0]
    rows.append([act, len(fs), f"{c[0][0]} → {c[0][1]} ({c[1]} provisions)"])
para("A  AMENDED PROVISIONS BY ACT", "AppendixH1")
P("The table summarizes the 171 amended provisions; the full list with section references is available with the replication materials.", first=True)
TAB("Amended provisions in the real-data bank, by Act", rows, size=7)
para("B  LEGISLATION SCAN", "AppendixH1")
P("Acts scanned, with the text in force on 1 January 2021 compared with the current text: Employment Rights Act 1996, Companies Act 2006, Income Tax (Earnings and Pensions) Act 2003, Income Tax Act 2007, Taxation of Chargeable Gains Act 1992, Inheritance Tax Act 1984, Value Added Tax Act 1994, Capital Allowances Act 2001, Corporation Tax Acts 2009 and 2010, Social Security Contributions and Benefits Act 1992, Data Protection Act 2018, Equality Act 2010, Consumer Rights Act 2015, Limitation Act 1980, Insolvency Act 1986, Housing Acts 1988 and 2004, Pensions Act 2008, Pension Schemes Act 1993, Employment Act 2002, National Minimum Wage Act 1998, Children Act 1989 (current text only) and Financial Services and Markets Act 2000 (current text only). A candidate is a replacement of one to three tokens in which both sides contain a number, spelled-out number, amount or percentage, with a unit in the context, excluding renumbering of cross-references and changes whose value is already in the preceding 16 words. Training: LoRA on all linear layers, rank 16, learning rate 2 × 10⁻⁴, batch size 16, up to 100 epochs, stopping at token accuracy 0.995; update: new adapter, rank 16, learning rate 10⁻⁴, 20 epochs; retention weight 10. Hardware: one 80 GB GPU per run.", first=True)

# references block (numbered by first citation)
for k in CITED:
    p = doc.add_paragraph(style="Bib_entry"); p.add_run(REFS[k])
    # move before the appendix: insert after the REFERENCES heading paragraph
    ref_heading = [q for q in doc.paragraphs if q.text == "REFERENCES"][0]
    ref_heading._p.addnext(p._p) if k == CITED[0] else prev._p.addnext(p._p)
    prev = p
out = "/home/user/fluffy-meme/tmis/TMIS_manuscript_blinded.docx"
os.makedirs(os.path.dirname(out), exist_ok=True); doc.save(out)
txt = " ".join(p.text for p in doc.paragraphs)
print("saved", out, "| words:", len(txt.split()), "| tables:", NT[0], "| figures:", NF[0], "| refs:", len(CITED))
print("abstract words:", len(P_ABS.split()))
