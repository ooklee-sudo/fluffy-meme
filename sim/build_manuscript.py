"""Assemble manuscript/manuscript_draft.md from the section files, fill tables and figures, run consistency checks,
and convert to .docx with pandoc.   python3 -I sim/build_manuscript.py"""
import re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from section5_tables import TABLES

M = ROOT / "manuscript"
ORDER = ["00_front.md", "01_introduction.md", "02_literature.md", "03_model.md", "04_analysis.md", "05_evidence.md", "06_discussion.md", "07_references.md", "A_appendix.md"]

FIG = {
 "FIG1": ("fig1_threshold.png", "**Figure 1.** *The firm's count threshold falls as errors become more harmful. Optimal number of errors after which the firm hands the task to a person (Proposition 1) as a function of the probability $\\theta_w$ that an error leads to a wrong output, for two costs of a wrong output ($F = 60$ and $100$). Hand-off cost $H = 40$; other costs are illustrative. Horizontal bars mark the estimated $\\theta_w$ of each agent after a misleading message in customer service; the ends of each bar are the additive and the model-consistent estimates (Section 5.3). For GPT-6.1-terra $\\theta_w$ is indistinguishable from zero and no count rule is warranted. The number of errors is capped at 12 in the plot.*"),
 "FIG2": ("fig2_portfolio.png", "**Figure 2.** *The best combination of controls as the cost of reaching a person varies. Best portfolio as the cost $H$ of handing a task to a person and the fixed cost $K$ of verifying outputs vary (Proposition 3). Colors give the escalation policy (E: always hand off; C: count rule; N: never hand off); hatching marks that output verification is adopted. Verification detects a derailed output with probability 0.8 and turns the cost of an undetected wrong output (100) into a repair cost (30). Probability that an error derails the task: $\\theta_w = 0.12$ (the estimate for Claude Sonnet 5.5). Costs are illustrative; verification was not manipulated in the experiments.*"),
 "FIG3": ("fig3_average_wait.png", "**Figure 3.** *A rule based on the observed wait hands off too many tasks. (a) Share of tasks handed to a person under the system optimum and under a rule that treats the average observed wait as the price of a hand-off, as the arrival rate of tasks grows; one reviewer with service rate 1 and delay cost 10 per unit of time (Proposition 4). (b) Cost of the average-wait rule relative to the system optimum when the same total capacity is split across 1, 2, 5, or 10 reviewers (Allen–Cunneen approximation with arrival variability equal to 1, queueing delay only). The curves are not smooth because the number of errors at which the rule hands off is an integer. Pooling raises the loss in most but not all cases: averaged over arrival rates of 2 or more, the loss is 11.9%, 13.7%, 16.7%, and 19.2% for 1, 2, 5, and 10 reviewers, and it exceeds the one-reviewer loss at 94% of the arrival rates tried. $\\theta_w = 0.29$, $F = 100$, reviewer working cost $h = 20$; illustrative.*"),
 "FIG4": ("fig4_two_channels.png", "**Figure 4.** *What a misleading tool message does. Customer service, misleading message versus no injected error. (a) Share of runs in which the agent transfers the task to a person. (b) Probability that a misleading message leads to a self-transfer ($\\theta_h$) or to a wrong output ($\\theta_w$). Dots and lines: model-consistent split with 95% task-clustered bootstrap intervals; open diamonds: additive split (Section 5.3). For GPT-6.1-terra almost all of the fall in success is self-transfer; for Claude Sonnet 5.5 it is wrong output; for DeepSeek-V3.1 the split of the wrong-output channel depends on the estimator. The Llama agents are omitted because their control success is too low to separate the channels.*"),
}


def build():
    text = "\n\n".join((M / f).read_text().strip() for f in ORDER) + "\n"
    for k, (img, cap) in FIG.items():
        text = text.replace("{{" + k + "}}", f"![]({'../figures/' + img}){{width=100%}}\n\n{cap}")
    for k in ("OBS", "SUCCESS", "ARMS", "DECOMP_MIS", "BEHAV", "NSTAR"):
        text = text.replace("{{" + k + "}}", TABLES[k])
    text = text.replace("{{TA1}}", TABLES["DECOMP_TRA"] + "\n\n*Table A1. Customer service, transient failure. Same definitions as Table 4.*")
    out = M / "manuscript_draft.md"
    out.write_text(text)
    return text, out


def checks(text):
    problems = []
    if "{{" in text: problems.append("unresolved placeholders: " + ", ".join(sorted(set(re.findall(r"\{\{(\w+)\}\}", text)))))
    for bad in ("0.39", "Manuscript (total", "ISR", "submitted manuscript"):
        if bad in text: problems.append(f"stale string present: {bad!r}")
    for must in ("80,036", "11,352", "0.40", "0.74"):
        if must not in text: problems.append(f"missing key number {must}")
    body = text.split("## References")[0]
    for n in range(1, 5):
        if f"Figure {n}" not in body: problems.append(f"Figure {n} not referenced in text")
        if f"**Figure {n}.**" not in text: problems.append(f"Figure {n} caption missing")
    for n in range(1, 7):
        if not re.search(rf"\*Table {n}\.", text): problems.append(f"Table {n} caption missing")
        if not re.search(rf"Table {n}\b", re.sub(rf"\*Table {n}\..*?\*", "", body, flags=re.S)): problems.append(f"Table {n} not referenced in text")
    for n in range(1, 5):
        if f"Proposition {n}" not in text: problems.append(f"Proposition {n} missing")
    # stray notation: 'd' as delay cost, Korean characters, status tags
    if re.search(r"[가-힣]", text): problems.append("Korean characters present")
    for tag in ("[Status", "[증명]", "[수치]", "[TODO"):
        if tag in text: problems.append(f"draft tag present: {tag}")
    # every cited author-year should be in the reference list
    refs = text.split("## References")[1].split("## Appendix A")[0]
    cites = set(re.findall(r"([A-Z][A-Za-zü]+(?: and [A-Z][A-Za-zü]+)?(?: et al\.)?) \(?((?:19|20)\d\d)\)?", body))
    missing = []
    for who, yr in sorted(cites):
        first = who.split(" and ")[0].replace(" et al.", "")
        if yr not in refs or first not in refs: missing.append(f"{who} {yr}")
    if missing: problems.append("citations without a reference entry: " + "; ".join(missing))
    return problems


if __name__ == "__main__":
    text, out = build()
    words = len(re.sub(r"```.*?```|\|.*\|", "", text, flags=re.S).split())
    print(f"wrote {out} ({len(text)} chars, about {words} words outside tables)")
    pr = checks(text)
    print("consistency checks:", "all passed" if not pr else "")
    for p in pr: print("  -", p)
    r = subprocess.run(["pandoc", str(out), "-o", str(M / "manuscript_draft.docx"), "--from", "markdown+tex_math_dollars+pipe_tables+implicit_figures",
                        "--resource-path", str(M)], capture_output=True, text=True)
    print("docx:", "ok" if r.returncode == 0 else r.stderr[:300])
