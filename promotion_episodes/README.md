# HF Hub ship/revert episode proxy

`python3 collect_hf_episodes.py --n 400 --out episodes.csv` (Hub API, no auth; gated repos return 0 commits).

Unit: commit on `main` of a top-downloaded `text-generation` repo. Label from commit title only:
`revert` (revert/rollback/restore/undo), `ship` (weights, config, generation_config, tokenizer, template, release),
`other` (README/license/metadata or unclassifiable).

Pilot (400 repos, 381 with history): 6,762 commits -> 2,785 ship, 13 revert (0.2%), 3,964 other.
Known limits: title-only labels are noisy (about half the reverts are README/model-card only);
no judge/rubric/eval-inventory info; gated repos (e.g. Meta-Llama) are empty; open-weight only.
Next: file-level diff to confirm artifact reverts; hand-code a sample to estimate precision.
