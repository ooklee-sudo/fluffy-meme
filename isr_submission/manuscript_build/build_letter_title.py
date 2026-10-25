from docbuild import *
from docx import Document
TITLE_TXT = "Reach Before Price: When AI Testing Services Get Adopted, and Why Vendors Invest in Reach in Discrete Jumps"

# ---------------------------------------------------------- word count of the main text
def count_words(path):
    doc = Document(path); n = 0; on = False
    for p in doc.paragraphs:
        t = p.text.strip()
        if t == "1. Introduction": on = True
        if t == "References": break
        if on: n += len(t.split())
    return n
NW = count_words("../Manuscript_blinded.docx")

# ---------------------------------------------------------- title page
d = new_doc(spacing=1.5, footer=False)
TITLE(d, TITLE_TXT, size=16)
P(d, "Ook Lee", indent=False, align="center", bold=True, spacing=1.15)
P(d, "Department of Information System, Hanyang University, Seoul, Korea", indent=False, align="center", size=11, spacing=1.15)
P(d, "ooklee@hanyang.ac.kr  ·  [ORCID, optional]", indent=False, align="center", size=11, spacing=1.15, after=12)
P(d, "**Corresponding author:** Ook Lee, ooklee@hanyang.ac.kr [postal address to be added]", indent=False, size=11, spacing=1.15, after=10)
H1(d, "Abstract")
P(d, "Vendors of AI-assisted software testing sell two things that buyers tend to run together: speed, meaning how fast a tool finds faults, and reach, meaning how large a share of the faults that a competent human team could eventually find the tool can find at all. We build a model that separates the two. A firm with heterogeneous stakes chooses a testing budget under a Goel–Okumoto fault-discovery process, and a monopolist sets a usage price and, in a second step, chooses how much to invest in reach. Adoption is a single interval of stakes. When the tool's reach falls short of the human baseline, the interval is bounded, and the highest-stakes firms stay with human testing under every pricing scheme in which the net transfer to the firm is bounded. When reach matches the baseline, the bound disappears. The vendor's profit is continuous in reach but has a kink at parity, and as a result the optimal investment jumps from none to parity at a cost threshold and then stays at parity over an interval of costs. A planner's threshold lies strictly above the vendor's, so a subsidy of limited size changes nothing for vendors in an intermediate cost range. All results are proved except where we say otherwise; the quantitative illustrations use uncalibrated parameters. Public data on coding agents and open-source defect reports are consistent with the model's building blocks but do not test it.", indent=False, size=11, spacing=1.3, align="justify")
P(d, "**Keywords:** AI-assisted testing; software reliability; nonhomogeneous Poisson process; technology adoption; vendor pricing; reach investment; economics of information systems", indent=False, size=11, spacing=1.3, before=8)
P(d, f"**Manuscript length:** about {NW:,} words of main text (Introduction through Conclusion), 5 figures, 4 tables in the main text; Online Appendix submitted separately.", indent=False, size=11, spacing=1.3, before=4)
H2(d, "Acknowledgments")
P(d, "[To be completed by the authors. Omit from the blinded manuscript.]", indent=False, size=11, spacing=1.3)
H2(d, "Funding and competing interests")
P(d, "[To be completed by the authors.]", indent=False, size=11, spacing=1.3)
H2(d, "Data and code availability")
P(d, "All code and derived data tables needed to reproduce the numerical results and figures are provided in the replication package. Raw public data (Public Jira Dataset, SWE-bench Verified, a public collection of coding-agent trajectories, and a public replication package of an AI-coding-assistant adoption study) are available from their original sources; the package contains scripts and instructions to download them. No proprietary or firm-level data are used.", indent=False, size=11, spacing=1.3)
H2(d, "Use of generative AI tools")
P(d, "[The authors must describe here any use of generative AI tools in the preparation of the manuscript, code, or analysis, in line with the journal's policy, and confirm that they take responsibility for the content.]", indent=False, size=11, spacing=1.3)
d.save("../Title_Page.docx")

# ---------------------------------------------------------- cover letter
d = new_doc(spacing=1.15, footer=False)
P(d, "[Date]", indent=False, after=10)
P(d, "[Name], Editor-in-Chief / Department Editor", indent=False)
P(d, "*Information Systems Research*", indent=False)
P(d, "INFORMS", indent=False, after=10)
P(d, "**Re: Submission of “" + TITLE_TXT + "”**", indent=False, after=10)
P(d, "Dear Professor [Name],", indent=False, after=8)
P(d, "We are submitting the manuscript above for consideration at *Information Systems Research*. The paper studies a question that sits squarely in the economics of information systems: when does a firm buy an AI-based service for a core IT activity, software testing, and how should the vendor of that service choose what to invest in? The manuscript has not been published and is not under review elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Summary of the paper")
P(d, "Marketing for AI testing tools emphasizes speed. We argue that buyers and vendors should distinguish speed from *reach*, the share of the fault pool that a competent human team could find that the tool can find at all. The two enter the firm's problem in different places. Reach sets the ceiling on what testing can save, while speed and price only determine how soon the firm gets close to it. We embed this distinction in a Goel–Okumoto testing model with heterogeneous firms and a monopoly vendor that chooses a usage price and, before that, its investment in reach.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Statement of contribution")
P(d, "The paper makes four contributions. We state each together with what we believe is its relationship to prior work, and we flag where we have not established novelty.", indent=False, spacing=1.3, after=4, align="justify")
BUL(d, [
 "**A decomposition of AI testing value into speed and reach, with a closed-form solution.** The net saving from testing has a closed form (Lemma 1), and reach appears as a multiplicative ceiling while speed and price enter only through an effectiveness index. This builds on the NHPP literature on optimal testing and release (Goel and Okumoto 1979; Okumoto and Goel 1980; Ji, Mookerjee, and Sethi 2005, in this journal) by making the technology's reach a separate attribute and by asking who adopts a vendor-supplied technology.",
 "**A characterization of who adopts, and a price-independent exclusion result.** Adoption is a single interval of stakes that is bounded if and only if reach is below the human baseline (Proposition 2, proved with a single-crossing argument). For any contract with bounded net transfers to the firm, the highest-stakes firms stay with human testing (Proposition 3). Richer pricing, such as committed-spend menus (Bergemann, Bonatti, and Smolin 2026), changes the vendor's profit but not who is excluded at the top. We are not aware of this result in the work we reviewed.",
 "**A discrete rule for vendor investment in reach.** We show that the vendor's profit is continuous in reach with a kink at the human baseline, steep from the left (Proposition 7), so that optimal investment jumps at a cost threshold and bunches at parity over an interval of costs (Propositions 6 and 8). To our knowledge the shape of the profit function and the bunching result are new, though the tools used to derive them are standard.",
 "**Policy implications that follow from the structure.** The planner's investment threshold exceeds the vendor's, so there is a window of under-investment, and a proportional subsidy has a threshold effect (Proposition 9). Price regulation and vendor liability do not remove the exclusion, while an instrument that lowers the cost of extending reach can. Extensions in the Online Appendix cover private information about reach, duopoly, learning from usage, and mixed-complexity markets. We treat the signaling extension as an application of known mechanisms (Bakshi, Kim, and Savva 2015; Bauer 2026), not as a contribution.",
], size=None)
H2(d, "Fit with Information Systems Research")
P(d, "The paper addresses the adoption and pricing of an IT service, the economics of software development and quality, and the strategic behavior of a technology vendor, topics the journal has published on. It is primarily an analytical-modeling paper. The empirical section uses public data to check three building blocks of the model, and we are explicit that it does not test the model's central predictions. A firm-level test would require data on stakes and adoption that public sources do not offer; the Online Appendix describes an identification strategy and we would welcome the editors' guidance on whether such a test is expected for this type of contribution.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Limitations we would like the editors to know about")
BUL(d, [
 "The model is static, with a monopoly vendor, risk-neutral firms, and human and AI testing treated as alternatives. Quantitative illustrations use parameters that we chose to display mechanisms; they are not calibrated.",
 "Most results are proved. The kink result (Proposition 7) is proved under a stated condition and for lognormal stakes, and the global maximum behind the bunching result (Proposition 8) is verified numerically, not proved. These distinctions are marked in the text and in Table A1 of the Online Appendix.",
 "Our claims of novelty are limited to the literature we reviewed, which includes recent working papers on AI pricing, signaling, and adoption and the IS and operations literature on software testing. We have not completed a systematic search of the published literature.",
 "The public-data evidence is indicative. A crude test of the adoption-interval prediction using GitHub stars as a proxy for stakes was uninformative, and we report it as such.",
], size=None)
H2(d, "Replication and compliance")
P(d, "A replication package with code, derived data, and instructions for obtaining the public raw data is provided. It contains a script that reproduces the numbers cited in the text. No proprietary data are used and no human subjects are involved. The authors declare no competing interests [to be confirmed]. [The authors should state here how generative AI tools were used in preparing the manuscript, code, and analysis, per the journal's policy.]", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Suggested editors and reviewers")
P(d, "[Authors to complete. Suggest a Department Editor and Associate Editor with expertise in the economics of IS and software, and three to four reviewers with no conflicts of interest. We have not chosen names because we have not verified the current editorial board.]", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Thank you for considering our work.", indent=False, after=10)
P(d, "Sincerely,", indent=False, after=24)
P(d, "Ook Lee", indent=False)
P(d, "Department of Information System, Hanyang University, Seoul, Korea", indent=False)
P(d, "ooklee@hanyang.ac.kr", indent=False)
d.save("../Cover_Letter.docx")
print("saved", NW)
