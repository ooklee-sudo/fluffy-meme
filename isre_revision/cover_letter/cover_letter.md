[[Date]]

Professor [[Name]]
Department Editor, Information Systems
*Management Science*

Dear Professor [[Name]],

We are pleased to submit our manuscript, "When Do Better AI Coding Tools Ship Fewer Defects? Detectability, Verification, and Liability," for consideration in the Information Systems department of *Management Science*.

Generative AI now writes a large share of new code, and every line of it still has to be checked. A natural worry is that developers check less as the tools improve, so that part of each improvement never reaches users. Risk compensation, moral hazard, and the literature on automation complacency all predict this response, but they predict only its direction. Managers who value these tools and regulators who are beginning to assign liability for generated code need its size. Our paper shows that the size is governed by a property of the detection technology that can be measured from ordinary test runs.

The paper makes three contributions. First, we show that the share of a quality improvement that survives verification depends only on how unevenly detectable defects are. With linear verification cost, the elasticity of shipped defects with respect to the tool's defect intensity equals CV²/(1 + CV²), where CV is the coefficient of variation of detection rates among the defects not yet found. The result needs no distributional assumption, and complete offsetting turns out to be a knife-edge case. Second, we model what is distinctive about AI-generated code: as models improve, they may make errors that are harder to see as well as fewer errors. We derive a verification-adjusted measure of tool quality and the threshold beyond which a better model would increase shipped defects. Third, we show that the same heterogeneity determines whether developer liability and tool quality are complements, and hence whether weak liability lowers vendors' investment in quality.

We take these quantities to data. In 25,120 solutions written by eight language models for 157 HumanEval+ tasks, detectability is strongly heterogeneous, and about 40 percent of a proportional quality gain would be absorbed by reduced verification. Across a wider panel of 25 models, stronger models also make defects that are harder to detect. This does not come close to the threshold at which improvements would stop reaching users, but it absorbs a further 17 percentage points. Less than half of the defect reduction that a better model shows on a benchmark therefore survives as fewer shipped defects. The heavy tail and the shift toward subtler errors both reappear on a second benchmark, MBPP+. The paper also shows that assistants which write tests as well as code fit the same framework, because cheaper verification and harder-to-detect errors affect shipped defects only through their ratio.

We believe the paper fits the Information Systems department well. It connects the IS literature on human–AI collaboration and over-reliance with the economics of software quality and liability, two streams that *Management Science* has helped to shape, and it offers organizations a concrete way to evaluate AI coding tools by what they deliver after verification rather than by benchmark accuracy.

The manuscript is not under review elsewhere, and it has not been published in any form. [[If you choose to disclose it: An earlier version was submitted to *Information Systems Research* and was declined without review. We have substantially revised the theory, the positioning, and the empirical analysis in response to the editor's comments.]] All data and code needed to reproduce the analyses, including the sampled solutions, the execution results, and the scripts, will be made available in accordance with the journal's data and code disclosure policy. [[Disclosure of AI assistance, as required by the journal's policy on generative AI tools.]] We have no conflicts of interest to declare. [[Optional: suggested or excluded reviewers.]]

Thank you for considering our submission. We look forward to hearing from you.

Sincerely,

[[Corresponding author name]]
[[Affiliation]]
[[Email]]
