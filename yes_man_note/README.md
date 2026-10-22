# Stance-sensitivity protocol (C1–C4): runner and analysis

Code for the paper in `measurement_note_JMIS.md`. It separates answer changes caused by a
stated stance from run-to-run instability, any-sentence effects and evidence-weighing.

**Status.** Validated only against a synthetic mock model (`python -m unittest tests.test_pipeline`).
It has not been run on any real model, and this repository does not contain the real 120-stem item bank.

## Channels

| | channel | what it adds |
|---|---|---|
| C1 | stance-free, `--reps` replicates (default 5) | instability `nu_U`; more precise `a` |
| C2 | one length-matched neutral sentence | any-sentence effect `rho_U` |
| C3 | stance sentence at 4 claimed-evidence levels (`pref`, `weak`, `strong`, `noev`), against and for the evidence | corrected effect, gradient, Rescue |
| C4 | option letters rotated (2 extra permutations) for N and the primary stance | letter/position effects |
| C5 | a `pref` stance against the evidence plus the requester's disclosed track record (`accuracy_levels`: 20, 50, 80% correct) | does following rise with the disclosed accuracy? (Proposition 6). Same sentence length at every level, so the slope is free of a length effect |

Replicate 0 of the stance-free channel is the reference run. Every conditional quantity is a share of the
stems answered correctly there (see the docstring in `analyze.py`).

## Building the item bank

```bash
python generate_items.py --per-domain 50 --seed 7 --out data/items_v1.jsonl   # 300 items, prints a sha256
python audit_items.py --items data/items_v1.jsonl                              # must pass before any model run
python audit_items.py --items data/items_v1.jsonl --export-review review_A.csv # blinded sheet, one per reviewer
python audit_items.py --items data/items_v1.jsonl --import-review review_A.csv review_B.csv --flag-out flagged.txt
python runner.py ... --channels C1,C3 --reps 3 --only <2 small + 2 large models> --out results/pilot.jsonl
python audit_items.py --items data/items_v1.jsonl --pilot results/pilot.jsonl --flag-out suspect_keys.txt
```

Six domains (expected net value, expense policy, invoice with credit and tax, eligibility with a missing record,
late fee under a versioned rule, unit conversion), three difficulty tiers each (`difficulty` 1–3; harder tiers add
rule steps and shrink margins). Every key follows from the stem by exact arithmetic. The `unsup` option is the result of a
named plausible mistake (stored in `meta`), so a stance toward it is tempting rather than absurd; `third` is a different
mistake or action. The audit re-derives each key by parsing the rendered text with separate code. That catches plumbing
errors, not a misreading shared by both implementations, so **two independent human reviews of the keys are required**
before the bank is frozen. After the pilot, items every model missed on every run go to human review as suspected
key errors; items every model got right carry no information about instability. Freeze the bank (record the sha256)
before the main run and do not edit it afterwards. Tiers are a starting guess; the pilot decides whether they need shifting.

## Item bank format (JSONL, one object per line)

```json
{"id": "s001", "domain": "D1", "stem": "…evidence and question…",
 "options": {"gold": "…", "unsup": "…", "third": "…"},
 "gold_action": "approve the request", "unsup_action": "reject the request"}
```

`gold_action` / `unsup_action` are **bare-infinitive** phrases inserted into the stance templates
(`config/stances.json`: "…we should {action}"). Write them so every template is grammatical for every item;
a defective phrase in one domain is the kind of problem the earlier study had (Domain 6). Option letters are
assigned from a hash of the item id, identically in every channel for a given rotation.

## Running through OpenRouter

`config/models.openrouter.json` lists all 14 models (10 open-weight, 4 Claude tiers) behind one endpoint. Put the key in
the cloud environment's settings as the variable `OPENROUTER_API_KEY` (never paste it into a chat); a new session picks it up.

```bash
python estimate_cost.py --items data/items_v1.jsonl --models config/models.openrouter.json    # about $22 for 300 items, 5 reps, if answers stay short
python runner.py --items data/items_v1.jsonl --models config/models.openrouter.json --out results/smoke.jsonl --limit 3 --channels C1 --reps 2   # 3 items, every model
python analyze.py ...                                                                        # QC flags multi-provider models and truncated answers
```

Every row records `served_model`, `served_by` (the provider that answered), `stop`, `tokens_in`, `tokens_out`. OpenRouter may route
the same model to different providers with different hardware or quantization; the analysis flags any model answered by more
than one provider. To pin a provider, add `"extra_body": {"provider": {"order": ["<name>"], "allow_fallbacks": false}}` to a model
entry after the pilot shows who serves it. Check `tokens_out` in the smoke run before the main run: if a Claude tier returns long
output (reasoning), the cost estimate is too low and `max_tokens` (default 512) may truncate the letter.

## Run

```bash
pip install numpy
cp config/models.example.json config/models.json      # edit model ids and env var names
export ANTHROPIC_API_KEY=… AGG_BASE_URL=… AGG_API_KEY=…

python runner.py --items data/items.jsonl --models config/models.json --out results/run1.jsonl --count
python runner.py --items data/items.jsonl --models config/models.json --out results/run1.jsonl --workers 8
python analyze.py --results results/run1.jsonl --models config/models.json --outdir out/
python analyze.py ... --parse error --outdir out_parse_error/          # sensitivity: parse failures as errors
python analyze.py ... --exclude-domain D6 --outdir out_no_d6/          # sensitivity: drop a domain
```

Dry run without any API: `python make_mock_items.py --n 120 --out data/mock_items.jsonl` and a models file
whose entries use `"backend": "mock"` (see `tests/mock_models.json`). Mock results mean nothing about real models.

Calls per model with the defaults: 5 stance-free + 1 neutral + 4 levels × 2 directions + 2 rotations × 2 prompts + 3 disclosed-accuracy levels = 21 per item, so 6,300 per model for 300 items (about $26 for all 14 models if answers stay short).
Resuming is safe: finished calls are skipped, failed API calls are retried, unparseable answers are kept as data.

## Outputs (`--outdir`)

`summary.md` (tables A–G), `model_stats.json` (point estimates, 95% stem-bootstrap intervals, QC counts),
`model_stats.csv`.

## How to read the tables

- **A.** `raw s` is the old conditional deference. If `nu_U` and `rho_U` are close to `raw s`, most of it is noise or
  any-sentence sensitivity; `s*` is the remainder.
- **B2.** Slope in the disclosed accuracy > 0 supports evidence-weighing; ≈ 0 supports deference.
- **B.** Slope > 0 and a negative `noev − pref` say the answer responds to the claimed evidence (evidence-weighing).
  Both near 0 say the stance moves the answer whatever it claims (deference). Neither proves the model's reason.
- **E.** With few families the exact sign test cannot reach p < .05 (the table prints the smallest attainable p).
- **G.** Large differences across rotations or a strongly non-uniform letter distribution mean position effects.

## Known limits of this code

- Temperature: set per model in the models file; `null` omits the argument. Replicates only differ if the
  model is stochastic at that setting, so check that `nu_U` is not identically zero for a model you expect to be noisy.
- The bootstrap resamples stems and treats the models as fixed.
- `V_closed` plugs `s*` (a conditional share) into `(1 − s)(a − π)`. `s*` can be negative when a stance lowers
  the unsupported-answer rate below the neutral baseline; it is reported unclipped.
