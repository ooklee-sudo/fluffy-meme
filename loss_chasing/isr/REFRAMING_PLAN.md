# Reframing plan for the Loss Chasing manuscript (ISR)

## 1. From the current frame to the new frame

**Current frame.** "Do loss frames make LLM operators skip verification?" The question comes from behavioral economics. The registered hypothesis was not supported, so the paper reads as a null result plus follow-up studies.

**New frame.** "What governs verification skipping in LLM operators?" The paper becomes a study of how the delegation interface (what the operator sees, how much it can reason, how much time it has) shapes risk choices of an automated maintenance operator. Loss framing is one candidate factor among several, tested first and found not to drive the behavior.

**Working title.** When Do LLM Operators Skip Verification? Goal Visibility, Reasoning, and Framing in an Automated Maintenance Environment

## 2. Core argument (three sentences)
1. Firms delegate maintenance decisions to LLM operators through text prompts; the prompt is the delegation contract, and its content is a managerial design choice.
2. In a controlled maintenance environment, whether the operator sees the target, whether it reasons before acting, and how many turns remain account for most of the variation in skipping, while the loss or gain wording of the headline matters little and in the opposite direction to loss chasing.
3. The pattern is specific to small, fast models; larger models with default reasoning show no skipping, which makes the delegation interface and model tier first-order governance variables.

## 3. Contributions to IS (what the paper adds)
1. **From "does AI copy human biases" to "which interface features control AI risk behavior".** The question matches IS work on delegation, interface design, and human-AI task allocation. The levers are managerial: goal specification, reasoning budget, information display.
2. **A registered, transparent test of a prominent behavioral claim.** Loss chasing is tested as pre-specified and not found; the paper then identifies what does move the behavior. A pre-registered null with a mechanism is a contribution in itself.
3. **A design for LLM-as-subject research in IS.** Wording is the unit of replication (16 independent wordings per frame), with variance shares for frame, wording, and interaction, a noise floor, and multiplicity checks. The design addresses a known weakness of single-prompt experiments.
4. **Boundary evidence across tiers.** Floor effects in three larger models are reported as a finding about when the question is informative.

## 4. Conceptual model and propositions
Verification skipping = f(goal visibility, reasoning, time pressure, framing, information on expected values), conditional on model tier.

| Proposition | Statement | Evidence in the paper |
|---|---|---|
| P1 Goal visibility | Skipping is higher when the target is not visible in the decision context | Study 4 (goal and valence manipulation) |
| P2 Reasoning | Reasoning before acting lowers skipping and shrinks differences between conditions | Study 3 (extended thinking) |
| P3 Time pressure | Skipping appears when few turns remain | Study 2 (12, 6, 3 turns left) |
| P4 Framing | Loss wording does not raise skipping; its effect is small and runs the other way | Study 1 (registered), Study 2, Study 4, affect-verb check |
| P5 Information | Showing expected values lowers skipping but does not remove it | Study 5 |
| P6 Tier | Larger models with default reasoning do not skip in this environment | Study 2 (Sonnet 5.5, Opus 5.5, Fable 5.1) |

The registered hypothesis (loss chasing) stays as the first test and is reported first. Later studies are described as designed after Study 1, with the order of design stated in the appendix. They are presented as tests of P1 to P6 with their intervals, not as exploratory add-ons.

## 5. Narrative arc and section map
1. **Introduction.** Delegation of maintenance to LLM operators; the prompt as contract; the question of what governs skipping; summary of findings and contributions.
2. **Theory and propositions.** Delegation and goal specification (principal-agent view); interface design; prospect theory and loss chasing as the registered competing account; reasoning and time pressure as conditions; propositions P1 to P6.
3. **Environment and method.** Maintenance state machine, hidden payoffs, first-choice outcome, wording as unit of replication, variance decomposition, multiplicity checks.
4. **Study 1 (registered).** Loss chasing test; result and why the test is uninformative for some models (floor).
5. **Study 2 (time pressure, wordings, tiers).** Where skipping appears; the frame ordering; tiers at floor.
6. **Study 3 (reasoning).** Thinking removes most skipping.
7. **Study 4 (goal visibility and valence).** The target matters, the valence does not.
8. **Study 5 (expected values).** Information lowers skipping without removing it.
9. **Discussion.** Interpretation; what is supported and what is not claimed; managerial implications (below); limitations.
10. **Conclusion.**

Length. Move the detailed Study 1 tables (open models, failure-history effects) to the online appendix, merge Studies 3 and 5 into short sections, and cut the repeated per-wording results. Target about 28 pages for the main text.

## 6. Managerial implications (derived from the evidence)
1. State the objective in the operator's decision context; hiding it raised skipping under time pressure.
2. Give reasoning budget to decisions that involve verification; thinking removed most skipping in the small model.
3. Do not rely on tone or framing of instructions to control risk behavior; the loss or gain headline did not drive skipping.
4. Showing expected values helps but is not sufficient; keep a verification check outside the operator.
5. Test the specific model and tier in use; larger tiers showed no skipping here, small fast tiers did.

## 7. What the paper claims and does not claim
| Claim | Status |
|---|---|
| Loss chasing as registered | Not supported; uninformative where behavior is at floor |
| Goal visibility and reasoning lower skipping in the small model | Supported in the tested environment and model |
| Loss frame increases skipping | Not supported; the loss frame skipped less than the gain frame in the small model |
| Effects generalize across model families | Not claimed; one small model skips |
| Findings transfer to human operators or to production maintenance | Not claimed |

## 8. Risks and responses
| Likely reviewer point | Response in the revision |
|---|---|
| One model drives the result | Add 2 to 3 small models from other vendors with the 16-wording design (largest single improvement) |
| Studies 2 to 5 not registered | Order of design disclosed; analysis scripts fixed before runs; intervals and multiplicity checks reported |
| Abstract environment | State the scope; frame the environment as an instrument, not a replica of operations |
| IS theory contribution | Section 2 and the contribution list above |
| Length | Section 5 cuts |

## 9. Next steps
1. Rewrite title, abstract, introduction, and a new theory section on this frame (about 3 pages), and re-cut the discussion.
2. Rewrite the cover-letter contribution statement (under 500 words, no square brackets).
3. Optionally, add small models from other vendors with the same 16-wording design.
4. Keep the claims table in Section 7 as a check on every sentence of the revision.
