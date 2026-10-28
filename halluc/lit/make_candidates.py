"""Turn candidates.json (Crossref metadata) into a topic-wise reading list (CANDIDATES.md). Title-based filtering only."""
import json
import re

rows = json.load(open("candidates.json"))
JW = {"Information Systems Research": 3, "MIS Quarterly": 2, "Management Science": 1,
      "Journal of Management Information Systems": 1, "Journal of the Association for Information Systems": 1}
AI = r"(AI\b|artificial intelligence|algorithm\w*|machine learning|generative|LLM\w*|language model\w*|ChatGPT|GPT|automat\w*|chatbot\w*)"
TOPIC_RULES = {
    "Human–AI collaboration and delegation": (AI, r"(collaborat\w*|delegat\w*|human[- ](AI|machine|algorithm)\w*|augment\w*|hybrid|teaming|in the loop|human[- ]centered)"),
    "Reliance on AI advice, automation bias, explanations": (AI, r"(reliance|overreliance|advice|advis\w*|explainab\w*|explain\w*|conform\w*|aversion|appreciation|trust\w*|bias\w*|judg\w*)"),
    "Generative AI and large language models": (r"(generative|LLM\w*|language model\w*|ChatGPT|GPT|hallucinat\w*)", r".*"),
    "Oversight, auditing, accountability, governance of AI": (AI, r"(oversight|audit\w*|accountab\w*|governance|responsib\w*|regulat\w*|compliance|transparen\w*|disclos\w*)"),
    "IT governance, control, and quality assurance": (r".*", r"(governance|control\b|assurance|verification|verif\w*|audit\w*|compliance|quality)"),
    "Fact-checking and misinformation detection": (r".*", r"(fact[- ]?check\w*|misinformation|disinformation|fake news|credib\w*)"),
    "Task–technology fit and AI": (AI, r"(task|fit\b)"),
}

STATUS = """## Status after reading (updated as papers are read; details in READ_NOTES.md)

| Paper | Read? | Outcome |
| --- | --- | --- |
| Leng & Yuan (2026, ISR) | Yes (partly) | No overlap (behavioral audit of LLMs before deployment); cited in Section 2 |
| Bouayad, Padmanabhan & Chari (2019, ISR) | Yes (partly) | No overlap (audit selection with deterrence, strategic audited parties); cited in Sections 2 and 8.1 |
| Taudien, Fügener, Gupta & Ketter (2026, ISR) | Yes (partly) | Related (signals and feedback in delegation to an image classifier); cited in Section 8.4, Prediction 5 |
| Jussupow, Bauer, Heigl, Vogt & Hinz (2026, ISR) | Yes (partly) | Related as a boundary for provenance recording; cited in Section 8.2 |
| Shi & Viswanathan (2023, ISR) | Yes (partly) | **Not relevant** (phone verification of user identity in online dating); the title-based guess was wrong; not cited |
| All other entries | No | Unread; do not cite |
"""

SHORTLIST = """## Suggested first reads (a guess from titles only)

Tier A: closest to our problem; read these first because they decide how the contribution is positioned.

| Paper | Why the title suggests it matters | What to look for |
| --- | --- | --- |
| Leng & Yuan (2026, ISR), *SUVA: A Probabilistic Framework for Auditing LLMs with an Application to Social Preferences* | Auditing LLMs probabilistically | Does it already model where LLM errors occur, or how to allocate audit effort? Is our contribution distinct? |
| Bouayad, Padmanabhan & Chari (2019, ISR), *Audit Policies Under the Sentinel Effect: Deterrence-Driven Algorithms* | Audit policy as an algorithmic design problem in ISR | The audit-theory framing we used in Section 8.1; how ISR authors treat audit allocation |
| Taudien, Fügener, Gupta et al. (2026, ISR), *Enhancing AI Use: How Complementary System Information Drives Delegation Frequency and Effectiveness* | Information about the AI's strengths and delegation | Related to provenance and risk signals (Section 8.2) |
| Jussupow, Bauer, Heigl et al. (2026, ISR), *The Indirect Disclosure Effect: How Disclosing Generative AI Use Impacts Human Creative Collaboration with AI* | Disclosure of generative-AI use | Related to provenance as a design feature (Section 8.2) |
| Shi & Viswanathan (2023, ISR), *Optional Verification and Signaling in Online Matching Markets* | Economics of verification in ISR | Modeling conventions for verification costs and signals |

Tier B: reliance on machine advice and human–AI collaboration (Sections 2 and 8.4).

| Paper | What to look for |
| --- | --- |
| Fügener, Grahl, Gupta & Ketter (2022, ISR), *Cognitive Challenges in Human–Artificial Intelligence Collaboration* | Already cited; confirm what it shows about delegation |
| Bauer, von Zahn & Hinz (2023, ISR), *Expl(AI)ned: The Impact of Explainable AI on Users' Information Processing* | Effects of explanations on how people process information |
| von Zahn, Liebich, Jussupow et al. (2026, ISR), *Knowing (Not) to Know: Explainable AI and Human Metacognition* | Reliance and metacognition |
| Shan, Risius, Wattal et al. (2026, MISQ), *The Differential Impact of AI Versus Human Fact-Checkers on News Believability* | Fact-checking by AI versus humans |
| Jussupow, Benbasat & Heinzl (2024, MISQ), *An Integrative Perspective on Algorithm Aversion and Appreciation in Decision-Making* | A review that could anchor Section 8.4 |

Tier C: background and positioning (skim): Liu, Yue, Leung et al. (2025, MISQ) on delegation dynamics; Grisold, Berente & Seidel (2025, MISQ) on guardrails for human–AI ecologies; Basu, Dennis, Garimella et al. (2026, ISR) on asymmetric algorithm aversion; Liel & Zalmanson (2025, JMIS) on algorithmic conformity; Benbya, Strich & Tamm (2024, JAIS) on generative-AI promises and perils.

**What to send back.** For each paper you read: the abstract, the introduction (about the first two pages), the paragraph(s) where the contribution is stated, and the reference entry. Tell me which ones you want cited and how they relate to our argument (builds on, contrasts with, overlaps with). I will rewrite Section 2 using only what you send, and I will not cite a paper whose content I have not been shown.
"""

out = ["# Candidate reading list for Section 2 (metadata only)", "",
       "**Status of this list.** Retrieved from Crossref (the INFORMS site is behind a bot challenge). Only titles, authors, years and DOIs were obtained. "
       "**None of these papers has been read by the assistant, and a title does not tell what a paper argues.** Filtering is by title keywords only. "
       "Use the list to decide what to read through institutional access; cite only what you have read. Search date 2026-10-28; "
       f"{len(rows)} unique records came back from the searches, of which the topic filters below keep the ones shown.", ""]
out.append(STATUS)
out.append(SHORTLIST)
kept_total = set()
for topic, (a_re, t_re) in TOPIC_RULES.items():
    lst = [r for r in rows if topic in r["topics"] and re.search(a_re, r["title"], re.I) and re.search(t_re, r["title"], re.I)]
    lst.sort(key=lambda r: (-JW[r["journal"]], -(r["year"] or 0), -r["hits"]))
    out += [f"## {topic}", "", f"{len(lst)} records pass the title filter; the first {min(len(lst), 12)} are shown (journal priority ISR > MISQ > others, then newest).", "",
            "| Year | Journal | Authors | Title | DOI |", "| --- | --- | --- | --- | --- |"]
    for r in lst[:12]:
        out.append(f"| {r['year']} | {r['journal']} | {r['authors']} | {r['title'].replace('|', '/')} | https://doi.org/{r['doi']} |")
        kept_total.add(r["doi"])
    out.append("")
open("CANDIDATES.md", "w").write("\n".join(out))
print("records kept across topics:", len(kept_total))
