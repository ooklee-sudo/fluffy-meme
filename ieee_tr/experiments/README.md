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

## Settings used for the reported run (fixed on held-out pilot seed 100)

Selection rule, fixed before looking at round 3: for each mechanism take the cheapest
setting (fewest processed tokens) whose mean fit on the facts it was trained on is >= 0.9
and, for the edit, whose locality (accuracy on untouched dynamic and static facts) is
>= 0.95. Pilot results are in `pilot_round1/`, `pilot_round2/`, `pilot_round3/`.

| mechanism | setting |
| --- | --- |
| deployed checkpoint | lr 1e-3 with linear decay to 10%, up to 200 epochs, target 95% |
| localized edit | MLP of layer 3, lr 5e-4, 15 epochs, 10 replayed unchanged facts per edited fact |
| LoRA | rank 16, no replay, lr 2e-3, 15 epochs |
| full fine-tune | lr 3e-4, 8 epochs on all current facts |

Pilot round 1 used no replay for the edit; the edit then overwrote unchanged dynamic
facts and raised total error. Reporting should say that the edit needs a locality
constraint (replay) to behave as a localized edit.
