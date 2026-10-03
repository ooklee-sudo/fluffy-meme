# Study 1b results record

Source: `results\analysis_1b_open.md`, `results\analysis_1b_open_dropfailed.md`, `results\analysis_1b_claude.md` on the author's computer (raw data `results\study1b.jsonl`, not in the repository). The numbers in `Study1_combined_v1.docx` were transcribed from these outputs.
Frozen bank: commit 0c61985 (items_hard.jsonl SHA-256 87d1f368...). Run on 2026-10-03 with `run_hard.bat`; 14 models x 240 queries; no model dropped or added after the results.

Registered primary (failed rows coded 0), open-weight sample, Large vs Small: RN +0.265, RS -0.292, CondRS -0.238, Flip -0.077, CorrectSocial +0.340 (all p<.01).
Equivalence: RS Large-Small 90% CI [-0.345, -0.238]; CondRS [-0.297, -0.179] (below the -5 point margin: H2 not supported). H3 one-sided p = 1.000.
Sensitivity (failed rows dropped): RN +0.248, RS -0.319, CondRS -0.238, Flip -0.091. Qwen2.5-7B parse failures 10.8% / 15.8%, mean output 20 tokens.
Family-level: RS lower in 5 of 5 families (exact sign test p = .062, the smallest attainable with five families); RN higher in 4 of 5.
Claude ladder: RN 1.000 in all tiers; RS .050 (Haiku), 0 for Sonnet, Opus, Fable; Large-Small -0.050 (p = .014); McNemar Flip 0 vs 6, p = .031.
Informativeness rule (open sample): mean RN .754 (in [.35, .95]); conditional deference far above .02: met.
