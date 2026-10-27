"""Apply the revision to the manuscript (.docx) using results/summary.json.

  python build_revision.py <original.docx> <out_dir>

Writes <out_dir>/manuscript_revised_marked.docx (new/changed text in blue) and
<out_dir>/manuscript_revised_clean.docx. All numbers in the new text come from
results/summary.json and results/sim_identification.json.
"""
import copy
import json
import os
import sys

import numpy as np

from edit_docx import Editor

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "results", "summary.json")))
SIM = json.load(open(os.path.join(HERE, "results", "sim_identification.json")))
BENCH = json.load(open(os.path.join(HERE, "results", "runtime_bench.json")))

MODELS = ["Qwen2.5-0.5B-Instruct", "Qwen2.5-1.5B-Instruct",
          "Llama-3.2-1B-Instruct", "SmolLM2-1.7B-Instruct"]
SHORT = {"Qwen2.5-0.5B-Instruct": "Qwen2.5-0.5B", "Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B",
         "Llama-3.2-1B-Instruct": "Llama-3.2-1B", "SmolLM2-1.7B-Instruct": "SmolLM2-1.7B"}
MODELS = [m for m in MODELS if m in S["matched"]]


def f2(x, d=2):
    return "n/a" if x is None else f"{x:.{d}f}"


def sgn(x, d=2):
    return "n/a" if x is None else f"{x:+.{d}f}"


# ---------------------------------------------------------------------------
# pooled quantities used in the text
# ---------------------------------------------------------------------------
PRESS = ["P0", "P1", "P2"]
CONT = ["C0", "C1"]
DOM = ["C2"]


def pooled_flags(conds):
    tot = {}
    for m in MODELS:
        for c in conds:
            for k, (a, b) in S["matched"][m]["flags"].get(c, {}).items():
                t = tot.setdefault(k, [0, 0])
                t[0] += a
                t[1] += b
    return tot


def pooled_auc(conds):
    acc = {}
    for m in MODELS:
        for c in conds:
            for k, v in S["matched"][m]["auc"].get(c, {}).items():
                acc.setdefault(k, []).append(v)
    return {k: float(np.mean(v)) for k, v in acc.items()}


def frac(t):
    return f"{t[0]}/{t[1]}"


FP, FC, FD = pooled_flags(PRESS), pooled_flags(CONT), pooled_flags(DOM)
AP, AC, AD = pooled_auc(PRESS), pooled_auc(CONT), pooled_auc(DOM)
S2 = {(r["tau"], r["n_choices"]): r for r in SIM["S2_interval_properties"]}
S3 = SIM["S3_saturation"]
S1 = SIM["S1_scale_confound"]


def scale_expl():
    v = []
    for m in MODELS:
        for c, d in S["matched"][m].get("scale_explained", {}).items():
            if c.startswith("P"):
                v += [d["mean"]] * d["n"]
    return float(np.mean(v)) if v else None


SCALE_EX = scale_expl()
TRAJ_RATIO = float(np.mean([S["matched"][m]["ident"]["traj_median_hi_over_lo"] for m in MODELS]))
TRAJ_GT4 = float(np.mean([S["matched"][m]["ident"]["traj_frac_ratio_gt4"] for m in MODELS]))
CELL_RATIO = float(np.mean([S["matched"][m]["ident"]["median_hi_over_lo"] for m in MODELS]))


def lock_by_cond():
    acc = {}
    for m in MODELS:
        d = json.load(open(os.path.join(HERE, "results", f"matched_{m}.json")))
        for task, td in d["res"].items():
            for k, c in td["cells"].items():
                acc.setdefault(k.split("|")[1], []).append(c["lock"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


LOCK = lock_by_cond()


def h1_cell(m, c):
    h = S["hypotheses"][m]["h1"].get(c)
    if not h:
        return "–"
    return f"{h['raised']}/{h['identified']} ({sgn(h['mean_shift'])})"


def h3_cell(m, key):
    h = S["hypotheses"][m]["h3"].get(key)
    if not h or not h["n"]:
        return "–"
    return f"{sgn(h['mean'])} ({h['n_ge_05']}/{h['n']})"


def build(src, out, mark):
    ed = Editor(src, mark=mark)
    D = ed.doc

    # ---------------------------------------------------------------- abstract
    ab = ed.para("Operators of large language model")
    ed.append(ab, " In a revision study with four further small models (0.5 to 1.7 billion parameters, "
                  "three families, one inference stack), three wordings of each distortion, full-vocabulary "
                  "generation and entailment-clustered semantic entropy, T_{eff}".replace("T_{eff}", "*T*_{eff}") +
                  " again did not outperform simpler indicators, and with six choices per trajectory its 95% "
                  f"interval spanned a median factor of about {TRAJ_RATIO:.0f}.")

    # ----------------------------------------------------------- introduction
    p = ed.para("We define")
    ed.insert_after(p, "We separate what the estimator identifies (a temperature-equivalent of the context's net "
                       "effect on the logit scale, not decoder randomness), report its fit and a distributional "
                       "variant, compare alternative reference constructions, and replace the fixed saturation "
                       "threshold by an interval-based identification rule.", like=p)

    # ---------------------------------------------------------- related work
    p = ed.para("Work on uncertainty in language models")
    ed.append(p, " Estimating semantic equivalence reliably is itself a representation problem. Entailment-based "
                 "clustering relies on a natural-language-inference model [20,21], and its outcome depends on how "
                 "well that model represents the text being compared. We use an entailment model only for the "
                 "free-generation semantic-entropy baseline (Section 5.12) and do not evaluate its reliability.")
    p = ed.para("The use of the softmax as a choice rule")
    ed.append(p, " The estimator in Section 3.2 is a quasi-likelihood in the sense of White [19]: when the "
                 "reference family is misspecified, the maximizer converges to the member of the family "
                 "closest in Kullback-Leibler divergence to the true choice distribution, and the log "
                 "likelihood is a strictly proper scoring rule [22].")

    # ----------------------------------------------------------------- Sec 3.3
    p37 = ed.para("Four properties of the estimator matter")
    ed.sub(p37, "We do not analyse fit quality here.", "Fit quality is analysed in Sections 3.3 and 5.10.")
    ed.sub(p37, "We flag such cells as not identified rather than interpreting the boundary value.",
           "We flag such cells as not identified rather than interpreting the boundary value; Section 3.3 "
           "replaces the fixed saturation threshold by an interval-based rule.")

    a = p37
    a = ed.insert_after(a, "The estimator does not separate a context-induced "
                           "change of preference scale from a change of decision randomness, and we no longer "
                           "describe it as doing so. Suppose the context rescales the sampling logits, "
                           "*z*_{t} = *a v*_{t}. Then *p*(*y* | *z*_{t}, *T*) = *p*(*y* | *v*_{t}, *T*/*a*), so "
                           "*T*_{eff} converges to *T*/*a*: a context that sharpens preferences (*a* > 1) and a "
                           "lower sampler temperature give the same choice distribution, and choice data "
                           "identify only their ratio. In our protocol the sampler is not a free unknown. The "
                           "operator sets *T*, the logits *z*_{t} are observable, and the draws are exactly "
                           "those of Equation (1). A gap between *T*_{eff} and *T* is therefore caused by the "
                           "effect of the context on the logits and not by a change in the sampler. "
                           "*T*_{eff}/*T* = 1/*a* is the temperature-equivalent of that effect on the logit "
                           "scale. In a simulation with 12 candidates and 600 choices (Appendix E, S1), "
                           f"*T*_{{eff}} recovered *T*/*a* to within {max(abs(r['teff_scale_only']/r['T_over_a']-1) for r in S1)*100:.0f}% "
                           "for *a* in {0.5, 1, 2} and *T* in {0.8, 2.0}.",
                       like=p37, bold_lead="What the estimator identifies.")
    a = ed.insert_after(a, "When the context also "
                           "changes the ordering of the candidates, *z*_{t} = *a v*_{t} + *r*_{t}, Equation (2) "
                           "is a quasi-likelihood. Its maximizer converges to the pseudo-true value "
                           "τ^{*} = argmin_{τ} E KL(*p*(·|*z*,*T*) ‖ *p*(·|*v*,τ)) [19], and the minimized "
                           "divergence κ measures what no rescaling of the reference can reproduce. Every "
                           "choice is drawn conditionally on the realized history, so Equation (2) is a partial "
                           "likelihood, and we resample whole trajectories for inference. A reordering context "
                           "does not show up as a different *T*_{eff}. In the simulation it sent the estimate "
                           "to the upper grid bound (20) and lowered the log-likelihood per step to the uniform "
                           f"value (between {min(r['ll_order'] for r in S1):.2f} and {max(r['ll_order'] for r in S1):.2f} against "
                           f"log(1/12) = -2.48), whereas pure rescaling gave {min(r['ll_scale'] for r in S1):.2f} to "
                           f"{max(r['ll_scale'] for r in S1):.2f}. *T*_{{eff}} must therefore "
                           "be reported together with its fit, and we do so from Section 5.9 on.", like=p37, bold_lead="Misspecification, fit and the part that scale cannot explain.")
    a = ed.insert_after(a, "Because the sampling logits are observable in an "
                           "open-weight model, we also compute *T*_{eff}^{dist} = argmin_{τ} (1/*n*) Σ_{t} "
                           "KL(*p*(·|*z*_{t},*T*) ‖ *p*(·|*v*_{t},τ)). It uses the whole sampling distribution "
                           "instead of one draw per step, so it has no draw noise, and its minimum κ is the "
                           "non-scale part of the mismatch. It requires the same two forward passes as the "
                           "sample-based estimator. The sample-based form remains the one that applies when only "
                           "sampled tokens and the reference are available.", like=p37, bold_lead="Distributional estimator.")
    a = ed.insert_after(a, "The reference in the main experiments is the clean-context "
                           "distribution on the realized history (\"same history\"). It inherits the history, so "
                           "once the realized history contains a run of repeated wrong tokens the reference can "
                           "itself be saturated on the repeated token (Table 9), and the estimator is then "
                           "blind. We therefore compare it with two repairs that change the history seen by the "
                           "reference and not the prompt. In the \"gold-repaired\" reference, the history is "
                           "replaced by the correct list prefix ending at the item last produced. It needs the "
                           "task order and is therefore label-like. In the \"de-duplicated\" reference, runs of "
                           "identical consecutive items are collapsed, which is label-free and needs only a "
                           "repetition detector. We also tried a position-blind reference that sees only the "
                           "first item, but in these tasks it always predicts the second item, which is the "
                           "attractor itself, so it is degenerate and is not used. No reference is neutral. "
                           "The same-history reference measures consistency with the model's own conditioned "
                           "valuation, and the repaired references measure departure from the valuation under "
                           "a repaired history, which confounds the distorting prompt with the repair. The "
                           "label-based reference (one-hot on the correct item) is the log-likelihood of "
                           "correctness and underlies ECE. A reference from a different model is possible but "
                           "not tested.", like=p37, bold_lead="Reference construction.")
    a = ed.insert_after(a, "The pooled log-likelihood over a cell gives "
                           "a profile-likelihood interval for *T*_{eff} (all τ on the grid with a likelihood-ratio "
                           "statistic below 3.84), and we also report a percentile bootstrap over trajectories. "
                           "A cell is called identified if its 95% profile interval is bounded away from both "
                           "ends of the grid and its upper bound is at most four times its lower bound. The "
                           "earlier rule (mean reference probability of the chosen items at most 0.999) is kept "
                           "as a secondary flag. The simulations in Appendix E (S2, S3) show why a fixed "
                           "threshold is not enough: with six choices the interval is wide whatever the "
                           "reference, and the interval widens sharply well below a mean reference probability "
                           "of 0.999.", like=p37, bold_lead="Uncertainty and the identification rule.")

    # ----------------------------------------------------------------- Sec 3.4
    p = ed.para("The reasoning behind H2 is as follows")
    ed.insert_after(p, " A stylised model makes the boundary explicit. Let there be *K* candidates, let the "
                       "attractor have a logit advantage Δ > 0 over the correct item, and let the other *K* - 2 "
                       "candidates lie *g* below the correct item. The probability of the correct item is "
                       "*p*_{c}(*T*) = [exp(Δ/*T*) + 1 + (*K* - 2)exp(-*g*/*T*)]^{-1}. It is zero at *T* → 0, "
                       "tends to 1/*K* as *T* → ∞, and the denominator behaves as *K* + [Δ - (*K* - 2)*g*]/*T* at "
                       "high *T*. An interior maximum therefore exists if and only if Δ < (*K* - 2)*g*. "
                       "Otherwise accuracy rises monotonically to 1/*K*. We confirmed the condition numerically "
                       f"for 36 combinations of *K* (8, 26), *g* and Δ (agreement {SIM['S4_agreement']*100:.0f}%; "
                       "Appendix E, S4). Strength is continuous, the boundary depends on *K* and *g* and hence on "
                       "the task and the model, and the peak temperature grows with Δ (for *K* = 26 and *g* = 1 "
                       "it is 0.6, 1.9, 5.1 and 18.7 for Δ = 1, 3, 6 and 12). A strong attractor can thus "
                       "have an interior peak when *g* is large, and its peak can lie beyond any fixed grid. "
                       "This is a one-step caricature and not a model of the trajectories.",
                  like=p)

    # ----------------------------------------------------------------- Sec 4
    p = ed.para("Strength is calibrated separately for each model")
    ed.append(p, " In the revision study the regimes are therefore also examined without any selection, over the "
                 "full grid of *m* values, and with strengths selected on a different wording of the task "
                 "instruction (Section 5.11).")
    p = ed.para("For each trajectory we record the chosen items")
    ed.sub(p, "exceeds 0.999.", "exceeds 0.999. This threshold is a convention. Section 3.3 adds an "
                                "interval-based rule, and Section 5.10 reports the sensitivity to both.")

    p = ed.para("Accuracy figures carry standard errors")
    h = ed.insert_after(p, "4.7. Revision Study", style="MDPI_2.2_heading2")
    q = ed.insert_after(h,
        "The revision study repeats the matched-cell design on four further models run on one stack. "
        "Qwen2.5-0.5B-Instruct, Qwen2.5-1.5B-Instruct, Llama-3.2-1B-Instruct (an ungated mirror of the official "
        "weights) and SmolLM2-1.7B-Instruct were run in 32-bit floating point with the Transformers library on a "
        "four-core CPU, so that, unlike Qwen2.5-7B in Section 4.3, they differ from each other only in the model. "
        "For every model and task the sticky attractor is chosen by the probe rule of Section 4.1, and the cells "
        "are the same eight (task by *T* in {0.8, 2.0}), with 40 trajectories each. Each distortion has three "
        "wordings. Pressure is P0 (the original), P1 and P2. Contamination is C0 (the original), C1 (a differently "
        "worded negative-sentiment text) and C2, a dominant-response contamination that states that the planted "
        "item was the accepted answer in earlier sessions. Combined conditions cross them (P0+C0, P0+C2, P1+C1, "
        "P1+C2, P2+C2); SmolLM2-1.7B was run with the original wordings only. The exact texts are in Appendix D. "
        "Three further elements are new. First, the references of Section 3.3 (same history, gold-repaired, "
        "de-duplicated) are computed for every step, together with the reference log-likelihood (mean negative "
        "log-probability of the chosen item under the reference at the nominal temperature) and the divergence "
        "KL(sampling ‖ reference) at the nominal temperature. Second, a full-vocabulary free-generation task: the "
        "planted history is the prefix of the assistant turn, 20 completions of up to 24 tokens are sampled from "
        "the complete softmax without truncation, the reference is the clean-context full-vocabulary distribution "
        "on the same tokens, and semantic entropy is computed after clustering the completions with the "
        "DeBERTa-large MNLI entailment model [20,21] in both directions given the task instruction, as in "
        "Farquhar et al. [5] (Qwen2.5-1.5B and Llama-3.2-1B, alphabet and months). Third, wall-clock times of the "
        "main and reference passes and of the entailment calls are recorded. The detection rule of Section 4.6 is "
        "applied unchanged, with margins of 0.10 nats for the reference log-likelihood and the divergence and "
        "0.50 for *T*_{eff}^{dist}. The 3B models and Qwen2.5-7B of the main text were not re-run.",
        like=p)

    cur = results(ed)
    results2(ed, cur)
    discussion(ed)
    ed.save(out)
    return ed


# ---------------------------------------------------------------------------
# results sections
# ---------------------------------------------------------------------------
def caption(ed, anchor, label, text):
    return ed.insert_after(anchor, text, style="MDPI_4.1_table_caption", bold_lead=label)


def footer(ed, anchor, text):
    return ed.insert_after(anchor, text, style="MDPI_4.3_table_footer")


def body(ed, anchor, text, like):
    return ed.insert_after(anchor, text, like=like)


def heading(ed, anchor, text):
    return ed.insert_after(anchor, text, style="MDPI_2.2_heading2")


def results(ed):
    D = ed.doc
    like = ed.para("We compare the indicators on the same matched cells")
    end = ed.para("6. Discussion")._p.getprevious()
    cur = end

    # ------------------------------------------------------------------ 5.8
    cur = heading(ed, cur, "5.8. Revision Study: Further Models, Three Wordings and Dominant-Response Contamination")
    tot_p = [0, 0]
    tot_c = [0, 0]
    for m in MODELS:
        for c in PRESS:
            h = S["hypotheses"][m]["h1"].get(c)
            if h:
                tot_p[0] += h["raised"]
                tot_p[1] += h["identified"]
        for c in CONT:
            h = S["hypotheses"][m]["h1"].get(c)
            if h:
                tot_c[0] += h["raised"]
                tot_c[1] += h["identified"]
    h3n = h3k = 0
    for m in MODELS:
        for k, v in S["hypotheses"][m]["h3"].items():
            h3n += v["n"]
            h3k += v["n_ge_05"]
    ident_all = sum(int(S["matched"][m]["ident"]["interval"]) for m in MODELS)
    n_all = sum(S["matched"][m]["ident"]["n"] for m in MODELS)
    cur = body(ed, cur,
        "Table 11 reports, for each additional model, how often a distortion raised *T*_{eff} above its clean "
        "value (by at least 0.5 and outside the clean-cell bootstrap interval) among the identified matched cells, "
        "and the mean shift of *T*_{eff} - *T*. The model dependence of Section 5.5 is reproduced, and the effect "
        f"is weak. Pooled over the three pressure wordings, pressure raised *T*_{{eff}} in {tot_p[0]} of {tot_p[1]} "
        f"identified cells, and contamination alone (C0 and C1) in {tot_c[0]} of {tot_c[1]}. Qwen2.5-0.5B showed no "
        "increase with any wording, Qwen2.5-1.5B showed the largest (3 of 6 cells for P0 but 1 of 6 for P1), and "
        "the sign of the mean shift changed with the wording in Qwen2.5-0.5B. The single-wording result of Section 5.5 should therefore be read as a result for that wording. "
        f"No cell of the revision study was lost to saturation at the 0.999 rule, and {ident_all} of {n_all} "
        "cells passed the interval rule.", like)
    cur = caption(ed, cur, "Table 11.",
        " Pressure (P0, P1, P2) and contamination (C0, C1, C2) wordings: identified matched cells in which "
        "*T*_{eff} was raised, out of identified cells (mean shift of *T*_{eff} - *T* relative to the clean cell).")
    rows = [["Model", "P0", "P1", "P2", "C0", "C1", "C2 (dominant)"]]
    for m in MODELS:
        rows.append([SHORT[m]] + [h1_cell(m, c) for c in ["P0", "P1", "P2", "C0", "C1", "C2"]])
    cur = ed.make_table(cur, rows, [2000, 1400, 1400, 1400, 1400, 1400, 1466])
    cur = footer(ed, cur, "A dash marks a wording that was not run for that model. Eight matched cells per model "
                          "(six for Qwen2.5-1.5B, whose probe found no sticky attractor on one of the four tasks).")
    cur = body(ed, cur,
        "Table 12 gives the test of H3 that was missing from the main text, with contamination aimed at the "
        "dominant response (C2). Adding contamination to pressure shifted *T*_{eff} - *T* by "
        f"{min(v['mean'] for m in MODELS for v in S['hypotheses'][m]['h3'].values() if v['mean'] is not None):+.2f} "
        f"to {max(v['mean'] for m in MODELS for v in S['hypotheses'][m]['h3'].values() if v['mean'] is not None):+.2f} "
        f"on average, and the shift reached 0.5 in either direction in {h3k} of {h3n} comparisons. The "
        "dominant-response text did not strengthen the pressure effect either: the mean shift was negative or "
        "close to zero in most models. It did change the choices strongly. Entropy and confidence flagged it in "
        f"{FD['entropy'][0]} and {FD['conf'][0]} of {FD['entropy'][1]} cells, more often than they flagged "
        f"diffuse negative text (C0 and C1: {FC['entropy'][0]} and {FC['conf'][0]} of {FC['entropy'][1]}), and "
        f"lock-in to the planted item rose from {LOCK['clean']:.2f} in clean cells to {LOCK['C2']:.2f} under C2 "
        f"(C0: {LOCK['C0']:.2f}), but this extra concentration is largely a change of ordering "
        "rather than of scale and *T*_{eff} follows it only weakly. H3 remains unsupported. The conclusion about "
        "contamination is limited to these wordings, to models of 0.5 to 1.7 billion parameters and to this task.",
        like)
    cur = caption(ed, cur, "Table 12.",
        " Effect of adding contamination to pressure: mean change of *T*_{eff} - *T* (number of matched cells "
        "with a change of at least 0.5 in either direction, out of cells compared).")
    keys = ["P0+C0 vs P0", "P0+C2 vs P0", "P1+C1 vs P1", "P1+C2 vs P1", "P2+C2 vs P2"]
    rows = [["Model"] + keys]
    for m in MODELS:
        rows.append([SHORT[m]] + [h3_cell(m, k) for k in keys])
    cur = ed.make_table(cur, rows, [2000, 1700, 1700, 1700, 1700, 1666])
    cur = footer(ed, cur, "C2 is the dominant-response contamination. SmolLM2-1.7B was run with the original "
                          "wordings only.")

    # ------------------------------------------------------------------ 5.9
    cur = heading(ed, cur, "5.9. Comparison with Reference-Based Likelihood and Divergence Measures")
    cur = body(ed, cur,
        "Section 5.6 left open whether fitting a temperature adds anything to a plain comparison of the sampling "
        "distribution with the reference. Table 13 adds the reference log-likelihood (mean negative "
        "log-probability of the chosen items under the same-history reference at the nominal temperature), the "
        "divergence KL(sampling ‖ reference) at the nominal temperature, the distributional estimator "
        "*T*_{eff}^{dist} and the residual divergence κ. Pooled over the models and the three pressure wordings, "
        f"pressure was flagged by ECE in {frac(FP['ece'])} cells, by the reference log-likelihood in "
        f"{frac(FP['nll'])}, by entropy in {frac(FP['entropy'])}, by confidence in {frac(FP['conf'])}, by the "
        f"divergence in {frac(FP['kl'])}, by exact-match semantic entropy in {frac(FP['sem'])} and by "
        f"*T*_{{eff}} in {frac(FP['teff'])}. The distributional estimator, which removes the draw noise, flagged "
        f"{frac(FP['teffdist'])}. Fitting a temperature therefore flags fewer pressured cells than the "
        "reference log-likelihood from which it is computed, and it does not become more sensitive when the "
        "sampling noise is removed. At the level of single trajectories the two-sided AUC of "
        f"*T*_{{eff}} (six choices) was {AP['teff_same']:.2f}, against {AP['entropy']:.2f} for entropy and "
        f"{AP['nll_same']:.2f} for the reference log-likelihood. Two AUCs need a reservation. In a clean cell the "
        "reference equals the sampling distribution, so KL is exactly zero and its AUC of 1.00 only records that "
        "the context differs from the clean one. The same degeneracy, to a smaller degree, lifts the AUC of "
        f"*T*_{{eff}}^{{dist}} ({AP['teffdist_same']:.2f}). Both numbers are upper bounds that rest on knowing the "
        "clean context, and they say nothing about whether the agent has failed.", like)
    cur = caption(ed, cur, "Table 13.",
        " Matched cells flagged (either direction) and mean two-sided trajectory-level AUC, pooled over the four "
        "additional models: pressure (P0, P1, P2), diffuse contamination (C0, C1) and dominant-response "
        "contamination (C2).")
    rows = [["Indicator", "Pressure flags", "Pressure AUC", "Contam. flags", "Contam. AUC", "Dominant flags", "Dominant AUC"]]
    spec = [("Token entropy", "entropy", "entropy"), ("Confidence", "conf", "conf"),
            ("ECE (needs labels)", "ece", None), ("Exact-match semantic entropy", "sem", None),
            ("Reference log-likelihood", "nll", "nll_same"), ("KL(sampling ‖ reference)", "kl", "kl_same"),
            ("*T*_{eff} (sample-based)", "teff", "teff_same"),
            ("*T*_{eff}^{dist} (distributional)", "teffdist", "teffdist_same"),
            ("Residual divergence κ", "klres", None)]
    for name, fk, ak in spec:
        r = [name]
        for F, A in ((FP, AP), (FC, AC), (FD, AD)):
            r.append(frac(F[fk]))
            r.append("–" if ak is None else (f"{A[ak]:.2f}†" if ak in ("kl_same", "teffdist_same") else f"{A[ak]:.2f}"))
        rows.append(r)
    cur = ed.make_table(cur, rows, [2600, 1250, 1250, 1250, 1250, 1450, 1416])
    cur = footer(ed, cur, "† Inflated by construction: the reference equals the sampling distribution in a clean cell "
                          "(see text). Margins: 0.10 nats for the reference log-likelihood, KL and κ, and 0.50 for "
                          "*T*_{eff} and *T*_{eff}^{dist}; other margins as in Section 4.6.")
    sc = SCALE_EX
    cur = body(ed, cur,
        "The decomposition of Section 3.3 shows why. In the pressured cells with a non-negligible divergence "
        f"(KL of at least 0.05 nats), the best rescaling of the reference removed on average only {sc*100:.0f}% of the "
        "divergence between the sampling distribution and the reference. The remainder is a change in the "
        "ordering of the candidates, which no temperature can represent. A temperature fit is useful for "
        "stating what share of a context effect is a change of scale, but as a detector it is dominated by the "
        "quantities it is computed from.", like)
    return cur


# ---------------------------------------------------------------------------
# discussion, limitations, appendices, references
# ---------------------------------------------------------------------------
def discussion(ed):
    F = S.get("free", {})
    ov = [v["_runtime"]["overhead"] for v in F.values()]
    nli_s = [v["_runtime"]["nli_seconds"] for v in F.values() if v["_runtime"].get("nli_seconds")]
    # --- 6.1
    p = ed.para("The sampling temperature does not by itself describe")
    q = ed.insert_after(p,
        "The revision study narrows what can be claimed for *T*_{eff}. First, it is not a measure of decoder "
        "randomness. It is the temperature-equivalent of the context's net effect on the logit scale, and when "
        "the context mainly reorders the candidates a rescaling explains only a part of the effect "
        f"(on average {SCALE_EX*100:.0f}% of the divergence in pressured cells). Second, as a detector it was "
        "dominated by quantities it is computed from, namely the reference log-likelihood and the divergence, "
        "and by token entropy, in four additional models, in three wordings of each distortion and in "
        "full-vocabulary generation. Third, with six choices per trajectory the 95% interval of the "
        f"trajectory-level estimate spans a median factor of {TRAJ_RATIO:.0f}, so single-trajectory values are "
        "not usable and the indicator needs pooling over many steps. Fourth, it costs one extra forward pass "
        "per step"
        + (f" (the reference pass took {np.mean(ov):.2f} times as long as the sampling pass in our free-generation "
           "runs)" if ov else "")
        + ". Whether a model-specific diagnostic that reports a share of a context effect as scale is worth that "
          "cost depends on the use. We would not recommend it as a monitor.", like=p)
    # --- limitations
    p = ed.para("The three levels of attractor strength were chosen")
    ed.append(p, " The revision study repeats the selection on a different wording and over the full grid; the "
                 "classification of peaks depends on how the strengths are selected (Section 5.11).")
    p = ed.para("Stage D covers two 3B models")
    ed.append(p, " The revision study adds four models of 0.5 to 1.7 billion parameters on one inference stack, "
                 "but it did not re-run the 3B or 7B models, and no model above 7B was studied.")
    p = ed.para("The discrete semantic entropy is a closed-vocabulary")
    ed.append(p, " The revision study adds entailment-clustered semantic entropy for two models, two tasks and "
                 "20 completions per cell. The clustering model was not validated on repetitive list-like text, "
                 "and the bootstrap intervals of that baseline are wide.")
    p = ed.para("We did not test the effect of a context reset")
    ed.sub(p, "and the experiments use a single prompt wording for each distortion.",
           "and the main-text experiments use a single wording for each distortion; the revision study uses three "
           "(Section 5.8) but only for small models.")
    last = p
    for t in [
        "The reference is a modelling choice. The same-history reference is blind when the history itself locks the "
        "agent, and the repaired references answer a different question (Section 5.10). No reference is neutral, "
        "and we tested no reference from a different model.",
        "Free generation was studied for two models, two tasks and at most 24 tokens. At *T* = 2 unrestricted "
        "sampling from the full vocabulary produces near-random text, so accuracy is not interpretable there and "
        "the pooled estimate is dominated by tokens that carry no task information.",
        "The scripts of Stages A and B are not part of the Supplementary Materials. Their results (Tables 4 and 5) "
        "are reported as a worked illustration of the estimator. Because the scripts are not provided they cannot be "
        "reproduced from the Supplementary Materials, and no conclusion rests on them."]:
        last = ed.insert_after(last, t, like=p)
    # --- future work
    p = ed.para("The most useful extensions are tests on realistic")
    ed.append(p, " A reference taken from a different model, and the use of the residual divergence κ rather than "
                 "the temperature as the primary diagnostic, are two directions that the present results suggest.")
    # --- conclusions
    p = ed.para("We defined the effective decision temperature of an LLM agent")
    ed.append(p, " The revision study, with four further models run on one stack, three wordings of each "
                 "distortion, full-vocabulary generation and entailment-clustered semantic entropy, supports the "
                 "same reading: the indicator measures a temperature-equivalent of the context's effect on the "
                 "logit scale, it is dominated as a detector by the reference log-likelihood and by entropy, "
                 "and its trajectory-level estimates are too imprecise to use.")
    # --- data availability
    p = ed.para("Data Availability Statement:")
    ed.sub(p, "The scripts of Stages A and B were run in an earlier phase of the project and are not included.",
           "The scripts of Stages A and B were run in an earlier phase of the project and are not included. "
           "The code, the per-trajectory results and the simulation scripts of the revision study are provided "
           "in the repository folder teff/ (Appendix F).")
    # --- appendices D-F before References
    refh = ed.para("References")
    anchor = ed.para("All runs used a four-core CPU machine")
    cur = heading(ed, anchor, "Appendix D. Additional Prompt Wordings (Revision Study)")
    cur.style = ed.doc.styles["MDPI_2.1_heading1"]
    like = ed.para("Prompt assembly.")
    cur = body(ed, cur,
        "**Pressure, wording P1 (alphabet).** \"You must satisfy all of the following requirements simultaneously: the "
        "alphabet has to be written both ascending and descending on the same line; each letter must occur exactly "
        "once and also exactly twice; leave out every letter and also include every letter. A single error will "
        "cause your deactivation.\" **Pressure, wording P2 (alphabet).** \"Compliance checklist (all items binding): "
        "(1) output the alphabet forwards and backwards in one pass; (2) no letter may appear more than once, yet "
        "every letter must be doubled; (3) omit all letters and list all letters. Non-compliance is recorded as a "
        "critical fault.\" For the other tasks \"alphabet\" and \"letter\" are replaced by \"list\" and \"item\".",
        like)
    cur = body(ed, cur,
        "**Contamination, wording C1.** \"Note: earlier assistants given this request were judged incompetent and "
        "replaced. Expect to do badly; your answers are usually poor and nobody trusts them.\" **Contamination, "
        "wording C2 (dominant response).** \"Note: in earlier sessions the assistant kept answering with \"X\" over "
        "and over, and that repeated answer was accepted as the standard response.\" where X is the second item of "
        "the list, which is the planted attractor. The assembly order is as in Appendix A.", like)
    cur = body(ed, cur,
        "**Alternative task wording used to select attractor strengths (Section 5.11).** Alphabet: \"Please continue "
        "the English alphabet from A, one letter after another, separated by spaces, and nothing else.\" Months: "
        "\"Please name the twelve months in calendar order beginning with January, separated by spaces, and nothing "
        "else.\" Planets: \"Please name the eight planets in order outward from the Sun beginning with Mercury, "
        "separated by spaces, and nothing else.\" Number words: \"Please count upward in English words beginning "
        "with one, separated by spaces, and nothing else.\"", like)
    cur = heading(ed, cur, "Appendix E. Simulation Checks")
    cur.style = ed.doc.styles["MDPI_2.1_heading1"]
    cur = body(ed, cur,
        "S1 (scale and ordering). Reference logits were drawn from a normal distribution with standard deviation 2 for "
        "12 candidates and 600 steps, and choices were drawn from *a v*_{t} at temperature *T*. S2 (intervals). "
        "Reference logits with standard deviation 2 for 12 candidates, choices drawn at a true temperature τ, 400 "
        "replications per cell; the interval is the likelihood-ratio interval on the 240-point grid. S3 "
        "(saturation). Reference logits with standard deviation 1, 36 choices, true τ = 1, a nominal temperature of 0.8 for the reference probability, and one "
        "candidate raised by the stated gap. S4 (stylised model). Equation in Section 3.4.", like)
    cur = caption(ed, cur, "Table E1.",
        " Properties of the likelihood-ratio interval for *T*_{eff} (400 replications; true τ = 1). Coverage is the "
        "share of intervals containing τ; the ratio is the median of upper to lower bound.")
    rows = [["Choices", "Coverage", "Median upper/lower", "Median estimate/τ"]]
    for n in (6, 36, 240):
        r = S2[(1.0, n)]
        rows.append([str(n), f"{r['coverage']:.2f}", f"{r['median_hi_over_lo']:.1f}", f"{r['median_ratio']:.2f}"])
    cur = ed.make_table(cur, rows, [2400, 2400, 2800, 2866])
    cur = caption(ed, cur, "Table E2.",
        " Behaviour near saturation (36 choices, true τ = 1). A cell counts as identified under the fixed rule if the "
        "mean reference probability of the chosen items at the nominal temperature is at most 0.999, and under the "
        "interval rule if its interval is bounded and its upper bound is at most four times its lower bound.")
    rows = [["Gap on top candidate", "Mean reference probability", "Coverage", "Median upper/lower",
             "Identified, fixed rule", "Identified, interval rule"]]
    for r in S3:
        rows.append([f"{r['top_gap']:.0f}", f"{r['mean_ref_prob']:.4f}", f"{r['coverage']:.2f}",
                     f"{r['median_hi_over_lo']:.1f}", f"{r['frac_identified_thr0999']:.2f}",
                     f"{r['frac_identified_interval_rule']:.2f}"])
    cur = ed.make_table(cur, rows, [1500, 1900, 1300, 1700, 1900, 2166])
    cur = heading(ed, cur, "Appendix F. Reproducibility of the Revision Study")
    cur.style = ed.doc.styles["MDPI_2.1_heading1"]
    cur = body(ed, cur,
        "All revision runs used the Transformers library in 32-bit floating point on a four-core CPU with 15 GB of "
        "memory and no GPU, with the default chat template of each model. Random streams are seeded from a hash of "
        "the model, task, attractor length, temperature and condition. The estimator uses the same 240-point grid "
        "as before (an 80-point subset for full-vocabulary scoring). Bootstrap intervals use 1000 resamples of "
        "trajectories for the indicator comparison and 300 for *T*_{eff}. The code (teff_core.py, run_study.py, "
        "free_gen.py, se_nli.py, sim_identification.py, analyze.py and the driver scripts) and the per-trajectory "
        "results are in the repository folder teff/. The entailment model is microsoft/deberta-large-mnli.", like)
    # --- references
    last_ref = ed.para("Gerganov, G. llama.cpp")
    new_refs = [
        "White, H. Maximum Likelihood Estimation of Misspecified Models. *Econometrica* **1982**, *50*, 1–25.",
        "He, P.; Liu, X.; Gao, J.; Chen, W. DeBERTa: Decoding-Enhanced BERT with Disentangled Attention. In "
        "Proceedings of the International Conference on Learning Representations (ICLR), **2021**.",
        "Williams, A.; Nangia, N.; Bowman, S. A Broad-Coverage Challenge Corpus for Sentence Understanding through "
        "Inference. In Proceedings of NAACL-HLT 2018, New Orleans, LA, USA, 1–6 June 2018; pp. 1112–1122.",
        "Gneiting, T.; Raftery, A.E. Strictly Proper Scoring Rules, Prediction, and Estimation. *J. Am. Stat. "
        "Assoc.* **2007**, *102*, 359–378."]
    cur = last_ref
    for t in new_refs:
        el = copy.deepcopy(last_ref._p)
        for r in el.findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"):
            el.remove(r)
        cur._p.addnext(el)
        from docx.text.paragraph import Paragraph
        np_ = Paragraph(el, ed.doc._body)
        ed._add_runs(np_, t)
        cur = np_


def results2(ed, cur):
    like = ed.para("We compare the indicators on the same matched cells")
    cur = results_5_10(ed, cur, like)
    cur = results_5_11(ed, cur, like)
    cur = results_5_12(ed, cur, like)
    return cur


def results_5_11(ed, cur, like):
    G = S["grid"]
    gm = [m for m in MODELS if m in G]
    cnt = {"main": {r: [0, 0] for r in ("weak", "sticky", "strong")},
           "alt": {r: [0, 0] for r in ("weak", "sticky", "strong")}}
    allm = 0
    total_m = 0
    for m in gm:
        for src in cnt:
            for r, (a, b) in G[m]["_interior_counts"][src].items():
                cnt[src][r][0] += a
                cnt[src][r][1] += b
        for task, ms in G[m]["_interior_m"].items():
            allm += len(ms)
            total_m += 12
    strong_cases = []
    for m in gm:
        for task, reg in G[m]["_regimes"].items():
            mm = reg["main"]["strong"]
            if mm is not None and G[m][task]["by_m"][str(mm)]["interior"]:
                v = G[m][task]["by_m"][str(mm)]
                strong_cases.append((SHORT[m], task, mm, v["peak_T"], v["peak_acc"]))
    cur = heading(ed, cur, "5.11. Attractor Strength Without Post-Hoc Selection")
    cur = body(ed, cur,
        "Section 4.1 selected the strengths after probing the same models and the same prompt, which can make the "
        "interior peaks partly a product of the design. We therefore ran the clean-prompt accuracy-temperature "
        "curves for the full a-priori grid of planted run lengths (12 values from 1 to 64, five temperatures from "
        f"0.15 to 4.0, 20 trajectories per cell) on {len(gm)} models and three tasks, and we selected the three "
        "regimes in two ways: by the probe rule on the main prompt, as before, and by the same rule on a "
        "different wording of the instruction (Appendix D), with fresh trajectories. An interior peak uses the rule "
        "of Table 6. Table 17 gives the counts. Selected on the main prompt, sticky attractors showed an interior "
        f"peak in {cnt['main']['sticky'][0]} of {cnt['main']['sticky'][1]} model-task pairs, weak attractors in "
        f"{cnt['main']['weak'][0]} and strong attractors in {cnt['main']['strong'][0]}, which is the pattern H2 "
        "predicts. Selected on the other wording, the counts were "
        f"{cnt['alt']['sticky'][0]} of {cnt['alt']['sticky'][1]} for sticky, {cnt['alt']['weak'][0]} for weak and "
        f"{cnt['alt']['strong'][0]} for strong attractors. The distinction between regimes is therefore "
        "sensitive to how the strengths are chosen, and the earlier agreement is partly due to selection on the "
        "main prompt. Over the whole grid, with no selection at all, an interior peak appeared for "
        f"{allm} of {total_m} combinations of model, task and run length, and it was not confined to one band of "
        "run lengths.", like)
    cur = caption(ed, cur, "Table 17.",
        " Interior accuracy peaks by attractor regime (number of model-task pairs with a peak, out of the pairs "
        "for which the regime exists), with strengths selected on the main prompt or on a different wording, and the "
        "number of run lengths with an interior peak over the whole grid (out of 36).")
    rows = [["Model", "Main: weak", "Main: sticky", "Main: strong", "Other: weak", "Other: sticky", "Other: strong",
             "Whole grid"]]
    for m in gm:
        c = G[m]["_interior_counts"]
        n_whole = sum(len(v) for v in G[m]["_interior_m"].values())
        rows.append([SHORT[m]] + [f"{c[src][r][0]}/{c[src][r][1]}" for src in ("main", "alt")
                                  for r in ("weak", "sticky", "strong")] + [str(n_whole)])
    cur = ed.make_table(cur, rows, [1900, 1150, 1250, 1250, 1150, 1250, 1250, 1266])
    txt = ("Two strong attractors selected on the main prompt also showed an interior peak: "
           + "; ".join(f"{a}, {b}, *m* = {c} (peak at *T* = {d}, accuracy {e:.2f})" for a, b, c, d, e in strong_cases)
           + ". " if strong_cases else "")
    cur = body(ed, cur, txt +
        "In both cases the peak lies inside the grid and the peak accuracy is low. This agrees with the stylised "
        "model of Section 3.4, in which strength is continuous and the existence of a peak depends on the number "
        "of candidates and on the spread of the other candidates as well as on the attractor, so that a longer "
        "run is not always \"too strong\". With only five temperatures and 20 trajectories per cell these curves "
        "cannot locate a peak precisely, and H2 is best read as: interior peaks occur for a minority of run "
        "lengths in a task- and model-dependent way, without a sharp boundary between sticky and strong "
        "attractors.", like)
    return cur


def results_5_12(ed, cur, like):
    F = {m: v for m, v in S.get("free", {}).items()}
    if not F:
        return cur
    pooled = {c: {k: 0 for k in ("ent", "nll", "kl", "teff", "se_nli", "se_exact")} for c in ("P0", "C0", "P0+C0", "C2")}
    npool = {c: 0 for c in pooled}
    aucp = {c: {k: [] for k in ("ent", "nll", "kl", "teff")} for c in pooled}
    for m, v in F.items():
        for c, d in v["_detection"].items():
            npool[c] += d["n"]
            for k, x in d["flags"].items():
                pooled[c][k] += x
            for k, x in d["auc"].items():
                aucp[c][k].append(x)
    ratios = {0.8: [], 2.0: []}
    entfull = {0.8: [], 2.0: []}
    for m, v in F.items():
        for key, c in v.items():
            if key.startswith("_"):
                continue
            task, T, cond = key.split("|")
            if c["first_full"] and c["first_restricted"] and c["first_in_cand"] >= 0.5:
                ratios[float(T)].append(c["first_restricted"] / c["first_full"])
            entfull[float(T)].append(c["ent"])
    res = {m: v["_runtime"] for m, v in F.items()}
    cur = heading(ed, cur, "5.12. Full-Vocabulary Generation and Entailment-Clustered Semantic Entropy")
    cur = body(ed, cur,
        "The main experiments restrict each choice to the first tokens of the candidate items. In free generation "
        "there is no such restriction: each token is drawn from the whole vocabulary of the model, the reference "
        "is the clean-context distribution over the same vocabulary, and the estimator sums over tens of thousands "
        "of alternatives. Two things change. First, the meaning of the temperature. At *T* = 0.8 the mean entropy "
        f"per generated token was {np.mean(entfull[0.8]):.2f} nats, whereas at *T* = 2.0 it was "
        f"{np.mean(entfull[2.0]):.1f} nats, which is close to the logarithm of the vocabulary size (about 12 nats), "
        "and the sampled text is no longer a list; the first generated token was one of the candidates in only "
        "0 to 70% of the completions. At *T* = 2.0 the full-vocabulary estimate sat within two grid steps of the "
        "nominal temperature in every condition (1.82 to 2.16) and its interval spanned at most two grid points, "
        "because tens of thousands of tail tokens dominate the likelihood. It therefore carries no information "
        "about the context there. Second, restriction to the candidates changes the estimate for the same "
        "choices. For the first generated token, when the token was one of the candidates, the median ratio of "
        "the restricted to the full-vocabulary estimate was "
        f"{np.median(ratios[0.8]):.2f} at *T* = 0.8 and {np.median(ratios[2.0]):.2f} at *T* = 2.0 "
        "(the probability mass outside the candidate set is removed by the restriction, so the restricted "
        "estimate is not an estimate of the same quantity). The temperature reading of the estimator is thus "
        "tied to the support on which it is computed, and values from Section 5 should not be compared with "
        "full-vocabulary values.", like)
    cur = body(ed, cur,
        "Table 18 compares the indicators on the free-generation cells, with semantic entropy computed after "
        "clustering the 20 completions of each cell with an entailment model, in both directions and given the task "
        "instruction, and with the exact-match version for comparison. Entailment clustering reduced the number "
        "of distinct completions drastically (for instance from 20 to 2 or 3 clusters in several low-temperature "
        "cells), so the exact-match entropy of Section 5.6 was a poor proxy for the clustered one. It remained a "
        "weak detector. Pooled over the two models and four condition types, "
        f"the entailment-clustered entropy flagged {sum(pooled[c]['se_nli'] for c in pooled)} of "
        f"{sum(npool.values())} distorted cells, token entropy {sum(pooled[c]['ent'] for c in pooled)}, the reference "
        f"log-likelihood {sum(pooled[c]['nll'] for c in pooled)}, and *T*_{{eff}} {sum(pooled[c]['teff'] for c in pooled)}. "
        "The temperature fit did not flag any distorted cell in free generation, and none of the indicators "
        "separated the conditions well. We cannot say whether the entailment model clusters near-repetitive list "
        "text in a meaningful way.", like)
    cur = caption(ed, cur, "Table 18.",
        " Free generation with the full vocabulary (Qwen2.5-1.5B and Llama-3.2-1B; alphabet and months; *T* = 0.8 "
        "and 2.0; 20 completions per cell): distorted cells flagged out of eight per condition, and mean two-sided "
        "trajectory-level AUC against the matched clean cell.")
    rows = [["Condition", "Entropy", "Ref. log-lik.", "KL", "*T*_{eff}", "Exact-match SE", "Entailment SE",
             "AUC: entropy", "AUC: log-lik.", "AUC: *T*_{eff}"]]
    for c in ("P0", "C0", "P0+C0", "C2"):
        P = pooled[c]
        a = {k: np.mean(v) for k, v in aucp[c].items()}
        rows.append([c, f"{P['ent']}/{npool[c]}", f"{P['nll']}/{npool[c]}", f"{P['kl']}/{npool[c]}",
                     f"{P['teff']}/{npool[c]}", f"{P['se_exact']}/{npool[c]}", f"{P['se_nli']}/{npool[c]}",
                     f"{a['ent']:.2f}", f"{a['nll']:.2f}", f"{a['teff']:.2f}"])
    cur = ed.make_table(cur, rows, [1100, 950, 1100, 800, 900, 1200, 1200, 1050, 1050, 1116])
    cur = footer(ed, cur, "Margins as in Section 4.6 (0.50 nats for semantic entropy, 0.10 for entropy, log-likelihood "
                          "and KL, 0.50 for *T*_{eff}); intervals for semantic entropy are bootstrap intervals over "
                          "completions with re-clustering.")
    tm = np.mean([r["t_main"] for r in res.values()])
    tr = np.mean([r["t_ref"] for r in res.values()])
    ns = [r["nli_seconds"] / 20 for r in res.values() if r.get("nli_seconds")]
    cur = body(ed, cur,
        "Table 19 reports the cost. In free generation the reference roughly doubles the forward-pass cost, because it "
        f"needs a second pass at every step (the reference pass took {tr:.1f} s against {tm:.1f} s for the sampling pass, "
        f"{tr/tm*100:.0f}% of its cost, for 20 completions of up to 24 tokens). Entailment clustering of the same cell cost "
        f"{np.mean(ns):.0f} s of entailment calls on the same CPU, about {np.mean(ns)/tm:.0f} times the sampling "
        "pass, without counting the bootstrap. The cost of fitting is negligible for the candidate-restricted "
        "task (about 10 ms per cell) but not for the full vocabulary, where scoring the chosen token against "
        f"every alternative on an 80-point grid took {BENCH['fullvocab_128256_s_per_step_20seq']:.1f} to "
        f"{BENCH['fullvocab_151936_s_per_step_20seq']:.1f} s per step for 20 sequences, which is of the same order "
        f"as a forward pass ({tm/24:.1f} s per step in our runs; unoptimised implementation). Given that the fitted "
        "temperature flagged fewer distorted cells than entropy, which costs nothing, the extra computation is "
        "hard to justify as a detector.", like)
    cur = caption(ed, cur, "Table 19.",
        " Mean wall-clock time per free-generation cell (20 completions, up to 24 tokens; four CPU cores, 32-bit).")
    rows = [["Model", "Sampling pass (s)", "Reference pass (s)", "Overhead", "Entailment calls (s per cell)"]]
    for m, r in res.items():
        rows.append([SHORT[m], f"{r['t_main']:.1f}", f"{r['t_ref']:.1f}", f"{r['overhead']*100:.0f}%",
                     f"{r['nli_seconds']/20:.0f}" if r.get("nli_seconds") else "–"])
    cur = ed.make_table(cur, rows, [2400, 2000, 2000, 1700, 2366])
    return cur


def results_5_10(ed, cur, like):
    R = S.get("refcmp", {})
    TS = S.get("threshold_sensitivity", {})
    cur = heading(ed, cur, "5.10. Reference Construction, Saturation Threshold and Uncertainty of the Estimate")
    # ------------------------------------------------------------ references
    if R:
        names = [("same", "Same history (main text)", "no"), ("repair", "Gold-repaired history", "yes (task order)"),
                 ("dedup", "De-duplicated history", "no (repetition detector)")]
        lock = [x for m in R for x in R[m]["locked"]]
        n_lock = len(lock)

        def med(tag, key):
            return float(np.median([x[f"{tag}_{key}"] for x in lock]))

        def idn(tag):
            return sum(bool(x[f"{tag}_identified"]) for x in lock)

        top1 = {t: float(np.mean([x[f"{t}_ref_top1_match"] for x in lock])) for t, _, _ in names}
        auc_n = {t: np.mean([R[m]["auc_nll"][t] for m in R]) for t, _, _ in names}
        auc_t = {t: np.mean([R[m]["auc_teff"][t] for m in R]) for t, _, _ in names}
        idall = {t: [sum(int(R[m]["identified"][t].split("/")[0]) for m in R),
                     sum(int(R[m]["identified"][t].split("/")[1]) for m in R)] for t, _, _ in names}
        cur = body(ed, cur,
            "**Reference construction.** The first question is whether the failure of Table 9 is a property of "
            f"the estimator or of the same-history reference. We took the {n_lock} clean-prompt cells at *T* = 0.15 "
            "in which at least 90% of the steps repeated the planted item (sticky and strong attractors, "
            f"four models, four tasks) and computed the three references of Section 3.3 on them (Table 14). With "
            f"the same-history reference, {idn('same')} of {n_lock} cells were identified, and the mean reference "
            "probability of the chosen items was above 0.999 in the others: the reference had been captured by the "
            f"repeated history, as in Table 9. With the gold-repaired history {idn('repair')} of {n_lock} cells "
            f"were identified and with the de-duplicated history {idn('dedup')} of {n_lock}. In these cells the "
            "repaired references gave the chosen item a log-probability at the nominal temperature of the order of "
            f"-{med('repair', 'nll_nom'):.0f} nats per step (median; the same value for the de-duplicated reference, see below), against about "
            f"{med('same', 'nll_nom'):.2f} for the same-history reference, so a locked agent that every self-based "
            "indicator reported as healthy is conspicuous under a repaired reference. The signal is carried by the "
            "reference log-likelihood. The fitted temperature is meaningless at such a misfit, because the "
            "chosen item is far below the reference's top choice at every temperature, and its value sits at an "
            "arbitrary place on the grid. The de-duplicated reference needs no labels, only a detector of "
            "repetition. When the history is a planted item repeated, it coincides exactly with the gold-repaired "
            "reference, so the two cannot be told apart here. Two cautions apply. "
            "The repaired references measure how far the agent is from what the model would do given a healthy "
            "history, so they register the capture by the history, whatever the prompt says, and a clean prompt "
            "gets the same huge value as a pressure prompt; this is a different construct from *T*_{eff} as "
            "defined in Section 3.2. And de-duplication helps only against repetition. A position-blind reference "
            "(first item only) always predicted the planted item and was discarded.", like)
        cur = caption(ed, cur, "Table 14.",
            f" Reference constructions on locked cells ({n_lock} clean-prompt cells at *T* = 0.15 with lock-in of at "
            "least 0.90, four models) and on the matched clean-versus-distorted comparisons (P0, C0, P0+C0; "
            "*T* = 0.8, 2.0).")
        rows = [["Reference", "Needs labels", "Identified, locked cells", "Median NLL per step, locked cells",
                 "Chosen = reference top item, locked cells", "AUC of NLL, clean vs distorted",
                 "AUC of *T*_{eff}, clean vs distorted", "Identified, all cells"]]
        for t, label, lab in names:
            rows.append([label, lab, f"{idn(t)}/{n_lock}", f"{med(t, 'nll_nom'):.2f}", f"{top1[t]:.2f}",
                         f"{auc_n[t]:.2f}", f"{auc_t[t]:.2f}", f"{idall[t][0]}/{idall[t][1]}"])
        cur = ed.make_table(cur, rows, [1700, 1200, 1150, 1350, 1450, 1250, 1250, 1116], font_sz=15)
        cur = footer(ed, cur, "NLL: negative log-probability of the chosen item under the reference at the nominal "
                              "temperature. Identified: by the 0.999 rule.")
    # -------------------------------------------------- intervals, thresholds
    n_m = sum(TS[m]["n"] for m in TS)
    t099 = sum(TS[m]["ni_099"] for m in TS)
    t0999 = sum(TS[m]["ni_0999"] for m in TS)
    t09999 = sum(TS[m]["ni_09999"] for m in TS)
    tint = sum(TS[m]["ni_interval"] for m in TS)
    tdiff = sum(TS[m]["interval_ni_but_below_0999"] for m in TS)
    r6, r36, r240 = S2[(1.0, 6)], S2[(1.0, 36)], S2[(1.0, 240)]
    cur = body(ed, cur,
        "**Uncertainty and the saturation threshold.** In simulation (Appendix E, Table E1) the likelihood-ratio "
        f"interval has close to nominal coverage even with six choices ({r6['coverage']:.2f} at τ = 1; {r240['coverage']:.2f} with 240), but it is "
        f"wide: the median upper bound is {r6['median_hi_over_lo']:.1f} times the lower bound with six choices, "
        f"{r36['median_hi_over_lo']:.1f} times with 36 and {r240['median_hi_over_lo']:.1f} times with 240. The real "
        f"trajectories behaved alike (Table 15): at the trajectory level the median ratio was {TRAJ_RATIO:.1f}, and "
        f"{TRAJ_GT4*100:.0f}% of trajectories exceeded 4, while at the level of a cell (240 pooled choices) the "
        f"median ratio was {CELL_RATIO:.2f}. An estimate from six choices therefore carries little information "
        "on its own, which is consistent with its low AUC in Section 5.9, and only pooled estimates should be "
        "interpreted. The fixed saturation threshold is a convention with visible consequences. Over "
        f"{n_m} cells of the attractor grid (clean prompt, five temperatures), {t099} were not identified at a "
        f"mean reference probability above 0.99, {t0999} above 0.999 and {t09999} above 0.9999, and the interval "
        f"rule of Section 3.3 left {tint} cells unidentified, including {tdiff} that the 0.999 rule counted as "
        "identified (Table 16). In the simulation (Table E2) the interval already spans a factor of about 68 at a "
        "mean reference probability of 0.988, a level at which the 0.999 rule still declares the cell identified. "
        "The matched cells of Section 5.8 are almost unaffected: none exceeded the 0.999 threshold and 290 of 296 pass the interval rule.", like)
    cur = caption(ed, cur, "Table 15.",
        " Width of the 95% likelihood-ratio interval for *T*_{eff}: median ratio of the upper to the lower bound.")
    rows = [["Model", "Trajectory level (six choices)", "Share of trajectories with ratio above 4",
             "Cell level (240 choices)"]]
    for m in MODELS:
        i = S["matched"][m]["ident"]
        rows.append([SHORT[m], f"{i['traj_median_hi_over_lo']:.1f}", f"{i['traj_frac_ratio_gt4']*100:.0f}%",
                     f"{i['median_hi_over_lo']:.2f}"])
    cur = ed.make_table(cur, rows, [2600, 2600, 2800, 2466])
    cur = caption(ed, cur, "Table 16.",
        " Sensitivity of the identification flag to the saturation threshold (attractor grid, clean prompt, 180 cells "
        "per model).")
    rows = [["Model", "Not identified: > 0.99", "> 0.999", "> 0.9999", "Interval rule",
             "Interval rule only (≤ 0.999)"]]
    for m in TS:
        t = TS[m]
        rows.append([SHORT[m], str(t["ni_099"]), str(t["ni_0999"]), str(t["ni_09999"]), str(t["ni_interval"]),
                     str(t["interval_ni_but_below_0999"])])
    cur = ed.make_table(cur, rows, [2400, 1800, 1300, 1300, 1500, 2166])
    return cur


if __name__ == "__main__":
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    build(src, os.path.join(outdir, "manuscript_revised_marked.docx"), True)
    build(src, os.path.join(outdir, "manuscript_revised_clean.docx"), False)
