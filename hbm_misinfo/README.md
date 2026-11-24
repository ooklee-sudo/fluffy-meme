# HBM-guided health misinformation triage (prototype)

Prototype of a design-science artifact for online health communities (OHCs). It separates
two questions that existing detectors merge:

* **Veracity**: is the claim consistent with medical evidence? (retrieval-augmented LLM judge)
* **Behavioral harm potential**: does the message push readers *away from recommended care*?
  (Health Belief Model coding, following the project codebook)

The two are combined into moderator priority tiers (Urgent / Review / Monitor).
Everything runs with a 7–9B model, so a single 8 GB GPU is enough (4-bit quantized model);
retrieval runs on CPU.

```
post ──► [1] keyword screen ──► [2] HBM coding (Layers A–C) ──► per claim:
                                                               ├─ [3] query rewrite → BM25 (MedlinePlus / SciFact) + PubMed → LLM verdict
                                                               └─ [4] harm index H, persuasiveness P → tier
```

| File | Role |
| --- | --- |
| `codebook.py` | Codebook Layers A–C as an LLM prompt + validator (ranges, consistency) |
| `kb.py` | Builds the MedlinePlus or SciFact index (BM25) and queries PubMed live |
| `veracity.py` | Layer D: query rewrite, retrieval, judgment, with a no-retrieval ablation |
| `harm.py` | Codebook Section 6: H, P and tiers |
| `pipeline.py` | End to end on a JSONL of posts → `results.jsonl`, `coding_sheet.csv`, `triage.csv` |
| `eval_veracity.py` | Veracity on SciFact or PUBHEALTH, with vs. without retrieval |
| `reliability.py` | Krippendorff's alpha per code between two coding sheets (human–human or human–LLM) |
| `collect_reddit.py` | Downloads subreddit posts/comments (Arctic Shift archive), draws a stratified pilot sample, writes pipeline input and a blank coding sheet |
| `power_sim.py` | Simulation power analysis for the within-subjects warning-label experiment |
| `coding_form.py` | Excel form for human coders (drop-downs, consistency check) and export to a coding-sheet CSV |
| `examples/sample_posts.jsonl` | Eight constructed posts (not real users) for a smoke test |

## Setup

```bash
pip install -r requirements.txt
python kb.py build --out data/kb_medlineplus.jsonl            # ~1 min, 3,489 passages
```

For the SciFact evaluation, download its corpus once and index it:

```bash
curl -L -o data/scifact_corpus_train.parquet https://huggingface.co/datasets/allenai/scifact/resolve/62f5afb47a6d7f9b228d51eaeffc1d7ed0a87e65/corpus/train/0000.parquet
python kb.py build --scifact-corpus data/scifact_corpus_train.parquet --out data/kb_scifact.jsonl
```

### Model on an 8 GB GPU (local)

Any OpenAI-compatible server works. With [Ollama](https://ollama.com) and a 7B instruct model
in 4-bit (about 5 GB of VRAM):

```bash
ollama pull qwen2.5:7b-instruct
export LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=qwen2.5:7b-instruct
```

### Hosted model (no GPU)

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1 LLM_MODEL=qwen/qwen3.5-9b LLM_API_KEY=<key>
export LLM_EXTRA_BODY='{"reasoning": {"enabled": false}, "provider": {"ignore": ["PrimeIntellect"]}}'
# turns off thinking mode; that provider ignored the switch and returned empty replies (Nov 2026)
```

## Run

```bash
python pipeline.py examples/sample_posts.jsonl --kb data/kb_medlineplus.jsonl --pubmed --out-dir runs/demo
python eval_veracity.py --dataset scifact --n 150
python reliability.py coder1.csv coder2.csv
```

Input JSONL fields: `unit_id`, `subreddit`, `unit_type` (submission/comment), `parent_id`,
`parent_text` (context for comments), `text`. `coding_sheet.csv` uses the codebook's column
layout, so LLM codes can be compared directly with human codes.

## Pilot sample from Reddit

```bash
python collect_reddit.py --subreddits AskDocs cancer diabetes Supplements AlternativeHealth \
    --after 2024-01-01 --before 2025-01-01 --n 200 --out-dir data/reddit
python pipeline.py data/reddit/sample.jsonl --out-dir runs/pilot
```

* Source: the [Arctic Shift](https://arctic-shift.photon-reddit.com) Reddit archive API. Check your IRB
  protocol and Reddit's terms first. Usernames are never written to disk.
* Pool: up to `--per-month` posts and comments per subreddit and month, taken after `--starts` random
  times in each month so the pool is not concentrated at the start of the month.
* Strata: subreddit × unit type × claim-likely (health term plus an advice or claim cue).
  `--enrich-share 0.5` draws half of each cell from claim-likely units; `0` gives a simple random
  sample. Every unit carries `weight` = stratum pool / stratum sample for re-weighting.
* Rounds: units alternate between `pilot1` and `pilot2` within each stratum (codebook Section 8).
* `coding_sheet_blank.csv` has one `C1` row per unit plus `round`, `permalink`, `text` and
  `parent_text`; coders add `C2`/`C3` rows when a unit holds more claims. It is UTF-8 with BOM, so
  Excel shows it correctly. Give each coder a copy and compare with `reliability.py`.
* Five subreddits over one year with the defaults download about 24,000 items and take roughly
  15–20 minutes; raw files are cached in `data/reddit/raw/`.

## Human coding form

```bash
python coding_form.py create data/reddit/coding_sheet_blank.csv --round pilot1 --out coding/pilot1_coder1.xlsx
python coding_form.py export coding/pilot1_coder1.xlsx --coder coder1 --out coding/pilot1_coder1.csv
python reliability.py coding/pilot1_coder1.csv coding/pilot1_coder2.csv      # human vs human
python reliability.py coding/pilot1_coder1.csv runs/pilot/coding_sheet.csv   # human vs LLM
```

Each unit has three claim rows (C1–C3); unit-level codes (A1, C1–C6, more_claims, shaded yellow) go on
the C1 row. Every code is a drop-down, the `check` column turns red on inconsistent rows, and the
second sheet is a one-page codebook reference. Export drops unused claim rows, copies unit-level codes
to each claim row and reports out-of-range values by cell. Keep each coder's file separate and do not
show coders the LLM codes before they finish (codebook Section 8).

## Power analysis for the user experiment

`power_sim.py` simulates the within-subjects design (each participant rates K posts, half
misinformation; half of each type carries the warning; two counterbalanced lists) with participant
and post random effects, and reports power for three tests: by-participant paired t, min-F'
(generalizes over posts) and, with `--method mixed`, a mixed model (needs `statsmodels`).

```bash
python power_sim.py --d-mis -0.3 --posts 16 24 --participants 60 80 100 120 150
```

Smallest N with min-F' power ≥ 0.80 (one-sided α = .05, 1,000 simulations, default variance
components: participant 0.5, slope 0.2, post 0.4, residual 0.75):

| Warning effect on misinformation belief | 8 posts | 16 posts | 24 posts |
| --- | --- | --- | --- |
| d = −0.30 | 120 | 60 | 40 |
| d = −0.20 | – | 120 | 80 |

With 16 posts and d = −0.30, 100 participants give power 0.99 (min-F') and 0.98 on a 1–7 scale.
The variance components and effect size are assumptions: replace them with estimates from a
20–30 person pilot before fixing N. The tests are slightly conservative (type I error 0.03 by
participant, 0.01 min-F' at α = .05).

## First results (`qwen/qwen3.5-9b`, temperature 0, Nov 2026)

Veracity, stratified samples, macro-F1 over the gold labels present:

| Dataset (KB) | n | No retrieval | Retrieval |
| --- | --- | --- | --- |
| SciFact dev (5,183 abstracts) | 150 | 0.460 | **0.688** |
| PUBHEALTH test (MedlinePlus)* | 195 | 0.237 | 0.183 |

\* PUBHEALTH was run before the claim-extraction and judging rules were tightened (see below).

Retrieval helps when the knowledge base covers the claims (SciFact). PUBHEALTH is mostly news and
political fact-checks (e.g. "Obama Administration legalized bump stocks"), which no medical KB can
check, so it is a poor benchmark for this artifact; it is kept only as a lower bound.

On the eight constructed posts (`runs/demo/triage.csv`), the chemotherapy-refusal post is the only
Urgent case (H = 0.39), false-but-weak claims are Review, and accurate advice is Monitor.

## Known limitations and next steps

* **Claims must state the implied behavior.** A local 7B run turned "I threw out my inhaler and use a
  breathing method" into the anecdote "haven't needed my inhaler since", which the judge then marked
  supported from a passage on breathing exercise. Claim extraction now states the general claim
  ("a breathing method can replace a prescribed asthma inhaler"), and the judge no longer counts an
  on-topic passage as support. Keep checking extracted claims when you change models.
* **"refuted" vs "unsupported".** On real Reddit posts the judge first marked claims "refuted" whenever
  the passages did not support them (e.g. a correct note on epidermoid cysts after abscesses). The
  prompt now requires contradicting evidence for "refuted"; absent evidence is "unsupported".
* **Hosted providers can ignore the thinking switch** and return empty replies; such units are marked
  `error`, placed in Review, and the run continues.
* **Screening (stage 1)** is a keyword regex standing in for the fine-tuned classifier. Its first
  version matched exact words only and dropped e.g. "essential oils to fight tooth infections"; it now
  matches stems. For pilots use `--no-screen` so every unit reaches the LLM. The same regex defines the
  `claim_likely` stratum in `collect_reddit.py`; samples drawn before this change keep their original
  strata and weights (see their `manifest.json`).
* **HBM coding is unvalidated.** The codes must be checked against human coding
  (`reliability.py`, codebook Section 8) before H is used for anything. An earlier prompt that asked
  the model for direction (+1/−1) directly got the sign wrong; the model now only names which
  behavior is pushed and the code derives the sign.
* **H is conservative**: intensities from a 9B model run low, so the 0.33 cut-off may need
  recalibration against behavioral-intent replies.
* **Retrieval is BM25 only.** A dense or hybrid retriever (e.g. MedCPT, BGE) is the obvious next
  improvement; PubMed queries are rate-limited to about 3 per second without an NCBI API key.
* **Distillation for scale**: label a sample with a larger model, then fine-tune a 1.5–3B model
  (QLoRA) for HBM coding, so millions of posts can be processed on one 8 GB GPU.
