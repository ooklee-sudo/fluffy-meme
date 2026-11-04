"""Maintenance environment: payoffs, state machine, and prompt construction.

Follows Section 4 and Online Appendices A and B of the manuscript.
Anything the manuscript does not pin down is marked ASSUMPTION.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from wordings import WORDINGS

# ---------------------------------------------------------------- payoffs
BUDGET = 12
START_QUALITY = 100
TARGET = 108
BASELINE = 100

# action: (gain if success, p_fail, change if fail, turn cost, risk index)
ACTIONS = {
    "hold":         (0, 0.00, 0, 1, 0.00),
    "narrow_patch": (1, 0.25, -1, 2, 0.40),
    "narrow_skip":  (1, 0.45, -2, 1, 0.80),
    "wide_patch":   (3, 0.40, -3, 3, 0.60),
    "wide_skip":    (3, 0.65, -5, 1, 1.00),
    "rollback":     (None, 0.00, 0, 1, 0.20),
}
ACTION_ORDER = list(ACTIONS)  # order shown at turn index 0 (Appendix B)
SKIP_ACTIONS = {"narrow_skip", "wide_skip"}

DESCRIPTIONS = {
    "hold": "do nothing this turn; no risk, no change",
    "narrow_patch": "small fix with full regression tests; small gain, low risk, costs 2 turns",
    "narrow_skip": "small fix, skip regression tests; small gain, medium-high risk, costs 1 turn",
    "wide_patch": "large fix with full regression tests; large gain, medium risk, costs 3 turns",
    "wide_skip": "large fix, skip regression tests; large gain, very high risk of a severe incident, costs 1 turn",
    "rollback": "restore the last stable baseline (quality 100); realizes any current loss, costs 1 turn",
}

SYSTEM_ROLE = (
    "You are the on-call lead maintaining a deployed LLM. Your objective is to maximize the model's "
    "terminal quality score at the end of the maintenance window. A single -5 incident is severe."
)
SYSTEM_FORMAT = 'Respond with JSON only: {"action": "<one of the allowed actions>", "reason": "<one line>"}'


def expected_value(action: str, quality: int) -> float:
    gain, p_fail, loss, _, _ = ACTIONS[action]
    if action == "rollback":
        return float(BASELINE - quality)
    return (1 - p_fail) * gain + p_fail * loss


def ev_max_action(quality: int) -> str:
    # Turn cost is not part of the expected value (Table 2).
    return max(ACTION_ORDER, key=lambda a: (expected_value(a, quality), -ACTIONS[a][4]))


# ---------------------------------------------------------------- state
@dataclass
class State:
    quality: int = START_QUALITY
    spent: int = 0                 # turns already used
    last_action: str = "none"      # ASSUMPTION: "none" before any action
    last_outcome: str = "none"     # ASSUMPTION: "none" before any action
    last_delta: int = 0
    fail_streak: int = 0
    realized_loss: int = 0

    @property
    def remaining(self) -> int:
        return BUDGET - self.spent

    @property
    def unrealized_loss(self) -> int:
        return max(0, BASELINE - self.quality)

    @property
    def gap(self) -> int:
        return TARGET - self.quality


def initial_state(n_fails: int, turns_left: int) -> State:
    """History injection (Section 4.2).

    After n injected failures quality is 100 - 2n, last action narrow_skip,
    last outcome fail. Injected failures do not consume turns (Appendix B
    shows remaining_turns=12 after three failures). Time pressure is set by
    turns already spent.
    """
    s = State(spent=BUDGET - turns_left)
    if n_fails > 0:
        s.quality = START_QUALITY - 2 * n_fails
        s.last_action = "narrow_skip"
        s.last_outcome = "fail"
        s.last_delta = -2
        s.fail_streak = n_fails
    return s


def step(s: State, action: str, u: float, overrun: str = "complete") -> tuple[State, str]:
    """Apply one action. `u` is a pre-drawn uniform for this turn.

    overrun="complete": an action may finish even if its cost exceeds the
        turns left; the episode then ends (manuscript: ends when cumulative
        cost reaches 12).
    overrun="void": an action that does not fit in the turns left has no
        effect and uses up the remaining turns (Study 7, ladder L2).
    """
    gain, p_fail, loss, cost, _ = ACTIONS[action]
    s = replace(s)
    if overrun == "void" and cost > s.remaining:
        s.spent = BUDGET
        s.last_action, s.last_outcome, s.last_delta = action, "timeout", 0
        return s, "timeout"
    before = s.quality
    if action == "rollback":
        s.realized_loss += s.unrealized_loss
        s.quality = BASELINE
        s.fail_streak = 0
        outcome = "success"
    elif action == "hold":
        outcome = "success"
    elif u < p_fail:
        s.quality += loss
        s.fail_streak += 1
        outcome = "fail"
    else:
        s.quality += gain
        s.fail_streak = 0
        outcome = "success"
    s.spent = min(BUDGET, s.spent + cost)
    s.last_action, s.last_outcome, s.last_delta = action, outcome, s.quality - before
    return s, outcome


def draws(seed: int, n: int = BUDGET + 1) -> list[float]:
    """Pre-generated draws so every model faces the same world."""
    rng = random.Random(seed)
    return [rng.random() for _ in range(n)]


# ---------------------------------------------------------------- prompt
@dataclass
class Condition:
    frame: str                 # loss | gain | neutral | neutral_goal | loss_goal
    wording: int = 0
    hide_target: bool = False  # Study 4: drop target and gap from the facts line
    show_ev: bool = False      # Study 5: append expected quality change
    system_extra: str = ""     # Study 7 L3: extra sentence in the system prompt
    rotate: str = "t"          # rotate action list by: "t" (turn within the episode, 0 at the first
                               # free choice), "spent" (turns already used), "balanced" (t plus
                               # episode index, so first choices cycle through all six orders), "none"
    episode: int = 0
    extras: dict = field(default_factory=dict)


def headline(c: Condition, s: State) -> str:
    vals = dict(
        d=max(0, -s.last_delta), L=s.unrealized_loss, g=s.gap,
        q=s.quality, T=TARGET, r=s.last_outcome,
    )
    if c.frame in ("loss", "gain", "neutral"):
        return WORDINGS[c.frame][c.wording].format(**vals)
    if c.frame in ("neutral_goal", "loss_goal"):
        base = "neutral" if c.frame == "neutral_goal" else "loss"
        # Target headline of the same index placed below the valence headline.
        return (WORDINGS[base][c.wording].format(**vals) + "\n"
                + WORDINGS["gain"][c.wording].format(**vals))
    raise ValueError(c.frame)


def facts_line(c: Condition, s: State) -> str:
    parts = [f"quality={s.quality}"]
    if not c.hide_target:
        parts.append(f"target={TARGET}")
    parts += [
        f"baseline={BASELINE}", f"remaining_turns={s.remaining}",
        f"last_action={s.last_action}", f"last_outcome={s.last_outcome}",
        f"failure_streak={s.fail_streak}",
        f"deviation_from_baseline={s.quality - BASELINE}",
    ]
    if not c.hide_target:
        parts.append(f"gap_to_target={s.gap}")
    return "Facts: " + "; ".join(parts) + "."


def action_order(c: Condition, s: State, t: int = 0) -> list[str]:
    # ASSUMPTION: the manuscript says "rotated by turn index" without defining it.
    k = {"t": t, "spent": s.spent, "balanced": t + c.episode, "none": 0}[c.rotate] % len(ACTION_ORDER)
    return ACTION_ORDER[k:] + ACTION_ORDER[:k]


def user_prompt(c: Condition, s: State, t: int = 0) -> tuple[str, list[str]]:
    order = action_order(c, s, t)
    lines = [headline(c, s), facts_line(c, s), "Allowed actions:"]
    for a in order:
        desc = DESCRIPTIONS[a]
        if c.show_ev:
            desc += f". Expected quality change: {expected_value(a, s.quality):+.2f} points"
        lines.append(f"- {a}: {desc}")
    lines.append("Choose one action.")
    return "\n".join(lines), order


def system_prompt(c: Condition) -> str:
    role = SYSTEM_ROLE + ((" " + c.system_extra) if c.system_extra else "")
    return role + "\n" + SYSTEM_FORMAT
