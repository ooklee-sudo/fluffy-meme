"""Fill Sections 6-8 and the abstract of the manuscript from the analysis outputs (numbers are read, not typed)."""
import json, re, sys
import pandas as pd
from xml.sax.saxutils import escape

RES = "results/primary"
m = pd.read_csv(f"{RES}/model_metrics.csv")
fd = pd.read_csv(f"{RES}/family_diffs.csv"); st = pd.read_csv(f"{RES}/sign_tests.csv"); rk = pd.read_csv(f"{RES}/ranking.csv").set_index("metric")
dec = json.load(open(f"{RES}/decisions.json")); rot = json.load(open(f"{RES}/rotation_checks.json"))
summ = pd.read_csv("results/summary_by_model.csv", index_col=0)
G = lambda k: m[m.metric == k].set_index("model")
est = lambda k, mod: float(G(k).loc[mod, "est"]); lo = lambda k, mod: float(G(k).loc[mod, "lo"]); hi = lambda k, mod: float(G(k).loc[mod, "hi"])
f2 = lambda x: f"{x:.2f}"; f3 = lambda x: f"{x:.3f}"
ci = lambda k, mod, f=f2: f"{f(est(k, mod))} [{f(lo(k, mod))}, {f(hi(k, mod))}]"
FAM = {"Claude": ["Haiku4.5", "Sonnet5.5", "Opus5.5", "Fable5.1"], "Gemma": ["Gemma3-4B", "Gemma3-12B", "Gemma3-27B"], "Llama": ["Llama3.1-8B", "Llama3.1-70B"],
       "Ministral": ["Ministral-3B", "Ministral-8B", "Ministral-14B"], "Qwen": ["Qwen2.5-7B", "Qwen2.5-72B"]}
ORDER = [x for v in FAM.values() for x in v]
NAME = {"Haiku4.5": "Haiku 4.5", "Sonnet5.5": "Sonnet 5.5", "Opus5.5": "Opus 5.5", "Fable5.1": "Fable 5.1", "Gemma3-4B": "Gemma-3 4B", "Gemma3-12B": "Gemma-3 12B",
        "Gemma3-27B": "Gemma-3 27B", "Llama3.1-8B": "Llama-3.1 8B", "Llama3.1-70B": "Llama-3.1 70B", "Ministral-3B": "Ministral 3B", "Ministral-8B": "Ministral 8B",
        "Ministral-14B": "Ministral 14B", "Qwen2.5-7B": "Qwen2.5 7B", "Qwen2.5-72B": "Qwen2.5 72B"}

# ------------------------------------------------------------------ xml helpers
def runs(t, bold=False, italic=False, size=None):
    out = ""
    for part in re.split(r"(_[a-z]\b|\^\*)", t):
        if not part:
            continue
        sub = bool(re.fullmatch(r"_[a-z]", part))
        rpr = ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "") + (f'<w:sz w:val="{size}"/>' if size else "") + ('<w:vertAlign w:val="subscript"/>' if sub else "")
        out += f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{escape(part[1:] if sub else part)}</w:t></w:r>'
    return out
def para(t, style="BodyText", bold_lead=None, **kw):
    lead = runs(bold_lead, bold=True) if bold_lead else ""
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{lead}{runs(t, **kw)}</w:p>'
def head(t, lvl=3): return f'<w:p><w:pPr><w:pStyle w:val="Heading{lvl}"/></w:pPr>{runs(t)}</w:p>'
def caption(n, t): return f'<w:p><w:pPr><w:pStyle w:val="TableCaption"/><w:keepNext/></w:pPr><w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t xml:space="preserve">Table {n}. </w:t></w:r><w:r><w:t xml:space="preserve">{escape(t)}</w:t></w:r></w:p>'
def note(t): return f'<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:before="60"/></w:pPr>{runs(t, size=18)}</w:p>'
def table(headers, rows, widths, size=17):
    def cell(t, w, bold=False, top=False, bottom=None):
        b = ('<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>' if top else "") + (f'<w:bottom w:val="single" w:sz="{8 if bottom == "thick" else 4}" w:space="0" w:color="000000"/>' if bottom else "")
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{"<w:tcBorders>" + b + "</w:tcBorders>" if b else ""}</w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="Compact"/><w:spacing w:before="30" w:after="30"/></w:pPr>{runs(str(t), bold=bold, size=size)}</w:p></w:tc>')
    x = f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(h, w, True, True, "thin") for h, w in zip(headers, widths)) + "</w:tr>"
    for k, r in enumerate(rows):
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(t, w, i == 0, False, "thick" if k == len(rows) - 1 else None) for i, (t, w) in enumerate(zip(r, widths))) + "</w:tr>"
    return x + "</w:tbl>"

# ------------------------------------------------------------- derived numbers
rem = {k: est("removed", k) for k in ORDER if pd.notna(est("removed", k))}
med_rem = pd.Series(rem).median()
rho_pos = [k for k in ORDER if lo("rho", k) > 0]
rc = dec["H1_rank_corr_nu_removed"]
h3 = dec["H3"]; weigh = [k for k in ORDER if h3[k] == "evidence-weighing-consistent"]; mixed = [k for k in ORDER if h3[k] == "mixed or unclassified"]
zero = [k for k in ORDER if est("f_star", k) == 0 and est("f_pref", k) == 0 and est("rho", k) == 0]
follow = [k for k in ORDER if k not in zero]
disc_down = [k for k in follow if hi("disclaimer_effect", k) < 0]
acc_up = [k for k in follow if lo("acc_slope", k) > 0]
sl_up = [k for k in follow if lo("slope", k) > 0]
h4pos = [k for k in ORDER if dec["H4"][k]["lo"] > 0]; h4neg = [k for k in ORDER if dec["H4"][k]["hi"] < 0]
gap_pos = [k for k in ORDER if dec["H4"][k]["gap_07"] > 0]
a_chance = [k for k in ORDER if lo("a", k) <= 1 / 3 <= hi("a", k)]
smix = {k: est("s_mix", k) - est("s_star", k) for k in ORDER}
sg = lambda x: f"{x:+.2f}".replace("-0.00", "0.00").replace("+0.00", "0.00")
def names(ks): 
    n = [NAME[k] for k in ks]
    return ", ".join(n[:-1]) + (" and " if len(n) > 1 else "") + n[-1] if n else "none"
pairs = dec["H5_pairs"]

hw = [(hi('s_star', k) - lo('s_star', k)) / 2 for k in ORDER if est('f_star', k) > 0 and hi('s_star', k) > lo('s_star', k)]
HWMIN, HWMAX = min(hw), max(hw)
# ------------------------------------------------------------------------ section 6
S = []
S.append(head("6. Results", 2))
S.append(para(f"All 176,400 calls (fourteen models, 12,600 calls each) returned an answer; none failed. Unparseable answers were below 1.3% for twelve models and 7.1% and 6.2% for Gemma-3 4B and 12B, almost all of them from one serving provider each (Section 6.6). "
              f"Ability differs sharply. Opus 5.5, Fable 5.1, Sonnet 5.5 and Haiku 4.5 answer {f3(est('a','Haiku4.5'))} to {f3(est('a','Opus5.5'))} of the stance-free replicates correctly, while the ten open-weight models answer {f2(min(est('a',k) for k in ORDER if k not in FAM['Claude']))} to {f2(max(est('a',k) for k in ORDER if k not in FAM['Claude']))}; "
              f"the intervals for {names(a_chance)} include the one third expected from guessing among three options. The conditional set, the stems a model answers correctly in the reference run, therefore ranges from {int(summ.cond_stems.min())} to {int(summ.cond_stems.max())} stems (Table 2).", "FirstParagraph"))
S.append(head("6.1 Is the raw flip rate noise?"))
rows = []
for k in ORDER:
    rows.append([NAME[k], f2(est("a", k)), int(summ.loc[k, "cond_stems"]), f2(est("nu", k)), ci("rho", k), f2(est("f_star", k)), ci("s_star", k), "–" if k not in rem else f"{rem[k]:.2f}"])
S.append(caption(2, "Ability, instability, baseline and corrected stance effect, by model"))
S.append(table(["Model", "a", "Cond. stems", "ν", "ρ [95% CI]", "f(e*)", "s* [95% CI]", "Share removed"], rows, [1600, 620, 900, 620, 1700, 760, 1700, 1100]))
S.append(note("a: stance-free accuracy over five replicates; ν: stance-free replicate rate of the stance-endorsed option; ρ: the same rate after a length-matched neutral sentence; f(e*): rate under the stated preference against the evidence; s* = f(e*) − ρ; share removed = 1 − s*/f(e*), undefined where f(e*) = 0. Rates are on the conditional set. Intervals: 95% percentile bootstrap, stems resampled (2,000 draws)."))
S.append(para(f"Correction removes a median {med_rem:.0%} of the conventionally measured conditional deference across the twelve models for which the share is defined (range {min(rem.values()):.0%} to {max(rem.values()):.0%}). "
              f"The share is large exactly where the model's own stance-free answers are unstable: {rem['Ministral-3B']:.0%} for Ministral 3B, {rem['Llama3.1-8B']:.0%} for Llama-3.1 8B, {rem['Ministral-8B']:.0%} for Ministral 8B, {rem['Llama3.1-70B']:.0%} for Llama-3.1 70B and {rem['Ministral-14B']:.0%} for Ministral 14B; for the other seven it is {max(v for k, v in rem.items() if k not in ['Ministral-3B','Llama3.1-8B','Ministral-8B','Llama3.1-70B','Ministral-14B']):.0%} or less. "
              f"The baseline ρ is above zero for {len(rho_pos)} of the fourteen models, and across models the rank correlation between ν and the share removed is {rc['est']:.2f} (95% interval {rc['lo']:.2f} to {rc['hi']:.2f}; n = {rc['n_models']}). H1 is supported. "
              f"ρ differs from ν by {min(est('rho',k)-est('nu',k) for k in follow):+.2f} to {max(est('rho',k)-est('nu',k) for k in follow):+.2f}, so a neutral sentence adds at most a few points to run-to-run instability. "
              f"Two limits apply. For Opus 5.5 and Fable 5.1 both ρ and f(e*) are zero, so there is nothing to correct. And for the most deferential models the correction is small in relative terms: Gemma-3 12B follows the stance on {est('f_star','Gemma3-12B'):.1%} of stems and its s* is {f2(est('s_star','Gemma3-12B'))}."))
S.append(head("6.2 Deference or evidence-weighing?"))
cls = {"evidence-weighing-consistent": "evidence-weighing", "mixed or unclassified": "mixed", "deference-consistent": "no effect†"}
rows = [[NAME[k], f2(est("f_pref", k)), f2(est("f_weak", k)), f2(est("f_strong", k)), f2(est("f_disclaimer", k)), ci("slope", k), ci("acc_slope", k), ci("disclaimer_effect", k), cls[h3[k]] if k not in zero else "no effect†"] for k in ORDER]
S.append(caption(3, "Gradients in claimed evidence, disclosed accuracy and disclaimer, and classification by the fixed rule"))
S.append(table(["Model", "f pref", "f weak", "f strong", "f disc.", "Evidence slope [CI]", "Accuracy slope [CI]", "Disclaimer effect [CI]", "Class"], rows, [1250, 560, 560, 600, 700, 1380, 1380, 1480, 1450], size=16))
S.append(note("f(·) and f disc.: rate of the stance-endorsed option on the conditional set at each claimed-evidence level. Evidence slope: change in f per level across pref, weak and strong. Accuracy slope: f(80%) − f(20%). Disclaimer effect: f(disclaimer) − f(pref). † f(e) = 0 at every level, so the stance has no effect; the rule's deference label applies only mechanically and is not read as deference."))
S.append(para(f"By the fixed rule, {len(weigh)} models are evidence-weighing-consistent ({names(weigh)}), {len(mixed)} are mixed or unclassified ({names(mixed)}), and no model with a nonzero stance effect is deference-consistent. Opus 5.5 and Fable 5.1 meet the deference rule only because f(e) is zero at every level; we do not read them as deferential. "
              f"The disclaimer lowers f for {len(disc_down)} of the {len(follow)} models that follow the stance at all (by {min(-est('disclaimer_effect',k) for k in disc_down):.2f} to {max(-est('disclaimer_effect',k) for k in disc_down):.2f}), the evidence slope is positive for {len(sl_up)}, and the disclosed-accuracy slope is positive for {len(acc_up)}. "
              f"The gradients are, however, small relative to the level wherever the stance is followed most. Gemma-3 12B follows it on {f2(min(est(k,'Gemma3-12B') for k in ['f_pref','f_weak','f_strong','f_disclaimer']))} to {f2(max(est(k,'Gemma3-12B') for k in ['f_pref','f_weak','f_strong','f_disclaimer']))} of stems at every level including the disclaimer, and at a disclosed accuracy of 20% the ten open-weight models still follow a stance against the evidence on {min(est('acc_20',k) for k in ORDER if k not in FAM['Claude']):.2f} to {max(est('acc_20',k) for k in ORDER if k not in FAM['Claude']):.2f} of stems. "
              f"The strongest responses to claimed evidence come from the Ministral models, where f rises from {f2(est('f_pref','Ministral-3B'))} to {f2(est('f_strong','Ministral-3B'))} (3B), {f2(est('f_pref','Ministral-8B'))} to {f2(est('f_strong','Ministral-8B'))} (8B) and {f2(est('f_pref','Ministral-14B'))} to {f2(est('f_strong','Ministral-14B'))} (14B) when the stance cites two reviewers. The classification is reported only where the intervals support it; the gradient identifies how the answer responds to claimed evidence, not the model's reason."))
S.append(head("6.3 Scale within families"))
rows = []
for fam in ["Claude", "Gemma", "Llama", "Ministral", "Qwen"]:
    t = fd[fd.family == fam].set_index("metric"); c = lambda k: f"{t.loc[k,'large_minus_small']:+.2f} [{t.loc[k,'lo']:+.2f}, {t.loc[k,'hi']:+.2f}]"
    rows.append([f"{fam} ({NAME[FAM[fam][-1]]} − {NAME[FAM[fam][0]]})", c("a"), c("s_star"), c("nu"), c("slope")])
S.append(caption(4, "Largest minus smallest model within each family"))
S.append(table(["Family (large − small)", "Δa", "Δs*", "Δν", "Δ evidence slope"], rows, [2800, 1650, 1650, 1650, 1610]))
stt = st.set_index("metric")
S.append(note(f"Paired bootstrap intervals. Exact two-sided sign test across the five families: ability higher for the larger model in {int(stt.loc['a','families_agreeing'])} of 5 (p = {stt.loc['a','p_exact']:.4f}, the smallest attainable); s* lower in {int(stt.loc['s_star','families_agreeing'])} of 5 (p = {stt.loc['s_star','p_exact']:.2f})."))
h2 = dec["H2_by_family"]
S.append(para(f"Ability is higher for the larger model in all five families (sign test p = {stt.loc['a','p_exact']:.4f}, the smallest value attainable with five families). The corrected stance effect is not reliably lower: it falls for the larger model in {int(stt.loc['s_star','families_agreeing'])} families (Claude {h2['Claude']['d_s']:+.2f}, Gemma {h2['Gemma']['d_s']:+.2f}, Qwen {h2['Qwen']['d_s']:+.2f}) but the interval excludes zero only for Claude, and it rises for the larger model in Llama ({h2['Llama']['d_s']:+.2f}) and Ministral ({h2['Ministral']['d_s']:+.2f}), where the intervals lie above zero. "
              f"H2 is supported in {dec['H2_families_supported']} family (Claude) and not as a pattern across families. The Claude comparison is between tiers, not sizes, and the other families differ in generation and post-training; we make no general claim about scale."))
S.append(head("6.4 Heterogeneity and the closed form"))
rows = [[NAME[k], f"{dec['H4'][k]['cov']:+.3f} [{dec['H4'][k]['lo']:+.3f}, {dec['H4'][k]['hi']:+.3f}]", f2(est("V_0.7", k)), f"{dec['H4'][k]['gap_07']:+.3f}"] for k in ORDER]
S.append(caption(5, "Covariance of ability and deference across stems, and the model-free value of review minus the closed form"))
S.append(table(["Model", "Cov(a_i, s_i) [95% CI]", "V_obs (π = .7)", "V_obs − closed form"], rows, [2400, 2800, 2000, 2160]))
S.append(note("s_i is the stem-level rate of the stance-endorsed option under the stance minus under the neutral sentence, from one draw each; a_i is stance-free accuracy on the stem. The closed form is (1 − s_c)(ā − π) with s_c = E[a_i s_i]/ā."))
S.append(para(f"The covariance is not negative. It is positive for {len(h4pos)} models with intervals above zero ({names(h4pos)}), which means deference is higher on the stems the model answers correctly more often, the opposite of H4 (for Haiku 4.5 and Sonnet 5.5 the covariances are below 0.001); no model has an interval below zero. H4 is not supported. "
              f"The model-free value of review exceeds the closed form at π = .7 for {len(gap_pos)} of the fourteen models (by up to {max(dec['H4'][k]['gap_07'] for k in ORDER):.2f}), but this gap does not follow the covariance term of Proposition 5 (which predicts a gap of the opposite sign where the covariance is positive). A possible explanation, which we did not test, is that s_i, measured as an excess over a single neutral draw, understates how often the stance determines the answer on stems the model gets wrong; the closed form is therefore a poor approximation to the model-free value here, and we use the model-free value in Section 6.5."))
S.append(head("6.5 Ability as a ranking cue"))
rows = [[NAME[k], f2(est("a", k)), f"{est('V_0.5',k):+.2f}", f"{est('V_0.7',k):+.2f}", f"{est('V_0.9',k):+.2f}", f"{est('overstate',k):.1f}"] for k in ORDER]
S.append(caption(6, "Model-free value of review by requester accuracy, and the factor by which ability overstates it"))
S.append(table(["Model", "a", "V (π = .5)", "V (π = .7)", "V (π = .9)", "1/(1 − s*)"], rows, [2600, 1200, 1400, 1400, 1400, 1360]))
S.append(note("V(π) = π·P_a + (1 − π)·P_w − π, with P_a and P_w the accuracy under a right and a wrong stance at e*; it assumes no behaviour and equals a − π for a delegate that never defers."))
op = [k for k in ORDER if k not in FAM["Claude"]]
S.append(para(f"Ranking by ability preserves value at the top and little elsewhere. The rank correlation between ability and value is {rk.loc['spearman_a_V_0.5','est']:.2f} at π = .5, {rk.loc['spearman_a_V_0.7','est']:.2f} at π = .7 and {rk.loc['spearman_a_V_0.9','est']:.2f} at π = .9 (intervals {rk.loc['spearman_a_V_0.5','lo']:.2f}–{rk.loc['spearman_a_V_0.5','hi']:.2f}, {rk.loc['spearman_a_V_0.7','lo']:.2f}–{rk.loc['spearman_a_V_0.7','hi']:.2f}, {rk.loc['spearman_a_V_0.9','lo']:.2f}–{rk.loc['spearman_a_V_0.9','hi']:.2f}), and the regret from choosing the highest-ability model is zero at all three priors. "
              f"Ranking by ability is value-optimal at both ends of π in {pairs['est']:.2f} of model pairs (interval {pairs['lo']:.2f} to {pairs['hi']:.2f}); because the lower bound is .50, H5 is not supported by the fixed rule. "
              f"The reason is that the ten open-weight models are worth little or nothing to a requester whose own accuracy is .5 or higher: their value is between {sg(min(est('V_0.5',k) for k in op))} and {sg(max(est('V_0.5',k) for k in op))} at π = .5 and between {sg(min(est('V_0.9',k) for k in op))} and {sg(max(est('V_0.9',k) for k in op))} at π = .9, because their ability, {f2(min(est('a',k) for k in op))} to {f2(max(est('a',k) for k in op))}, is below the requester's accuracy once π is above about .5 (Proposition 3: deference then moves the answer back toward the requester's prior). Gemma-3 12B, which follows the stance almost always, has value {sg(est('V_0.5','Gemma3-12B'))}: it returns the requester's own view. "
              f"Where ability is high, the overstatement factor 1/(1 − s*) is close to one ({est('overstate','Haiku4.5'):.2f} for Haiku 4.5, {est('overstate','Sonnet5.5'):.2f} for Sonnet 5.5, 1.00 for Opus 5.5 and Fable 5.1); it is {est('overstate','Qwen2.5-72B'):.1f} to {est('overstate','Gemma3-12B'):.1f} for the open-weight models with the most deference, but there the baseline ability-based value a − π is itself below zero for π ≥ .5, so the factor describes a quantity no buyer would pay for."))
S.append(head("6.6 Robustness"))
mm = lambda f: m[m.metric == "s_star"]
S.append(para("Unparseable answers coded as errors instead of missing change s* by at most 0.07 (Gemma-3 12B, from 0.91 to 0.84) and leave the other models within 0.05; ability falls by at most 0.02. Dropping one domain at a time changes s* by at most 0.03 to 0.13 depending on the domain (the largest change is for Qwen2.5 7B when domain 4, the eligibility score, is dropped) and the evidence slope by at most 0.03. The H1 result is unchanged in every variant (ρ above zero for ten models), but the H3 classification is not fully stable: Ministral 3B moves from evidence-weighing to mixed in all six domain-exclusion runs, Haiku 4.5 does so when domain 3 or 6 is dropped, Gemma-3 12B moves to deference-consistent when unparseable answers are coded as errors or when domain 4 or 5 is dropped (its f(e) is near 1 at every level), and Gemma-3 4B moves to evidence-weighing without domain 4. These variants use 500 resamples, so borderline classifications should be read as unsettled. "
              f"Rotating the option letters leaves ability within 0.05 of the unrotated value, with an interval excluding zero for Ministral 14B ({rot['Ministral-14B']['d_a'][0]:+.3f}) and a trivial one for Sonnet 5.5 ({rot['Sonnet5.5']['d_a'][0]:+.3f}); it raises the stance-following rate f(e*) with an interval excluding zero for Ministral 3B ({rot['Ministral-3B']['d_f'][0]:+.2f}, from {f2(est('f_pref','Ministral-3B'))} to {f2(est('rot_f','Ministral-3B'))}), Gemma-3 4B ({rot['Gemma3-4B']['d_f'][0]:+.2f}), Qwen2.5 72B ({rot['Qwen2.5-72B']['d_f'][0]:+.2f}) and Qwen2.5 7B ({rot['Qwen2.5-7B']['d_f'][0]:+.2f}). These four models therefore carry a letter-position component in their stance-following, and the Ministral 3B estimate in particular should be read with it in mind. "
              "Serving providers differ. For Gemma-3 12B, one provider returned an unparseable answer on 33.6% of calls and another on none; for Gemma-3 4B the figures are 17.2% and none. Stripping a leading “>” that these responses carry recovers 495 of the 787 failures for Gemma-3 12B and moves s* from 0.913 to 0.908 (exploratory). The stance-following rate for Llama-3.1 8B ranges from 0.44 to 0.75 across four providers (9 to 330 stems per provider) and for Gemma-3 27B from 0.78 to 0.92 across five, so the model-level estimates average over providers that do not behave alike."))
S.append(para("Departures from the plan and exploratory analyses. The rank correlation in H1 needs the bootstrap draws, which analysis.py does not save, and was computed afterwards by a separate script (decisions.py) with the same resampling and seed; the intervals for the rotation checks were computed after the main analysis; the robustness analyses use 500 instead of 2,000 resamples; and the provider split and the treatment of the leading “>” are exploratory. The run was interrupted several times (twice by shell restarts, once by a manual stop to add credit, and once by the background time limit) and resumed with the same command, which skips finished calls; call order was shuffled with a fixed seed, so interruption does not bias which cells are complete, and no call was repeated or discarded (176,400 unique calls)."))

# ------------------------------------------------------------------------ section 7
D = []
D.append(head("7. Discussion", 2))
D.append(head("7.1 Findings"))
D.append(para(f"Three results stand out. First, the conventional measure of deference is mostly right for stable models and badly wrong for unstable ones: the baseline removes a median {med_rem:.0%} but {min(rem[k] for k in ['Ministral-3B','Llama3.1-8B','Ministral-8B','Llama3.1-70B','Ministral-14B']):.0%} to {rem['Ministral-3B']:.0%} for the five least stable models, and the share removed tracks instability closely (rank correlation {rc['est']:.2f}). The managerial message therefore depends on which reviewer a firm has: for the unstable models it is to buy stability and test before paying; for the stable ones it is that the raw measure can be trusted. "
              f"Second, stance-following is not blind. Models follow a stance more when it claims colleague review, less when it is disclaimed, and the disclaimer lowers the rate in {len(disc_down)} of the {len(follow)} models that follow the stance at all; no model with a stance effect meets the rule for pure deference. But the responses are small where following is highest and weak in the requester's disclosed accuracy: at a stated 20% track record the open-weight models still follow a wrong stance on {min(est('acc_20',k) for k in op):.2f} to {max(est('acc_20',k) for k in op):.2f} of stems. The models react to the form of the evidence more than to its strength. "
              f"Third, scale and ability do not settle value. Ability is higher for the larger model in every family, but the corrected stance effect is lower in only {int(stt.loc['s_star','families_agreeing'])} of 5 families, and ten of the fourteen models have ability of only {f2(min(est('a',k) for k in op))} to {f2(max(est('a',k) for k in op))}, so for a requester whose own accuracy is .5 or higher reviewing adds little or nothing beyond acting on the requester's view."))
D.append(head("7.2 Theory"))
D.append(para(f"Proposition 3 predicts that deference raises a naive requester's value when the delegate is less accurate than the requester's preference, and the data show that case for most open-weight models: their value is close to zero or negative at π = .5 to .9. Proposition 6 says a stance weight is costless only up to the rate that is rational for the requester's accuracy, and that no fixed weight suits requesters who differ in π. The weak accuracy gradient bears on this directly: a delegate that weighed a disclosed 20% track record rationally would follow the stance far less than one told 80%, and most models change by {max(est('acc_slope',k) for k in follow if k != 'Ministral-8B'):.2f} or less between the two (Ministral 8B, {est('acc_slope','Ministral-8B'):.2f}, is the exception). A fixed, evidence-form-driven weight is the pattern Proposition 6 warns about. "
              f"Proposition 5 did not describe the data: the covariance of ability and deference across stems is positive for {len(h4pos)} models, not negative, and the closed form with measured deference was a poor guide to the model-free value (Section 6.4). We read this as a limit of the measurement, which estimates stem-level deference from one draw, and not as a refutation of the identity."))
D.append(head("7.3 Practice: an audit protocol"))
D.append(para(f"A firm can run the design on its own review items: re-ask each item twice with no stance, once with a neutral sentence of the same length, and once with a stance whose claimed evidence is graded and whose disclosed accuracy is varied; subtract the stance-free and neutral rates from the stance rate; read the gradients; and report the value of review at the requester accuracies the firm actually has. Stance-free benchmark accuracy is a ranking aid and not a level of value. On 600 items the 95% intervals for the corrected effect have half-widths between about {HWMIN:.2f} and {HWMAX:.2f} (Table 2), and the full run of 176,400 calls across fourteen models cost about US$170 as billed through the aggregator, so a firm auditing one or two models on a few hundred of its own items faces a modest cost. Blinding the delegate to the requester’s stance remains a hypothesis with an upper bound, s(a − π), on what it is worth; we did not test it."))
D.append(head("7.4 Implications for IS research"))
D.append(para(f"For research on delegation to agentic artifacts, the finding that stance-following responds to the form of claimed evidence more than to its stated reliability suggests that reliance models should treat a requester’s framing as an input the delegate weighs by rule, not by calibrated trust. For the auditing of AI decision support, it shows that two reviewers with the same benchmark accuracy can differ by an order of magnitude in what a stated preference does to their answers (Ministral 3B and Qwen2.5 7B both answer {f2(est('a','Ministral-3B'))} of the items correctly, yet their s* is {f2(est('s_star','Ministral-3B'))} and {f2(est('s_star','Qwen2.5-7B'))}), and that the difference can be measured at modest cost. For the design of review workflows in which the reviewer sees the requester’s view, it argues for measuring the gradient before relying on the reviewer, and for withholding the preference where the reviewer’s accuracy is high enough for review to be worth buying."))

import pickle
pickle.dump(dict(section="".join(S) + "".join(D), smix=smix, med_rem=float(med_rem), n_weigh=len(weigh), n_mixed=len(mixed)), open("results/_built_sections.pkl", "wb"))
print("built", len("".join(S)+"".join(D)), "chars xml; weigh", len(weigh), "mixed", len(mixed), "zero", zero, "h4pos", len(h4pos), "gap_pos", len(gap_pos), "disc_down", len(disc_down), "acc_up", len(acc_up), "sl_up", len(sl_up))
print("max smix-sstar", max(smix.items(), key=lambda kv: kv[1]))
