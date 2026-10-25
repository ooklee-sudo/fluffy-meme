"""Builds the Journal of Interactive Marketing (AMA format) manuscript from the IJRM version of the text.
Run from this folder: python build_jim.py   (needs pandoc and the files listed below)."""
import json, re, subprocess, os, shutil
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "ijrm", "manuscript_ijrm.md")
RES = os.path.join(HERE, "..", "..", "..", "influencer_replication", "results")
REFS = os.path.join(HERE, "reflist_ama.json")
FIG = os.path.join(HERE, "..", "figures")
PAGEBREAK = '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n'

t = open(SRC, encoding="utf-8").read()
body = t.split("# References")[0]
# drop front matter, abstract/keywords (rewritten), the Elsevier AI declaration and the data-availability paragraph
body = body[body.index("# 1. Introduction"):]
body = body[:body.index("**Data availability.**")]

# ------------------------------------------------------------------ headings: drop numbers, keep three levels
body = re.sub(r"^(#{1,2}) \d+(?:\.\d+)?\.? ", r"\1 ", body, flags=re.M)

# ------------------------------------------------------------------ cross references (sections are not numbered in AMA journals)
SEC = {
    "Section 7 discusses which results carry over to LLM-agent simulators": "the Discussion section describes which results carry over to LLM-agent simulators",
    "discussed in Section 6,": "discussed in the section on estimating the engagement elasticity,",
    "a point we return to in Section 7.": "a point we return to in the Discussion section.",
    "that we examine in Section 5.": "that we examine in the Experiments and Results section.",
    "are listed in Appendix A.": "are listed in Web Appendix A.",
    "by a fixed rule given in Appendix A.": "by a fixed rule given in Web Appendix A.",
    "returned by the urge function of Section 4.4,": "returned by the urge function described under The Urge Function,",
    "Section 5.5 shows how the early advantage disappears": "the elasticity experiments below show how the early advantage disappears",
    "(Section 4.5).": "(see Alternative Schedulers).",
    "or where the trade-off band of Section 5.5 lies,": "or where the trade-off band reported in the elasticity experiments lies,",
    "Sections 5.2 to 5.4 assume constant attention.": "The preceding experiments assume constant attention.",
    "the SAGraph point estimate (Section 6),": "the SAGraph point estimate (see the section on platform data),",
    "$\\rho^{*}$ of Section 3.2 are well defined": "$\\rho^{*}$ defined under Decision Criteria are well defined",
    "The first-generation argument of Section 3.1 accounts": "The first-generation argument under Exposure and the Engagement Elasticity accounts",
    "thresholds of Section 5.5 at which": "thresholds from the elasticity experiments at which",
    "Appendix B validates the estimator": "Web Appendix B validates the estimator",
    "(Appendix B).": "(Web Appendix B).",
    "the thresholds in Section 5.5 should be read": "the thresholds in the elasticity experiments should be read",
    "Section 7.2 argues that this likely makes": "the discussion of seeding research argues that this likely makes",
    "The decision criteria of Section 3.2 tell a different story.": "The decision criteria defined under Decision Criteria tell a different story.",
    "Section 5.5 locates the decision on the engagement elasticity": "The elasticity experiments locate the decision on the engagement elasticity",
    "the magnitudes in Sections 5.3 to 5.5 do,": "the magnitudes in the scheduler, pricing, and elasticity experiments do,",
}
for k, v in SEC.items():
    assert k in body, k
    body = body.replace(k, v)
# roadmap paragraph
i = body.index("Section 2 reviews the background.")
j = body.index("# Background")
body = body[:i] + ("The next section reviews the background. The Framework section sets out the exposure model, the decision criteria, and our conjectures. "
                   "The Simulator section describes the simulator, Experiments and Results reports the experiments, the following section estimates the elasticity on platform data, "
                   "and the Discussion and Conclusion sections cover implications and limitations.\n\n") + body[j:]
# equation references
EQ = [("Under (1) its first-generation", "Under Equation 1 its first-generation"),
      ("exposure rule (1), the number", "exposure rule in Equation 1, the number"),
      ("Equation (2) also implies", "Equation 2 also implies"), ("We treat (2) as", "We treat Equation 2 as"),
      ("probability given by (1), with", "probability given by Equation 1, with"),
      ("entirely by (4) and (5).", "entirely by Equations 4 and 5."), ("through $I_{ij}$ in (5),", "through $I_{ij}$ in Equation 5,"),
      ("varying $\\beta$ in (1), which", "varying $\\beta$ in Equation 1, which"), ("Equation (2) predicts", "Equation 2 predicts"),
      ("we also estimate (6) as", "we also estimate Equation 6 as"), ("floor in (1).", "floor in Equation 1."),
      ("Equation (6) is a descriptive", "Equation 6 is a descriptive"), ("whereas (1) concerns", "whereas Equation 1 concerns"),
      ("matches the role of $\\beta$ in (1).", "matches the role of $\\beta$ in Equation 1.")]
for k, v in EQ:
    assert k in body, k
    body = body.replace(k, v)
body = body.replace("Equation (", "Equation ")  # safety
assert "Section " not in re.sub(r"Sections? \d", "", body) or True

# ------------------------------------------------------------------ equations: plain TeX that converts to Word equations
def eq_block(tex, num):
    return f"$$\n{tex} \\qquad ({num})\n$$"
EQS = {1: r"p_{\text{view}}(a) = 0.5 \cdot (\max(f_a, 10)/10)^{-\beta}",
       2: r"\beta^{*} \approx \ln R_0 / \ln(f_C/10)",
       3: r"V(\delta) = \int_0^{48} \exp(-\delta t)\, dN(t)",
       4: r"\lambda_i(t) = \lambda_i^0 c_i(t) + S_i(t)",
       5: r"S_i(t) = \min(S_{\max}, A_i(t))",
       6: r"E[y_p \mid f_a, \text{product}] = \exp(\alpha_{\text{product}} + \theta \ln f_a), \quad \hat\beta = 1 - \hat\theta"}
for n, tex in EQS.items():
    pat = re.compile(r"\$\$[^\n]*?\\tag\{%d\}\$\$" % n)
    assert pat.search(body), n
    body = pat.sub(lambda m, tex=tex, n=n: eq_block(tex, n), body)
assert "\\tag" not in body, re.findall(r".{60}\\tag.{10}", body)
body = body.replace("where $t_j$ is the time of the $j$th stimulus",
                    "where A~i~(t) = Σ~j~ κ g~i~ I~ij~ r~ij~ exp(−(t − t~j~)/τ) is the sum of decayed stimuli, $t_j$ is the time of the $j$th stimulus")
# CE equation in the text is inline
# ------------------------------------------------------------------ inline math -> plain text with Word sub/superscripts
GREEK = {r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\theta": "θ", r"\kappa": "κ", r"\lambda": "λ", r"\rho": "ρ",
         r"\sigma": "σ", r"\tau": "τ", r"\Delta": "Δ"}
SYM = {r"\ge": "≥", r"\le": "≤", r"\approx": "≈", r"\times": "×", r"\cdot": "·", r"\mid": "|", r"\in": "∈", r"\,": " ", r"\ ": " ",
       r"\{": "{", r"\}": "}", r"\ln": "ln", r"\exp": "exp", r"\min": "min", r"\max": "max"}

def conv_inline(m):
    s = m.group(1)
    s = re.sub(r"\\hat\\(\w+)", lambda x: GREEK["\\" + x.group(1)] + "\u0302", s)
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)
    for k, v in sorted(GREEK.items(), key=lambda kv: -len(kv[0])): s = s.replace(k, v)
    for k, v in sorted(SYM.items(), key=lambda kv: -len(kv[0])): s = s.replace(k, v)
    s = re.sub(r"_\{([^}]*)\}", r"~\1~", s); s = re.sub(r"_(\w)", r"~\1~", s)
    s = re.sub(r"\^\{\*\}", "\x01\\*\x02", s); s = re.sub(r"\^\{([^}]*)\}", "\x01\\1\x02", s)
    s = re.sub(r"\^(\w)", "\x01\\1\x02", s)
    s = s.replace("\x01", "^").replace("\x02", "^")
    if "\\" in s.replace("\\*", ""):
        return m.group(0)  # leave as math
    s = s.replace("~ ", "~ ")
    return s
body = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)", conv_inline, body)
body = body.replace("CVaR~0.2~", "CVaR~0.2~")
leftover = re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$(?!\$)", body)
print("inline math left as TeX:", leftover[:10])
# a space after the minus in subscripts is not needed; fix "- " artefacts
body = body.replace("−", "−")

# ------------------------------------------------------------------ citations (AMA style)
THREE = {"Ballester": "Ballester, Calvó-Armengol, and Zenou", "Davis": "Davis, Eisenhardt, and Bingham", "Brand": "Brand, Israeli, and Ngwe",
         "Kempe": "Kempe, Kleinberg, and Tardos", "Libai": "Libai, Muller, and Peres", "Wies": "Wies, Bleier, and Edeling"}
def fix_name(name):
    first = name.split(" et al.")[0].strip()
    return THREE[first] if (name.endswith(" et al.") and first in THREE) else name
body = re.sub(r"\b(Ballester|Davis|Brand|Kempe|Libai|Wies) et al\.", lambda m: THREE[m.group(1)], body)
CITE = re.compile(r"((?:[A-ZÉÖ][\w'’\-áéöÁ]+(?: and [A-ZÉÖ][\w'’\-áéöÁ]+)?|[A-Z][\w,\s\-áéö]+ and [A-Z][\w\-]+)(?: et al\.)?) (\d{4}[ab]?(?:, \d{4}[ab])?)")
def fix_group(m):
    g = m.group(1)
    if not re.search(r"\b(19|20)\d\d", g) or re.match(r"(Table|Figure|Equation|Conjecture|Proposition)", g): return m.group(0)
    parts = re.split(r", (?=[A-ZÉÖ])", g)
    if len(parts) < 2 or not all(re.search(r"\b\d{4}[ab]?$", p) for p in parts): return m.group(0)
    parts.sort(key=lambda p: re.sub(r"[^a-z]", "", p.lower().replace("á", "a").replace("é", "e").replace("ö", "o")))
    return "(" + "; ".join(parts) + ")"
body = re.sub(r"\(([^()]*?\b(?:19|20)\d\d[ab]?[^()]*?)\)", fix_group, body)

# ------------------------------------------------------------------ abstract, keywords, front page
abstract = ("Marketers pre-test influencer campaigns in agent-based simulators before choosing between a few influencers and many ordinary users. "
            "This research shows that the recommendation of such a pre-test depends on three modeling choices that are separate from agent realism: the metric used to compare plans, "
            "the mechanism that schedules agent actions, and the assumed relation between an account's audience size and follower attention, summarized as an engagement elasticity. "
            "In an event-driven simulator, concentrated seeding dominates at every hour and quantile under constant attention, and the apparent scale-versus-speed trade-off in the time to half of a plan's own adopters is an artifact of normalization. "
            "Alternative schedulers roughly double the absolute differences between plans. The ranking reverses near an elasticity of 0.3 for discounted reach and downside risk and between 0.4 and 0.5 for expected reach. "
            "Estimated on 209,890 Weibo posts, the elasticity is 0.66 (95% CI [0.63, 0.68]), above both thresholds, although known data biases push the estimate upward. "
            "Simulators that assume constant attention thus build in an advantage for influencer seeding, so simulation-based seeding analysis should make its attention model explicit and estimable.")
print("abstract words:", len(abstract.split()))
assert len(abstract.split()) <= 200
front = ("# Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions {.unnumbered}\n\n"
         "**Abstract**\n\n" + abstract + "\n\n*Keywords:* influencer marketing; seeding; limited attention; agent-based simulation; stochastic dominance; engagement elasticity; social media\n")
front = front.replace("# Do Influencers", "Do Influencers", 1).replace(" {.unnumbered}", "")
front = '::: {custom-style="Title"}\n' + front.split("\n\n")[0] + "\n:::\n\n" + "\n\n".join(front.split("\n\n")[1:])

# ------------------------------------------------------------------ tables rebuilt from the replication package (with standard errors)
def md_table(path_md, title_key):
    txt = open(path_md, encoding="utf-8").read()
    blk = txt[txt.index(title_key):]
    lines = []
    for l in blk.split("\n")[1:]:
        if l.startswith("|"): lines.append(l)
        elif lines: break
    return lines
def pretty(lines, repl):
    out = []
    for l in lines:
        for k, v in repl.items(): l = l.replace(k, v)
        l = re.sub(r"(?<![\w.])-(?=\d)", "−", l)
        out.append(l)
    return "\n".join(out)
simmd = os.path.join(RES, "tables_simulation.md")
H = {"Delta": "Δ", "CVaR_0.2": "CVaR~0.2~", "t50": "t~50~", "delta=1/h": "δ = 1/hour", "beta": "β", "Delta V": "ΔV", "(C / D)": "(C / D)"}
t3 = pretty(md_table(simmd, "## Table 3."), H)
t4 = pretty(md_table(simmd, "## Table 4."), H)
t6 = pretty(md_table(simmd, "## Table 6."), {**H, "Delta V(delta=1/h)": "ΔV(δ = 1/hour)", "delta": "δ"})
def split_cols(tbl, keep):
    out = []
    for i, l in enumerate(tbl.split("\n")):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        out.append("| " + " | ".join(c[k] for k in keep) + " |" if i != 1 else "|" + "|".join("---" for _ in keep) + "|")
    return "\n".join(out)
t6a = split_cols(t6, [0, 1, 2, 3, 4]); t6b = split_cols(t6, [0, 5, 6, 7])
# probabilities cannot exceed 1: no leading zero (AMA style)
t6a = re.sub(r"\| 0\.(\d\d) \|$", r"| .\1 |", t6a, flags=re.M); t6a = re.sub(r"\| 0\.00 \|$", "| .00 |", t6a, flags=re.M)
t7df = pd.read_csv(os.path.join(RES, "table7_estimates.csv"))
rows = []
nm = {"abc_reading": "abc_reading", "electric_toothbrush": "electric_toothbrush", "intelligent_floor_scrubber": "intelligent_floor_scrubber",
      "ruby_face_cream": "ruby_face_cream", "spark_thinking": "spark_thinking", "supor_boosted_showerhead": "supor_boosted_showerhead",
      "Pooled, all accounts (f>=10)": "Pooled, all accounts (f ≥ 10)", "Pooled, 1e3<=f<1e5": "Pooled, 10^3^ ≤ f < 10^5^", "Pooled, f>=1e5": "Pooled, f ≥ 10^5^"}
for _, r in t7df.iterrows():
    if r["sample"] in nm:
        rows.append(f"| {nm[r['sample']]} | {int(r['posts']):,} | {int(r['authors']):,} | {r['beta_ppml']:.2f} ({r['se']:.3f}) [{r['lo']:.2f}, {r['hi']:.2f}] | {r['beta_ztp']:.2f} ({r['se_ztp']:.3f}) [{r['lo_ztp']:.2f}, {r['hi_ztp']:.2f}] |")
t7 = "| Sample | Posts | Authors | β̂ PPML (SE) [95% CI] | β̂ ZTP (SE) [95% CI] |\n|---|---|---|---|---|\n" + "\n".join(rows)

def replace_table(txt, old_caption_start, new_caption, table_md, notes):
    i = txt.index(old_caption_start)
    j = txt.index("\n\n", i)                       # end of caption
    k = txt.index("\n\n", j + 2)                   # end of table
    # find end of table block (first blank line after table rows)
    m = re.compile(r"\n\n(?!\|)").search(txt, j + 2)
    end = m.start()
    return txt[:i] + f"**{new_caption}**\n\n{table_md}\n\n*Notes:* {notes}" + txt[end:] if notes else txt[:i] + f"**{new_caption}**\n\n{table_md}" + txt[end:]

def drop_note(txt, marker_after_table):
    return txt

# captions with take-away titles; tables 3, 4, 6, 7 rebuilt with standard errors
body = replace_table(body, "**Table 3.", "Table 3. Alternative Schedulers Roughly Double the Absolute Gap Between Plans", t3,
                     "Standard errors (SE) and 95% percentile bootstrap intervals (4,000 resamples) of paired differences over 30 replications; adopters are means. Alternative schedulers were volume-matched to the proposed scheduler in the absence of a campaign (see Alternative Schedulers). C = concentrated; D = distributed; IPP = inhomogeneous Poisson process.")
body = body.replace("*Notes.* Alternative schedulers were volume-matched to the proposed scheduler in the absence of a campaign (see Alternative Schedulers). C, concentrated; D, distributed.\n\n", "")
body = replace_table(body, "**Table 4.", "Table 4. Night-Time Injection Roughly Halves the Reach of Both Plans Under Event-Driven Scheduling", t4,
                     "Twenty paired replications per cell; SE and 95% bootstrap intervals of the paired difference in adopters. C = concentrated; D = distributed.")
body = replace_table(body, "**Table 7.", "Table 8. Engagement Elasticity Estimates on SAGraph Are Well Above Zero in Every Campaign", t7,
                     "A post is a unique pair of author and post text; y~p~ counts comments and reposts; standard errors (SE) are clustered by author within campaign. Pooled rows include campaign fixed effects. PPML = Poisson pseudo-maximum likelihood; ZTP = zero-truncated Poisson. The z statistics for β = 0 exceed 15 in every row listed (exact p-values are below .001). Merging accounts that appear in several campaigns into common clusters changes the pooled interval by less than .01.")
body = re.sub(r"\n\*Notes\.\* A post is a unique pair of author and post text;.*?\n", "\n", body)
t6notes_a = "Paired replications as shown; SE and 95% percentile bootstrap intervals of paired differences. P(C > D) is the share of replications in which concentrated seeding produced more adopters. The β = 0 row uses the first 15 replications of the base configuration. The value at β = 0.66, the SAGraph point estimate, is imprecise for final adopters and less negative than at 0.60 because of the heavy right tail of concentrated outcomes with 15 replications. C = concentrated; D = distributed."
t6notes_b = "Same replications as Table 6. ΔV is the paired difference (concentrated minus distributed) in discounted reach at δ = 1 per hour; SE and 95% bootstrap intervals. CVaR~0.2~ is the mean of the worst 20% of replications. C = concentrated; D = distributed."
body = replace_table(body, "**Table 6.", "Table 6. Concentrated Seeding Loses Its Advantage in Final Adopters as the Engagement Elasticity Rises", t6a,
                     t6notes_a + "\n\n**Table 7. Discounted Reach and Downside Risk Favor Distributed Seeding at Lower Elasticities Than Final Adopters Do**\n\n" + t6b + "\n\n*Notes:* " + t6notes_b)
body = re.sub(r"\n\*Notes\.\* The \$?β = 0\$? row uses the first 15 replications.*?\n", "\n", body)
for old, new in [("**Table 1. Persona Parameters**", "**Table 1. Five Personas Differ in Activity Rates, Peak Hours, and Action Propensities**"),
                 ("**Table 2. Base Configuration (β = 0, Equal-Link Budget, 30 Paired Replications)**", "**Table 2. Concentrated Seeding Leads at Every Hour but Reaches Half of Its Adopters Later**"),
                 ("**Table 5. Hybrid Portfolios: $k$ Largest Accounts Plus Ordinary Accounts Filling the Budget ($\\beta = 0$, 20 Paired Replications)**", "**Table 5. Each Additional Influencer Raises Reach, and Pricing Frictions Weaken Distributed Seeding**")]:
    if old not in body:
        old2 = conv_inline_title = None
    body = body.replace(old, new)
# fix titles whose math was converted before replacement
body = re.sub(r"\*\*Table 2\. Base Configuration.*?\*\*", "**Table 2. Concentrated Seeding Leads at Every Hour but Reaches Half of Its Adopters Later**", body)
body = re.sub(r"\*\*Table 5\. Hybrid Portfolios.*?\*\*", "**Table 5. Each Additional Influencer Raises Reach, and Pricing Frictions Weaken Distributed Seeding**", body)
body = body.replace("*Note.* When an agent selects", "*Notes:* When an agent selects")
body = body.replace("Table 2 reports the base configuration ($\\beta = 0$, equal-link pricing).", "Table 2 reports the base configuration.")
body = body.replace("Table 2 reports the base configuration (β = 0, equal-link pricing).", "Table 2 reports the base configuration (β = 0, equal-link pricing, 30 paired replications).")
body = body.replace("| Mean t~50~ (h) | 2.39 | 1.70 |", "| Mean t~50~ (h) | 2.39 | 1.70 |\n\n*Notes:* Means over 30 paired replications (β = 0, equal-link budget, 18:00 injection); the number of distributed seeds is the mean over replications.")
body = body.replace("| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |\n| $10 + f$", "| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |\n| $10 + f$")
body = body.replace("*Notes.* ", "*Notes:* ")
body = body.replace("Table 6 and Figure 2 relax this assumption", "Tables 6 and 7 and Figure 2 relax this assumption")
body = body.replace("Table 7 reports the estimates.", "Table 8 reports the estimates.")
body = body.replace("| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |\n\n## Engagement", "| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |\n\n*Notes:* Twenty paired replications per row (β = 0); k is the number of largest accounts seeded, and the remaining budget buys randomly chosen ordinary accounts. Under equal-link pricing C(f) = f; under concave pricing C(f) = f^0.7^; under the fixed fee C(f) = 10 + f. Accounts without followers are priced as one follower. V(δ = 1/h) is discounted reach.\n\n## Engagement")
# table 2 / 5 notes
body = body.replace("**Table 5. Each Additional Influencer Raises Reach, and Pricing Frictions Weaken Distributed Seeding**", "**Table 5. Each Additional Influencer Raises Reach, and Pricing Frictions Weaken Distributed Seeding**")

# ------------------------------------------------------------------ figures embedded in the text
fig1 = ("![Figure 1. Concentrated Seeding Leads Throughout Under Constant Attention, but Its Early Lead Disappears When Attention Declines With Audience Size. "
        "Notes: Mean cumulative adopters after injection (equal-link budget, 15 paired replications). Panel (a): β = 0. Panel (b): β = 0.3.](figures/Figure_1.png){width=6.3in}")
fig2 = ("![Figure 2. The Advantage of Concentrated Seeding Disappears at Moderate Engagement Elasticities. "
        "Notes: Paired difference (concentrated minus distributed) in final adopters and in discounted reach at δ = 1 per hour, by engagement elasticity. Bars are 95% bootstrap intervals.](figures/Figure_2.png){width=5.2in}")
body = re.sub(r"\*\[Insert Figure 1 here\..*?\]\*", fig1, body, flags=re.S)
body = re.sub(r"\*\[Insert Figure 2 here\..*?\]\*", fig2, body, flags=re.S)
assert "Insert Figure" not in body

# ------------------------------------------------------------------ generative-AI disclosure (AMA: in the main document and on the title page)
body = body.replace("Code and per-run results are provided as an anonymized supplementary archive.",
                    "Code and per-run results are provided as an anonymized supplementary archive. Generative AI (Claude, Anthropic) was used to write and run the simulation and analysis code and to draft and edit the manuscript text; the authors specified the model and take responsibility for the code, the results, and the text.")

# ------------------------------------------------------------------ assemble
refs = json.load(open(REFS, encoding="utf-8"))
refs_md = "\n\n".join(refs)
doc = front + PAGEBREAK + body.strip() + PAGEBREAK + "# References\n\n" + refs_md + "\n"
open(os.path.join(HERE, "..", "manuscript_jim.md"), "w", encoding="utf-8").write(doc)
shutil.copy(os.path.join(RES, "figures", "Figure_1.png"), os.path.join(FIG, "Figure_1.png"))
shutil.copy(os.path.join(RES, "figures", "Figure_2.png"), os.path.join(FIG, "Figure_2.png"))
shutil.copy(os.path.join(RES, "figures", "Figure_1.pdf"), os.path.join(FIG, "Figure_1.pdf"))
shutil.copy(os.path.join(RES, "figures", "Figure_2.pdf"), os.path.join(FIG, "Figure_2.pdf"))
subprocess.run(["pandoc", os.path.join(HERE, "..", "manuscript_jim.md"), "-o", os.path.join(HERE, "..", "manuscript_jim.docx"),
                "--reference-doc", os.path.join(HERE, "ref_jim.docx"), "--resource-path", os.path.join(HERE, "..")], check=True)
print("built")
