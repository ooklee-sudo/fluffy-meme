# Manuscript edits for resubmission

Ready-to-paste text and an edit list, written against the ISR proof (ISRE-2026-4635).
Square brackets mark numbers you do not have yet. Every reference marked **[verify]**
is one I believe exists but you must check before citing.

---

## 1. Title

> **When Do Better AI Coding Tools Ship Fewer Defects? Detectability, Verification, and Liability**

The current title asks whether better generation "crowds out" verification. That is a
behavioural claim the paper cannot yet support, and it invites the "this is just risk
compensation" reading. The new title asks the question the theory answers.

---

## 2. Abstract (~220 words; ends on the contribution)

> AI coding tools lower the rate at which defects enter software, but developers may respond by
> verifying less. We ask how much of a better tool's quality reaches users as fewer shipped defects.
> In a model in which defects arrive as a Poisson process and verification detects each defect at its
> own rate, the share of a quality gain retained as fewer residual defects is governed by a single,
> measurable quantity: heterogeneity in how detectable defects are. With linear verification cost the
> elasticity of residual defects with respect to defect intensity equals CV²/(1+CV²), where CV is the
> coefficient of variation of detection rates among defects that survive verification. At high effort it
> converges to 1/(1+k), where k indexes the density of the hardest-to-find defects. Complete offsetting,
> the risk-compensation benchmark, arises only when all defects are equally easy to find. Because AI
> tools change which errors they make and not only how many, a better tool reduces shipped defects only
> if its errors do not become harder to detect faster than a threshold set by the same heterogeneity.
> Under heavy-tailed detection, willingness to pay for tool quality also scales with the developer's
> share of the loss, so developer liability and tool quality are complements. In 8,659 defects from
> 25,120 solutions written by eight language models we estimate k ≈ 0.63 (95% interval 0.52–0.78),
> so about 38% of a proportional quality gain would be absorbed by reduced verification
> [; across models, more capable tools make defects that are η̂ = … harder to detect]. The analysis
> yields a verification-adjusted measure of AI tool quality that can be estimated from test-execution
> data.

If you run the experiment, replace "would be absorbed" with the estimate and add one sentence:
*"In a preregistered experiment with [N] developers, randomly assigned tool quality reduced
verification effort and residual defects with an estimated elasticity of [ε̂], close to the calibrated
prediction."*

**Keywords:** AI coding assistants; software verification; human–AI collaboration; over-reliance;
software liability; defect detectability; economics of information systems.
(Dropped: *warranties*, *Poisson thinning*.)

---

## 3. Introduction (replaces Section 1)

> **1. Introduction**
>
> Developers now write a large and growing share of their code with generative AI tools, and field
> experiments report sizable gains in output (Peng et al. 2023, Cui et al. 2025). Code that a developer
> did not write line by line still has to be checked, however, and checking is increasingly where the
> time goes. Verification has been described as the binding constraint on what AI can deliver in
> knowledge work (Catalini et al. 2026). For managers and policymakers this raises a question that
> benchmark scores do not answer: when a coding tool improves so that fewer defects enter the code,
> how much of the improvement reaches users as fewer shipped defects, and how much is spent as less
> verification?
>
> Two familiar answers bracket the possibilities. The risk-compensation and moral-hazard view
> (Peltzman 1975, Holmström 1979) predicts that users of a safer technology take more risk, and in its
> starkest form that they offset the gain completely. Research on automation complacency and
> over-reliance on AI (Parasuraman and Manzey 2010; Fügener et al. 2021; Dell'Acqua et al. 2023
> **[verify]**) documents that people monitor reliable automation less. Both literatures predict the
> *direction* of the response. Neither tells us its *size*, and a manager deciding whether a tool that
> halves defect rates will halve production incidents needs the size. The IS literature on software
> quality has long modelled developers' quality effort as an incentive problem (Austin 2001;
> Harter et al. 2000; Krishnan et al. 2000 **[verify]**), but it predates generated code and treats the
> technology of defect detection as a black box.
>
> This paper shows that the size of the response is pinned down by the *detection technology*, not by
> behaviour alone, and that the relevant property of the technology is measurable. We model defects as
> arriving at a tool-specific Poisson rate and verification as detecting each defect at its own rate.
> The developer chooses how much to verify, given the share of the loss from shipped defects that she
> bears. Our first result is that, with linear verification cost, the elasticity of shipped defects
> with respect to the tool's defect intensity equals CV²/(1+CV²), where CV is the coefficient of
> variation of detection rates among the defects verification has not yet found (Proposition 2). The
> result needs no parametric assumption about how detectability is distributed. Complete offsetting
> occurs only in the knife-edge case in which every defect is equally easy to find. Whenever some
> defects are obvious and others subtle, the obvious ones are found first and the survivors are
> disproportionately hard. Additional verification then stops paying quickly, so the developer cuts it
> only a little when the tool improves, and most of the gain survives. The same behavioural assumption
> thus yields complete or partial compensation depending on the detection technology. At high effort
> the elasticity converges to 1/(1+k), where k measures how much mass sits on defects that are nearly
> impossible to find.
>
> The second result is what makes the problem specific to AI. Generative models do not merely make
> fewer errors as they improve; they may make *different* errors, fluent and plausible code that is
> wrong in ways that are harder to catch. We let tool quality shift the detectability of defects as
> well as their number and show that shipped defects scale locally as λ^ε θ^−(1−ε), where λ is defect
> intensity and θ detectability (Proposition 3). A better tool reduces shipped defects only if its
> errors become harder to detect more slowly than a threshold equal to CV². This yields a
> *verification-adjusted* notion of tool quality. Benchmark pass rates measure λ alone, while what
> users receive depends on λ and θ in proportions set by the heterogeneity of detectability.
>
> Third, the same quantity shapes liability. When the developer bears only part of the loss she
> under-verifies, as in any moral-hazard model. Under heavy-tailed detection, however, weak developer
> liability also lowers her willingness to pay for tool quality, which scales with her loss share raised
> to the power ε, so developer liability and tool quality are complements (Proposition 4). This channel
> is absent when detection is homogeneous, and it distinguishes our setting from analyses of software
> liability in which the vendor's quality and the user's care are substitutes (August and Tunca 2011
> **[verify]**). A monopoly vendor under-supplies quality, and the shortfall grows as developer
> liability weakens, but only to the extent that detectability is heterogeneous (Corollary 2).
>
> Finally, we show how to measure the detection technology. On 25,120 solutions written by eight
> language models for 157 HumanEval+ tasks, detectability is strongly heterogeneous: a quarter of
> defects break at least 85 percent of a task's inputs, while a tenth break fewer than half of one
> percent. We estimate k ≈ 0.63 (95% interval 0.52–0.78), which implies that about 38 percent of a
> proportional quality gain would be absorbed by reduced verification. The estimate is stable across
> defect definitions and test orders, and it is confirmed by a nonparametric estimate of the survivor CV
> [report value]. [Across models, more capable tools produce defects that are η̂ = … (95% CI …) harder to
> detect, below/above the threshold of 1/k ≈ 1.6.]
>
> The paper contributes to three IS conversations. For research on human–AI collaboration and
> over-reliance, it replaces a directional prediction with a magnitude tied to a measurable property of
> AI errors, and it identifies a channel, the composition of errors, through which better AI can
> degrade outcomes without any behavioural bias. For research on the economics of software quality
> and liability, it shows that whether liability rules affect investment in tool quality depends on the
> detection technology. For practice, it gives organizations and regulators a way to value AI coding
> tools by what they deliver after verification rather than by benchmark accuracy. Section 2 positions
> the paper, Section 3 sets out the model, Sections 4–6 develop the results, Section 7 measures the
> detection technology, Section 8 discusses implications, and Section 9 concludes.

### Contribution statement (one paragraph, for the cover letter or end of Section 2)

> Prior work predicts that people verify less when automation improves, as in risk compensation,
> moral hazard and automation complacency, but not by how much, and it treats AI quality as a scalar.
> We show that the share of a quality improvement that survives verification is determined by
> heterogeneity in the detectability of defects, CV²/(1+CV²), with no parametric assumption. Complete
> offsetting is a knife-edge case. Because AI tools change the composition of their errors, a better
> tool can increase shipped defects through a technology channel rather than a behavioural one, and we
> derive the threshold at which this happens. The same quantity determines whether developer liability
> and tool quality are complements. All of these objects can be estimated from test-execution data, and
> we estimate them for eight language models.

---

## 4. Related literature: what to add (Section 2)

Restructure Section 2 into three streams, each ending with a sentence that states the gap:

1. **Human–AI collaboration and over-reliance (IS).** Fügener et al. (2021, *MISQ*); Fügener et al.
   (2022, *ISR*); Jussupow et al. (2021, *ISR*); Dell'Acqua et al. (2023, HBS working papers on the
   "jagged frontier" and "falling asleep at the wheel"); Agarwal et al. (2023, NBER, radiology);
   Parasuraman and Manzey (2010, *Human Factors*). **[verify all]**
   *Gap: these papers measure the direction of over-reliance; none ties its magnitude to properties of
   the AI's errors.*
2. **Economics of software quality and development (IS).** Austin (2001, *ISR*), an agency model of
   quality under time pressure and the closest IS antecedent, so engage it explicitly; Harter, Krishnan and Slaughter
   (2000, *MS*); Krishnan et al. (2000, *MS*); Banker, Davis and Slaughter (1998, *MS*). Keep
   Goel–Okumoto as the source of the exponential benchmark. **[verify]**
3. **Software liability and security economics.** August and Tunca (2006, 2011, *MS*); Arora,
   Caulkins and Telang (2006, *MS*); Gordon and Loeb (2002); keep Anderson (2001), Anderson and Moore
   (2006), Shavell (1980). **[verify]**
   *Gap: liability's effect on investment in quality is studied for vendor patching and user care, not
   for a verification technology whose returns depend on the detectability of errors.*

Delete the paragraph on signalling and adverse selection (Akerlof, Spence, Grossman, Cho–Kreps,
Dulleck); see §5.

---

## 5. Cuts: Sections 6.2 and 6.3, and everything that points to them

| Location | Action |
|---|---|
| Abstract | Delete "Vendor warranties cannot signal quality if developers learn defect intensity while verifying". |
| Intro, "Our results fall into four groups" paragraph | Delete from "A vendor warranty cannot signal quality…" to "…indexes learning (Proposition 6)." (Superseded by the new intro.) |
| Section 2, last paragraph (Akerlof … Dulleck … "moral-hazard device") | Delete entirely. |
| Section 6.2 Warranties, Proposition 6 | Delete. Keep one sentence in the liability discussion: *"Shifting part of the loss to the vendor, for instance through a warranty, lowers the developer's share and so raises residual defects by the same mechanism."* |
| Section 6.3 Unobserved quality and market unraveling | Delete. |
| Section 9, "For vendors and for those who evaluate vendors' claims" | Replace with a paragraph on **verification-adjusted quality**: vendors and buyers should report detectability of failures (e.g., the share of failing tests per defect), not only pass@k. Independent, reproducible evaluation of θ is what buyers need. |
| Section 10, Limitations | Delete "the choice among several warranty levels in a continuum of types" and "apart from the stylized learning in Sections 6.2 and 6.3". |
| Online Appendix B | Delete the proof of Proposition 6 and the lemons numerical example (the "Full participation / partial / No trade" table). |
| Online Appendix C | Delete any numerical checks of Props 6 and the lemons example. Add the checks in `sim_cv_elasticity.py` (see README). |
| References | Remove Akerlof (1970), Spence (1973), Grossman (1981), Cho and Kreps (1987), Dulleck et al. (2011) unless cited elsewhere. |
| Proposition numbering | Old 1 → 1; new CV result → 2; old 2 (closed forms) → fold into 2(d) or keep as 3; old 3–4 → 4–5; old 5 → Corollary; new η result → place right after the CV result. |

### Keep 6.1? Yes, but only as a short corollary

It does use ψ in a way that is new to the paper's story. With
ψ = 1 + (1−δ)/(δ(k+1)), the liability externality reaches the vendor's quality choice only when
detection is heterogeneous: ψ → 1 as k → ∞ for any δ. In the exponential benchmark weak liability does
not distort vendor quality at all (consistent with Prop. 3(b)), while under the estimated tail the
distortion ratio rises from 1.54 (δ = 1) to 3.31 (δ = 0.2). That is the point to keep. Proposed text
(replaces all of Section 6):

> **6. Vendor Investment in Quality**
>
> **Corollary 2.** *Let a monopolist choose tool quality at fixed cost K₀/λ and sell to developers whose
> willingness to pay is proportional to that in Proposition 5(a), with a uniform scale. The ratio of the
> monopolist's defect intensity to the planner's is (2ψ)^{1/(1+ε)}, where ψ = 1 + (1−δ)/(δ(k+1)).*
>
> The factor 2 is the textbook distortion from ignoring inframarginal surplus. The new element is ψ.
> Weak developer liability depresses vendor quality only through the heterogeneity of detectability: in
> the homogeneous benchmark (k → ∞) ψ = 1 whatever the liability share, whereas with k = 0.63 the ratio
> rises from 1.54 under full developer liability to 2.07 at δ = 0.5 and 3.31 at δ = 0.2. Liability
> rules for AI-generated code therefore matter for the quality of the tools themselves, and the
> detection technology determines by how much.

Move the derivation to Appendix B. Drop "the monopolist further excludes buyers with ν < ν̄/2".

*Caveat:* WTP ∝ δ^ε and ψ as written rely on ε being constant in effort (the gamma case). Say so
explicitly. Under general G the same statements hold locally, with ε evaluated at e*.

---

## 6. Sentences to delete or replace

| Where | Current text | Replacement |
|---|---|---|
| p. 4–5, end of contribution paragraph | "We are not aware of earlier work that models the developer's verification choice and the vendor's quality choice together in this way, although our search of the literature was not exhaustive." | Delete. The new intro's contribution paragraph makes the claim directly. |
| §7.1 | "…for a total of 25,120 solutions at a total cost of $2.09." | "…for a total of 25,120 solutions." |
| Abstract, last sentence | "Field data on agentic pull requests show no detectable change … so the behavioral prediction remains untested." | Removed (new abstract above). |
| §8 | Whole section in main text | Move to an online appendix as "A field test without a first stage", or drop. If kept, add a first stage first: fix-up commits or reverts within 30 days of merge, as a measure of shipped defects. |

---

## 7. Rebuilt Tables 1–3 (LaTeX, booktabs)

The proof shows the first letter of each header and of each multi-digit number in a separate
column ("P ass rate", "D efects", "3 ,140"). That pattern usually means a column too narrow for its
contents in the source (Word) table, or a table pasted as tab-separated text. Rebuild the tables rather
than patching them. Numbers below are transcribed from the proof; check them against your output files.

```latex
\begin{table}[t]\centering
\caption{Quality of the eight models on HumanEval+ (157 tasks, 20 samples per task). A defect is a distinct failure signature within a solution.}
\begin{tabular}{lccc}\toprule
Model & Pass rate & Mean defect clusters per sample & Samples \\ \midrule
Claude Haiku 5.5            & 0.933 & 0.078 & 3,140 \\
Qwen3 Coder 30B-A3B         & 0.891 & 0.139 & 3,140 \\
Mistral Small 3.2 24B       & 0.826 & 0.219 & 3,140 \\
GPT-4o mini                 & 0.823 & 0.219 & 3,140 \\
Qwen 2.5 7B Instruct        & 0.781 & 0.289 & 3,140 \\
Ministral 3B                & 0.712 & 0.382 & 3,140 \\
Llama 3.1 8B Instruct       & 0.543 & 0.652 & 3,140 \\
Llama 3.2 3B Instruct       & 0.419 & 0.779 & 3,140 \\ \bottomrule
\end{tabular}
\end{table}

\begin{table}[t]\centering
\caption{Sensitivity of the tail index $k$ and the implied elasticity $\varepsilon=1/(1+k)$ to the definition of a defect and the order of tests. 95\% task-bootstrap intervals (300 resamples).}
\begin{tabular}{lrcc}\toprule
Variant & Defects & $k$ (95\% CI) & $\varepsilon$ (95\% CI) \\ \midrule
Baseline (random order)                    & 8,659 & 0.63 (0.52, 0.78) & 0.61 (0.56, 0.66) \\
Whole sample counted as one defect         & 6,504 & 0.52 (0.42, 0.69) & 0.66 (0.59, 0.71) \\
Subtle defects only (fail $<$50\% of tests) & 5,488 & 0.94 (0.73, 1.29) & 0.52 (0.44, 0.58) \\
Drop samples with timeouts or load errors  & 7,286 & 0.72 (0.59, 0.90) & 0.58 (0.53, 0.63) \\
Dataset order                              & 8,659 & 0.62 (0.44, 1.68) & 0.62 (0.37, 0.70) \\
Short inputs first                         & 8,659 & 0.84 (0.60, 1.36) & 0.54 (0.42, 0.63) \\
Long inputs first                          & 8,659 & 0.23 (0.18, 0.30) & 0.82 (0.77, 0.85) \\ \bottomrule
\end{tabular}
\end{table}

\begin{table}[t]\centering
\caption{Pull-request outcomes before and after the change in the default model (21-day windows, repository fixed effects, standard errors clustered by repository; 35,636 pull requests in 1,431 repositories).}
\begin{tabular}{lcccc}\toprule
Outcome & Pre-period mean & Post $-$ pre (SE) & Jump with trends (SE) & $p$ (jump) \\ \midrule
Any human review           & 0.264 & \phantom{$-$}0.010 (0.007) & \phantom{$-$}0.005 (0.010) & 0.62 \\
Human reviews per PR       & 0.764 & \phantom{$-$}0.077 (0.056) & \phantom{$-$}0.020 (0.073) & 0.79 \\
Changes requested          & 0.030 & $-$0.001 (0.002)          & $-$0.002 (0.004)          & 0.67 \\
Merged                     & 0.749 & \phantom{$-$}0.002 (0.008) & \phantom{$-$}0.010 (0.011) & 0.37 \\
Log lines added            & 5.136 & $-$0.117 (0.048)          & \phantom{$-$}0.083 (0.088) & 0.34 \\
Any test file changed      & 0.440 & \phantom{$-$}0.013 (0.009) & \phantom{$-$}0.005 (0.013) & 0.70 \\
Test share of added lines  & 0.202 & \phantom{$-$}0.017 (0.007) & \phantom{$-$}0.006 (0.009) & 0.48 \\ \bottomrule
\end{tabular}
\end{table}
```

New table to add to Section 7, the nonparametric check: a row for $\hat\varepsilon(u)$ at
u ∈ {0.01, 0.05, 0.25, 1} with bootstrap CIs, and the lower-tail (Hill) estimate of k.

---

## 8. Where to send it next

ISR is closed for this paper: a desk-rejected manuscript should not come back unless it is
substantially new. Which journal to choose depends on how much of the plan you complete.

| Package | Recommended outlet | Why |
|---|---|---|
| **Full**: CV and η theory, η estimated across 20–30 models, and the experiment | **Management Science (Information Systems dept.)** | Analytical IS papers with a clean behavioural test are a core MS genre. The experiment answers objection 4, and the η channel answers objection 2. Expect the same scrutiny on novelty, so lead with Props 2–3, not offsetting per se. |
| **Theory and measurement, no experiment**: CV and η, nonparametric estimate, η across models | **Journal of Management Information Systems** | Publishes economics-of-IS models with calibration and is less insistent on causal behavioural evidence. Positioning in IS (§4 above) is essential. |
| Same package, if you prefer an economics audience | **Information Economics and Policy** | Faster turnaround and a natural home for the liability results. Lower IS visibility. |
| Liability-led reframing | *International Review of Law and Economics* or *Journal of Law, Economics, and Organization* **[check fit]** | Only if you are willing to make Props 4–5 the core and the coding-tool setting the application. |
| Calibration alone | *Empirical Software Engineering* or MSR | The detectability measurement (survivor CV of LLM defects, η across models, AI vs human defects) stands as an empirical software engineering contribution and would not prevent a later econ/IS paper that cites it. |

My recommendation: the experiment costs roughly 5–8k USD (see `experiment_protocol.md`) and turns
objection 4 from a weakness into the paper's strongest evidence. Run it and target MS. Fall back to
JMIS if it fails or the timeline does not allow it.
