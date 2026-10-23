# Draft revision materials (HSSC, Submission e1f8f39f-ffa0-4b28-b8b5-c3ed9708dcf9)

## Data Availability statement (use identically in the manuscript and under "Declarations" in the submission system)

> All data analysed in this study are publicly available aggregate figures. The compiled dataset (professor salaries, large-firm pay, business R&D, researcher counts, HBM market shares and the CPI series), variable definitions, the transformations applied, and the Python script that reproduces every derived figure in the text and Tables 1-2 are available at https://github.com/ooklee-sudo/fluffy-meme/tree/main/pay_stagnation [replace with a DOI-bearing archive, e.g. Zenodo, before final publication] and in Supplementary Tables S1-S2. The primary sources are the published reports cited in the article (Ministry of Science and ICT/KISTEP Survey of R&D; Statistics Korea CPI; Ministry of Education salary figures and CEO Score / Leaders Index pay analyses as reported in the press; Counterpoint Research). No restricted or individual-level data were used, and there are no obstacles to sharing.

## Point-by-point response

**Editor, item 1: data and supporting documentation.**
We have deposited the full dataset behind Tables 1-2, Fig. 1-2 and the quoted figures (`data/*.csv`), with variable definitions, coding of missing years, and every transformation (CPI deflation, 2013 = 100 indices, compound growth rates, ratios) documented in `README.md`. `reproduce.py` regenerates each derived number in the text. The study uses no raw or cleaned individual-level data; the "raw" data are the published figures cited, listed with sources in Supplementary Table S1. A Data Availability statement now closes the manuscript and is entered identically under "Declarations".

**Editor: accurate reporting, overstated conclusions, limitations.**
Candidate manuscript edits (not yet made; each needs the author's decision):
1. Add a Limitations paragraph: salary points exist for only 7 of 12 years (2013, 2015-2019, 2024); the 2013 value may be understated (zero-value reports); large-firm samples differ across years (211-366 firms); professor and employee windows differ (2012/2025 vs 2013/2024); figures come from press reports, not primary ministry tables.
2. State that the 2019-2024 real fall (-12%) rests on two endpoints, with no 2020-2023 observations.
3. Soften causal wording in the title ("a key force"), abstract and conclusion, since Methods state the design is descriptive and cannot identify causal effects.
4. Say explicitly that the 4.3% (employees) and 1.6% (professors) growth rates are nominal and cover different year ranges, or compare like for like.
5. Replace the personal-experience estimate of time-to-full-professor with a cited source, or flag it as anecdotal.
