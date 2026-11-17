# Preregistration H2b: a published tensor-network adapter (QuanTA) and the TT layout

Status: written before any H2b run. The git commit that adds this file, `adapters.py` (`QuantaDelta`),
`test_adapters.py`, `analyze_h2b.py` and `h2b_brands.txt` is its timestamp.

## 1. Why

H2 found LoRA ahead of our own tensor-train (TT) adapter at every matched budget (TT ahead for 0 of 31 brands
at the smallest budget). A reviewer can attribute this to our implementation or to the TT layout (4 cores,
balanced factors). H2b tests (a) a published tensor-network adapter, QuanTA (Chen et al., NeurIPS 2024),
ported from the authors' code (Apache-2.0) and checked against its mathematical definition in
`test_adapters.py`, and (b) TT with 3 and 5 cores.

LoRETTA (Yang et al., NAACL 2024) is not run: its code is GPL-3.0 and built on an old PEFT version, and its shape
table has no entry for Qwen2.5-1.5B's 256-wide v projection. This is reported as a limitation.

## 2. Hypothesis (two-sided)

- **H2b.** On the H2 task, QuanTA with 4 axes (`quanta:4`, 634,368 parameters) and LoRA r=4 (`lora:4`, 544,768
  parameters) differ in NLL relative gain. H0: the per-brand difference has median 0. QuanTA gets 16% more
  parameters, which favors it.

## 3. Sample and design

- 16 brands in `h2b_brands.txt`: every second of the 31 H2 brands. Same split (data seed 0; 320 train, 40 dev,
  80 eval), Qwen2.5-1.5B bf16, q and v projections, 300 steps, warmup + cosine, dev early stopping, seed 0.
- QuanTA learning rate: tuned on the 10 Phase 1 brands with `quanta:4` over 3e-4/1e-3/3e-3/1e-2, highest mean dev
  relative gain (`analyze_tune.py`); a choice at a grid edge extends the grid by one step (the H2 rule).
- LoRA and TT use the H2 learning rates (LoRA 3e-3, TT 1e-3) and are rerun in the same runs.

## 4. Commands (laptop)

```
python phase2.py --tune --tenants-from results/phase1 --configs quanta:4 --tune-lrs quanta=3e-4/1e-3/3e-3/1e-2 --out results/h2b_tune
python analyze_tune.py results/h2b_tune
python phase2.py --tenants $(grep -v '^#' h2b_brands.txt | paste -sd, -) --configs lora:1,lora:4,quanta:5,quanta:4,tt:2,tt:10 --lrs lora=3e-3,tt=1e-3,quanta=<tuned> --out results/h2b_main
python phase2.py --tenants $(grep -v '^#' h2b_brands.txt | paste -sd, -) --d 3 --configs tt:2,tt:10 --lrs tt=1e-3 --out results/h2b_tt_d3
python phase2.py --tenants $(grep -v '^#' h2b_brands.txt | paste -sd, -) --d 5 --configs tt:2,tt:10 --lrs tt=1e-3 --out results/h2b_tt_d5
python analyze_h2b.py results/h2b_main results/h2b_tt_d3 results/h2b_tt_d5
```

## 5. Analysis

- **Primary:** per brand, relative gain of `quanta:4` minus `lora:4`; Wilcoxon signed-rank, two-sided, alpha
  0.05; Hodges-Lehmann estimate with a bootstrap 95% interval.
- **Secondary (descriptive):** `quanta:5` (215,040 parameters) vs `lora:1` (136,192); TT with 3 and 5 cores vs 4
  cores at bond dimensions 2 and 10; the best TT/QuanTA configuration per brand, chosen on eval (optimistic for
  tensor networks), vs `lora:1`; training seconds per run.
- **Exclusions:** only technical failures, reported and not replaced.

## 6. Deviations

None (runs on 2026-11-17). The QuanTA tuning chose lr 1e-3, an interior point of the grid (mean dev relative
gain: 3e-4 0.448, 1e-3 0.453, 3e-3 0.426, 1e-2 0.324), so the grid was not extended. No brand was excluded.

## 7. Results

### H2b (supported: QuanTA is worse)

`quanta:4` minus `lora:4`: QuanTA ahead for 0 of 16 brands; median -0.0184; Hodges-Lehmann -0.0181 [-0.0201,
-0.0148]; Wilcoxon p = 3.1e-5 (the smallest attainable with 16 brands). H0 is rejected, against QuanTA, although
it had 16% more parameters.

| config | parameters | mean relative gain | seconds per run |
|---|---|---|---|
| lora:1 | 136,192 | 0.421 | 45 |
| lora:4 | 544,768 | 0.419 | 46 |
| quanta:5 | 215,040 | 0.401 | 110 |
| quanta:4 | 634,368 | 0.401 | 82 |
| tt:2 (4 cores) | 24,640 | 0.333 | 57 |
| tt:2, 3 cores | 53,760 | 0.371 | 54 |
| tt:2, 5 cores | 14,560 | 0.312 | 61 |
| tt:10 (4 cores) | 472,640 | 0.399 | 59 |
| tt:10, 3 cores | 806,400 | 0.400 | 54 |
| tt:10, 5 cores | 269,920 | 0.393 | 63 |

Secondary:
- `quanta:5` minus `lora:1`: ahead for 0 of 16, HL -0.0197 [-0.0246, -0.0150].
- TT layout: at bond dimension 2, fewer cores help (3 vs 4 cores: +0.039, 15 of 16 brands; 5 cores: -0.022,
  0 of 16), largely because fewer cores means more parameters at the same bond dimension. At bond dimension
  10 the layout matters little (3 cores +0.002, n.s.; 5 cores -0.006).
- The best of all eight TT and QuanTA configurations per brand, picked on the evaluation set itself (an
  optimistic choice), is still below `lora:1` for 15 of 16 brands (median -0.015).
- QuanTA trains 1.8-2.4 times slower than LoRA per run on this laptop GPU.

The H2 result is therefore not specific to our TT implementation or to its 4-core layout: a published
tensor-network adapter, ported from its authors' code and tuned by the same rule, is also below LoRA r=1 on
every brand.
