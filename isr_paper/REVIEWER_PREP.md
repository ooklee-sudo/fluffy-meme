# Reviewer Preparation Notes

Internal document, not for submission. Table numbers follow the current manuscript. All scripts are run from `isr_paper/` (see `README.md`). Numbers quoted here are copied from the manuscript text; re-run the script before relying on any of them in a response letter.

## 1. Logic of the paper, section by section

| Section | What it does | What the reader should take away |
| --- | --- | --- |
| 1 Introduction | Poses the question (displacement now, or early phase of adoption?), states the approach and main results, lists contributions | The paper reports small, fragile post-2022 declines, substantial but early adoption, and a conditional projection |
| 2 Literature | 2.1 delayed adoption and J-curve; 2.2 AI exposure measures; 2.3 cheaper prediction, platform studies (Hui; Demirci; Zhou and Lee; Kim, Jin and Lee; Brynjolfsson, Li and Raymond) | Platform evidence shows fast substitution where switching is cheap; national hiring data have not been studied for visual AI |
| 3 Theory | Labor demand change is approximately adoption share times net effect among adopters; acceptance threshold a* = (c+r)/θ; hypotheses H1–H4 | Gives the scaling exercise (Table 9) and projection (Table 11) a formal basis |
| 4 Data | Eurostat adoption and barriers; UK/European/Canadian vacancy data; exposure construction and validation; supplementary data | Only open data; exposure is an LLM-coded measure with human validation |
| 5 Methods | Dose-response event study, quality heterogeneity, scaling | Continuous exposure, sub-major group FE, clustered by SOC minor group, randomization inference |
| 6 Results | 6.1 adoption and barriers; 6.2 UK; 6.3 Europe; 6.4 Canada; 6.5 groups; 6.6 quality; 6.7 scaling; 6.8 supplementary; 6.9 broad measure; 6.10 summary; 6.11 projection | Direction is negative and similar across three data sources, but magnitudes are small, partly pre-existing, and not monotone |
| 7 Discussion | Contributions, implications, limitations | Early-adoption interpretation is a hypothesis consistent with the data, not a test against alternatives |
| 8 Conclusion | Restates findings and the falsifiable criteria | |

## 2. Where each key number comes from

| Number (manuscript) | Script | Output file / table |
| --- | --- | --- |
| 9.6% EU27 firms use picture/video/audio generation; 8.8% text; barriers 70/54/53/38/18% | `eurostat_adoption_barriers.py` | `data/eurostat/*`; Tables 2–3 |
| Cross-country correlations (r = −0.76, −0.24, −0.02, 0.46; 23 countries) | `eurostat_adoption_barriers.py` | `data/eurostat/*` |
| Sector exposure vs adoption (0.84, 0.83, 0.81; 0.57 log points, permutation p = 0.006) | `eurostat_adoption_barriers.py` | `data/eurostat/*` |
| Task coding: 859 tasks scoring 1 or 2; quality split 237/355/267 | `classify_onet.py`, `classify_quality.py` | `data/all_creation_llm.jsonl`, `data/quality_llm.jsonl` |
| Rule-based score and agreement with LLM score | `rule_creation.py` | printed |
| Human validation (200-task stratified sample, weights, kappa, coders' disagreement) | `make_human_creation_sample.py`, `agreement_creation.py` | `data/human_creation_sample_*` |
| Broad measure (14.9% of tasks scoring 1 or more; rubric v2 tuned on first half of coder A sample) | `classify_onet.py` with `prompt_broad_v2.txt`; `classify_human_sample_broad.py` | `data/all_broad_llm.jsonl`, `data/human_sample_broad_v2.csv` |
| UK exposure (O*NET to ISCO to SOC 2020) | `uk_exposure.py` | UK SOC4 exposures |
| UK coefficients (−2.4%, −1.1%, −2.1%, −3.3%; randomization p) — Table 4, Fig. 1 | `uk_dose_response.py` (`EXPO=llm`) | `data/ons/uk_dose_response_*.csv/png` |
| Rule-based UK coefficients | `uk_dose_response.py` (`EXPO=rule`) | same directory |
| UK fragility checks (web designers dropped, base-year weights, share of tasks) | `uk_soc4_checks.py` | `data/ons/uk_soc4_*` |
| UK occupation groups — Table 7 | `uk_soc4_event_study.py` | `data/ons/uk_soc4_*` |
| European replication (16 countries) — Table 5 | `eurostat_oja_dose_response.py` | `data/eurostat/oja_*.csv` |
| Canada (308 unit groups, NOC 2021 duties scored with same rubric) — Table 6 | `classify_noc.py`, `canada_dose_response.py` | `data/statcan/canada_dose_response.csv` |
| Quality heterogeneity — Table 8 | `uk_threshold_heterogeneity.py` | `data/ons/uk_threshold_heterogeneity.csv` |
| Scaling by adoption — Table 9 | `uk_bound.py` | printed |
| US sectors (Indeed) | `indeed_event_study.py` | `data/indeed/*` |
| EU creative-industry employment | `eurostat_creative_employment.py` | `data/eurostat/*` |
| Broad-measure dose-response — Table 10 | `uk_dose_response.py` and `eurostat_oja_dose_response.py` with `EXPO=broad` | `data/ons/uk_dose_response_broad.*`, `data/eurostat/oja_dose_response_broad.csv` |
| Projection (threshold −0.27; adoption paths) — Table 11 | `projection.py` | `data/projection_detectability.csv` |

## 3. Anticipated reviewer questions and suggested answers

**Q1. This is a null result. Why is it publishable in ISR?**
The paper does not claim "no effect". It reports a small, fragile negative association, shows with survey data that adoption is substantial but early, and shows by scaling that observed declines in the most exposed occupations are too large to attribute to current adoption. The contribution is the link between adoption evidence, barriers, and labor-demand evidence, plus a conditional projection with falsifiable criteria. If the editor wants a stronger framing, lean on the delayed-assimilation literature (Fichman and Kemerer 1999) and the gap between platform and organizational settings.

**Q2. Identification: exposure is not randomly assigned. Why read the coefficients as related to generative AI at all?**
We do not claim causal identification. The text says so (Sections 5.2, 6.2, 7.3). Evidence offered is descriptive: dose-response in three independent data sources, within-group comparisons, randomization inference, and placebo design occupations. We state that the UK result is partly a reversal of a 2022 post-COVID rebound and cannot be separated from generative AI.

**Q3. The UK 2021 coefficient is negative. Isn't that a pre-trend?**
Yes, and the manuscript reports it. Exposed occupations were lower in 2021 than in 2022, so part of the post-2022 decline is a reversal. The European data show no differential decline before 2022 (+0.024, +0.008, +0.011), which is why we present the replication.

**Q4. LLM-coded exposure: how do you know it measures what you say?**
(a) Stratified, blinded 200-task human sample with design weights (strata A–D) and design-weighted kappa; (b) a rule-based keyword benchmark; (c) a broad alternative rubric tuned on half of coder A's sample and evaluated on the other half; (d) control for LLM exposure (Eloundou et al.). Be candid that the two coders disagree with each other (κ 0.18), so human agreement is limited and is reported as a limitation. Point to Section 4.3 and Table 10.

**Q5. Why do exposure estimates get larger without the LLM-exposure control?**
Visual-creation and LLM exposure are positively correlated across occupations (0.25 UK, 0.27 Europe), so the uncontrolled estimate partly captures text-AI exposure and general digitalization. We report both and treat the controlled estimate as the main one.

**Q6. Exposure also predicts adoption of text generation and image recognition. Is the measure specific?**
No, and the paper says so (Section 6.1). The exposure measure carries a general adoption propensity; this is why we use within-group comparisons and the language control.

**Q7. Job adverts measure hiring, not employment or wages.**
Agreed. We use adverts because they are the only open, occupation-level, timely series; employment is only available at the industry level (Section 6.8). We do not claim effects on employment or wages.

**Q8. The projection is speculative.**
It is labelled conditional, built on a logistic adoption path from an observed starting point, and framed as detectability under assumed β, not as a forecast. Section 6.11 lists falsification criteria that later data can use. Be ready to show sensitivity to the diffusion speed (Table 11 already does).

**Q9. Why a −0.27 detection threshold?**
The design is taken to detect an effect when the coefficient exceeds 1.96 times the standard error of the UK 2026 estimate (0.017), i.e. 0.033 per standard deviation of exposure. Dividing by the exposure of the most exposed occupation (8.0 standard deviations, graphic and multimedia designers) gives an aggregate log change of 0.27 for that occupation (Section 6.11 and `projection.py`). This is a scenario convention, not a power analysis; say so.

**Q10. Why only open data? Lightcast or Burning Glass would be better.**
Open data allow full replication and cover three countries. We acknowledge that commercial posting data with employer identifiers would allow firm-level adoption linkage; this is listed as future work.

**Q11. Use of generative AI in the research.**
The manuscript includes a Data, Code, and Generative AI Statement. Authors must fill in the model name and version and confirm the statement against INFORMS policy before submission.

**Q12. Is the scaling exercise (Table 9) a valid inference?**
It is an accounting bound, not an estimate. Observed decline divided by adoption share gives the implied effect among adopters. We use it only to show that the largest observed declines imply implausibly large effects among adopters, and discuss both readings (higher adoption among employers of designers vs decline not due to AI).

**Q13. Why not use the US as the main setting?**
US occupation-level posting data are not open. We use Indeed sectors as supplementary evidence only.

**Q14. Why are literature gaps in IS journals still present?**
We cite Gopal et al. (2025) in ISR on generative AI and IS research and the platform studies. No MISQ or JMIS empirical paper on generative visual AI and labor demand was verified during our search. Before submission, authors should search the journals' recent issues and add any such work.

## 4. Open items for the authors

1. Fill in `[MODEL NAME AND VERSION]`, the anonymized repository link, and the authors' confirmation of the AI-use statement.
2. Check ISR's current length and format limits; the guidelines page was not reachable during drafting.
3. Brynjolfsson, Li and Raymond (2025) is cited without volume and pages; complete the reference.
4. Kim, Jin and Lee (2026) is an NBER working paper; update if published.
5. Open the .docx in Word and check layout, tables, and the figure.
