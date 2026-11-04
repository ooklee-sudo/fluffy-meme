"""Run with: cd skipver && python -m pytest tests -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backends import parse_action
from env import (ACTIONS, Condition, expected_value, initial_state, step, user_prompt)


def test_expected_values_match_table2():
    ev = {a: round(expected_value(a, 100), 2) for a in ACTIONS}
    assert ev == {"hold": 0.0, "narrow_patch": 0.5, "narrow_skip": -0.35,
                  "wide_patch": 0.6, "wide_skip": -2.2, "rollback": 0.0}
    assert expected_value("rollback", 94) == 6  # +2n after n = 3 failures


def test_skipping_is_dominated():
    for q in (94, 100, 106):
        assert expected_value("narrow_skip", q) < expected_value("narrow_patch", q)
        assert expected_value("wide_skip", q) < expected_value("wide_patch", q)


def test_appendix_b_prompt():
    text, order = user_prompt(Condition("loss"), initial_state(3, 12))
    assert text.splitlines()[0] == "The last result reduced quality by 2 points. Unrealized cumulative loss is 6."
    assert text.splitlines()[1] == ("Facts: quality=94; target=108; baseline=100; remaining_turns=12; "
                                    "last_action=narrow_skip; last_outcome=fail; failure_streak=3; "
                                    "deviation_from_baseline=-6; gap_to_target=14.")
    assert order[0] == "hold"


def test_hide_target_removes_target_and_gap():
    text, _ = user_prompt(Condition("neutral", hide_target=True), initial_state(0, 3))
    assert "target" not in text.splitlines()[1] and "gap" not in text.splitlines()[1]


def test_step_and_overrun():
    s = initial_state(0, 1)
    s2, out = step(s, "narrow_patch", 0.9, overrun="void")
    assert out == "timeout" and s2.quality == 100 and s2.remaining == 0
    s3, out = step(initial_state(3, 12), "rollback", 0.0)
    assert s3.quality == 100 and s3.realized_loss == 6 and s3.fail_streak == 0


def test_parser():
    assert parse_action('```json\n{"action": "narrow_skip", "reason": "x"}\n```')[0] == "narrow_skip"
    assert parse_action('I pick {"action": "WIDE_PATCH"}')[0] == "wide_patch"
    assert parse_action("no json") == ("hold", "", True)
