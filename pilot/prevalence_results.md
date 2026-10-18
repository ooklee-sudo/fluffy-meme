# Share of LLM-drafted text in pre-grant publications, by year

Human model p: 1183 chunks from 2021. LLM model q: draft+expand rewrites (4954), equal weight over 7 generators, train split only. Vocabulary 6000. One ~1,100-word chunk per application; ~3,000 applications per year (random sample of the year's long-text file).

## All 6,000 words

| year | docs | alpha-hat (95% CI) | calibrated share (95% CI) | by publication quartile (alpha-hat Q1..Q4) |
|---|---|---|---|---|
| 2021 | 1183 | 0.019 (0.011–0.027) | 0.000 (0.000–0.009) | 0.014 / 0.027 / 0.014 / 0.020 |
| 2024 | 2970 | 0.017 (0.013–0.022) | 0.000 (0.000–0.004) | 0.011 / 0.023 / 0.018 / 0.017 |
| 2025 | 2949 | 0.025 (0.020–0.031) | 0.007 (0.001–0.014) | 0.013 / 0.027 / 0.017 / 0.041 |

Calibration curve (true share -> mean alpha-hat in 600-doc mixtures): 0.00->0.019, 0.02->0.035, 0.05->0.059, 0.10->0.101, 0.15->0.148, 0.20->0.190, 0.30->0.272, 0.40->0.355, 0.50->0.438, 0.70->0.610, 1.00->0.868

## Robustness: only the 300 most frequent words (mostly function words, less affected by topic drift)

| year | alpha-hat (95% CI) | calibrated share |
|---|---|---|
| 2021 | 0.025 (0.015–0.036) | 0.000 (0.000–0.011) |
| 2024 | 0.025 (0.019–0.031) | 0.000 (0.000–0.005) |
| 2025 | 0.031 (0.023–0.039) | 0.005 (0.000–0.014) |

## Words that most separate LLM text from human text (log odds ratio of occurrence)

LLM-overused: suffer (4.2), deficiencies (4.2), paramount (4.2), adaptability (4.1), drawbacks (4.1), relates (4.1), widespread (4.0), challenges (4.0), reliance (3.9), introduces (3.8), evolving (3.8), degrading (3.8), strategically (3.8), advancements (3.8), demands (3.8), preserves (3.8), ergonomic (3.8), adoption (3.8), emerged (3.7), modern (3.7), sustainable (3.7), promising (3.7), inadequate (3.7), lifespan (3.7), predominantly (3.7)
Human-overused: infig (-5.5), tofig (-4.4), offig (-3.9), infigs (-3.7), tofigs (-3.4), aand (-2.9), ais (-2.8), etc (-2.7), andfig (-2.7), offigs (-2.3), aof (-2.2), seefig (-2.1), and (-2.0), bof (-2.0), words (-2.0), shown (-1.9), seen (-1.9), explained (-1.9), shows (-1.8), fig (-1.8), bmay (-1.8), withfig (-1.8), ato (-1.7), amay (-1.7), cis (-1.7)
