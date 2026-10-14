# Pre-registration: who reported the decision first — the post or an outside source? (committed before any search, 2026-10-14)

Motivation (simulated peer review): the argument that the platform matters depends on whether the post was the first public source of the decision (platform as first channel) or whether wires/officials had already reported it (post as echo). Prior sample of 20 triangulated cases is selected on the outcome; this test covers all war-period signal posts with an hourly reaction.

## Sample
All 61 war-period posts coded ESC (n = 28) or DEESC (n = 33) by the blind direction coder with an hourly reaction (`qual/wire_input.json`; reaction values withheld from the researchers who search; ID key `qual/wire_cases_KEY.csv`).

## Procedure (researchers who search see only post time and text)
For each post, find the earliest public report, in any reputable wire/major outlet or official source with a stated or inferable UTC time, of the substantive decision or statement the post contains. Classify:
- POST_FIRST: no earlier public report found, and at least one report after the post is found;
- OTHER_FIRST: a public report that precedes the post by more than 10 minutes;
- SIMULTANEOUS: within ±10 minutes (including when outlets cite the post as the source with times within 10 min);
- UNDETERMINABLE: timing cannot be established from accessible sources (the default if in doubt).
Record source, URL, UTC time, and quote (≤ 30 words). Record lead time in minutes where known. No guessing.

## Hypotheses (confirmatory; decision rules fixed now)
W1. Directional reaction (e = sign × two-hour WTI reaction) is larger for POST_FIRST than for OTHER_FIRST posts. One-sided permutation test (20,000; seed 20261014) on posts that are classifiable (POST_FIRST vs OTHER_FIRST), pooling ESC and DEESC and also reported separately.
W2. Reported descriptively: share of each class among de-escalation and escalation posts; reaction by class.
Decision: W1 supported if one-sided p < .05. If fewer than 8 posts fall in either class, the test is reported as "not estimable" and only descriptive shares are given. UNDETERMINABLE is never recoded.

## Caveats stated in advance
Timestamps in accessible sources are often at minute or hour resolution; paywalled outlets may be unreachable; classification is by model-instance researchers (a human check of a random 10 is planned [TODO]).

## Amendments
(none)
