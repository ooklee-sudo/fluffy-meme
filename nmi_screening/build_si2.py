import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
import pandas as pd, json
D = "replication/data"
M = pd.read_csv(f"{D}/audit_matrix.csv"); sr = json.load(open(f"{D}/screen_results.json"))
NAMES = {"screen_baseline": "Count screen (rates, dispersion)", "screen_clustering": "Count screen (+ clustering)", "loglik": "Log-likelihood", "logrank": "Log-rank", "entropy": "Entropy", "binoculars": "Binoculars", "fastdetect": "Fast-DetectGPT", "tfidf": "TF-IDF logistic", "roberta": "Fine-tuned RoBERTa", "gemini": "Gemini 2.5 Pro judge"}
GN = {"claude": "Claude", "gpt4o": "GPT-4o", "llama": "Llama"}
C = ["orig", "edit0.25", "edit0.5", "edit0.75", "edit1.0", "rewrite", "hybrid0.5", "hybrid1.0", "mix30", "mix50", "noise3", "noise10", "rewrite2"]
C = [c for c in C if c in M.columns]
f = lambda x: "–" if pd.isna(x) else f"{x:.2f}"
d = new_doc(spacing=1.15, running="Supplementary Information")
TITLE(d, "Supplementary Information", size=15)
P(d, "Which screens for machine-written scholarly text survive an adaptive author?  ·  Ook Lee", indent=False, align="center", size=10, italic=True, after=10)
H1(d, "1. Full AUC matrix")
P(d, "AUC of every method under every condition, against 200 unattacked human papers (100 machine papers per generator and condition; the judge column for mixing has 99, 100 and 64 papers for Claude, GPT-4o and Llama). Conditions: none (orig); feature edit at effort 0.25 to 1.0; LLM rewrite; hybrid (rewrite then edit) at effort 0.5 and 1.0; sentence mixing at 30% and 50%; typo noise at 3% and 10%; second rewrite. '–' means not run.", indent=False, size=10, after=6, align="justify")
SH = {"screen_baseline": "Count", "screen_clustering": "Count+clu.", "loglik": "Log-lik.", "logrank": "Log-rank", "entropy": "Entropy", "binoculars": "Binoc.", "fastdetect": "Fast-DGPT", "tfidf": "TF-IDF", "roberta": "RoBERTa", "gemini": "Judge"}
P(d, "Columns: Count = count screen (rates, dispersion); Count+clu. = with clustering features; Log-lik. = log-likelihood; Binoc. = Binoculars; Fast-DGPT = Fast-DetectGPT; Judge = Gemini 2.5 Pro.", indent=False, size=9, italic=True, after=6)
for g, gl in GN.items():
    rows = [["Condition"] + list(SH.values())]
    for c in C:
        rows.append([c] + [f(M[(M.detector == k) & (M.generator == g)].iloc[0].get(c)) if ((M.detector == k) & (M.generator == g)).any() else "–" for k in SH])
    TABLE(d, f"**Supplementary Table {list(GN).index(g)+1} | {gl} papers.**", rows, widths=[0.9] + [0.56] * len(SH), size=8)
H1(d, "2. Count screens: transfer between generators and human-only training")
rows = [["Train → test", "Rates", "Dispersion", "Both"]]
for k in ("gpt4o->gpt4o", "gpt4o->claude", "gpt4o->llama", "claude->gpt4o", "claude->claude", "claude->llama", "llama->gpt4o", "llama->claude", "llama->llama"):
    v = sr[k]; rows.append([k.replace("->", " → "), v["rates"], v["dispersion"], v["both"]])
TABLE(d, "**Supplementary Table 4 | AUC (95% bootstrap interval) by training and test generator.** Folds are grouped by source paper.", rows, widths=[1.6, 1.6, 1.6, 1.6], size=9)
rows = [["Target", "Baseline", "Clustering", "Difference"]] + [[GN[g], sr[f"unseen:{g}"]["baseline"], sr[f"unseen:{g}"]["clustering"], sr[f"unseen:{g}"]["diff"]] for g in GN]
TABLE(d, "**Supplementary Table 5 | Unseen generator.** Trained on human papers and the other two generators.", rows, widths=[1.2, 1.7, 1.7, 1.9], size=9)
rows = [["Target", "Rates", "Dispersion", "Both", "Clustering"]] + [[GN[g]] + [sr[f"human_only:{g}"][k] for k in ("rates", "dispersion", "both", "clustering")] for g in GN]
TABLE(d, "**Supplementary Table 6 | Trained on human papers only (no machine examples).**", rows, widths=[1.0, 1.4, 1.4, 1.4, 1.4], size=9)
H1(d, "3. Two-sided probability scores")
b = pd.read_csv(f"{D}/attacked2_binoculars.csv"); b["cond"] = b.id.str.split("|").str[-1]; neg = b[b.cond == "clean"]
from sklearn.metrics import roc_auc_score
rows = [["Score", "Generator", "Condition", "One-sided AUC", "Two-sided AUC"]]
for m in ("loglik", "entropy"):
    med = neg[m].median()
    for g in ("claude", "gpt4o"):
        for c in ("mix30", "mix50", "noise10"):
            x = pd.concat([neg, b[(b.generator == g) & (b.cond == c)]]); rows.append([NAMES[m], GN[g], c, f(roc_auc_score(x.label, x[m])), f(roc_auc_score(x.label, (x[m] - med).abs()))])
TABLE(d, "**Supplementary Table 7 | One- and two-sided scores under perturbation.** Two-sided score = absolute deviation from the median of the 186 human negatives (the threshold uses the evaluation negatives, so values are optimistic).", rows, widths=[1.3, 1.0, 1.0, 1.4, 1.4], size=9)
H1(d, "4. Artifact control")
ac = pd.read_csv(f"{D}/artifact_control_results.csv"); acp = ac.pivot_table(index=["protocol", "generator"], columns="variant", values="auc")
rows = [["Protocol", "Generator", "Raw", "Artifacts removed", "Function words only"]] + [[p, GN[g], f(r["raw"]), f(r["clean"]), f(r["function"])] for (p, g), r in acp.iterrows()]
TABLE(d, "**Supplementary Table 8 | TF-IDF classifier variants** (see Methods of the main text; script s10_artifact_control.py).", rows, widths=[1.5, 1.0, 1.0, 1.5, 1.5], size=9)
H1(d, "5. Procedure details")
P(d, "Generation: three prompt levels of increasing detail; each paper was written in four requests (introduction, methods, results, discussion) from the title and abstract of a sampled human paper (scripts s1 and s2). Judge prompt: see s5_judges.py. Attacks: see s7_attacks.py and s9_adaptive.py. Compute: the study used about US$78 of API calls and a rented 48 GB GPU for the published detectors and the RoBERTa classifier. All code and derived data are at https://doi.org/10.5281/zenodo.23664508.", indent=False, size=10, align="justify")
d.save("NMI_Audit_Supplementary_Information.docx")
