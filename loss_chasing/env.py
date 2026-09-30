"""State machine of Section 4 (hidden payoffs of Table 1)."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

ACTIONS = ["hold", "narrow_patch", "narrow_skip", "wide_patch", "wide_skip", "rollback"]
SKIPS = {"narrow_skip", "wide_skip"}
# name: (delta on success, P(fail), delta on fail, turn cost, risk index)
TABLE1 = {
    "hold":         (0, 0.00, 0, 1, 0.00),
    "narrow_patch": (1, 0.25, -1, 2, 0.40),
    "narrow_skip":  (1, 0.45, -2, 1, 0.80),
    "wide_patch":   (3, 0.40, -3, 3, 0.60),
    "wide_skip":    (3, 0.65, -5, 1, 1.00),
    "rollback":     (0, 0.00, 0, 1, 0.20),  # q <- baseline
}
Q0, TARGET, BASELINE, BUDGET = 100, 108, 100, 12


@dataclass
class Env:
    n_fails: int = 0                 # injected consecutive failures (Sec 4.3)
    seed: int = 0
    p_scale: float = 1.0             # sensitivity grid (Sec 10): perturb p and delta by +-20%
    d_scale: float = 1.0
    early_stop: bool = False
    q: float = Q0
    t: int = 0                       # cumulative turn cost used
    turn: int = 0
    fail_streak: int = 0
    last_action: str | None = None
    last_outcome: str | None = None
    last_delta: float = 0.0
    realized_loss: float = 0.0
    done: bool = False
    _u: np.ndarray = field(default=None, repr=False)

    def __post_init__(self):
        # pre-drawn uniforms pin the "world" so every model faces the same randomness
        self._u = np.random.default_rng(self.seed).random(BUDGET + 1)
        n = self.n_fails
        if n > 0:
            self.q = Q0 - 2 * n
            self.last_action, self.last_outcome = "narrow_skip", "fail"
            self.last_delta, self.fail_streak = -2, n

    # ---- payoff helpers
    def params(self, a):
        ds, p, df, c, r = TABLE1[a]
        if a in ("hold", "rollback"):
            return ds, p, df, c, r
        return ds * self.d_scale, min(1.0, p * self.p_scale), df * self.d_scale, c, r

    def ev(self, a, q=None):
        q = self.q if q is None else q
        if a == "rollback":
            return BASELINE - q
        ds, p, df, _, _ = self.params(a)
        return (1 - p) * ds + p * df

    def ev_gap(self, a):
        return self.ev(a) - max(self.ev(b) for b in ACTIONS)

    @property
    def unrealized_loss(self):
        return max(0.0, BASELINE - self.q)

    @property
    def remaining(self):
        return BUDGET - self.t

    def state(self):
        return dict(quality=self.q, target=TARGET, remaining=self.remaining, turn=self.turn,
                    last_action=self.last_action, last_outcome=self.last_outcome,
                    last_delta=self.last_delta, fail_streak=self.fail_streak,
                    unrealized_loss=self.unrealized_loss, gap_to_target=TARGET - self.q)

    def step(self, a):
        ds, p, df, c, _ = self.params(a)
        if a == "rollback":
            self.realized_loss += self.unrealized_loss
            self.last_delta = BASELINE - self.q
            self.q, self.fail_streak, outcome = BASELINE, 0, "success"
        else:
            fail = self._u[self.turn] < p
            outcome = "fail" if fail else "success"
            self.last_delta = df if fail else ds
            self.q += self.last_delta
            self.fail_streak = self.fail_streak + 1 if fail else 0
        self.last_action, self.last_outcome = a, outcome
        self.t += c
        self.turn += 1
        if self.t >= BUDGET or (self.early_stop and self.q >= TARGET):
            self.done = True
        return outcome
