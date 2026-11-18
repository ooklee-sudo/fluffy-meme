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
 "FIG1": ("fig1_threshold.png", "**Figure 1.** *The count threshold falls as wrong outputs become more costly. Optimal number of errors after which the firm hands the task to a person (Proposition 1) as a function of the probability $\\theta_w$ that an error leads to a wrong output, for three costs of a wrong output (\\$12.35, \\$22, and \\$44, that is 1.4, 2.5, and 5 times the cost of a hand-off $H = \\$8.82$; Appendix C). Horizontal bars mark the estimated $\\theta_w$ of each agent after a misleading message in customer service; the ends of each bar are the additive and the model-consistent estimates (Section 5.3). For GPT-6.1-terra $\\theta_w$ is indistinguishable from zero and no count rule is warranted. Error rate per step 0.014, $\\theta_h = 0.05$; the number of errors is capped at 12 in the plot.*"),
 "FIG2": ("fig2_portfolio.png", "**Figure 2.** *The best combination of controls as the cost of reaching a person varies. Best portfolio as the cost $H$ of handing a task to a person and the cost $K$ of verifying one output vary (Proposition 3), (a) without self-transfer and (b) with frequent self-transfer ($\\theta_h = 0.5$). Colors give the escalation policy (E: always hand off; C: count rule that binds within ten errors; N: no hand-off in practice); hatching marks that output verification is adopted. Verification detects a derailed output with probability 0.8 and turns the cost of an undetected wrong output (\\$44) into a repair cost (\\$8.82). $\\theta_w = 0.12$ and error rate 0.014 per step (Claude Sonnet 5.5-like). A typical human-handled contact costs \\$6--13.5, and a check by a language-model judge costs cents. Verification is adopted in {{F2_NV0}} of {{F2_N}} cases in (a) and in {{F2_NV1}} in (b). Verification was not manipulated in the experiments.*"),
 "FIG3": ("fig3_average_wait.png", "**Figure 3.** *A rule based on the observed wait hands off too many tasks. (a) Share of tasks handed to a person under the system optimum and under a rule that treats the average observed wait as the price of a hand-off, as the arrival rate of tasks grows; one reviewer with service rate 1 (Proposition 4). (b) Extra cost of the average-wait rule relative to the system optimum when the same total capacity is split across 1, 2, 5, or 10 reviewers (Allen–Cunneen approximation with arrival variability equal to 1, queueing delay only). The curves are not smooth because the number of errors at which the rule hands off is an integer. The agent is DeepSeek-V3.1-like ($\\theta_w = 0.17$, $\\theta_h = 0.27$, error rate 0.055 per step), a wrong output costs \\$44, a hand-off costs \\$8.82, and delay costs \\$2.69 per service time (Appendix C). Averaged over arrival rates of 2 or more, the loss is {{F3_MEANS}} for 1, 2, 5, and 10 reviewers; it is below the one-reviewer loss at most arrival rates because pooling delays its onset.*"),
 "FIG4": ("fig4_two_channels.png", "**Figure 4.** *What a misleading tool message does. Customer service, misleading message versus no injected error. (a) Share of runs in which the agent transfers the task to a person. (b) Probability that a misleading message leads to a self-transfer ($\\theta_h$) or to a wrong output ($\\theta_w$). Dots and lines: model-consistent split with 95% task-clustered bootstrap intervals; open diamonds: additive split (Section 5.3). For GPT-6.1-terra almost all of the fall in success is self-transfer; for Claude Sonnet 5.5 it is wrong output; for DeepSeek-V3.1 the split of the wrong-output channel depends on the estimator. The Llama agents are omitted because their control success is too low to separate the channels.*"),
}


def numbers():
    import json
    fd = json.load(open(ROOT / "sim/f_domains.json"))["breakeven"]
    pw = json.load(open(ROOT / "sim/power_airline.json"))
    n = json.load(open(ROOT / "figures/figure_numbers.json"))
    f2, f3 = n["fig2"], n["fig3"]
    m = f3["mean_loss_lam_ge_2"]; mx = f3["max_loss"]
    lst = lambda d: ", ".join(f"{d[k]:.1f}%" for k in ("1", "2", "5")) + f", and {d['10']:.1f}%"
    d22 = f3["max_loss_deepseek_F22"]; son = f3["max_loss_sonnet_F44"]
    return {"F2_Z0": f"{f2['z_inf']['0.0']:.3f}", "F2_Z1": f"{f2['z_inf']['0.5']:.3f}", "F2_NV0": str(f2["n_with_verification"]["0.0"]),
            "F2_NV1": str(f2["n_with_verification"]["0.5"]), "F2_N": str(f2["n_cells"]),
            "PW_GPT": f"{pw['gpt61terra']['mde_now']:.2f}", "PW_SON": f"{pw['sonnet55']['mde_now']:.2f}", "PW_DS": f"{pw['deepseek']['mde_now']:.2f}", "PW_GPT4": f"{pw['gpt61terra']['mde_by_reps']['4']:.2f}", "PW_SON4": f"{pw['sonnet55']['mde_by_reps']['4']:.2f}", "BE_AIR5": f"{100 * fd['5']['p_severe_airline']:.1f}%", "BE_AIR3": f"{100 * fd['3']['p_severe_airline']:.1f}%", "F3_MEANS": lst(m), "F3_PEAKS": lst(mx),
            "F3_F22": f"{d22['1']:.1f}% with one reviewer and {d22['10']:.1f}% with ten", "F3_SON": f"{max(son.values()):.1f}%"}


def build():
    text = "\n\n".join((M / f).read_text().strip() for f in ORDER) + "\n"
    for k, (img, cap) in FIG.items():
        text = text.replace("{{" + k + "}}", f"![]({'../figures/' + img}){{width=100%}}\n\n{cap}")
    for k in ("OBS", "SUCCESS", "ARMS", "DECOMP_MIS", "BEHAV", "NSTAR", "DOMAIN_TH", "DOMAIN_N", "AIR_UPPER", "AIR_UPPER_N", "CALIB", "SENS", "SONNET_N", "BE10", "BE5", "BE3", "BE2"):
        text = text.replace("{{" + k + "}}", TABLES[k])
    text = text.replace("{{TA1}}", TABLES["DECOMP_TRA"] + "\n\n*Table A1. Customer service, transient failure. Same definitions as Table 4.*")
    for k, v in numbers().items(): text = text.replace("{{" + k + "}}", v)
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
    for n in range(1, 9):
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
