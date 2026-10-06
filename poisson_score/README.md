# poisson_score

Reference implementation of the Poisson-Score (see `../paper/manuscript.md`, Section 3).

Event families: **P** academic punctuation/symbols, **D** discourse markers, **N** passives + nominalizations.
Score = mean Hellinger distance between binned window-count distribution and Poisson(λ̂) over families, in [0,1].
Also reported: signed index of dispersion (direction), dispersion-test p-value, and an NB-Score against a negative-binomial benchmark fitted on human text.

    pip install numpy scipy pytest
    python -m pytest tests
    python -m poisson_score.cli explain paper.txt
    python -m poisson_score.cli score corpus_dir -o scores.csv
    python -m poisson_score.cli pilot --human human_dir --synthetic llm_dir -o pilot.csv

Inputs are plain `.txt` files (one document each). Rules are heuristic regex/suffix based (no spaCy) so every counted token is auditable; a POS-tagger-based passive detector is a planned upgrade.
`pilot` fits the NB reference in-sample; split calibration/test for the real study.
