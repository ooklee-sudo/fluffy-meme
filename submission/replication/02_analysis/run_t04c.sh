#!/usr/bin/env bash
# Specifications of Table 4, Test C (August/September 2024 cohort = "2024-09", event window -8..+6) and Figure 1.
# Run from the package root:  bash 02_analysis/run_t04c.sh
set -e
S=02_analysis/t04c_test_c_callaway_santanna.py
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S all          # all platforms           (+0.022)
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S mobile       # mobile web              (+0.062)
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S all pt       # all platforms, excl. pt (robustness, not tabulated)
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S desktop pt   # desktop excl. Portuguese (-0.061)
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S desktop hi   # desktop excl. Hindi      (-0.090)
EMIN=-8 EMAX=6 python3 $S desktop                    # desktop, all cohorts pooled (-0.047)
# run the main desktop specification LAST so that output/cs_es_desktop.csv holds the Figure 1 series
EMIN=-8 EMAX=6 ONLYG=2024-09 python3 $S desktop      # desktop (-0.089), Figure 1
# The first exploratory run in the session used the default window (-12..12), all cohorts:  python3 $S all
