# Share of LLM-drafted text in pre-grant publications, by year

Human model p: 1183 chunks from 2021. LLM model q: draft+expand rewrites (4954), equal weight over 7 generators, train split only. Vocabulary 6000. One ~1,100-word chunk per application; ~3,000 applications per year (random sample of the year's long-text file).

## All 6,000 words

| year | docs | alpha-hat (95% CI) | calibrated share (95% CI) | by publication quartile (alpha-hat Q1..Q4) |
|---|---|---|---|---|
| 2021 | 1183 | 0.020 (0.012–0.029) | 0.000 (0.000–0.010) | 0.014 / 0.030 / 0.014 / 0.022 |
| 2024 | 2970 | 0.018 (0.014–0.023) | 0.000 (0.000–0.003) | 0.012 / 0.023 / 0.019 / 0.018 |
| 2025 | 2949 | 0.027 (0.021–0.033) | 0.008 (0.001–0.015) | 0.014 / 0.029 / 0.020 / 0.043 |

Calibration curve (true share -> mean alpha-hat in 600-doc mixtures): 0.00->0.020, 0.02->0.037, 0.05->0.060, 0.10->0.103, 0.15->0.149, 0.20->0.190, 0.30->0.273, 0.40->0.354, 0.50->0.436, 0.70->0.606, 1.00->0.863

## Robustness: only the 300 most frequent words (mostly function words, less affected by topic drift)

| year | alpha-hat (95% CI) | calibrated share |
|---|---|---|
| 2021 | 0.034 (0.023–0.045) | 0.000 (0.000–0.011) |
| 2024 | 0.033 (0.026–0.040) | 0.000 (0.000–0.006) |
| 2025 | 0.036 (0.027–0.044) | 0.001 (0.000–0.010) |

## Words that most separate LLM text from human text (log odds ratio of occurrence)

LLM-overused: suffer (4.2), deficiencies (4.2), paramount (4.2), adaptability (4.1), drawbacks (4.1), relates (4.1), widespread (4.0), challenges (4.0), reliance (3.9), introduces (3.8), evolving (3.8), degrading (3.8), strategically (3.8), advancements (3.8), demands (3.8), preserves (3.8), ergonomic (3.8), adoption (3.8), emerged (3.7), modern (3.7), sustainable (3.7), promising (3.7), inadequate (3.7), lifespan (3.7), predominantly (3.7)
Human-overused: etc (-2.7), and (-2.0), words (-2.0), shown (-1.9), seen (-1.9), explained (-1.9), shows (-1.8), fig (-1.8), arrow (-1.7), hence (-1.6), figs (-1.6), equation (-1.5), bare (-1.5), respectively (-1.4), noted (-1.4), except (-1.4), min (-1.4), discussed (-1.4), again (-1.3), preferable (-1.3), here (-1.3), sent (-1.3), able (-1.2), bis (-1.2), illustrated (-1.2)
