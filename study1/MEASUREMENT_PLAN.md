# Study 1 measurement-improvement plan (written before re-running any outcome regression)

Date: 2026-11-25. Context: the first uncorrected run (results/study1_results_uncorrected.txt) was mostly null.
Changes below are chosen on measurement-quality criteria only (reliability, agreement, positional bias),
not on regression outcomes. Both the original and the improved runs will be reported.

Diagnostics from the first run (reliability.txt):
- BT photo scores: split-half reliability 0.96-0.97 for all attributes (high; reliability is not validity).
- Review-based experience scores: split-half reliability 0.48 (cleanliness), 0.81 (spaciousness), 0.71 (furnishings); brightness
  has too few mentions (3.2% of listings) to analyze.
- Cleanliness photo judgments show strong positional bias (first-position share 0.67, order reversal 0.34).

Planned changes:
1. Experience scores: use up to 50 most recent English reviews per listing (was 15) to raise reliability (target: cleanliness >= 0.7).
2. Cross-model check of photo scores: second VLM (qwen/qwen3-vl-30b-a3b-instruct) on a 2,000-listing random subset, new
   within-subset pairs (K = 10, both orders). Report correlation of BT scores with the primary model.
3. Brightness: reported but excluded from the composite if mentioned for < 10% of listings (pre-specified rule).
4. Errors-in-variables sensitivity: disattenuate regression coefficients using the measured reliabilities (report as sensitivity only).
5. Human validation: an annotation kit (blind, randomized) is produced; PPI correction is run only if human labels are supplied.
No outcome-based tuning of prompts, thresholds or model choice will be done after seeing regressions.
