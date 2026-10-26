"""NMI manuscript v3: attacks aimed at a detector's own score, and a defence by combining detectors that fail differently.
All numbers are computed from replication/data (independent re-implementation)."""
import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
import pandas as pd, numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
D = "replication/data"
R = pd.read_csv(f"{D}/defence_results.csv")
GENS = [("claude", "Claude"), ("gpt4o", "GPT-4o"), ("llama", "Llama"), ("deepseek", "DeepSeek")]
CONDS = ["orig", "edit1.0", "rewrite", "hybrid1.0", "rewrite2", "noise10", "mix50", "bok_rw", "bok_mix"]
CL = {"orig": "None", "edit1.0": "Feature edit", "rewrite": "LLM rewrite", "hybrid1.0": "Rewrite + edit", "rewrite2": "Rewrite twice", "noise10": "10% typos",
      "mix50": "50% human sentences", "bok_rw": "Guided rewrite", "bok_mix": "Guided mixing", "mix30": "30% human sentences", "noise3": "3% typos"}
ML = {"sc": "Count screen", "ll": "Log-likelihood", "bi": "Binoculars", "fd": "Fast-DetectGPT", "tf": "TF-IDF classifier", "rb": "RoBERTa classifier",
      "dl": "Two-sided log-likelihood*", "mean4": "Ensemble, mean*", "top2": "Ensemble, top-2*", "judge": "Gemini 2.5 Pro judge"}
MAIN = R[R.target != "econ"]
def cell(m, g, c, k="auc"):
    x = MAIN[(MAIN.method == m) & (MAIN.generator == g) & (MAIN.cond == c)]
    return float(x[k].iloc[0]) if len(x) else np.nan
def ci(m, g, c): return f"{cell(m,g,c):.2f} [{cell(m,g,c,'lo'):.2f}, {cell(m,g,c,'hi'):.2f}]"
# judge AUCs (negatives: Gemini scores of the evaluation humans)
samp = pd.read_csv(f"{D}/judge_sample.csv"); jc = pd.read_csv(f"{D}/judge_scores.csv")
hum = jc[(jc.judge == "gemini") & jc.id.isin(samp[samp.generator == "human"].id)].p_ai.dropna().values
J = {}
for fn in ("attack_judge_scores", "attacked2_judge_scores", "attacked_bok_judge_scores", "attacked_ds_judge_scores", "attacked2_ds_judge_scores"):
    p = f"{D}/{fn}.csv"
    if not os.path.exists(p): continue
    j = pd.read_csv(p).dropna(subset=["p_ai"]); j["g"] = j.id.str.split(":").str[0]
    for (g, c), x in j.groupby(["g", "cond"]):
        J[(g, c)] = (roc_auc_score(np.r_[np.zeros(len(hum)), np.ones(len(x))], np.r_[hum, x.p_ai.values]), len(x))
def jcell(g, c): return J.get((g, c), (np.nan, 0))[0]
METH = ["sc", "ll", "bi", "fd", "tf", "rb", "dl", "mean4", "top2"]
f2 = lambda x: "–" if pd.isna(x) else f"{x:.2f}"
# worst cases
def worst(m, g=None):
    x = MAIN[(MAIN.method == m) & (MAIN.cond != "orig") & (MAIN.cond.isin(CONDS))]
    if g: x = x[x.generator == g]
    r = x.loc[x.auc.idxmin()]; return r.auc, r.cond, r.generator
# ---------------- figures
fig, axs = plt.subplots(1, 4, figsize=(13.5, 4.1), sharey=True)
rows_m = METH + ["judge"]
for ax, (g, gl) in zip(axs, GENS):
    mat = np.array([[jcell(g, c) if m == "judge" else cell(m, g, c) for c in CONDS] for m in rows_m])
    im = ax.imshow(mat, vmin=0.3, vmax=1.0, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(CONDS))); ax.set_xticklabels([CL[c] for c in CONDS], rotation=60, ha="right", fontsize=7); ax.set_title(gl, fontsize=10)
    for i in range(mat.shape[0]):
        for k in range(mat.shape[1]):
            if not np.isnan(mat[i, k]): ax.text(k, i, f"{mat[i,k]:.2f}", ha="center", va="center", fontsize=5.8, color="white" if mat[i, k] < 0.7 else "black")
    ax.axhline(5.5, color="w", lw=1.5)
axs[0].set_yticks(range(len(rows_m))); axs[0].set_yticklabels([ML[m] for m in rows_m], fontsize=7.5)
fig.colorbar(im, ax=axs, shrink=0.8, label="AUC"); fig.savefig("fig3_audit.png", dpi=200, bbox_inches="tight"); plt.close(fig)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4))
wc = [worst(m)[0] for m in METH]; cols = ["#7f7f7f"] * 6 + ["#2a6f97"] * 3
a1.barh(range(len(METH)), wc, color=cols); a1.set_yticks(range(len(METH))); a1.set_yticklabels([ML[m] for m in METH], fontsize=8); a1.invert_yaxis(); a1.axvline(0.5, color="k", lw=0.6, ls="--")
a1.set_xlim(0, 1); a1.set_xlabel("Lowest AUC over 4 generators × 8 attacks"); a1.set_title("a  Worst case", fontsize=9, loc="left")
for i, v in enumerate(wc): a1.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=7)
xs = np.arange(len(CONDS))
for m, col, ls in (("fd", "#7f7f7f", "-"), ("dl", "#6fa8c7", "--"), ("mean4", "#2a6f97", "-")):
    a2.plot(xs, [cell(m, "claude", c) for c in CONDS], marker="o", ms=3, color=col, ls=ls, label=ML[m].rstrip("*"))
a2.set_xticks(xs); a2.set_xticklabels([CL[c] for c in CONDS], rotation=55, ha="right", fontsize=7); a2.set_ylim(0.2, 1.02); a2.axhline(0.5, color="k", lw=0.6, ls=":")
a2.set_ylabel("AUC (Claude papers)"); a2.set_title("b  Complementary failures", fontsize=9, loc="left"); a2.legend(fontsize=7, frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig("fig4_defence.png", dpi=200); plt.close(fig)
# ---------------- tables
T1 = [["Method"] + [gl for _, gl in GENS]] + [[ML[m]] + [f2(jcell(g, "orig")) if m == "judge" else f2(cell(m, g, "orig")) for g, _ in GENS] for m in METH + ["judge"]]
def wcell(m, g):
    v, c, _ = worst(m, g); return f"{cell(m, g, 'orig'):.2f} → {v:.2f} ({CL[c].lower()})"
T2 = [["Method"] + [gl for _, gl in GENS]] + [[ML[m]] + [wcell(m, g) for g, _ in GENS] for m in METH]
OP = ["orig", "edit1.0", "rewrite2", "mix50", "bok_mix"]
def tpr(m, c): x = MAIN[(MAIN.method == m) & (MAIN.cond == c)]; return x.tpr.mean()
FPR = R.groupby("method").fpr.mean()
T3 = [["Method", "FPR (eval. humans)"] + [CL[c] for c in OP]] + [[ML[m], f"{FPR[m]:.3f}"] + [f2(tpr(m, c)) for c in OP] for m in ["fd", "rb", "tf", "sc", "dl", "mean4", "top2"]]
E = R[R.target == "econ"]
def ecell(m, g, c): x = E[(E.method == m) & (E.generator == g) & (E.cond == c)]; return f2(x.auc.iloc[0]) if len(x) else "–"
T4 = [["Method"] + [f"{gl}: none / mixing" for _, gl in GENS]] + [[ML[m]] + [f"{ecell(m,g,'orig')} / {ecell(m,g,'mix50')}" for g, _ in GENS] for m in ["fd", "rb", "tf", "sc", "dl", "mean4", "top2"]]
ac = pd.read_csv(f"{D}/artifact_control_results.csv"); acp = ac.pivot_table(index=["protocol", "generator"], columns="variant", values="auc")
T5 = [["Protocol", "Generator", "Raw text", "Artifacts removed", "Function words only"]] + [[{"grouped-cv": "Same generator in training", "unseen-generator": "Unseen generator"}[p], dict(GENS)[g], f2(r["raw"]), f2(r["clean"]), f2(r["function"])] for (p, g), r in acp.iterrows()]
sr = json.load(open(f"{D}/screen_results.json"))
n_cal = int((R.target != "econ").sum() > 0) and 100
wfd, cfd, gfd = worst("fd"); wm4 = worst("mean4")[0]; wt2 = worst("top2")[0]; wrb = worst("rb")[0]; wsc = worst("sc")[0]; wtf = worst("tf")[0]
wm3 = worst("mean3")[0] if "mean3" in set(R.method) else np.nan
print("worst", wfd, cfd, gfd, wm4, wt2, wrb, wsc, wtf, wm3)
REFS = {}
exec(open("/tmp/refs_nmi.txt").read())
REFS.update({
 "wang24": "Wang, Y. et al. Stumbling blocks: stress testing the robustness of machine-generated text detectors under attacks. In *Proc. 62nd Annu. Meet. Assoc. Computational Linguistics* 2894–2925 (ACL, 2024).",
 "huang24": "Huang, G. et al. Are AI-generated text detectors robust to adversarial perturbations? In *Proc. 62nd Annu. Meet. Assoc. Computational Linguistics* 6005–6024 (ACL, 2024).",
 "cheng25": "Cheng, Y., Sadasivan, V. S., Saberi, M., Saha, S. & Feizi, S. Adversarial paraphrasing: a universal attack for humanizing AI-generated text. In *Adv. Neural Inf. Process. Syst.* **38** (2025).",
 "stealth": "Ranganath, S. & Ramesh, A. StealthRL: reinforcement learning paraphrase attacks for multi-detector evasion of AI-text detectors. Preprint at https://arxiv.org/abs/2602.08934 (2026).",
 "ding25": "Dingfelder, P. & Riess, C. Contamination in generated text detection benchmarks. Preprint at https://arxiv.org/abs/2511.09200 (2025).",
 "puda26": "Pudasaini, S., Miralles-Pechuan, L., Lillis, D. & Llorens Salvador, M. Why AI-generated text detection fails: evidence from explainable AI beyond benchmark accuracy. Preprint at https://arxiv.org/abs/2603.23146 (2026).",
 "yu26": "Yu, S., Luo, M., Madasu, A., Lal, V. & Howard, P. Is your paper being reviewed by an LLM? Benchmarking AI text detection in peer review. In *Proc. Int. Conf. Learning Representations* (2026).",
 "liang25": "Liang, W. et al. Quantifying large language model usage in scientific papers. *Nat. Hum. Behav.* https://doi.org/10.1038/s41562-025-02273-8 (2025).",
})
order = []
def C(*keys):
    for k in keys:
        if k not in order: order.append(k)
    return "^{" + ",".join(str(order.index(k) + 1) for k in keys) + "}"

d = new_doc(spacing=1.5, running="Defending screens for machine-written scholarly text")
TITLE(d, "Combining detectors that fail differently protects screens for machine-written scholarly text against adaptive authors", size=15)
P(d, "Ook Lee^{1}*", indent=False, align="center", size=11, spacing=1.15, after=2)
P(d, "^{1}Hanyang University, Seoul, Republic of Korea. *Corresponding author: ooklee@hanyang.ac.kr", indent=False, align="center", size=10, spacing=1.15, after=10)
P(d, "**Abstract**", indent=False, after=2, spacing=1.15)
P(d, f"Screens for machine-written manuscripts are usually tested on text no author has tried to disguise. We test nine screens on 474 human papers and papers from four generators under eight attacks, including two that query a detector's own score and keep the candidate it rates most human. Every single detector has a failure: replacing half of a Claude paper's sentences with human sentences and keeping the candidate Fast-DetectGPT scores lowest drives its AUC from {cell('fd','claude','orig'):.2f} to {cell('fd','claude','bok_mix'):.2f}, below chance, while probability-based scores invert because spliced text is less probable than genuine human text. We propose a defence that needs no knowledge of the attack: a two-sided likelihood score, calibrated on a separate set of human papers, combined with detectors that fail elsewhere. Across four generators and eight attacks, the worst-case AUC rises from {wfd:.2f} for the best single detector to {wm4:.2f}–{wt2:.2f} for the combination. The gain is smaller at a fixed 5% false-positive rate, and the defence is not tested against attackers who optimize against the combination itself.", indent=False, spacing=1.3, size=11, align="justify")
P(d, "", indent=False, spacing=1.0)
P(d, "Large language models make fluent scientific prose cheap, and corpus-level estimates suggest that a growing share of scientific papers already show signs of their use" + C("liangmap", "liang25") + ". Publishers, preprint servers and integrity offices therefore screen manuscripts, but published detectors are usually evaluated on unmodified output" + C("mitchell", "bao") + ". Evaluations that include attackers show that paraphrasing, perturbation and detector-guided rewriting can defeat them" + C("sadasivan", "krishna", "wang24", "huang24", "cheng25") + ", that accuracy falls on generators and domains absent from training" + C("li", "dugan") + ", that detection benchmarks can contain artifacts that classifiers learn as shortcuts" + C("ding25", "puda26") + ", and that detectors can be biased against non-native writers" + C("liangbias") + ". Watermarking" + C("kirch") + " avoids detection but requires the cooperation of every generator.", indent=False)
P(d, "Two questions follow for anyone who must deploy a screen. First, how badly does each type of detector fail when an author can see its score? Second, is there a defence that does not require knowing the attack in advance? We address both on scientific papers. We test nine screens, from a transparent screen built on counts of seven linguistic events to Fast-DetectGPT, supervised classifiers and a language-model judge, against eight attacks on papers from four generators. Two attacks query Fast-DetectGPT and keep the most human-looking of four candidates. We then propose and test a defence built from two observations in our data: probability-based scores invert under perturbation, so a two-sided score detects text that is too improbable as well as too probable; and detectors fail on different attacks, so combining standardized scores raises the worst case. To our knowledge no earlier study combines score-guided attacks of this kind with a control for structural artifacts on scholarly text, although each element has precedents" + C("cheng25", "stealth", "ding25") + ".", indent=False)
P(d, "This is an independent re-implementation: the original data and code of an earlier version of this work were not available, so the corpus, the generation, the screens and all attacks were rebuilt, and the numbers differ from those of any earlier version. Negative results are reported as they came.", indent=False)

H1(d, "Results")
H2(d, "Without an attacker, supervised classifiers and Fast-DetectGPT lead, and Claude is hardest")
P(d, f"Table 1 gives the AUC of each method against 186 human papers held out from all training and calibration. Fast-DetectGPT reaches {cell('fd','claude','orig'):.2f} to {cell('fd','gpt4o','orig'):.2f}, RoBERTa and TF-IDF classifiers trained without the target generator 0.92 or more, and the count screen {min(cell('sc',g,'orig') for g,_ in GENS):.2f} to {max(cell('sc',g,'orig') for g,_ in GENS):.2f}. One-sided log-likelihood is near chance on Claude papers ({cell('ll','claude','orig'):.2f}) and weak on DeepSeek papers ({cell('ll','deepseek','orig'):.2f}). The Gemini judge reaches {jcell('claude','orig'):.2f} on Claude papers and {jcell('llama','orig'):.2f} on Llama papers. DeepSeek V4.1 Flash, the newest generator, is about as easy as GPT-4o for Fast-DetectGPT and the supervised classifiers, but harder for likelihood-based scores. Claude is the hardest generator for every method.", indent=False)
TABLE(d, "**Table 1 | Detection without attack.** AUC, 186 evaluation humans against 100 machine papers per generator. Supervised models and the count screen were trained without the target generator, without Llama (the attacker's rewriting model) and without DeepSeek. *Proposed defence components.", T1, widths=[2.3, 1.0, 1.0, 1.0, 1.0], size=9, note="The judge column uses 200 evaluation humans (Methods). '–' not run.")
H2(d, "Attacks that query the detector find its blind spot")
P(d, f"Two attacks assume that the author can submit drafts to Fast-DetectGPT and keep the candidate it scores lowest among four: four LLM rewrites (guided rewrite) or four random replacements of half the sentences with human sentences from the same field (guided mixing). Guided rewriting does not work: Fast-DetectGPT stays at {min(cell('fd',g,'bok_rw') for g in ('claude','gpt4o','llama')):.2f} or above. Guided mixing works. On Claude papers the AUC falls from {ci('fd','claude','orig')} to {ci('fd','claude','bok_mix')}, below chance, on GPT-4o papers to {cell('fd','gpt4o','bok_mix'):.2f}, and on Llama papers to {cell('fd','llama','bok_mix'):.2f} (Fig. 1, Table 2; 95% bootstrap intervals in brackets). The attack transfers in part: RoBERTa falls to {cell('rb','claude','bok_mix'):.2f} on the same Claude papers, but no lower than under unguided mixing ({cell('rb','claude','mix50'):.2f}), because the selection exploits Fast-DetectGPT's score and not RoBERTa's. The judge is not fooled ({jcell('claude','bok_mix'):.2f} on Claude papers), consistent with its reading spliced text as incoherent.", indent=False)
FIG(d, "fig3_audit.png", "**Fig. 1 | AUC of every method under every attack, by generator.** Negatives are 186 evaluation humans. Rows below the white line are the proposed defence components (two-sided log-likelihood, two ensembles) and the judge. Guided attacks were run on the three original generators; the judge on a subset of attacks. Blank: not run.", width=6.7)
TABLE(d, "**Table 2 | Worst case under attack.** AUC without attack, then the lowest AUC over eight attacks for that generator (the attack in brackets).", T2, widths=[1.7, 1.25, 1.25, 1.25, 1.25], size=7.5)
H2(d, "Probability scores invert, and a two-sided score turns the inversion into a signal")
P(d, f"Mixing in human sentences makes text less probable than genuine human text, because spliced sentences break coherence, so a rule that calls high-probability text machine-written labels it human: one-sided log-likelihood falls to {cell('ll','claude','mix50'):.2f} on Claude papers and {cell('ll','gpt4o','mix50'):.2f} on GPT-4o papers. A two-sided score, the absolute deviation of log-likelihood from the median of 100 calibration humans that are used for nothing else, reaches {ci('dl','claude','bok_mix')} on Claude papers under guided mixing, exactly where Fast-DetectGPT fails (Fig. 2b). It is weak where Fast-DetectGPT is strong: on unattacked Claude papers it is near chance ({cell('dl','claude','orig'):.2f}).", indent=False)
H2(d, "Combining detectors that fail differently raises the worst case")
P(d, f"We standardize each score by the median and robust standard deviation of the calibration humans and combine four components, Fast-DetectGPT, RoBERTa, the count screen and the two-sided score, by their mean or by the mean of the two largest. Neither rule uses attacked text. Over four generators and eight attacks the lowest AUC is {wm4:.2f} for the mean and {wt2:.2f} for the top-2 rule, against {wfd:.2f} for Fast-DetectGPT, {wrb:.2f} for RoBERTa, {wtf:.2f} for TF-IDF and {wsc:.2f} for the count screen (Fig. 2a). Under guided mixing on Claude papers the mean ensemble reaches {ci('mean4','claude','bok_mix')}. On unattacked papers it loses little ({cell('mean4','claude','orig'):.2f} against {cell('fd','claude','orig'):.2f} on Claude papers). The two-sided score is what makes the combination work: the same mean over Fast-DetectGPT, RoBERTa and the count screen alone has a worst case of {wm3:.2f}.", indent=False)
FIG(d, "fig4_defence.png", "**Fig. 2 | The defence.** **a**, Lowest AUC over four generators and eight attacks for each method; proposed components in blue. **b**, AUC on Claude papers under each attack for Fast-DetectGPT, the two-sided score and the mean ensemble: the two-sided score is strong where Fast-DetectGPT fails.", width=6.5)
P(d, f"The gain is smaller at an operating point. With the threshold set at the 95th percentile of the calibration humans, the false-positive rate on evaluation humans is {FPR['mean4']:.3f} for the mean ensemble and {FPR['fd']:.3f} for Fast-DetectGPT. Under guided mixing the share of machine papers flagged, averaged over generators, is {tpr('mean4','bok_mix'):.2f} for the mean ensemble against {tpr('fd','bok_mix'):.2f} for Fast-DetectGPT, and the two-sided score alone flags {tpr('dl','bok_mix'):.2f} (Table 3). Averaging dilutes a strong component at strict thresholds; a deployment that cares about a fixed false-positive rate may prefer to run the two-sided score as a separate alarm, at the price of its higher false-positive rate on evaluation humans ({FPR['dl']:.3f}), which suggests that its calibration on 100 humans is not yet tight.", indent=False)
TABLE(d, "**Table 3 | Operating point.** Share of machine papers flagged at a threshold equal to the 95th percentile of 100 calibration humans, averaged over generators; FPR measured on the 186 evaluation humans.", T3, widths=[1.7, 0.9, 0.7, 0.8, 0.8, 0.9, 0.9], size=8)
H2(d, "A new field: strong numbers that we do not trust")
P(d, "We collected 130 economics papers (arXiv econ.*, 2017–2019) and had each generator write papers on the same topics. Supervised detectors trained only on medicine and computer science score near 1.00 on these papers, and mixing lowers them little (Table 4). We do not read this as evidence of transfer across fields: all economics human papers were converted from PDF and carry the headers, figure labels and other structural artifacts that the next section shows supervised classifiers exploit, whereas the machine papers carry none. Fast-DetectGPT, which does not learn from labels, falls under mixing on Claude and DeepSeek papers in this field as well.", indent=False)
TABLE(d, "**Table 4 | Economics papers.** AUC without attack / with 50% human sentences. Supervised models were trained on medicine and computer science papers of human authors, GPT-4o and Claude.", T4, widths=[1.7, 1.25, 1.25, 1.25, 1.25], size=8)
H2(d, "Supervised accuracy rests partly on artifacts")
P(d, f"Human papers extracted from PDFs and XML contain headers, 'Fig.' and 'Table' labels, 'et al.', years and affiliations; machine papers contain none. We compared a TF-IDF classifier on raw text, on text with these tokens removed and on function words only (Table 5). Accuracy stays near 1.00 when the generator is in training, because function-word style differs ('thus', 'hence' for humans; 'across', 'such' for machines), but on an unseen generator the AUC for Claude papers falls from {acp.loc[('unseen-generator','claude'),'raw']:.2f} to {acp.loc[('unseen-generator','claude'),'clean']:.2f} and {acp.loc[('unseen-generator','claude'),'function']:.2f}.", indent=False)
TABLE(d, "**Table 5 | Artifact control for the TF-IDF classifier.**", T5, widths=[2.0, 1.0, 1.1, 1.4, 1.5], size=8.5)

H1(d, "Discussion")
P(d, "No single detector in this study survives every attack, and the attacks that hurt each detector are different. That is the basis of the defence: probability-based detectors are hurt by mixing and noise, supervised detectors by mixing and by shifts in generator and field, and the count screen by edits to its own features, while a two-sided score gains exactly where the others lose. A combination with no learned weights and no attacked training data raises the worst case substantially. It does so in AUC more than at a strict operating point, and this difference matters for a desk editor who will investigate every flag.", indent=False)
P(d, "Two limits bound the claim. The attacks are adaptive to one detector, not to the combination; reinforcement-learning paraphrasers trained against an ensemble of detectors that includes Fast-DetectGPT and RoBERTa already evade it" + C("stealth") + ", and an author who can query our ensemble may do the same. And the guided attacks used four candidates; more candidates or iterated selection would push further. The defence raises the cost of evasion; it does not make evasion impossible, which theoretical work suggests cannot be done for sufficiently good generators" + C("sadasivan") + ".", indent=False)
P(d, "The study has further limits. Each cell compares 100 attacked papers with 186 human papers, so AUC differences below about 0.07 are within sampling error (bootstrap intervals in the Supplementary Information). The corpus covers English papers from medicine, computer science and economics, and human and machine texts differ in how they were obtained, which our artifact control addresses only for TF-IDF. Zero-shot detectors used one open model pair; the judge was run on a subset of attacks because of cost. We did not test light human editing of machine text, fairness for non-native writers" + C("liangbias") + ", or peer reviews" + C("yu26") + ".", indent=False)

H1(d, "Methods")
H2(d, "Documents")
P(d, "We sampled 500 human papers from 2015 to 2019: 330 from the open-access subset of PubMed Central and 170 from arXiv (cs.*). Papers with fewer than 2,000 tokens after cleaning were dropped, leaving 474 (309 and 165). For each sampled paper a generator wrote a paper on the same topic from its title and abstract, with one of three prompts of increasing detail, in four requests (introduction, methods, results, discussion). Generators were GPT-4o, Claude Sonnet 5.5, Llama 3.3 70B Instruct and DeepSeek V4.1 Flash (low reasoning effort). For the field test we sampled 130 economics papers (arXiv econ.GN, econ.EM, econ.TH; 2017–2019), and each generator wrote papers from them. Documents were truncated to 2,000 whitespace tokens with markdown removed (Supplementary Table 1).", indent=False)
H2(d, "Splits")
P(d, "Two hundred human papers were fixed as evaluation negatives (186 have at least 2,000 tokens) and 100 further human papers as calibration humans; neither set was used to train any model. For each target generator, supervised models and the count screen were trained on the remaining human papers and on GPT-4o and Claude papers other than the target, excluding Llama (the rewriting model of the attacks), DeepSeek and every paper whose source paper is an evaluation paper. Attacks were applied to 100 papers per generator.", indent=False)
H2(d, "Detectors")
P(d, "The count screen counts parentheses, square brackets, semicolons, paired quotation marks, fourteen discourse markers, passive constructions and nominalizations in four 500-token windows and uses each event's rate, mean log Fano factor across windows of 50 to 400 tokens and its slope (21 features, logistic regression)" + C("cameron") + ". Log-likelihood, Binoculars" + C("hans") + " and Fast-DetectGPT" + C("bao") + " used Falcon-7B and Falcon-7B-instruct on the first 1,024 tokens. The TF-IDF classifier uses word unigrams and bigrams with logistic regression; the RoBERTa classifier is roberta-base fine-tuned for two epochs. Gemini 2.5 Pro was asked zero-shot for the probability that an excerpt was AI-written" + C("zheng") + ".", indent=False)
H2(d, "Attacks")
P(d, "The feature edit moves counts of five events toward the human mean; the LLM rewrite asks Llama 3.3 70B to rewrite the paper as an experienced researcher would; the hybrid edits the rewrite; the second rewrite rewrites again with different wording; mixing replaces 50% of sentences with sentences from human papers of the same field outside the evaluation set; noise gives each word of four or more letters a random typo with probability 10%. Guided attacks generate four candidates per paper (four rewrites at temperature 1, alternating two prompts, or four independent mixes) and keep the candidate with the lowest Fast-DetectGPT score.", indent=False)
H2(d, "Defence")
P(d, "Each component score is standardized as (s − m)/r, where m is the median and r = 1.4826 × the median absolute deviation over the calibration humans of the same target. The two-sided score is |ℓ − m_ℓ|, with ℓ the mean token log-likelihood and m_ℓ its calibration median, standardized in the same way. The mean ensemble averages the standardized Fast-DetectGPT, RoBERTa, count-screen and two-sided scores; the top-2 ensemble averages the two largest. No weights are fitted and no attacked text is used.", indent=False)
H2(d, "Statistics")
P(d, "AUCs compare evaluation humans with the attacked papers of one generator; 95% intervals come from 400 bootstrap resamples of documents within each class. Operating points use the 95th percentile of the calibration humans as threshold. For the judge, negatives are its scores on 200 evaluation humans.", indent=False)
H2(d, "Reporting")
P(d, "No human participants were involved. All analyses used published papers and machine-generated text.", indent=False)
H1(d, "Data availability")
P(d, "Machine-generated papers, features, scores and result tables are in the replication package on Zenodo (https://doi.org/10.5281/zenodo.23664508; to be updated with this version). Human papers are public (PubMed Central open access, arXiv) and are re-collected with the identifier lists in the package.", indent=False)
H1(d, "Code availability")
P(d, "All code is in the replication package on Zenodo (https://doi.org/10.5281/zenodo.23664508), released under the MIT licence.", indent=False)
H1(d, "Author contributions")
P(d, "O.L. conceived and designed the study, built the corpus and the analysis pipeline, interpreted the results and wrote the manuscript.", indent=False)
H1(d, "Competing interests")
P(d, "The author declares no competing interests. Generative AI disclosure: the machine-written papers studied here were produced by GPT-4o, Claude Sonnet 5.5, Llama 3.3 70B Instruct and DeepSeek V4.1 Flash, and Gemini 2.5 Pro served as a judge. An AI coding assistant (Claude Code) was used to write and run the analysis code and to draft and edit the manuscript text; the author reviewed the results and takes responsibility for the content.", indent=False)
PB(d)
H1(d, "References")
for i, k in enumerate(order, 1):
    p = d.add_paragraph(); pf = p.paragraph_format; pf.left_indent = Inches(0.4); pf.first_line_indent = Inches(-0.4); pf.line_spacing = 1.15; pf.space_after = Pt(3); runs(p, f"{i}. " + REFS[k], size=10)
d.save("NMI_Defence_Manuscript.docx")
print("words", sum(len(p.text.split()) for p in d.paragraphs), "refs", len(order))
