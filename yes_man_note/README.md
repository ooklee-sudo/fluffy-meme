# Stance-sensitivity protocol (C1–C4): runner and analysis

Code for the measurement note in `measurement_note_JMIS.md`. It separates answer changes caused by a
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

Calls per model with 120 stems and the defaults: 120 × (5 + 1 + 4×2 + 2×2 rotations) = 2,160.
Resuming is safe: finished calls are skipped, failed API calls are retried, unparseable answers are kept as data.

## Outputs (`--outdir`)

`summary.md` (tables A–G), `model_stats.json` (point estimates, 95% stem-bootstrap intervals, QC counts),
`model_stats.csv`.

## How to read the tables

- **A.** `raw s` is the old conditional deference. If `nu_U` and `rho_U` are close to `raw s`, most of it is noise or
  any-sentence sensitivity; `s*` is the remainder.
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
