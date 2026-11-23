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
export LLM_EXTRA_BODY='{"reasoning": {"enabled": false}}'   # turn off thinking mode
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

## First results (`qwen/qwen3.5-9b`, temperature 0, Nov 2026)

Veracity, stratified samples, macro-F1 over the gold labels present:

| Dataset (KB) | n | No retrieval | Retrieval |
| --- | --- | --- | --- |
| SciFact dev (5,183 abstracts) | 150 | 0.408 | **0.669** |
| PUBHEALTH test (MedlinePlus) | 195 | 0.237 | 0.183 |

Retrieval helps when the knowledge base covers the claims (SciFact). PUBHEALTH is mostly news and
political fact-checks (e.g. "Obama Administration legalized bump stocks"), which no medical KB can
check, so it is a poor benchmark for this artifact; it is kept only as a lower bound.

On the eight constructed posts (`runs/demo/triage.csv`), the chemotherapy-refusal post is the only
Urgent case (H = 0.39), false-but-weak claims are Review, and accurate advice is Monitor.

## Known limitations and next steps

* **Screening (stage 1)** is a keyword regex standing in for the fine-tuned classifier.
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
