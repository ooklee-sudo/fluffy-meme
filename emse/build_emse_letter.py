import sys, json; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
R = json.load(open("../reach_pilot/emse_results.json"))
MS = ["Claude Haiku 5.5", "Claude Sonnet 5.5", "DeepSeek V4.1 Flash"]
m1 = [R["mutation"][m][0]["A"] for m in MS]; m8 = [R["mutation"][m][-1]["A"] for m in MS]; r6 = [R["real_faults"][m][-1]["A"] for m in MS]
anyr = R["real_faults"]["Any of the three"][-1]["A"]; V = R["validity"]
T = "Mutants overstate what LLM-written unit tests can find: reach on mutants and on real faults"
d = new_doc(spacing=1.15, footer=False)
P(d, "Ook Lee", indent=False); P(d, "Department of Information Systems, Hanyang University, Seoul, Republic of Korea", indent=False); P(d, "ooklee@hanyang.ac.kr", indent=False, after=10)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editors-in-Chief", indent=False); P(d, "*Empirical Software Engineering*", indent=False, after=10)
P(d, "**Submission of a research article: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editors,", indent=False, after=8)
P(d, "I submit the manuscript above for consideration as a regular research article in *Empirical Software Engineering*. It has not been published and is not under consideration elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "What the study asks and finds")
P(d, f"Unit tests written by large language models are usually evaluated by coverage and mutation scores. The study asks whether these measures tell a team what it needs to know before relying on generated tests: the share of faults the tests reveal. With the same three models and prompts, it measures this reach on 947 AST mutants of seven library modules and on {R['n_bugs']} validated real faults from seven BugsInPy projects, with up to eight independent attempts and bootstrap intervals that resample modules or projects. The main findings are:", indent=False, spacing=1.3, after=4, align="justify")
BUL(d, [
 f"On mutants, LLM-written tests reach or exceed the existing tests within one or two attempts (reach {min(m1):.2f}–{max(m1):.2f} at one attempt, {min(m8):.2f}–{max(m8):.2f} at eight).",
 f"On real faults, six attempts reveal only {min(r6):.2f}–{max(r6):.2f} of the faults, and all three models together {anyr:.2f}.",
 f"Most failing generated tests are wrong rather than revealing: {min(v['any_fail_buggy'] for v in V.values())*100:.0f}–{max(v['any_fail_buggy'] for v in V.values())*100:.0f}% of attempts contain a test that fails on the faulty version, but only {min(v['detected'] for v in V.values())*100:.0f}–{max(v['detected'] for v in V.values())*100:.0f}% reveal the fault, which links the gap to the oracle problem.",
 "Translated into a decision bound, the measured real-fault reach limits the substitution of generated tests for developer tests to low-stakes settings, whereas mutation scores would suggest no limit.",
], size=None)
H2(d, "Fit with the journal")
P(d, "The paper is an empirical study of a widely used class of tools, with a design that measures the same tests against two ground truths and reports both, a threats-to-validity analysis, and a full replication package. It speaks to practitioners who evaluate generated tests and to researchers who use mutation scores as a proxy for fault detection.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Transparency")
BUL(d, [
 "During the study I found and corrected an error in the mutation harness (truncated test names); the affected results were recomputed from the stored generated tests, and the correction is described in the manuscript and the replication package.",
 "The interpretation in RQ4 uses a decision bound from a separate theoretical manuscript of mine on the economics of AI testing tools; the empirical study, data and results reported here are not part of that manuscript.",
 "Limitations stated in the paper include the concentration of real faults in two projects, the hint given by the changed files, possible training-data contamination, and the restriction to Python.",
], size=None)
H2(d, "Declarations")
P(d, "Code, prompts and all results are available at https://doi.org/10.5281/zenodo.23674752. No human participants were involved. I declare no competing interests. Generative AI use is disclosed in the manuscript: the studied tests were written by three LLMs, and an AI coding assistant was used to write analysis code and to draft and edit text, which I reviewed. Suggested reviewers: [optional — to be completed in the submission system].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Thank you for considering this submission.", indent=False, after=8)
P(d, "Sincerely,", indent=False, after=20)
P(d, "Ook Lee", indent=False)
d.save("EMSE_Cover_Letter.docx"); print("ok")
