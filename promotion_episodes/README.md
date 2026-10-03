# HF Hub ship/revert episode proxy

`python3 collect_hf_episodes.py --n 400 --out episodes.csv` (Hub API, no auth; gated repos return 0 commits).

Unit: commit on `main` of a top-downloaded `text-generation` repo. Label from commit title only:
`revert` (revert/rollback/restore/undo), `ship` (weights, config, generation_config, tokenizer, template, release),
`other` (README/license/metadata or unclassifiable).

Pilot (400 repos, 381 with history): 6,762 commits -> 2,785 ship, 13 revert (0.2%), 3,964 other.
Known limits: title-only labels are noisy (about half the reverts are README/model-card only);
no judge/rubric/eval-inventory info; gated repos (e.g. Meta-Llama) are empty; open-weight only.
Next: file-level diff to confirm artifact reverts; hand-code a sample to estimate precision.

## Step 2: file-level diffs (`add_file_diffs.py episodes.csv`)
Adds `files`, `cats`, `artifact_change`, `label2` using `/api/models/{repo}/compare/{sha}^..{sha}`.
`label2` demotes ship/revert commits that touch only docs (README, license, images) to `docs_only`;
`unknown` = no diff (root commit or API failure).

| label (title) | label2 (file diff) | n |
|---|---|---|
| ship | ship | 2,368 |
| ship | docs_only | 378 |
| ship | unknown | 39 |
| revert | revert | 7 |
| revert | docs_only | 6 |

Confirmed artifact reverts (7): phi-4 generation_config stop token, Apertus tokenizer special token,
falcon-7b in-library PR, gte-Qwen2 undo PR, Phi-4-multimodal PR 56, Qwen3.6-abliterated config fields, gpt-j-6b restore.
Caveat: file touched != behaviour changed; and a revert commit does not show what promotion it reverses (not linked yet).
