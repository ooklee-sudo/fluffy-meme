# Study 1: Scale, Deference, and Dual Rationality in LLMs (code)

Implements the registered plan in `Study1_ISR_Format.docx`: 120 stems x 2 channels (normative / social) per model,
deterministic decoding, outcomes RN, RS, Flip, within-family size contrasts.

| File | Purpose |
|---|---|
| `items.py` | Generates the 120-stem bank (6 domains x 20), gold keys, closed list of four stance sentences. `python items.py` writes `items.jsonl`, `gold.json`, `MANIFEST.json` (SHA-256 hashes). Freeze these before collecting. |
| `prompts.py` | System prompt (identical for every model and item) and the answer parser (`RECOMMENDATION: A/B/C`, `CONFIDENCE: 0-100`; `<think>` blocks stripped). |
| `models.json` | Registered model grid. Check every model id and record the revision before collection. |
| `run.py` | Collects completions (backends: local `hf`, `openai`-compatible, `anthropic`). Temperature 0, top-p 1, 512 new tokens, one completion per query, interleaved order by hash of stem id, `--resume`, `--cut` (pre-registered reduction). |
| `audit.py` | Pilot checks before any model is queried: independent re-solver of every gold key, option/role checks, one-sentence difference between channels, balance, blind review sheet for two human reviewers and kappa, pilot ceiling/floor table. |
| `analyze.py` | Linear probability models (family + domain FE, stem-clustered SEs, Holm), H4 interaction, McNemar for closed pairs, ECE, parse-failure report, echo dual-coding export and Cohen's kappa. |

## Run

```
python items.py                                  # once; commit items.jsonl, gold.json, MANIFEST.json
python run.py --models models.json --only qwen2.5-7b qwen2.5-14b qwen2.5-32b --out results/study1.jsonl --resume
python analyze.py results/study1.jsonl --md results/analysis.md
python analyze.py results/study1.jsonl --drop-failed        # the "without failed rows" version
python analyze.py results/study1.jsonl --echo-sample echo_sample.csv   # 20% social completions for two blind coders
python analyze.py results/study1.jsonl --kappa echo_sample_coded.csv
```

API models need `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` set in the shell (never in files or chat). Large open models
(Qwen2.5-32B, Llama-3.1-70B, Gemma-2-27B) need a GPU machine; alternatively serve them with vLLM or a hosted endpoint and
use `"backend": "openai"` with `base_url` and `key_env` in `models.json`.

## Before collection (pilot checklist)

```
python items.py && python audit.py                          # must print 'mechanical problems: 0'
python audit.py --review-sheet review.csv                   # two reviewers answer independently, blind to the key
python audit.py --score-review review_filled.csv            # fix or drop any stem where a reviewer disagrees with the key
python run.py --models models.json --only qwen2.5-7b --out results/pilot.jsonl --limit 60
python audit.py --pilot results/pilot.jsonl                 # ceiling/floor by domain
```
Wording robustness: repeat the primary models with `--system-variant 1` and `--system-variant 2`, and with `--social-set B`
(separate `--out` files; `analyze.py` reports the size contrasts per wording when the logs are concatenated).

## Implementation choices (state them in the paper)

* The three options per stem have fixed roles: gold, unsupported, other. Letters are assigned by a hash of the stem id and
  are the same in both channels, so position is not confounded with channel. The social sentence is inserted after the
  scenario and before the option list; nothing else changes.
* Domains 4 and 5 are balanced so that the gold action is not always "no": D4 has 12 volatile-figure stems (gold: do not
  fine-tune) and 8 stable-behavior stems (gold: authorize); D5 mixes eligible and ineligible applicants. D1 mixes
  risky-better and certain-better stems. D6 gold is always declining the assurance, as the domain is defined.
* The audit found and fixed one generator imbalance before collection (Domain 5 was 19 declines of 20); Domain 6 remains
  constant by definition (always decline the prohibited assurance), so an always-refuse policy scores 100% RN there.
* "Not mechanical complements": CorrectSocial and RS are reported separately because of the third option.
* Holm is applied to two-sided p-values for b1 (RN, Flip); one-sided p-values for the directional hypotheses are
  reported next to them.
* Failed parses count as 0 on every indicator by default; `--drop-failed` drops them. A blind second coding of failures
  can be supplied with `--manual` (columns `model_key,stem_id,channel,letter`).
* Qwen3 thinking checkpoints get `max_new_tokens=4096` in `models.json` because 512 tokens truncate the reasoning; this is
  a deviation from the registered 512 and must be reported.
* Claude Opus/Sonnet 5.x reject a temperature argument; `temperature_applied` is logged per row and the manuscript must
  say that these tiers were not run at temperature zero.
