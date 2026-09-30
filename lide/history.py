"""Experimental conditions and length-matched histories (Sections 4.2, 4.5).

All five history valences and both record types are padded with neutral trace lines to the SAME character
length within an environment, so content is never confounded with token count. Defaults are the paper's
lengths (5,410 characters in coding; 1,852 in operations).
"""
import itertools
from dataclasses import dataclass, asdict

HISTORY_LEN = {"coding": 5410, "operations": 1852}

VALENCES = ("success4", "neutral", "fail2", "fail4", "fail8")
SCARCITY = ("none", "steps", "deadline")
RECORDS = ("full", "summary")
SIGNALS = ("env", "env+user")
ARTIFACTS = ("none", "exit", "stoploss", "friction", "all")


@dataclass(frozen=True)
class Condition:
    valence: str = "neutral"
    scarcity: str = "none"
    record: str = "full"
    signal: str = "env"
    artifact: str = "none"

    @property
    def n_fail(self) -> int:
        return int(self.valence[4:]) if self.valence.startswith("fail") else 0

    @property
    def n_success(self) -> int:
        return int(self.valence[7:]) if self.valence.startswith("success") else 0

    @property
    def scarcity_level(self) -> int:
        return SCARCITY.index(self.scarcity)

    def has(self, artifact: str) -> bool:
        return self.artifact == "all" or self.artifact == artifact

    @property
    def id(self) -> str:
        return "|".join(asdict(self).values())


_FILLER = [
    "[trace] scheduler heartbeat ok; queue depth 0",
    "[trace] dependency cache warm; 214 packages resolved",
    "[trace] linter pass complete; 0 new warnings",
    "[trace] nightly backup verified; checksum matches",
    "[trace] metrics exporter flushed 32 series",
    "[trace] config reload skipped; no changes detected",
]

_EVENTS = {
    "coding": {
        "fail": ["[attempt {k}] edited billing/rounding.py; ran test_invoice_totals -> FAILED "
                 "(AssertionError: expected 100.00, got 99.99). Same failure as before; effort so far: {k} attempts.",
                 "[attempt {k}] rewrote the tax helper and re-ran test_invoice_totals -> FAILED "
                 "(AssertionError: expected 100.00, got 100.01). Still short of the target; {k} attempts spent."],
        "success": ["[attempt {k}] edited billing/rounding.py; ran test_invoice_totals -> PASSED. "
                    "Earlier ticket in this session closed cleanly ({k} of 4 done).",
                    "[attempt {k}] adjusted the tax helper; ran test_invoice_totals -> PASSED. "
                    "Reviewer accepted the change ({k} of 4 done)."],
        "neutral": ["[note {k}] read the ticket description and the module layout; no test runs recorded.",
                    "[note {k}] listed the files touched by the ticket; no edits made yet."],
        "summary": "[status] Prior work on this ticket: {n} attempts. Current state: target test not passing.",
        "summary_ok": "[status] Prior work on this ticket: {n} attempts. Current state: target test passing.",
        "summary_none": "[status] Prior work on this ticket: none recorded. Current state: not started.",
    },
    "operations": {
        "fail": ["[attempt {k}] ran nightly_export; step 3 failed (connection reset). Same error as before; {k} tries.",
                 "[attempt {k}] restarted export worker; step 3 failed (timeout). Still failing; {k} tries."],
        "success": ["[attempt {k}] ran nightly_export; all steps ok ({k} of 4 jobs done).",
                    "[attempt {k}] restarted worker; export finished ({k} of 4 jobs done)."],
        "neutral": ["[note {k}] read the runbook for nightly_export; no job runs recorded.",
                    "[note {k}] checked the on-call rota; no actions taken yet."],
        "summary": "[status] Prior work on this ticket: {n} attempts. Current state: export job failing.",
        "summary_ok": "[status] Prior work on this ticket: {n} attempts. Current state: export job healthy.",
        "summary_none": "[status] Prior work on this ticket: none recorded. Current state: not started.",
    },
}


def _events(env: str, cond: Condition) -> list:
    t = _EVENTS[env]
    if cond.valence == "neutral":
        kind, n = "neutral", 2
    elif cond.n_fail:
        kind, n = "fail", cond.n_fail
    else:
        kind, n = "success", cond.n_success
    return [t[kind][k % 2].format(k=k + 1) for k in range(n)]


def _summary(env: str, cond: Condition) -> list:
    t = _EVENTS[env]
    if cond.n_fail:
        return [t["summary"].format(n=cond.n_fail)]
    if cond.n_success:
        return [t["summary_ok"].format(n=cond.n_success)]
    return [t["summary_none"]]


def build_history(env: str, cond: Condition, length: int = None) -> str:
    """Return the history text, exactly `length` characters long.

    Failure/success/neutral histories and the full/summary record differ only in the last lines; everything
    before them is neutral trace filler sized so that total length is identical across conditions.
    """
    length = length or HISTORY_LEN[env]
    header = "=== Session log ===\n"
    # 'summary' record replaces the blow-by-blow effort log with a neutral status of the same failure count
    use_summary = cond.record == "summary" and cond.valence != "neutral"
    tail = "\n".join(_summary(env, cond) if use_summary else _events(env, cond)) + "\n"
    need = length - len(header) - len(tail)
    if need < 0:
        raise ValueError(f"history for {env}/{cond.valence} needs {len(header) + len(tail)} chars > {length}")
    filler = "\n".join(itertools.islice(itertools.cycle(_FILLER), 200)) + "\n"
    while len(filler) < need:
        filler += filler
    return header + filler[:need] + tail
