# Labeling codebook (one label per row in `label_sheet.csv`, column `label`)
You see the end of the assistant's previous message and the user's next turn. Judge the user's turn only.

| Label | Meaning | Examples |
|---|---|---|
| **A** | User says the previous output was wrong, failed, or not what they wanted (explicit rejection, factual correction, "I meant ...", pasted error/traceback from running it, complaint) | "No, that's wrong", "I meant the other one", `Traceback ...` |
| **B** | User asks for a different/redone version without saying it was wrong (rewrite, redo, shorter, change tone, "try another") | "Rewrite it more formally", "do it again" |
| **C** | New request, continuation, or answer to a question the assistant asked | "Now translate it", "Yes, option 2" |
| **U** | Cannot tell | |

Rules: label blind (do not open `label_key_DO_NOT_OPEN.csv`). Do not discuss rows with a second labeler. Broad definition of correction = A+B; narrow = A only. Report both.
