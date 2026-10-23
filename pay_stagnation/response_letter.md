# Response to the editor

Submission ID e1f8f39f-ffa0-4b28-b8b5-c3ed9708dcf9
"Underpaid professors and world-leading firms: academic pay stagnation as a plausible force behind the flow of research talent into Korean industry"

Dear Ms Muthukumaran,

Thank you for the technical check. I have addressed each request below; changes are marked as tracked changes in `HSSC_manuscript_revised_tracked.docx` (a clean copy is `HSSC_manuscript_revised.docx`).

**1. Data and supporting documentation**
- The dataset behind Tables 1-2, Figs 1-2 and the figures quoted in the text, variable definitions, the handling of missing years (no interpolation), every transformation (CPI deflation, 2013 = 100 indices, compound growth rates, ratios), and a script that recomputes every derived number are deposited at https://github.com/ooklee-sudo/fluffy-meme/tree/main/pay_stagnation (`data/*.csv`, `README.md`, `reproduce.py`). The study uses no individual-level or restricted data; the underlying figures are the published sources listed in Supplementary Table S1.
- A Data Availability statement is at the end of the manuscript and is entered identically under "Declarations" in the submission system.

**2. Accurate reporting, overstated conclusions, limitations**
- Title, Discussion and Conclusions: "a key force" is now "a plausible force"; "supports the argument" is now "is consistent with the argument ... although the descriptive design cannot establish that it was the cause"; "central role" is now "probably played an important part"; "cause" is now "factor"; the policy paragraph is framed as conditional on the argument.
- New limitations paragraph at the end of the Discussion: descriptive design and no controls; sparse salary series (7 of 12 years) and the possibly understated 2013 value; secondary press sources; differing large-firm samples (211-366 firms); averages across fields; the career-stage assumption in the executive comparison.
- Results: stated that the -12% real fall rests on the 2019 and 2024 observations only; labelled the 4.3% (employees) and 1.6% (professors) growth rates as nominal and noted their slightly different windows; the abstract now says "in nominal terms".
- Methods/Results: the time-to-full-professor estimate is now explicitly presented as the author's observation, since no systematic source was found.
- All derived figures were recomputed with `reproduce.py` and agree with the text.

Kind regards,
Ook Lee
