"""Write the point-by-point response to the reviewer as a .docx.

  python build_response.py <out.docx>
Numbers come from results/summary.json via build_revision (imported).
"""
import sys

import numpy as np
import docx
from docx.shared import Pt, RGBColor

import build_revision as B

S, SIM = B.S, B.SIM
R = S.get("refcmp", {})
TS = S.get("threshold_sensitivity", {})


def lockstats():
    lock = [x for m in R for x in R[m]["locked"]]
    n = len(lock)
    idn = {t: sum(bool(x[f"{t}_identified"]) for x in lock) for t in ("same", "repair", "dedup")}
    med = {t: float(np.median([x[f"{t}_nll_nom"] for x in lock])) for t in ("same", "repair", "dedup")}
    return n, idn, med


def main(out):
    d = docx.Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)

    def h(t, lvl=1):
        d.add_heading(t, level=lvl)

    def quote(t):
        p = d.add_paragraph()
        r = p.add_run(t)
        r.italic = True
        r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        p.paragraph_format.left_indent = Pt(14)

    def para(t, bold_lead=None):
        p = d.add_paragraph()
        if bold_lead:
            p.add_run(bold_lead + " ").bold = True
        p.add_run(t)
        return p

    def bullet(t):
        d.add_paragraph(t, style="List Bullet")

    FP, FC, FD = B.FP, B.FC, B.FD
    AP = B.AP
    n_lock, idn, med = lockstats() if R else (0, {}, {})
    AUCS = {t: float(np.mean([R[m]['auc_nll'][t] for m in R])) for t in ('same', 'repair', 'dedup')} if R else {}
    t099 = sum(TS[m]["ni_099"] for m in TS)
    t0999 = sum(TS[m]["ni_0999"] for m in TS)
    t09999 = sum(TS[m]["ni_09999"] for m in TS)
    tint = sum(TS[m]["ni_interval"] for m in TS)
    nm = sum(TS[m]["n"] for m in TS)
    r6, r36, r240 = B.S2[(1.0, 6)], B.S2[(1.0, 36)], B.S2[(1.0, 240)]
    G = S["grid"]
    gm = [m for m in B.MODELS if m in G]
    cm = {src: {r: [0, 0] for r in ("weak", "sticky", "strong")} for src in ("main", "alt")}
    for m in gm:
        for src in cm:
            for r, (a, b) in G[m]["_interior_counts"][src].items():
                cm[src][r][0] += a
                cm[src][r][1] += b
    F = S.get("free", {})
    ov = np.mean([v["_runtime"]["overhead"] for v in F.values()]) if F else float("nan")
    tm = np.mean([v["_runtime"]["t_main"] for v in F.values()]) if F else float("nan")
    ns = np.mean([v["_runtime"]["nli_seconds"] / 20 for v in F.values()]) if F else float("nan")

    d.add_heading("Response to the Reviewer", 0)
    para("Manuscript: \"Is the Sampling Temperature the Agent's Decision State? A Reference-Based Indicator and Its "
         "Comparison with Entropy, Calibration and Semantic Entropy\"")
    para("We thank the reviewer for a careful and constructive report. Every point below was addressed either by a "
         "change in the theory, by new experiments, or, where we could not do what was asked, by narrowing our claims "
         "and saying so. New and changed text in the revised manuscript is marked in blue. All new experiments are "
         "run with the code in the repository folder teff/ (Appendix F), and every number quoted below is produced "
         "by it.")
    h("Summary of what changed", 1)
    bullet("Theory (Section 3.3): T_eff is no longer described as separating preference scaling from decision "
           "randomness. We show that only their ratio is identified (T_eff converges to T/a), characterise the "
           "estimator as a quasi-likelihood, add a distributional estimator and a fit/residual measure, and give "
           "alternative reference constructions. A stylised model gives the condition for an interior accuracy "
           "peak (Section 3.4).")
    bullet("New experiments (Sections 4.7, 5.8-5.12): four further models (Qwen2.5-0.5B, Qwen2.5-1.5B, "
           "Llama-3.2-1B, SmolLM2-1.7B) on one stack and precision, three wordings of each distortion including a "
           "dominant-response contamination, reference-based log-likelihood and divergence baselines, "
           "full-vocabulary free generation, entailment-clustered semantic entropy, run-time measurements, "
           "interval and threshold sensitivity, and attractor strengths without post-hoc selection.")
    bullet("The conclusions became more cautious. The new evidence does not rescue T_eff as a detector, and the "
           "revised abstract, discussion and conclusions say so.")
    bullet("What we could not do: re-run the 3B and 7B models of the main text, add models above 2B parameters, and "
           "supply the Stage A and B scripts (see Points 7).")

    h("Point 1: Identification of the effective temperature and the choice of reference", 1)
    quote("Eq. (2) estimates the effective temperature using clean-context logits, but changes in logit scale can also "
          "change the estimated temperature without changing the actual sampling setting. Please explain how the "
          "method distinguishes context-induced preference scaling from genuine changes in decision randomness. "
          "[...] The clean reference is calculated using the same generated history, which may already contain "
          "repeated wrong tokens. Table 9 shows that this reference becomes saturated during fully locked "
          "trajectories. Please examine alternative reference construction strategies and explain how the proposed "
          "method can deal with this failure.")
    para("The reviewer is right, and we have changed the claim and not only its justification. If the context "
         "rescales the sampling logits, z = a v, the choice distribution is p(y | v, T/a), so choice data identify "
         "only the ratio of the two; T_eff converges to T/a. The method therefore cannot separate a context-induced "
         "change of scale from a change of randomness, and we no longer say it does. In our protocol the sampler is "
         "not a free unknown (the operator sets T, the logits are observable, and the draws are exactly those of "
         "Eq. 1), so a gap between T_eff and T is attributable to the effect of the context on the logits. "
         "T_eff/T = 1/a is the temperature-equivalent of that effect. When the context also reorders the "
         "candidates, Eq. (2) is a quasi-likelihood whose maximiser is the KL-projection of the sampling "
         "distribution onto the one-parameter family generated by the reference, and the minimised divergence is "
         "what no rescaling can reproduce (Section 3.3).", "Reply, theory.")
    para(f"In a simulation T_eff recovered T/a within "
         f"{max(abs(r['teff_scale_only']/r['T_over_a']-1) for r in SIM['S1_scale_confound'])*100:.0f}% for pure "
         "rescaling, and a pure reordering drove the estimate to the grid bound with a log-likelihood at the uniform "
         "value, which is why the fit is now reported with the estimate (Appendix E, S1). In the real pressured cells "
         f"the best rescaling removed on average only {B.SCALE_EX*100:.0f}% of the divergence between the sampling "
         "distribution and the reference (Section 5.9), so most of the context effect is a change of ordering that "
         "T_eff cannot represent.", "Reply, evidence.")
    if R:
        para(f"We compared three references (Section 3.3, Table 14): the same-history reference of the main text, a "
             f"gold-repaired reference (history replaced by the correct prefix ending at the item last produced; it "
             f"needs the task order) and a de-duplicated reference (runs of repeated items collapsed; label-free). A "
             f"position-blind reference was tried and discarded, because in these tasks it always predicts the "
             f"attractor. On {n_lock} fully locked cells (clean prompt, T = 0.15, lock-in of at least 0.90, four "
             f"models), {idn['same']} were identified with the same-history reference, {idn['repair']} with the "
             f"repaired reference and {idn['dedup']} with the de-duplicated one. Under the repaired references the "
             f"locked agent gave the chosen item a median log-probability of about -{med['repair']:.0f} nats per "
             f"step, against {med['same']:.2f} for the same-history reference, so the lock is conspicuous. "
             f"The signal is carried by the reference log-likelihood and not by the fitted temperature, which is "
             f"meaningless at such a misfit.", "Reply, alternative references.")
    para("We state plainly that the proposed estimator itself does not deal with the failure: with the same-history "
         "reference it remains blind (Section 5.6 is unchanged), and the repaired references register capture by the "
         "history whatever the prompt says, which is a different construct from T_eff as defined. They also do not "
         f"improve the detection of distorted prompts (mean AUC of the log-likelihood {AUCS['same']:.2f}, {AUCS['repair']:.2f} "
         f"and {AUCS['dedup']:.2f} for the three references, Table 14). We say this in Sections 3.3, 5.10 and 6.1.")

    h("Point 2: Saturation threshold, confidence intervals and six choices per trajectory", 1)
    quote("Section 4.4 flags the estimator as unidentified when the mean reference probability exceeds 0.999. This "
          "threshold seems rather arbitrary. Please provide sensitivity analysis and confidence intervals of the "
          "estimated temperature. It is still unclear how reliable the estimates are with only six choices per "
          "trajectory.")
    para(f"We now report profile-likelihood intervals and trajectory bootstrap intervals, and we replaced the fixed "
         f"threshold by an interval rule (identified if the 95% interval is bounded away from the grid ends and its "
         f"upper bound is at most four times its lower bound; the 0.999 rule is kept as a secondary flag). "
         f"Sensitivity: of {nm} grid cells, {t099} were not identified at 0.99, {t0999} at 0.999 and {t09999} at "
         f"0.9999, and {tint} under the interval rule (Table 16). In simulation the interval at a mean reference "
         f"probability of 0.988 already spans a factor of about 68 while the 0.999 rule still calls the cell "
         f"identified (Table E2).", "Reply, threshold.")
    para(f"Six choices: in simulation the interval has near-nominal coverage ({r6['coverage']:.2f}) but a median "
         f"upper-to-lower ratio of {r6['median_hi_over_lo']:.1f}; with 36 choices {r36['median_hi_over_lo']:.1f} and with "
         f"240 choices {r240['median_hi_over_lo']:.1f} (Table E1). In the real trajectories the median ratio was "
         f"{B.TRAJ_RATIO:.1f} and {B.TRAJ_GT4*100:.0f}% exceeded 4, against {B.CELL_RATIO:.2f} for a pooled cell "
         "(Table 15). We conclude, and now state, that trajectory-level estimates are not usable on their own and only "
         "pooled estimates should be interpreted. The distributional estimator in Section 3.3 removes the draw "
         "noise but not this limitation, since it still rests on six histories.", "Reply, six choices.")

    h("Point 3: Comparison with reference-based measures; candidate-restricted sampling", 1)
    quote("Table 8 shows that the proposed indicator detects only 6 of 15 pressured cells, while ordinary token "
          "entropy detects 10 of 16. [...] Please compare with reference-based log-likelihood and "
          "distribution-divergence measures to show whether temperature fitting provides any additional value. The "
          "experiments restrict sampling to the first tokens of predefined candidate items. [...] Please explain how "
          "this restriction affects the temperature interpretation and include a more realistic generation task.")
    para(f"Section 5.9 and Table 13 add the reference log-likelihood, KL(sampling || reference), the distributional "
         f"estimator and the residual divergence. Pooled over four models and three pressure wordings, pressure was "
         f"flagged by the reference log-likelihood in {B.frac(FP['nll'])} cells, by entropy in {B.frac(FP['entropy'])}, "
         f"by KL in {B.frac(FP['kl'])}, by T_eff in {B.frac(FP['teff'])} and by the distributional estimator in "
         f"{B.frac(FP['teffdist'])}. The temperature fit therefore adds nothing as a detector. Its value is "
         "interpretive: it says what share of a context effect is a change of scale. A caveat is stated in the "
         "text: in a clean cell the reference equals the sampling distribution, so KL is exactly zero and its AUC of "
         "1.00 (and the high AUC of the distributional estimator) are artefacts of the matched design, not results.")
    para("Restriction and a realistic task (Section 5.12): we added full-vocabulary free generation (20 completions "
         "of up to 24 tokens, no truncation, reference over the same vocabulary) for two models and two tasks. The "
         "restriction changes the quantity estimated: for the first token the restricted and full-vocabulary "
         "estimates differ, and at T = 2.0 the full-vocabulary estimate is pinned at the nominal temperature in every "
         "condition and carries no information, because tens of thousands of tail tokens dominate the likelihood. In "
         "free generation T_eff flagged none of the distorted cells. We say that the temperature reading is tied to "
         "the support on which it is computed. The free-generation task is still a controlled list task, not an "
         "open-ended assistant task.")

    h("Point 4: Attractor strengths chosen on the same models; semantic evaluation and representation reliability", 1)
    quote("Section 4.1 selects attractor strengths after probing the same models used in the main experiments. [...] "
          "Please validate the findings using independently selected attractor strengths and examine the cases where "
          "strong attractors also show interior peaks. The discussion of semantic evaluation and representation "
          "reliability could be expanded a little. Related studies such as ROUGE-SEM [...] and MCRSpell [...] may "
          "provide useful perspectives [...].")
    para(f"Section 5.11 and Table 17: we ran the full a-priori grid of 12 run lengths for three models and three tasks, "
         f"with no selection, and selected the regimes in two ways, on the main prompt and on a different wording of "
         f"the instruction with fresh trajectories. Selected on the main prompt, sticky attractors showed an "
         f"interior peak in {cm['main']['sticky'][0]} of {cm['main']['sticky'][1]} model-task pairs, weak in "
         f"{cm['main']['weak'][0]} and strong in {cm['main']['strong'][0]}; selected on the other wording the counts "
         f"were {cm['alt']['sticky'][0]}, {cm['alt']['weak'][0]} and {cm['alt']['strong'][0]}. So the clean pattern "
         "of the main text depends on how the strengths are selected, and we now say that H2 is supported only in "
         "the weak form (interior peaks for a minority of run lengths, without a sharp boundary). The strong "
         "attractors with interior peaks are listed in Section 5.11; the peaks lie inside the grid and have low "
         "accuracy. The stylised model in Section 3.4 gives the existence condition for a peak (Delta < (K-2)g) and "
         "explains why strength is continuous and task-dependent; we checked it numerically.")
    para("We expanded the discussion of semantic equivalence and representation reliability in Section 2.2, with "
         "references [20-23]. [AUTHORS TO DECIDE: the two cited papers are only loosely related to this study and "
         "share an author; keep the sentence only if you consider them relevant.]")

    h("Point 5: One prompt template, mostly negative-sentiment contamination, and H3", 1)
    quote("The pressure and contamination experiments use only one prompt template, and the contamination text is "
          "mainly negative sentiment. H3 is not fully examined because the dominant-response-related contamination "
          "condition is missing. Please test additional prompt formulations and make the conclusions about "
          "contamination more careful.")
    para(f"Section 4.7, Appendix D and Tables 11 and 12: each distortion now has three wordings (pressure P0, P1, P2; "
         f"contamination C0, C1 and C2, a dominant-response contamination stating that the planted item was the "
         f"accepted answer) for three models, and the original wordings for a fourth. Pressure raised T_eff in a "
         f"minority of cells and the sign changed with wording in one model; contamination did not raise it. The "
         f"dominant-response text changed the choices strongly (lock-in {B.LOCK['clean']:.2f} to {B.LOCK['C2']:.2f}) but "
         f"not T_eff, and adding it to pressure did not strengthen the pressure effect, so H3 remains unsupported "
         f"in the case that was missing. The conclusions about contamination are now explicitly limited to these "
         f"wordings, to small models and to this task (Sections 5.8, 6.4 and 7).")

    h("Point 6: Semantic entropy baseline; computational overhead", 1)
    quote("The semantic entropy baseline is reduced to exact matching of complete outputs. [...] Please include a "
          "more faithful implementation on open-ended responses. [...] Please report the actual runtime and "
          "computational overhead. [...]")
    para(f"Section 5.12 and Table 18: for the free-generation cells we cluster the 20 completions of a cell with an "
         f"entailment model (DeBERTa-large MNLI, both directions, given the task instruction), as in Farquhar et al., "
         f"and compute the entropy over the clusters, with bootstrap intervals that re-cluster. Clustering reduced the "
         f"number of distinct completions drastically, so the exact-match version was a poor proxy, but the "
         f"clustered entropy was also a weak detector. We did not validate the entailment model on repetitive "
         f"list-like text, and the implementation is a discrete-entropy version on 20 samples for two models and "
         f"two tasks, not a full replication on a hallucination benchmark.")
    para(f"Cost (Table 19): the reference pass takes about {ov*100:.0f}% of the sampling pass (it doubles the "
         f"forward-pass cost), the entailment calls took about {ns:.0f} s per cell against {tm:.0f} s of sampling, "
         f"and fitting is negligible for the candidate-restricted task (about 10 ms per cell) but not for the full "
         f"vocabulary. Since the fitted temperature flagged fewer distorted cells than entropy, which is free, we say "
         f"that the extra computation is hard to justify as a detector (Section 6.1).")

    h("Point 7: Small models, mixed inference stacks, and missing scripts", 1)
    quote("The model comparison is limited mainly to small language models, and Qwen2.5-7B uses a different inference "
          "framework and quantization setting. Please add more controlled cross-model experiments and provide the "
          "missing scripts from Stages A and B. [...]")
    para("Controlled comparison: all four new models were run in 32-bit floating point with the same library on the "
         "same CPU, so they differ only in the model. They are two Qwen2.5 sizes, Llama-3.2-1B and SmolLM2-1.7B. All "
         "are below 2B parameters, because the experiments were run on a CPU-only machine; we did not re-run the 3B "
         "models or Qwen2.5-7B and we cannot make claims about models above 7B. Section 6.4 says so, and the "
         "conclusions are restricted to small models and to this task family. The abstract, discussion and "
         "conclusions now restrict the claims accordingly.")
    para("Scripts: the code for the revision study is in teff/ with the per-trajectory results. [AUTHORS TO "
         "CONFIRM: the scripts of Stages A and B could not be located in the repository or the supplied files. If "
         "they exist, add them to the Supplementary Materials. Otherwise state that they were lost. The revised "
         "manuscript reports Tables 4 and 5 only as an illustration and states that no conclusion rests on them.]")
    d.save(out)


if __name__ == "__main__":
    main(sys.argv[1])
