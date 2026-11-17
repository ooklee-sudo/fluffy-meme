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

Any change after the runs start will be listed here with its reason and date.
