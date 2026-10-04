# Early Adoption, Delayed Displacement? Generative Visual AI and Creative Work

Manuscript: `ISR_Submission_Early_Adoption_Delayed_Displacement.docx` (built by `build.js`, `node build.js`).

## Pipeline (run from this directory)
| Step | Script | Output |
| --- | --- | --- |
| O*NET task coding (visual content creation) | `classify_onet.py --model $LLM_MODEL --prompt-file prompt_creation.txt --out data/all_creation_llm.jsonl` (needs `OPENROUTER_API_KEY` and `LLM_MODEL`, the identifier of the model used for coding, which is reported in the manuscript) | 18,796 task scores (0/1/2) |
| Quality-requirement coding of the 859 creation tasks | `classify_quality.py` (`prompt_quality.txt`) | `data/quality_llm.jsonl` |
| Rule-based check of the creation score | `rule_creation.py` | task- and occupation-level agreement with the LLM score |
| O*NET -> ISCO-08 -> UK SOC 2020 exposure mapping | `uk_exposure.py` | UK SOC4 exposures |
| UK dose-response event study (Table 4, Fig. 1) | `EXPO=llm python uk_dose_response.py 0` (`EXPO=rule` for the rule-based score) | `data/ons/uk_dose_response_*.csv/png` |
| UK occupation groups (Table 5), robustness | `uk_soc4_event_study.py`, `uk_soc4_checks.py` | `data/ons/uk_soc4_*` |
| Broad-measure analysis (Table 10) | `classify_onet.py --prompt-file prompt_broad_v2.txt --with-occupation --out data/all_broad_llm.jsonl`, then `EXPO=broad python uk_dose_response.py 0` and `EXPO=broad python eurostat_oja_dose_response.py` | `data/ons/uk_dose_response_broad.*`, `data/eurostat/oja_dose_response_broad.csv` |
| Quality-requirement heterogeneity (Table 6) | `uk_threshold_heterogeneity.py` | `data/ons/uk_threshold_heterogeneity.csv` |
| Eurostat adoption, barriers, exposure gradient (Tables 2-3) | `eurostat_adoption_barriers.py` | `data/eurostat/*` |
| Scaling by adoption (Table 7) | `uk_bound.py` | printed |
| European replication (Table 5) | `eurostat_oja_dose_response.py` | `data/eurostat/oja_*.csv` |
| Canada replication (Table 6) | `classify_noc.py` then `canada_dose_response.py` | `data/statcan/canada_dose_response.csv` |
| Conditional projection (Table 10) | `projection.py` | `data/projection_detectability.csv` |
| Supplementary: US sectors, EU employment | `indeed_event_study.py`, `eurostat_creative_employment.py` | `data/indeed/*`, `data/eurostat/*` |

## Data sources (open)
O*NET 29.1; ONS Labour demand volumes by SOC 2020 (Textkernel) and SOC 2020 coding index (download to `data/ons/`, large files not tracked); Eurostat isoc_eb_ai, isoc_eb_ain2, lfsa_eisn2, lfsa_egan22d (API); Indeed Hiring Lab job postings tracker (GitHub).

Not validated: the LLM exposure measure has no human-coder validation yet (see manuscript Section 4.3).
