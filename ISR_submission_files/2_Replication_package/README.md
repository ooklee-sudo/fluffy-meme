# Replication package

Paper: "When the Platform Moves Underneath: Maintaining Complementary IT Assets under Endogenous Release Cadence"
(anonymized for double-blind review; the package contains no author information.)

## What is in this package

| Path | Content |
| --- | --- |
| `code/` | All scripts (see the mapping below) |
| `data/release_counts.csv` | Family-level release counts, window lengths, mean gaps and gap CVs behind Table 3 and Table 6 |
| `results/` | Outputs of the scripts, and the per-seed JSON files of every model-pair run (`seeds_gpu`, `seeds_large_gpu`, `tasks_small_gpu`, `tasks_large_gpu`) |
| `figures/` | Figures recreated from the model (Figures 1, 3, 4) and the sensitivity figure (Figure 5) |
| `run_all.sh` | Reproduces Tables 3 to 7, Appendix C summaries, Appendix F and the figures (about 5 minutes on a CPU) |
| `run_model_experiments.sh` | Re-runs the model-pair experiments (needs a GPU and internet) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Python 3.10 or later
pip install numpy scipy matplotlib                        # enough for run_all.sh
bash run_all.sh                                           # ~5 minutes, no GPU
```

`run_all.sh` ends with `code/check_against_paper.py`, which compares 62 numbers with the numbers printed in the manuscript
and prints PASS or FAIL for each. All 62 pass on the supplied outputs. `pip install -r requirements.txt` additionally installs
`torch`, `transformers`, `peft`, `datasets`, which are only needed for `run_model_experiments.sh`.

## Where each result comes from

| Manuscript item | Script | Input |
| --- | --- | --- |
| Table 3 (upgrade intensity, LR test) | `code/release_intensity.py` | `data/release_counts.csv` |
| Table 4 (policy regions) and Section 4 | `code/policy_regions.py`, `code/real_options.py` | closed-form formulas of Propositions 1 and 2 |
| Tables 5 and 7, Section 6 intensities, Numerical Finding 1, Figures 1, 3, 4 | `code/monopoly_duopoly.py`, `code/make_figures.py` | baseline parameters in the file header |
| Table 6 (regular arrivals) | `code/arrival_robustness.py` | `data/release_counts.csv` |
| Appendix F, Figure 5 | `code/vendor_sensitivity.py` | grid defined in the script |
| Tables C.1 to C.3, Section 3.3, $\Gamma$ values | `code/run_seeds.py`, `code/act_llama.py` (runs), `code/aggregate_seeds.py`, `code/analysis_all.py` (summaries) | public checkpoints and datasets from the Hugging Face Hub |

## Model-pair experiments

* Models: Pythia 160M and 1.4B (checkpoints at steps 73000, 113000, 133000 and 143000), SmolLM2 360M and 1.7B, Qwen2.5 0.5B, 1.5B and 3B (base and instruct). All are public.
* Tasks: GSM8K (`openai/gsm8k`), DialogSum (`knkarthick/dialogsum`), text-to-SQL (`b-mc2/sql-create-context`).
* Settings: rank-8 LoRA on every linear layer of the decoder, 500 training problems, 300 AdamW steps (batch size 4, learning rate 5e-4), 128 unlabeled calibration prompts, float32. Five seeds (three for the two larger pairs on the two added tasks). The seed resamples the training and calibration rows and the training order; the 200 evaluation rows are fixed.
* A seed is dropped when its retraining gain is less than half the pair's median gain (one seed overall; see Appendix C of the manuscript). `aggregate_seeds.py --keep-all` switches this off.
* Hardware used: one RTX 4090 (small pairs, GSM8K and the two added tasks), one NVIDIA H200 (larger pairs, GSM8K) and one H100 80GB (larger pairs, added tasks), float32. Results are not bit-identical across devices; the CPU run of seed 0 for Pythia +10k gave R_C = 0.940, R_A = 0.941 against 0.954 and 0.953 on the GPU.
* Wall-clock cost ratios C_A/C_N are only meaningful on CPU runs; the GPU ratios are dominated by fixed overhead and are not used in the paper.
* Downloads can be slow on some hosts (13 minutes for Pythia-1.4B on one machine); the first run of each model is dominated by this.

## Known deviations from the printed numbers

* Table 3: the input file uses the window lengths as printed (rounded to 0.01 year), so the pooled rate is 1.975 against 1.97 printed, Mistral is 2.67 against 2.66, and the LR statistic is 3.44 against 3.43. The checker allows for this.
* Table 4: values of v* and the band differ from the printed ones by up to 1 percent (for example Gemma v* copy 3.52 against 3.50, Gamma 0.38 in both), because the manuscript prints R_copy = 0.57 and R_transfer = 0.78 rounded.
* Numerical Finding 1 is verified at H = 20 for the printed profile (mu, R) = (2.50, 0.96) versus (1.38, 0.08): neither owner gains from a deviation on a grid with step 0.1 in mu and 0.02 in R, and prices and mean customer values match. The statements about other values of H (symmetric equilibrium at weak races, both owners fast and compatible at very intense races) are not reproduced by this package.

## Not included

* The dated release history behind Table 3 and Figure 2 (release dates of 36 main-line versions and the broad-definition list). The package contains only the family-level counts, window lengths, gaps and CVs printed in Table 3. Figure 2 therefore is not recreated.
* Model weights, adapters and training logs (they can be regenerated with `run_model_experiments.sh`).

## Notes

* All scripts run from this directory (`python code/<script>.py`), write only to `results/` and `figures/`, and use fixed seeds where randomness is involved.
* `code/real_options.py`, `code/vendor_sensitivity.py` and `code/act_llama.py` contain the model, the parameter grid and the transfer experiments with docstrings that describe the equations they implement.
