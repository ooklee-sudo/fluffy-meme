# ChatGPT-release dose-response (first test of the original design)

Data: weekly new questions for the 50 sampled tags from the HF Stack Overflow dump (mikex86/stackoverflow-posts). Despite the card saying "before 2023-06-14", the data ends in the week of 2023-01-23 (partial), so only ChatGPT (2022-11-30) has a post window (7 full weeks, 2022-12-05 to 2023-01-16). Counts differ in level from the API (dump includes later-removed questions), relative changes are what matter.

Outcome: per tag, [mean ln(1+n) over 7 post weeks - same over 7 pre weeks (2022-10-10 to 2022-11-21)] minus the average of the same change in the three prior years (calendar-aligned).
Treatment: tag accuracy of GPT-3.5 (0613) on 40 pre-2022 questions per tag. Instrument: tag accuracy of Llama 3.1 8B.

- Mean seasonally adjusted change: -0.082 (SD across tags 0.103). Accuracy: GPT-3.5 mean 0.567, SD 0.102; Llama 3.1 8B mean 0.223, SD 0.085; corr across tags 0.39.
- OLS per +1 SD accuracy: +0.008 (se 0.017, t 0.47, R2 0.01).
- IV (Llama as instrument): +0.025, bootstrap 95% interval [-0.057, +0.131].
- Placebo (prior-year changes): betas -0.006, +0.008, -0.002 (all |t| < 0.8).

No dose-response in the first 7 weeks. The window is short: the large decline appears in 2023H1 (see volume_v3.json), after this data ends.
