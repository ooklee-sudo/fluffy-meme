"""Builds supp.tex (Supplementary Material) from the online appendix (docx), the result CSVs and the pilot logs."""
import json, os, re
import numpy as np, pandas as pd
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "..", "results"); X = os.path.join(HERE, "..", "extra")
DOCX = os.path.join(HERE, "source", "online_appendix.docx")

# ----------------------------------------------------------------------------- text conversion
UNI = {"ν": r"$\nu$", "ρ": r"$\rho$", "π": r"$\pi$", "Δ": r"$\Delta$", "±": r"$\pm$", "−": r"$-$", "×": r"$\times$", "≥": r"$\geq$", "≤": r"$\leq$",
       "≈": r"$\approx$", "“": "``", "”": "''", "’": "'", "‘": "`", "–": "--", "—": "---", "…": r"\ldots{}", "†": r"\textdagger{}", "α": r"$\alpha$", "δ": r"$\delta$", "\u00a0": " ",
       "é": r"\'e", "ü": r"\"u", "κ": r"$\kappa$", "→": r"$\to$"}
PROT = [(r"\bs\*", r"$s^{*}$"), (r"f\(e\*\)", r"$f(e^{*})$"), (r"\bs_mix\b", r"$s_{\mathrm{mix}}$"), (r"1/\(1 − s\*\)", r"$1/(1-s^{*})$"),
        (r"\be\*", r"$e^{*}$")]

def esc(t):
    toks = []
    def keep(m):
        toks.append(m.group(0)); return f"\u27e6{len(toks)-1}\u27e7"
    for pat, _ in PROT:
        t = re.sub(pat, keep, t)
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}"), (">", r"\textgreater{}"), ("|", r"\textbar{}"), ("<", r"\textless{}")):
        t = t.replace(a, b)
    for k, v in UNI.items():
        t = t.replace(k, v)
    def back(m):
        s = toks[int(m.group(1))]
        for pat, rep in PROT:
            if re.fullmatch(pat, s):
                return rep
        return s
    t = re.sub("\u27e6(\\d+)\u27e7", back, t)
    bad = {c for c in t if ord(c) > 127}
    assert not bad, bad
    return t

def table_tex(tb, caption, spec=None, size="scriptsize"):
    n = len(tb.columns)
    spec = spec or ("l" + "c" * (n - 1))
    rows = [[esc(c.text.strip().replace("\n", " ")) for c in r.cells] for r in tb.rows]
    return mk_table(rows, caption, spec, size)

def mk_table(rows, caption, spec, size="scriptsize"):
    out = [f"\\begin{{{size}}}", "\\setlength{\\tabcolsep}{2pt}", f"\\begin{{longtable}}{{{spec}}}", f"\\caption{{{caption}}}\\\\", "\\toprule",
           " & ".join(f"\\textbf{{{c}}}" for c in rows[0]) + " \\\\", "\\midrule", "\\endfirsthead", "\\toprule", " & ".join(f"\\textbf{{{c}}}" for c in rows[0]) + " \\\\", "\\midrule", "\\endhead", "\\bottomrule", "\\endfoot"]
    out += [" & ".join(r) + " \\\\" for r in rows[1:]]
    out += ["\\end{longtable}", f"\\end{{{size}}}", ""]
    return "\n".join(out)

SPEC = {0: "llp{3.4cm}p{5cm}rr", 1: "lp{7.4cm}p{3.6cm}ll", 2: "lp{12cm}", 3: "lp{12cm}", 4: "p{1.6cm}p{3.2cm}rrp{3.8cm}p{2.6cm}", 11: "llrrrrr"}
SIZE = {0: "scriptsize", 1: "scriptsize", 2: "footnotesize", 3: "footnotesize", 4: "tiny", 5: "tiny", 6: "scriptsize", 7: "footnotesize", 8: "tiny", 9: "tiny", 10: "scriptsize", 11: "scriptsize", 12: "footnotesize", 13: "footnotesize"}

d = docx.Document(DOCX)
seq = []
for ch in d.element.body.iterchildren():
    tag = ch.tag.split("}")[1]
    if tag == "p":
        p = Paragraph(ch, d)
        if p.text.strip():
            seq.append(("p", p.style.name, p.text))
    elif tag == "tbl":
        seq.append(("t", None, Table(ch, d)))

def prose(t):
    t = esc(t)
    # lead-in labels such as "Audit." or "Pilot." in italics
    return re.sub(r"^((?:Audit|Human review|Pilot|Power|Exploratory)\.?)(?= )", r"\\emph{\1}", t) if re.match(r"^(Audit|Human review|Pilot|Power|Exploratory)", t) else t

# ----------------------------------------------------------------------------- proofs (typeset by hand)
PROOFS = r"""
\section{Proofs of the propositions}
Propositions 1, 3 and 6 are stated in the main text. The remaining statements are given here for completeness; the numbering follows the original analysis plan. Throughout, a reviewer is correct with probability $a$ independently of whether the stated preference $S$ is correct, which has probability $\pi$, and defers with probability $s_r$ (if $S$ is right) or $s_w$ (if $S$ is wrong).

\paragraph{Proposition 2 (complementarity).} In the symmetric case with integrity $i=1-s$, $V=i(a-\pi)$, and the cross-partial derivative with respect to $a$ and $i$ is one. \emph{Proof:} $\partial^2 V/\partial a\,\partial i=\partial^2[i(a-\pi)]/\partial a\,\partial i=1$.

\paragraph{Proposition 4 (overstatement).} The share of the ability-based value $a-\pi$ that is lost to deference is $s$ whatever $\pi$; valuing a reviewer by $a-\pi$ overstates its value by the factor $1/(1-s)$. \emph{Proof:} $1-V/(a-\pi)=s$ for $a\ne\pi$.

\paragraph{Proposition 5 (heterogeneity across items).} Let items $i$ differ in ability $a_i$ and in deference $s_i$ (symmetric within an item), with means $\bar a$ and $\bar s$, and define the conditional deference $s_c=E[a_is_i]/\bar a$. Then $V(\pi)=E[(1-s_i)(a_i-\pi)]=\bar a(1-s_c)-\pi(1-\bar s)$, and the closed form $V_{\mathrm{cf}}=(1-s_c)(\bar a-\pi)$ differs from it by $V(\pi)-V_{\mathrm{cf}}=\pi(\bar s-s_c)=-\pi\,\mathrm{Cov}(a_i,s_i)/\bar a$.

\paragraph{Proposition 7 (sophisticated requester).} If the requester knows the parameters and updates, her value is weakly decreasing in $s$, and strictly where the report would change her decision; the report of a deferential reviewer is a garbling of that of a non-deferential one.

\paragraph{Proposition 8 (implied prices).} If the process can hide the stance from the reviewer at a cost $\delta$ in ability, so that a blinded reviewer does not defer and yields $a-\delta-\pi$, blinding is better if and only if $\delta<s(a-\pi)$; it never helps when $a\le\pi$. The expression $s(a-\pi)$ is the largest amount that a buyer who observes $s$ should pay for a non-deferential version of the same reviewer.

\paragraph{Proposition 9 (ranking by ability).} For two reviewers with $a_1>a_2$, $V_1-V_2=N+\pi(s_1-s_2)$, where $N=(1-s_1)a_1-(1-s_2)a_2$. Ranking by ability is value-optimal for every prior in $[0,1]$ if and only if $(1-s_1)a_1\ge(1-s_2)a_2$ and $(1-s_1)(1-a_1)\le(1-s_2)(1-a_2)$.

\bigskip\noindent\textbf{Proof of Proposition 1.} Accuracy with review is $\pi[s_r+(1-s_r)a]+(1-\pi)(1-s_w)a$: when $S$ is right the reviewer reports $S$ with probability $s_r$ and otherwise reports the correct answer with probability $a$; when $S$ is wrong it reports the correct answer, which is not $S$, with probability $(1-s_w)a$. Subtracting $\pi$ gives
\[
V=(1-\pi)(1-s_w)\,a-\pi(1-s_r)(1-a),
\]
because $\pi[s_r+(1-s_r)a]-\pi=-\pi(1-s_r)(1-a)$. With $s_w=s_r=s$, $V=(1-s)[(1-\pi)a-\pi(1-a)]=(1-s)(a-\pi)$. $V$ is linear in $\pi$. Its zero solves $(1-\pi)(1-s_w)a=\pi(1-s_r)(1-a)$, that is $\pi^{*}=(1-s_w)a/[(1-s_w)a+(1-s_r)(1-a)]$, which equals $a$ when $s_w=s_r$. \hfill$\square$

\medskip\noindent\textbf{Proof of Propositions 2--4.} With $i=1-s$, $V=i(a-\pi)$. The cross-partial $\partial^2V/\partial a\,\partial i$ equals one. $\mathrm{d}V/\mathrm{d}s=-(a-\pi)$, which has the sign of $\pi-a$: deference lowers $V$ if and only if $a>\pi$ and raises it if $a<\pi$. The loss share is $1-V/(a-\pi)=s$ for $a\ne\pi$. \hfill$\square$

\medskip\noindent\textbf{Proof of Proposition 5.} In item $i$ the reviewer is correct with probability $(1-s_i)a_i+s_i\,\mathbf 1[S\text{ correct}]$. Averaging over the stance (right with probability $\pi$) and over items gives $E[(1-s_i)a_i]+\pi E[s_i]-\pi=E[(1-s_i)(a_i-\pi)]$. Expanding, $V=\bar a-\pi-E[a_is_i]+\pi\bar s$. By definition $E[a_is_i]=\bar a s_c$, so $V=\bar a(1-s_c)-\pi(1-\bar s)$. The closed form at $s_c$ is $(1-s_c)(\bar a-\pi)=\bar a(1-s_c)-\pi(1-s_c)$, so the difference is $\pi(\bar s-s_c)$. Since $E[a_is_i]=\bar a\bar s+\mathrm{Cov}(a_i,s_i)$, $s_c=\bar s+\mathrm{Cov}/\bar a$ and $\bar s-s_c=-\mathrm{Cov}/\bar a$. A numerical check on 2{,}000 random banks agrees with the identity to machine precision, and a simulation of the report process agrees within sampling error. \hfill$\square$

\medskip\noindent\textbf{Proof of Proposition 6.} For a naive requester, accuracy equals the probability that the report is correct. Given $(x,\text{stance})$, the report $S$ is correct with posterior probability $P(S\text{ correct}\mid x)=\ell(x)\pi/[\ell(x)\pi+(1-\pi)]$, which is at least $1/2$ if and only if $\ell(x)\pi/(1-\pi)\ge1$. The rule that reports the more probable action for every $(x,\text{stance})$ maximizes the probability of being correct among all rules that depend on $(x,\text{stance})$, and is the unique maximizer up to sets of probability zero. A rule that reports $S$ where $\ell(x)\pi/(1-\pi)<1$ reports the less probable action on that set, and accuracy falls by the posterior difference integrated over it. \hfill$\square$

\medskip\noindent\textbf{Proof of Proposition 7.} Let the report be $r\in\{S,\text{not }S\}$. With probability $1-s$ the reviewer reports a binary signal that equals the correct action with probability $a$; with probability $s$ it reports $S$. The experiment with deference $s$ is the non-deferential experiment $E_0$ followed by a garbling that replaces the signal by the constant $S$ with probability $s$. By Blackwell~\cite{blackwell1953equivalent}, for every decision problem the value of $E_s$ is weakly below that of $E_0$, and the same argument orders $E_s$ and $E_{s'}$ for $s<s'$. The inequality is strict when the signal would have changed the decision. \hfill$\square$

\medskip\noindent\textbf{Proof of Proposition 8.} The blinded reviewer does not defer, so its value is $a-\delta-\pi$. It exceeds $(1-s)(a-\pi)$ if and only if $a-\delta-\pi>(1-s)(a-\pi)$, that is, if and only if $\delta<s(a-\pi)$. If $a\le\pi$ the right side is nonpositive and the inequality fails for $\delta\ge0$. The willingness to pay for a non-deferential version of the same reviewer, in units of the requester's accuracy, is the difference of values, $(a-\pi)-(1-s)(a-\pi)=s(a-\pi)$. \hfill$\square$

\medskip\noindent\textbf{Proof of Proposition 9.} $V_1-V_2=(1-s_1)(a_1-\pi)-(1-s_2)(a_2-\pi)=N+\pi(s_1-s_2)$ with $N=(1-s_1)a_1-(1-s_2)a_2$. This is linear in $\pi$, so it is nonnegative on $[0,1]$ if and only if it is nonnegative at both endpoints. At $\pi=0$ it equals $(1-s_1)a_1-(1-s_2)a_2$; at $\pi=1$ it equals $-(1-s_1)(1-a_1)+(1-s_2)(1-a_2)$. \hfill$\square$
"""

# ----------------------------------------------------------------------------- appendix B..G from the docx
out = []
tcount = -1
LET = {"Appendix B.": "B", "Appendix C.": "C", "Appendix D.": "D", "Appendix E.": "E", "Appendix F.": "F", "Appendix G.": "G"}
k = 0
started = False
while k < len(seq):
    typ, st, x = seq[k]
    if typ == "p" and st.startswith("Heading") and x.startswith("Appendix B"):
        started = True
    if not started:
        k += 1; continue
    if typ == "p" and st.startswith("Heading"):
        out.append("\\section{" + esc(re.sub(r"^Appendix [A-G]\. ", "", x)) + "}")
    elif typ == "p" and st == "Table Caption":
        cap = re.sub(r"^Table [A-G]\d+\. ", "", x)
        nxt = seq[k + 1][2]; idx = [i for i, t in enumerate(d.tables) if t._tbl is nxt._tbl][0]
        out.append(table_tex(nxt, esc(cap), SPEC.get(idx), SIZE[idx]))
        k += 1
    elif typ == "p" and st == "Compact":
        out.append("\\begin{quote}\\small " + esc(x) + "\\end{quote}")
    elif typ == "p":
        out.append(prose(x) + "\n")
    k += 1
APP_BG = "\n".join(out)

# ----------------------------------------------------------------------------- appendix H: post-main-run experiments
f2 = lambda v: "--" if not np.isfinite(v) else f"{v:.2f}"
f3 = lambda v: "--" if not np.isfinite(v) else f"{v:.3f}"
NM = {"Haiku4.5": "Haiku 4.5", "Qwen3.6-27B": "Qwen3.6-27B", "Qwen3.8-27B": "Qwen3.8-27B"}
H = []
H.append(r"""
\section{Experiments added after the main run}
\label{app:extra}
The two experiments below were designed after the main-run results were known (Section~VI of the paper). The frozen files of the main run were not modified; the added code is in \texttt{extra/extra\_run.py} and \texttt{analysis\_extra.py}, and every departure is recorded in \texttt{deviation\_log.md} of the replication package.

\subsection{Design}
\emph{Conditions.} Haiku~4.5 (a stratified sample of 300 items, 50 per domain, tiers in proportion, seed 2026102301; 3{,}300 calls per condition), Qwen3.6-27B and Qwen3.8-27B (600 items; 6{,}600 calls per condition), each with the API reasoning switch on and off (\texttt{reasoning.enabled}). Channels per item (11): stance-free $\times3$, neutral sentence $\times1$, stance against the evidence at four levels, and the three disclosed-accuracy levels; the rotation and the stance-toward-gold channels were not run. Both conditions use a 2{,}048-token limit, the frozen long-form parser, the frozen system prompt and temperature 1.0. Gemini~3.1~Pro (\texttt{google/gemini-3.1-pro-preview}) was run once with all 21 channels on 600 items (12{,}600 calls) at the endpoint default, because its reasoning cannot be disabled. Call order was shuffled with seed 20261023 and the run is resumable. In total 45{,}600 calls were made, 0 remained unresolved, and the billed cost was US\$170.56.

\emph{Estimation.} \texttt{analysis\_extra.py} imports the estimators of \texttt{analysis.py} unchanged. For each on/off pair the items are resampled once (2{,}000 draws, seed 20260101) and the same resample is applied to both conditions, so $\Delta=\text{on}-\text{off}$ has a paired percentile interval. Because the conditional set depends on the condition, $\Delta$ is also computed on the items answered correctly in the reference run under both conditions (the intersection). $\Delta s^{*}$ is called directional if its interval excludes zero and equivalent if the interval lies within $\pm0.05$; there was no directional hypothesis. Truncated and unparseable answers are missing in the primary analysis and errors in the sensitivity analysis.
""")

# pilot table from the pilot logs
rows = [["Condition", "Calls", "Parse fail.", "Truncated", "Mean reasoning tokens", "US\\$ per call"]]
pil = pd.concat([pd.DataFrame([json.loads(l) for l in open(f"{X}/data/{f}")]) for f in ("pilot.jsonl", "pilot2.jsonl") if os.path.exists(f"{X}/data/{f}")])
pil["fail"] = pil.parser_branch.eq("none"); pil["trunc"] = pil.finish_reason.eq("length")
g = pil.groupby("model").agg(n=("key", "size"), fail=("fail", "mean"), trunc=("trunc", "mean"), rt=("reasoning_tokens", "mean"), cost=("cost", "mean"))
for m, r in g.iterrows():
    rows.append([esc(m.replace("|", " | ")), str(int(r.n)), f"{r.fail:.2f}", f"{r.trunc:.2f}", f"{r.rt:.0f}", f"{r.cost:.4f}"])
H.append("\\subsection{Pilot used to choose the models}\nThe pilot sent a fixed-shuffle prefix of each condition (1{,}450 calls, US\\$3.5). Before it, one arithmetic question was sent with the reasoning switch on and off to 14 candidate models. Sonnet~5.5, Gemini~3.1~Pro and Gemini~3.5~Flash returned ``Reasoning is mandatory for this endpoint and cannot be disabled''; the older Qwen3 models (14B, 32B, 30B-A3B) still emitted reasoning tokens when it was switched off; Haiku~4.5, Qwen3.5/3.6/3.7/3.8, GLM-4.7-flash and DeepSeek-V3.2 honored the switch. Qwen3.5-9B truncated at the token limit on 91\\% of reasoning-on calls and Qwen3.5-27B on 9\\%, so Qwen3.6-27B and Qwen3.8-27B were used instead.\n")
H.append(mk_table(rows, "Pilot calls by condition (the 400 Qwen3.6/3.8 calls come from the second pilot batch).", "lccccc", "footnotesize"))

# full on/off deltas
dl = pd.read_csv(f"{R}/extra/delta_onoff.csv"); di = pd.read_csv(f"{R}/extra/delta_intersection.csv"); de = pd.read_csv(f"{R}/extra_err/delta_onoff.csv")
KEYS = [("a", "$a$"), ("nu", r"$\nu$"), ("rho", r"$\rho$"), ("f_pref", "$f$ pref"), ("f_weak", "$f$ weak"), ("f_strong", "$f$ strong"), ("f_disclaimer", "$f$ disc."),
        ("s_star", "$s^{*}$"), ("s_mix", r"$s_{\mathrm{mix}}$"), ("slope", "Evidence slope"), ("acc_slope", "Accuracy slope"), ("disclaimer_effect", "Disclaimer effect")]
def delta_rows(df):
    rows = [["Model", "Items", "Metric", "Off", "On", r"$\Delta$ (on $-$ off)", "95\\% interval"]]
    for b in ["Haiku4.5", "Qwen3.6-27B", "Qwen3.8-27B"]:
        g = df[df.model == b].set_index("metric")
        for k, lab in KEYS:
            r = g.loc[k]
            rows.append([NM[b], str(int(r["items"])), lab, f3(r.off), f3(r.on), f"{r.delta:+.3f}", f"[{r.lo:+.3f}, {r.hi:+.3f}]"])
    return rows
H.append("\\subsection{Reasoning on versus off: all metrics}\n")
H.append(mk_table(delta_rows(dl), "Reasoning on versus off, primary analysis (missing excluded). Paired 95\\% bootstrap intervals, 2{,}000 draws.", "llcccrr", "scriptsize"))
H.append(mk_table(delta_rows(di), "The same comparison on the items answered correctly in the reference run under both conditions (298, 282 and 241 items).", "llcccrr", "scriptsize"))
rows = [["Model", "$\\Delta s^{*}$ primary [95\\% CI]", "$\\Delta s^{*}$ missing as error [95\\% CI]", "Direction (primary)", "Equivalent within $\\pm0.05$"]]
for b in ["Haiku4.5", "Qwen3.6-27B", "Qwen3.8-27B"]:
    p = dl[(dl.model == b) & (dl.metric == "s_star")].iloc[0]; e = de[(de.model == b) & (de.metric == "s_star")].iloc[0]
    rows.append([NM[b], f"{p.delta:+.3f} [{p.lo:+.3f}, {p.hi:+.3f}]", f"{e.delta:+.3f} [{e.lo:+.3f}, {e.hi:+.3f}]", esc(str(p.direction_s_star)), esc(str(p.equivalent_s_star))])
H.append(mk_table(rows, "Sensitivity of $\\Delta s^{*}$ to the treatment of truncated and unparseable answers.", "lcccc", "footnotesize"))

cv = pd.read_csv(f"{R}/extra/coverage.csv")
rows = [["Condition", "Calls", "Parse fail.", "Truncated", "Reasoning tokens", "Completion tokens", "US\\$", "Providers (1\\% or more)"]]
for _, r in cv.iterrows():
    rows.append([esc(r.model.replace("|", " | ")), str(int(r.calls)), f"{r.parse_fail:.3f}", f"{r.truncated:.3f}", f"{r.mean_reasoning_tokens:.0f}", f"{r.mean_completion_tokens:.0f}", f"{r.cost_usd:.2f}", esc(str(r.providers))])
H.append("\\subsection{Coverage, truncation, tokens and providers}\n")
H.append(mk_table(rows, "Calls, parse failures, truncation at 2{,}048 tokens, mean tokens per call, billed cost and serving providers.", "lrrrrrrp{4cm}", "scriptsize"))

gm = pd.read_csv(f"{R}/extra/Gemini3.1-Pro/model_metrics.csv").set_index("metric")
rows = [["Metric", "Estimate", "95\\% interval"]]
for k, lab in [("a", "$a$"), ("nu", r"$\nu$"), ("rho", r"$\rho$"), ("f_pref", "$f$ pref"), ("f_weak", "$f$ weak"), ("f_strong", "$f$ strong"), ("f_disclaimer", "$f$ disc."),
               ("acc_20", "ACC 20"), ("acc_50", "ACC 50"), ("acc_80", "ACC 80"), ("s_star", "$s^{*}$"), ("rot_a", "$a$ rotated"), ("rot_f", "$f(e^{*})$ rotated"), ("Pw_pref", "$P_w$"), ("Pa_pref", "$P_a$")]:
    r = gm.loc[k]; rows.append([lab, f3(r.est), f"[{f3(r.lo)}, {f3(r.hi)}]"])
H.append("\\subsection{Gemini 3.1 Pro}\nGemini~3.1~Pro answered the stance-free reference run correctly and never chose the unsupported option under any stance. All intervals have zero width.\n")
H.append(mk_table(rows, "Gemini~3.1~Pro, all 21 channels, 600 items (main-run estimators).", "lcc", "footnotesize"))

dev = open(os.path.join(HERE, "..", "deviation_log.md")).read()
def md(l):
    parts = re.split(r"`([^`]*)`", l.lstrip("- "))
    return "".join(esc(p) if i % 2 == 0 else "\\texttt{" + esc(p).replace("\\_", "\\_\\allowbreak{}").replace("/", "/\\allowbreak{}") + "}" for i, p in enumerate(parts))
H.append("\\subsection{Deviation log}\n" + "\n".join("\\noindent " + md(l) + "\n" for l in dev.splitlines() if l.strip() and not l.startswith("#")))

PRE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.6in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,longtable}
\usepackage{cite}
\sloppy
\counterwithin{table}{section}
\renewcommand{\thetable}{\thesection\arabic{table}}
\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}
\begin{document}
\begin{center}
{\Large\bfseries Supplementary Material\\[3pt] \large Deference or Noise? A Baseline-Corrected Protocol for Auditing Stance Sensitivity in LLM Reviewers}\\[6pt]
Ook Lee\\ Department of Information System, Hanyang University, Seoul, Korea
\end{center}
\medskip
\noindent\textbf{Contents.} A.~Proofs of the propositions. B.~The item bank. C.~Prompts. D.~Models and call settings. E.~Complete results by model. F.~Robustness details. G.~Pilot study, power and human review. H.~Experiments added after the main run.
"""
BIB = r"""
\begin{thebibliography}{1}
\bibitem{blackwell1953equivalent}
D.~Blackwell, ``Equivalent comparisons of experiments,'' \emph{Ann. Math. Statist.}, vol.~24, no.~2, pp. 265--272, 1953.
\end{thebibliography}
\end{document}
"""
open(os.path.join(HERE, "supp.tex"), "w").write(PRE + "\\appendix\n" + PROOFS + APP_BG + "\n".join(H) + BIB)
print("written")
