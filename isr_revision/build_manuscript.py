"""Assemble the IEEE Intelligent Systems manuscript from the section drafts.

    python isr_revision/build_manuscript.py [--template path/to/CS_Mag.docx]

Writes isr_revision/ieee_is_manuscript.md (and .docx if pandoc is available),
numbers citations by first appearance, and checks the word limits
(6,000 words with each figure/table counted as 300; abstract <= 150; <= 20 refs).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
FIG = HERE.parent / "skipver" / "figures"

# Author line and biographies follow the CS magazine template:
#   line: Name, Institution, City, (State), Postal Code, Country
#   bio:  current role and institution; three brief research interests; highest degree,
#         topic, and awarding institution (no year); professional memberships; email.
AUTHORS = [
    {"line": "[Given name] [Family name], Hanyang University, Seoul, 04763, South Korea",
     "bio": ("**[Given name] [Family name]** is a [position] at Hanyang University, Seoul, South Korea. "
             "[Their] current research interests include [interest 1], [interest 2], and [interest 3]. "
             "[Family name] received the [Ph.D.] degree in [field] from [university]. "
             "[He/She/They] [is a member of the IEEE Computer Society]. Contact [him/her/them] at ooklee@hanyang.ac.kr.")},
]

TITLE = "Same Model, Different Shortcuts: How Prompt Layout Steers LLM Operators to Skip Verification"
HEADER = "FEATURE ARTICLE: AUDITING AI OPERATORS"

REFS = {
    "Sculley": 'D. Sculley et al., "Hidden technical debt in machine learning systems," in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 28, 2015.',
    "Jensen": 'M. C. Jensen and W. H. Meckling, "Theory of the firm: Managerial behavior, agency costs and ownership structure," *J. Financial Econ.*, vol. 3, no. 4, pp. 305–360, 1976.',
    "Kellogg": 'K. C. Kellogg, M. A. Valentine, and A. Christin, "Algorithms at work: The new contested terrain of control," *Acad. Manage. Ann.*, vol. 14, no. 1, pp. 366–410, 2020.',
    "Scheurer": 'J. Scheurer, M. Balesni, and M. Hobbhahn, "Large language models can strategically deceive their users when put under pressure," 2023, arXiv:2311.07590.',
    "Jiang": 'H. Jiang and K. Tang, "Why agents compromise safety under pressure," in *Findings Assoc. Comput. Linguistics: ACL 2026*, 2026, arXiv:2603.14975.',
    "Chen": 'H. Chen, Y. Liu, J. Shao, X. Xu, Z. Sun, and W. Hu, "Polished but unresolved: Identifying late-stage pressure states in long-horizon tool-use agents," in *Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP)*, 2026, arXiv:2609.00823.',
    "Horton": 'J. J. Horton, "Large language models as simulated economic agents: What can we learn from Homo silicus?" 2023, arXiv:2301.07543.',
    "Ross": 'J. Ross, Y. Kim, and A. W. Lo, "LLM economicus? Mapping the behavioral biases of LLMs via utility theory," 2024, arXiv:2408.02784.',
    "Belcak": 'P. Belcak et al., "Small language models are the future of agentic AI," 2025, arXiv:2506.02153.',
    "Ong": 'I. Ong et al., "RouteLLM: Learning to route LLMs from preference data," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2025.',
    "Kahneman": 'D. Kahneman and A. Tversky, "Prospect theory: An analysis of decision under risk," *Econometrica*, vol. 47, no. 2, pp. 263–291, 1979.',
    "Thaler": 'R. H. Thaler and E. J. Johnson, "Gambling with the house money and trying to break even: The effects of prior outcomes on risky choice," *Manage. Sci.*, vol. 36, no. 6, pp. 643–660, 1990.',
    "Schweitzer": 'M. E. Schweitzer, L. Ordóñez, and B. Douma, "Goal setting as a motivator of unethical behavior," *Acad. Manage. J.*, vol. 47, no. 3, pp. 422–432, 2004.',
    "Ordonez": 'L. D. Ordóñez, M. E. Schweitzer, A. D. Galinsky, and M. H. Bazerman, "Goals gone wild: The systematic side effects of overprescribing goal setting," *Acad. Manage. Perspect.*, vol. 23, no. 1, pp. 6–16, 2009.',
    "Pezeshkpour": 'P. Pezeshkpour and E. Hruschka, "Large language models sensitivity to the order of options in multiple-choice questions," in *Findings Assoc. Comput. Linguistics: NAACL 2024*, 2024, pp. 2006–2017.',
    "Zheng": 'C. Zheng, H. Zhou, F. Meng, J. Zhou, and M. Huang, "Large language models are not robust multiple choice selectors," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2024.',
}
# Placeholders used in the earlier section drafts.
LEGACY = {"n1": "Pezeshkpour", "n2": "Zheng", "n3": "Kahneman", "n4": "Thaler", "n5": "Schweitzer", "n6": "Ordonez"}

CAPTIONS = {
    1: ("FIGURE 1. The status prompt an operator reads, with the parts that vary across conditions marked "
        "(headline, target in the facts line, turns left, and option order), and the expected quality change of each "
        "action, which the operator does not see. Both test-skipping actions have lower expected value than their "
        "tested counterparts."),
    2: ("FIGURE 2. Share of first decisions that skip tests, by status headline (Claude Haiku 4.5, three turns left, "
        "option order balanced; bars are means over 16 wordings with 95% intervals). Headlines that state the target "
        "(blue) raise skipping whether they are neutral or describe a loss. When the target appears nowhere in the "
        "prompt, the other headlines produce no skipping."),
    3: ("FIGURE 3. The same decisions split by the option listed first. Headlines that state the target raise skipping "
        "mainly when hold or rollback heads the list; when a tested fix is listed first, the model takes it. Listing "
        "the untested wide fix first yields about one-third skipping under every headline."),
}


def section(path: str, heading: str) -> str:
    text = (HERE / path).read_text()
    start = text.index(heading) + len(heading)
    end = text.find("\n---", start)
    return text[start:end].strip()


def figure(n: int, img: str | None) -> str:
    if img and (FIG / img).exists():
        return f"![{CAPTIONS[n]}]({(FIG / img).resolve()})"
    return f"**[{CAPTIONS[n]}]**"


def build() -> tuple[str, dict]:
    R = "ieee_is_remaining.md"
    parts = [
        ("abstract", section(R, "## ABSTRACT")),
        ("intro", section(R, "## (INTRODUCTION, no heading)")),
        ("## A MAINTENANCE TASK WITH A KNOWN RIGHT ANSWER", section(R, "## A MAINTENANCE TASK WITH A KNOWN RIGHT ANSWER")),
        ("fig1", figure(1, "fig1_prompt.png")),
        ("## GOALS, NOT LOSSES", section("ieee_is_goals.md", "## GOALS, NOT LOSSES")),
        ("fig2", figure(2, "fig2_goal.png")),
        ("## OPTION ORDER MATTERS AS MUCH AS WORDING", section("ieee_is_option_order.md", "## OPTION ORDER MATTERS AS MUCH AS WORDING")),
        ("fig3", figure(3, "fig3_order.png")),
        ("## WHAT REDUCES SKIPPING", section("ieee_is_reduces.md", "## WHAT REDUCES SKIPPING")),
        ("## WHICH MODELS SKIP", section("ieee_is_models.md", "## WHICH MODELS SKIP")),
        ("## AUDITING AN LLM OPERATOR BEFORE DELEGATION (SIDEBAR)", section(R, "## SIDEBAR: AUDITING AN LLM OPERATOR BEFORE DELEGATION")),
        ("## LIMITATIONS", section(R, "## LIMITATIONS")),
        ("## CONCLUSION", section(R, "## CONCLUSION")),
    ]
    body = []
    for head, text in parts:
        if head == "abstract":
            body.append(f"**Abstract**—{text}")
        elif head.startswith("##"):
            body.append(f"{head}\n\n{text}")
        else:
            body.append(text)
    md = "\n\n".join(body)

    # Citations: {Name} and legacy [nK] -> numbers by first appearance, set as superscripts.
    md = re.sub(r"\[(n\d)\]", lambda m: "{" + LEGACY[m.group(1)] + "}", md)
    order: list[str] = []
    for name in re.findall(r"\{(\w+)\}", md):
        if name not in order:
            order.append(name)
    unknown = [n for n in order if n not in REFS]
    if unknown:
        raise SystemExit(f"unknown citations: {unknown}")
    num = {n: i + 1 for i, n in enumerate(order)}
    # Merge adjacent callouts like {A}, {B} into one superscript.
    def callout(names):
        ns = sorted(num[x] for x in names)
        runs, start = [], ns[0]
        for prev, cur in zip(ns, ns[1:] + [None]):
            if cur != prev + 1 if cur is not None else True:
                runs.append(str(start) if start == prev else (f"{start},{prev}" if prev == start + 1 else f"{start}–{prev}"))
                start = cur
        return "^" + ",".join(runs) + "^"
    md = re.sub(r"\{(\w+)\}(?:, \{(\w+)\})*", lambda m: callout(re.findall(r"\{(\w+)\}", m.group(0))), md)

    # Template style: callout follows punctuation with no space ("signal.^3^").
    md = re.sub(r" \^([\d,]+)\^([.,;:]?)", r"\2^\1^", md)

    refs = "\n".join(f"{num[n]}. {REFS[n]}" for n in order)
    author_lines = "\n\n".join(a["line"] for a in AUTHORS)
    bios = "\n\n".join(a["bio"] for a in AUTHORS)
    full = (f"*{HEADER}*\n\n# {TITLE}\n\n{author_lines}\n\n{md}\n\n## REFERENCES\n\n{refs}\n\n"
            f"## AUTHOR BIOGRAPHIES\n\n{bios}\n")

    # Word counts.
    def words(s: str) -> int:
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)        # figure captions counted via the 300-word rule
        s = re.sub(r"\*\*\[FIGURE[^\]]*\]\*\*", "", s)
        s = re.sub(r"\^[\d,]+\^", "", s)
        s = re.sub(r"^\|.*\|$", "", s, flags=re.M)          # table counted via the 300-word rule
        return len(re.findall(r"\S+", s))
    abstract = parts[0][1]
    body_no_abs = md.split("\n\n", 1)[1]
    n_fig_tab = 3 + 1
    stats = {
        "abstract": len(abstract.split()),
        "text": words(body_no_abs),
        "figures_tables": n_fig_tab * 300,
        "references": len(order),
    }
    stats["total_with_abstract"] = stats["abstract"] + stats["text"] + stats["figures_tables"]
    return full, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", help="CS magazine .docx template used as the pandoc reference document")
    args = ap.parse_args()
    full, st = build()
    out = HERE / "ieee_is_manuscript.md"
    out.write_text(full)
    print(f"wrote {out}")
    print(f"abstract {st['abstract']} words (limit 150)")
    print(f"text {st['text']} + figures/tables {st['figures_tables']} + abstract {st['abstract']} "
          f"= {st['total_with_abstract']} (limit 6,000)")
    print(f"references {st['references']} (limit 20)")
    if shutil.which("pandoc"):
        cmd = ["pandoc", str(out), "-o", str(HERE / "ieee_is_manuscript.docx")]
        if args.template:
            cmd += ["--reference-doc", args.template]
        subprocess.run(cmd, check=True)
        print(f"wrote {HERE / 'ieee_is_manuscript.docx'}")


if __name__ == "__main__":
    main()
