"""Reproduce every table, simulation result and figure in the manuscript.

Usage (from this folder):  python reproduce.py
Outputs are written to ../results/. Runtime: under a minute on a laptop.
"""
import runpy, time, os
HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("verify.py",     "Check the simulation against the analytical break-even and theta values"),
    ("table_life.py", "Table 1: lifetimes (Kaplan-Meier) and notice periods by vendor"),
    ("run_all.py",    "Table 2: savings and break-even premium by vendor and price scenario"),
    ("run_notice.py", "Notice-policy results (Anthropic vs Bedrock notice, Gemini previews)"),
    ("run_switch.py", "Early-switching comparison (NPV rule vs option threshold)"),
    ("fig1.py",       "Figure 1"),
]
os.chdir(HERE)
for script, what in STEPS:
    t = time.time()
    print(f"\n=== {script}: {what}", flush=True)
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")
    print(f"--- done in {time.time() - t:.0f} s", flush=True)
print("\nAll outputs are in", os.path.normpath(os.path.join(HERE, "..", "results")))
