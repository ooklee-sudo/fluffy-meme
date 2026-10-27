"""Supplementary Information for the defence manuscript (v3). All numbers from replication/data."""
import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build"); sys.path.insert(0, "replication")
from docbuild import *
import pandas as pd, numpy as np, json
from sklearn.metrics import roc_auc_score
from s7_attacks import REWRITE
from s9_adaptive import R2
from s5_judges import PROMPT
D = "replication/data"
R = pd.read_csv(f"{D}/defence_results.csv")
GENS = [("claude", "Claude"), ("gpt4o", "GPT-4o"), ("llama", "Llama"), ("deepseek", "DeepSeek")]
CONDS = ["orig", "edit0.25", "edit0.5", "edit0.75", "edit1.0", "rewrite", "hybrid0.5", "hybrid1.0", "rewrite2", "noise3", "noise10", "mix30", "mix50", "bok_rw", "bok_mix"]
CL = {"orig": "none", "edit0.25": "edit e=0.25", "edit0.5": "edit e=0.5", "edit0.75": "edit e=0.75", "edit1.0": "edit e=1", "rewrite": "LLM rewrite", "hybrid0.5": "rewrite+edit 0.5",
      "hybrid1.0": "rewrite+edit 1", "rewrite2": "rewrite twice", "noise3": "3% typos", "noise10": "10% typos", "mix30": "30% human sent.", "mix50": "50% human sent.", "bok_rw": "guided rewrite", "bok_mix": "guided mixing"}
SH = {"sc": "Count", "ll": "LogLik", "bi": "Binoc.", "fd": "FDGPT", "tf": "TF-IDF", "rb": "RoBRT", "dl": "2-sided*", "de": "2-s. ent.", "mean3": "Mean3", "mean4": "Mean4*", "top2": "Top2*"}
f2 = lambda x: "–" if pd.isna(x) else f"{x:.2f}"
d = new_doc(spacing=1.15, running="Supplementary Information")
TITLE(d, "Supplementary Material", size=15)
P(d, "Combining Detectors That Fail Differently Defends Screens for Machine-Written Scholarly Text Against Adaptive Authors  ·  Ook Lee", indent=False, align="center", size=10, italic=True, after=10)
P(d, "Contents: 1 Corpus · 2 Full AUC tables · 3 Bootstrap intervals · 4 Operating points · 5 Judge · 6 Economics papers · 7 Guided attacks · 8 Count screen transfer · 9 Prompts and procedures. *Proposed defence components. Abbreviations: RoBRT = RoBERTa classifier; Count = count screen (clustering features); LogLik = one-sided log-likelihood; Binoc. = Binoculars; FDGPT = Fast-DetectGPT; 2-sided = two-sided log-likelihood; 2-s. ent. = two-sided entropy; Mean3 = mean of standardized FDGPT, RoBERTa and Count; Mean4 = Mean3 plus 2-sided; Top2 = mean of the two largest of the Mean4 components.", indent=False, size=9, align="justify", after=6)
# 1 corpus
H1(d, "1. Corpus")
cnt = lambda f: sum(1 for _ in open(f"{D}/{f}"))
words = lambda f: int(np.median([len(json.loads(l)["text"].split()) for l in open(f"{D}/{f}")]))
rows = [["Source", "Documents", "Median words"], ["Human, medicine and computer science (PMC, arXiv cs)", "500 collected / 474 analysed", f"{words('human.jsonl'):,}"]]
for g, gl in (("gpt4o", "GPT-4o"), ("claude", "Claude Sonnet 5.5"), ("llama", "Llama 3.3 70B Instruct"), ("deepseek", "DeepSeek V4.1 Flash")):
    rows.append([gl, str(cnt(f"machine_{g}.jsonl")), f"{words(f'machine_{g}.jsonl'):,}"])
rows.append(["Human, economics (arXiv econ.*)", str(cnt("human_econ.jsonl")), f"{words('human_econ.jsonl'):,}"])
for g, gl in (("gpt4o", "GPT-4o"), ("claude", "Claude"), ("llama", "Llama"), ("deepseek", "DeepSeek")):
    rows.append([f"{gl}, economics topics", str(cnt(f"machine_econ_{g}.jsonl")), f"{words(f'machine_econ_{g}.jsonl'):,}"])
TABLE(d, "**Supplementary Table 1 | Documents.** Word counts before truncation to 2,000 tokens. DeepSeek papers: 200 generated, of which 100 with at least 2,400 words were attacked.", rows, widths=[3.2, 1.8, 1.2], size=8.5)
# 2 full AUC tables
H1(d, "2. Full AUC tables (medicine and computer science)")
P(d, "Negatives: 186 evaluation humans. Positives: 100 attacked papers per cell (guided attacks: 100 per generator for the three original generators). Training for each target excluded the target generator, Llama and DeepSeek.", indent=False, size=9, after=4)
meths = list(SH)
for i, (g, gl) in enumerate(GENS, 2):
    x = R[(R.target == g) & (R.generator == g)]
    rows = [["Attack"] + [SH[m] for m in meths]]
    for c in CONDS:
        y = x[x.cond == c]
        if len(y): rows.append([CL[c]] + [f2(y[y.method == m].auc.iloc[0]) if (y.method == m).any() else "–" for m in meths])
    TABLE(d, f"**Supplementary Table {i} | {gl} papers, AUC.**", rows, widths=[1.25] + [0.49] * len(meths), size=6.8)
# 3 CIs
H1(d, "3. Bootstrap intervals for key cells")
rows = [["Generator", "Attack"] + [SH[m] for m in ("fd", "rb", "sc", "dl", "mean4", "top2")]]
for g, gl in GENS:
    for c in ("orig", "mix50", "bok_mix", "noise10"):
        y = R[(R.target == g) & (R.generator == g) & (R.cond == c)]
        if not len(y): continue
        rows.append([gl, CL[c]] + [(lambda r: f"{r.auc:.2f} [{r.lo:.2f}, {r.hi:.2f}]")(y[y.method == m].iloc[0]) for m in ("fd", "rb", "sc", "dl", "mean4", "top2")])
TABLE(d, "**Supplementary Table 6 | AUC with 95% bootstrap intervals** (400 resamples of documents within each class).", rows, widths=[0.8, 1.0] + [0.78] * 6, size=7)
# 4 operating points
H1(d, "4. Operating points")
rows = [["Generator", "Attack"] + [SH[m] for m in ("fd", "rb", "tf", "sc", "dl", "mean4", "top2")]]
for g, gl in GENS:
    for c in ("orig", "edit1.0", "rewrite2", "mix50", "bok_mix"):
        y = R[(R.target == g) & (R.generator == g) & (R.cond == c)]
        if len(y): rows.append([gl, CL[c]] + [f2(y[y.method == m].tpr.iloc[0]) for m in ("fd", "rb", "tf", "sc", "dl", "mean4", "top2")])
fp = R.groupby(["target", "method"]).fpr.mean().unstack()
rows.append(["FPR", "evaluation humans (mean over targets)"] + [f"{fp[m].mean():.3f}" for m in ("fd", "rb", "tf", "sc", "dl", "mean4", "top2")])
TABLE(d, "**Supplementary Table 7 | Share of machine papers flagged** at the 95th percentile of 100 calibration humans; last row: false-positive rate on the evaluation humans.", rows, widths=[0.8, 1.3] + [0.62] * 7, size=7)
# 5 judge
H1(d, "5. Language-model judge")
samp = pd.read_csv(f"{D}/judge_sample.csv"); jc = pd.read_csv(f"{D}/judge_scores.csv")
hum = jc[(jc.judge == "gemini") & jc.id.isin(samp[samp.generator == "human"].id)].p_ai.dropna().values
rows = [["Generator", "Attack", "n", "AUC", "Share ≥ 50"]]
for fn in ("attack_judge_scores", "attacked2_judge_scores", "attacked_bok_judge_scores", "attacked_ds_judge_scores", "attacked2_ds_judge_scores"):
    j = pd.read_csv(f"{D}/{fn}.csv").dropna(subset=["p_ai"]); j["g"] = j.id.str.split(":").str[0]
    for (g, c), x in j.groupby(["g", "cond"]):
        rows.append([dict(GENS)[g], CL.get(c, c), str(len(x)), f"{roc_auc_score(np.r_[np.zeros(len(hum)), np.ones(len(x))], np.r_[hum, x.p_ai.values]):.2f}", f"{(x.p_ai >= 50).mean():.2f}"])
rows.append(["Human", "none", str(len(hum)), "–", f"{(hum >= 50).mean():.2f}"])
TABLE(d, "**Supplementary Table 8 | Gemini 2.5 Pro judge.** Negatives: 200 evaluation humans. Runs on mixing were limited by a spending cap.", rows, widths=[1.0, 1.4, 0.6, 0.7, 0.9], size=8)
# 6 econ
H1(d, "6. Economics papers")
E = R[R.target == "econ"]; rows = [["Generator", "Attack"] + [SH[m] for m in ("fd", "rb", "tf", "sc", "dl", "mean4", "top2")]]
for g, gl in GENS:
    for c in ("orig", "mix50", "noise10"):
        y = E[(E.generator == g) & (E.cond == c)]
        if len(y): rows.append([gl, CL[c]] + [f2(y[y.method == m].auc.iloc[0]) for m in ("fd", "rb", "tf", "sc", "dl", "mean4", "top2")])
TABLE(d, "**Supplementary Table 9 | Economics papers, AUC.** Negatives: 130 economics human papers; calibration: 86 calibration humans from the main fields. Supervised models trained on medicine and computer science (human, GPT-4o, Claude). Human economics papers were all converted from PDF, so supervised scores here are likely inflated by structural artifacts (main text).", rows, widths=[0.8, 1.2] + [0.62] * 7, size=7.5)
# 7 guided attacks
H1(d, "7. Guided attacks")
b = pd.DataFrame([json.loads(l) for l in open(f"{D}/attacked_bok.jsonl")])[["id", "cond", "generator", "fd"]]
o = pd.read_csv(f"{D}/attacked_binoculars.csv"); o["cond"] = o.id.str.split("|").str[-1]
o2 = pd.read_csv(f"{D}/attacked2_binoculars.csv"); o2["cond"] = o2.id.str.split("|").str[-1]
rows = [["Generator", "Original", "Rewrite (one)", "Guided rewrite (best of 4)", "Mixing (one)", "Guided mixing (best of 4)"]]
for g, gl in GENS[:3]:
    rows.append([gl, f"{o[(o.generator == g) & (o.cond == 'orig')].fastdetect.mean():.2f}", f"{o[(o.generator == g) & (o.cond == 'rewrite')].fastdetect.mean():.2f}",
                 f"{b[(b.generator == g) & (b.cond == 'bok_rw')].fd.mean():.2f}", f"{o2[(o2.generator == g) & (o2.cond == 'mix50')].fastdetect.mean():.2f}", f"{b[(b.generator == g) & (b.cond == 'bok_mix')].fd.mean():.2f}"])
TABLE(d, "**Supplementary Table 10 | Mean Fast-DetectGPT score** (higher = more machine-like; human papers average about 0.06). Selection lowers the score far more for mixing than for rewriting.", rows, widths=[0.9, 0.8, 1.0, 1.3, 1.0, 1.3], size=8)
# 8 count screen transfer
H1(d, "8. Count screen: transfer between generators (full corpus, earlier protocol)")
sr = json.load(open(f"{D}/screen_results.json"))
rows = [["Train → test", "Rates", "Dispersion", "Both"]] + [[k.replace("->", " → "), sr[k]["rates"], sr[k]["dispersion"], sr[k]["both"]] for k in sr if "->" in k]
TABLE(d, "**Supplementary Table 11 | Count screen, AUC (95% bootstrap interval)** with five-fold cross-validation grouped by source paper, before the calibration split was introduced.", rows, widths=[1.6, 1.6, 1.6, 1.6], size=8)
rows = [["Target", "Baseline", "Clustering", "Difference"]] + [[dict(GENS)[g], sr[f"unseen:{g}"]["baseline"], sr[f"unseen:{g}"]["clustering"], sr[f"unseen:{g}"]["diff"]] for g in ("gpt4o", "claude", "llama")]
TABLE(d, "**Supplementary Table 12 | Count screen on an unseen generator.**", rows, widths=[1.2, 1.7, 1.7, 1.9], size=8)
# 9 prompts
H1(d, "9. Prompts and procedures")
P(d, "**Rewrite (attacks 'LLM rewrite', 'rewrite + edit', guided rewrite with even k).** " + REWRITE.replace("{n}", "N").replace("{chunk}", "[passage]").replace("\n", " "), indent=False, size=9)
P(d, "**Second rewrite (attack 'rewrite twice', guided rewrite with odd k; temperature 1).** " + R2.replace("{n}", "N").replace("{chunk}", "[passage]").replace("\n", " "), indent=False, size=9)
P(d, "**Judge (Gemini 2.5 Pro, temperature 0).** " + PROMPT.replace("{text}", "[excerpt]").replace("\n", " "), indent=False, size=9)
P(d, "**Procedure.** Rewrites were done in chunks of 800 tokens by Llama 3.3 70B Instruct. Mixing replaces sentences with sentences of similar length from human papers of the same field that are neither evaluation humans nor the paper's own source. Zero-shot scores used Falcon-7B (observer) and Falcon-7B-instruct (performer) on the first 1,024 tokens. RoBERTa: roberta-base, two epochs, learning rate 2 × 10^{−5}, batch 16, maximum length 512. Compute: about US$118 of API calls in total for generation, attacks and judging, and about US$4 of GPU time for the final scoring run. All code and derived data: https://doi.org/10.5281/zenodo.23664508.", indent=False, size=9, align="justify")
d.save("TAI_Supplementary_Material.docx")
print("ok")
