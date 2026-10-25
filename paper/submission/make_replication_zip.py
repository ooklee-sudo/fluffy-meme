"""Build the anonymized replication package as a zip file: word/05_Replication_Code.zip.
Run from paper/submission:  python3 make_replication_zip.py"""
import os, zipfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "word", "05_Replication_Code.zip")
TOP = "replication"

CODE = [
    "contracts/contracts.py", "contracts/running_example.py", "contracts/incentive_rent_table.py", "contracts/robustness.py",
    "contracts/asymmetric.py", "contracts/asym_sweep.py", "contracts/diff_bertrand.py", "contracts/diff_sweep.py",
    "contracts/calibration.py", "contracts/sensitivity.py", "contracts/fig_sensitivity.py", "contracts/verify_proofs.py",
    "contracts/general_theory.py",
    "empirical/load_repairbench.py", "empirical/analyze.py", "empirical/swebench_repo_level.py",
    "empirical/sampling/sample_humanevalfix.py", "empirical/sampling/analyze_hef.py",
]
# Our own generated data (pass/fail outcomes and token counts only; no model-generated code).
DATA = ["empirical/sampling/raw_google_gemma-3-4b-it.jsonl", "empirical/sampling/raw_meta-llama_llama-3.2-3b-instruct.jsonl",
        "empirical/sampling/raw_mistralai_ministral-8b-2512.jsonl"]
OUTPUTS = [
    "contracts/results_contracts.txt", "contracts/results_running_example.txt", "contracts/results_incentive_rent.txt",
    "contracts/results_robustness.txt", "contracts/results_asymmetric.txt", "contracts/results_asym_sweep.txt",
    "contracts/results_diff_bertrand.txt", "contracts/results_diff_sweep.txt", "contracts/results_calibration.txt",
    "contracts/results_sensitivity.txt", "contracts/results_verify_proofs.txt", "contracts/results_general_theory.txt",
    "contracts/fig_intuition.png", "contracts/fig_sensitivity.png",
    "empirical/results_empirical.txt", "empirical/results_swebench.txt", "empirical/sampling/results_hef.txt",
]

def sanitize(text):
    text = text.replace("/home/user/assert-kth/repairbench/results", "<REPAIRBENCH_CLONE>/results")
    text = text.replace("/home/user/swe-bench/experiments/evaluation", "<SWE_BENCH_EXPERIMENTS_CLONE>/evaluation")
    return text

README = """# Replication Package

"Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance"

This package contains the code that produces every number, table, and figure in the manuscript, the
HumanEvalFix sampling outcomes we generated, and the expected output of each script. Identifying
information has been removed for review.

## Contents

    contracts/          analytical model, equilibria, calibration, sensitivity, proof checks
    empirical/          RepairBench and SWE-bench analyses
    empirical/sampling/ HumanEvalFix sampling, analysis, and our sampled outcomes (raw_*.jsonl)
    expected_output/    output of each script as used in the manuscript and online appendix
    requirements.txt    Python packages and versions

## Environment

Python 3.13 with the packages in requirements.txt. Scripts in contracts/ import contracts.py and
each other, so run them from inside contracts/. Random seeds are fixed in each script.

## Run order and mapping to the manuscript

| Manuscript item | Script (folder) |
|---|---|
| Table 1, Figure 1 | running_example.py (contracts) |
| Table 2 | incentive_rent_table.py (contracts) |
| Table 3 and the 296-draw comparison (Section 5.1) | contracts.py, robustness.py (contracts) |
| Section 5.2 | asymmetric.py, then asym_sweep.py (contracts) |
| Table 4 and the 240-cell sweep (Section 5.3) | diff_bertrand.py, then diff_sweep.py (contracts) |
| Section 5.4 calibration, Table 5, Figure 2 | calibration.py, sensitivity.py, fig_sensitivity.py (contracts) |
| Online Appendix D numerical checks | verify_proofs.py, general_theory.py (contracts) |
| Section 6, RepairBench | load_repairbench.py, then analyze.py (empirical) |
| Section 6, SWE-bench | swebench_repo_level.py (empirical) |
| Section 6, HumanEvalFix | analyze_hef.py; sampling with sample_humanevalfix.py (empirical/sampling) |

Each script writes a results_*.txt file in its own folder; compare it with expected_output/.

## Data

- RepairBench results: clone the public RepairBench repository (we used the commit of 26 October 2025)
  and run `python3 load_repairbench.py <REPAIRBENCH_CLONE>/results`. This writes bug_counts.json,
  which analyze.py reads. The repository carries no license file, so its data are not redistributed here.
- SWE-bench submissions: clone the public SWE-bench experiments repository and run
  `python3 swebench_repo_level.py <SWE_BENCH_EXPERIMENTS_CLONE>/evaluation`.
- HumanEvalFix: our sampled outcomes are included (raw_*.jsonl: task, sample index, pass/fail,
  token counts, billed cost; no generated code), so `python3 analyze_hef.py` reproduces Section 6
  directly. To re-sample, download the Python split of the HumanEvalPack dataset (Hugging Face,
  bigcode/humanevalpack, file python/test-00000-of-00001.parquet, MIT license), save it as
  hep_python.parquet in empirical/sampling/, set OPENROUTER_API_KEY, and run
  `python3 sample_humanevalfix.py <model> 40` for meta-llama/llama-3.2-3b-instruct,
  mistralai/ministral-8b-2512 and google/gemma-3-4b-it. Model outputs vary between runs, so
  re-sampled numbers will differ slightly from ours. Our sampling cost was $0.56.
- Prices and statistics used in calibration.py are constants taken from the public sources cited in
  Section 5.4 of the manuscript (accessed 25 October 2026).
"""

REQUIREMENTS = "numpy==2.5.3\nscipy==1.18.1\npandas==3.0.5\npyarrow==26.0.0\nmatplotlib==3.11.2\n"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"{TOP}/README.md", README)
    z.writestr(f"{TOP}/requirements.txt", REQUIREMENTS)
    for rel in CODE:
        z.writestr(f"{TOP}/{rel}", sanitize(open(os.path.join(ROOT, rel)).read()))
    for rel in DATA:
        z.write(os.path.join(ROOT, rel), f"{TOP}/{rel}")
    for rel in OUTPUTS:
        z.write(os.path.join(ROOT, rel), f"{TOP}/expected_output/{os.path.basename(rel)}")

# check: no identifying strings or local paths
bad = re.compile(r"/home/user|fluffy|ooklee|hanyang|zen-wright", re.I)
with zipfile.ZipFile(OUT) as z:
    hits = [n for n in z.namelist() if not n.endswith((".png", ".jsonl")) and bad.search(z.read(n).decode("utf-8", "ignore"))]
    print(f"{OUT}: {len(z.namelist())} files, {os.path.getsize(OUT)/1024:.0f} KB; files with identifying strings: {hits or 'none'}")
