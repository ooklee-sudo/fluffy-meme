# Preregistration: label-counterbalanced replication of Studies 1 and 2

Written and committed before any data for this replication were collected. Motivated by Kang (2026,
arXiv:2607.17219), which found that QQ verdicts in an LLM can change with the mapping of answer labels.

## Design

- Answers are given as a single letter, A or B. Mapping M1: A = Yes, B = No. Mapping M2: A = No, B = Yes.
  The mapping is stated in the system prompt and repeated after each question; it is the same for both
  questions in an interview. Answers are converted back to Yes/No before analysis.
- Study 1R: the first 400 response pairs of Study 1 (same items, same focal side, brands and positions),
  conditions blind / disclosure x orders QR / RQ x mappings M1 / M2, one interview per cell per model.
- Study 2R: the five Study 2 item pairs, 250 simulated respondents per item x order x mapping x model.
- Models, temperature (0.7 in 1R, 1.0 in 2R), token limit and reasoning settings as in the original studies.

## Analysis (fixed in advance)

- Per cell (Study 1R: model x condition, pooled over items; Study 2R: model x item): q computed within each
  mapping and pooled as the equal-weight mean of the two mapping-specific q values, with
  SE = 0.5 * sqrt(SE_M1^2 + SE_M2^2). Violation = two-sided p < 0.05 on the pooled q.
- Reported per mapping as diagnostics: q, its p value, and the yes-share of each question when asked first.
- Replication criteria: (a) a QQ verdict replicates if the pooled verdict equals the original verdict;
  (b) a verdict is label-robust if both mapping-specific verdicts agree with each other;
  (c) the "no" tendency replicates if the pooled yes-share is below 0.5 where the original was.
- The degeneracy rule of the earlier preregistrations (yes-share asked first < 0.05 or > 0.95, here applied
  to the pooled yes-share) is reported, not used to exclude cells.
