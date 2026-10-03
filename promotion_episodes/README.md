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

## Step 3: link reverts to the ship they reverse (`link_reverts.py` -> `revert_links.csv`)
Order: commit hash in title, then PR number in title, then fallback = latest earlier commit with overlapping changed files.

| method | n | confidence |
|---|---|---|
| pr_number | 2 | high (gte-Qwen2 undo PR 20, Phi-4-multimodal PR 56) |
| file_overlap | 5 | candidate only, needs hand check |
| hash | 0 | - |

Hand-check notes: Bahushruth config fix->revert and falcon-7b look right; phi-4 (525 days) and Apertus (245 days) are
suspect because overlap picks any earlier touch of the file, not necessarily the commit that introduced the reverted change;
gpt-j-6b is plausible (weights upload -> restore). Only 7 pairs, so this is a feasibility check, not a sample.

## Step 4: wider sample (fine-tune / adapter repos)
Collector gained `--filter` (repeatable), `--sort`, `--exclude`, threads. New sample = `text-generation` repos tagged
peft (1,500), trl (690), unsloth (684), merge (699), excluding repos already in the pilot: 3,420 repos, 77,440 commits
(`episodes_new.csv`): 31,823 ship-by-title, 76 revert-by-title.
File diffs fetched only for reverts (`add_file_diffs.py episodes_new.csv revert`); ship rows are `ship_unchecked`
(title label only, includes docs-only commits). Of 76 title-reverts: 57 docs_only, 19 artifact reverts
(`revert_links_new.csv`: 10 file_overlap, 9 unlinked). Combined with the pilot: `revert_links_all.csv` (26 artifact reverts, `sample` column).

Quality notes: fine-tune repos give genuine checkpoint rollbacks (e.g. t4nishq/phi-redactor, JoaoGuiAlves/thagiPo,
Jongbin-kr/exaone, jacob-24b GGUFs) but also noise: the 7 figment-finetuned-model-archive rows are archive restores
(not reversals), 'Upload rollback adapter artifacts' is a ship, and most links are same-day (days_ship_to_revert ~0),
which fits training-run churn rather than a promotion that went live. A stricter revert regex and a hash/diff-inversion
link check are the next fixes.

## Step 5: strict reverts + diff-inversion linking (`link_reverts_v2.py` -> `revert_links_v2.csv`)
Strict revert = title starts with revert/rollback/undo/restore/back out, not an archive repo, touches a non-docs artifact.
Link = best earlier commit (lookback 50) whose removed lines reappear as added lines in the revert (non-docs files only;
LFS pointer oids count). Threshold 0.5; every accepted link scored 1.0.
Result over both samples: 16 strict reverts, 12 linked, 4 not (gpt-j-6b, exaone, Sentie archive restore, StarSupernova).
Only 4 of the 12 have ship->revert gaps over one day (gte-Qwen2 3.1d, phi-4 525d, Apertus 245d; falcon 0.7d);
the rest are same-day training-run churn or delete-then-restore. These are artifact reversals, not evidence that a
judge-promoted release was rolled back: no judge/rubric data attached.
