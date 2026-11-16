# Economics of mass personalization: first results (exploratory), 2026-11-16

Not preregistered. Same 31 brands and evaluation tokens as Phase 2 (`results/econ_e1`, `results/phase2_s*`);
serving costs measured on an RTX 5070 Laptop GPU (`results/econ_e2.json`).

## E1. Quality: tiny adapters beat in-context personalization on every brand

| Method | Mean relative gain | Context tokens per request | Trainable params per tenant |
| --- | --- | --- | --- |
| No personalization | 0 | 30 | 0 |
| Few-shot, 4 / 8 random examples | 0.213 / 0.260 | 252 / 473 | 0 |
| RAG, 4 / 8 retrieved examples (TF-IDF) | 0.241 / 0.284 | 251 / 480 | 0 |
| VeRA r=256 / r=1024 | 0.388 / 0.394 | 30 | 64,512 / 107,520 |
| LoRA r=1 / r=4 | 0.391 / 0.393 | 30 | 136,192 / 544,768 |

Per brand, RAG-8 was below LoRA r=1 and below VeRA r=256 for 31 of 31 brands (median -0.112 and -0.109;
Wilcoxon p < 0.001). RAG-8 beat random few-shot-8 for 28 of 31 brands.

## E2. Serving cost (batch 32, 30-token prompt, 32-token greedy reply)

| Method | ms per request | Requests per GPU-hour |
| --- | --- | --- |
| No personalization | 23.5 | 153,193 |
| 450 extra context tokens (RAG-8 scale) | 63.4 | 56,825 |
| LoRA r=1, unmerged | 26.4 | 136,219 |
| VeRA r=256, unmerged | 28.5 | 126,223 |

Training one LoRA r=1 adapter: 45 s (median of 31 Phase 2 runs, including dev checks).

## Cost model

Per tenant with request volume V: cost(RAG-8) = 63.35 ms x V; cost(LoRA r=1) = 45 s + 26.43 ms x V.

- **Break-even volume: about 1,200 requests** (LoRA 1,219; VeRA 1,292). Above it, the adapter is both
  cheaper and better.
- Using each brand's number of replies in the TWCS data as its request volume (210 to 168,649, median
  5,558), **81 of 106 brands are above the break-even** for LoRA.
- GPU-hours to serve every brand's TWCS volume: no personalization 8.2; RAG-8 for all 22.2; LoRA r=1 for
  all 10.6 (52% less than RAG-8, and higher quality); cheaper of the two per brand 10.4. Scaled to a year
  (x6): 49.3, 132.9, 56.8 and 56.8.
- For the 25 brands below the break-even, RAG is cheaper but worse; the extra cost of giving them an
  adapter anyway is small (at most 45 s of GPU time each).

## Caveats

- One laptop GPU, one base model (Qwen2.5-1.5B), naive unmerged adapters (no S-LoRA-style kernels), and
  no cost for loading many adapters into memory.
- Training cost assumes one training run per tenant; retraining when data or the base model changes adds
  cost (see the repository's real-options model of adapter maintenance).
- TWCS covers a few months of 2017 (treated here as about two months); the yearly figure is a scaling.
- Quality is response NLL, not a business outcome.
