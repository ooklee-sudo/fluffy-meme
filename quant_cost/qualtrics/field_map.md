# Loop & Merge field map (Study 2)

Qualtrics refers to loop columns by number: `${lm://Field/n}`. Paste each `loop_merge_V*.tsv` into the **Static Loop & Merge** table of its block (4 rows = cells C1 to C4, 13 columns).

| Field | Content | Used in |
| --- | --- | --- |
| 1 | cell (C1 to C4) | analysis: identifies the condition |
| 2 | case code (A to D) | analysis |
| 3 | scenario title | heading |
| 4 | task description | first paragraph |
| 5 | data sentence | first paragraph |
| 6 | B, running cost saving (thousand dollars) | key figures |
| 7 | E, cost of extra errors (thousand dollars) | key figures |
| 8 | L, loss if exposure occurs (thousand dollars) | key figures; WTP range |
| 9 | exposure probability (%): 2 or 6 | key figures |
| 10 | accuracy, local model (%) | performance table |
| 11 | accuracy, cloud API (%) | performance table |
| 12 | cost-per-correct row (HTML), empty for the accuracy-only cells | performance table |
| 13 | upper limit of the WTP question (L/4, thousand dollars) | Q3 prompt |

Cell definitions: C1 = 2%, accuracy only; C2 = 2%, accuracy + cost; C3 = 6%, accuracy only; C4 = 6%, accuracy + cost.
Responses are exported with the loop row number as a column prefix (`1_Q2`, `2_Q2`, ...), so the row number identifies the cell regardless of presentation order.
