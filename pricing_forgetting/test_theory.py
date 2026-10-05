"""pytest wrapper: the propositions must verify numerically."""
import subprocess
import sys
import pathlib


def test_theory_checks():
    r = subprocess.run([sys.executable, "theory_checks.py"], cwd=pathlib.Path(__file__).parent, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
