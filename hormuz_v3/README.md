# Hormuz manuscript: third coder, v3 labels, correction simulation (work in progress)

Companion to the files on branch `claude/admiring-noether-734lkh` (`misq_note/hf`). Copy `code/*.py` into `misq_note/hf` and run from there.

## Status
- Done: third-coder analysis (`analysis_third_coder.py`, plan `ANALYSIS_PLAN_THIRD_CODER.md`); v3 labels (`results/human_labels_191_v3.csv`);
  re-analysis on v3 of Tables 1-6 and Figure 1 (`analysis_reanalysis.py v3 --no-placebo`; validated by reproducing the paper on `final`);
  correction simulation naive / human-only / PPI / DSL (`sim_dsl.py [v3]`, Figure 2).
- Manuscripts: v6 (misclassification), v7 (Bayesian appendix), v8 (model IDs), v9 (MISQ rewrite), v10 (third coder), v11 (v3 labels + simulation section).
- Pending: placebo, drift, weekend next-open and robustness (Table 7) and Figure 3 on v3. They need ~1,300 more Dukascopy tick-hours
  (`data/todo_v3.txt`). Run `code/fetch_ticks.py` on any PC with Python 3 (no packages), upload `WTI_ticks.zip`, merge with
  `data/WTI_bi5_downloaded.tar.gz`, rebuild ticks with `build_ticks.py`, then run `python analysis_reanalysis.py v3`.
- Manuscript source: `manuscript_build/content.txt` + `tables.json`, built with `node build.js <dir> <out.docx>` (needs npm `docx`).
