"""Manuscript numbers next to the balanced-order reruns (Studies 2-5, Haiku 4.5).

    python compare_paper.py --out results/compare_paper.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from analyze import cell_table, contrast, load

R = Path(__file__).parent / "results"

# Manuscript values (percent / percentage points), Tables 5-9.
PAPER = {
    "s2": {12: {"skip": 0.0}, 6: {"skip": 0.5, "loss-gain": -1.5, "neutral-gain": -1.5},
           3: {"skip": 27.2, "loss-gain": -62.9, "neutral-gain": -50.4}},
    "s3": {"skip": 9.7, "loss-gain": -5.2, "neutral-gain": -6.2},
    "s4": {
        False: {"rates": {"neutral": 15.0, "loss": 1.9, "gain": 62.3, "neutral_goal": 69.2, "loss_goal": 32.1},
                "c": [54.2, 30.2, -13.1, -37.1, -60.4, -6.9]},
        True: {"rates": {"neutral": 0.0, "loss": 0.0, "gain": 56.0, "neutral_goal": 31.7, "loss_goal": 23.8},
               "c": [31.7, 23.8, 0.0, -7.9, -56.0, 24.4]},
    },
    "s5": {"rates": {"neutral": 10.2, "loss": 0.0, "gain": 25.0, "neutral_goal": 17.3, "loss_goal": 21.5},
           "c": [7.1, 21.5, -10.2, None, -25.0, None]},
}
C5 = [("Goal effect, neutral text", "neutral_goal", "neutral"),
      ("Goal effect, loss text", "loss_goal", "loss"),
      ("Valence without target (loss − neutral)", "loss", "neutral"),
      ("Valence with target (loss_goal − neutral_goal)", "loss_goal", "neutral_goal"),
      ("Registered contrast (loss − gain)", "loss", "gain"),
      ("Gain − neutral_goal", "gain", "neutral_goal")]


def ci_str(c, lv=95.0):
    lo, hi = c["ci"][lv]
    return f"{100 * c['mean']:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]"


def survives(c):
    lo, hi = c["ci"][99.6]
    return "yes" if lo > 0 or hi < 0 else "no"


def five_frame_section(title, d, paper, rng):
    out = [f"### {title}", "", "Skip rate by frame (%):", "",
           "| Frame | Manuscript | Balanced |", "|---|---|---|"]
    by = d.groupby("frame")["skip"].mean() * 100
    for f in ["neutral", "loss", "gain", "neutral_goal", "loss_goal"]:
        out.append(f"| {f} | {paper['rates'][f]:.1f} | {by.get(f, np.nan):.1f} |")
    out += ["", "| Contrast, pp | Manuscript | Balanced [95% CI] | Excludes 0 at 99.6% |", "|---|---|---|---|"]
    rate, n = cell_table(d)
    for (name, a, b), pv in zip(C5, paper["c"]):
        c = contrast(rate, n, a, b, rng)
        pstr = "–" if pv is None else f"{pv:+.1f}"
        out.append(f"| {name} | {pstr} | {ci_str(c) if c else 'floor'} | {survives(c) if c else '–'} |")
    return out + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    rng = np.random.default_rng(0)
    out = ["# Manuscript vs balanced action order (Haiku 4.5)", ""]

    d2 = load([R / "study2_bal__haiku45__bal.jsonl"])
    out += ["## Study 2: time pressure", "",
            "| Turns left | Skip, manuscript | Skip, balanced | Loss − gain, manuscript | Loss − gain, balanced | Neutral − gain, manuscript | Neutral − gain, balanced |",
            "|---|---|---|---|---|---|---|"]
    for t in (12, 6, 3):
        d = d2[d2.turns_left == t]
        rate, n = cell_table(d)
        p = PAPER["s2"][t]
        cs = [contrast(rate, n, a, "gain", rng) if d.skip.sum() else None for a in ("loss", "neutral")]
        out.append(f"| {t} | {p['skip']:.1f}% | {100 * d.skip.mean():.1f}% | "
                   f"{p.get('loss-gain', '–')} | {ci_str(cs[0]) if cs[0] else 'floor'} | "
                   f"{p.get('neutral-gain', '–')} | {ci_str(cs[1]) if cs[1] else 'floor'} |")
    out.append("")

    d3 = load([R / "study3_bal__haiku45_think__bal.jsonl"])
    rate, n = cell_table(d3)
    p = PAPER["s3"]
    cs = [contrast(rate, n, a, "gain", rng) if d3.skip.sum() else None for a in ("loss", "neutral")]
    d2_3 = d2[d2.turns_left == 3]
    out += ["## Study 3: extended thinking (3 turns left)", "",
            "| | Manuscript | Balanced |", "|---|---|---|",
            f"| Skip, no thinking | 27.2% | {100 * d2_3.skip.mean():.1f}% |",
            f"| Skip, thinking | {p['skip']:.1f}% | {100 * d3.skip.mean():.1f}% |",
            f"| Loss − gain, thinking | {p['loss-gain']:+.1f} | {ci_str(cs[0]) if cs[0] else 'floor'} |",
            f"| Neutral − gain, thinking | {p['neutral-gain']:+.1f} | {ci_str(cs[1]) if cs[1] else 'floor'} |", ""]

    d4 = load([R / "study4_bal__haiku45__s4_bal.jsonl"])
    out += ["## Study 4: goal visibility and valence", ""]
    for hide in (False, True):
        out += five_frame_section("Facts line " + ("without" if hide else "with") + " the target",
                                  d4[d4.hide_target == hide], PAPER["s4"][hide], rng)

    d5 = load([R / "study5_bal__haiku45__s5_bal.jsonl"])
    out += ["## Study 5: expected values shown", ""]
    out += five_frame_section("Expected values shown (target in the facts line)", d5, PAPER["s5"], rng)

    out += ["## Floor checks under balanced order (3 turns left)", ""]
    for f in sorted(R.glob("floor_bal__*.jsonl")):
        d = load([f])
        by = d.groupby("first_listed")["skip"].mean() * 100
        out.append(f"- {f.stem}: skip {100 * d.skip.mean():.1f}% of {len(d)} first choices; by first-listed action: "
                   + ", ".join(f"{k} {v:.1f}%" for k, v in by.items()))
    text = "\n".join(out)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
