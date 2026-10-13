"""Assemble the anonymized online-supplement archive (Online_Supplement.zip) from the repository."""
import os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))           # dynamic_bertrand/
OUT = os.path.join(HERE, "..", "Online_Supplement.zip")
CODE = ["bertrand_mpe.py", "equilibria_states.py", "sensitivity.py", "make_sens_tables.py", "theory_checks.py", "price_game.py",
        "make_price_figs.py", "alternating.py", "joint_dynamic.py", "joint_dynamic_starts.py", "joint_dynamic_sens.py", "timing_experiment.py"]
EMP = ["build_price_panel.py", "analyze_repricing.py", "collect_openrouter.py", "analyze_snapshots.py", "price_panel.csv.gz", "snapshots.csv"]
TOP = "Online_Supplement"


def main():
    files = [(os.path.join(HERE, "supplement_README.md"), "README.md"), (os.path.join(HERE, "supplement_requirements.txt"), "requirements.txt")]
    files += [(os.path.join(ROOT, f), f) for f in CODE]
    files += [(os.path.join(ROOT, "empirical", f), "empirical/" + f) for f in EMP]
    for dp, _, fs in os.walk(os.path.join(ROOT, "results")):
        for f in sorted(fs):
            full = os.path.join(dp, f)
            files.append((full, os.path.relpath(full, ROOT).replace(os.sep, "/")))
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in sorted(files, key=lambda x: x[1]):
            info = zipfile.ZipInfo(f"{TOP}/{arc}", date_time=(2026, 10, 13, 0, 0, 0))     # fixed timestamp
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, open(src, "rb").read())
    print("wrote", os.path.abspath(OUT), len(files), "files")


if __name__ == "__main__":
    main()
