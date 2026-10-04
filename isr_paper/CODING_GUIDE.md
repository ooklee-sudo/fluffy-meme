# Coding guide: visual dependence of O*NET tasks

File: `data/human_coding_sample.csv` (200 random tasks). Fill the column `score_0_1_2` with 0, 1 or 2. Judge only the task text and occupation shown. Do not look up model labels.

Does performing the task DEPEND ON VISUAL PERCEPTION OR INSPECTION? That means the worker must see, watch, read visual displays/images/scenes, inspect or examine physical objects, or visually monitor something, and this visual judgment is central to doing the task, not merely incidental.

- **2** = visual perception is central (e.g. inspect products for defects, read X-ray images, watch a scene for hazards)
- **1** = visual perception is a meaningful but secondary part (e.g. review documents or blueprints as one input to a larger task)
- **0** = not dependent (talking, writing, calculating, lifting, deciding with no visual input specified)

Use `notes` for ambiguous cases. Ideally two coders code independently so human-human agreement can be reported alongside human-model agreement (save the second copy as a separate file).

After coding: `python agreement.py data/human_coding_sample_filled.csv`
