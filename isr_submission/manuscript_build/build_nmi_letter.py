from docbuild import *
T = "Reach, not speed, limits who benefits from AI testing tools and where vendors invest"
d = new_doc(spacing=1.15, footer=False)
P(d, "[Date]", indent=False, after=10)
P(d, "The Editors", indent=False); P(d, "*Nature Machine Intelligence*", indent=False, after=10)
P(d, "**Manuscript: “" + T + "”**", indent=False, after=10)
P(d, "Dear Editors,", indent=False, after=8)
P(d, "I submit the manuscript above as an Article for consideration in *Nature Machine Intelligence*. It has not been published and is not under consideration elsewhere.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "The question and the finding")
P(d, "AI tools for software testing are evaluated and sold mostly on speed and benchmark pass rates. I argue that a second attribute, *reach* (the share of the faults a competent human team would eventually find that the tool can find at all), governs who benefits from such tools and what developers of them have reason to build. I give a simple, analytically tractable model in which reach and speed enter in different places: reach sets a ceiling on the value of testing, whereas speed and price determine how soon it is approached.", indent=False, spacing=1.3, after=8, align="justify")
BUL(d, [
 "Adopters form a single interval of stakes. Below the human baseline the interval is bounded, and the firms with the most to lose from undetected faults stay with human testing under any contract with bounded transfers, including menus, two-part tariffs and warranties. At the baseline the bound disappears.",
 "A developer's profit is continuous in reach but has a kink at the human baseline. As a result, optimal investment in reach jumps from none to parity at a cost threshold and stays at parity over a range of costs. The social optimum lies beyond the vendor's, so a modest subsidy can have no effect on marginal developers.",
 "Public data on coding agents (resolution rates falling from 40% to 5% as human fix time rises; solve rates that depend on attempt budget) and on open-source defect histories (saturating discovery in 80% of 3,333 releases) are consistent with the model's building blocks.",
], size=None)
H2(d, "Why this is relevant to the journal's readers")
P(d, "The paper concerns how the capabilities of deployed AI systems should be characterized, and what incentives shape which capabilities get built. It suggests that evaluating a tool by speed and pass rate at a fixed budget can mislead the people who must decide whether to rely on it, and that the payoff to broadening what a system can do may concentrate at a specific benchmark, human parity. These points bear on how AI evaluation and procurement are designed. I recognize that the paper is theoretical and draws on economics; I would be grateful for the editors' view of whether it fits the journal's scope, and I am happy to send a pre-submission inquiry or a shortened version if that is more appropriate.", indent=False, spacing=1.3, after=8, align="justify")
H2(d, "Limitations")
BUL(d, [
 "The model is static, with a monopoly vendor, risk-neutral firms and two technologies that are alternatives. Quantitative values use illustrative parameters and are not calibrated.",
 "Most results are proved. The kink result is proved under a stated condition for lognormal stakes, and the global maximum behind the bunching result is verified numerically. These distinctions are marked in the text and in the Supplementary Information.",
 "The public-data evidence is indicative. It does not test the model's adoption or exclusion predictions, which would need firm-level data on stakes and adoption. A crude test with a poor proxy for stakes was uninformative, and the paper says so.",
], size=None)
H2(d, "Compliance")
P(d, "No human participants or personal data are involved. Code and derived data are provided in a replication package, with instructions for obtaining the public raw data. The author declares no competing interests [to be confirmed]. [State here how generative AI tools were used in preparing the manuscript, code and analysis, as the journal's policy requires.] The Reporting Summary is completed at submission. Suggested reviewers: [to be completed by the author].", indent=False, spacing=1.3, after=8, align="justify")
P(d, "Sincerely,", indent=False, after=24)
P(d, "Ook Lee", indent=False); P(d, "Department of Information System, Hanyang University, Seoul, Korea", indent=False); P(d, "ooklee@hanyang.ac.kr", indent=False)
d.save("../NMI_Cover_Letter.docx")
