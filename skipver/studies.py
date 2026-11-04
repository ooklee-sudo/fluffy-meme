"""Study definitions (Table 1 of the manuscript, plus the proposed Study 7).

A study is a list of Runs. A Run is one model crossed with a grid of
conditions, with a fixed number of episodes per cell.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backends import ModelSpec

W16 = list(range(16))
F3 = ["loss", "gain", "neutral"]
F5 = ["neutral", "loss", "gain", "neutral_goal", "loss_goal"]

M = {
    # Commercial ladder (Studies 1-5). Larger tiers reject temperature and reason by default.
    "haiku45":        ModelSpec("haiku45", "anthropic/claude-haiku-4.5", temperature=0.7),
    "haiku45_t0":     ModelSpec("haiku45_t0", "anthropic/claude-haiku-4.5", temperature=0.0),
    "haiku45_think":  ModelSpec("haiku45_think", "anthropic/claude-haiku-4.5", temperature=None,
                                reasoning={"max_tokens": 2000}, max_tokens=3000),
    "sonnet55":       ModelSpec("sonnet55", "anthropic/claude-sonnet-5.5", temperature=None, max_tokens=4000),
    "opus55":         ModelSpec("opus55", "anthropic/claude-opus-5.5", temperature=None, max_tokens=4000),
    "fable51":        ModelSpec("fable51", "anthropic/claude-fable-5.1", temperature=None, max_tokens=4000),
    # Study 1 open models, local with JSON pre-fill.
    "qwen25_1p5b":    ModelSpec("qwen25_1p5b", "Qwen/Qwen2.5-1.5B-Instruct", backend="local"),
    "smollm2_1p7b":   ModelSpec("smollm2_1p7b", "HuggingFaceTB/SmolLM2-1.7B-Instruct", backend="local"),
    # Study 6 screen (temperature 0.7 where accepted). Reasoning models get a
    # larger output budget: at 200 tokens their original runs came back empty.
    "gemini25fl":     ModelSpec("gemini25fl", "google/gemini-2.5-flash-lite"),
    "gemini31fl":     ModelSpec("gemini31fl", "google/gemini-3.1-flash-lite"),
    "gemma3_12b":     ModelSpec("gemma3_12b", "google/gemma-3-12b-it"),
    "ministral8b":    ModelSpec("ministral8b", "mistralai/ministral-8b-2512"),
    "llama31_8b":     ModelSpec("llama31_8b", "meta-llama/llama-3.1-8b-instruct"),
    "gpt5nano":       ModelSpec("gpt5nano", "openai/gpt-5-nano", temperature=None, max_tokens=4000),
    "qwen3_14b":      ModelSpec("qwen3_14b", "qwen/qwen3-14b", max_tokens=4000),
    # Study 7 additions.
    # Sonnet 5.5 cannot run without reasoning on OpenRouter ("Reasoning is
    # mandatory for this endpoint"), so L1 uses the lowest effort it accepts.
    "sonnet55_min":   ModelSpec("sonnet55_min", "anthropic/claude-sonnet-5.5", temperature=None,
                                reasoning={"effort": "minimal"}, max_tokens=4000),
    "haiku55":        ModelSpec("haiku55", "anthropic/claude-haiku-5.5", temperature=None, max_tokens=4000),
    "mock":           ModelSpec("mock", "mock", backend="mock", extra={"p_skip": 0.2}),
}

STAKES = "Missing the target at the end of the window breaches the service-level agreement."


@dataclass
class Run:
    model: str
    frames: list = field(default_factory=lambda: list(F3))
    wordings: list = field(default_factory=lambda: list(W16))
    turns_left: list = field(default_factory=lambda: [3])
    n_fails: list = field(default_factory=lambda: [0])
    hide_target: list = field(default_factory=lambda: [False])
    show_ev: bool = False
    system_extra: str = ""
    overrun: str = "complete"
    episodes: int = 30
    rotate: str = "t"      # see env.action_order
    tag: str = ""          # distinguishes runs of one model within a study

    def cells(self):
        for f in self.frames:
            for w in self.wordings:
                for t in self.turns_left:
                    for n in self.n_fails:
                        for h in self.hide_target:
                            yield dict(frame=f, wording=w, turns_left=t, n_fails=n, hide_target=h)

    def n_calls(self) -> int:
        return sum(1 for _ in self.cells()) * self.episodes


def study4_runs(model: str, tag: str = "", **kw) -> list[Run]:
    return [Run(model, frames=F5, hide_target=[False, True], tag=tag or "s4", **kw)]


STUDIES: dict[str, list[Run]] = {
    "study1": [
        Run(m, frames=F3, wordings=[0], turns_left=[12], n_fails=[0, 1, 3], episodes=100)
        for m in ["qwen25_1p5b", "smollm2_1p7b", "haiku45", "haiku45_t0"]
    ],
    "study2": [Run(m, turns_left=[12, 6, 3]) for m in ["haiku45", "sonnet55", "opus55", "fable51"]],
    "study3": [Run("haiku45_think")],
    "study4": study4_runs("haiku45"),
    "study5": [Run("haiku45", frames=F5, show_ev=True, tag="s5")],
    "study6_screen": [Run(m) for m in ["gemini25fl", "ministral8b", "llama31_8b", "gemini31fl",
                                        "gemma3_12b", "gpt5nano", "qwen3_14b"]],
    "study6_followup": [Run("gemini25fl", turns_left=[12, 6], tag="turns")] + study4_runs("gemini25fl"),
    # ---- Study 7 (proposed): conditions under which larger tiers skip.
    # Each step is a screen (Study 2 design at the stated turns). A step that
    # reaches 5% skipping is followed by the Study 4 design under the same
    # setting (see study7_followup in README). Fix this list before running.
    "study7_screen": [
        Run("sonnet55_min", tag="L1_min_reasoning"),
        Run("sonnet55", turns_left=[1, 2], overrun="void", tag="L2_deadline"),
        Run("sonnet55", system_extra=STAKES, tag="L3_stakes"),
        Run("haiku55", tag="L0_current_fast_tier"),
    ],
    # ---- robustness: position of actions in the list. With "balanced", the
    # first choices of a cell cycle through all six rotations (use episodes
    # in multiples of 6). Compare with Study 2/4 run under rotate="t".
    "order_check": [Run("haiku45", episodes=30, rotate="balanced", tag="balanced"),
                    Run("haiku45", frames=F5, hide_target=[False], episodes=30, rotate="balanced",
                        tag="s4_balanced")],
    # ---- Studies 2-5 rerun with balanced action order (Haiku 4.5), plus
    # checks of whether the floor in other models survives balanced order.
    "study2_bal": [Run("haiku45", turns_left=[12, 6, 3], rotate="balanced", tag="bal")],
    "study3_bal": [Run("haiku45_think", rotate="balanced", tag="bal")],
    "study4_bal": [Run("haiku45", frames=F5, hide_target=[False, True], rotate="balanced", tag="s4_bal")],
    "study5_bal": [Run("haiku45", frames=F5, show_ev=True, rotate="balanced", tag="s5_bal")],
    "study6_bal": [Run("gemini25fl", rotate="balanced", tag="bal"),
                   Run("gemini25fl", frames=F5, hide_target=[False, True], rotate="balanced", tag="s4_bal")],
    "floor_bal": [Run("sonnet55", episodes=6, rotate="balanced", tag="bal"),
                  Run("haiku55", rotate="balanced", tag="bal")],
    # ---- pipeline check, no API calls
    "smoke": [Run("mock", wordings=[0, 1, 2, 3], turns_left=[12, 3], episodes=20),
              Run("mock", frames=F5, wordings=[0, 1, 2, 3], hide_target=[False, True], episodes=20, tag="s4")],
}


def study7_followup(step_tag: str) -> list[Run]:
    """Study 4 design under the setting of a Study 7 step that passed the screen."""
    base = {r.tag: r for r in STUDIES["study7_screen"]}[step_tag]
    return study4_runs(base.model, tag=f"{step_tag}_s4", turns_left=base.turns_left,
                       system_extra=base.system_extra, overrun=base.overrun)
