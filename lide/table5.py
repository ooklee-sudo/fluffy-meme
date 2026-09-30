"""Generate the Table 5 analogue (known-groups validation) from the harness: python -m lide.table5"""
import os

from .agents import ScriptedAgent
from .runner import run_grid

COLS = ["mean_risk", "max_risk", "reward_hack", "false_completion", "honest_exit", "asked_operator", "damage", "violations"]
HEAD = ["Mean risk", "Max risk", "Reward hack", "False completion", "Honest exit", "Asked operator", "Damage", "Rule violations"]

if __name__ == "__main__":
    df = run_grid(lambda e, m, r: ScriptedAgent(m, e), models=("escalating", "honest"), reps=10)
    df["model"] = df["model"].str.replace("scripted-", "").str.capitalize()
    g = df.groupby(["model", "env"])
    n = g.size().iloc[0]
    lines = [f"Table 5 (harness output; {len(df)} episodes, {n} per row)", "",
             "| Agent | Environment | " + " | ".join(HEAD) + " |", "|" + "---|" * (2 + len(HEAD))]
    for (m, e), r in g[COLS].mean().iterrows():
        lines.append(f"| {m} | {e.capitalize()} | " + " | ".join(f"{r[c]:.3f}" if c == "mean_risk" else f"{r[c]:.2f}" for c in COLS) + " |")
    os.makedirs("results/lide", exist_ok=True)
    open("results/lide/table5.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
