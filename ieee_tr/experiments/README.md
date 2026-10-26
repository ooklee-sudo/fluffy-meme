# Multi-seed replication of the Pythia-70M study

    pip install torch transformers peft numpy scipy matplotlib
    python seed_study.py --seeds 0-9 --out results_seeds     # GPU strongly recommended
    python aggregate.py results_seeds --figdir ../figs_seeds

* `--quick` runs a 30-company, 30-day smoke test (about 12 min per seed on 4 CPU cores).
* One JSON per seed; re-running skips finished seeds.
* **Tune before the real run.** Run seed 0 alone first and check that (i) the deployed
  checkpoint reaches >= 95% on both suites and with notes, (ii) `follow_conflicting_note`
  is high, and (iii) the edit and LoRA settings (`--edit-lr`, `--lora-lr`, epochs) behave
  as intended. In the CPU smoke test the default edit/LoRA learning rates were too
  aggressive (retention damage of +7 to +40 pp), and the deployed model only reached
  about 92% on the dynamic suite after 40 epochs. Choose the settings on a pilot seed
  and keep them fixed for all reported seeds.
* This is a re-implementation from the manuscript's description, not the original code.
