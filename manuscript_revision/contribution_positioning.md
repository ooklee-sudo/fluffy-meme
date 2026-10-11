# Positioning the contribution for an IS journal

This file is advice for the authors, with a draft paragraph. It has three parts: the objection a reviewer is most likely to raise, a tighter statement of the contribution, and the literature to add. References were checked against their public pages; the ones I could not confirm are marked.

## 1. The objection to answer first

A reviewer will say: *"Frame shift" is the default effect, present bias, automation bias and loss aversion put together. What is new?* The manuscript currently answers by naming the construct. That is not enough; each ingredient has an established literature (all cited in Section 2.3 already):

| Ingredient | Existing literature | What the paper adds |
|---|---|---|
| Present bias, planning fallacy | Laibson 1997; O'Donoghue and Rabin 1999; Buehler et al. 1994 | Applies it to refactoring plans |
| Fluency, automation bias | Alter and Oppenheimer 2009; Parasuraman and Manzey 2010; Goddard et al. 2012 | Applies it to reviewing generated code |
| Default effect, loss aversion, endowment | Johnson and Goldstein 2003; Kahneman and Tversky 1979 | Applies it to accepting a suggestion |
| Effort-based valuation | Norton et al. 2012 | Weak ownership of generated code |

**The defensible novelty is not any one of these.** It is two things the paper already has and should put first:

1. **The construct is a change in the decision's structure, not a new bias.** With an assistant, an artifact exists before the quality decision is made. That turns a choice between two future outcomes into an accept-or-reject decision about something already in hand, and it is why all four biases apply together. State this as a theoretical claim with a boundary condition (it applies when generation precedes the decision), not as a label.
2. **A result that separates the behavioral account from its rational rival.** Result 2 shows that aggregate debt cannot tell the two apart, and that three statistics can. This is the part a reader cannot get from the existing literature. It also disciplines the empirical work, because it says which tests can and cannot discriminate.

## 2. A tighter statement of the contributions

I would reduce the claims to a primary one and two consequences:

- **Primary (theory).** The choosing-to-accepting shift, formalized, and what separates it from rational acceleration (Results 1–2). Evidence: the possession effect and the lapse of planned refactoring, measured in the experiment (Study 2).
- **Consequence 1.** Under the shift, better models need not mean less debt (Result 3) and present bias can trap a codebase (Result 4).
- **Consequence 2 (governance).** Who controls the assistant's configuration matters more than market structure, bounded by shadow-IT bypass (Results 5–7).

Result 8 (learning) is an extension that can go to an appendix or a short section. The paper currently presents eight results and eleven propositions with equal weight; reviewers will read that as a catalogue.

**Draft contribution paragraph** (for the end of the Introduction):

> We argue that generation-first assistance changes the structure of a developer's decision, not merely the cost of its options. An artifact now exists before the quality decision is made, so a choice between an expedient and a quality implementation becomes a decision about whether to accept something already in hand. We formalize this change and show that, although it can raise aggregate technical debt, so can a rational response to faster development; aggregate debt therefore cannot adjudicate between the accounts, whereas the self-admitted share of debt, the effect of possessing an artifact on refactoring, and the lapse of planned refactoring can. We then derive two consequences: more reliable models can raise debt, and an organization's control over tool configuration, rather than vendor competition, governs how much debt developers' defaults produce. We test the discriminating statistics experimentally and report early field evidence from public repositories.

Adjust the last sentence to what is actually completed.

## 3. Literature to add

**Verified (public pages checked):**

- Peng, Kalliamvakou, Cihon and Demirer (2023), *The Impact of AI on Developer Productivity: Evidence from GitHub Copilot*, [arXiv:2302.06590](https://arxiv.org/abs/2302.06590). A randomized experiment; the Copilot group finished an HTTP-server task 55.8% faster. This is the standard evidence for the speed side that the paper's rational-acceleration account needs.
- METR (2025), *Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*, [metr.org](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/). A randomized trial with 16 experienced developers; allowing AI increased completion time by 19% although developers expected a 20% reduction. Relevant to the perception wedge: developers misjudge the tool's effect. Cite the full paper from the page (author list: check).
- Dell'Acqua et al., *Navigating the Jagged Technological Frontier*. A preregistered experiment with 758 knowledge workers at a consulting firm; AI helped inside the frontier and hurt outside it. The search showed an Organization Science listing (volume 37, issue 2, 2026) alongside the 2023 working paper; verify the citation before using it.
- Liu, Widyasari, Zhao, Irsan, Chen and Lo (2026), *Debt Behind the AI Boom: A Large-Scale Empirical Study of AI-Generated Code in the Wild*, [arXiv:2603.28592](https://arxiv.org/abs/2603.28592) (preprint). 302.6 thousand AI-authored commits from 6,299 repositories; static analysis before and after each commit; 484,366 issues, 89.3% code smells; more than 15% of commits from every assistant introduced at least one issue, and 22.7% of tracked issues were still present in the latest version.
- Mujahid and Imran (2026), *"TODO: Fix the Mess Gemini Created": Towards Understanding GenAI-Induced Self-Admitted Technical Debt*, [arXiv:2601.07786](https://arxiv.org/abs/2601.07786), TechDebt 2026. Of 6,540 comments referencing LLMs, 81 (about 1.2%) also admitted technical debt, mostly postponed testing and incomplete integration. They propose "GenAI-Induced Self-admitted Technical debt".

**Why the last two matter.** Both are close to the paper's empirical territory. The first already measures debt introduced by AI-authored code with static analysis, so the paper cannot claim the descriptive finding; the second studies self-admitted debt with LLMs. The paper's contribution has to be the theory and the discriminating tests, not the observation that debt rises or is rarely admitted. The Liu et al. data are also a route to the missing static-analysis measure for P4.

**Not found:** I did not find a verified MIS Quarterly or Information Systems Research paper on this specific topic. Search those journals directly (and the IS conference proceedings) for human-AI collaboration, automation bias, IT governance and shadow IT, and cite what a reviewer from those journals would expect.

## 4. Other likely objections and how to meet them

| Objection | Response available |
|---|---|
| "The behavioral parameters are assumed, not shown." | Study 2 recovers β and λ separately (see `study2/study2_protocol.md`). Without it, this objection stands. |
| "Rational acceleration is a strawman." | It is built as the strongest rival (it can match any aggregate level, Result 2a) and the discriminating statistics are derived from it. Say so explicitly. |
| "Too many results; unclear what the paper is about." | Cut to the primary claim and two consequences (section 2). |
| "Observational evidence is correlational." | State what each test can and cannot show (Table 2 logic); lean on the experiment for mechanism and on a design with adoption timing (event study) for the field. |
| "Closed forms rely on constant rework cost and uniform inspection time." | The paper says sign results are general (Appendix B); make sure that proof is complete, since I could not check it. |
